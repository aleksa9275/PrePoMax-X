"""Real mesh-order, quadratic CAD regions, original configuration and native solve."""
import hashlib,json
from pathlib import Path
from unittest.mock import patch
from PyQt6 import QtCore,QtWidgets


def begin(app,w,source,output):
    from viewport import decode
    from analysis_editor import AnalysisDialog
    from quadratic_analysis import boundary_fixture, field_errors
    output.mkdir(parents=True,exist_ok=False)
    report={'success':False,'transport':w.transport,'checks':[]};state={'done':False}
    w.confirm_discard=lambda:True
    def check(name,condition):
        report['checks'].append({'name':name,'passed':bool(condition)})
        if not condition:raise ValueError(name)
    def finish(error=None):
        if state['done']:return
        if w.busy:
            w.cancel_operation();QtCore.QTimer.singleShot(100,lambda:finish(error or 'Timeout'));return
        state['done']=True;report['success']=error is None
        if error:report['error']=str(error)
        (output/'workflow.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report),flush=True);w.editor_dirty=False;w.close();app.exit(0 if error is None else 1)
    def guarded(fn):
        def call(*args):
            try:fn(*args)
            except Exception as error:finish(error)
        return call
    def capture(name):
        w.raise_();loop=QtCore.QEventLoop(w);QtCore.QTimer.singleShot(250,loop.quit);loop.exec()
        if w.transport=='frame-bridge':pix=w.grab()
        else:
            origin=w.mapToGlobal(QtCore.QPoint(0,0));pix=w.screen().grabWindow(0,origin.x(),origin.y(),w.width(),w.height())
        check(name+' screenshot saved',pix.save(str(output/(name+'.png'))))
    @guarded
    def imported(result):
        check('native CAD import succeeds',result['success'])
        state['sourceHash']=hashlib.sha256(source.read_bytes()).hexdigest()
        def choose_order():
            dialog=app.activeModalWidget()
            try:
                check('real mesh order dialog opens',isinstance(dialog,QtWidgets.QDialog))
                order=dialog.findChild(QtWidgets.QComboBox,'cadMeshOrder')
                check('linear remains default',order.currentData()==1)
                order.setCurrentIndex(order.findData(2));dialog.findChild(QtWidgets.QDoubleSpinBox,'cadMaximumSize').setValue(5)
                check('quadratic formulation is explicitly labelled','C3D10' in order.currentText())
                dialog.grab().save(str(output/'order-dialog.png'))
                dialog.findChild(QtWidgets.QDialogButtonBox).button(QtWidgets.QDialogButtonBox.StandardButton.Ok).click()
            except Exception as error:
                state['dialogError']=str(error)
                if dialog:dialog.reject()
        QtCore.QTimer.singleShot(100,choose_order);w.mesh_action.trigger()
        if state.get('dialogError'):raise ValueError(state['dialogError'])
        check('quadratic meshing runs in background',w.busy and w.cancel_action.isEnabled())
    @guarded
    def meshed(result):
        check('native quadratic meshing completes',result['success'])
        scene=w.model_scene;mesh=w.cad_mesh;report['mesh']={'nodes':len(scene['nodes']),'elements':len(scene['elements']),'parts':len(scene['cadMesh']['parts'])}
        check('all original ten-node cells retained',all(e['vtkCellType']==24 and len(e['nodeIds'])==10 for e in scene['elements']))
        check('VTK receives quadratic tetrahedra',w.mapper.GetInput().GetCellType(0)==24 and w.mapper.GetInput().GetCell(0).GetNumberOfPoints()==10)
        check('analysis and configuration controls are enabled',w.run_action.isEnabled() and w.configure_action.isEnabled())
        check('mesh export is enabled',w.export_mesh_action.isEnabled())
        frozen=mesh.freeze(output/'frozen')
        check('frozen CAD mesh retains second-order static profile',frozen['elementOrder']==2 and frozen['analysisEligible'] is True)
        check('frozen file inventory verifies',all(hashlib.sha256((output/'frozen'/f['file']).read_bytes()).hexdigest()==f['sha256'] for f in frozen['files']))
        # Source CAD picks still create original-reader node sets with midsides.
        part=scene['cadMesh']['parts'][0];face=part['faceIds'][0]
        w.regions.select({('face',1,face)})
        refs=w.regions.sources('node')
        w.add_cad_region_set('node','QuadraticFace')
        check('quadratic face region includes midsides',next(s['count'] for s in w.model_scene['nodeSets'] if s['name']=='QuadraticFace')>=6)
        check('midside region authoring retains calculation controls',w.quadratic_mesh and w.run_action.isEnabled())
        w.regions.change_view(w.regions.view.findData('cad'));check('CAD view remains available','cad' in w.scene)
        w.regions.change_view(w.regions.view.findData('mesh'));check('quadratic mesh view restores all nodes',w.scene is w.model_scene)
        capture('quadratic')
        target=output/'quadratic-export.inp';before=w.mesh_bytes
        with patch.object(QtWidgets.QFileDialog,'getSaveFileName',return_value=(str(target),'INP')):w.export_mesh_action.trigger()
        check('real export action publishes checked mesh-only INP',target.read_bytes()==before and w.mesh_export_result['originalReadbackPassed'])
        try:
            from mesh_export import publish_mesh
            publish_mesh(before,w.model_scene,target,decode)
        except FileExistsError:check('existing export is preserved',target.read_bytes()==before)
        else:raise ValueError('Existing export overwritten')
        reopened=decode(target)
        check('fresh original INP readback retains all quadratic cells',reopened['elements']==w.model_scene['elements'])
        # Explicit manufactured analytical fixture, validated by the original reader.
        mesh_bytes,spec,geometry=boundary_fixture(w.mesh_bytes,w.model_scene)
        report['geometry']=geometry
        fixture=output/'affine-mesh.inp';fixture.write_bytes(mesh_bytes)
        checked=decode(fixture);checked['cadMesh']=w.model_scene['cadMesh']
        w.mesh_bytes,w.model_scene,w.model_path=mesh_bytes,checked,fixture
        w.definition=spec;w.analysis_valid=False
        w.show_scene(checked,fixture);w.update_model_tree()
        state['export']=target
        def apply_controls():
            dialog=app.activeModalWidget()
            try:
                check('real C3D10 static configuration opens',isinstance(dialog,AnalysisDialog))
                dialog.materials.table.item(0,1).setText('0');dialog.apply()
                check('invalid material blocks quadratic submission',dialog.definition is None and dialog.isVisible() and not w.job.active)
                dialog.materials.table.item(0,1).setText('1000');dialog.apply()
                check('original C3D10 deck validation succeeds',dialog.definition is not None and dialog.validation['success'])
                report['validation']=dialog.validation
            except Exception as error:
                state['dialogError']=str(error)
                if dialog:dialog.reject()
        QtCore.QTimer.singleShot(100,apply_controls);w.configure_action.trigger()
        if state.get('dialogError'):raise ValueError(state['dialogError'])
        check('configured quadratic definition becomes runnable',w.analysis_valid)
        w.run_action.trigger()
        check('native solve disables mesh and region mutation',w.busy and not w.mesh_action.isEnabled() and not w.regions.create.isEnabled())
    @guarded
    def solved(result):
        check('native quadratic CalculiX completes',result['success'] and result['outcome']['solverExecuted'])
        report['job']=result
        scene=decode(Path(result['directory'])/'analysis.frd')
        check('FRD and viewport preserve ten-node quadratic results',len(scene['elements'])==report['mesh']['elements'] and all(e['vtkCellType']==24 and len(e['nodeIds'])==10 for e in scene['elements']) and w.mapper.GetInput().GetCellType(0)==24)
        errors=field_errors(scene);report['errors']=errors
        check('analytical curved-mesh displacement',errors['displacement']<=2e-7 and errors['lateral']<=2e-8)
        check('analytical curved-mesh stress',errors['axialStress']<=1e-4 and errors['otherStress']<=1e-4)
        check('quadratic result contours enabled',w.mapper.GetScalarVisibility()==1)
        frozen=Path(result['inputDirectory'])/'cad';identity=json.loads((frozen/'identity.json').read_text())
        check('submitted job freezes quadratic order and regions',identity['elementOrder']==2 and identity['analysisEligible'] and identity['authoredRegions'][0]['name']=='QuadraticFace')
        check('submitted CAD and mesh hashes verify',all(hashlib.sha256((frozen/f['file']).read_bytes()).hexdigest()==f['sha256'] for f in identity['files']))
        capture('results')
        w.regions.change_view(w.regions.view.findData('cad'));w.regions.change_view(w.regions.view.findData('results'))
        check('quadratic CAD/results switching preserves contours',w.regions.result is not None and w.scene is w.regions.result[0])
        check('source CAD file unchanged',hashlib.sha256(source.read_bytes()).hexdigest()==state['sourceHash'])
        w.editor_dirty=False;w.load(state['export'],as_model=True)
        check('reopened quadratic mesh offers configuration and solve',w.quadratic_mesh and w.run_action.isEnabled() and w.configure_action.isEnabled())
        capture('reopened')
        finish()
    w.cad_completed.connect(imported);w.mesh_completed.connect(meshed)
    w.job.completed.connect(lambda result:QtCore.QTimer.singleShot(250,lambda:solved(result)))
    QtCore.QTimer.singleShot(180000,lambda:finish('Quadratic calculation probe timed out'))
    try:w.start_cad_import(source)
    except Exception as error:finish(error)

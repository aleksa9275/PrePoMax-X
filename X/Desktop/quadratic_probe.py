"""Real mesh-order dialog, quadratic rendering, region/export and admission gates."""
import hashlib,json
from pathlib import Path
from unittest.mock import patch
from PyQt6 import QtCore,QtWidgets


def begin(app,w,source,output):
    from viewport import decode
    from jobs import examples
    from analysis_editor import validate_definition
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
                check('quadratic preview is explicitly labelled','preview' in order.currentText())
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
        check('analysis and configuration controls are disabled',not w.run_action.isEnabled() and not w.configure_action.isEnabled())
        for label,action in [('run',w.run_model),('configure',w.configure_model)]:
            try:action()
            except ValueError:check(label+' cannot bypass quadratic gate',True)
            else:raise ValueError(label+' bypassed quadratic gate')
        check('no solver job was created',w.job.directory is None)
        check('mesh export is enabled',w.export_mesh_action.isEnabled())
        frozen=mesh.freeze(output/'frozen')
        check('frozen CAD mesh retains second-order ineligible profile',frozen['elementOrder']==2 and frozen['analysisEligible'] is False)
        check('frozen file inventory verifies',all(hashlib.sha256((output/'frozen'/f['file']).read_bytes()).hexdigest()==f['sha256'] for f in frozen['files']))
        # Source CAD picks still create original-reader node sets with midsides.
        part=scene['cadMesh']['parts'][0];face=part['faceIds'][0]
        w.regions.select({('face',1,face)})
        refs=w.regions.sources('node')
        w.add_cad_region_set('node','QuadraticFace')
        check('quadratic face region includes midsides',next(s['count'] for s in w.model_scene['nodeSets'] if s['name']=='QuadraticFace')>=6)
        check('region authoring retains the analysis gate',w.quadratic_preview and not w.run_action.isEnabled())
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
        definition=json.loads((examples()/'cube-analysis.json').read_text())
        try:validate_definition(before,definition)
        except ValueError as error:check('original static deck validator independently refuses C3D10','quadratic' in str(error).lower() or 'c3d4' in str(error).lower())
        else:raise ValueError('Static validator admitted quadratic tetrahedra')
        w.editor_dirty=False;w.load(target,as_model=True)
        check('reopened standalone quadratic mesh remains gated',w.quadratic_preview and not w.run_action.isEnabled() and not w.configure_action.isEnabled())
        capture('reopened')
        check('source CAD file unchanged',hashlib.sha256(source.read_bytes()).hexdigest()==state['sourceHash'])
        finish()
    w.cad_completed.connect(imported);w.mesh_completed.connect(meshed)
    QtCore.QTimer.singleShot(180000,lambda:finish('Quadratic preview probe timed out'))
    try:w.start_cad_import(source)
    except Exception as error:finish(error)

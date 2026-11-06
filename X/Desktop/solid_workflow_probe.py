"""Integrated desktop solid formulations, pyramid export, native solve and results."""
import hashlib,json
from pathlib import Path
from unittest.mock import patch
from PyQt6 import QtCore,QtWidgets
from analysis_editor import AnalysisDialog,validate_definition
from solid_formulations import SolidFormulationDialog
from quadratic_analysis import field_errors
from jobs import examples


def begin(app,w,output):
    from viewport import decode
    output.mkdir(parents=True,exist_ok=False)
    report={'success':False,'transport':w.transport,'checks':[],'runs':{}}
    state={'phase':0,'done':False}
    phases=['mixed-solids','pyramid-wedges','pyramid-hexahedrons']
    w.confirm_discard=lambda:True
    def check(name,passed):
        report['checks'].append({'name':name,'passed':bool(passed)})
        if not passed:raise ValueError(name)
    def finish(error=None):
        if state['done']:return
        if w.busy:
            w.cancel_operation();QtCore.QTimer.singleShot(100,lambda:finish(error or 'Timeout'));return
        state['done']=True;report['success']=error is None
        if error:report['error']=str(error)
        (output/'workflow.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'success':report['success'],'transport':w.transport,'checks':len(report['checks']),'error':report.get('error')}),flush=True)
        w.editor_dirty=False;w.close();app.exit(0 if error is None else 1)
    def guarded(fn):
        def call(*args):
            try:fn(*args)
            except Exception as error:finish(error)
        return call
    def apply_controls():
        dialog=app.activeModalWidget()
        try:
            check('original static editor opens for '+state['name'],isinstance(dialog,AnalysisDialog))
            if state['phase']:
                combo=dialog.findChild(QtWidgets.QComboBox,'pyramidConversion')
                check('pyramid conversion requires an explicit choice',combo is not None and combo.currentData() is None)
                combo.setCurrentIndex(combo.findData('wedges' if state['phase']==1 else 'hexahedrons'))
            dialog.apply()
            check('original deck validates '+state['name'],dialog.definition is not None and dialog.validation['success'])
        except Exception as error:
            state['dialogError']=str(error)
            if dialog:dialog.reject()
    @guarded
    def prepare():
        phase=state['phase'];name=phases[phase];state['name']=name
        fixture='mixed-solids' if phase==0 else 'mixed-pyramids'
        mesh=examples()/(fixture+'.inp');spec=json.loads((examples()/(fixture+'.json')).read_text())
        if phase:spec.pop('pyramidConversion')
        w.editor_dirty=False;w.load(mesh,as_model=True,definition=spec)
        state['sourceHash']=hashlib.sha256(mesh.read_bytes()).hexdigest()
        state['sourcePath']=mesh
        if phase==0:
            original=w.mesh_bytes;before=w.model_scene
            invalid=[b['formulation'] for b in before['elementBlocks']];invalid[0]='C3D20'
            try:w.change_formulations(invalid)
            except ValueError:check('incompatible formulation preserves original mesh and state',w.mesh_bytes==original and w.model_scene is before)
            else:raise ValueError('Incompatible element topology accepted')
            def choose():
                dialog=app.activeModalWidget()
                try:
                    check('real solid formulation dialog opens',isinstance(dialog,SolidFormulationDialog))
                    replacements={'C3D8':'C3D8R','C3D8R':'C3D8I','C3D8I':'C3D8','C3D20':'C3D20R','C3D20R':'C3D20','C3D10':'C3D10T','C3D10T':'C3D10'}
                    for combo in dialog.choices:combo.setCurrentIndex(combo.findData(replacements.get(combo.currentData(),combo.currentData())))
                    dialog.accept()
                except Exception as error:
                    state['dialogError']=str(error)
                    if dialog:dialog.reject()
            QtCore.QTimer.singleShot(100,choose);w.formulation_action.trigger()
            if state.get('dialogError'):raise ValueError(state['dialogError'])
            check('formulation edit retains coordinates and engineering connectivity',w.model_scene['nodes']==before['nodes'] and w.model_scene['elements']==before['elements'])
            check('all ten original solid formulations remain explicit',len({b['formulation'] for b in w.model_scene['elementBlocks']})==10 and w.mesh_bytes!=original)
            check('formulation edit requires revalidation',not w.analysis_valid and w.editor_dirty and w.regions.result is None)
        else:
            try:validate_definition(w.mesh_bytes,spec)
            except ValueError:check(name+' refuses implicit pyramid conversion',True)
            else:raise ValueError('Pyramid conversion was selected implicitly')
        # Actual original wedge VTK permutations must reach the native grid.
        grid=w.mapper.GetInput()
        points=w.model_scene['nodes'];ids={n['id']:i for i,n in enumerate(points)}
        check(name+' VTK uses original per-family point ordering',all(
            [grid.GetCell(i).GetPointId(j) for j in range(grid.GetCell(i).GetNumberOfPoints())]==[ids[n] for n in e['vtkNodeIds']]
            for i,e in enumerate(w.model_scene['elements'])))
        QtCore.QTimer.singleShot(100,apply_controls);w.configure_action.trigger()
        if state.get('dialogError'):raise ValueError(state['dialogError'])
        check(name+' configured model can run',w.analysis_valid)
        state['expected']=w.model_scene;state['submitted']=w.mesh_bytes
        w.run_action.trigger()
        check(name+' active job freezes formulation editing',w.busy and not w.formulation_action.isEnabled())
    @guarded
    def solved(result):
        name=state['name'];phase=state['phase']
        check(name+' native solve completes',result['success'] and result['outcome']['solverExecuted'])
        scene=decode(Path(result['directory'])/'analysis.frd');expected=state['expected']
        normalize=lambda elements:{e['id']:(e['vtkCellType'],e['nodeIds'],e['vtkNodeIds']) for e in elements}
        check(name+' original result IDs and topology match model',normalize(scene['elements'])==normalize(expected['elements']))
        errors=field_errors(scene)
        check(name+' analytical displacement and stress',errors['displacement']<=1e-9 and errors['lateral']<=1e-10 and errors['axialStress']<=1e-4 and errors['otherStress']<=1e-5)
        check(name+' force equilibrium',max(map(abs,errors['forceResultant'].values()))<=1e-5)
        check(name+' original nodal histories decode',decode_histories(Path(result['directory'])/'analysis.dat'))
        inputs=Path(result['inputDirectory']);identity=json.loads((inputs/'input-identity.json').read_text())
        definition=json.loads((inputs/'analysis.json').read_text())
        check(name+' submitted mesh and definition hashes verify',hashlib.sha256((inputs/'mesh.inp').read_bytes()).hexdigest()==identity['meshSha256'] and (inputs/'mesh.inp').read_bytes()==state['submitted'] and hashlib.sha256((inputs/'analysis.json').read_bytes()).hexdigest()==identity['analysisSha256'])
        if phase:
            mode='wedges' if phase==1 else 'hexahedrons'
            check(name+' original collapsed solver topology is retained',definition['pyramidConversion']==mode and {e['type'] for e in scene['solverElements']}==({'LinearWedgeElement','ParabolicWedgeElement'} if phase==1 else {'LinearHexaElement','ParabolicHexaElement'}))
        check(name+' result contours are displayed',w.mapper.GetScalarVisibility()==1 and 'fields' in w.scene)
        report['runs'][name]={'nodes':len(scene['nodes']),'elements':len(scene['elements']),'errors':errors,'job':result,'types':sorted({e['type'] for e in scene['elements']})}
        w.raise_();app.processEvents()
        if w.transport=='frame-bridge':picture=w.grab()
        else:
            origin=w.mapToGlobal(QtCore.QPoint(0,0));picture=w.screen().grabWindow(0,origin.x(),origin.y(),w.width(),w.height())
        check(name+' results captured',picture.save(str(output/(name+'.png'))))
        target=output/(name+'-export.inp')
        with patch.object(QtWidgets.QFileDialog,'getSaveFileName',return_value=(str(target),'INP')):w.export_mesh_action.trigger()
        check(name+' original mesh-only export retains all nodes/formulations',target.read_bytes()==state['submitted'] and w.mesh_export_result['originalReadbackPassed'])
        w.editor_dirty=False;w.load(target,as_model=True,definition=definition)
        check(name+' exported mesh reopens for configuration',w.configure_action.isEnabled() and normalize(w.model_scene['elements'])==normalize(expected['elements']))
        check(name+' source fixture remains byte-identical',hashlib.sha256(state['sourcePath'].read_bytes()).hexdigest()==state['sourceHash'])
        state['phase']+=1
        if state['phase']==len(phases):finish()
        else:QtCore.QTimer.singleShot(150,prepare)
    def decode_histories(path):
        from viewport import run_reader,ROOT
        from jobs import resources
        import sys
        command=[str(resources()/'hosts/results/PrePoMaxX.InspectResults')] if getattr(sys,'frozen',False) else ['dotnet',str(ROOT/'X/Results/Inspect/bin/Release/net10.0/PrePoMaxX.InspectResults.dll')]
        return bool(run_reader([*command,'inspect-dat',str(path)])['histories'])
    w.job.completed.connect(lambda result:QtCore.QTimer.singleShot(250,lambda:solved(result)))
    QtCore.QTimer.singleShot(240000,lambda:finish('Solid workflow timed out'))
    QtCore.QTimer.singleShot(0,prepare)

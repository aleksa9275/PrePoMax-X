"""Real discrete/cross-family jobs, original fields and owned mesh editing."""
import hashlib
import json
import math
from pathlib import Path
from PyQt6 import QtCore,QtWidgets
from unittest.mock import patch
from analysis_editor import AnalysisDialog
from jobs import examples
from element_family_fixtures import CASES
from results_tools import read_histories,export_histories

def verify(case,scene,history,check):
    metrics={};frames=[f for f in scene.get('fields',[]) if f['name']=='DISP']
    if case=='spring-ground':
        check('ground spring omitted from FRD without fabricated values',scene['emptyResultMesh'] and not scene['nodes'] and not scene['fields'] and scene['OriginalElementCount']==1)
    else:check(case+' nodal results decoded',bool(frames))
    if case in ('spring-pair','spring-axial','spring-ground','gap-compression'):
        h=next(h for h in history['histories'] if h['BaseSetName']=='TIP' and h['FieldName']=='DISPLACEMENTS' and h['ComponentName']=='U1')
        value=h['values'][-1];expected=-.01 if case=='gap-compression' else .01
        metrics={'tipDisplacement':value,'expected':expected,'error':abs(value-expected)}
        check(case+' independent force/stiffness displacement',metrics['error']<1e-8)
    elif case=='mass-spring-frequency':
        expected=[2*math.sqrt(1000/2)*math.sin((2*i-1)*math.pi/18)/(2*math.pi) for i in (1,2)]
        actual=[f['time'] for f in frames];metrics={'expectedHz':expected,'actualHz':actual}
        check('four-mass chain independent eigenfrequencies',len(actual)==2 and all(abs(a-b)<=1e-6 for a,b in zip(actual,expected)))
        check('mass records remain distinct from emitted spring topology',scene['OriginalElementCount']==8 and len(scene['elements'])==4)
    elif case=='mass-spring-transient':
        index=scene['nodeIdsInValueOrder'].index(2);error=max(abs(f['components']['U1'][index]-.01*(1-math.cos(math.sqrt(500)*f['time']))) for f in frames)
        metrics={'timeStep':.005,'maximumDisplacementError':error,'analyticalModel':'m=2,k=1000,F=10 step load'}
        check('single-mass transient analytical displacement at all frames',len(frames)==40 and error<5e-5)
        check('original transient velocities retained',any(f['name']=='VELO' for f in scene['fields']))
    elif case=='mixed-solid-springs':
        frame=frames[-1];nodes={n['id']:n for n in scene['nodes']};error=max(abs(frame['components']['U1'][i]-.1*(nodes[n]['x']+1)) for i,n in enumerate(scene['nodeIdsInValueOrder']))
        metrics={'maximumDisplacementError':error,'expected':'u1=0.1*(x+1), k_solid=k_springs=1000'}
        check('shared-node solid/spring analytical series stiffness',error<1e-8)
    elif case.endswith('-frequency'):
        metrics={'frequenciesHz':[f['time'] for f in frames]}
        check(case+' three positive original modes',len(frames)==3 and all(f['time']>0 and f['stepType']=='Frequency' for f in frames))
        if case=='axisymmetric-frequency':check('axisymmetric original mode scaling remains explicit',scene['AxisymmetricScalingApplied'])
    elif case=='beam-transient':
        metrics={'frames':len(frames),'datasets':history['DataSetCount']}
        check('expanded line implicit transient and long histories',len(frames)==80 and history['DataSetCount']>256)
    return metrics

def begin(app,w,output):
    from viewport import decode
    output.mkdir(parents=True,exist_ok=False);state={'index':0,'done':False};report={'success':False,'transport':w.transport,'checks':[],'runs':{}}
    w.confirm_discard=lambda:True
    def check(name,value):
        report['checks'].append({'name':name,'passed':bool(value)})
        if not value:raise ValueError(name)
    def finish(error=None):
        if state['done']:return
        if w.busy:w.cancel_operation();QtCore.QTimer.singleShot(100,lambda:finish(error or 'Timeout'));return
        state['done']=True;w.result_tools.toggle(False);report['success']=error is None
        if error:report['error']=str(error)
        (output/'workflow.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'success':report['success'],'checks':len(report['checks']),'error':report.get('error')}),flush=True)
        w.editor_dirty=False;w.close();app.exit(0 if error is None else 1)
    def guarded(fn):
        def call(*args):
            try:fn(*args)
            except Exception as error:finish(error)
        return call
    def controls():
        dialog=app.activeModalWidget()
        try:
            check(state['case']+' editor opens',isinstance(dialog,AnalysisDialog));dialog.apply();check(state['case']+' original controls validate',dialog.definition is not None)
        except Exception as error:
            state['dialogError']=str(error)
            if dialog:dialog.reject()
    @guarded
    def prepare():
        case=CASES[state['index']];state['case']=case;mesh=examples()/(case+'.inp');spec=json.loads(mesh.with_suffix('.json').read_text());w.editor_dirty=False;w.load(mesh,as_model=True,definition=spec)
        state['hash']=hashlib.sha256(w.mesh_bytes).hexdigest();state['model']=w.model_scene
        QtCore.QTimer.singleShot(100,controls);w.configure_model()
        if state.get('dialogError'):raise ValueError(state['dialogError'])
        w.run_action.trigger();check(case+' job starts',w.busy)
    @guarded
    def solved(result):
        case=state['case'];directory=Path(result['directory'])
        check(case+' frozen source mesh retained',hashlib.sha256(w.mesh_bytes).hexdigest()==state['hash'])
        if case=='beam-modal-transient':
            check('original modal beam failure is explicit and preserves model',not result['success'] and result['state']=='Failed' and w.scene is w.model_scene and w.model_scene is state['model'])
            metrics={'originalFailureRetained':True,'nativeExit':result['outcome'].get('exitCode'),'originalWindowsExit':5,'numericalAcceptance':False}
        else:
            check(case+' native job completes',result['success']);scene=decode(directory/'analysis.frd')
            history=read_histories(directory/'analysis.dat') if not case.endswith('-frequency') else None
            metrics=verify(case,scene,history,check)
            check(case+' scene displayed',w.scene is w.model_scene if scene['emptyResultMesh'] else w.scene['SourceSha256']==scene['SourceSha256'])
            if history:export_histories(output/(case+'-histories.csv'),history['histories'])
            if scene['fields']:
                w.result_tools.deformed.setChecked(True);w.result_tools.scale.setValue(10);w.fit();app.processEvents()
            if w.transport=='frame-bridge':picture=w.grab()
            else:
                origin=w.mapToGlobal(QtCore.QPoint(0,0));picture=w.screen().grabWindow(0,origin.x(),origin.y(),w.width(),w.height())
            check(case+' viewport captured',picture.save(str(output/(case+'.png'))))
        with patch.object(QtWidgets.QFileDialog,'getSaveFileName',return_value=(str(output/(case+'-export.inp')),'INP')):w.export_mesh_action.trigger()
        check(case+' original mesh export/reopen',w.mesh_export_result['originalReadbackPassed'])
        report['runs'][case]={'job':result,'metrics':metrics};state['index']+=1
        if state['index']==len(CASES):mesh_edits();finish()
        else:QtCore.QTimer.singleShot(50,prepare)
    def mesh_edits():
        w.editor_dirty=False;w.load(examples()/'cube-mesh.inp',as_model=True,definition=json.loads((examples()/'cube-analysis.json').read_text()));raw=w.mesh_bytes
        w.apply_mesh_edit({'operation':'rotate','axis':[0,0,1],'center':[0,0,0],'angleDegrees':90});rotated=w.mesh_bytes
        check('original mesh rotation applied',raw!=rotated and max(n['x'] for n in w.model_scene['nodes'])<1e-12)
        w.undo_mesh_edit();check('mesh undo restores exact bytes',w.mesh_bytes==raw);w.redo_mesh_edit();check('mesh redo restores exact bytes',w.mesh_bytes==rotated);w.undo_mesh_edit()
        w.apply_mesh_edit({'operation':'surface','nodeSet':'Z0','formulation':'S4'});check('surface extraction preserves original face nodes',{n['id'] for n in w.model_scene['nodes']}=={1,2,3,4})
        w.apply_mesh_edit({'operation':'edge','nodeSet':'Y0','formulation':'B31'});check('edge extraction creates beam topology',w.model_scene['elementBlocks'][0]['formulation']=='B31' and w.model_scene['elements'][0]['nodeIds']==[1,2])
        w.undo_mesh_edit();w.undo_mesh_edit();check('extraction undo retains original analysis and mesh',w.mesh_bytes==raw and len(w.definition['sections'])==1)
    w.job.completed.connect(lambda result:QtCore.QTimer.singleShot(200,lambda:solved(result)))
    QtCore.QTimer.singleShot(300000,lambda:finish('Workflow timeout'));QtCore.QTimer.singleShot(0,prepare)

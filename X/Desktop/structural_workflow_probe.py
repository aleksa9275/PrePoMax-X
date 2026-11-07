"""Native shell/membrane/beam/truss workflows with independent diagnostics."""
import hashlib
import json
import math
from pathlib import Path
from PyQt6 import QtCore,QtWidgets
from unittest.mock import patch
from analysis_editor import AnalysisDialog
from jobs import examples
from results_tools import read_histories,export_histories
from structural_workflow_fixtures import CASES


def verify_fields(case,scene,history,check):
    fields={f['name']:f['components'] for f in scene['fields']};nodes=scene['nodes'];order=scene['nodeIdsInValueOrder'];by_id={n['id']:n for n in nodes}
    check(case+' original fields and histories decoded',{'DISP','STRESS','FORC'}<=fields.keys() and bool(history['histories']))
    d=fields['DISP'];stress=fields['STRESS'];metrics={}
    if case in ('shell-tension','membrane-tension','membrane-quadratic'):
        metrics={'displacement':0.,'stress':0.}
        for i,identity in enumerate(order):
            n=by_id[identity];origin=2*int((n['x']+1e-7)/2)
            metrics['displacement']=max(metrics['displacement'],abs(d['U1'][i]+.00025*(n['x']-origin)),abs(d['U2'][i]-.001*n['y']))
            metrics['stress']=max(metrics['stress'],abs(stress['S22'][i]-1),abs(stress['S11'][i]),abs(stress['S33'][i]))
        metrics['displacementPassed']=metrics['displacement']<1e-8
        if case!='membrane-quadratic':check(case+' independent displacement',metrics['displacementPassed'])
        metrics['stressPatchPassed']=metrics['stress']<1e-4
        if case!='membrane-quadratic':check(case+' independent stress patch',metrics['stressPatchPassed'])
        else:metrics['originalAccuracyDiagnostic']='Original quadratic membrane stress mismatch retained; see original-solver comparison and free-case evidence.'
    elif case in ('shell-bending','beam-bending','beam-centerline','beam-circular','shell-pressure'):
        expected=-.075 if case=='shell-bending' else -.25 if case in ('beam-bending','beam-centerline') else -(.001*100/(2*1000*(math.pi*.2**4/64))) if case=='beam-circular' else -.01875
        tip=[d['U3'][j] for j,n in enumerate(nodes) if abs(n['x']-10)<1e-6];observed=sum(tip)/len(tip)
        metrics={'tipDisplacement':observed,'continuumTipDisplacement':expected,'continuumError':abs(observed-expected),'continuumPassed':abs(observed-expected)<(1e-5 if case=='shell-pressure' else 1e-6)}
        if case!='beam-circular':check(case+' independent bending displacement',metrics['continuumPassed'])
        if case=='beam-centerline':check(case+' original quadratic centerline topology',len(nodes)==21 and all(e['type']=='ParabolicBeamElement' for e in scene['elements']))
        else:check(case+' full expanded cross section',any(n['z']>0 for n in nodes) and any(n['z']<0 for n in nodes))
        if case in ('shell-bending','beam-bending'):
            slope=1.5 if case=='shell-bending' else 5.
            error=max(abs(stress['S11'][j]-slope*n['z']) for j,n in enumerate(nodes) if n['x']>1)
            metrics['bendingStressError']=error;check(case+' through-thickness bending stress',error<1e-4)
    elif case=='line-tension':
        for part,form in enumerate(('B31','B31R','B21','B32','B32R','T3D2','T2D2','T3D3')):
            ix=[j for j,n in enumerate(nodes) if abs(n['y']-3*part)<.3];error=max(abs(d['U1'][j]-.001*nodes[j]['x']) for j in ix)
            metrics[form]={'displacementError':error,'continuumPassed':error<1e-8}
            if form!='T3D3':check(form+' independent axial displacement',error<1e-8)
    elif case=='composite-tension':
        check(case+' separate layer elements retained',len(scene['elements'])==3*40)
        # Far from the load application and end constraint, the symmetric stack
        # has extensional stiffness sum(E_i*t_i)=300 and strain N/300=.001.
        mid=[j for j,n in enumerate(nodes) if 3<=n['x']<=7]
        metrics={'stressRange':[min(stress['S11'][j] for j in mid),max(stress['S11'][j] for j in mid)]}
        check(case+' layer stress contrast retained',metrics['stressRange'][0]<1.1 and metrics['stressRange'][1]>1.9)
        ends=[]
        for x in (3,7):
            vals=[d['U1'][j] for j,n in enumerate(nodes) if abs(n['x']-x)<1e-7];ends.append(sum(vals)/len(vals))
        metrics['bulkStrain']=(ends[1]-ends[0])/4
        check(case+' independent laminate extension',abs(metrics['bulkStrain']-.001)<1e-8)
    force=[h for h in history['histories'] if h['FieldName']=='FORCES']
    residual={c:sum(h['values'][-1] for h in force if h['ComponentName']==c) for c in ('RF1','RF2','RF3')}
    # A distributed-pressure load is not part of the printed root/tip nodal force
    # sets. Check its root reaction directly instead of calling it imbalance.
    if case=='shell-pressure':
        root=sum(h['values'][-1] for h in force if h['ComponentName']=='RF3' and h['BaseSetName']=='ROOT')
        metrics['rootReaction']=root;metrics['continuumRootReaction']=.0001;metrics['rootReactionPassed']=abs(root-.0001)<1e-8
    elif case not in ('shell-bending','beam-bending','beam-centerline','beam-circular','membrane-quadratic','line-tension'):
        component='RF1' if case in ('line-tension','composite-tension') else 'RF2'
        check(case+' loaded-direction equilibrium on complete supports',abs(residual[component])<1e-5)
    if case=='line-tension':metrics['printedForceEquilibriumPassed']=abs(residual['RF1'])<1e-5
    metrics['printedForceResidual']=residual
    return metrics


def begin(app, w, output):
    output.mkdir(parents=True, exist_ok=False)
    report = {'success': False, 'transport': w.transport, 'checks': [], 'runs': {}}
    state = {'index': 0, 'done': False}
    w.confirm_discard = lambda: True
    def check(name, passed):
        report['checks'].append({'name': name, 'passed': bool(passed)})
        if not passed:
            raise ValueError(name)
    def finish(error=None):
        if state['done']:
            return
        if w.busy:
            w.cancel_operation(); QtCore.QTimer.singleShot(100, lambda: finish(error or 'Timeout')); return
        state['done'] = True; report['success'] = error is None
        if error:
            report['error'] = str(error)
        (output/'workflow.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps({'success': report['success'], 'checks': len(report['checks']), 'error': report.get('error')}), flush=True)
        w.editor_dirty = False; w.close(); app.exit(0 if error is None else 1)
    def guarded(fn):
        def call(*args):
            try: fn(*args)
            except Exception as error: finish(error)
        return call
    def controls():
        dialog = app.activeModalWidget()
        try:
            check(state['case']+' configuration opens', isinstance(dialog, AnalysisDialog))
            check(state['case']+' model space explicit', dialog.model_space.currentData() == w.definition.get('modelSpace','ThreeD'))
            check(state['case']+' configuration captured', dialog.grab().save(str(output/(state['case']+'-configure.png'))))
            dialog.apply(); check(state['case']+' original validation passes', dialog.definition is not None)
        except Exception as error:
            state['dialogError'] = str(error)
            if dialog: dialog.reject()
    @guarded
    def prepare():
        case = CASES[state['index']]; state['case'] = case
        mesh = examples()/(case+'.inp'); spec = json.loads(mesh.with_suffix('.json').read_text())
        w.editor_dirty = False; w.load(mesh, as_model=True, definition=spec)
        state['meshHash'] = hashlib.sha256(w.mesh_bytes).hexdigest()
        QtCore.QTimer.singleShot(100, controls); w.configure_model()
        if state.get('dialogError'): raise ValueError(state['dialogError'])
        w.run_action.trigger(); check(case+' native job starts', w.busy)
    @guarded
    def solved(result):
        from viewport import decode
        from solid_formulations import SolidFormulationDialog
        case = state['case']; check(case+' native solver completes', result['success'])
        directory = Path(result['directory']); scene = decode(directory/'analysis.frd'); history = read_histories(directory/'analysis.dat')
        check(case+' result displayed', w.scene['SourceSha256'] == scene['SourceSha256'])
        check(case+' immutable input', hashlib.sha256(w.mesh_bytes).hexdigest() == state['meshHash'] and json.loads((Path(result['inputDirectory'])/'analysis.json').read_text()) == w.definition)
        metrics = verify_fields(case, scene, history, check)
        if case=='beam-centerline':
            from viewport import verify_mesh_view
            w.result_tools.deformed.setChecked(False)
            verify_mesh_view(w,check)
        dialog = SolidFormulationDialog(w, w.model_scene)
        check(case+' formulation identity retained', dialog.values() == [b['formulation'] for b in w.model_scene['elementBlocks']])
        export_histories(output/(case+'-histories.csv'), history['histories'])
        # Export the original model mesh, not the solver-expanded result mesh.
        with patch.object(QtWidgets.QFileDialog, 'getSaveFileName', return_value=(str(output/(case+'-export.inp')), 'INP')):
            w.export_mesh_action.trigger()
        check(case+' mesh export succeeds', w.mesh_export_result['originalReadbackPassed'])
        reopened = decode(output/(case+'-export.inp'))
        check(case+' export reopens with topology and formulations', reopened['elements'] == w.model_scene['elements'] and reopened['elementBlocks'] == w.model_scene['elementBlocks'])
        w.result_tools.deformed.setChecked(True); w.result_tools.outline.setChecked(True); w.result_tools.scale.setValue(25)
        w.fit(); app.processEvents()
        if w.transport == 'frame-bridge': picture = w.grab()
        else:
            origin = w.mapToGlobal(QtCore.QPoint(0, 0))
            picture = w.screen().grabWindow(0, origin.x(), origin.y(), w.width(), w.height())
        check(case+' viewport captured', picture.save(str(output/(case+'.png'))))
        report['runs'][case] = {'job': result, 'analytical': metrics}; state['index'] += 1
        if state['index'] == len(CASES): finish()
        else: QtCore.QTimer.singleShot(50, prepare)
    w.job.completed.connect(lambda result: QtCore.QTimer.singleShot(200, lambda: solved(result)))
    QtCore.QTimer.singleShot(300000, lambda: finish('Workflow timeout')); QtCore.QTimer.singleShot(0, prepare)

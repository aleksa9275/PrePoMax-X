"""Radiation, amplitude and thermal-stress milestones through real desktop jobs."""
import hashlib
import json
import math
from pathlib import Path
from PyQt6 import QtCore,QtWidgets
from analysis_editor import AnalysisDialog
from jobs import examples
from results_tools import HistoryDialog,read_histories,export_histories
from thermomechanical_workflow_fixtures import CASES


def radiation_temperature():
    lo,hi=20.,100.
    for _ in range(100):
        mid=(lo+hi)/2
        if .01*(100-mid)>.8*5.670374419e-11*((mid+273.15)**4-(20+273.15)**4):lo=mid
        else:hi=mid
    return (lo+hi)/2


def verify_fields(case,scene,history,check):
    nodes={n['id']:n for n in scene['nodes']};order=scene['nodeIdsInValueOrder'];fields=scene['fields'];errors={}
    if case in ('radiation-cooling','temperature-conductivity','amplitude-heating'):
        temperatures=[f for f in fields if f['name']=='NDTEMP'];check(case+' thermal fields decoded',bool(temperatures))
        error=0
        for f in temperatures if case=='amplitude-heating' else temperatures[-1:]:
            for n,value in zip(order,f['components']['T']):
                z=nodes[n]['z'];t=f['time']
                if case=='radiation-cooling':expected=100+(radiation_temperature()-100)*z
                elif case=='temperature-conductivity':expected=100*(math.sqrt(1+3*z)-1)
                else:
                    expected=10+(2*t*t if t<=.5 else 4*t-2*t*t-1)
                error=max(error,abs(value-expected))
        bound=.002 if case=='temperature-conductivity' else .0501 if case=='amplitude-heating' else 5e-5
        check(case+' independent heat equation temperature',error<=bound);errors['temperatureMaximumError']=error;errors['temperatureBound']=bound
        if case=='amplitude-heating':
            check('thermal pulse has twenty original frames',len(temperatures)==20)
            check('thermal pulse integrated energy reaches 11 C',all(abs(v-11)<1e-5 for v in temperatures[-1]['components']['T']))
            # Original backward Euler heat integration: T_n = T_(n-1)+dt*P(t_n)/(rho*c).
            previous=10.;last=0.;discrete_error=0
            for f in temperatures:
                t=f['time'];power=4*t if t<=.5 else 4-4*t;previous+=(t-last)*power;last=t
                discrete_error=max(discrete_error,max(abs(v-previous) for v in f['components']['T']))
            check('thermal pulse original time-discrete energy balance',discrete_error<1e-5);errors['timeDiscreteMaximumError']=discrete_error
        elif case=='radiation-cooling':
            expected=.01*(100-radiation_temperature());reactions={name:sum(h['values'][-1] for h in history['histories'] if h['ComponentName']=='RFL' and h['BaseSetName']==name) for name in ('TOP','BOTTOM')}
            check('radiation Stefan Boltzmann boundary energy balance',abs(reactions['TOP']+expected)<1e-6 and abs(reactions['BOTTOM']-expected)<1e-6)
        else:check('temperature table has forty stored frames',len(temperatures)==40)
        return errors
    displacements=[f for f in fields if f['name']=='DISP'];error=0;stress_error=0
    for f in displacements:
        t=f['time'];a=2*t if t<=.5 else 1.5-t
        for i,n in enumerate(order):
            point=nodes[n]
            for d,axis in enumerate(('x','y','z')):
                expected=(.1 if d==0 else -.03)*point[axis]*a if case=='amplitude-force' else (.001 if case=='free-expansion' else .0013 if d<2 else 0)*point[axis]*t
                error=max(error,abs(f['components']['U'+str(d+1)][i]-expected))
        stress=next(s for s in fields if s['name']=='STRESS' and s['incrementId']==f['incrementId'])
        for c in ('S11','S22','S33','S12','S13','S23'):
            expected=100*a if case=='amplitude-force' and c=='S11' else -t if case=='restrained-expansion' and c=='S33' else 0
            stress_error=max(stress_error,max(abs(v-expected) for v in stress['components'][c]))
    check(case+' analytical displacement at every node/time',error<2e-7)
    stress_bound=.005 if case=='amplitude-force' else 5e-5 if case=='restrained-expansion' else 1e-8
    check(case+' original nodal stress extrapolation',stress_error<=stress_bound)
    point_error=0
    for h in history['histories']:
        if h['FieldName']!='STRESSES':continue
        for t,v in zip(h['time'],h['values']):
            a=2*t if t<=.5 else 1.5-t;expected=100*a if case=='amplitude-force' and h['ComponentName']=='S11' else -t if case=='restrained-expansion' and h['ComponentName']=='S33' else 0
            point_error=max(point_error,abs(v-expected))
    check(case+' integration point stress matches independent solution',point_error<1e-4)
    check(case+' original linear static final frame retained',len(displacements)==1)
    return {'displacementMaximumError':error,'nodalStressMaximumError':stress_error,'integrationPointStressMaximumError':point_error}


def begin(app,w,output):
    output.mkdir(parents=True,exist_ok=False);report={'success':False,'transport':w.transport,'checks':[],'runs':{}};state={'index':0,'done':False};w.confirm_discard=lambda:True
    def check(name,passed):
        report['checks'].append({'name':name,'passed':bool(passed)})
        if not passed:raise ValueError(name)
    def finish(error=None):
        if state['done']:return
        if w.busy:w.cancel_operation();QtCore.QTimer.singleShot(100,lambda:finish(error or 'Timeout'));return
        state['done']=True;report['success']=error is None
        if error:report['error']=str(error)
        (output/'workflow.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'success':report['success'],'checks':len(report['checks']),'error':report.get('error')}),flush=True)
        w.editor_dirty=False;w.close();app.exit(0 if error is None else 1)
    def guarded(fn):
        def call(*args):
            try:fn(*args)
            except Exception as error:finish(error)
        return call
    def controls():
        d=app.activeModalWidget();case=state['case']
        try:
            check(case+' configuration opens',isinstance(d,AnalysisDialog))
            d.tabs.setCurrentIndex(13 if case.startswith('amplitude') else 14 if case.endswith('expansion') else 12 if case=='temperature-conductivity' else 10)
            d.show();app.processEvents();check(case+' configuration captured',d.grab().save(str(output/(case+'-configure.png'))))
            d.apply();check(case+' original validation passes',d.definition is not None and d.validation['success'])
        except Exception as error:
            state['dialogError']=str(error)
            if d:d.reject()
    @guarded
    def prepare():
        case=CASES[state['index']];state['case']=case;mesh=examples()/(case+'.inp');spec=json.loads(mesh.with_suffix('.json').read_text());w.editor_dirty=False
        w.load(mesh,as_model=True,definition=spec);state['meshHash']=hashlib.sha256(w.mesh_bytes).hexdigest();QtCore.QTimer.singleShot(100,controls);w.configure_model(10 if case in CASES[:3] else 14)
        if state.get('dialogError'):raise ValueError(state['dialogError'])
        w.run_action.trigger();check(case+' native job starts',w.busy)
    @guarded
    def solved(result):
        from viewport import decode
        case=state['case'];check(case+' native solver completed',result['success']);directory=Path(result['directory']);scene=decode(directory/'analysis.frd');h=read_histories(directory/'analysis.dat')
        check(case+' original fields displayed',w.scene['SourceSha256']==scene['SourceSha256'])
        check(case+' source mesh preserved',hashlib.sha256(w.mesh_bytes).hexdigest()==state['meshHash'])
        check(case+' original job definition frozen',json.loads((Path(result['inputDirectory'])/'analysis.json').read_text())==w.definition)
        metrics=verify_fields(case,scene,h,check);deck=(directory/'analysis.inp').read_text()
        if case.startswith('amplitude'):check(case+' original named amplitude emitted','*Amplitude, Name=Pulse' in deck and 'Amplitude=Pulse' in deck)
        if case.endswith('expansion'):check(case+' original expansion/initial/defined keywords emitted','*Expansion, Zero=20' in deck and '*Initial conditions, Type=Temperature' in deck and '*Temperature' in deck)
        if case=='radiation-cooling':check('original radiation and physical constants emitted','*Radiate' in deck and '*Physical constants' in deck)
        if case=='amplitude-heating':
            d=HistoryDialog(w,directory/'analysis.dat',h);d.show();app.processEvents();d.series.setCurrentIndex(next(i for i,v in enumerate(h['histories']) if v['ComponentName']=='T'))
            check('time-variable heat history graph/table',d.table.model().rowCount()==20 and d.grab().save(str(output/'pulse-history.png')))
            export_histories(output/'pulse-histories.csv',h['histories']);d.close()
        if case=='amplitude-force':
            w.frames.setCurrentIndex(0);w.result_tools.deformed.setChecked(True);w.result_tools.scale.setValue(1);w.result_tools.outline.setChecked(True)
            check('time-variable force deformed frame available',w.result_tools.selected_displacement() is not None)
        w.fit();app.processEvents();check(case+' viewport captured',w.grab().save(str(output/(case+'.png'))))
        report['runs'][case]={'job':result,**metrics};state['index']+=1
        if state['index']==len(CASES):finish()
        else:QtCore.QTimer.singleShot(50,prepare)
    w.job.completed.connect(lambda result:QtCore.QTimer.singleShot(200,lambda:solved(result)));QtCore.QTimer.singleShot(300000,lambda:finish('Workflow timeout'));QtCore.QTimer.singleShot(0,prepare)

"""Original transient procedures against an independent axial oscillator."""
import hashlib
import json
import math
from pathlib import Path
from PyQt6 import QtCore,QtWidgets
from analysis_editor import AnalysisDialog
from jobs import examples
from results_tools import HistoryDialog,read_histories,export_histories
from dynamics_workflow_fixtures import CASES,PERIOD,DT,OMEGA,ZETA


def response(t,damped):
    z=ZETA if damped else 0.;w=OMEGA;wd=w*math.sqrt(1-z*z);p=1/(1000*PERIOD);q=-2*z*p/w
    a=-q;b=(-p+z*w*a)/wd;e=math.exp(-z*w*t);c=math.cos(wd*t);s=math.sin(wd*t)
    return p*t+q+e*(a*c+b*s),p+e*((-z*w*a+wd*b)*c+(-z*w*b-wd*a)*s)


def discrete_response(damped):
    m=.001/3;k=1000.;c=2*ZETA*OMEGA*m if damped else 0.;u=v=a=0.;result={}
    for n in range(1,65):
        t=n*DT;up=u+DT*v+DT*DT*.25*a;vp=v+DT*.5*a
        a=(t/PERIOD-c*vp-k*up)/(m+c*.5*DT+k*.25*DT*DT)
        u=up+.25*DT*DT*a;v=vp+.5*DT*a;result[n]=(u,v)
    return result


def verify_fields(case,scene,history,check):
    damped=case.endswith('damped');modal=case.startswith('modal');nodes={n['id']:n for n in scene['nodes']};order=scene['nodeIdsInValueOrder']
    fields=[f for f in scene['fields'] if f['mode']<=0];disp=[f for f in fields if f['name']=='DISP'];velocity=[f for f in fields if f['name']=='VELO']
    check(case+' sixty-four physical displacement and velocity frames',len(disp)==len(velocity)==64)
    check(case+' physical step identity',all(f['stepId']==(2 if modal else 1) for f in disp))
    discrete=discrete_response(damped);errors={'displacement':0.,'velocity':0.,'continuumDisplacement':0.,'continuumVelocity':0.}
    for name,frames,component,which in [('displacement',disp,'U1',0),('velocity',velocity,'V1',1)]:
        for f in frames:
            exact=response(f['time'],damped)[which];expected=exact if modal else discrete[f['incrementId']][which]
            for n,value in zip(order,f['components'][component]):
                x=nodes[n]['x'];errors[name]=max(errors[name],abs(value-x*expected));errors['continuum'+name.title()]=max(errors['continuum'+name.title()],abs(value-x*exact))
        check(case+' independent '+name,errors[name]<(2e-8 if which==0 else 2e-5))
    check(case+' time history velocities decoded',any(h['ComponentName']=='V1' for h in history['histories']))
    check(case+' basis tables explicitly separated',len(history.get('ExcludedBasisTables',[]))==(4 if modal else 0))
    if not modal:
        energy_error=0.
        for f in fields:
            if f['name']=='ENER':
                u=discrete[f['incrementId']][0];energy_error=max(energy_error,max(abs(v-.5*1000*u*u) for v in f['components']['ENER']))
        check(case+' strain energy agrees with oscillator',energy_error<1e-7);errors['strainEnergyMaximumError']=energy_error
    history_error=0.
    for h in history['histories']:
        if h['ComponentName'] not in ('U1','V1'):continue
        which=0 if h['ComponentName']=='U1' else 1
        for t,inc,value in zip(h['time'],h['IncrementIds'],h['values']):
            expected=(response(t,damped) if modal else discrete[inc])[which]*nodes[h['Id']]['x']
            history_error=max(history_error,abs(value-expected))
    check(case+' original DAT matches independent response',history_error<2e-5);errors['historyMaximumError']=history_error
    return errors


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
            check(case+' configuration opens',isinstance(d,AnalysisDialog));d.tabs.setCurrentIndex(d.tabs.count()-1);app.processEvents()
            check(case+' controls captured',d.grab().save(str(output/(case+'-configure.png'))));d.apply();check(case+' original validation passes',d.definition is not None and d.validation['success'])
        except Exception as error:
            state['dialogError']=str(error)
            if d:d.reject()
    @guarded
    def prepare():
        case=CASES[state['index']];state['case']=case;mesh=examples()/(case+'.inp');spec=json.loads(mesh.with_suffix('.json').read_text());w.editor_dirty=False
        w.load(mesh,as_model=True,definition=spec);state['meshHash']=hashlib.sha256(w.mesh_bytes).hexdigest();QtCore.QTimer.singleShot(100,controls);w.configure_model()
        if state.get('dialogError'):raise ValueError(state['dialogError'])
        w.run_action.trigger();check(case+' native job starts',w.busy)
    @guarded
    def solved(result):
        from viewport import decode
        case=state['case'];check(case+' native solver completed',result['success']);directory=Path(result['directory']);scene=decode(directory/'analysis.frd');history=read_histories(directory/'analysis.dat')
        check(case+' result displayed',w.scene['SourceSha256']==scene['SourceSha256']);check(case+' source mesh retained',hashlib.sha256(w.mesh_bytes).hexdigest()==state['meshHash'])
        check(case+' job inputs frozen',json.loads((Path(result['inputDirectory'])/'analysis.json').read_text())==w.definition)
        metrics=verify_fields(case,scene,history,check);deck=(directory/'analysis.inp').read_text()
        if case.startswith('modal'):check(case+' stored original frequency basis',directory.joinpath('analysis.eig').stat().st_size>0 and 'Storage=Yes' in deck and '*Modal dynamics' in deck)
        else:check(case+' original implicit keyword','*Dynamic' in deck)
        w.frames.setCurrentIndex(w.frames.count()-1);w.result_tools.deformed.setChecked(True);w.result_tools.outline.setChecked(True);w.result_tools.scale.setValue(10)
        check(case+' deformed physical frame',w.result_tools.selected_displacement() is not None)
        before=w.frames.currentIndex();w.result_tools.animation.setCurrentIndex(0);w.result_tools.tick();check(case+' physical animation advances',w.frames.currentIndex()!=before)
        check(case+' animation stays in physical step',w.result_tools.selected_displacement()['stepId']==(2 if case.startswith('modal') else 1) and w.result_tools.selected_displacement()['mode']<=0)
        w.frames.setCurrentIndex(w.frames.count()-1)
        d=HistoryDialog(w,directory/'analysis.dat',history);d.show();app.processEvents();d.series.setCurrentIndex(next(i for i,h in enumerate(history['histories']) if h['ComponentName']=='V1' and h['Id']==2))
        check(case+' velocity history graph and table',d.table.model().rowCount()==64 and d.grab().save(str(output/(case+'-history.png'))));export_histories(output/(case+'-histories.csv'),history['histories']);d.close()
        w.fit();app.processEvents();check(case+' viewport captured',w.grab().save(str(output/(case+'.png'))));report['runs'][case]={'job':result,**metrics};state['index']+=1
        if state['index']==len(CASES):finish()
        else:QtCore.QTimer.singleShot(50,prepare)
    w.job.completed.connect(lambda result:QtCore.QTimer.singleShot(200,lambda:solved(result)));QtCore.QTimer.singleShot(300000,lambda:finish('Workflow timeout'));QtCore.QTimer.singleShot(0,prepare)

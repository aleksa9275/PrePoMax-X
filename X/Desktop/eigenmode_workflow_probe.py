"""Combined frequency/buckling/result-tools milestone integration through real UI/jobs."""
import csv
import hashlib
import json
import math
from pathlib import Path
from PyQt6 import QtCore,QtWidgets
from jobs import examples
from analysis_editor import AnalysisDialog,validate_definition
from results_tools import HistoryDialog,read_histories,export_histories


def begin(app,w,output):
    output.mkdir(parents=True,exist_ok=False)
    report={'success':False,'transport':w.transport,'checks':[],'runs':{}}
    phases=[('frequency','axial-frequency'),('buckling','column-buckling'),('histories','plastic-tension')]
    state={'index':0,'done':False};w.confirm_discard=lambda:True
    def check(name,passed):
        report['checks'].append({'name':name,'passed':bool(passed)})
        if not passed:raise ValueError(name)
    def finish(error=None):
        if state['done']:return
        if w.busy:
            w.cancel_operation();QtCore.QTimer.singleShot(100,lambda:finish(error or 'Timeout'));return
        state['done']=True;w.result_tools.toggle(False);report['success']=error is None
        if error:report['error']=str(error)
        (output/'workflow.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'success':report['success'],'checks':len(report['checks']),'error':report.get('error')}),flush=True)
        w.editor_dirty=False;w.close();app.exit(0 if error is None else 1)
    def guarded(fn):
        def call(*args):
            try:fn(*args)
            except Exception as error:finish(error)
        return call
    def apply_controls():
        dialog=app.activeModalWidget();case=state['case']
        try:
            check(case+' original configure dialog opens',isinstance(dialog,AnalysisDialog))
            if case!='histories':
                dialog.analysis_kind.setCurrentIndex(dialog.analysis_kind.findData(case));dialog.mode_count.setValue(3)
                check(case+' static time controls disabled',not dialog.step_fields['timePeriod'].isEnabled())
            dialog.apply();check(case+' original model/deck validation passes',dialog.definition is not None and dialog.validation['success'])
        except Exception as error:
            state['dialogError']=str(error)
            if dialog:dialog.reject()
    @guarded
    def prepare():
        case,fixture=phases[state['index']];state['case']=case
        spec=json.loads((examples()/(fixture+'.json')).read_text());mesh=examples()/(fixture+'.inp')
        w.editor_dirty=False;w.load(mesh,as_model=True,definition=spec);state['sourceHash']=hashlib.sha256(w.mesh_bytes).hexdigest()
        if case=='frequency':
            invalid=json.loads(json.dumps(spec));invalid['materials'][0].pop('density')
            try:validate_definition(w.mesh_bytes,invalid)
            except ValueError:check('missing modal density rejected before job',True)
            else:raise ValueError('Frequency admitted without density')
        if case=='buckling':
            invalid=json.loads(json.dumps(spec));invalid['step']['loads']=[]
            try:validate_definition(w.mesh_bytes,invalid)
            except ValueError:check('missing reference load rejected before buckling job',True)
            else:raise ValueError('Buckling admitted without reference load')
        QtCore.QTimer.singleShot(100,apply_controls);w.configure_model(9 if case!='histories' else 6)
        if state.get('dialogError'):raise ValueError(state['dialogError'])
        w.run_action.trigger();check(case+' native job starts',w.busy)
    @guarded
    def solved(result):
        from viewport import decode
        case=state['case'];check(case+' native solver completed',result['success'])
        scene=decode(Path(result['directory'])/'analysis.frd');check(case+' results displayed',w.scene['SourceSha256']==scene['SourceSha256'])
        check(case+' submitted mesh preserved',hashlib.sha256(w.mesh_bytes).hexdigest()==state['sourceHash'])
        inputs=Path(result['inputDirectory']);frozen=json.loads((inputs/'analysis.json').read_text())
        check(case+' frozen original definition matches editor',frozen==w.definition)
        deck=(Path(result['directory'])/'analysis.inp').read_text();frames=list(dict.fromkeys((f['stepId'],f['incrementId'],f['time']) for f in scene['fields']))
        if case=='frequency':
            check('original frequency keyword reaches solver','*Frequency\n' in deck and '*Density\n' in deck)
            check('three modal result frames',len(frames)==3 and all(f['stepType']=='Frequency' for f in scene['fields']))
            check('first rod frequency matches analytical 250 Hz',abs(frames[0][2]-250)<.001)
            first=next(f for f in scene['fields'] if f['name']=='DISP' and f['incrementId']==1)
            node_map={n['id']:n for n in scene['nodes']};expected_shape=[math.sin(math.pi*node_map[n]['z']/2) for n in scene['nodeIdsInValueOrder']];actual=first['components']['U3']
            amplitude=sum(a*b for a,b in zip(actual,expected_shape))/sum(b*b for b in expected_shape)
            shape_error=max(abs(a-amplitude*b) for a,b in zip(actual,expected_shape))/max(map(abs,actual))
            check('first rod mode shape matches analytical sine',shape_error<1e-5)
            check('frequency displayed in Hz','Hz' in w.frames.itemText(0))
        elif case=='buckling':
            check('original buckle keyword reaches solver','*Buckle\n' in deck)
            factors=[f[2] for f in frames if f[2]!=0];expected=math.pi**2*1000*(1*.5**3/12)/(4*10**2*.1)
            check('three buckling modes plus reference load state',len(factors)==3 and frames[0][2]==0)
            check('first column factor agrees with slender Euler approximation',abs(factors[0]-expected)/expected<.02)
            check('buckling reference and load factor labelled','reference load state' in w.frames.itemText(0) and 'factor' in w.frames.itemText(1))
        else:
            snapshot=read_histories(Path(result['directory'])/'analysis.dat');check('original DAT reader returns histories',len(snapshot['histories'])>0)
            dialog=HistoryDialog(w,Path(result['directory'])/'analysis.dat',snapshot);dialog.show();app.processEvents()
            series=next(i for i,h in enumerate(snapshot['histories']) if h['ComponentName']=='U3' and h['BaseSetName']=='TOP')
            dialog.series.setCurrentIndex(series);selected=snapshot['histories'][series]
            check('history table preserves original times and values',dialog.table.model().rowCount()==len(selected['time']) and selected['time'][-1]==1)
            check('history graph rendered',dialog.grab().save(str(output/'history-plot.png')))
            csv_path=output/'histories.csv';export_histories(csv_path,snapshot['histories']);before=csv_path.read_bytes()
            rows=list(csv.DictReader(csv_path.open()));check('CSV contains every original history value',len(rows)==sum(len(h['values']) for h in snapshot['histories']))
            check('CSV roundtrips original numeric values',float(rows[0]['time'])==snapshot['histories'][0]['time'][0] and float(rows[0]['value'])==snapshot['histories'][0]['values'][0])
            try:export_histories(csv_path,snapshot['histories'])
            except FileExistsError:check('CSV refuses existing destination',csv_path.read_bytes()==before)
            else:raise ValueError('CSV overwrote destination')
            dialog.close()
        tools=w.result_tools;w.frames.setCurrentIndex(w.frames.count()-1);original=json.dumps(w.scene,sort_keys=True)
        tools.scale.setValue(1 if case=='buckling' else .01 if case=='frequency' else 2);tools.deformed.setChecked(True);tools.outline.setChecked(True)
        displacement=tools.selected_displacement();order={n:i for i,n in enumerate(w.scene['nodeIdsInValueOrder'])};scale=tools.scale.value()
        error=max(abs(w.grid.GetPoint(i)[d]-(n[a]+scale*displacement['components'][f'U{d+1}'][order[n['id']]])) for i,n in enumerate(w.scene['nodes']) for d,a in enumerate(('x','y','z')))
        check(case+' displayed deformation maps original node values',error<1e-12)
        check(case+' undeformed reference outline visible',tools.reference.GetVisibility()==1)
        tools.animation.setCurrentIndex(1);tools.play.setChecked(True);tools.tick()
        check(case+' shape animation advances',tools.timer.isActive() and tools.phase!=1)
        tools.toggle(False);check(case+' stopping restores selected deformation',tools.phase==1 and not tools.timer.isActive())
        tools.animation.setCurrentIndex(0);index=w.frames.currentIndex();tools.play.setChecked(True);tools.tick();check(case+' increment animation advances',w.frames.currentIndex()==(index+1)%w.frames.count());tools.toggle(False)
        check(case+' display operations preserve authoritative results',json.dumps(w.scene,sort_keys=True)==original)
        tools.deformed.setChecked(False);check(case+' undeformed coordinates restored',all(w.grid.GetPoint(i)==tuple(n[a] for a in ('x','y','z')) for i,n in enumerate(w.scene['nodes'])))
        w.frames.setCurrentIndex(0 if case=='frequency' else 1 if case=='buckling' else w.frames.count()-1)
        tools.deformed.setChecked(True);w.fit();w.raise_();app.processEvents();check(case+' display captured',w.grab().save(str(output/(case+'.png'))))
        report['runs'][case]={'frames':frames,'job':result,'displayDeformationError':error}
        state['index']+=1
        if state['index']==len(phases):finish()
        else:QtCore.QTimer.singleShot(100,prepare)
    w.job.completed.connect(lambda result:QtCore.QTimer.singleShot(250,lambda:solved(result)))
    QtCore.QTimer.singleShot(300000,lambda:finish('Combined workflow timeout'));QtCore.QTimer.singleShot(0,prepare)

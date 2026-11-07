"""Thermal milestones through original services, native jobs and desktop results."""
import copy
import csv
import hashlib
import json
from pathlib import Path
from PyQt6 import QtCore,QtWidgets
from analysis_editor import AnalysisDialog,validate_definition
from jobs import examples
from results_tools import HistoryDialog,read_histories,export_histories
from thermal_workflow_fixtures import CASES


def verify_fields(case,scene,history,check):
    """Independent 1D heat equation and energy balance for documented fixtures."""
    nodes={n['id']:n for n in scene['nodes']};order=scene['nodeIdsInValueOrder']
    temperatures=[f for f in scene['fields'] if f['name']=='NDTEMP']
    check(case+' original temperature, flux and reaction fields',set(f['name'] for f in scene['fields'])=={'NDTEMP','FLUX','RFL'})
    error=0
    for f in temperatures:
        for identity,actual in zip(order,f['components']['T']):
            z=nodes[identity]['z']
            expected=100*z if case=='steady-conduction' else 10+f['time'] if case=='transient-heating' else 10*z if case in ('surface-heating','nodal-heating') else 4*z*(1-z) if case=='body-heating' else 100-(160/3)*z
            error=max(error,abs(actual-expected))
    check(case+' analytical temperature at every stored node/time',error<=5e-5)
    last=temperatures[-1]['time'];flux=next(f for f in reversed(scene['fields']) if f['name']=='FLUX')
    expected_flux=-100 if case=='steady-conduction' else -10 if case in ('surface-heating','nodal-heating') else 160/3 if case=='film-cooling' else 0
    flux_error=max(abs(v-(8*nodes[n]['z']-4 if case=='body-heating' else expected_flux)) for n,v in zip(order,flux['components']['F3']))
    # Original solver extrapolation rounds nodal heat flux. Integration-point DAT
    # values are checked separately below; original extrapolation stays unchanged.
    check(case+' original extrapolated nodal heat flux',flux_error<=.006)
    check(case+' transverse heat flux zero',max(abs(v) for c in ('F1','F2') for v in flux['components'][c])<1e-9)
    h=history['histories'];check(case+' original temperature histories',any(r['FieldName']=='TEMPERATURES' for r in h))
    if case=='transient-heating':
        check('twenty transient increments retained',len(temperatures)==20 and last==1)
        check('temperature histories match heat capacity energy balance',all(abs(v-(10+t))<1e-5 for r in h if r['ComponentName']=='T' for t,v in zip(r['time'],r['values'])))
        check('insulated transient reaction flow zero',max(abs(v) for r in h if r['ComponentName']=='RFL' for v in r['values'])<1e-9)
    else:
        reactions={name:sum(r['values'][-1] for r in h if r['BaseSetName']==name and r['ComponentName']=='RFL') for name in ('TOP','BOTTOM')}
        expected={'steady-conduction':(100,-100),'surface-heating':(10,-10),'nodal-heating':(10,-10),'body-heating':(-11/3,-11/3),'film-cooling':(-160/3,160/3)}[case]
        check(case+' original nodal heat flow sum',max(abs(reactions[n]-v) for n,v in zip(('TOP','BOTTOM'),expected))<1e-4)
        if case=='body-heating':
            # Stored RFL omits the consistent body-source contribution on
            # prescribed boundary nodes (Q * boundary-cell volume / 6 per end).
            # The independent balance includes that source; preserve raw RFL.
            check('body source heat balance with boundary nodal contribution',abs(sum(reactions.values())-2*(8*.25/6)+8)<1e-4)
        # Check exact uniform integration-point flux cases against an independent
        # gradient, while retaining the quadratic body-heating varying flux.
        dat_flux=[r for r in h if r['FieldName']=='HEAT_FLUX']
        check(case+' integration point flux identities retained',len(dat_flux)>0 and all(r['IntegrationPoint'] is not None for r in dat_flux))
        if case!='body-heating':check(case+' integration point heat flux',max(abs(r['values'][-1]-(expected_flux if r['ComponentName']=='Q3' else 0)) for r in dat_flux)<1e-4)
    return {'temperatureMaximumError':error,'nodalFluxMaximumError':flux_error,'frames':len(temperatures),'histories':len(h)}


def begin(app,w,output):
    output.mkdir(parents=True,exist_ok=False);report={'success':False,'transport':w.transport,'checks':[],'runs':{}}
    state={'index':0,'done':False};w.confirm_discard=lambda:True
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
        dialog=app.activeModalWidget();case=state['case']
        try:
            check(case+' thermal configuration opens',isinstance(dialog,AnalysisDialog) and dialog.analysis_kind.currentData()=='heat-transfer')
            check(case+' thermal time and material controls enabled',dialog.step_fields['timePeriod'].isEnabled() and dialog.thermal_properties.isEnabled() and not dialog.loads.isEnabled())
            dialog.apply();check(case+' original validation passes',dialog.definition is not None and dialog.validation['success'])
        except Exception as error:
            state['dialogError']=str(error)
            if dialog:dialog.reject()
    @guarded
    def prepare():
        case=CASES[state['index']];state['case']=case
        spec=json.loads((examples()/(case+'.json')).read_text());mesh=examples()/(case+'.inp')
        w.editor_dirty=False;w.load(mesh,as_model=True,definition=spec);state['meshHash']=hashlib.sha256(w.mesh_bytes).hexdigest()
        if case=='transient-heating':
            for label,alter in [('missing heat capacity',lambda v:v['materials'][0].pop('specificHeat')),('missing initial temperature',lambda v:v['step']['thermal'].pop('initialTemperature'))]:
                invalid=copy.deepcopy(spec);alter(invalid)
                try:validate_definition(w.mesh_bytes,invalid)
                except ValueError:check(label+' refused before solve',True)
                else:raise ValueError(label+' admitted')
        QtCore.QTimer.singleShot(100,controls);w.configure_model(10)
        if state.get('dialogError'):raise ValueError(state['dialogError'])
        w.run_action.trigger();check(case+' native job starts',w.busy)
    @guarded
    def solved(result):
        from viewport import decode
        case=state['case'];check(case+' native solver completes',result['success'])
        directory=Path(result['directory']);scene=decode(directory/'analysis.frd');history=read_histories(directory/'analysis.dat')
        check(case+' native fields displayed',w.scene['SourceSha256']==scene['SourceSha256'])
        check(case+' mesh remains unchanged',state['meshHash']==hashlib.sha256(w.mesh_bytes).hexdigest())
        check(case+' submitted definition frozen',json.loads((Path(result['inputDirectory'])/'analysis.json').read_text())==w.definition)
        metrics=verify_fields(case,scene,history,check)
        check(case+' every thermal frame selectable',w.frames.count()==metrics['frames'])
        check(case+' thermal fields available in viewport',any('NDTEMP' in w.fields.itemText(i) for i in range(w.fields.count())))
        # Pick a transported ID using the actual result point array.
        identity=w.grid.GetPointData().GetGlobalIds().GetValue(0);check(case+' original picking IDs retained',identity==scene['nodes'][0]['id'])
        check(case+' thermal coordinates remain undeformed',all(w.grid.GetPoint(i)==tuple(n[a] for a in ('x','y','z')) for i,n in enumerate(scene['nodes'])))
        if case=='transient-heating':
            dialog=HistoryDialog(w,directory/'analysis.dat',history);dialog.show();app.processEvents()
            i=next(i for i,h in enumerate(history['histories']) if h['ComponentName']=='T');dialog.series.setCurrentIndex(i)
            check('temperature history graph/table has twenty values',dialog.table.model().rowCount()==20)
            check('thermal history graph captured',dialog.grab().save(str(output/'thermal-history.png')))
            destination=output/'temperature-histories.csv';export_histories(destination,history['histories']);rows=list(csv.DictReader(destination.open()))
            check('thermal history CSV retains samples',len(rows)==sum(len(h['values']) for h in history['histories']))
            dialog.close()
            w.result_tools.play.setChecked(True);w.result_tools.tick();check('thermal increment animation advances',w.frames.currentIndex()==0);w.result_tools.toggle(False);w.frames.setCurrentIndex(w.frames.count()-1)
        w.fit();app.processEvents();check(case+' viewport captured',w.grab().save(str(output/(case+'.png'))))
        report['runs'][case]={'job':result,**metrics};state['index']+=1
        if state['index']==len(CASES):finish()
        else:QtCore.QTimer.singleShot(50,prepare)
    w.job.completed.connect(lambda result:QtCore.QTimer.singleShot(200,lambda:solved(result)))
    QtCore.QTimer.singleShot(300000,lambda:finish('Thermal workflow timeout'));QtCore.QTimer.singleShot(0,prepare)

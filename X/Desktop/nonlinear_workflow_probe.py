"""Integrated mechanical editor, original loads/materials, nonlinear frames and results."""
import hashlib,json
from pathlib import Path
from PyQt6 import QtCore,QtWidgets
from analysis_editor import AnalysisDialog,validate_definition
from jobs import examples


def frame_fields(scene,increment=None):
    increment=max(f['incrementId'] for f in scene['fields']) if increment is None else increment
    return {f['name']:f['components'] for f in scene['fields'] if f['incrementId']==increment}


def analytical_errors(scene,case):
    fields=frame_fields(scene);order=scene['nodeIdsInValueOrder'];nodes={n['id']:n for n in scene['nodes']}
    if case.startswith('pressure'):
        excluded={n for e in scene['elements'] if e['type']=='ParabolicPyramidElement' for n in e['nodeIds']} if case=='pressure-wedges' else set()
        valid=[i for i,n in enumerate(order) if n not in excluded]
        errors={'displacement':max(abs(fields['DISP']['U3'][i]-.001*nodes[order[i]]['z']) for i in valid),
            'stress':max(abs(fields['STRESS']['S33'][i]-1) for i in valid)}
        if excluded:
            errors['originalQuadraticPyramidWedge']={'displacement':max(abs(fields['DISP']['U3'][i]-.001*nodes[n]['z']) for i,n in enumerate(order) if n in excluded),
                'stress':max(abs(fields['STRESS']['S33'][i]-1) for i,n in enumerate(order) if n in excluded)}
        return errors
    if case=='gravity':
        return {'displacement':max(abs(fields['DISP']['U3'][i]-.001*(nodes[n]['z']-nodes[n]['z']**2/2)) for i,n in enumerate(order)),
            'stress':max(abs(fields['STRESS']['S33'][i]-(1-nodes[n]['z'])) for i,n in enumerate(order))}
    if case=='plastic':
        stress=(1+100*.01)/(1+100/1000);plastic=.01-stress/1000
        return {'displacement':max(abs(fields['DISP']['U3'][i]-.01*nodes[n]['z']) for i,n in enumerate(order)),
            'stress':max(abs(v-stress) for v in fields['STRESS']['S33']),
            'plasticStrain':max(abs(v-plastic) for v in fields['PE']['PE'])}
    return {'displacement':max(abs(fields['DISP']['U3'][i]-.2*nodes[n]['z']) for i,n in enumerate(order)),
        'nonlinearStress':max(fields['STRESS']['S33'])}


def begin(app,w,output):
    from viewport import decode
    output.mkdir(parents=True,exist_ok=False)
    report={'success':False,'transport':w.transport,'checks':[],'runs':{},'openCorrectnessChecks':[]}
    phases=[('pressure-hexahedrons','pressure-solids'),('pressure-wedges','pressure-solids'),('gravity','gravity-column'),('plastic','plastic-tension'),('finite','finite-tension')]
    state={'index':0,'done':False}
    w.confirm_discard=lambda:True
    def check(name,passed):
        report['checks'].append({'name':name,'passed':bool(passed)})
        if not passed:raise ValueError(name)
    def finish(error=None):
        if state['done']:return
        if w.busy:
            w.cancel_operation();QtCore.QTimer.singleShot(100,lambda:finish(error or 'Timeout'));return
        state['done']=True;report['success']=error is None;report['fullyNumericallyAccepted']=not report['openCorrectnessChecks']
        if error:report['error']=str(error)
        (output/'workflow.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'success':report['success'],'checks':len(report['checks']),'error':report.get('error'),'openCorrectnessChecks':report['openCorrectnessChecks']}),flush=True)
        w.editor_dirty=False;w.close();app.exit(0 if error is None else 1)
    def guarded(fn):
        def call(*args):
            try:fn(*args)
            except Exception as error:finish(error)
        return call
    def apply_controls():
        dialog=app.activeModalWidget();case=state['case']
        try:
            check(case+' original mechanical editor opens',isinstance(dialog,AnalysisDialog))
            if case.startswith('pressure'):
                dialog.pyramid_conversion.setCurrentIndex(dialog.pyramid_conversion.findData('wedges' if case.endswith('wedges') else 'hexahedrons'))
                check(case+' pressure row retains named boundary region',dialog.pressures.values()[0]['nodeSet']=='TOP')
            elif case=='gravity':
                dialog.mechanical_properties.table.item(0,1).setText('=1/1000')
                dialog.gravity.table.item(0,4).setText('=1000')
            elif case=='plastic':
                dialog.plastic_curve.table.item(0,1).setText('=1')
                dialog.plastic_curve.table.item(1,1).setText('=2')
            else:dialog.nonlinear.setChecked(True)
            dialog.apply()
            check(case+' original material/load/step validation passes',dialog.definition is not None and dialog.validation['success'])
        except Exception as error:
            state['dialogError']=str(error)
            if dialog:dialog.reject()
    @guarded
    def prepare():
        case,fixture=phases[state['index']];state['case']=case
        mesh=examples()/(fixture+'.inp');spec=json.loads((examples()/(fixture+'.json')).read_text())
        if case=='finite':spec['step']['nonlinearGeometry']=False
        w.editor_dirty=False;w.load(mesh,as_model=True,definition=spec)
        state['meshHash']=hashlib.sha256(w.mesh_bytes).hexdigest();state['mesh']=w.model_scene
        if case=='gravity':
            invalid=json.loads(json.dumps(spec));invalid['materials'][0].pop('density')
            try:validate_definition(w.mesh_bytes,invalid)
            except ValueError:check('gravity without density is rejected before a job',True)
            else:raise ValueError('Gravity admitted without density')
        if case=='plastic':
            invalid=json.loads(json.dumps(spec));invalid['materials'][0]['plasticCurve'][1][1]='0'
            try:validate_definition(w.mesh_bytes,invalid)
            except ValueError:check('invalid plastic curve is rejected before a job',True)
            else:raise ValueError('Unordered plastic curve admitted')
        QtCore.QTimer.singleShot(100,apply_controls);w.configure_action.trigger()
        if state.get('dialogError'):raise ValueError(state['dialogError'])
        check(case+' editor retains the mesh',hashlib.sha256(w.mesh_bytes).hexdigest()==state['meshHash'])
        w.run_action.trigger();check(case+' native job starts',w.busy)
    @guarded
    def solved(result):
        case=state['case'];check(case+' native solver completes',result['success'] and result['outcome']['solverExecuted'])
        scene=decode(Path(result['directory'])/'analysis.frd')
        topology=lambda s:{e['id']:(e['vtkCellType'],e['nodeIds'],e['vtkNodeIds']) for e in s['elements']}
        check(case+' original model/result topology matches',topology(scene)==topology(state['mesh']))
        errors=analytical_errors(scene,case)
        check(case+' analytical axial displacement',errors['displacement']<=1e-8)
        if 'stress' in errors:check(case+' analytical stress',errors['stress']<=1e-4)
        if case=='pressure-wedges':
            discrepancy=errors['originalQuadraticPyramidWedge']
            check('original quadratic-pyramid wedge pressure discrepancy stays visible',discrepancy['stress']>1e-3)
            report['openCorrectnessChecks'].append({'name':'quadratic pyramid converted to wedge under pressure','passed':False,'errors':discrepancy,'scope':'Inherited original solver behavior; hexahedron route passes analytical pressure case'})
        if case=='plastic':check('analytical plastic strain after yield',errors['plasticStrain']<=1e-6)
        inputs=Path(result['inputDirectory']);definition=json.loads((inputs/'analysis.json').read_text());deck=(Path(result['directory'])/'analysis.inp').read_text()
        identity=json.loads((inputs/'input-identity.json').read_text())
        check(case+' frozen input hashes verify',hashlib.sha256((inputs/'mesh.inp').read_bytes()).hexdigest()==identity['meshSha256'] and hashlib.sha256((inputs/'analysis.json').read_bytes()).hexdigest()==identity['analysisSha256'])
        if case.startswith('pressure'):check(case+' original pressure keyword and explicit conversion retained','*Dload' in deck and '_XPressure_' in deck and definition['pyramidConversion']==('wedges' if case.endswith('wedges') else 'hexahedrons'))
        if case=='gravity':check('original density and gravity keywords retained','*Density' in deck and ', Grav,' in deck and definition['materials'][0]['density']=='=1/1000')
        if case=='plastic':check('original plasticity and PE output retained','*Plastic' in deck and 'PEEQ' in deck and len(scene['fields'])>64)
        if case=='finite':check('original NLGEOM keyword changes the calculation',', Nlgeom' in deck and errors['nonlinearStress']>210)
        if case in ('plastic','finite'):
            check(case+' multiple increments are selectable',w.frames.count()==20)
            if case=='plastic':
                index=next(i for i in range(w.fields.count()) if w.fields.itemText(i).startswith('PE / PE'))
                w.fields.setCurrentIndex(index)
            w.frames.setCurrentIndex(0)
            selected=w.grid.GetPointData().GetArray(w.fields.currentData())
            expected='PE' if case=='plastic' else 'DISP';component='PE' if case=='plastic' else 'ALL'
            first=frame_fields(scene,min(f['incrementId'] for f in scene['fields']))[expected][component]
            values={n:v for n,v in zip(scene['nodeIdsInValueOrder'],first)}
            check(case+' first increment maps original nodal values',all(abs(selected.GetValue(i)-values[n['id']])<=1e-12 for i,n in enumerate(w.scene['nodes'])))
            w.frames.setCurrentIndex(w.frames.count()-1)
            if case=='plastic':check('plastic strain grows from zero to yielded result',max(first)==0 and w.grid.GetPointData().GetArray(w.fields.currentData()).GetRange()[1]>.008)
        check(case+' native contours display',w.mapper.GetScalarVisibility()==1)
        report['runs'][case]={'errors':errors,'frames':w.frames.count(),'fields':len(scene['fields']),'nodes':len(scene['nodes']),'elements':len(scene['elements']),'job':result}
        w.raise_();app.processEvents()
        if w.transport=='frame-bridge':image=w.grab()
        else:
            origin=w.mapToGlobal(QtCore.QPoint(0,0));image=w.screen().grabWindow(0,origin.x(),origin.y(),w.width(),w.height())
        check(case+' result captured',image.save(str(output/(case+'.png'))))
        state['index']+=1
        if state['index']==len(phases):finish()
        else:QtCore.QTimer.singleShot(100,prepare)
    w.job.completed.connect(lambda result:QtCore.QTimer.singleShot(250,lambda:solved(result)))
    QtCore.QTimer.singleShot(300000,lambda:finish('Mechanical workflow timeout'))
    QtCore.QTimer.singleShot(0,prepare)

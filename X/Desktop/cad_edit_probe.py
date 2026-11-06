"""Real desktop CAD edit dialogs, STEP exchange, remeshing and native results."""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from unittest.mock import patch
from PyQt6 import QtCore,QtWidgets


def begin(app,w,source,output):
    from viewport import decode
    from jobs import examples
    from cad_document import CadDocument
    output.mkdir(parents=True,exist_ok=False)
    report={'success':False,'transport':w.transport,'checks':[]}
    state={'phase':'initial','done':False,'sourceHash':hashlib.sha256(source.read_bytes()).hexdigest()}
    step=output/'selected.step'
    w.confirm_discard=lambda:True  # Explicit response only in this automated probe.
    def check(name,condition):
        report['checks'].append({'name':name,'passed':bool(condition)})
        if not condition:raise ValueError(name)
    def finish(error=None):
        if state['done']:return
        if w.busy:
            w.cancel_operation();QtCore.QTimer.singleShot(100,lambda:finish(error or 'Probe timed out'));return
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
        check(name+' screenshot',pix.save(str(output/(name+'.png'))))
        if name=='results':
            image=pix.toImage();scale=image.width()/w.width()
            origin=w.vtk.mapTo(w,QtCore.QPoint(0,0));x0,y0=round(origin.x()*scale),round(origin.y()*scale)
            x1=min(image.width(),x0+round(w.vtk.width()*scale*.8));y1=min(image.height(),y0+round(w.vtk.height()*scale))
            check('edited mesh contours are visible on screen',sum(image.pixelColor(x,y).saturation()>140 for x in range(x0,x1,8) for y in range(y0,y1,8))>20)
    def operation(name,values):
        state['operation']=name
        def interact():
            dialog=app.activeModalWidget()
            try:
                check(name+' real dialog opens',isinstance(dialog,QtWidgets.QDialog))
                dialog.findChild(QtWidgets.QComboBox).setCurrentIndex(0)
                for i,value in enumerate(values):dialog.findChild(QtWidgets.QLineEdit,'cadParameter'+str(i)).setText(str(value))
                check(name+' dialog screenshot',dialog.grab().save(str(output/(name+'-dialog.png'))))
                dialog.findChild(QtWidgets.QDialogButtonBox).button(QtWidgets.QDialogButtonBox.StandardButton.Ok).click()
            except Exception as error:
                state['error']=error
                if dialog:dialog.reject()
        QtCore.QTimer.singleShot(100,interact)
        with patch.object(QtWidgets.QFileDialog,'getSaveFileName',return_value=(str(step),'STEP')):
            getattr(w.operations,name+'_action').trigger()
        if state.get('error'):raise state['error']
        check(name+' runs in background',w.busy and not w.open_action.isEnabled() and w.cancel_action.isEnabled())
    @guarded
    def imported(result):
        check('CAD import succeeds',result['success'])
        if state['phase']=='reopen':
            check('exported edited STEP reopens in desktop',len(w.cad_document.parts)==1)
            props=w.cad_document.scene['cad']['parts'][0]['entities']['solid'][0]['properties']
            check('reopened edited solid retains analytical volume',math.isclose(props['volume'][0],1000,rel_tol=1e-12,abs_tol=1e-9))
            check('original external CAD file unchanged',hashlib.sha256(source.read_bytes()).hexdigest()==state['sourceHash'])
            capture('reopened');finish();return
        check('two original CAD parts retained',len(w.cad_document.parts)==2)
        state['originalDocRoot']=w.cad_document.root;w.start_cad_mesh(3)
    @guarded
    def meshed(result):
        check('native C3D4 mesh succeeds',result['success'])
        if state['phase']=='initial':
            state['originalMeshRoot']=w.cad_mesh.root
            w.definition={'placeholder':'discard only after successful edit'};w.analysis_valid=True
            w.regions.refs.add(('face',1,1))
            operation('translate',[7,-3,5]);return
        check('all three edited bodies remesh',len(w.model_scene['cadMesh']['parts'])==3)
        scene=w.model_scene;nodes=scene['nodes'];parts=scene['cadMesh']['parts']
        definition=json.loads((examples()/'cube-analysis.json').read_text())
        definition['materials']=[{'name':'Elastic','youngsModulus':'1000','poissonsRatio':'0'}]
        definition['sections']=[{'name':'Section'+str(i),'material':'Elastic','elementSet':f'PART_{i}_SOLID_1'} for i in range(1,4)]
        constraints=[{'name':'Transverse','nodeSet':'ALL_NODES','displacements':['0','0',None]}]
        for i,part in enumerate(parts,1):
            selected=[n for n in nodes if n['id']>part['nodeOffset'] and (i==len(parts) or n['id']<=parts[i]['nodeOffset'])]
            for label,z in [('Bottom',min(n['z'] for n in selected)),('Top',max(n['z'] for n in selected))]:
                ids=[str(n['id']) for n in selected if abs(n['z']-z)<1e-9]
                name=label+str(i);w.add_named_set('node',name,','.join(ids))
                constraints.append({'name':name,'nodeSet':name,'displacements':[None,None,str(.001*z)]})
        definition['step'].update(constraints=constraints,loads=[],nodalHistorySets=[],elementHistorySets=[])
        w.definition=definition;w.analysis_valid=True
        state.update(document=w.cad_document,mesh=w.cad_mesh,meshBytes=w.mesh_bytes,definition=deepcopy(w.definition),scene=w.scene)
        operation('export',[])
    @guarded
    def operated(result):
        name=state['operation'];check(name+' completes',result['success'])
        if name=='translate':
            check('successful edit releases old geometry and mesh',not state['originalDocRoot'].exists() and not state['originalMeshRoot'].exists())
            check('successful edit clears stale mesh assignments and selection',w.cad_mesh is None and w.model_scene is None and w.definition is None and not w.regions.refs)
            check('new geometry is marked unsaved',w.editor_dirty)
            operation('split',[0,0,15,0,0,1])
        elif name=='split':
            check('split publishes three parts and checked origins',len(w.cad_document.parts)==3 and w.cad_document.edits[-1]['partOrigins']==[1,1,2])
            operation('repair',[1e-6])
        elif name=='repair':
            check('all three geometry edit receipts retained',[e['operation'] for e in w.cad_document.edits]==['translate','split','repair'])
            capture('edited');state['phase']='edited';w.start_cad_mesh(3)
        else:
            report['export']=result['receipt']
            check('STEP export preserves active model and mesh',w.cad_document is state['document'] and w.cad_mesh is state['mesh'] and w.mesh_bytes==state['meshBytes'] and w.definition==state['definition'])
            check('STEP export retains unsaved editing state',w.editor_dirty)
            reopened=CadDocument(step,w.cad_document.tool,decode)
            try:
                props=reopened.scene['cad']['parts'][0]['entities']['solid'][0]['properties']
                check('exported edited part center matches analytical result',all(math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-10) for a,b in zip(props['center_of_mass'],[12,2,10])))
            finally:reopened.close()
            w.run_model()
    @guarded
    def solved(result):
        check('native solver completes edited geometry job',result['success'] and result['outcome']['solverExecuted'])
        report['job']=result;scene=decode(Path(result['directory'])/'analysis.frd')
        fields={f['name']:f['components'] for f in scene['fields']};nodes={n['id']:n for n in scene['nodes']}
        errors=[abs(fields['DISP']['U3'][i]-.001*nodes[n]['z']) for i,n in enumerate(scene['nodeIdsInValueOrder'])]
        report['maximumDisplacementError']=max(errors)
        check('analytical affine displacement at every edited mesh node',max(errors)<=2e-8 and max(map(abs,fields['DISP']['U1']))<=1e-12 and max(map(abs,fields['DISP']['U2']))<=1e-12)
        check('analytical unit axial stress at every edited mesh node',max(abs(v-1) for v in fields['STRESS']['S33'])<=1e-6)
        frozen=Path(result['inputDirectory'])/'cad';identity=json.loads((frozen/'identity.json').read_text())
        check('job freezes all geometry edit receipts and part origins',len(identity['geometryEdits'])==3 and identity['geometryEdits'][1]['partOrigins']==[1,1,2])
        check('job freezes exact original operation inputs and recipes',all((frozen/f'cad-operation-{i:04d}-input.brep').is_file() and (frozen/f'cad-operation-{i:04d}-parameters.txt').is_file() for i in range(1,4)))
        check('all frozen CAD file hashes verify',all(hashlib.sha256((frozen/f['file']).read_bytes()).hexdigest()==f['sha256'] for f in identity['files']))
        w.fields.setCurrentIndex(1);capture('results')
        state['phase']='reopen';w.start_cad_import(step)
    w.cad_completed.connect(imported);w.mesh_completed.connect(meshed);w.operations.completed.connect(operated)
    w.job.completed.connect(lambda r:QtCore.QTimer.singleShot(200,lambda:solved(r)))
    QtCore.QTimer.singleShot(180000,lambda:finish('CAD edit probe timed out'))
    try:w.start_cad_import(source)
    except Exception as error:finish(error)

"""Original CAD PMX -> native edit/save/reopen -> native solver desktop proof."""
import hashlib
import json
from pathlib import Path
from PyQt6 import QtCore, QtWidgets
from pmx_project import PmxDialog


def begin(app, window, source, output):
    output.mkdir(parents=True,exist_ok=False)
    report={'success':False,'transport':window.transport,'checks':[]}
    state={'done':False}
    saved=output/'edited.pmx'
    def check(name,condition):
        report['checks'].append({'name':name,'passed':bool(condition)})
        if not condition:raise ValueError(name)
    def finish(error=None):
        if state['done']:return
        if window.busy:
            window.cancel_operation()
            QtCore.QTimer.singleShot(100,lambda:finish(error or 'Probe timed out'))
            return
        state['done']=True;report['success']=error is None
        if error:report['error']=str(error)
        (output/'workflow.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report),flush=True)
        window.editor_dirty=False;window.close();app.exit(0 if error is None else 1)
    def capture(name):
        window.raise_();app.processEvents()
        if window.transport=='frame-bridge':pixmap=window.grab()
        else:
            origin=window.mapToGlobal(QtCore.QPoint(0,0))
            pixmap=window.screen().grabWindow(0,origin.x(),origin.y(),window.width(),window.height())
        check(name+' capture',pixmap.save(str(output/(name+'.png'))))
    def dialog_edit():
        dialog=app.activeModalWidget()
        try:
            check('real CAD PMX editor opens',isinstance(dialog,PmxDialog))
            dialog.modulus.setText('0')
            check('invalid modulus publishes nothing',dialog.save(saved) is None and not saved.exists())
            dialog.poisson.setText('0.5')
            dialog.modulus.setText('84500.5')
            check('invalid Poisson ratio publishes nothing',dialog.save(saved) is None and not saved.exists())
            dialog.poisson.setText('0.25');dialog.density.setText('8.1e-9')
            dialog.force.setText('-3');dialog.force2.setText('4');dialog.force3.setText('-12')
            if 'X0_Copy' in dialog.session.project['graph']['nodeSets']:
                check('load choices contain only existing node regions',
                      all(dialog.load_region.itemText(i) in dialog.session.project['graph']['nodeSets']
                          for i in range(dialog.load_region.count())))
                dialog.section_region.setCurrentText('SOLID_Copy')
                dialog.load_region.setCurrentText('X0_Copy')
                for name, region in [('X0','X1_Copy'),('Y0','Y0_Copy'),('Z0','Z0_Copy')]:
                    dialog.support_regions[name].setCurrentText(region)
                state['reassigned']=True
            check('PMX editor capture',dialog.grab().save(str(output/'editor.png')))
            receipt=dialog.save(saved)
            check('CAD PMX Save As validates original graph and deck',receipt and receipt['portableReadbackPassed'] and receipt['unchangedGeometryMeshAndHistory'])
            report['write']=receipt
            check('existing PMX destination refused',dialog.save(saved) is None)
            dialog.accept()
        except Exception as error:
            state['error']=error
            if dialog:dialog.reject()
    def solved(result):
        try:
            check('native CAD PMX solve completes',result['success'] and result['outcome']['solverExecuted'])
            report['job']=result
            frozen=Path(result['inputDirectory'])
            check('job freezes exact source PMX including CAD',hashlib.sha256((frozen/'source.pmx').read_bytes()).hexdigest()==report['write']['outputSha256'])
            check('original tetrahedral results loaded',len(window.scene['elements'])==843 and all(e['vtkCellType']==10 for e in window.scene['elements']))
            check('source CAD and model remain after solve',window.cad_document is not None and window.model_path==saved)
            window.regions.view.setCurrentIndex(window.regions.view.findData('cad'))
            window.regions.view.setCurrentIndex(window.regions.view.findData('results'))
            check('CAD and result views survive reopen and solve',window.current_path.name=='analysis.frd' and window.regions.result is not None)
            window.fields.setCurrentIndex(1)
            check('original result field maps to contour and legend',window.mapper.GetScalarVisibility() and window.legend.GetVisibility())
            capture('result')
            check('original PMX stays unchanged',hashlib.sha256(source.read_bytes()).hexdigest()==state['sourceHash'])
            finish()
        except Exception as error:finish(error)
    try:
        state['sourceHash']=hashlib.sha256(source.read_bytes()).hexdigest()
        window.open_pmx(source)
        original=window.pmx_session
        check('original CAD/C3D4 project opens',original.cad_model and len(window.model_scene['nodes'])==276 and len(window.model_scene['elements'])==843)
        check('saved CAD is available without remeshing',window.cad_document is not None and not window.mesh_action.isEnabled() and not window.regions.create.isVisible())
        window.regions.view.setCurrentIndex(window.regions.view.findData('cad'))
        check('source CAD faces display',len(window.cad_faces)==6 and 'cad' in window.scene)
        capture('cad')
        QtCore.QTimer.singleShot(100,dialog_edit);window.edit_pmx_action.trigger()
        if state.get('error'):raise state['error']
        window.open_pmx(saved)
        check('saved equations reopen in fresh session',window.pmx_session is not original and window.pmx_session.modulus=='84500.5' and window.pmx_session.force=='-3')
        check('all signed global force components reopen',window.pmx_session.forces==['-3','4','-12'])
        check('saved Poisson ratio and density reopen',window.pmx_session.poisson=='0.25' and window.pmx_session.density=='8.1E-9')
        if state.get('reassigned'):
            graph=window.pmx_session.project['graph']
            check('solid section assignment reopens',graph['sections'][0]['region']=='SOLID_Copy')
            check('load assignment reopens',graph['steps'][0]['loads'][0]['region']=='X0_Copy')
            check('all support assignments reopen',
                  {item['name']:item['region'] for item in graph['steps'][0]['constraints']}==
                  {'X0':'X1_Copy','Y0':'Y0_Copy','Z0':'Z0_Copy'})
        check('saved CAD BREP and named regions unchanged',window.pmx_session.project['cadGeometry']==original.project['cadGeometry'] and window.pmx_session.project['graph']['nodeSets']==original.project['graph']['nodeSets'])
        malformed=output/'unsupported.pmx';malformed.write_bytes(source.read_bytes().replace(b'PrePoMax v3.0.0',b'PrePoMax v2.6.0',1))
        before=window.pmx_session
        try:window.open_pmx(malformed)
        except ValueError:check('unsupported project preserves current CAD model',window.pmx_session is before and window.cad_document is not None)
        else:raise ValueError('Unsupported PMX accepted')
        window.job.completed.connect(lambda result:QtCore.QTimer.singleShot(200,lambda:solved(result)))
        QtCore.QTimer.singleShot(120000,lambda:finish('CAD PMX probe timeout'))
        window.run_model()
    except Exception as error:finish(error)

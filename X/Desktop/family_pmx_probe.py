"""Original PMX family open, exact Save As, reopen and native solve."""
import hashlib
import json
from pathlib import Path
from PyQt6 import QtCore,QtWidgets
from pmx_project import FamilyPmxSession,FamilyPmxDialog
from results_tools import read_histories

CASES=('shell-tension','mixed-solids','plane-force','strain-force','axis-prescribed','membrane-api')

def begin(app,w,source,output):
    output.mkdir(parents=True,exist_ok=False);state={'index':0,'done':False};report={'success':False,'checks':[],'runs':{},'transport':w.transport}
    w.confirm_discard=lambda:True
    def check(name,value):
        report['checks'].append({'name':name,'passed':bool(value)})
        if not value:raise ValueError(name)
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
    @guarded
    def prepare():
        c=CASES[state['index']];state['case']=c;path=source/c/'original.pmx';w.editor_dirty=False;w.open_pmx(path)
        original=w.pmx_session;check(c+' family PMX projection opens',isinstance(original,FamilyPmxSession) and w.analysis_valid)
        dialog=FamilyPmxDialog(w,original);dialog.show();app.processEvents();check(c+' PMX controls captured',dialog.grab().save(str(output/(c+'-pmx.png'))));dialog.close()
        saved=output/(c+'.pmx');out=original.save_copy(saved);check(c+' exact-byte original PMX Save As',out['success'] and saved.read_bytes()==path.read_bytes())
        try:original.save_copy(saved)
        except FileExistsError:pass
        else:raise ValueError('Existing PMX destination was overwritten.')
        reopened=FamilyPmxSession(saved);check(c+' graph/model/history preserved on reopen',original.project['graph']==reopened.project['graph'] and original.project['originalModelSha256']==reopened.project['originalModelSha256'])
        state['sha']=hashlib.sha256(original.contents).hexdigest();w.run_action.trigger();check(c+' native PMX job starts',w.busy)
    @guarded
    def solved(result):
        c=state['case'];check(c+' native PMX solve completes',result['success']);directory=Path(result['directory'])
        check(c+' immutable PMX input retained',hashlib.sha256((Path(result['inputDirectory'])/'source.pmx').read_bytes()).hexdigest()==state['sha'])
        check(c+' native result fields displayed',any(f['name']=='DISP' for f in w.scene.get('fields',[])))
        if c in ('plane-force','strain-force','membrane-api'):
            frame=next(f for f in w.scene['fields'] if f['name']=='DISP');nodes={n['id']:n for n in w.scene['nodes']};error=max(abs(frame['components']['U2'][i]-.001*nodes[n]['y']) for i,n in enumerate(w.scene['nodeIdsInValueOrder']));check(c+' independent extension',error<1e-8)
        if c=='axis-prescribed':
            f=next(f for f in w.scene['fields'] if f['name']=='DISP');nodes={n['id']:n for n in w.scene['nodes']};check(c+' prescribed axial displacement',all(abs(f['components']['U2'][i]-.001*nodes[n]['y'])<1e-8 for i,n in enumerate(w.scene['nodeIdsInValueOrder'])))
        w.fit();app.processEvents()
        if w.transport=='frame-bridge':picture=w.grab()
        else:
            origin=w.mapToGlobal(QtCore.QPoint(0,0));picture=w.screen().grabWindow(0,origin.x(),origin.y(),w.width(),w.height())
        check(c+' PMX result captured',picture.save(str(output/(c+'.png'))));report['runs'][c]={'job':result,'sourceSha256':state['sha']};state['index']+=1
        if state['index']==len(CASES):finish()
        else:QtCore.QTimer.singleShot(50,prepare)
    w.job.completed.connect(lambda result:QtCore.QTimer.singleShot(200,lambda:solved(result)))
    QtCore.QTimer.singleShot(300000,lambda:finish('PMX workflow timeout'));QtCore.QTimer.singleShot(0,prepare)

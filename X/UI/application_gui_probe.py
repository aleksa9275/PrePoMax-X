"""Real C5 Qt/native-VTK workflow, original services and local automation transport."""
import json,traceback,threading,time,urllib.request,urllib.error,os,struct
from pathlib import Path
from PyQt6 import QtCore,QtWidgets,QtGui,QtTest
from application_widgets import SettingsDialog,HistoryDialog,KeywordDialog,LibraryDialog,UserViewsDialog
from PrePoMaxX.UI import PropertySheet
from PrePoMax.Rpc import RpcSessionInfoWriter

def start(app,w,output,check_three_mf=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);report={'success':False,'checks':[]}
    def check(name,value):
        report['checks'].append({'name':name,'passed':bool(value)})
        if not value:raise AssertionError(name)
    def wait(condition,seconds=20):
        deadline=time.monotonic()+seconds
        while not condition() and time.monotonic()<deadline:QtTest.QTest.qWait(20)
        if not condition():raise TimeoutError('C5 GUI condition timed out')
    def run():
        try:
            c=w.controller;baseline=output.parent/'service/application.pmx';w.open(str(baseline));app.processEvents()
            check('C5 menus and native viewport',all(n in w.application_actions for n in ['Settings…','Material library…','Edit commands…','CalculiX keywords…','Run Python file…']) and len(w.scene.actors)>0)
            dialog=SettingsDialog(w);check('all original settings pages presented',dialog.pages.count()==13)
            dialog.pages.setCurrentText('Graphics') if hasattr(dialog.pages,'setCurrentText') else dialog.pages.setCurrentRow(list(dialog.rule.Pages).index('Graphics'))
            app.processEvents();check('original graphics property widget', 'AmbientComponent' in dialog.panel.entries);dialog.panel.entries['AmbientComponent'][1].setText('0.6');dialog.apply();check('settings GUI applies original values',abs(c.Settings.Graphics.AmbientComponent-.6)<1e-6);dialog.reject()
            history=HistoryDialog(w);check('command grid and original Python preview',history.table.rowCount()==c.GetCommands().Count and 'pmx' in history.script.toPlainText());check('original command property inspector descriptors',len(history.rule.Properties(0).Fields)>0);history.reject()
            keywords=KeywordDialog(w);check('original keyword tree and preview',keywords.tree.topLevelItem(0).childCount()>0 and '*NODE' in keywords.preview.toPlainText().upper());keywords.reject()
            library=LibraryDialog(w);library.rule.Open(str(output.parent/'service/materials.lib'));library.rebuild();check('material library graph is visible',library.tree.topLevelItem(0).child(0).child(0).text(0)=='XSTEEL');library.reject()
            views=UserViewsDialog(w);views.add();views.rebuild();check('user view captures original camera',len(views.rule.Names)==1);views.rule.Apply();views.reject()
            c.SetUserView(c.GetUserViewParameters()[0].Name);app.processEvents();check('original saved view controls native camera',w.renderer.GetActiveCamera().GetParallelScale()>0)
            check('original advisor pages visible',len(w.advisor_pages)==9 and w.advisor_index.count()==9)
            from PrePoMaxX.UI import QuerySession
            check('original query calculations available from UI','Bounding box' in QuerySession(c).Run('Bounding box',__import__('System').Array[__import__('System').Int32]([])))
            w.application.Find('Node',1,True);w.refresh();w.scene.show_selection(w.session.Presentation.SelectionActors);check('original Find highlight and annotation',w.scene.highlight_actor is not None and len(c.Annotations.GetCurrentAnnotationNames())>0)
            w.set_edge_mode('No edges');check('no-edge mode controls native actors',all(not a.GetVisibility() for a in w.scene.element_edge_actors));w.set_edge_mode('Model edges')
            w.pick_mode.setCurrentIndex(0);w.box_select.setChecked(True);QtTest.QTest.mousePress(w.viewport,QtCore.Qt.MouseButton.LeftButton,pos=QtCore.QPoint(2,2));QtTest.QTest.mouseMove(w.viewport,QtCore.QPoint(w.viewport.width()-2,w.viewport.height()-2));QtTest.QTest.mouseRelease(w.viewport,QtCore.Qt.MouseButton.LeftButton,pos=QtCore.QPoint(w.viewport.width()-2,w.viewport.height()-2));app.processEvents();check('rectangle gesture resolves original frustum element IDs',w.selected==[1]);w.box_select.setChecked(False);w.clear_selection()
            check('native orientation and scale preference widgets',hasattr(w,'orientation_widget') and hasattr(w,'scale_actor'))
            w.capture(str(output/'transparent.png'),True,2);image=QtGui.QImage(str(output/'transparent.png'));check('magnified RGBA capture',image.hasAlphaChannel() and image.width()==w.viewport.GetRenderWindow().GetSize()[0]*2);check('transparent capture background',image.pixelColor(0,0).alpha()==0)
            w.script_dock.show();w.script_edit.setPlainText('print("C5", 7*6)');w.script_record.setChecked(True);w.execute_script();check('script task locks document menus',not w.tree.isEnabled());wait(lambda:w.operation_task is None);check('original Python output in panel','C5 42' in w.script_output.toPlainText());check('script task unlocks document',w.tree.isEnabled())
            from PrePoMax.Python import PythonEngineManager
            w.script_edit.setPlainText('while True:\n    pass');w.execute_script();wait(lambda:PythonEngineManager.IsExecuting);w.interrupt_script();wait(lambda:w.operation_task is None);check('original Python Stop interrupts active script','KeyboardInterrupt' in w.script_output.toPlainText());w.script_edit.setPlainText('print("C5", 7*6)')
            from UserControls import XYPlotCurveState
            from System import Array,Double
            state=w.plot_panel.session.State;curve=XYPlotCurveState();curve.XValues=Array[Double]([0,1,2]);curve.YValues=Array[Double]([2,4,6]);curve.Settings.Name='C5 plot';state.Plots[0].Curves.Add(curve);w.plot_panel.rebuild();w.plot_dock.show();app.processEvents();check('original XY plot state rendered',w.plot_panel.tabs.count()==1 and w.plot_panel.tabs.currentWidget().state.Curves.Count>=1)
            view=w.plot_panel.tabs.currentWidget();before=view.state.Settings.XAxisAutoScale;view.state.Settings.XAxisAutoScale=False;view.state.Settings.XAxisMin=0;view.state.Settings.XAxisMax=2;view.update();check('plot settings use original scale state',view.state.Settings.XAxisMax==2)
            w.capture_panel_state();c.SaveToPmxCommand(str(output/'ui-state.pmx'));w.open(str(output/'ui-state.pmx'));app.processEvents();check('script and plot state reopen through PMX','C5' in w.script_edit.toPlainText() and w.plot_panel.session.State.Plots[0].Curves.Count>=1)
            # Authenticated endpoint stays on loopback; test refused requests without logging its token.
            RpcSessionInfoWriter.NativeSessionsDirectory=str(output/'automation-sessions');w.application.GenerateAccessToken();w.application.Automation.Start();endpoint=w.application.Automation.EndpointUrl;token=c.AutomationSettings.AccessToken
            def request(body,auth=True,origin=None):
                headers={'Content-Type':'application/json'}
                if auth:headers['Authorization']='Bearer '+token
                if origin:headers['Origin']=origin
                req=urllib.request.Request(endpoint,data=json.dumps(body).encode(),headers=headers)
                try:
                    with urllib.request.urlopen(req,timeout=15) as r:return r.status,json.loads(r.read())
                except urllib.error.HTTPError as e:return e.code,None
            def background(cb):
                values=[]
                def work():
                    try:values.append((True,cb()))
                    except BaseException as e:values.append((False,e))
                thread=threading.Thread(target=work);thread.start();wait(lambda:bool(values));thread.join()
                if not values[0][0]:raise values[0][1]
                return values[0][1]
            init={'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'C5 verification','version':'1'}}}
            check('MCP refuses unauthenticated request',background(lambda:request(init,False))[0]==401)
            check('MCP refuses browser Origin',background(lambda:request(init,True,'https://example.invalid'))[0]==403)
            status,reply=background(lambda:request(init));check('original MCP handshake',status==200 and reply['result']['serverInfo']['name']=='prepomax')
            tools={'jsonrpc':'2.0','id':2,'method':'tools/list','params':{}};status,reply=background(lambda:request(tools));check('original automation tools catalog',status==200 and any(t['name']=='run_python' for t in reply['result']['tools']))
            call={'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'eval_expression','arguments':{'expression':'6*7'}}};status,reply=background(lambda:request(call));check('original live Python through MCP',status==200 and '42' in json.dumps(reply) and not reply['result'].get('isError',False))
            old_name=c.Model.Name;w.application.Automation.IsReadOnlyRequested=True
            write={'jsonrpc':'2.0','id':4,'method':'tools/call','params':{'name':'run_python','arguments':{'source':'pmx.model.properties.name = "Forbidden"'}}};status,reply=background(lambda:request(write));check('original read-only automation refuses model command',status==200 and 'read only' in json.dumps(reply).lower() and c.Model.Name==old_name);w.application.Automation.IsReadOnlyRequested=False
            from System.IO.Pipes import NamedPipeClientStream,PipeDirection
            from System.IO import StreamWriter,StreamReader
            pipe=NamedPipeClientStream('.',w.application.Automation.PipeName,PipeDirection.InOut)
            try:
                pipe.Connect(3000);writer=StreamWriter(pipe);writer.AutoFlush=True;reader=StreamReader(pipe);writer.WriteLine('{"jsonrpc":"2.0","id":1,"method":"ping","params":{}}');response=json.loads(reader.ReadLine());check('original current-user named pipe protocol',response['result']['protocolVersion']=='1.0')
            finally:pipe.Dispose()
            # The original busy gate refuses model access while a modeless draft is open.
            draft=KeywordDialog(w);w.show_editor(draft,'Keywords');status,reply=background(lambda:request(call));check('automation respects active modeless editor','dialog' in json.dumps(reply).lower());draft.reject();app.processEvents()
            sessions=list((output/'automation-sessions').glob('*.json'));check('private session file created',len(sessions)==1 and (os.name=='nt' or sessions[0].stat().st_mode&0o077==0));w.application.Automation.Stop();check('automation stop removes session file',not list((output/'automation-sessions').glob('*.json')))
            # Original data is opened from the C4 receipt when supplied by the milestone verifier.
            results=output.parents[1]/'results/service/results.pmx'
            if results.is_file():
                w.open(str(results));w.frames.setValue(3);w.play_animation();w.animation_timer.stop();w.export_animation(str(output/'animation.avi'),fps=12,swing=True);data=(output/'animation.avi').read_bytes();check('portable AVI stream contains native frames',data[:4]==b'RIFF' and data[8:12]==b'AVI ' and b'idx1' in data);w.stop_animation()
                # The verifier supplies the exact 2.4.1 native library through a fingerprinted manifest.
                if check_three_mf:
                    import zipfile
                    from PrePoMax import Export3mfFileProperties
                    w.update_export_view();properties=Export3mfFileProperties();properties.FileName=str(output/'contours.3mf');w.application.Export3mf(properties)
                    with zipfile.ZipFile(output/'contours.3mf') as archive:check('original native 3MF contour export',any(n.endswith('.model') for n in archive.namelist()) and any(n.endswith('.png') for n in archive.namelist()))
                check('result field/history component trees',any(e.data(0,QtCore.Qt.ItemDataRole.UserRole).Family=='Result field components' for e in w.walk_tree()))
                def leaves(family):return [e.data(0,QtCore.Qt.ItemDataRole.UserRole) for e in w.walk_tree() if e.data(0,QtCore.Qt.ItemDataRole.UserRole).Family==family]
                components=leaves('Result field components');count=len(components);entry=next(e for e in components if e.Step=='DoubleStress');w.remove_result_leaf(entry);check('original per-component field removal',len(leaves('Result field components'))==count-1)
                components=leaves('Result history components');count=len(components)
                if components:w.remove_result_leaf(components[0]);check('original per-component history removal',len(leaves('Result history components'))==count-1)
            else:report['pending']=['C4 result fixture not supplied for AVI/component integration']
            w.fit();app.processEvents();QtTest.QTest.qWait(100);origin=w.mapToGlobal(QtCore.QPoint(0,0));w.screen().grabWindow(0,origin.x(),origin.y(),w.width(),w.height()).save(str(output/'workbench.png'));report['success']=True
        except BaseException as error:report['error']=str(error);report['traceback']=traceback.format_exc()
        finally:
            try:w.application.Automation.Stop()
            except Exception:pass
            if w.active_editor is not None:w.active_editor.reject()
            w.dirty=False;c.ModelChanged=False
            (output/'application-gui.json').write_text(json.dumps(report,indent=2)+'\n');w.viewport.Finalize();app.quit()
    QtCore.QTimer.singleShot(400,run)

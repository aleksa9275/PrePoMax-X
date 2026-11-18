"""Real native Qt/VTK C4 solve, result controls, animation and captures."""
import json
import System,time,traceback
from pathlib import Path
from PyQt6 import QtCore,QtWidgets,QtTest
from System import Single,Array,Double
from PrePoMax import ViewGeometryModelResults
from results_probe import prepare


def start(app,window,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);checks=[];report={'success':False,'checks':checks};state={};started=time.monotonic()
    def check(name,value):
        if not value:raise AssertionError(name)
        checks.append(name)
    def wait():
        if window.operation_task is not None:return False
        if getattr(window,'operation_error',None):raise AssertionError(window.operation_error)
        return True
    def setup():
        from form_driver import FormDriver
        prepare(window.session,output);window.refresh();window.edit_results('Jobs')
        driver=FormDriver(window);form=driver.form
        check('Create Analysis opens the original FrmAnalysis',type(form).__name__=='FrmAnalysis' and str(form.Text)=='Create Analysis')
        driver.set('Name','GUI_Cube');driver.ok()
        check('original FrmAnalysis OK creates the job (AddJobCommand)',window.controller.GetJob('GUI_Cube') is not None and not form.Visible)
    def run():
        if not wait():return False
        app.processEvents();window.refresh()
        check('original job in model tree',any(i.data(0,QtCore.Qt.ItemDataRole.UserRole).Family=='Jobs' and not i.data(0,QtCore.Qt.ItemDataRole.UserRole).Group for i in window.walk_tree()))
        window.run_job(name='GUI_Cube')
        monitor=next((f for f in window.form_host.AllForms if type(f).__name__=='FrmMonitor'),None)
        check('solver locks document and shows the original FrmMonitor (MonitorAnalysis)',window.operation_task is not None and not window.tree.isEnabled() and monitor is not None and monitor.Visible
              and window.form_renderer.windows.get(monitor) is not None)
    def solved():
        if not wait():return False
        from form_driver import walk
        app.processEvents();window.form_renderer.flush()
        job=window.controller.GetJob('GUI_Cube');check('original solver succeeded',str(job.JobStatus)=='OK')
        monitor=next(f for f in window.form_host.AllForms if type(f).__name__=='FrmMonitor')
        controls={str(c.Name):c for c in walk(monitor)}
        report['monitorState']={k:str(controls[k].Text)[:200] for k in ('tbOutput','tbStatus','labAnalysisStatus')};report['monitorState']['style']=str(controls['pbAnalysisStatus'].Style)
        check('FrmMonitor shows solver output and status (UpdateOutput, UpdateProgress)',bool(str(controls['tbOutput'].Text)) and bool(str(controls['tbStatus'].Text))
              and str(controls['labAnalysisStatus'].Text).strip()=='Finished' and str(controls['pbAnalysisStatus'].Style)=='Blocks')
        from ZedGraph import ZedGraphControl
        graphs=[c for c in walk(monitor) if isinstance(c,ZedGraphControl)]
        status=graphs[0].GraphPane
        report_monitor={'graphs':len(graphs),'statusCurves':[str(c.Label.Text) for c in status.CurveList],
                        'statusX':[float(status.XAxis.Scale.Min),float(status.XAxis.Scale.Max),float(status.XAxis.Scale.MajorStep)],
                        'statusY':[float(status.YAxis.Scale.Min),float(status.YAxis.Scale.Max),float(status.YAxis.Scale.MajorStep)]}
        report.setdefault('forms',{})['FrmMonitor']=report_monitor
        check('AnalysisProgressView plots the original status data (SetStatusData, AxisChange)',len(graphs)>=1 and status.CurveList.Count>=2 and status.XAxis.Scale.Max>status.XAxis.Scale.Min)
        # Results: FrmMonitor.btnResults -> FrmMain.ResultsAnalysis (the workbench opens the results).
        window.form_renderer.guard(controls['btnResults'].RaiseClick)
    def loaded():
        if not wait():return False
        from form_driver import walk
        monitor=next(f for f in window.form_host.AllForms if type(f).__name__=='FrmMonitor')
        check('the monitor stays open after Results (item form; CloseMonitorWindow sets a DialogResult only)',monitor.Visible and not window.tree.isEnabled())
        window.form_renderer.guard(next(c for c in walk(monitor) if str(c.Name)=='btnClose').RaiseClick);window.form_renderer.flush()
        check('closing the monitor turns the menus on again (itemForm_VisibleChanged)',not monitor.Visible and window.tree.isEnabled())
        from CaeGlobals import UnitSystem,UnitSystemType
        window.controller.CurrentResult.UnitSystem=UnitSystem(UnitSystemType.Undefined)
        def choose_units():
            dialog=QtWidgets.QApplication.activeModalWidget();dialog.findChild(QtWidgets.QComboBox).setCurrentText('MM_TON_S_C');dialog.accept()
        QtCore.QTimer.singleShot(50,choose_units);window.session.Presentation.SelectResultsUnitSystem()
        check('unknown result units use interactive original policy',window.controller.CurrentResult.UnitSystem.UnitSystemType==UnitSystemType.MM_TON_S_C)
        check('results view and scalar surface visible',window.controller.CurrentView==ViewGeometryModelResults.Results and len(window.scene.actors)>0)
        check('field controls contain original data',window.result_boxes['Field'].count()>=3 and window.original_strips['tsResults'].isEnabled() and window.tool_tscbStepAndIncrement.count()>0)
        window.result_boxes['Field'].setCurrentText('DISP');window.result_boxes['Component'].setCurrentText('U1');app.processEvents()
        check('field control changes original current field',window.controller.CurrentFieldData.Name=='DISP' and window.controller.CurrentFieldData.Component=='U1')
        check('native scalar mapper active',bool(window.scene.presentation.scalar_mappers) and all(m.GetScalarVisibility()==1 for m in window.scene.presentation.scalar_mappers))
        check('original legend colors and status rendered',window.scene.presentation.scalar_bar is not None and window.scene.presentation.status is not None and window.scene.presentation.table.GetNumberOfTableValues()==9)
        window.results.Deformation('DISP','TrueScale',Single(1));window.refresh();check('deformation uses original scale',window.controller.GetScale()==1)
        window.result_boxes['View'].setCurrentText('VectorPlot');app.processEvents();check('native vector plot rendered',len(window.scene.presentation.plot_commands)>0)
        window.result_boxes['Field'].setCurrentText('STRESS');window.result_boxes['Component'].setCurrentText('S11');app.processEvents();window.results.Representation('TensorPlot');window.refresh()
        check('native tensor plot rendered',any('Tensor' in name for name,_,_ in window.scene.presentation.plot_commands))
        window.result_boxes['Field'].setCurrentText('DISP');window.result_boxes['Component'].setCurrentText('U1');window.result_boxes['View'].setCurrentText('ColorContours');app.processEvents()
        window.controller.Annotations.AddNodeAnnotation(2);window.controller.Annotations.AddDistanceAnnotation(1,2);window.refresh()
        check('original annotations rendered',any(v.Name=='AddArrowWidget' for v in window.session.Presentation.RenderCommands) and len(window.scene.presentation.props)>2)
        window.animation_type.setCurrentText('Scale factor');window.frames.setValue(5);window.play_animation();window.animation_timer.stop()
        window.show_frame(0);state['first']=window.scene.presentation.animated[0][1].GetMapper().GetInput().GetPoint(1);window.show_frame(4);state['last']=window.scene.presentation.animated[0][1].GetMapper().GetInput().GetPoint(1)
        check('original frame data moves native points',state['first']!=state['last']);check('animation slider supports all frames',window.frame_slider.maximum()==4)
        window.export_animation(str(output/'frames.png'));check('animation PNG sequence exported',len(list(output.glob('*_frames.png')))==5)
        window.export_animation(str(output/'animation.ogv'));check('native Ogg Theora animation exported',(output/'animation.ogv').stat().st_size>1000)
        window.stop_animation();window.fit();window.capture(str(output/'contours.png'))
        check('native PNG capture',(output/'contours.png').stat().st_size>2000)
        window.session.Presentation.SaveAutomationScreenshot(str(output/'automation.png'),False,1)
        check('original automation screenshot reaches rendered viewport',(output/'automation.png').stat().st_size>2000)
        from presentation_widgets import PresentationDialog,TransformationsDialog
        dialog=PresentationDialog(window,'Legend');check('original legend view descriptors',len(dialog.rule.Properties.Fields)>5);dialog.reject()
        dialog=PresentationDialog(window,'Section view');dialog.rule.Properties.Set('X','0.5');dialog.rule.Apply();window.refresh();check('native section plane and cap rendered',len(window.scene.presentation.features.cuts)>0);window.controller.RemoveSectionView(False);window.refresh();dialog.reject()
        dialog=TransformationsDialog(window);dialog.rule.Add(3);dialog.rule.ApplyTransformation();window.refresh();check('original linear pattern rendered',len(window.scene.presentation.features.copies)>0);window.controller.RemoveCurrentTransformations(True);window.refresh();dialog.reject()
        from CaeResults import Transformation,CircularPattern
        from System.Collections.Generic import List
        from System import Array,Double
        window.results.Field('STRESS','S11',1,1);patterns=List[Transformation]();patterns.Add(CircularPattern('Quarter_turn',Array[Double]([0,0,0]),Array[Double]([0,0,1]),90,2));window.controller.SetTransformations(patterns);window.refresh()
        bounds=window.scene.presentation.table.GetTableRange();check('rotated tensor component included in scalar range',bounds[0]<1 and bounds[1]>90)
        window.controller.RemoveCurrentTransformations(True);window.results.Field('DISP','U1',1,1);window.refresh()
        from results_widgets import ResultsDialog
        for family,name in [('Result coordinate systems','GUI_CS'),('Result reference points','GUI_RP')]:
            feature=ResultsDialog(window,family);feature.entries['Name'][1].setText(name);feature.flush();feature.rule.Commit();feature.reject()
        window.refresh();check('result coordinate/reference editors commit original definitions','GUI_CS' in list(window.controller.GetResultCoordinateSystemNames()) and 'GUI_RP' in list(window.controller.GetResultReferencePointNames()))
        # Original FrmResultFieldOutput compiled whole (C10), opened through FrmMain.tsmiCreateResultFieldOutput_Click.
        from form_driver import FormDriver
        forms=FormDriver(window);window.edit_results('Result fields')
        check('original FrmResultFieldOutput opened',type(forms.form).__name__=='FrmResultFieldOutput' and str(forms.form.Text)=='Create Field Output')
        check('original result field output types',forms.types==['Limit','Envelope','Equation','Coordinate System Transform','Material Axes','Shell In-Plane State','Composite Failure'])  # 3.0.1 adds the shell/composite types
        forms.select_type('Equation');forms.set('Name','GUI_Double');forms.set('Equation','=2*STRESS.S11');forms.ok()
    def authored():
        if not wait():return False
        check('result equation widget uses original command',window.controller.GetResultFieldOutput('GUI_Double') is not None)
        from history_widgets import show_history
        # Original FrmResultHistoryOutput (C10): From Table with the original DataGridViewCopyPaste.
        from form_driver import FormDriver,walk
        from System.Windows.Forms import DataGridView,TabControl
        from forms_gui_probe_grid import edit_cell
        forms=FormDriver(window);window.edit_results('Result histories')
        check('original FrmResultHistoryOutput opened',type(forms.form).__name__=='FrmResultHistoryOutput' and str(forms.form.Text)=='Create History Output')
        forms.select_type('From Table');forms.set('Name','GUI_Table')
        form=forms.form;w=window.form_renderer.windows[form]
        dgv=next(c for c in walk(form) if isinstance(c,DataGridView));tabs=next(c for c in walk(form) if isinstance(c,TabControl))
        window.form_renderer.guard(lambda:setattr(tabs,'SelectedIndex',1));forms.flush()
        table=w.widgets[dgv]
        for row,values in enumerate([[0,1],[1,2]]):
            for col,value in enumerate(values):edit_cell(app,table,row,col,str(value));forms.flush()
        forms.set('Name','GUI_Table')
        check('history table cells survive property edits (UpdateTableDataFromGrid)',dgv.RowCount==3 and str(dgv.GetCellText(1,1))=='2')
        forms.ok()
    def history():
        if not wait():return False
        from history_widgets import show_history
        check('table history widget creates original output','GUI_Table' in list(window.controller.GetHistoryResultSetNames()))
        state['history']=show_history(window,'GUI_Table');check('original history table and plot opened',state['history'].isVisible())
        state['oldPart']=list(window.controller.GetResultPartNames())[0]
        # Original FrmPartProperties compiled whole (C9), opened through FrmMain.EditResultPart.
        from form_driver import FormDriver
        forms=FormDriver(window);window.edit_geometry('Parts',state['oldPart'])
        check('original FrmPartProperties opened through FrmMain.EditResultPart',type(forms.form).__name__=='FrmPartProperties' and str(forms.form.Text).startswith('Edit Part'))
        forms.set('Name','GUI_ResultPart');forms.ok()
    def result_views():
        """Original result-view forms (C11): FrmAnimation drives the frames through FrmMain.SetAnimationFrame,
        FrmSectionView/FrmTransformation change the rendered scene, FrmFollowerView opens, and a history leaf
        opens FrmViewResultHistoryOutput."""
        if not wait():return False
        from form_driver import walk
        from forms_gui_probe_child import ChildFormsProbe
        r=window.form_renderer;helper=ChildFormsProbe(app,window,check,report,lambda *a:None)
        def visible(cls):return next((f for f in window.form_host.AllForms if type(f).__name__==cls and f.Visible),None)
        def named(form):return {str(c.Name):c for c in walk(form)}
        def settle(ms=300):QtTest.QTest.qWait(ms);r.flush();app.processEvents()
        forms=report.setdefault('forms',{})
        # Animation
        window.run_original_entry('tsbAnimate_Click');settle()
        form=visible('FrmAnimation');check('Animate opens the original FrmAnimation (tsbAnimate_Click)',form is not None)
        check('animation turns the tree and results tool strips off (SetMenuAndToolStripVisibilityByAnimation)',not window.tree.isEnabled() and not window.original_strips['tsResults'].isEnabled())
        c=named(form);frames=int(System.Decimal.ToDouble(c['numNumberOfFrames'].Value))
        positions=[]
        for frame in (1,frames):
            r.guard(lambda f=frame:c['numCurrFrame'].UserSetValue(System.Decimal(f)));settle(200)
            positions.append(tuple(window.scene.presentation.animated[0][1].GetMapper().GetInput().GetPoint(1)))
        forms['FrmAnimation']={'frames':frames,'current':int(System.Decimal.ToDouble(c['numCurrFrame'].Value)),'workbenchFrame':window.animation_frame}
        check('original frame controls move the rendered points (FrmMain.SetAnimationFrame)',positions[0]!=positions[1] and window.animation_frame==frames-1)
        r.guard(c['btnClose'].RaiseClick);settle()
        check('Close ends the animation and turns the menus on again',not form.Visible and window.tree.isEnabled())
        # Section view
        window.run_original_entry('tsmiSectionView_Click');settle()
        form=visible('FrmSectionView');check('Section View opens the original FrmSectionView',form is not None)
        c=named(form);bar=c['hsbPosition']
        from System.Windows.Forms import ScrollEventType;r.guard(lambda:bar.UserScroll(ScrollEventType.ThumbPosition,(bar.Minimum+bar.Maximum)//2));settle(500)
        forms['FrmSectionView']={'scroll':[bar.Minimum,bar.Maximum,bar.Value],'cuts':len(window.scene.presentation.features.cuts)}
        check('the position scroll bar draws the section (original preview)',len(window.scene.presentation.features.cuts)>0)
        r.guard(c['btnCancel'].RaiseClick);settle()
        check('Cancel removes the section',not form.Visible and len(window.scene.presentation.features.cuts)==0)
        # Transformation
        window.run_original_entry('tsmiTransformation_Click');settle()
        form=visible('FrmTransformation');check('Transformation opens the original FrmTransformation',form is not None)
        c=named(form);tree=c['tvTransformations'];_,tree_widget=helper.widget(form,tree)
        def nodes(collection):
            for n in collection:
                yield n;yield from nodes(n.Nodes)
        texts=[str(n.Text) for n in nodes(tree.Nodes)];forms['FrmTransformation']={'types':texts}
        node=[n for n in nodes(tree.Nodes) if 'Linear' in str(n.Text)]
        check('the original transformation tree lists a linear pattern',bool(node));node=node[0];node.EnsureVisible();r.flush()
        helper.tree_click(tree_widget,node);r.guard(c['btnAdd'].RaiseClick);r.guard(c['bntApply'].RaiseClick);settle()
        check('a linear pattern added in the original tree is rendered',len(window.scene.presentation.features.copies)>0)
        r.guard(c['btnCancel'].RaiseClick);settle()
        check('Cancel hides the form and keeps the applied pattern (original btnCancel_Click)',not form.Visible and len(window.scene.presentation.features.copies)>0)
        window.controller.RemoveCurrentTransformations(True);window.refresh()
        # Follower view
        window.run_original_entry('tsmiFollowerView_Click');settle()
        form=visible('FrmFollowerView');check('Follower View opens the original FrmFollowerView',form is not None)
        r.guard(named(form)['btnCancel'].RaiseClick);settle();check('Follower View Cancel hides it',not form.Visible)
        # History data
        if state.get('history') is not None:state['history'].close()
        leaf=next(i for i in window.walk_tree() if i.data(0,QtCore.Qt.ItemDataRole.UserRole) is not None and i.data(0,QtCore.Qt.ItemDataRole.UserRole).Family=='Result history components'
                  and str(i.data(0,QtCore.Qt.ItemDataRole.UserRole).Step).startswith('GUI_Table'))
        window.edit_item(leaf);settle()
        form=visible('FrmViewResultHistoryOutput');check('a history leaf opens the original FrmViewResultHistoryOutput',form is not None)
        grid=named(form)['dgvHistory'];forms['FrmViewResultHistoryOutput']={'columns':[str(col.HeaderText) for col in grid.Columns],'rows':grid.RowCount}
        check('the history data rows are in the original grid (CreateCells/AddRange)',grid.RowCount>=2)
        r.guard(named(form)['btnClose'].RaiseClick);settle()
    def renamed():
        if not wait():return False
        check('result part properties use original command','GUI_ResultPart' in list(window.controller.GetResultPartNames()))
        window.path=str(output/'gui-results.pmx');window.save();window.open(window.path)
        check('GUI PMX preserves results/tools',window.controller.ResultsInitialized and window.controller.GetResultFieldOutput('GUI_Double') is not None)
        window.view.setCurrentText('Model');window.controller.DrawSymbols(list(window.controller.GetStepNames())[0],False);window.refresh()
        check('original BC/load symbols captured',any(v.Name.startswith('AddOriented') for v in window.session.Presentation.RenderCommands))
        check('native BC/load symbols rendered',len(window.scene.presentation.props)>0)
        window.view.setCurrentText('Results');window.fit();QtTest.QTest.qWait(100)
        check('results window captured',window.screen().grabWindow(0,window.x(),window.y(),window.width(),window.height()).save(str(output/'workbench.png')))
        report.update(success=True,project=window.path,frames={'first':state['first'],'last':state['last']})
    steps=iter([setup,run,solved,loaded,authored,history,result_views,renamed]);current=[None];timer=QtCore.QTimer(window)
    def tick():
        try:
            if time.monotonic()-started>240:raise TimeoutError('C4 GUI workflow timed out')
            if current[0] is None:current[0]=next(steps)
            if current[0]() is not False:current[0]=None
        except StopIteration:timer.stop();finish()
        except Exception as e:report.update(error=str(e),traceback=traceback.format_exc());timer.stop();finish()
    def finish():
        (output/'results-gui.json').write_text(json.dumps(report,indent=2)+'\n');window.dirty=False
        window.close();app.exit(0 if report['success'] else 1)
    timer.timeout.connect(tick);timer.start(50)

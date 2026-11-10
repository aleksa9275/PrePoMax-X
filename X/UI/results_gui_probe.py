"""Real native Qt/VTK C4 solve, result controls, animation and captures."""
import json,time,traceback
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
        if window.operation_error:raise AssertionError(window.operation_error)
        return True
    def setup():
        prepare(window.session,output);window.refresh();window.edit_results('Jobs');dialog=window.active_editor
        dialog.entries['Name'][1].setText('GUI_Cube');dialog.apply();check('analysis editor commits off UI thread',window.operation_task is not None)
    def run():
        if not wait():return False
        check('original job in model tree',any(i.data(0,QtCore.Qt.ItemDataRole.UserRole).Family=='Jobs' and not i.data(0,QtCore.Qt.ItemDataRole.UserRole).Group for i in window.walk_tree()))
        window.run_job(name='GUI_Cube');check('solver locks document and retains monitor',window.operation_task is not None and not window.tree.isEnabled() and window.monitors[-1].isVisible())
    def solved():
        if not wait():return False
        job=window.controller.GetJob('GUI_Cube');check('original solver succeeded',str(job.JobStatus)=='OK');monitor=window.monitors[-1];monitor.refresh()
        check('monitor displays solver output and status',bool(monitor.texts['Output'].toPlainText()) and bool(monitor.texts['Status'].toPlainText()))
        window.open_job('GUI_Cube')
    def loaded():
        if not wait():return False
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
        window.edit_results('Result fields');dialog=window.active_editor;dialog.types.setCurrentIndex(2);app.processEvents();dialog.entries['Name'][1].setText('GUI_Double');dialog.entries['Equation'][1].setText('=2*STRESS.S11');dialog.apply()
    def authored():
        if not wait():return False
        check('result equation widget uses original command',window.controller.GetResultFieldOutput('GUI_Double') is not None)
        from history_widgets import show_history
        window.edit_results('Result histories');dialog=window.active_editor;dialog.types.setCurrentIndex(dialog.types.count()-1);app.processEvents();dialog.entries['Name'][1].setText('GUI_Table');dialog.matrix.setRowCount(2)
        for row,values in enumerate([[0,1],[1,2]]):
            for col,value in enumerate(values):dialog.matrix.setItem(row,col,QtWidgets.QTableWidgetItem(str(value)))
        name_field=next(f for f in dialog.rule.Properties.Fields if f.Name=='Name');dialog.panel.commit_field(name_field,dialog.entries['Name'][1]);app.processEvents()
        check('pending history cells survive property rebuild',dialog.matrix.rowCount()==2 and dialog.matrix.item(1,1).text()=='2.0')
        dialog.apply()
    def history():
        if not wait():return False
        from history_widgets import show_history
        check('table history widget creates original output','GUI_Table' in list(window.controller.GetHistoryResultSetNames()))
        state['history']=show_history(window,'GUI_Table');check('original history table and plot opened',state['history'].isVisible())
        state['oldPart']=list(window.controller.GetResultPartNames())[0]
        window.edit_geometry('Parts',state['oldPart']);dialog=window.active_editor;dialog.entries['Name'][1].setText('GUI_ResultPart');dialog.apply()
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
    steps=iter([setup,run,solved,loaded,authored,history,renamed]);current=[None];timer=QtCore.QTimer(window)
    def tick():
        try:
            if time.monotonic()-started>120:raise TimeoutError('C4 GUI workflow timed out')
            if current[0] is None:current[0]=next(steps)
            if current[0]() is not False:current[0]=None
        except StopIteration:timer.stop();finish()
        except Exception as e:report.update(error=str(e),traceback=traceback.format_exc());timer.stop();finish()
    def finish():
        (output/'results-gui.json').write_text(json.dumps(report,indent=2)+'\n');window.dirty=False
        window.close();app.exit(0 if report['success'] else 1)
    timer.timeout.connect(tick);timer.start(50)

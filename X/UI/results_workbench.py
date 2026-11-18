"""C4 analysis/results UI: commands operate on the live original Controller."""
from pathlib import Path
from PyQt6 import QtCore,QtWidgets
from System import Array,String,Single,Enum,Int32
from PrePoMax import ViewGeometryModelResults,ViewResultsTypeEnum
from CaeResults import DeformationScaleFactorTypeEnum
from CaeResults import FeResults,ComplexResultTypeEnum
from PrePoMaxX.UI import ResultsSession
from results_widgets import ResultsDialog,JobMonitor
from authoring_widgets import PropertyPanel,message

class ResultsWorkbench:
    def build_results_ui(self):
        self.results=ResultsSession(self.session);self.monitors=[];self.animation_frame=None;self.animation_count=0
        self.animation_timer=QtCore.QTimer(self);self.animation_timer.timeout.connect(self.next_frame)
        jobs=self.menuBar().addMenu('Analysis');post=self.menuBar().addMenu('Results');view=self.menuBar().addMenu('Presentation')
        self.geometry_menus.extend([jobs,post,view])
        jobs.addAction('Create…',lambda:self.guard(lambda:self.edit_results('Jobs')))
        for title,callback in [('Run',lambda:self.run_job(False)),('Check model',lambda:self.run_job(True)),('Monitor…',self.monitor_job),('Kill',self.kill_job),('Open results',self.open_job)]:
            jobs.addAction(title,lambda checked=False,cb=callback:self.guard(cb))
        for operation in ['Duplicate jobs','Remove jobs']:
            jobs.addAction(operation,lambda checked=False,op=operation:self.guard(lambda:self.results_operation(op,'Jobs')))
        post.addAction('Open…',lambda:self.guard(self.open_result_file));post.addAction('Append…',lambda:self.guard(lambda:self.open_result_file(True)))
        for family in ['Result fields','Result histories','Result reference points','Result coordinate systems']:
            post.addAction('Create '+family.lower()+'…',lambda checked=False,f=family:self.guard(lambda:self.edit_results(f)))
        post.addAction('Units…',lambda:self.guard(self.set_result_units))
        post.addAction('View history data…',lambda:self.guard(self.history_data))
        post.addAction('Export current field…',lambda:self.guard(self.export_field))
        post.addAction('Remove current result',lambda:self.guard(lambda:self.results_operation('Remove result')))
        view.addAction('Deformation…',lambda:self.guard(self.deformation_dialog));view.addAction('Complex results…',lambda:self.guard(self.complex_dialog))
        view.addAction('Capture image…',lambda:self.guard(self.capture_dialog))
        self.addToolBarBreak();self.result_toolbar=self.addToolBar('Results')
        self.result_boxes={}
        for label in ['Result','Field','Component','Step','Increment','View']:
            box=QtWidgets.QComboBox();box.setMinimumContentsLength(6);box.setSizeAdjustPolicy(QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon);box.setMaximumWidth(240);box.setToolTip(label);self.result_boxes[label]=box
            # The result name box sits in the original tsResultDeformation strip (main_toolbars.py).
            if label!='Result':self.result_toolbar.addWidget(box)
            box.currentTextChanged.connect(lambda value,key=label:self.guard(lambda:self.result_changed(key,value)))
        # Original tsSymbols combo; placed and driven by main_toolbars.py (FrmMain.UpdateSymbolsList).
        self.symbols=QtWidgets.QComboBox()
        for family in ['Legend','Postprocessing','Annotations','Status block','Number format','Section view','Exploded view']:
            view.addAction(family+'…',lambda checked=False,f=family:self.guard(lambda:self.presentation_dialog(f)))
        view.addAction('Remove section view',lambda:self.guard(self.remove_section))
        view.addAction('Remove exploded view',lambda:self.guard(self.remove_exploded))
        view.addAction('Result transformations…',lambda:self.guard(self.transformations_dialog))
        view.addAction('Annotate…',lambda:self.guard(self.annotate))
        view.addAction('Remove annotations',lambda:self.guard(self.remove_annotations))
        view.addAction('Export animation…',lambda:self.guard(self.export_animation_dialog))
        self.result_boxes['View'].addItems([str(v) for v in Enum.GetValues(ViewResultsTypeEnum)])
        self.addToolBarBreak();self.animation_toolbar=self.addToolBar('Animation')
        self.animation_type=QtWidgets.QComboBox();self.animation_type.addItems(['Scale factor','Time increments','Harmonic']);self.animation_toolbar.addWidget(self.animation_type)
        self.frames=QtWidgets.QSpinBox();self.frames.setRange(2,1000);self.frames.setValue(21);self.frames.setToolTip('Animation frames');self.animation_toolbar.addWidget(self.frames)
        self.animation_options={'fps':20,'style':'Loop','step':1,'first':0,'last':None,'all_frames':True,'backward':False}
        self.animation_toolbar.addAction('Options…',lambda:self.guard(self.animation_options_dialog))
        self.animation_toolbar.addAction('Play',lambda:self.guard(self.play_animation));self.animation_toolbar.addAction('Stop',self.stop_animation)
        self.animation_toolbar.addAction('Close',lambda:self.guard(self.close_animation))
        self.frame_slider=QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal);self.frame_slider.setMaximumWidth(130);self.animation_toolbar.addWidget(self.frame_slider)
        self.frame_slider.valueChanged.connect(lambda frame:self.guard(lambda:self.show_frame(frame)))
        self.result_toolbar.hide();self.animation_toolbar.hide()
        self.view.addItem('Results')

    def update_results_ui(self):
        # Tool strip visibility/enabling: main_toolbars.update_original_toolbar_state.
        active=self.controller.CurrentView==ViewGeometryModelResults.Results and self.controller.ResultsInitialized
        if not active:return
        field=self.controller.CurrentFieldData
        values={'Result':list(self.results.ResultNames),'Field':list(self.results.Fields),'Component':list(self.results.Components(field.Name)),'Step':[str(v) for v in self.results.Steps],'Increment':[str(v) for v in self.results.Increments(field.StepId)]}
        selected={'Result':self.controller.AllResults.GetCurrentResultName(),'Field':field.Name,'Component':field.Component,'Step':str(field.StepId),'Increment':str(field.StepIncrementId),'View':str(self.controller.ViewResultsType)}
        for label,box in self.result_boxes.items():
            box.blockSignals(True)
            if label in values:box.clear();box.addItems(values[label])
            box.setCurrentText(selected[label]);box.blockSignals(False)
        self.resize_result_names()

    def resize_result_names(self):
        """FrmMain.SetResultNames/ResizeResultNamesComboBox: fit the selected name (125-400 px),
        drop-down as wide as the longest name."""
        box=self.result_boxes['Result'];metrics=box.fontMetrics()
        names=[box.itemText(i) for i in range(box.count())]
        if not names:return
        box.setMaximumWidth(16777215);box.setMinimumContentsLength(0)
        width=min(max(metrics.horizontalAdvance(box.currentText())+20+box.iconSize().width(),125),400)
        box.setFixedWidth(width)
        box.view().setMinimumWidth(max(metrics.horizontalAdvance(n) for n in names)+30)
    def result_changed(self,key,value):
        if not value or self.controller.CurrentView!=ViewGeometryModelResults.Results or not self.controller.ResultsInitialized:return
        self.stop_animation(False)
        if key=='Result':self.results.SelectResult(value)
        elif key=='View':self.results.Representation(value)
        else:
            current=self.controller.CurrentFieldData;name=value if key=='Field' else current.Name
            component=value if key=='Component' else current.Component
            if component not in list(self.results.Components(name)):component=self.results.Components(name)[0]
            step=int(value) if key=='Step' else current.StepId
            increments=list(self.results.Increments(step));increment=int(value) if key=='Increment' else current.StepIncrementId
            if increment not in increments:increment=increments[-1]
            self.results.Field(name,component,step,increment)
        self.refresh()

    def job_name(self,name=None):
        if name:return name
        names=list(self.selected_names('Jobs'))
        if len(names)!=1:raise ValueError('Select one analysis in the model tree.')
        return names[0]

    def edit_results(self,family,name=None):
        if self.active_editor is not None:return
        if family!='Jobs' and not self.controller.ResultsInitialized:raise ValueError('Open results first.')
        if self.open_original(family,None,name):return
        self.show_editor(ResultsDialog(self,family,name),family)

    def run_job(self,check=False,name=None):
        name=self.job_name(name);self.monitor_job(name)
        self.run_operation(self.results.RunJob(name,check),cancel=lambda:self.results.Kill(name))

    def monitor_job(self,name=None):
        # FrmMain.MonitorAnalysis: the original FrmMonitor.
        self.run_original_entry('MonitorAnalysis',name=str(self.job_name(name)))

    def kill_job(self):self.results.Kill(self.job_name())
    def open_job(self,name=None):self.run_operation(self.results.OpenJob(self.job_name(name)),lambda:self.result_opened())
    def open_result_file(self,append=False):
        path,_=QtWidgets.QFileDialog.getOpenFileName(self,'Append results' if append else 'Open results','','Results (*.frd *.dat *.odb *.foam)')
        if path:self.run_operation(self.results.Open(str(Path(path).resolve()),append),self.result_opened)
    def result_opened(self):self.controller.DrawResults(False);self.refresh();self.fit()

    def results_operation(self,operation,family=None):
        self.results.Execute(operation,self.selected_names(family) if family else Array[String]([]));self.refresh()

    def results_tree_menu(self,entry):
        menu=QtWidgets.QMenu(self)
        if entry.Family in ['Jobs','Result fields','Result histories','Result reference points','Result coordinate systems']:
            if entry.Group:menu.addAction('Create…',lambda:self.guard(lambda:self.edit_results(entry.Family)))
            else:
                # Raw solver history sets have data but no editable derived-output definition.
                editable=(entry.Family!='Result fields' or any(o.Name==entry.Name for o in self.controller.GetResultFieldOutputs())) and (entry.Family!='Result histories' or any(o.Name==entry.Name for o in self.controller.GetResultHistoryOutputs()))
                if not editable and entry.Family=='Result histories':
                    menu.addAction('Remove raw history set',lambda:self.guard(lambda:self.remove_raw_history(entry.Name)))
                if editable:
                    menu.addAction('Edit…',lambda:self.guard(lambda:self.edit_results(entry.Family,entry.Name)))
                    suffix={'Jobs':'jobs','Result fields':'fields','Result histories':'histories','Result reference points':'reference points','Result coordinate systems':'coordinate systems'}[entry.Family]
                    for op in ['Duplicate ','Remove ']:menu.addAction(op+suffix,lambda checked=False,o=op+suffix:self.guard(lambda:self.results_operation(o,entry.Family)))
                if entry.Family=='Jobs':
                    menu.addAction('Run',lambda:self.guard(lambda:self.run_job(name=entry.Name)));menu.addAction('Monitor…',lambda:self.guard(lambda:self.monitor_job(entry.Name)));menu.addAction('Open results',lambda:self.guard(lambda:self.open_job(entry.Name)))
                elif entry.Family in ['Result reference points','Result coordinate systems']:
                    for op in ['Hide ','Show ']:menu.addAction(op+suffix,lambda checked=False,o=op+suffix:self.guard(lambda:self.results_operation(o,entry.Family)))
                elif entry.Family=='Result histories':menu.addAction('View data…',lambda:self.guard(lambda:self.history_data(entry.Name)))
        elif entry.Family=='Result parts' and not entry.Group:
            menu.addAction('Properties…',lambda:self.guard(lambda:self.edit_geometry('Parts',entry.Name)))
            menu.addAction('Color…',lambda:self.guard(self.result_color))
            menu.addAction('Transparency…',lambda:self.guard(self.result_transparency))
            menu.addAction('Toggle contour representation',lambda:self.guard(lambda:self.toggle_result_contours(entry.Name)))
            menu.addAction('Export…',lambda:self.guard(self.export_result_parts))
            for op in ['Hide parts','Show parts','Merge parts','Remove parts']:menu.addAction(op,lambda checked=False,o=op:self.guard(lambda:self.results_operation(o,'Result parts')))
        menu.exec(self.tree.viewport().mapToGlobal(self.tree.viewport().rect().center()))

    def result_color(self):
        color=QtWidgets.QColorDialog.getColor(parent=self)
        if color.isValid():self.results.Color(self.selected_names('Result parts'),color.red(),color.green(),color.blue());self.refresh()
    def result_transparency(self):
        opacity,ok=QtWidgets.QInputDialog.getInt(self,'Transparency','Opacity (0 transparent, 255 opaque)',255,0,255)
        if ok:self.results.Transparency(self.selected_names('Result parts'),opacity);self.refresh()
    def toggle_result_contours(self,name):self.results.Contours(self.selected_names('Result parts'),not self.controller.GetResultPart(name).ResultRepresentation);self.refresh()
    def export_result_parts(self):
        format,ok=QtWidgets.QInputDialog.getItem(self,'Export result parts','Format',list(self.results.ExportFormats),0,False)
        if not ok:return
        path,_=QtWidgets.QFileDialog.getSaveFileName(self,'Export result parts')
        if path:self.run_operation(self.results.ExportParts(self.selected_names('Result parts'),path,format))
    def deformation_dialog(self):
        if not self.controller.ResultsInitialized:raise ValueError('Open results first.')
        dialog=QtWidgets.QDialog(self);dialog.setWindowTitle('Deformation');layout=QtWidgets.QFormLayout(dialog)
        variable=QtWidgets.QComboBox();variable.addItems([str(k) for k in FeResults.GetPossibleDeformationFieldOutputNamesMap().Keys]);variable.setCurrentText(self.session.Presentation.GetDeformationVariable())
        mode=QtWidgets.QComboBox();mode.addItems([str(v) for v in Enum.GetValues(DeformationScaleFactorTypeEnum)]);mode.setCurrentText(str(self.session.Presentation.GetDeformationType()))
        factor=QtWidgets.QDoubleSpinBox();factor.setRange(-1e12,1e12);factor.setDecimals(6);factor.setValue(self.session.Presentation.GetDeformationFactor())
        layout.addRow('Variable',variable);layout.addRow('Scale',mode);layout.addRow('Factor',factor)
        self.dialog_buttons(dialog,layout)
        if dialog.exec():self.results.Deformation(variable.currentText(),mode.currentText(),Single(factor.value()));self.refresh()

    @staticmethod
    def dialog_buttons(dialog,layout):
        buttons=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok|QtWidgets.QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);layout.addRow(buttons)

    def complex_dialog(self):
        if not self.controller.ContainsComplexResults:raise ValueError('The current result has no complex fields.')
        dialog=QtWidgets.QDialog(self);dialog.setWindowTitle('Complex results');layout=QtWidgets.QFormLayout(dialog)
        mode=QtWidgets.QComboBox();mode.addItems([str(v) for v in Enum.GetValues(ComplexResultTypeEnum)]);mode.setCurrentText(str(self.controller.CurrentResult.ComplexResultType))
        angle=QtWidgets.QDoubleSpinBox();angle.setRange(-36000,36000);angle.setValue(self.controller.CurrentResult.ComplexAngleDeg)
        layout.addRow('Representation',mode);layout.addRow('Angle [degrees]',angle);self.dialog_buttons(dialog,layout)
        if dialog.exec():self.results.Complex(mode.currentText(),Single(angle.value()));self.refresh()

    def select_result_units(self):
        from CaeGlobals import UnitSystemType
        units=[str(v) for v in Enum.GetValues(UnitSystemType) if str(v)!='Undefined']
        value,ok=QtWidgets.QInputDialog.getItem(self,'Results properties','Unit system',units,units.index('UNIT_LESS'),False)
        if not ok:raise RuntimeError('Result unit selection cancelled.')
        return Enum.Parse(UnitSystemType,value)
    def set_result_units(self):
        self.controller.SetResultsUnitSystem(self.select_result_units());self.refresh()
    def change_symbols(self,value):
        if value:self.controller.DrawSymbols(value,False);self.refresh()
    def presentation_dialog(self,family):
        from presentation_widgets import PresentationDialog
        dialog=PresentationDialog(self,family);dialog.exec()
    def transformations_dialog(self):
        if not self.controller.ResultsInitialized:raise ValueError('Open results first.')
        from presentation_widgets import TransformationsDialog
        TransformationsDialog(self).exec()
    def remove_section(self):self.controller.RemoveSectionView(False);self.refresh()
    def remove_exploded(self):self.controller.RemoveExplodedView(True);self.refresh()
    def remove_annotations(self):self.controller.Annotations.RemoveCurrentArrowAnnotations();self.refresh()
    def annotate(self):
        kind,ok=QtWidgets.QInputDialog.getItem(self,'Annotation','Type',['Node','Element','Edge','Surface','Part','Distance','Angle','Circle','Text'],0,False)
        if not ok:return
        text,ok=QtWidgets.QInputDialog.getText(self,'Annotation','Part name or IDs separated by commas (Text uses the last picked point)')
        if not ok:return
        c=self.controller.Annotations
        if kind=='Part':c.AddPartAnnotation(text)
        elif kind=='Text':
            content,ok=QtWidgets.QInputDialog.getMultiLineText(self,'Text annotation','Text')
            if ok:c.AddTextAnnotation(c.GetFreeAnnotationName(),content,Array[__import__('System').Double](self.last_pick_point or [0,0,0]))
        else:
            ids=[int(v.strip()) for v in text.split(',')]
            counts={'Node':1,'Element':1,'Edge':1,'Surface':1,'Distance':2,'Angle':3,'Circle':3}
            if len(ids)!=counts[kind]:raise ValueError('Enter '+str(counts[kind])+' IDs.')
            getattr(c,'Add'+kind+'Annotation')(*ids)
        self.refresh()

    def play_animation(self):
        self.animation_timer.stop();self.animation_count=self.results.Animate(self.animation_type.currentText(),self.frames.value());self.animation_frame=0
        self.animation_delta=-abs(self.animation_options['step']) if self.animation_options['backward'] else abs(self.animation_options['step'])
        self.frame_slider.blockSignals(True);self.frame_slider.setRange(0,self.animation_count-1);self.frame_slider.setValue(0);self.frame_slider.blockSignals(False)
        self.refresh();self.show_frame(self.animation_count-1 if self.animation_options['backward'] else min(self.animation_count-1,self.animation_options['first']));self.animation_timer.start(max(1,round(1000/self.animation_options['fps'])))
    def next_frame(self):
        first=min(self.animation_options['first'],self.animation_count-1);last=min(self.animation_count-1,self.animation_options['last'] if self.animation_options['last'] is not None else self.animation_count-1);value=self.animation_frame+self.animation_delta;style=self.animation_options['style']
        if value<first or value>last:
            if style=='Once':value=max(first,min(last,value));self.animation_timer.stop()
            elif style=='Loop':value=last if value<first else first
            else:self.animation_delta=-self.animation_delta;value=first if value<first else last
        # Set directly: a Swing endpoint can repeat, matching the original timer.
        self.frame_slider.blockSignals(True);self.frame_slider.setValue(value);self.frame_slider.blockSignals(False);self.show_frame(value)
    def show_frame(self,frame):
        if self.animation_frame is None:return
        if getattr(self,'animation_scene_stale',False):self.animation_scene_stale=False
        # FrmMain.SetAnimationFrame -> vtkControl.SetAnimationFrame (the original FrmAnimation's frame)
        self.animation_frame=frame;self.viewport.host.SetAnimationFrame(frame,self.animation_options['all_frames']);self.results.AnimationFrame(frame)
    def show_original_animation_frame(self,frame,all_frames):
        """FrmMain.SetAnimationFrame from the original FrmAnimation: the view already shows the frame
        (OriginalViewHost); the toolkit follows the frame number."""
        self.animation_frame=frame;self.results.AnimationFrame(frame)
    def save_original_animation(self,name,arguments):
        """FrmMain.SaveAnimationAsImages/AsAVI: OriginalViewHost writes them with vtkControl."""
        return
    def stop_animation(self,redraw=True):
        self.animation_timer.stop();was=self.animation_frame is not None;self.animation_frame=None
        if was and redraw and self.controller.ResultsInitialized:self.controller.DrawResults(False);self.refresh()

    def capture(self,path,transparent=False,magnification=1):
        """FrmMain.CaptureViewport / SaveAutomationScreenshot: vtkControl.RenderToPNG."""
        self.vtk.RenderToPNG(str(path),bool(transparent),int(magnification))
    def capture_dialog(self):
        from PrePoMax import CaptureViewportProperties
        from PrePoMax.Forms import ViewCaptureViewportProperties
        from PrePoMaxX.UI import PropertySheet
        from application_widgets import SheetDialog
        properties=self.current_capture_properties()
        def capture():
            if self.capture_viewport(properties):self.capture_properties=properties
        SheetDialog(self,'Capture viewport',PropertySheet(ViewCaptureViewportProperties(properties)),capture).exec()
    def current_capture_properties(self):
        from PrePoMax import CaptureViewportProperties
        return getattr(self,'capture_properties',None) or CaptureViewportProperties(self.controller.GetWorkDirectory(),'Viewport')
    def capture_now(self):
        """tsmiCaptureViewport: capture with the current Capture Viewport properties, no form."""
        self.capture_viewport(self.current_capture_properties())
    def capture_viewport(self,properties):
        """FrmMain.CaptureViewport."""
        import tempfile
        from CaeGlobals import CaeException
        if not properties.SaveToFile and not properties.CopyToClipboard:
            raise CaeException('Select to save the picture to a file, to copy it to the clipboard or both.')
        QImage=__import__('PyQt6.QtGui',fromlist=['QImage']).QImage
        if properties.SaveToFile:
            path=str(properties.GetFileName())
            if Path(path).exists() and QtWidgets.QMessageBox.warning(self,'Warning',"The file '"+path+"' already exists. Replace it?",QtWidgets.QMessageBox.StandardButton.Yes|QtWidgets.QMessageBox.StandardButton.No)!=QtWidgets.QMessageBox.StandardButton.Yes:return False
            self.capture(path,properties.TransparentBackground,properties.Magnification)
            if properties.CopyToClipboard:QtWidgets.QApplication.clipboard().setImage(QImage(path))
            self.output.appendPlainText('Viewport captured into: '+path)
        else:
            with tempfile.TemporaryDirectory(prefix='prepomaxx-capture-') as folder:
                target=str(Path(folder)/'viewport.png');self.capture(target,properties.TransparentBackground,properties.Magnification)
                QtWidgets.QApplication.clipboard().setImage(QImage(target))
        if properties.CopyToClipboard:self.output.appendPlainText('Viewport captured to the clipboard.')
        return True
    def export_animation(self,path,fps=20,swing=False):
        """The animation of the original FrmAnimation saved by vtkControl: PNG frames (SaveAnimationAsImages) or AVI
        (SaveAnimationAsAVI; uncompressed off Windows, see X/Domain/vtkControl/AviWriter.Portable.cs)."""
        if self.animation_count<1 or self.animation_frame is None:raise ValueError('Prepare an animation with Play first.')
        self.animation_timer.stop();first=min(self.animation_options['first'],self.animation_count-1);last=min(self.animation_count-1,self.animation_options['last'] if self.animation_options['last'] is not None else self.animation_count-1)
        step=max(1,self.animation_options['step']);frames=Array[Int32]([first,last]);path=Path(path)
        if path.suffix.lower()=='.png':self.vtk.SaveAnimationAsImages(str(path),frames,step,bool(self.animation_options['all_frames']),bool(swing))
        elif path.suffix.lower()=='.avi':self.vtk.SaveAnimationAsAVI(str(path),frames,step,int(fps),bool(self.animation_options['all_frames']),bool(swing),False)
        else:raise ValueError('Choose PNG frames or AVI.')
    def export_animation_dialog(self):
        formats=['PNG frames (*.png)','AVI (*.avi)']
        path,_=QtWidgets.QFileDialog.getSaveFileName(self,'Export animation','',';;'.join(formats))
        if path:self.export_animation(path,self.animation_options['fps'],self.animation_options['style']=='Swing')
    def export_field(self):
        path,_=QtWidgets.QFileDialog.getSaveFileName(self,'Export current field','','CSV (*.csv)')
        if path:self.results.ExportField(path)
    def history_data(self,name=None):
        from history_widgets import show_history
        if name is None:
            name,ok=QtWidgets.QInputDialog.getItem(self,'History output','Set',list(self.controller.GetHistoryResultSetNames()),0,False)
            if not ok:return
        show_history(self,name)

    def open_result_leaf(self,entry):
        if entry.Family=='Result field components':
            current=self.controller.CurrentFieldData;self.results.Field(entry.Step,entry.Name,current.StepId,current.StepIncrementId);self.refresh()
        else:
            # FrmMain.ModelTree_EditEvent: HistoryResultData -> ViewResultHistoryOutputData (original FrmViewResultHistoryOutput).
            from CaeResults import HistoryResultData
            data=entry.Item if isinstance(entry.Item,HistoryResultData) else HistoryResultData(entry.Step.split('|')[0],entry.Name,None)
            self.show_original_form('ViewResultHistoryOutputData',data)
    def results_leaf_menu(self,entry,position):
        menu=QtWidgets.QMenu(self);menu.addAction('View',lambda:self.guard(lambda:self.open_result_leaf(entry)));menu.addAction('Remove',lambda:self.guard(lambda:self.remove_result_leaf(entry)))
        if entry.Family=='Result history components':
            menu.addAction('Add to XY plot',lambda:self.guard(lambda:self.plot_result_leaf(entry)))
        menu.exec(self.tree.viewport().mapToGlobal(position))
    def remove_result_leaf(self,entry):
        names=Array[String]([entry.Name])
        if entry.Family=='Result field components':self.controller.RemoveResultFieldOutputComponentsCommand(entry.Step,names)
        elif entry.Family=='Result history fields':self.controller.RemoveResultHistoryFieldsCommand(entry.Step,names)
        else:
            set_name,field=entry.Step.split('|',1);self.controller.RemoveResultHistoryFieldsCommand(set_name,field,names)
        self.refresh()
    def plot_result_leaf(self,entry):
        from CaeResults import HistoryResultData
        name,field=entry.Step.split('|',1)
        if self.plot_panel.current()<0:self.plot_panel.add()
        self.plot_panel.session.AddHistory(self.plot_panel.current(),HistoryResultData(name,field,entry.Name));self.plot_panel.rebuild();self.plot_dock.show()
    def remove_raw_history(self,name):self.controller.RemoveResultHistoryOutputsCommand(Array[String]([name]));self.refresh()

    def animation_options_dialog(self):
        dialog=QtWidgets.QDialog(self);dialog.setWindowTitle('Animation options');layout=QtWidgets.QFormLayout(dialog);entries={}
        for name,label,maximum in [('first','First frame',1000),('last','Last frame (0 = all)',1000),('step','Increment step',1000),('fps','Frames per second',120)]:
            edit=QtWidgets.QSpinBox();edit.setRange(0 if name in ['first','last'] else 1,maximum);edit.setValue((self.animation_options[name] or 0)+(1 if name=='first' else 0));entries[name]=edit;layout.addRow(label,edit)
        style=QtWidgets.QComboBox();style.addItems(['Once','Loop','Swing']);style.setCurrentText(self.animation_options['style']);limits=QtWidgets.QCheckBox('Use scalar limits from all frames');limits.setChecked(self.animation_options['all_frames']);back=QtWidgets.QCheckBox('Play backward');back.setChecked(self.animation_options['backward']);layout.addRow('Style',style);layout.addRow(limits);layout.addRow(back);self.dialog_buttons(dialog,layout)
        if dialog.exec():
            if entries['last'].value() and entries['last'].value()<entries['first'].value():raise ValueError('The last frame must be at least the first frame.')
            self.animation_options.update({name:edit.value() for name,edit in entries.items()});self.animation_options['first']=max(0,self.animation_options['first']-1);self.animation_options['last']=self.animation_options['last']-1 if self.animation_options['last'] else None;self.animation_options.update(style=style.currentText(),all_frames=limits.isChecked(),backward=back.isChecked())

"""C4 analysis/results UI: commands operate on the live original Controller."""
from pathlib import Path
from PyQt6 import QtCore,QtWidgets
from System import Array,String,Single,Enum
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
            box=QtWidgets.QComboBox();box.setMinimumContentsLength(6);box.setSizeAdjustPolicy(QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon);box.setMaximumWidth(240);box.setToolTip(label);self.result_toolbar.addWidget(box);self.result_boxes[label]=box
            box.currentTextChanged.connect(lambda value,key=label:self.guard(lambda:self.result_changed(key,value)))
        self.symbols=QtWidgets.QComboBox();self.symbols.setToolTip('Original symbols / step');self.viewport_toolbar.addWidget(self.symbols)
        self.symbols.currentTextChanged.connect(lambda value:self.guard(lambda:self.change_symbols(value)))
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
        self.frame_slider=QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal);self.frame_slider.setMaximumWidth(130);self.animation_toolbar.addWidget(self.frame_slider)
        self.frame_slider.valueChanged.connect(lambda frame:self.guard(lambda:self.show_frame(frame)))
        self.result_toolbar.hide();self.animation_toolbar.hide()
        self.view.addItem('Results')

    def update_results_ui(self):
        if hasattr(self,'symbols'):
            self.symbols.blockSignals(True);self.symbols.clear();self.symbols.addItems(['None','Model','Result']+list(self.controller.GetStepNames()));self.symbols.setCurrentText(self.controller.GetDrawSymbolsForStep() or 'None');self.symbols.blockSignals(False)
        active=self.controller.CurrentView==ViewGeometryModelResults.Results and self.controller.ResultsInitialized
        self.result_toolbar.setVisible(active);self.animation_toolbar.setVisible(active)
        if not active:return
        field=self.controller.CurrentFieldData
        values={'Result':list(self.results.ResultNames),'Field':list(self.results.Fields),'Component':list(self.results.Components(field.Name)),'Step':[str(v) for v in self.results.Steps],'Increment':[str(v) for v in self.results.Increments(field.StepId)]}
        selected={'Result':self.controller.AllResults.GetCurrentResultName(),'Field':field.Name,'Component':field.Component,'Step':str(field.StepId),'Increment':str(field.StepIncrementId),'View':str(self.controller.ViewResultsType)}
        for label,box in self.result_boxes.items():
            box.blockSignals(True)
            if label in values:box.clear();box.addItems(values[label])
            box.setCurrentText(selected[label]);box.blockSignals(False)

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
        self.show_editor(ResultsDialog(self,family,name),family)

    def run_job(self,check=False,name=None):
        name=self.job_name(name);self.monitor_job(name)
        self.run_operation(self.results.RunJob(name,check),cancel=lambda:self.results.Kill(name))

    def monitor_job(self,name=None):
        monitor=JobMonitor(self,self.job_name(name));monitor.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose);self.monitors.append(monitor);monitor.show();return monitor

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
        self.animation_frame=frame;self.scene.set_frame(frame);self.scene.presentation.rescale_frame(frame,self.animation_options['all_frames']);self.results.AnimationFrame(frame);self.update_follower();self.render()
    def stop_animation(self,redraw=True):
        self.animation_timer.stop();was=self.animation_frame is not None;self.animation_frame=None
        if was and redraw and self.controller.ResultsInitialized:self.controller.DrawResults(False);self.refresh()

    def capture(self,path,transparent=False,magnification=1):
        from vtkmodules.vtkRenderingCore import vtkWindowToImageFilter
        from vtkmodules.vtkIOImage import vtkPNGWriter
        window=self.viewport.GetRenderWindow();old=window.GetAlphaBitPlanes();alpha=self.renderer.GetBackgroundAlpha();gradient=self.renderer.GetGradientBackground();window.SetAlphaBitPlanes(1)
        try:
            self.renderer.SetBackgroundAlpha(0 if transparent else 1)
            if transparent:self.renderer.GradientBackgroundOff()
            self.render();image=vtkWindowToImageFilter();image.SetInput(window);image.SetScale(magnification)
            if transparent:image.SetInputBufferTypeToRGBA()
            else:image.SetInputBufferTypeToRGB()
            image.ReadFrontBufferOff();image.Update();writer=vtkPNGWriter();writer.SetFileName(str(path));writer.SetInputConnection(image.GetOutputPort());writer.Write()
            if writer.GetErrorCode():raise RuntimeError('The viewport capture could not be written.')
        finally:window.SetAlphaBitPlanes(old);self.renderer.SetBackgroundAlpha(alpha);self.renderer.SetGradientBackground(gradient);self.render()
    def capture_dialog(self):
        from PrePoMax import CaptureViewportProperties
        from PrePoMax.Forms import ViewCaptureViewportProperties
        from PrePoMaxX.UI import PropertySheet
        from application_widgets import SheetDialog
        properties=getattr(self,'capture_properties',None) or CaptureViewportProperties(self.controller.GetWorkDirectory(),'Viewport')
        def capture():
            import tempfile
            path=properties.GetFileName() if properties.SaveToFile else None
            if path is None:
                with tempfile.TemporaryDirectory(prefix='prepomaxx-capture-') as folder:
                    target=str(Path(folder)/'viewport.png');self.capture(target,properties.TransparentBackground,properties.Magnification)
                    if properties.CopyToClipboard:QtWidgets.QApplication.clipboard().setImage(__import__('PyQt6.QtGui',fromlist=['QImage']).QImage(target))
            else:
                self.capture(path,properties.TransparentBackground,properties.Magnification)
                if properties.CopyToClipboard:QtWidgets.QApplication.clipboard().setImage(__import__('PyQt6.QtGui',fromlist=['QImage']).QImage(path))
            self.capture_properties=properties
        SheetDialog(self,'Capture viewport',PropertySheet(ViewCaptureViewportProperties(properties)),capture).exec()
    def export_animation(self,path,fps=20,swing=False):
        if self.animation_count<1 or self.animation_frame is None:raise ValueError('Prepare an animation with Play first.')
        self.animation_timer.stop();first=min(self.animation_options['first'],self.animation_count-1);last=min(self.animation_count-1,self.animation_options['last'] if self.animation_options['last'] is not None else self.animation_count-1);indices=list(range(first,last+1,max(1,self.animation_options['step'])))
        if swing:indices+=list(range(last,first-1,-max(1,self.animation_options['step'])))
        path=Path(path);old=self.animation_frame
        try:
            if path.suffix.lower()=='.png':
                for n,index in enumerate(indices):self.show_frame(index);self.capture(str(path.with_name(str(n+1).zfill(len(str(len(indices))))+'_'+path.name)))
            else:
                # VTK's original AVI writer is platform-specific. Try the native pinned
                # VTK video modules explicitly; never install or select an encoder silently.
                from vtkmodules.vtkRenderingCore import vtkWindowToImageFilter
                if path.suffix.lower()=='.avi':
                    import importlib.util
                    if importlib.util.find_spec('vtkmodules.vtkIOAVI'):
                        from vtkmodules.vtkIOAVI import vtkAVIWriter
                        writer=vtkAVIWriter()
                    else:
                        from avi_writer import AviWriter
                        self.render();image=vtkWindowToImageFilter();image.SetInput(self.viewport.GetRenderWindow());image.SetInputBufferTypeToRGB();image.ReadFrontBufferOff();image.Update();dimensions=image.GetOutput().GetDimensions();avi=AviWriter(path,dimensions[0],dimensions[1],fps,len(indices))
                        try:
                            for index in indices:self.show_frame(index);image.Modified();image.Update();avi.write(image.GetOutput())
                            avi.finish()
                        except BaseException:avi.abort();raise
                        return
                elif path.suffix.lower()=='.ogv':
                    from vtkmodules.vtkIOOggTheora import vtkOggTheoraWriter
                    writer=vtkOggTheoraWriter()
                else:raise ValueError('Choose PNG frames, AVI or OGV.')
                image=vtkWindowToImageFilter();image.SetInput(self.viewport.GetRenderWindow());image.SetInputBufferTypeToRGB();image.ReadFrontBufferOff();writer.SetInputConnection(image.GetOutputPort());writer.SetFileName(str(path));writer.SetRate(fps);writer.Start()
                for index in indices:self.show_frame(index);image.Modified();writer.Write()
                writer.End()
                if not path.exists() or not path.stat().st_size:raise RuntimeError('The pinned VTK encoder did not create the animation.')
        finally:self.show_frame(old)
    def export_animation_dialog(self):
        import importlib.util
        formats=['PNG frames (*.png)','AVI (*.avi)']
        if importlib.util.find_spec('vtkmodules.vtkIOOggTheora'):formats.append('Ogg Theora (*.ogv)')
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
            from history_widgets import show_history
            show_history(self,entry.Step.split('|')[0])
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

"""Original application/automation actions and native presentation lifecycle."""
from pathlib import Path
from PyQt6 import QtCore,QtGui,QtWidgets
from System import Action,Array,Int32,String,Double,Enum,Func
from CaeGlobals import Selection,SelectionNodeIds,vtkSelectOperation,vtkSelectItem
from PrePoMax import ViewGeometryModelResults,SettingsContainer,CaptureViewportProperties
from PrePoMaxX.UI import ApplicationSession,PropertySheet
from application_widgets import SettingsDialog,HistoryDialog,KeywordDialog,LibraryDialog,UserViewsDialog,SheetDialog

class ApplicationWorkbench:
    def build_application_ui(self):
        self.application=ApplicationSession(self.session);self.application_actions={};self.automation_working=False
        self.post_delegate=Action[Action](lambda cb:self.dispatcher.post(cb));self.session.Presentation.PostToUi=self.post_delegate
        self.busy_delegate=Func[String](self.automation_busy_reason);self.session.Presentation.AutomationBusyReason=self.busy_delegate
        self.exit_delegate=Action(self.close);self.session.Presentation.AutomationExit=self.exit_delegate;self.session.Presentation.IsWindowHidden=False
        file=self.menuBar().addMenu('File');edit=self.menuBar().addMenu('Edit');tools=self.menuBar().addMenu('Tools');self.geometry_menus.extend([file,edit,tools])
        # Reuse toolbar actions, including their document/task locks.
        for title in ['New…','Open…','Save','Save As…']:file.addAction(self.actions[title])
        self.recent_menu=file.addMenu('Recent files');self.recent_menu.aboutToShow.connect(self.rebuild_recent)
        def add(menu,title,callback,shortcut=None):
            action=menu.addAction(title);action.triggered.connect(lambda checked=False:self.guard(callback));self.application_actions[title]=action
            if shortcut:action.setShortcut(shortcut)
            return action
        add(file,'Run history file…',self.open_history)
        add(file,'Import materials…',self.import_materials)
        for label,abaqus in [('Export CalculiX model…',False),('Export Abaqus model…',True)]:add(file,label,lambda value=abaqus:self.export_model(value))
        add(file,'Export 3MF…',self.export_3mf);add(file,'Export Python journal…',self.export_journal);file.addSeparator();add(file,'Close all results',self.close_results);add(file,'Exit',self.close,QtGui.QKeySequence.StandardKey.Quit)
        for title in ['Undo','Redo']:edit.addAction(self.actions[title])
        add(edit,'Edit commands…',lambda:self.show_editor(HistoryDialog(self),'History'))
        add(edit,'Regenerate history…',self.regenerate)
        add(edit,'CalculiX keywords…',lambda:self.show_editor(KeywordDialog(self),'Keywords'))
        add(edit,'Select by IDs…',self.select_ids,'Ctrl+I');add(edit,'Clear selection',self.clear_selection,'Escape')
        add(edit,'Find…',self.find_dialog,QtGui.QKeySequence.StandardKey.Find)
        add(edit,'Expand tree',self.tree.expandAll);add(edit,'Collapse tree',self.tree.collapseAll)
        add(tools,'Query…',self.query_dialog);add(tools,'Search contact pairs…',self.contact_search_dialog);add(tools,'Settings…',self.settings_dialog);add(tools,'Material library…',lambda:self.show_editor(LibraryDialog(self),'Library'))
        add(tools,'Import parameters…',lambda:self.parameters_file(True));add(tools,'Export parameters…',lambda:self.parameters_file(False));add(tools,'Check model',self.check_model)
        self.build_script_panel();self.build_plot_panel();self.build_advisor()
        tools.addAction(self.advisor_dock.toggleViewAction());tools.addAction(self.script_dock.toggleViewAction());tools.addAction(self.plot_dock.toggleViewAction())
        add(tools,'Run Python file…',self.run_python_file)
        automation=tools.addMenu('Automation server');self.automation_menu=automation
        add(automation,'Start server',self.start_automation);add(automation,'Stop server',self.application.Automation.Stop)
        add(automation,'Generate access token',self.generate_token);add(automation,'Clear access token',self.clear_token);add(automation,'Connection details…',self.automation_details)
        view=self.menuBar().addMenu('Camera');self.geometry_menus.append(view)
        for name,direction,up in [('Front',(0,-1,0),(0,0,1)),('Back',(0,1,0),(0,0,1)),('Top',(0,0,1),(0,1,0)),('Bottom',(0,0,-1),(0,-1,0)),('Left',(-1,0,0),(0,0,1)),('Right',(1,0,0),(0,0,1)),('Isometric',(1,-1,1),(0,0,1))]:add(view,name,lambda d=direction,u=up:self.camera_view(d,u))
        add(view,'Parallel projection',lambda:self.projection(True));add(view,'Perspective projection',lambda:self.projection(False));add(view,'User views…',lambda:self.show_editor(UserViewsDialog(self),'User views'));add(view,'Follower view…',self.follower_dialog);add(view,'Disable follower view',lambda:self.controller.RemoveCurrentFollowerView())
        for mode in ['Model edges','Element edges','Wireframe','No edges']:add(view,mode,lambda m=mode:self.set_edge_mode(m))
        add(view,'Show all parts',lambda:self.visible_parts('Show'));add(view,'Hide all parts',lambda:self.visible_parts('Hide'));add(view,'Invert visible parts',lambda:self.visible_parts('Invert'))
        for operation in ['Color','Transparency','Reset color']:add(view,'Part '+operation.lower()+'…',lambda op=operation:self.part_appearance(op))
        add(view,'Edit annotation text…',self.edit_annotation)
        help_menu=self.menuBar().addMenu('Help');add(help_menu,'About',self.about_dialog)
        self.tree.itemSelectionChanged.connect(self.tree_selection_changed)
        self.tree.itemChanged.connect(self.rename_tree_item)
        self.tree.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tree_shortcuts=[]
        for key,callback in [('F2',self.rename_selected),('Delete',self.remove_selected),('Ctrl+D',self.duplicate_selected)]:
            shortcut=QtGui.QShortcut(QtGui.QKeySequence(key),self.tree);shortcut.setContext(QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut);shortcut.activated.connect(lambda cb=callback:self.guard(cb));self.tree_shortcuts.append(shortcut)
        self.path_shortcuts=[]
        for title,key in [('New…',QtGui.QKeySequence.StandardKey.New),('Open…',QtGui.QKeySequence.StandardKey.Open),('Save As…',QtGui.QKeySequence.StandardKey.SaveAs)]:self.actions[title].setShortcut(key)
        self.apply_preferences()

    def automation_busy_reason(self):
        if self.operation_task is not None:return 'PrePoMax is busy with an operation.'
        if self.active_editor is not None:return 'A dialog is open: '+self.active_editor.windowTitle()
        if QtWidgets.QApplication.activeModalWidget() is not None:return 'A modal dialog is open.'
        if any(d.isVisible() for d in self.findChildren(QtWidgets.QDialog)):return 'A dialog is open.'
        if self.controller.SavingFile:return 'PrePoMax is saving a file.'
        return None
    def set_application_busy(self,busy):
        self.automation_working=busy
        if self.operation_task is not None or self.active_editor is not None:return
        for menu in self.geometry_menus:menu.setEnabled(not busy)
        for action in self.actions.values():action.setEnabled(not busy)
        for widget in [self.tree,self.view,self.viewport,self.pick_mode,self.result_toolbar,self.animation_toolbar,self.symbols]:widget.setEnabled(not busy)
        if not busy:self.refresh()
    def settings_dialog(self):SettingsDialog(self).exec()
    def persist_preferences(self):
        if self.preferences_path:self.application.SavePreferences(str(self.preferences_path))
    def apply_preferences(self):
        settings=self.controller.Settings;graphics=settings.Graphics
        top,bottom=graphics.TopColor,graphics.BottomColor;self.renderer.SetBackground(bottom.R/255,bottom.G/255,bottom.B/255);self.renderer.SetBackground2(top.R/255,top.G/255,top.B/255);self.renderer.SetGradientBackground(str(graphics.BackgroundType)=='Gradient')
        window=self.viewport.GetRenderWindow();window.SetPointSmoothing(graphics.PointSmoothing);window.SetLineSmoothing(graphics.LineSmoothing)
        interactor=window.GetInteractor();style=interactor.GetInteractorStyle()
        if hasattr(style,'SetMotionFactor'):style.SetMotionFactor(10*settings.Navigation.RotateSensitivity)
        if hasattr(style,'SetMouseWheelMotionFactor'):style.SetMouseWheelMotionFactor(settings.Navigation.ZoomSensitivity*(-1 if settings.Navigation.InvertZoom else 1))
        self.apply_view_widgets();self.render()
    def rebuild_recent(self):
        self.recent_menu.clear()
        for path in self.controller.Settings.General.GetRecentFiles():self.recent_menu.addAction(str(path),lambda p=str(path):self.guard(lambda:self.open_with_discard(p)))
        self.recent_menu.addAction('Clear recent files',lambda:self.controller.ClearRecentFiles())
    def open_with_discard(self,path):
        if self.confirm_discard():self.open(path)
    def open_history(self):
        path,_=QtWidgets.QFileDialog.getOpenFileName(self,'Run original history','','PrePoMax history (*.pmh)')
        if path and self.confirm_discard():self.run_operation(self.application.Open(path),self.refresh)
    def regenerate(self):
        dialog=QtWidgets.QDialog(self);dialog.setWindowTitle('Regenerate history');layout=QtWidgets.QFormLayout(dialog);scope=QtWidgets.QComboBox();scope.addItems(['All','PreProcess','Analysis','PostProcess']);files=QtWidgets.QCheckBox('Choose other input files');mesh=QtWidgets.QCheckBox('Edit meshing parameters');layout.addRow('Scope',scope);layout.addRow(files);layout.addRow(mesh);self.dialog_buttons(dialog,layout)
        if dialog.exec():self.run_operation(self.application.Regenerate(files.isChecked(),mesh.isChecked(),scope.currentText()))
    def import_materials(self):
        path,_=QtWidgets.QFileDialog.getOpenFileName(self,'Import materials','','Model input (*.inp)')
        if path:self.application.ImportMaterials(path);self.refresh()
    def parameters_file(self,importing):
        choose=QtWidgets.QFileDialog.getOpenFileName if importing else QtWidgets.QFileDialog.getSaveFileName
        path,_=choose(self,'Parameters','','Parameters (*.csv)')
        if path:self.application.Parameters(path,importing);self.refresh()
    def export_model(self,abaqus):
        path,_=QtWidgets.QFileDialog.getSaveFileName(self,'Export model','','Input deck (*.inp)')
        if path:self.application.Export(path,abaqus)
    def export_journal(self):
        path,_=QtWidgets.QFileDialog.getSaveFileName(self,'Export active history','','Python (*.py)')
        if path:self.application.Journal(path)
    def export_3mf(self):
        from PrePoMax import Export3mfFileProperties
        from PrePoMax.Forms import ViewExport3mfFileProperties
        path,_=QtWidgets.QFileDialog.getSaveFileName(self,'Export current view','','3MF (*.3mf)')
        if path:
            props=Export3mfFileProperties();props.FileName=path
            if SheetDialog(self,'3MF export',PropertySheet(ViewExport3mfFileProperties(props))).exec():
                self.update_export_view();self.application.Export3mf(props)
    def update_export_view(self):
        p=self.session.Presentation;up=self.renderer.GetActiveCamera().GetViewUp();axis=max(range(3),key=lambda i:abs(up[i]));closest=[0.,0.,0.];closest[axis]=1 if up[axis]>0 else -1 if up[axis]<0 else 0;p.ExportUpDirection=Array[Double](closest)
        if hasattr(self.scene,'presentation'):
            from vtkControl import vtkMaxLookupTable
            lookup=vtkMaxLookupTable();table=self.scene.presentation.table;colors=[]
            from System.Drawing import Color
            for i in range(table.GetNumberOfTableValues()):
                c=table.GetTableValue(i);colors.append(Color.FromArgb(round(c[3]*255),round(c[0]*255),round(c[1]*255),round(c[2]*255)))
            lookup.SetExportData(*table.GetTableRange(),Array[Color](colors),str(self.scene.presentation.spectrum.Mode)=='Smooth')
            p.ExportLookupTable=lookup
    def close_results(self):self.controller.ClearResultsCommand();self.view.setCurrentText('Model');self.refresh()
    def check_model(self):QtWidgets.QMessageBox.information(self,'Model validity','\n'.join(self.application.CheckModel()) or 'No invalid model items found.')
    def start_automation(self):self.application.Automation.Start();self.output.appendPlainText('Automation listening at '+self.application.Automation.EndpointUrl)
    def generate_token(self):
        if self.controller.AutomationSettings.AccessToken and QtWidgets.QMessageBox.question(self,'Automation','Replace the existing access token?')!=QtWidgets.QMessageBox.StandardButton.Yes:return
        self.application.Automation.Stop();self.application.GenerateAccessToken();self.persist_preferences();self.automation_details()
    def clear_token(self):
        if QtWidgets.QMessageBox.question(self,'Automation','Clear the token and stop the server?')==QtWidgets.QMessageBox.StandardButton.Yes:self.application.ClearAccessToken();self.persist_preferences()
    def automation_details(self):
        dialog=QtWidgets.QDialog(self);dialog.setWindowTitle('Automation connection');layout=QtWidgets.QFormLayout(dialog)
        endpoint=self.application.Automation.EndpointUrl or 'Server stopped';address=QtWidgets.QLineEdit(endpoint);address.setReadOnly(True);token=QtWidgets.QLineEdit(self.controller.AutomationSettings.AccessToken);token.setReadOnly(True);token.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        reveal=QtWidgets.QCheckBox('Show token');reveal.toggled.connect(lambda on:token.setEchoMode(QtWidgets.QLineEdit.EchoMode.Normal if on else QtWidgets.QLineEdit.EchoMode.Password));layout.addRow('Address',address);layout.addRow('Access token',token);layout.addRow(reveal);close=QtWidgets.QPushButton('Close');close.clicked.connect(dialog.accept);layout.addRow(close);dialog.exec()
    def build_script_panel(self):
        self.script_dock=QtWidgets.QDockWidget('Python',self);panel=QtWidgets.QWidget();layout=QtWidgets.QVBoxLayout(panel);self.script_edit=QtWidgets.QPlainTextEdit();self.script_edit.setFont(QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.SystemFont.FixedFont));layout.addWidget(self.script_edit)
        self.script_output=QtWidgets.QPlainTextEdit();self.script_output.setReadOnly(True);layout.addWidget(self.script_output);row=QtWidgets.QHBoxLayout();self.script_record=QtWidgets.QCheckBox('Record as one script command');row.addWidget(self.script_record)
        for label,cb in [('Open…',self.open_script),('Save…',self.save_script),('Run',self.execute_script),('Reset scope',self.application.ResetPython)]:
            button=QtWidgets.QPushButton(label);button.clicked.connect(lambda checked=False,f=cb:self.guard(f));row.addWidget(button)
        self.script_stop=QtWidgets.QPushButton('Stop');self.script_stop.clicked.connect(lambda:self.guard(self.interrupt_script));row.addWidget(self.script_stop);self.script_stop.setEnabled(False);layout.addLayout(row);self.script_dock.setWidget(panel);self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea,self.script_dock);self.script_dock.hide();self.script_file=None
    def open_script(self):
        path,_=QtWidgets.QFileDialog.getOpenFileName(self,'Open Python script','','Python (*.py)')
        if path:self.script_edit.setPlainText(Path(path).read_text());self.script_file=path
    def save_script(self):
        path,_=QtWidgets.QFileDialog.getSaveFileName(self,'Save Python script',self.script_file or '', 'Python (*.py)')
        if path:Path(path).write_text(self.script_edit.toPlainText());self.script_file=path;self.script_edit.document().setModified(False)
    def execute_script(self):
        source=self.script_edit.textCursor().selectedText().replace('\u2029','\n') or self.script_edit.toPlainText();self.script_stop.setEnabled(True)
        task=self.application.Execute(source,self.script_record.isChecked(),self.script_file,Array[String]([]))
        def done():
            self.script_stop.setEnabled(False);result=task.Result;self.script_output.appendPlainText(str(result.Output or '')+str(result.ErrorOutput or '')+str(result.Error or ''));self.refresh()
        self.run_operation(task,done,cancel=self.interrupt_script)
    def interrupt_script(self):
        if self.application.InterruptPython():self.output.appendPlainText('Python interruption requested.')
    def run_python_file(self):
        self.open_script()
        if self.script_file:self.script_dock.show();self.script_record.setChecked(True);self.execute_script()
    def build_plot_panel(self):
        from plot_widgets import PlotPanel
        self.plot_dock=QtWidgets.QDockWidget('XY plots',self);self.plot_panel=PlotPanel(self);self.plot_dock.setWidget(self.plot_panel);self.addDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea,self.plot_dock);self.plot_dock.hide()
    def capture_panel_state(self):
        from UserControls import SidePanelsState,PythonPanelState,SidePanelTypeEnum
        state=SidePanelsState();state.AdvisorPanelState=__import__('UserControls',fromlist=['AdvisorPanelState']).AdvisorPanelState();state.AdvisorPanelState.PageId=self.advisor_pages[self.advisor_index.currentIndex()].Id;state.AdvisorPanelState.VerticalScrollPosition=self.advisor_scroll.verticalScrollBar().value();state.PythonPanelState=PythonPanelState();state.PythonPanelState.ScriptText=self.script_edit.toPlainText();state.PythonPanelState.FileName=self.script_file or '';state.PythonPanelState.Modified=self.script_edit.document().isModified();state.XYPlotPanelState=self.plot_panel.session.State;state.XYPlotPanelState.SelectedPlotIndex=self.plot_panel.current()
        state.VisiblePanel=SidePanelTypeEnum.Python if self.script_dock.isVisible() else SidePanelTypeEnum.XYPlot if self.plot_dock.isVisible() else SidePanelTypeEnum.Advisor if self.advisor_dock.isVisible() else getattr(SidePanelTypeEnum,'None');self.session.Presentation.SetPendingSidePanelsState(state)
    def restore_panel_state(self,state):
        if state is None:return
        if state.PythonPanelState is not None:self.script_edit.setPlainText(state.PythonPanelState.ScriptText);self.script_file=state.PythonPanelState.FileName or None;self.script_edit.document().setModified(state.PythonPanelState.Modified)
        if state.XYPlotPanelState is not None:self.plot_panel.session.State=state.XYPlotPanelState;self.plot_panel.rebuild()
        if state.AdvisorPanelState is not None:
            index=next((i for i,p in enumerate(self.advisor_pages) if p.Id==state.AdvisorPanelState.PageId),0);self.advisor_index.setCurrentIndex(index);self.advisor_scroll.verticalScrollBar().setValue(state.AdvisorPanelState.VerticalScrollPosition)
        self.advisor_dock.setVisible(str(state.VisiblePanel)=='Advisor');self.script_dock.setVisible(str(state.VisiblePanel)=='Python');self.plot_dock.setVisible(str(state.VisiblePanel)=='XYPlot')
    def select_ids(self):
        kind,ok=QtWidgets.QInputDialog.getItem(self,'Select IDs','Item',['Node','Element','Surface','Part','Geometry','GeometryEdge','GeometrySurface'],0,False)
        if not ok:return
        text,ok=QtWidgets.QInputDialog.getText(self,'Select IDs','Comma-separated IDs or ranges (for example 1, 3-8)')
        if not ok:return
        ids=[]
        for item in text.split(','):
            parts=item.strip().split('-');ids.extend(range(int(parts[0]),int(parts[1])+1) if len(parts)==2 else [int(parts[0])])
        selection=Selection();selection.CurrentView=int(self.controller.CurrentView);selection.SelectItem=Enum.Parse(vtkSelectItem,kind);selection.Add(SelectionNodeIds(getattr(vtkSelectOperation,'None'),False,Array[Int32](ids),kind.startswith('Geometry')));self.selected=list(self.controller.GetIdsFromSelection(selection));self.controller.Selection=selection;self.controller.HighlightSelection();self.scene.show_selection(self.session.Presentation.SelectionActors);self.render()
    def clear_selection(self):self.controller.ClearSelectionHistoryAndCallSelectionChanged();self.selected=[];self.scene.show_selection([]);self.render()
    def find_dialog(self):
        dialog=QtWidgets.QDialog(self);dialog.setWindowTitle('Find');layout=QtWidgets.QFormLayout(dialog);kind=QtWidgets.QComboBox();kind.addItems(['Node','Element','Edge','Surface','Part']);id=QtWidgets.QSpinBox();id.setRange(1,2147483647);annotate=QtWidgets.QCheckBox('Add annotation');layout.addRow('Type',kind);layout.addRow('ID',id);layout.addRow(annotate);find=QtWidgets.QPushButton('Find')
        def run():self.application.Find(kind.currentText(),id.value(),annotate.isChecked());self.scene.update(self.session.Presentation.SceneActors,self.session.Presentation.RenderCommands);self.scene.show_selection(self.session.Presentation.SelectionActors);self.render()
        find.clicked.connect(lambda:self.guard(run));layout.addRow(find);dialog.show();self.find_window=dialog
    def camera_view(self,direction,up):
        camera=self.renderer.GetActiveCamera();focus=camera.GetFocalPoint();distance=camera.GetDistance();length=sum(d*d for d in direction)**.5;camera.SetPosition(*(focus[i]+direction[i]/length*distance for i in range(3)));camera.SetViewUp(*up);self.fit()
    def projection(self,parallel):self.renderer.GetActiveCamera().SetParallelProjection(parallel);self.fit()
    def set_edge_mode(self,mode):
        self.edge_mode=mode;self.element_edges.setChecked(mode=='Element edges');self.refresh()
    def apply_edge_mode(self):
        mode=getattr(self,'edge_mode','Model edges')
        for actor in self.scene.element_edge_actors:actor.SetVisibility(mode in ['Model edges','Element edges'])
        for actor in self.scene.actors:
            if mode=='Wireframe':actor.GetProperty().SetRepresentationToWireframe()
    def visible_parts(self,operation):
        mesh=self.controller.DisplayedMesh
        if mesh is None:return
        for part in list(mesh.Parts.Values):
            visible=operation=='Show' or operation=='Invert' and not part.Visible
            names=Array[String]([part.Name]);view=str(self.controller.CurrentView)
            if view=='Geometry':getattr(self.controller,('Show' if visible else 'Hide')+'GeometryPartsCommand')(names)
            elif view=='Results':getattr(self.controller,('Show' if visible else 'Hide')+'ResultPartsCommand')(names)
            else:getattr(self.controller,('Show' if visible else 'Hide')+'ModelPartsCommand')(names)
        self.refresh()
    def follower_dialog(self):
        rule=self.application.Follower();dialog=SheetDialog(self,'Follower view',rule.Properties,rule.Apply)
        row=QtWidgets.QHBoxLayout()
        for name in ['Center','Direction1','Direction2']:
            button=QtWidgets.QPushButton('Use selected node for '+name);row.addWidget(button)
            def picked(key=name):
                if len(self.selected)!=1:raise ValueError('Select one displayed node first.')
                rule.Pick(key,self.selected[0]);dialog.rebuild()
            button.clicked.connect(lambda checked=False,f=picked:self.guard(f))
        dialog.layout.insertLayout(1,row);self.show_editor(dialog,'Follower view')
    def edit_annotation(self):
        c=self.controller.Annotations;name,ok=QtWidgets.QInputDialog.getItem(self,'Edit annotation','Annotation',list(c.GetCurrentAnnotationNames()),0,False)
        if ok:
            value=c.GetCurrentAnnotation(name);text,ok=QtWidgets.QInputDialog.getMultiLineText(self,'Annotation text','Text',value.GetAnnotationText())
            if ok:value.OverriddenText=text;c.DrawAnnotations(False,True);self.refresh()
    def tree_selection_changed(self):
        if self.operation_task is not None or self.active_editor is not None:return
        entries=[i.data(0,QtCore.Qt.ItemDataRole.UserRole) for i in self.tree.selectedItems()];items=[]
        for e in entries:
            if e is None or e.Group:continue
            try:
                getter={'Parts':'GetModelPart','Geometry parts':'GetGeometryPart','Result parts':'GetResultPart','Node sets':'GetNodeSet','Element sets':'GetElementSet','Surfaces':'GetSurface','Materials':'GetMaterial','Sections':'GetSection','Constraints':'GetConstraint','Loads':'GetLoad','Boundary conditions':'GetBoundaryCondition'}.get(e.Family)
                if getter:items.append(getattr(self.controller,getter)(e.Step,e.Name) if e.Step else getattr(self.controller,getter)(e.Name))
            except Exception as error:self.output.appendPlainText(str(error))
        if items:self.controller.Highlight3DObjects(Array[__import__('System').Object](items));self.scene.show_selection(self.session.Presentation.SelectionActors);self.render()
    def rename_selected(self):
        items=self.tree.selectedItems()
        if len(items)==1 and not items[0].data(0,QtCore.Qt.ItemDataRole.UserRole).Group:items[0].setFlags(items[0].flags()|QtCore.Qt.ItemFlag.ItemIsEditable);self.tree.editItem(items[0],0)
    def rename_tree_item(self,item,column):
        e=item.data(0,QtCore.Qt.ItemDataRole.UserRole)
        if e is None or e.Group or item.text(0)==e.Name:return
        self.guard(lambda:self.application.Rename(e.Family,e.Step,e.Name,item.text(0)));self.refresh()
    def remove_selected(self):self.selected_tree_operation(False)
    def duplicate_selected(self):self.selected_tree_operation(True)
    def selected_tree_operation(self,duplicate):
        entries=[i.data(0,QtCore.Qt.ItemDataRole.UserRole) for i in self.tree.selectedItems()];entries=[e for e in entries if e is not None and not e.Group]
        if not entries:return
        family,step=entries[0].Family,entries[0].Step
        if any(e.Family!=family or e.Step!=step for e in entries):raise ValueError('Select items from one collection and step.')
        names=Array[String]([e.Name for e in entries])
        if family in ['Geometry parts','Parts']:self.run_operation(self.geometry.Execute('Remove',names)) if not duplicate else self.edit_geometry('Translate');return
        if family.startswith('Result') or family=='Jobs':
            suffix={'Jobs':'jobs','Result fields':'fields','Result histories':'histories','Result reference points':'reference points','Result coordinate systems':'coordinate systems','Result parts':'parts'}[family];self.results.Execute(('Duplicate ' if duplicate else 'Remove ')+suffix,names)
        else:getattr(self.authoring,'Duplicate' if duplicate else 'Remove')(family,step,names)
        self.refresh()
    def add_model_tree_actions(self,menu,actions,entry):
        if entry.Group:return
        c=self.controller;names=self.selected_names(entry.Family)
        if len(names)==0:names=Array[String]([entry.Name])
        def add(title,callback):actions[menu.addAction(title)]=callback
        suffixes={'Constraints':'Constraints','Contact pairs':'ContactPairs','Initial conditions':'InitialConditions','Reference points':'ModelReferencePoints','Coordinate systems':'ModelCoordinateSystems','Boundary conditions':'BoundaryCondition','Loads':'Loads','Defined fields':'DefinedFields'}
        if entry.Family in suffixes:
            for action in ['Hide','Show']:
                method=getattr(c,action+suffixes[entry.Family]+'Command')
                add(action,lambda m=method:m(entry.Step,names) if entry.Step else m(names))
        if entry.Step and entry.Family in ['Boundary conditions','Loads','Defined fields','History outputs','Field outputs']:
            suffix={'Boundary conditions':'BoundaryCondition','Loads':'Load','Defined fields':'DefinedField','History outputs':'HistoryOutput','Field outputs':'FieldOutput'}[entry.Family]
            add('Propagate to later steps',lambda:getattr(c,'Propagate'+suffix+'Command')(entry.Step,entry.Name))
        if entry.Family in ['Constraints','Contact pairs']:
            suffix='Constraints' if entry.Family=='Constraints' else 'ContactPairs'
            add('Swap master/slave',lambda:getattr(c,'SwapMasterSlave'+suffix+'Command')(names))
            add('Merge by master/slave',lambda:getattr(c,'MergeByMasterSlave'+suffix+'Command')(names))
        if entry.Family=='Element sets':add('Convert to mesh parts',lambda:c.ConvertElementSetsToMeshPartsCommand(names))
        if entry.Family=='Amplitudes':add('Add to XY plot',lambda:self.add_amplitude_plot(entry.Name))
    def add_amplitude_plot(self,name):
        if self.plot_panel.current()<0:self.plot_panel.add()
        self.plot_panel.session.AddAmplitude(self.plot_panel.current(),name);self.plot_panel.rebuild();self.plot_dock.show()
    def query_dialog(self):
        from PrePoMaxX.UI import QuerySession
        rule=QuerySession(self.controller);dialog=QtWidgets.QDialog(self);dialog.setWindowTitle('Query');dialog.resize(780,500);layout=QtWidgets.QVBoxLayout(dialog);kind=QtWidgets.QComboBox();kind.addItems(['Node','Element','Edge','Surface','Part','Distance','Angle','Circle','Assembly','Bounding box']);layout.addWidget(kind);ids=QtWidgets.QLineEdit();ids.setPlaceholderText('IDs separated by commas; leave blank to use the current selection');layout.addWidget(ids);output=QtWidgets.QPlainTextEdit();output.setReadOnly(True);layout.addWidget(output)
        def run():
            values=[int(i.strip()) for i in ids.text().split(',')] if ids.text().strip() else self.selected;needed={'Assembly':0,'Bounding box':0,'Distance':2,'Angle':3,'Circle':3}.get(kind.currentText(),1)
            if len(values)<needed:raise ValueError('Select or enter '+str(needed)+' IDs.')
            result=rule.Run(kind.currentText(),Array[Int32](values));output.appendPlainText(result);self.output.appendPlainText(result);self.scene.update(self.session.Presentation.SceneActors,self.session.Presentation.RenderCommands);self.scene.show_selection(self.session.Presentation.SelectionActors);self.render()
        row=QtWidgets.QHBoxLayout()
        for title,callback in [('Query',run),('Clear annotations',lambda:self.controller.Annotations.RemoveCurrentArrowAnnotations()),('Close',dialog.accept)]:
            button=QtWidgets.QPushButton(title);button.clicked.connect(lambda checked=False,cb=callback:self.guard(cb));row.addWidget(button)
        layout.addLayout(row);dialog.show();self.query_window=dialog
    def contact_search_dialog(self):
        from application_widgets import ContactSearchDialog
        if self.controller.Model.Mesh is None:raise ValueError('Create or import a mesh first.')
        self.show_editor(ContactSearchDialog(self),'Contact search')
    def apply_follower(self,parts,ids):
        from PrePoMaxX.UI import FollowerCameraSession
        self.follower_nodes=(list(parts),list(ids));self.follower_math=FollowerCameraSession();self.update_follower()
    def update_follower(self):
        if not getattr(self,'follower_nodes',None):return
        points=[]
        for name,id in zip(*self.follower_nodes):
            found=False
            for original,actor in zip(self.scene.drawn,self.scene.actors):
                if original.Data.Name!=name:continue
                labels=list(original.Data.Geometry.Nodes.Ids or [])
                if int(id) not in labels:continue
                points.append(actor.GetMapper().GetInput().GetPoint(labels.index(int(id))));found=True;break
            if not found:return
        camera=self.renderer.GetActiveCamera();data=self.follower_math.Step(Array[Array[Double]]([Array[Double](p) for p in points]),Array[Double](camera.GetPosition()),Array[Double](camera.GetFocalPoint()),Array[Double](camera.GetViewUp()));camera.SetPosition(*data.Position);camera.SetFocalPoint(*data.FocalPoint);camera.SetViewUp(*data.Up);self.renderer.ResetCameraClippingRange();self.render()
    def build_advisor(self):
        from PrePoMaxX.UI import AdvisorPages
        from UserControls import PanelItemLinkLabel
        self.advisor_dock=QtWidgets.QDockWidget('Advisor',self);panel=QtWidgets.QWidget();layout=QtWidgets.QVBoxLayout(panel);self.advisor_action_delegate=Action[String,Int32](lambda action,index:self.guard(lambda:self.advisor_action(action,index)));self.advisor_pages=list(AdvisorPages.Create(self.advisor_action_delegate));self.advisor_index=QtWidgets.QComboBox();self.advisor_index.addItems([p.Title for p in self.advisor_pages]);layout.addWidget(self.advisor_index);self.advisor_scroll=QtWidgets.QScrollArea();self.advisor_scroll.setWidgetResizable(True);layout.addWidget(self.advisor_scroll)
        row=QtWidgets.QHBoxLayout()
        for title,delta in [('Back',-1),('Next',1)]:
            button=QtWidgets.QPushButton(title);button.clicked.connect(lambda checked=False,d=delta:self.advisor_index.setCurrentIndex(max(0,min(len(self.advisor_pages)-1,self.advisor_index.currentIndex()+d))));row.addWidget(button)
        layout.addLayout(row)
        def show_page(index):
            page=self.advisor_pages[index];body=QtWidgets.QWidget();column=QtWidgets.QVBoxLayout(body)
            for item in page.Items:
                if isinstance(item,PanelItemLinkLabel):
                    button=QtWidgets.QPushButton(item.Text);button.clicked.connect(lambda checked=False,i=item,p=page:self.guard(lambda:self.activate_advisor(p,i)));column.addWidget(button)
                else:label=QtWidgets.QLabel(item.Text);label.setWordWrap(True);label.setTextFormat(QtCore.Qt.TextFormat.PlainText);column.addWidget(label)
            column.addStretch();old=self.advisor_scroll.takeWidget();self.advisor_scroll.setWidget(body)
            if old:old.deleteLater()
        self.advisor_index.currentIndexChanged.connect(show_page);show_page(0);self.advisor_dock.setWidget(panel);self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea,self.advisor_dock);self.advisor_dock.hide()
    def activate_advisor(self,page,item):self.view.setCurrentText(str(page.AssociatedView));item.Activate()
    def advisor_action(self,action,index):
        if action=='tsmiNew_Click':self.new_project()
        elif action=='tsmiImportFile_Click':self.import_cad()
        elif action=='tsmiEditGeometryPart_Click':
            names=list(self.geometry.Tree[0].Children)
            if not names:raise ValueError('Import geometry first.')
            self.edit_geometry('Geometry parts',names[0].Name)
        elif action=='CreateDefaultMesh':
            names=Array[String](list(self.controller.Model.Geometry.Parts.Keys));self.execute_geometry('Create mesh',names)
        elif action=='CreateSimpleMaterial':self.edit_definition('Materials')
        elif action=='tsmiMaterialLibrary_Click':self.show_editor(LibraryDialog(self),'Library')
        elif action in ['tsmiCreateSection_Click','tsmiCreateStep_Click','tsmiCreateBC_Click','tsmiCreateLoad_Click']:
            family={'tsmiCreateSection_Click':'Sections','tsmiCreateStep_Click':'Steps','tsmiCreateBC_Click':'Boundary conditions','tsmiCreateLoad_Click':'Loads'}[action];step=None
            if family in ['Boundary conditions','Loads']:
                names=list(self.controller.GetStepNames())
                if not names:raise ValueError('Create a step first.')
                step=names[0]
            self.edit_definition(family,step)
            if index>=0 and hasattr(self.active_editor,'types'):self.active_editor.types.setCurrentIndex(index)
        elif action in ['tsmiRunAnalysis_Click','tsmiResultsAnalysis_Click']:
            jobs=list(self.controller.GetJobNames())
            if not jobs:raise ValueError('Create an analysis first.')
            self.run_job(name=jobs[0]) if action=='tsmiRunAnalysis_Click' else self.open_job(jobs[0])
        elif action=='tsmiSave_Click':self.save()
        else:raise ValueError('Unknown original advisor action: '+action)
    def part_appearance(self,operation):
        from System.Drawing import Color
        from System import Byte
        names=self.selected_names('Result parts') if self.controller.CurrentView==ViewGeometryModelResults.Results else self.selected_names()
        if len(names)==0:raise ValueError('Select at least one part.')
        suffix={'Geometry':'GeometryParts','Model':'ModelParts','Results':'ResultParts'}[str(self.controller.CurrentView)]
        if operation=='Color':
            color=QtWidgets.QColorDialog.getColor(parent=self)
            if color.isValid():getattr(self.controller,'SetColorFor'+suffix+'Command')(names,Color.FromArgb(color.red(),color.green(),color.blue()))
        elif operation=='Transparency':
            value,ok=QtWidgets.QInputDialog.getInt(self,'Transparency','Opacity (0 transparent, 255 opaque)',255,0,255)
            if ok:getattr(self.controller,'SetTransparencyFor'+suffix+'Command')(names,Byte(value))
        else:getattr(self.controller,'ResetColorFor'+suffix+'Command')(names)
        self.refresh()
    def apply_view_widgets(self):
        from vtkmodules.vtkRenderingAnnotation import vtkAxesActor,vtkLegendScaleActor
        from vtkmodules.vtkInteractionWidgets import vtkOrientationMarkerWidget
        graphics=self.controller.Settings.Graphics
        if not hasattr(self,'orientation_widget'):
            self.orientation_widget=vtkOrientationMarkerWidget();axes=vtkAxesActor()
            for caption in [axes.GetXAxisCaptionActor2D(),axes.GetYAxisCaptionActor2D(),axes.GetZAxisCaptionActor2D()]:caption.GetCaptionTextProperty().SetColor(.1,.1,.1);caption.GetCaptionTextProperty().ShadowOff()
            self.orientation_widget.SetOrientationMarker(axes);self.orientation_widget.SetInteractor(self.viewport.GetRenderWindow().GetInteractor());self.orientation_widget.SetViewport(0,0,.18,.18)
        self.orientation_widget.SetEnabled(graphics.CoorSysVisibility)
        if graphics.CoorSysVisibility:self.orientation_widget.SetInteractive(graphics.WidgetHighlightEnabled)
        if not hasattr(self,'scale_actor'):
            self.scale_actor=vtkLegendScaleActor();self.scale_actor.TopAxisVisibilityOff();self.scale_actor.LeftAxisVisibilityOff();self.scale_actor.RightAxisVisibilityOff();self.scale_actor.LegendVisibilityOff();self.scale_actor.SetBottomBorderOffset(45);self.scale_actor.GetBottomAxis().GetLabelTextProperty().SetColor(.1,.1,.1);self.scale_actor.GetBottomAxis().GetTitleTextProperty().SetColor(.1,.1,.1)
        self.scale_actor.SetVisibility(graphics.ScaleWidgetVisibility)
        self.renderer.AddActor(self.scale_actor)
    def area_pick(self,x0,y0,x1,y1):
        from vtkmodules.vtkRenderingCore import vtkAreaPicker
        from vtkmodules.vtkCommonDataModel import vtkPlane
        from CaeGlobals import SelectionNodeMouse,vtkSelectBy
        picker=vtkAreaPicker();picker.AreaPick(min(x0,x1),min(y0,y1),max(x0,x1),max(y0,y1),self.renderer);frustum=picker.GetFrustum();planes=[]
        for i in range(frustum.GetNumberOfPlanes()):
            plane=vtkPlane();frustum.GetPlane(i,plane);planes.append(Array[Double](list(plane.GetOrigin())+list(plane.GetNormal())))
        index=self.pick_mode.currentIndex();kinds=[vtkSelectItem.Element,vtkSelectItem.Node,vtkSelectItem.Node,vtkSelectItem.Surface,vtkSelectItem.Part,vtkSelectItem.Geometry,vtkSelectItem.Geometry,vtkSelectItem.GeometryEdge,vtkSelectItem.GeometrySurface,vtkSelectItem.Part,vtkSelectItem.Node,vtkSelectItem.Node,vtkSelectItem.Node,vtkSelectItem.GeometryEdge,vtkSelectItem.GeometrySurface]
        mode=vtkSelectBy.Geometry if index in [5,6,7,8,9,13,14] else vtkSelectBy.Node if kinds[index]==vtkSelectItem.Node else vtkSelectBy.Surface if kinds[index]==vtkSelectItem.Surface else vtkSelectBy.Part if kinds[index]==vtkSelectItem.Part else vtkSelectBy.Element
        modifiers=QtWidgets.QApplication.keyboardModifiers();shift=bool(modifiers&QtCore.Qt.KeyboardModifier.ShiftModifier);control=bool(modifiers&(QtCore.Qt.KeyboardModifier.ControlModifier|QtCore.Qt.KeyboardModifier.MetaModifier));operation=vtkSelectOperation.Intersect if shift and control else vtkSelectOperation.Add if shift else vtkSelectOperation.Subtract if control else getattr(vtkSelectOperation,'None')
        selection=self.controller.Selection.DeepCopy(True,False) if (shift or control) and self.controller.Selection.SelectItem==kinds[index] else Selection();selection.CurrentView=int(self.controller.CurrentView);selection.SelectItem=kinds[index]
        selection.Add(SelectionNodeMouse(None,Array[Double](self.renderer.GetActiveCamera().GetDirectionOfProjection()),Array[Array[Double]](planes),x1>=x0,operation,self.controller.DisplayedMesh.GetVisiblePartIds(),None,mode,self.selection_angle.value()));self.selected=list(self.controller.GetIdsFromSelection(selection));self.controller.Selection=selection;self.controller.HighlightSelection();self.scene.show_selection(self.session.Presentation.SelectionActors);self.render();self.statusBar().showMessage('Selected IDs: '+', '.join(map(str,self.selected)))

    def about_dialog(self):
        dialog=QtWidgets.QDialog(self);dialog.setWindowTitle('About PrePoMax-X');layout=QtWidgets.QVBoxLayout(dialog)
        original=Path(__file__).resolve().parents[2]/'PrePoMax/Resources/Splash_01.png'
        if original.is_file():image=QtWidgets.QLabel();image.setPixmap(QtGui.QPixmap(str(original)).scaledToWidth(600,QtCore.Qt.TransformationMode.SmoothTransformation));layout.addWidget(image)
        label=QtWidgets.QLabel('PrePoMax-X\nPrePoMax 3.0.0 engineering code and native cross-platform UI.\nCopyright and licence: see the original LICENSE and third-party notices.');label.setWordWrap(True);layout.addWidget(label)
        links=QtWidgets.QLabel('<a href="https://prepomax.fs.um.si/">PrePoMax</a> · <a href="https://www.kimm.re.kr/eng">KIMM</a> · <a href="https://www.smartdo.co/">SmartDO</a> · <a href="https://www.capgemini.com/">Capgemini</a>');links.setOpenExternalLinks(True);layout.addWidget(links);close=QtWidgets.QPushButton('Close');close.clicked.connect(dialog.accept);layout.addWidget(close);dialog.exec()

"""Geometry/mesh menus and task-aware native operation presentation."""
from PyQt6 import QtCore, QtWidgets
from System import Array, String
from PrePoMax import ViewGeometryModelResults
from PrePoMaxX.UI import GeometrySession
from authoring_widgets import message
from geometry_widgets import GeometryDialog

class GeometryWorkbench:
    def build_geometry_menus(self):
        geometry=self.menuBar().addMenu('Geometry')
        mesh=self.menuBar().addMenu('Mesh')
        self.geometry_menus=[geometry,mesh]
        def editor(menu,label,family):
            action=menu.addAction(label)
            action.triggered.connect(lambda checked=False:self.guard(lambda:self.edit_geometry(family)))
        geometry.addAction('Import…',self.import_cad)
        geometry.addAction('Analyze geometry…',lambda:self.guard(self.analyze_geometry))
        for operation in ['Group split cells','Fuse bodies','Rename split subpart']:
            geometry.addAction(operation+'…',lambda checked=False,value=operation:self.guard(lambda:self.compound_operation(value)))
        editor(geometry,'Mesh setup…','Mesh setup')
        for family in GeometrySession.GeometryEditors:editor(geometry,family+'…',family)
        geometry.addSeparator()
        for operation in ['Create compound','Regenerate compound','Swap geometries','Shell to solid','Solid to shell','Flip STL normals']:
            geometry.addAction(operation,lambda checked=False,value=operation:self.guard(lambda:self.execute_geometry(value)))
        mesh.addAction('Create mesh',lambda:self.guard(lambda:self.execute_geometry('Create mesh')))
        mesh.addAction('Preview edge mesh',lambda:self.guard(lambda:self.execute_geometry('Preview edge mesh')))
        mesh.addSeparator()
        for family in GeometrySession.MeshEditors:editor(mesh,family+'…',family)
        mesh.addAction('Merge mesh parts',lambda:self.guard(lambda:self.execute_geometry('Merge mesh parts')))
        for nodes in [True,False]:
            mesh.addAction('Renumber '+('nodes…' if nodes else 'elements…'),lambda checked=False,value=nodes:self.guard(lambda:self.renumber(value)))
        mesh.addAction('Update nodal coordinates…',lambda:self.guard(self.update_coordinates))
        for menu in [geometry,mesh]:
            menu.addSeparator()
            for transform in GeometrySession.Transforms:editor(menu,transform+'…',transform)
            menu.addAction('Find edges by angle…',lambda:self.guard(self.find_edges))
            menu.addAction('Export selected parts…',lambda:self.guard(self.export_parts))
        dock=QtWidgets.QDockWidget('Output',self)
        self.output=QtWidgets.QPlainTextEdit();self.output.setReadOnly(True)
        dock.setWidget(self.output);self.addDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea,dock)
        dock.hide()
        self.menuBar().addAction(dock.toggleViewAction())
        self.cancel_operation=QtWidgets.QPushButton('Cancel operation')
        self.cancel_operation.clicked.connect(lambda:self.guard(self.geometry.Cancel))
        self.statusBar().addPermanentWidget(self.cancel_operation);self.cancel_operation.hide()

    def selected_names(self,family=None):
        entries=[item.data(0,QtCore.Qt.ItemDataRole.UserRole) for item in self.tree.selectedItems()]
        return Array[String]([e.Name for e in entries if e is not None and not e.Group and (e.Family==family if family else e.Family in ['Parts','Geometry parts'])])

    def edit_geometry(self,family,name=None):
        if self.active_editor is not None:
            self.active_editor.raise_();self.active_editor.activateWindow();return
        if self.operation_task is not None:return
        if family in list(GeometrySession.GeometryEditors)+['Mesh setup']:
            if self.controller.CurrentView!=ViewGeometryModelResults.Geometry:self.view.setCurrentText('Geometry')
        elif family in list(GeometrySession.MeshEditors):
            if self.controller.CurrentView!=ViewGeometryModelResults.Model:self.view.setCurrentText('Model')
        parts=self.selected_names()
        if family in list(GeometrySession.Transforms) and len(parts)==0:raise ValueError('Select at least one part first.')
        if family=='Element quality' and len(parts)==0:raise ValueError('Select at least one mesh part first.')
        dialog=GeometryDialog(self,family,name,parts)
        self.show_editor(dialog,family)

    def execute_geometry(self,operation,names=None):
        names=self.selected_names() if names is None else names
        if len(names)==0:raise ValueError('Select at least one part first.')
        def done():
            if operation=='Create mesh':self.view.setCurrentText('Model');self.change_view('Model')
            self.refresh()
        self.run_operation(self.geometry.Execute(operation,names),done)

    def run_operation(self,task,done=None,editor=None,cancel=None):
        if self.operation_task is not None:raise RuntimeError('Another operation is in progress.')
        self.operation_task=task
        if hasattr(self,'animation_timer'):self.animation_timer.stop()
        if hasattr(self,'result_toolbar'):self.result_toolbar.setEnabled(False);self.animation_toolbar.setEnabled(False);self.symbols.setEnabled(False)
        self.cancel_operation.clicked.disconnect()
        self.cancel_operation.clicked.connect(lambda:self.guard(cancel or self.geometry.Cancel))
        for action in self.actions.values():action.setEnabled(False)
        for menu in self.geometry_menus:menu.setEnabled(False)
        self.tree.setEnabled(False);self.view.setEnabled(False);self.viewport.setEnabled(False);self.pick_mode.setEnabled(False)
        self.element_edges.setEnabled(False)
        if editor is not None:editor.setEnabled(False)
        self.cancel_operation.show();self.statusBar().showMessage('Working…')
        self.operation_timer=QtCore.QTimer(self)
        def poll():
            if not task.IsCompleted:return
            self.operation_timer.stop();self.operation_timer.deleteLater()
            self.operation_task=None;self.cancel_operation.hide()
            if hasattr(self,'result_toolbar'):self.result_toolbar.setEnabled(self.active_editor is None);self.animation_toolbar.setEnabled(self.active_editor is None);self.symbols.setEnabled(self.active_editor is None)
            for menu in self.geometry_menus:menu.setEnabled(self.active_editor is None)
            self.viewport.setEnabled(True);self.pick_mode.setEnabled(True)
            self.element_edges.setEnabled(True)
            if editor is not None:editor.setEnabled(True)
            if self.active_editor is None:
                for action in self.actions.values():action.setEnabled(True)
                self.tree.setEnabled(True);self.view.setEnabled(True)
            else:self.actions['Fit'].setEnabled(True)
            try:
                self.refresh()
                if getattr(self,'pending_fit',False):self.pending_fit=False;self.fit()
                if task.IsCanceled:raise RuntimeError('Operation cancelled.')
                if task.IsFaulted:raise RuntimeError(str(task.Exception.GetBaseException().Message))
                if done:done()
                self.statusBar().showMessage('Operation completed')
            except Exception as error:
                if editor is not None:editor.error.setText(message(error))
                else:
                    self.output.appendPlainText(message(error));self.output.parentWidget().show()
                    self.statusBar().showMessage(message(error))
                self.operation_error=message(error)
        self.operation_error=None
        self.operation_timer.timeout.connect(poll);self.operation_timer.start(20)

    def show_preview(self):
        self.scene.show_selection(self.controller.Host.SelectionActors);self.render()

    def geometry_tree_menu(self,entry,position):
        menu=QtWidgets.QMenu(self);actions={}
        def add(title,callback):actions[menu.addAction(title)]=callback
        family=entry.Family
        if family=='Mesh setup':
            add('Create…',lambda:self.edit_geometry(family))
            if not entry.Group:
                names=self.selected_names(family)
                add('Edit…',lambda:self.edit_geometry(family,entry.Name))
                for operation in ['Duplicate mesh setup','Remove mesh setup']:
                    add(operation,lambda value=operation:self.execute_geometry(value,names))
                for active in [True,False]:add('Activate' if active else 'Deactivate',lambda value=active:self.geometry.SetActive(names,value))
        elif not entry.Group:
            add('Properties…',lambda:self.edit_geometry(family,entry.Name))
            for transform in GeometrySession.Transforms:add(transform+'…',lambda value=transform:self.edit_geometry(value))
            for operation in (['Create mesh','Preview edge mesh','Create compound','Regenerate compound'] if family=='Geometry parts' else ['Merge mesh parts']):
                add(operation,lambda value=operation:self.execute_geometry(value))
            add('Find edges by angle…',self.find_edges);add('Export…',self.export_parts)
            for operation in ['Hide','Show','Remove']:add(operation,lambda value=operation:self.execute_geometry(value))
        chosen=menu.exec(self.tree.viewport().mapToGlobal(position))
        if chosen in actions:
            self.guard(actions[chosen])
            if self.operation_task is None:self.refresh()

    def find_edges(self):
        angle,ok=QtWidgets.QInputDialog.getDouble(self,'Find edges','Angle [degrees]',30,0,180,3)
        if ok:self.run_operation(self.geometry.FindEdges(self.selected_names(),angle))

    def renumber(self,nodes):
        start,ok=QtWidgets.QInputDialog.getInt(self,'Renumber','Start ID',1,1,2147483647)
        if ok:self.run_operation(self.geometry.Renumber(nodes,start))

    def update_coordinates(self):
        path,_=QtWidgets.QFileDialog.getOpenFileName(self,'Nodal coordinates')
        if path:self.run_operation(self.geometry.UpdateCoordinates(path))

    def export_parts(self):
        names=self.selected_names()
        if not len(names):raise ValueError('Select at least one part first.')
        formats=list(self.geometry.ExportFormats)
        format,ok=QtWidgets.QInputDialog.getItem(self,'Export parts','Format',formats,editable=False)
        if not ok:return
        path,_=QtWidgets.QFileDialog.getSaveFileName(self,'Export parts')
        if path:self.run_operation(self.geometry.Export(names,path,format))

    def compound_operation(self,operation):
        compounds=list(self.geometry.CompoundNames)
        if not compounds:raise ValueError('There is no compound geometry part.')
        compound,ok=QtWidgets.QInputDialog.getItem(self,operation,'Compound',compounds,editable=False)
        if not ok:return
        if operation=='Rename split subpart':
            subparts=list(self.geometry.SubParts(compound))
            if not subparts:raise ValueError('The compound has no grouped split subparts.')
            name,ok=QtWidgets.QInputDialog.getItem(self,operation,'Subpart',subparts,editable=False)
            if not ok:return
            target,ok=QtWidgets.QInputDialog.getText(self,operation,'New name',text=name)
            if ok:self.run_operation(self.geometry.RenameSubPart(compound,name,target))
            return
        dialog=QtWidgets.QDialog(self);dialog.setWindowTitle(operation)
        layout=QtWidgets.QVBoxLayout(dialog);layout.addWidget(QtWidgets.QLabel('Select cells/bodies'))
        items=QtWidgets.QListWidget();items.addItems(list(self.geometry.Bodies(compound)))
        items.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection);layout.addWidget(items)
        target=QtWidgets.QLineEdit()
        if operation=='Group split cells':layout.addWidget(QtWidgets.QLabel('Subpart name (blank creates a name)'));layout.addWidget(target)
        buttons=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok|QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons)
        if dialog.exec()!=QtWidgets.QDialog.DialogCode.Accepted:return
        names=Array[String]([i.text() for i in items.selectedItems()])
        task=self.geometry.GroupCells(compound,names,target.text() or None) if operation=='Group split cells' else self.geometry.FuseBodies(compound,names)
        self.run_operation(task)

    def analyze_geometry(self):
        names=self.selected_names()
        if not len(names):raise ValueError('Select at least one part first.')
        data=self.geometry.Analyze(names)
        def ready():
            dialog=QtWidgets.QDialog(self);dialog.setWindowTitle('Analyze geometry');dialog.resize(580,350)
            layout=QtWidgets.QFormLayout(dialog);entries=[]
            for label,flag,prop,minimum,unit in [('Edges shorter than','ShowEdges','EdgeLimit',data.ShortestEdge,data.LengthUnit),('Unconnected edges closer than','ShowCloseEdges','DistanceLimit',data.ClosestEdges,data.LengthUnit),('Faces smaller than','ShowFaces','FaceLimit',data.SmallestFace,data.AreaUnit),('Vertices with angle greater than','ShowVertices','Angle',None,'degrees')]:
                box=QtWidgets.QCheckBox(label);box.setChecked(getattr(data,flag))
                edit=QtWidgets.QDoubleSpinBox();edit.setDecimals(9);edit.setRange(0,180 if prop=='Angle' else 1e100);edit.setValue(getattr(data,prop));edit.setSuffix(' '+unit)
                layout.addRow(box,edit)
                if minimum is not None:layout.addRow(QtWidgets.QLabel('Model min: '+str(minimum)+' '+unit))
                entries.append((flag,prop,box,edit))
            error=QtWidgets.QLabel();error.setWordWrap(True);layout.addRow(error);dialog.error=error
            show=QtWidgets.QPushButton('Show');close=QtWidgets.QPushButton('Close')
            def display():
                for flag,prop,box,edit in entries:setattr(data,flag,box.isChecked());setattr(data,prop,edit.value())
                self.run_operation(data.Show(),self.show_preview,dialog)
            show.clicked.connect(lambda:self.guard(display));close.clicked.connect(dialog.accept)
            layout.addRow(show,close);self.show_editor(dialog,'Geometry analysis')
        self.run_operation(data.Measure(),ready)

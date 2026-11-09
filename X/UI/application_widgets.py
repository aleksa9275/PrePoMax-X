"""Application dialogs over original C# settings, library, keyword and history objects."""
from pathlib import Path
from PyQt6 import QtCore,QtGui,QtWidgets
from authoring_widgets import PropertyPanel,message
from PrePoMaxX.UI import KeywordEditSession,PropertySheet

class SheetDialog(QtWidgets.QDialog):
    def __init__(self,owner,title,sheet,apply=None):
        super().__init__(owner);self.setWindowTitle(title);self.resize(650,600);self.sheet=sheet;self.apply_callback=apply
        self.layout=QtWidgets.QVBoxLayout(self);self.scroll=QtWidgets.QScrollArea();self.scroll.setWidgetResizable(True);self.layout.addWidget(self.scroll)
        self.error=QtWidgets.QLabel();self.error.setWordWrap(True);self.layout.addWidget(self.error);self.rebuild()
        self.buttons=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok|QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.apply);self.buttons.rejected.connect(self.reject);self.layout.addWidget(self.buttons)
    def rebuild(self):
        old=self.scroll.takeWidget()
        if old:old.deleteLater()
        self.panel=PropertyPanel(self.sheet,self.error.setText,self,changed=self.rebuild);self.scroll.setWidget(self.panel)
    def apply(self):
        try:
            self.panel.flush()
            if self.apply_callback:self.apply_callback()
            self.accept()
        except Exception as error:self.error.setText(message(error))

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self,owner):
        super().__init__(owner);self.owner=owner;self.rule=owner.application.Settings();self.setWindowTitle('Settings');self.resize(850,690)
        layout=QtWidgets.QVBoxLayout(self);split=QtWidgets.QSplitter();self.pages=QtWidgets.QListWidget();self.pages.addItems(list(self.rule.Pages));split.addWidget(self.pages)
        self.scroll=QtWidgets.QScrollArea();self.scroll.setWidgetResizable(True);split.addWidget(self.scroll);split.setSizes([180,670]);layout.addWidget(split)
        self.error=QtWidgets.QLabel();self.error.setWordWrap(True);layout.addWidget(self.error);self.panel=None
        buttons=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok|QtWidgets.QDialogButtonBox.StandardButton.Apply|QtWidgets.QDialogButtonBox.StandardButton.Cancel|QtWidgets.QDialogButtonBox.StandardButton.Reset)
        buttons.accepted.connect(lambda:self.apply(True));buttons.rejected.connect(self.reject);buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply)
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Reset).clicked.connect(self.reset);layout.addWidget(buttons)
        self.pages.currentTextChanged.connect(self.change_page);self.pages.setCurrentRow(0)
    def change_page(self,name):
        try:
            if self.panel:self.panel.flush()
            self.current_page=name;self.rebuild()
        except Exception as error:self.error.setText(message(error))
    def rebuild(self):
        old=self.scroll.takeWidget()
        if old:old.deleteLater()
        self.panel=PropertyPanel(self.rule.Page(self.current_page),self.error.setText,self,changed=self.rebuild);self.scroll.setWidget(self.panel)
    def reset(self):self.rule.Reset(self.current_page);self.rebuild()
    def apply(self,close=False):
        try:
            self.panel.flush();self.rule.Apply();self.owner.apply_preferences();self.owner.persist_preferences();self.owner.refresh()
            if close:self.accept()
        except Exception as error:self.error.setText(message(error))

class HistoryDialog(QtWidgets.QDialog):
    def __init__(self,owner):
        super().__init__(owner);self.owner=owner;self.rule=owner.application.History();self.setWindowTitle('Edit commands');self.resize(1000,670)
        layout=QtWidgets.QVBoxLayout(self);self.table=QtWidgets.QTableWidget();self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows);self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection);layout.addWidget(self.table)
        self.table.cellDoubleClicked.connect(lambda row,column:SheetDialog(self,'Command properties',self.rule.Properties(row)).exec())
        self.script=QtWidgets.QPlainTextEdit();self.script.setReadOnly(True);layout.addWidget(self.script);self.error=QtWidgets.QLabel();layout.addWidget(self.error)
        row=QtWidgets.QHBoxLayout()
        for label,cb in [('Open PMH…',self.open),('Save PMH…',self.save),('Export Python…',self.export),('Reset',self.reset),('Reorganize',self.rule.Reorganize),('Remove',self.remove),('Move up',lambda:self.move(-1)),('Move down',lambda:self.move(1)),('Clear all',self.rule.Clear)]:
            button=QtWidgets.QPushButton(label);button.clicked.connect(lambda checked=False,f=cb:self.guard(f));row.addWidget(button)
        layout.addLayout(row);buttons=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok|QtWidgets.QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(self.apply);buttons.rejected.connect(self.reject);layout.addWidget(buttons);self.refresh()
    def guard(self,callback):
        try:callback();self.refresh()
        except Exception as error:self.error.setText(message(error))
    def refresh(self):
        fields=['Id','DateTime','Name','Type','Data','ExecutionTimeString'];rows=self.rule.Rows;self.table.setColumnCount(len(fields));self.table.setRowCount(len(rows));self.table.setHorizontalHeaderLabels(fields)
        for i,row in enumerate(rows):
            for col,key in enumerate(fields):
                item=QtWidgets.QTableWidgetItem(str(getattr(row,key)));item.setFlags(item.flags()&~QtCore.Qt.ItemFlag.ItemIsEditable);self.table.setItem(i,col,item)
        self.table.horizontalHeader().setSectionResizeMode(4,QtWidgets.QHeaderView.ResizeMode.Stretch);self.script.setPlainText(self.rule.PythonText)
    def reset(self):self.rule.Reset()
    def remove(self):
        if self.table.currentRow()>=0:self.rule.Remove(self.table.currentRow())
    def move(self,delta):
        if self.table.currentRow()>=0:self.rule.Move(self.table.currentRow(),delta)
    def open(self):
        path,_=QtWidgets.QFileDialog.getOpenFileName(self,'Open history','','History (*.pmh)')
        if path:self.rule.Open(path)
    def save(self):
        path,_=QtWidgets.QFileDialog.getSaveFileName(self,'Save history','','History (*.pmh)')
        if path:self.rule.Save(path)
    def export(self):
        path,_=QtWidgets.QFileDialog.getSaveFileName(self,'Export history as Python','','Python (*.py)')
        if path:self.rule.ExportPython(path)
    def apply(self):
        if QtWidgets.QMessageBox.warning(self,'Edit history','Changing history might break model regeneration. Apply changes?',QtWidgets.QMessageBox.StandardButton.Ok|QtWidgets.QMessageBox.StandardButton.Cancel)!=QtWidgets.QMessageBox.StandardButton.Ok:return
        try:self.rule.Apply();self.accept()
        except Exception as error:self.error.setText(message(error))

class KeywordDialog(QtWidgets.QDialog):
    def __init__(self,owner):
        super().__init__(owner);self.owner=owner;self.rule=KeywordEditSession(owner.controller);self.setWindowTitle('CalculiX keyword editor');self.resize(1100,730);self.node=None
        layout=QtWidgets.QVBoxLayout(self);split=QtWidgets.QSplitter();self.tree=QtWidgets.QTreeWidget();self.tree.setHeaderLabel('Keywords');split.addWidget(self.tree)
        editors=QtWidgets.QWidget();column=QtWidgets.QVBoxLayout(editors);self.text=QtWidgets.QPlainTextEdit();column.addWidget(self.text);self.preview=QtWidgets.QPlainTextEdit();self.preview.setReadOnly(True);column.addWidget(self.preview);split.addWidget(editors);split.setSizes([350,750]);layout.addWidget(split)
        self.error=QtWidgets.QLabel();self.error.setWordWrap(True);layout.addWidget(self.error);row=QtWidgets.QHBoxLayout();self.active=QtWidgets.QCheckBox('Active');self.hide=QtWidgets.QCheckBox('Hide large data');row.addWidget(self.active);row.addWidget(self.hide)
        self.hide.toggled.connect(lambda value:self.guard(lambda:self.rule.SetHideData(value)))
        for label,cb in [('Add',self.add),('Delete',self.remove),('Move up',lambda:self.move(True)),('Move down',lambda:self.move(False)),('Reset fragment',self.reset)]:
            button=QtWidgets.QPushButton(label);button.clicked.connect(lambda checked=False,f=cb:self.guard(f));row.addWidget(button)
        layout.addLayout(row);buttons=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok|QtWidgets.QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(self.apply);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
        self.tree.currentItemChanged.connect(self.change);self.rebuild()
    def flush(self):
        if self.node is not None and not self.node.Title and self.text.document().isModified():self.rule.Set(self.node,self.text.toPlainText(),self.active.isChecked());self.text.document().setModified(False)
        elif self.node is not None and not self.node.Title and self.active.isChecked()!=self.node.Active:
            # Original active checkbox prefixes/unprefixes every line.
            lines=self.text.toPlainText().split('\n');active=self.active.isChecked()
            data='\n'.join(line[2:] if len(line)>=2 else '' for line in lines) if active else '\n'.join('**'+line for line in lines)
            self.rule.Set(self.node,data,active)
    def rebuild(self):
        selected=self.node;self.tree.blockSignals(True);self.tree.clear();self.nodes=[]
        def add(parent,node):
            item=QtWidgets.QTreeWidgetItem(parent,[node.Text]);item.setData(0,QtCore.Qt.ItemDataRole.UserRole,len(self.nodes));self.nodes.append(node)
            if node.Modified:font=item.font(0);font.setBold(True);item.setFont(0,font)
            for child in node.Nodes:add(item,child)
            item.setExpanded(node.Expanded or node.Parent is None)
            if selected is not None and node==selected:self.tree.setCurrentItem(item)
        add(self.tree,self.rule.Root);self.tree.blockSignals(False);self.preview.setPlainText(self.rule.Preview)
        self.display()
    def display(self):
        self.text.setPlainText(self.node.Data if self.node is not None else '');self.text.document().setModified(False);self.text.setReadOnly(self.node is None or self.node.Title or '... hidden data ...' in self.text.toPlainText())
        self.active.setChecked(self.node.Active if self.node is not None else True)
    def change(self,item,previous):
        try:
            self.flush();self.node=self.nodes[item.data(0,QtCore.Qt.ItemDataRole.UserRole)] if item else None;self.display();self.preview.setPlainText(self.rule.Preview)
        except Exception as error:self.error.setText(message(error))
    def guard(self,callback):
        try:self.flush();callback();self.rebuild()
        except Exception as error:self.error.setText(message(error))
    def add(self):self.node=self.rule.Add(self.node or self.rule.Root)
    def remove(self):
        if self.node is not None:self.rule.Remove(self.node);self.node=None
    def move(self,up):
        if self.node is not None:self.rule.Move(self.node,up)
    def reset(self):
        if self.node is not None:self.rule.Reset(self.node)
    def apply(self):
        try:
            self.flush()
            if any(node.Modified for node in self.nodes) and QtWidgets.QMessageBox.warning(self,'Modified keywords','Output overrides may be reset by later model changes. Continue?',QtWidgets.QMessageBox.StandardButton.Yes|QtWidgets.QMessageBox.StandardButton.No)!=QtWidgets.QMessageBox.StandardButton.Yes:return
            self.rule.Apply();self.accept()
        except Exception as error:self.error.setText(message(error))

class LibraryDialog(QtWidgets.QDialog):
    def __init__(self,owner):
        super().__init__(owner);self.owner=owner;self.rule=owner.application.Library();self.setWindowTitle('Material library');self.resize(950,660);self.dirty_libraries=set();self.libraries={}
        layout=QtWidgets.QVBoxLayout(self);self.files=QtWidgets.QComboBox();layout.addWidget(self.files);self.files.currentTextChanged.connect(self.select_library)
        split=QtWidgets.QSplitter();self.tree=QtWidgets.QTreeWidget();self.tree.setHeaderLabel('Library');self.model=QtWidgets.QListWidget();split.addWidget(self.tree);split.addWidget(self.model);layout.addWidget(split)
        self.error=QtWidgets.QLabel();self.error.setWordWrap(True);layout.addWidget(self.error);row=QtWidgets.QGridLayout()
        for i,(label,cb) in enumerate([('New library…',lambda:self.file(True)),('Add library…',lambda:self.file(False)),('Remove library',self.unregister),('Save library',self.save),('Add category…',self.category),('Rename…',self.rename),('Delete library item',self.remove),('Copy to model →',self.to_model),('← Copy to library',self.to_library),('Remove model material',self.remove_model),('Move up',lambda:self.move(-1)),('Move down',lambda:self.move(1)),('Preview…',self.preview)]):
            button=QtWidgets.QPushButton(label);button.clicked.connect(lambda checked=False,f=cb:self.guard(f));row.addWidget(button,i//4,i%4)
        layout.addLayout(row);buttons=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok|QtWidgets.QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(self.apply);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
        self.tree.itemDoubleClicked.connect(lambda item,col:self.guard(self.to_model));self.model.itemDoubleClicked.connect(lambda item:self.guard(self.to_library));self.rebuild()
        for path in owner.controller.Settings.General.GetMaterialLibraryFiles():
            if Path(str(path)).is_file():self.rule.Open(str(path));self.libraries[str(path)]=self.rule.Root;self.files.addItem(str(path))
    def select_library(self,path):
        if path in self.libraries:self.rule.Use(path,self.libraries[path]);self.rebuild()
    @property
    def changed(self):return bool(self.dirty_libraries)
    @changed.setter
    def changed(self,value):
        path=self.rule.FileName
        if path:
            if value:self.dirty_libraries.add(str(path))
            else:self.dirty_libraries.discard(str(path))
    def current(self):
        item=self.tree.currentItem();return self.nodes[item.data(0,QtCore.Qt.ItemDataRole.UserRole)] if item else self.rule.Root
    def rebuild(self):
        self.nodes=[];self.tree.clear()
        def add(parent,node):
            item=QtWidgets.QTreeWidgetItem(parent,[node.Name]);item.setData(0,QtCore.Qt.ItemDataRole.UserRole,len(self.nodes));self.nodes.append(node)
            for child in node.Items:add(item,child)
            item.setExpanded(node.Expanded or node==self.rule.Root)
        add(self.tree,self.rule.Root);self.model.clear();self.model.addItems([m.Name for m in self.rule.ModelMaterials])
    def guard(self,callback):
        try:callback();self.rebuild()
        except Exception as error:self.error.setText(message(error))
    def file(self,new):
        dialog=QtWidgets.QFileDialog.getSaveFileName if new else QtWidgets.QFileDialog.getOpenFileName
        path,_=dialog(self,'Material library','','Material library (*.lib)')
        if path:
            if new:self.rule.New(path)
            else:self.rule.Open(path)
            self.libraries[path]=self.rule.Root
            if self.files.findText(path)<0:self.files.addItem(path)
            self.files.setCurrentText(path)
    def save(self):self.rule.Save();self.changed=False
    def unregister(self):
        path=self.rule.FileName
        self.dirty_libraries.discard(str(path))
        self.rule.Unregister();self.libraries.pop(str(path),None);self.files.removeItem(self.files.currentIndex())
    def category(self):
        name,ok=QtWidgets.QInputDialog.getText(self,'New category','Name',text='NewCategory')
        if ok:self.rule.Category(self.current(),name);self.changed=True
    def parent_node(self,node):return next((n for n in self.nodes if any(c==node for c in n.Items)),None)
    def rename(self):
        node=self.current();parent=self.parent_node(node)
        if parent is None:return
        name,ok=QtWidgets.QInputDialog.getText(self,'Rename','Name',text=node.Name)
        if ok:self.rule.Rename(parent,node,name);self.changed=True
    def remove(self):
        node=self.current();parent=self.parent_node(node)
        if parent is not None:self.rule.Remove(parent,node);self.changed=True
    def to_model(self):self.rule.ToModel(self.current())
    def to_library(self):
        node=self.current();node=self.parent_node(node) if node.Tag is not None else node
        if self.model.currentItem():self.rule.ToLibrary(node,self.model.currentItem().text());self.changed=True
    def remove_model(self):
        if self.model.currentItem():self.rule.RemoveModel(self.model.currentItem().text())
    def move(self,delta):
        if self.model.hasFocus():self.rule.MoveModel(self.model.currentRow(),delta)
        else:
            node=self.current();parent=self.parent_node(node)
            if parent is not None:self.rule.Move(parent,node,delta);self.changed=True
    def preview(self):
        node=self.current()
        if node.Tag is not None:
            from authoring_widgets import MultiPropertyDialog
            from PrePoMaxX.UI import MaterialEditSession
            dialog=MultiPropertyDialog(self.owner,node.Tag.Name,draft=MaterialEditSession.Preview(self.owner.controller,node.Tag));dialog.setWindowTitle('Preview material properties')
            for edit in dialog.findChildren(QtWidgets.QLineEdit):edit.setReadOnly(True)
            for button in dialog.findChildren(QtWidgets.QPushButton):button.setEnabled(False)
            for check in dialog.findChildren(QtWidgets.QCheckBox):check.setEnabled(False)
            for combo in dialog.findChildren(QtWidgets.QComboBox):combo.setEnabled(False)
            buttons=dialog.findChild(QtWidgets.QDialogButtonBox);buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).hide();close=buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel);close.setText('Close');close.setEnabled(True);dialog.exec()
    def apply(self):
        try:self.rule.Apply();self.done(QtWidgets.QDialog.DialogCode.Accepted)
        except Exception as error:self.error.setText(message(error))
    def done(self,result):
        if self.changed:
            answer=QtWidgets.QMessageBox.question(self,'Material library','Save changed libraries?',QtWidgets.QMessageBox.StandardButton.Save|QtWidgets.QMessageBox.StandardButton.Discard|QtWidgets.QMessageBox.StandardButton.Cancel)
            if answer==QtWidgets.QMessageBox.StandardButton.Cancel:return
            if answer==QtWidgets.QMessageBox.StandardButton.Save:
                try:
                    for path in list(self.dirty_libraries):self.rule.Use(path,self.libraries[path]);self.rule.Save();self.dirty_libraries.discard(path)
                except Exception as error:self.error.setText(message(error));return
        super().done(result)

class UserViewsDialog(QtWidgets.QDialog):
    def __init__(self,owner):
        super().__init__(owner);self.owner=owner;self.rule=owner.application.UserViews();self.setWindowTitle('User views');self.resize(760,620)
        layout=QtWidgets.QVBoxLayout(self);split=QtWidgets.QSplitter();self.views=QtWidgets.QListWidget();split.addWidget(self.views);self.scroll=QtWidgets.QScrollArea();self.scroll.setWidgetResizable(True);split.addWidget(self.scroll);layout.addWidget(split);self.panel=None;self.error=QtWidgets.QLabel();layout.addWidget(self.error)
        row=QtWidgets.QHBoxLayout()
        for label,cb in [('Create',self.add),('Update',lambda:self.rule.Update(self.views.currentRow())),('Show',lambda:self.rule.Show(self.views.currentRow())),('Remove',lambda:self.rule.Remove(self.views.currentRow())),('Move up',lambda:self.rule.Move(self.views.currentRow(),-1)),('Move down',lambda:self.rule.Move(self.views.currentRow(),1))]:
            button=QtWidgets.QPushButton(label);button.clicked.connect(lambda checked=False,f=cb:self.guard(f));row.addWidget(button)
        layout.addLayout(row);buttons=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok|QtWidgets.QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(self.apply);buttons.rejected.connect(self.reject);layout.addWidget(buttons);self.views.currentRowChanged.connect(self.select);self.rebuild()
    def guard(self,callback):
        try:
            if self.panel:self.panel.flush()
            callback();self.rebuild()
        except Exception as error:self.error.setText(message(error))
    def rebuild(self):
        self.views.blockSignals(True);row=self.views.currentRow();self.views.clear();self.views.addItems(list(self.rule.Names));self.views.setCurrentRow(max(0,min(row,len(self.rule.Names)-1)));self.views.blockSignals(False);self.select(self.views.currentRow())
    def select(self,index):
        old=self.scroll.takeWidget()
        if old:old.deleteLater()
        self.panel=None
        if index>=0:self.panel=PropertyPanel(self.rule.Properties(index),self.error.setText,self);self.scroll.setWidget(self.panel)
    def add(self):self.rule.Add()
    def apply(self):
        try:
            if self.panel:self.panel.flush()
            self.rule.Apply();self.accept()
        except Exception as error:self.error.setText(message(error))

class ContactSearchDialog(QtWidgets.QDialog):
    def __init__(self,owner):
        from PrePoMaxX.UI import ContactSearchSession
        super().__init__(owner);self.owner=owner;self.rule=ContactSearchSession(owner.controller);self.setWindowTitle('Search contact pairs');self.resize(850,650)
        layout=QtWidgets.QVBoxLayout(self);form=QtWidgets.QFormLayout();self.distance=QtWidgets.QLineEdit('0.01');self.angle=QtWidgets.QLineEdit('10');self.group=QtWidgets.QComboBox();self.group.addItems(['None','ByParts','ByContactGraph']);self.group.setCurrentIndex(1);self.type=QtWidgets.QComboBox();self.type.addItems(['Tie','Contact']);self.interaction=QtWidgets.QComboBox();self.interaction.addItems(list(self.rule.Interactions));self.method=QtWidgets.QComboBox();self.method.addItems(['Node to surface','Surface to surface']);self.method.setCurrentIndex(1);self.adjust=QtWidgets.QCheckBox('Adjust mesh');self.ignore=QtWidgets.QCheckBox('Ignore hidden parts');self.ignore.setChecked(True)
        for label,widget in [('Distance',self.distance),('Angle [degrees]',self.angle),('Group by',self.group),('Type',self.type),('Surface interaction',self.interaction),('Method',self.method)]:form.addRow(label,widget)
        form.addRow(self.adjust);form.addRow(self.ignore);self.filters={}
        for name in ['Solid','Shell','ShellEdge']:
            box=QtWidgets.QCheckBox(name);box.setChecked(True);form.addRow(box);self.filters[name]=box
        layout.addLayout(form);split=QtWidgets.QSplitter();self.list=QtWidgets.QListWidget();self.list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection);split.addWidget(self.list);self.scroll=QtWidgets.QScrollArea();self.scroll.setWidgetResizable(True);split.addWidget(self.scroll);layout.addWidget(split);self.panel=None;self.error=QtWidgets.QLabel();self.error.setWordWrap(True);layout.addWidget(self.error)
        row=QtWidgets.QHBoxLayout()
        for label,cb in [('Search',self.search),('Swap master/slave',self.swap),('Merge by master/slave',self.merge),('Remove',self.remove)]:
            button=QtWidgets.QPushButton(label);button.clicked.connect(lambda checked=False,f=cb:owner.guard(f));row.addWidget(button)
        layout.addLayout(row);buttons=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok|QtWidgets.QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(self.apply);buttons.rejected.connect(self.reject);layout.addWidget(buttons);self.list.currentRowChanged.connect(self.selected)
    def merge(self):
        from System import Array,Int32
        indices=sorted({i.row() for i in self.list.selectedIndexes()})
        if indices:self.rule.Merge(Array[Int32](indices));self.rebuild()
    def rebuild(self):self.list.clear();self.list.addItems([p.Name for p in self.rule.Pairs]);self.list.setCurrentRow(0)
    def selected(self,index):
        if self.panel:self.panel.flush()
        old=self.scroll.takeWidget()
        if old:old.deleteLater()
        self.panel=None
        if index>=0:self.panel=PropertyPanel(self.rule.Properties(index),self.error.setText,self);self.scroll.setWidget(self.panel);self.rule.Highlight(index);self.owner.show_preview()
    def search(self):
        from CaeMesh.ContactSearchNamespace import GeometryFilterEnum
        from CaeGlobals import StringLengthConverter,StringAngleDegConverter
        from System import Convert
        filter=getattr(GeometryFilterEnum,'None')
        for name,box in self.filters.items():
            if box.isChecked():filter|=getattr(GeometryFilterEnum,name)
        if self.ignore.isChecked():filter|=GeometryFilterEnum.IgnoreHidden
        distance=Convert.ToDouble(StringLengthConverter().ConvertFromString(self.distance.text()));angle=Convert.ToDouble(StringAngleDegConverter().ConvertFromString(self.angle.text()))
        self.owner.run_operation(self.rule.Search(distance,angle,self.group.currentText(),self.type.currentText(),self.interaction.currentText(),self.method.currentText(),self.adjust.isChecked(),filter),self.rebuild,self)
    def swap(self):
        if self.list.currentRow()>=0:self.rule.Swap(self.list.currentRow());self.rebuild()
    def remove(self):
        if self.list.currentRow()>=0:self.rule.Remove(self.list.currentRow());self.rebuild()
    def apply(self):
        try:
            if self.panel:self.panel.flush()
            self.rule.Apply();self.accept()
        except Exception as error:self.error.setText(message(error))

"""Toolkit widgets bound directly to original .NET view descriptors and form rules."""
from PyQt6 import QtCore, QtGui, QtWidgets
from System import Array, Int32, Double
from PrePoMaxX.UI import AuthoringSession, MaterialEditSession


def message(error):
    return str(error).split('   at ')[0].strip()


def value_text(widget):
    return widget.currentText() if isinstance(widget, QtWidgets.QComboBox) else widget.text()


class TableWidget(QtWidgets.QWidget):
    def __init__(self, sheet, error, parent=None, changed=None):
        super().__init__(parent)
        self.sheet, self.error, self.changed = sheet, error, changed
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        self.table = QtWidgets.QTableWidget()
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
        buttons = QtWidgets.QHBoxLayout()
        for label, callback in [('Add row', self.add),('Remove row', self.remove),('Move up',lambda:self.move(-1)),('Move down',lambda:self.move(1)),('Copy', self.copy),('Paste', self.paste)]:
            button = QtWidgets.QPushButton(label)
            button.clicked.connect(lambda checked=False, cb=callback:self.guard(cb))
            buttons.addWidget(button)
        layout.addLayout(buttons)
        self.rebuild()

    def guard(self, callback):
        try:
            callback()
        except Exception as error:
            self.error(message(error))

    def rebuild(self):
        fields = self.sheet.Columns
        self.table.setColumnCount(len(fields))
        self.table.setRowCount(self.sheet.Count)
        self.table.setHorizontalHeaderLabels([f.Label.replace('[?]','') for f in fields])
        self.entries = []
        for row in range(self.sheet.Count):
            sheet = self.sheet.Row(row)
            for col, field in enumerate(sheet.Fields):
                if len(field.Choices):
                    edit = QtWidgets.QComboBox()
                    edit.addItems(list(field.Choices))
                    edit.setEditable(not field.Exclusive)
                    edit.setCurrentText(field.Text)
                    edit.setEnabled(not field.ReadOnly)
                else:
                    edit = QtWidgets.QLineEdit(field.Text)
                    edit.setReadOnly(field.ReadOnly)
                edit.setToolTip(field.Description)
                self.table.setCellWidget(row,col,edit)
                self.entries.append((sheet,field,edit))
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

    def flush(self):
        for sheet, field, edit in self.entries:
            if not field.ReadOnly:
                sheet.Set(field.Name,value_text(edit))
        if self.changed:
            self.changed()

    def add(self):
        self.flush()
        self.sheet.Add(self.table.currentRow())
        self.rebuild()

    def remove(self):
        self.flush()
        row=self.table.currentRow()
        if row>=0:
            self.sheet.Remove(row)
            self.rebuild()

    def move(self, offset):
        self.flush()
        row=self.table.currentRow()
        if row>=0:
            self.sheet.Move(row,offset)
            self.rebuild()
            self.table.selectRow(max(0,min(row+offset,self.sheet.Count-1)))

    def copy(self):
        self.flush()
        rows = sorted({index.row() for index in self.table.selectedIndexes()}) or list(range(self.sheet.Count))
        QtWidgets.QApplication.clipboard().setText('\n'.join('\t'.join(f.Text for f in self.sheet.Row(row).Fields) for row in rows))

    def paste(self):
        self.flush()
        start=max(0,self.table.currentRow())
        for offset,line in enumerate(QtWidgets.QApplication.clipboard().text().splitlines()):
            row=start+offset
            while row>=self.sheet.Count:
                self.sheet.Add()
            sheet=self.sheet.Row(row)
            fields=sheet.Fields
            values=line.split('\t')
            if len(values)!=len(fields):
                raise ValueError('The pasted row must contain '+str(len(fields))+' tab-separated cells.')
            for field,text in zip(fields,values):
                if not field.ReadOnly:
                    sheet.Set(field.Name,text)
        self.rebuild()


class PropertyPanel(QtWidgets.QWidget):
    def __init__(self, sheet, error, parent=None, changed=None, pick=None):
        super().__init__(parent)
        self.sheet, self.error, self.changed, self.pick = sheet, error, changed, pick
        self.form=QtWidgets.QFormLayout(self)
        self.entries={}
        self.initial={}
        for field in sheet.Fields:
            container = QtWidgets.QWidget()
            row=QtWidgets.QHBoxLayout(container)
            row.setContentsMargins(0,0,0,0)
            if len(field.Choices):
                edit=QtWidgets.QComboBox()
                edit.addItems(list(field.Choices))
                edit.setEditable(not field.Exclusive)
                if field.Text not in list(field.Choices):edit.addItem(field.Text)
                edit.setCurrentText(field.Text)
                edit.setEnabled(not field.ReadOnly)
                edit.activated.connect(lambda index, f=field, w=edit:self.commit_field(f,w))
            else:
                edit=QtWidgets.QLineEdit(field.Text)
                edit.setReadOnly(field.ReadOnly or not field.CanConvertFromString)
                edit.editingFinished.connect(lambda f=field,w=edit:self.commit_field(f,w))
            edit.setToolTip(field.Description)
            row.addWidget(edit)
            editor=field.Editor or ''
            if 'FilteredFileNameEditor' in editor:
                button=QtWidgets.QPushButton('Browse…')
                button.clicked.connect(lambda checked=False,w=edit,f=field:self.browse(f,w))
                row.addWidget(button)
            elif 'ColorEditorEx' in editor:
                button=QtWidgets.QPushButton('Color…')
                button.clicked.connect(lambda checked=False,w=edit,f=field:self.color(f,w))
                row.addWidget(button)
            elif field.IsFlags:
                button=QtWidgets.QPushButton('Select…')
                button.clicked.connect(lambda checked=False,w=edit,f=field:self.flags(f,w))
                row.addWidget(button)
            elif 'DampingRatiosAndValues' in editor:
                button=QtWidgets.QPushButton('Edit rows…')
                button.clicked.connect(lambda checked=False,f=field:self.edit_table(f))
                row.addWidget(button)
            elif 'SinglePointDataEditor' in editor and pick is not None:
                button=QtWidgets.QPushButton('Use picked point')
                button.clicked.connect(lambda checked=False,f=field:self.use_point(f))
                row.addWidget(button)
            self.form.addRow(field.Label.strip(),container)
            self.entries[field.Name]=(sheet,edit)
            self.initial[field.Name]=value_text(edit)

    def flush(self):
        for field in self.sheet.Fields:
            if field.Name in self.entries and not field.ReadOnly and field.CanConvertFromString:
                text=value_text(self.entries[field.Name][1])
                if text!=self.initial[field.Name]:
                    self.sheet.Set(field.Name,text)
                    self.initial[field.Name]=text

    def commit_field(self, field, widget):
        try:
            if field.ReadOnly or not field.CanConvertFromString:
                return
            text=value_text(widget)
            if text==self.initial[field.Name]:return
            self.sheet.Set(field.Name,text)
            self.initial[field.Name]=text
            # Layout changes are queued until the widget's signal has returned.
            if self.changed:
                QtCore.QTimer.singleShot(0,self.changed)
        except Exception as error:
            self.error(message(error))

    def browse(self, field, edit):
        path,_=QtWidgets.QFileDialog.getOpenFileName(self,'Select file',edit.text())
        if path:
            edit.setText(path)
            self.commit_field(field,edit)

    def color(self, field, edit):
        color=QtWidgets.QColorDialog.getColor(parent=self,options=QtWidgets.QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if color.isValid():
            edit.setText(f'{color.alpha()}, {color.red()}, {color.green()}, {color.blue()}')
            self.commit_field(field,edit)

    def flags(self, field, edit):
        dialog=QtWidgets.QDialog(self)
        dialog.setWindowTitle(field.Label)
        layout=QtWidgets.QVBoxLayout(dialog)
        values=[]
        for choice in field.Choices:
            box=QtWidgets.QCheckBox(choice)
            box.setChecked(choice in [v.strip() for v in value_text(edit).split(',')])
            layout.addWidget(box)
            values.append(box)
        buttons=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok|QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec()==QtWidgets.QDialog.DialogCode.Accepted:
            text=', '.join(box.text() for box in values if box.isChecked()) or '0'
            if isinstance(edit,QtWidgets.QComboBox):edit.setCurrentText(text)
            else:edit.setText(text)
            self.commit_field(field,edit)

    def edit_table(self, field):
        sheet=self.sheet.Collection(field.Name)
        if sheet is None:return
        dialog=QtWidgets.QDialog(self)
        dialog.setWindowTitle(field.Label)
        dialog.resize(700,420)
        layout=QtWidgets.QVBoxLayout(dialog)
        table=TableWidget(sheet,self.error,dialog)
        layout.addWidget(table)
        button=QtWidgets.QPushButton('Done')
        def done():
            try:table.flush();dialog.accept()
            except Exception as error:self.error(message(error))
        button.clicked.connect(done);layout.addWidget(button)
        dialog.exec()

    def use_point(self, field):
        try:
            self.pick(field.Name)
            if self.changed:self.changed()
        except Exception as error:self.error(message(error))


class PropertyDialog(QtWidgets.QDialog):
    """A modal draft; original form rules own construction/acceptance."""
    def __init__(self, parent, family, step=None, name=None):
        super().__init__(parent)
        self.family,self.parent_window=family,parent
        self.rule=parent.authoring.Edit(family,step,name)
        self.setWindowTitle(('Edit ' if name else 'Create ')+family.lower())
        self.resize(750,680)
        layout=QtWidgets.QVBoxLayout(self)
        self.types=QtWidgets.QComboBox()
        self.types.addItems([choice.Text for choice in self.rule.Choices])
        self.types.setVisible(bool(self.types.count()) and name is None)
        self.types.currentIndexChanged.connect(self.select_type)
        layout.addWidget(self.types)
        self.scroll=QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        layout.addWidget(self.scroll)
        self.error=QtWidgets.QLabel()
        self.error.setWordWrap(True);self.error.setStyleSheet('color: #b83b35')
        layout.addWidget(self.error)
        buttons=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok|QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.apply);buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.rebuild()

    def select_type(self,index):
        try:self.rule.Select(index);self.rebuild()
        except Exception as error:self.error.setText(message(error))

    def rebuild(self):
        body=QtWidgets.QWidget()
        layout=QtWidgets.QVBoxLayout(body)
        self.panel=PropertyPanel(self.rule.Properties,self.error.setText,body,changed=self.rebuild,pick=self.pick_point)
        layout.addWidget(self.panel)
        self.entries=self.panel.entries
        self.tables=[]
        for name in self.rule.CollectionNames:
            # Damping has its original modal editor above; DataPoints is a table.
            if name!='DataPoints':continue
            table=TableWidget(self.rule.Collection(name),self.error.setText,body)
            self.tables.append(table);layout.addWidget(table)
        for prefix in self.rule.SelectionPrefixes:
            row=QtWidgets.QHBoxLayout()
            label=prefix or ('Items' if self.family in ['Node sets','Element sets','Surfaces'] else 'Region')
            row.addWidget(QtWidgets.QLabel(label))
            button=QtWidgets.QPushButton('Use picked selection')
            button.clicked.connect(lambda checked=False,p=prefix:self.use_selection(p))
            row.addWidget(button)
            if self.family in ['Node sets','Element sets','Surfaces']:
                edit=QtWidgets.QPushButton('Enter IDs…')
                edit.clicked.connect(lambda checked=False,p=prefix:self.enter_ids(p))
                row.addWidget(edit)
            layout.addLayout(row)
        layout.addStretch()
        old=self.scroll.takeWidget();self.scroll.setWidget(body)
        if old:old.deleteLater()

    def flush(self):
        self.panel.flush()
        for table in self.tables:table.flush()

    def use_selection(self,prefix):
        try:
            self.flush()
            self.rule.SetSelection(Array[Int32](self.parent_window.selected),self.parent_window.controller.Selection,prefix)
            self.rebuild()
        except Exception as error:self.error.setText(message(error))

    def enter_ids(self,prefix):
        text,ok=QtWidgets.QInputDialog.getMultiLineText(self,'Item IDs','Enter comma/space-separated IDs')
        if ok:
            try:
                self.rule.SetSelection(Array[Int32]([int(v) for v in text.replace(',',' ').split()]),None,prefix)
                self.rebuild()
            except Exception as error:self.error.setText(message(error))

    def pick_point(self,property_name):
        self.rule.SetPoint(property_name,Array[Int32](self.parent_window.selected))

    def apply(self):
        try:self.flush();self.rule.Commit();self.accept()
        except Exception as error:self.error.setText(message(error))


class MultiPropertyDialog(QtWidgets.QDialog):
    def __init__(self,parent,name=None,kind='Materials',step=None):
        super().__init__(parent)
        self.kind=kind
        self.draft=parent.authoring.Material(name) if kind=='Materials' else parent.authoring.Interaction(name) if kind=='Surface interactions' else parent.authoring.Controls(step)
        self.setWindowTitle(('Edit ' if name else 'Create ')+kind.lower())
        self.resize(840,650)
        layout=QtWidgets.QVBoxLayout(self)
        form=QtWidgets.QFormLayout()
        self.name=QtWidgets.QLineEdit(self.draft.Name)
        form.addRow('Name',self.name)
        self.description=QtWidgets.QLineEdit(getattr(self.draft,'Description','') or '')
        if kind=='Materials':
            form.addRow('Description',self.description)
            self.temperature=QtWidgets.QCheckBox('Temperature dependent')
            self.temperature.setChecked(self.draft.TemperatureDependent)
            self.temperature.toggled.connect(self.set_temperature)
            form.addRow(self.temperature)
        if kind=='Solution controls':self.name.setEnabled(False)
        layout.addLayout(form)
        row=QtWidgets.QHBoxLayout()
        self.available=QtWidgets.QComboBox()
        self.available.addItems(list(type(self.draft).AvailableProperties))
        row.addWidget(self.available)
        for title,cb in [('Add property',self.add_property),('Remove',self.remove_property),('Move left',lambda:self.move_property(-1)),('Move right',lambda:self.move_property(1))]:
            button=QtWidgets.QPushButton(title);button.clicked.connect(lambda checked=False,f=cb:self.guard(f));row.addWidget(button)
        layout.addLayout(row)
        self.pages=QtWidgets.QTabWidget();layout.addWidget(self.pages)
        self.error=QtWidgets.QLabel();self.error.setWordWrap(True)
        self.error.setMinimumHeight(self.error.fontMetrics().height()*3);self.error.setStyleSheet('color: #b83b35')
        layout.addWidget(self.error)
        buttons=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok|QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.apply);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
        self.rebuild()

    def guard(self,cb):
        try:cb()
        except Exception as error:self.error.setText(message(error))

    def rebuild(self):
        current=self.pages.currentIndex()
        while self.pages.count():
            page=self.pages.widget(0);self.pages.removeTab(0);page.deleteLater()
        self.entries={};self.panels=[];self.tables=[]
        for index,title in enumerate(self.draft.PropertyNames):
            page=QtWidgets.QWidget();box=QtWidgets.QVBoxLayout(page)
            if self.draft.ShowProperties(index):
                panel=PropertyPanel(self.draft.Properties(index),self.error.setText,page,changed=self.rebuild)
                self.panels.append(panel);box.addWidget(panel)
                for key,value in panel.entries.items():self.entries[(index,key)]=value
            if self.draft.ShowTable(index):
                sheet=self.draft.Table(index)
                if sheet is not None:
                    table=TableWidget(sheet,self.error.setText,page)
                    self.tables.append(table);box.addWidget(table)
                    for row in range(sheet.Count):
                        for field in sheet.Row(row).Fields:
                            # Keep the established C1 probe access for scalar fields.
                            pass
            box.addStretch();self.pages.addTab(page,title)
        if self.pages.count():self.pages.setCurrentIndex(max(0,min(current,self.pages.count()-1)))

    def flush(self):
        for panel in self.panels:panel.flush()
        for table in self.tables:table.flush()

    def set_temperature(self,value):
        def change():self.flush();setattr(self.draft,'TemperatureDependent',value);self.rebuild()
        self.guard(change)

    def add_property(self):
        self.flush();self.draft.AddProperty(self.available.currentIndex());self.rebuild();self.pages.setCurrentIndex(self.pages.count()-1)

    def remove_property(self):
        index=self.pages.currentIndex()
        if index>=0:self.flush();self.draft.RemoveProperty(index);self.rebuild()

    def move_property(self,offset):
        index=self.pages.currentIndex()
        if index>=0:self.flush();self.draft.MoveProperty(index,offset);self.rebuild();self.pages.setCurrentIndex(max(0,min(index+offset,self.pages.count()-1)))

    def apply(self):
        try:
            self.flush();self.draft.Name=self.name.text()
            if self.kind=='Materials':self.draft.Description=self.description.text()
            result=self.draft.Commit()
            if self.kind!='Solution controls' or result:self.accept()
        except Exception as error:self.error.setText(message(error))


class MaterialDialog(MultiPropertyDialog):
    def __init__(self,parent,name=None):super().__init__(parent,name)


class ParametersDialog(QtWidgets.QDialog):
    def __init__(self,parent):
        super().__init__(parent)
        self.draft=parent.authoring.Parameters()
        self.setWindowTitle('Equation parameters');self.resize(880,560)
        layout=QtWidgets.QVBoxLayout(self)
        self.error=QtWidgets.QLabel();self.error.setWordWrap(True);self.error.setStyleSheet('color: #b83b35')
        self.table=TableWidget(self.draft.Table,self.error.setText,self)
        layout.addWidget(self.table);layout.addWidget(self.error)
        row=QtWidgets.QHBoxLayout()
        for label,cb in [('Evaluate',self.evaluate),('OK',self.apply),('Cancel',self.reject)]:
            button=QtWidgets.QPushButton(label);button.clicked.connect(cb);row.addWidget(button)
        layout.addLayout(row)

    def evaluate(self):
        try:self.table.flush();self.draft.Evaluate();self.table.rebuild()
        except Exception as error:self.error.setText(message(error))

    def apply(self):
        try:self.table.flush();self.draft.Commit();self.accept()
        except Exception as error:self.error.setText(message(error));self.table.rebuild()

    def reject(self):self.draft.Cancel();super().reject()

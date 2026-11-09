"""Native controls over the original viewport property views."""
from PyQt6 import QtCore,QtWidgets
from PrePoMaxX.UI import PresentationEditSession
from PrePoMaxX.UI.OriginalForms import TransformationEditSession
from authoring_widgets import PropertyPanel,message

class PresentationDialog(QtWidgets.QDialog):
    def __init__(self,owner,family):
        super().__init__(owner);self.owner=owner;self.rule=PresentationEditSession(owner.controller,family);self.setWindowTitle(family);self.resize(650,620)
        layout=QtWidgets.QVBoxLayout(self);self.scroll=QtWidgets.QScrollArea();self.scroll.setWidgetResizable(True);layout.addWidget(self.scroll);self.error=QtWidgets.QLabel();layout.addWidget(self.error)
        self.rebuild();buttons=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok|QtWidgets.QDialogButtonBox.StandardButton.Apply|QtWidgets.QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(lambda:self.apply(True));buttons.rejected.connect(self.reject);buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply);layout.addWidget(buttons)
    def rebuild(self):
        self.panel=PropertyPanel(self.rule.Properties,self.error.setText,changed=self.rebuild);old=self.scroll.takeWidget();self.scroll.setWidget(self.panel)
        if old:old.deleteLater()
    def apply(self,close=False):
        try:self.panel.flush();self.rule.Apply();self.owner.refresh();self.owner.fit() if self.windowTitle()=='Exploded view' else None;self.accept() if close else None
        except Exception as e:self.error.setText(message(e))

class TransformationsDialog(QtWidgets.QDialog):
    def __init__(self,owner):
        super().__init__(owner);self.owner=owner;self.rule=TransformationEditSession(owner.controller);self.setWindowTitle('Result transformations');self.resize(750,650)
        layout=QtWidgets.QVBoxLayout(self);row=QtWidgets.QHBoxLayout();self.types=QtWidgets.QComboBox();self.types.addItems(['Symmetry X','Symmetry Y','Symmetry Z','Linear pattern','Circular pattern']);row.addWidget(self.types);add=QtWidgets.QPushButton('Add');add.clicked.connect(self.add);row.addWidget(add);remove=QtWidgets.QPushButton('Remove');remove.clicked.connect(self.remove);row.addWidget(remove)
        for text,delta in [('Move up',-1),('Move down',1)]:
            button=QtWidgets.QPushButton(text);button.clicked.connect(lambda checked=False,d=delta:self.move(d));row.addWidget(button)
        layout.addLayout(row);self.items=QtWidgets.QListWidget();layout.addWidget(self.items);self.scroll=QtWidgets.QScrollArea();self.scroll.setWidgetResizable(True);layout.addWidget(self.scroll);self.error=QtWidgets.QLabel();layout.addWidget(self.error);self.panel=None
        self.items.currentRowChanged.connect(self.select);self.rebuild()
        buttons=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok|QtWidgets.QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(self.apply);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
    def flush(self):
        if self.panel:self.panel.flush()
    def rebuild(self,index=0):
        self.items.blockSignals(True);self.items.clear();self.items.addItems([self.rule.Name(i) for i in range(self.rule.Count)]);self.items.setCurrentRow(min(index,self.rule.Count-1));self.items.blockSignals(False);self.select(self.items.currentRow())
    def select(self,index):
        try:
            self.flush();self.panel=PropertyPanel(self.rule.Properties(index),self.error.setText) if index>=0 else None
            old=self.scroll.takeWidget()
            if self.panel:self.scroll.setWidget(self.panel)
            if old:old.deleteLater()
        except Exception as e:self.error.setText(message(e))
    def add(self):self.flush();self.rule.Add(self.types.currentIndex());self.rebuild(self.rule.Count-1)
    def remove(self):
        if self.items.currentRow()>=0:self.rule.Remove(self.items.currentRow());self.panel=None;self.rebuild()
    def move(self,delta):
        index=self.items.currentRow()
        if index>=0:self.flush();self.rule.Move(index,delta);self.panel=None;self.rebuild(max(0,index+delta))
    def apply(self):
        try:self.flush();self.rule.ApplyTransformation();self.owner.refresh();self.accept()
        except Exception as e:self.error.setText(message(e))

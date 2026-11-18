"""C3 toolkit controls. Original C# form rules own engineering and commands."""
from PyQt6 import QtCore, QtWidgets
from System import Array, Int32
from authoring_widgets import PropertyDialog, message

class GeometryDialog(PropertyDialog):
    def __init__(self,parent,family,name=None,parts=None):
        rule=parent.geometry.Edit(family,name,parts)
        super().__init__(parent,family,name=name,rule=rule)
        self.setWindowTitle(family if name is None else 'Edit '+name)
        self.setWindowModality(QtCore.Qt.WindowModality.NonModal)
        row=QtWidgets.QHBoxLayout()
        if rule.CanPreview:
            button=QtWidgets.QPushButton('Preview');button.clicked.connect(self.preview);row.addWidget(button)
        if rule.CanReset:
            button=QtWidgets.QPushButton('Reset');button.clicked.connect(self.reset);row.addWidget(button)
        self.layout().insertLayout(self.layout().count()-1,row)

    def target(self,prefix):
        return {'Part':'Pick geometry part','Element':'Pick element','Node':'Pick node','Geometry':'Pick geometry','GeometrySurface':'Pick geometry surface','Surface':'Pick surface','GeometryEdge':'Pick geometry edge'}[str(self.rule.SelectionKind(prefix))]

    def prepare_selection(self,prefix):
        self.flush()
        self.rule.PrepareSelection(prefix)
        self.parent_window.pick_mode.setCurrentText(self.target(prefix))
        self.parent_window.selected=[]
        self.parent_window.render()
        self.error.setText('Pick in the viewport, then use the picked selection for '+(prefix or 'Region')+'.')

    def done(self,result):
        self.rule.Close()
        super().done(result)

    def apply(self):
        try:
            self.flush()
            self.parent_window.run_operation(self.rule.CommitInBackground(),self.accept,self)
        except Exception as error:self.error.setText(message(error))

    def preview(self):
        try:
            self.flush()
            self.parent_window.run_operation(self.rule.PreviewInBackground(),lambda:self.parent_window.show_preview(),self)
        except Exception as error:self.error.setText(message(error))

    def reset(self):
        try:self.rule.Reset();self.rebuild()
        except Exception as error:self.error.setText(message(error))

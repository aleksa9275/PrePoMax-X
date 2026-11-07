"""Controls for job-owned original mesh transforms and boundary extraction."""
from PyQt6 import QtWidgets

class MeshEditDialog(QtWidgets.QDialog):
    def __init__(self,parent,scene):
        super().__init__(parent);self.setWindowTitle('Edit mesh');self.resize(600,440)
        form=QtWidgets.QFormLayout(self)
        note=QtWidgets.QLabel('Mesh coordinates use the selected model length units. Extraction creates a new mesh from complete exterior faces or edges, including midsides. Configure its sections and loads after extraction.');note.setWordWrap(True);form.addRow(note)
        self.operation=QtWidgets.QComboBox()
        for label,key in [('Translate','translate'),('Rotate','rotate'),('Scale','scale'),('Renumber IDs','renumber'),('Extract surface mesh','surface'),('Extract edge mesh','edge')]:self.operation.addItem(label,key)
        self.region=QtWidgets.QComboBox();self.region.addItem('Whole mesh',None)
        for s in scene.get('nodeSets',[]):self.region.addItem(s['name'],s['name'])
        self.vector=QtWidgets.QLineEdit('0, 0, 0');self.center=QtWidgets.QLineEdit('0, 0, 0');self.axis=QtWidgets.QLineEdit('0, 0, 1');self.angle=QtWidgets.QLineEdit('0');self.nodes=QtWidgets.QSpinBox();self.nodes.setRange(1,2000000000);self.elements=QtWidgets.QSpinBox();self.elements.setRange(1,2000000000)
        self.formulation=QtWidgets.QLineEdit();self.formulation.setPlaceholderText('Blank = original shell/truss topology')
        for label,widget in [('Operation',self.operation),('Node region',self.region),('Translation / scale factors',self.vector),('Center',self.center),('Axis',self.axis),('Angle [degrees]',self.angle),('First node ID',self.nodes),('First element ID',self.elements),('Extracted formulation',self.formulation)]:form.addRow(label,widget)
        self.message=QtWidgets.QLabel();form.addRow(self.message)
        buttons=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok|QtWidgets.QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(self.apply);buttons.rejected.connect(self.reject);form.addRow(buttons)
        self.operation.currentIndexChanged.connect(self.refresh);self.refresh();self.recipe=None
    def refresh(self):
        op=self.operation.currentData()
        for w,enabled in [(self.region,op!='renumber'),(self.vector,op in ('translate','scale')),(self.center,op in ('scale','rotate')),(self.axis,op=='rotate'),(self.angle,op=='rotate'),(self.nodes,op=='renumber'),(self.elements,op=='renumber'),(self.formulation,op in ('surface','edge'))]:w.setEnabled(enabled)
    def collect(self):
        op=self.operation.currentData();recipe={'operation':op}
        if op!='renumber' and self.region.currentData():recipe['nodeSet']=self.region.currentData()
        def vector(w):
            values=[float(v.strip()) for v in w.text().split(',')]
            if len(values)!=3:raise ValueError('Enter three comma-separated coordinates.')
            return values
        if op in ('translate','scale'):recipe['vector']=vector(self.vector)
        if op in ('scale','rotate'):recipe['center']=vector(self.center)
        if op=='rotate':recipe.update(axis=vector(self.axis),angleDegrees=float(self.angle.text()))
        if op=='renumber':recipe.update(startNode=self.nodes.value(),startElement=self.elements.value())
        if op in ('surface','edge') and self.formulation.text().strip():recipe['formulation']=self.formulation.text().strip()
        return recipe
    def apply(self):
        try:self.recipe=self.collect();self.accept()
        except ValueError as e:self.message.setText(str(e))

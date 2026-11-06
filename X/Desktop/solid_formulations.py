"""Presentation for topology-compatible original solid formulation choices."""
from PyQt6 import QtCore, QtWidgets


class SolidFormulationDialog(QtWidgets.QDialog):
    def __init__(self, parent, scene):
        super().__init__(parent)
        self.setWindowTitle('Solid element formulations')
        self.resize(650, 380)
        layout=QtWidgets.QVBoxLayout(self)
        note=QtWidgets.QLabel('Choose the solver formulation for each imported element block. '
            'Coordinates, connectivity and named regions are preserved. '
            'Pyramid solver conversion is selected in Configure → Model / units.')
        note.setWordWrap(True);layout.addWidget(note)
        blocks=scene.get('elementBlocks',[])
        self.table=QtWidgets.QTableWidget(len(blocks),3)
        self.table.setHorizontalHeaderLabels(['Element block','Elements','Formulation'])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.choices=[]
        for i,block in enumerate(blocks):
            for column,text in enumerate((block.get('name') or f'Block {i+1}',str(block['count']))):
                item=QtWidgets.QTableWidgetItem(text)
                item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(i,column,item)
            combo=QtWidgets.QComboBox();combo.setObjectName('solidFormulation_'+str(i))
            options=block['compatibleFormulations']
            for name in options:combo.addItem(name,name)
            if not options:combo.addItem(block['formulation'],block['formulation']);combo.setEnabled(False)
            combo.setCurrentIndex(max(0,combo.findData(block['formulation'])))
            self.table.setCellWidget(i,2,combo);self.choices.append(combo)
        layout.addWidget(self.table)
        buttons=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok|QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons)

    def values(self):
        return [combo.currentData() for combo in self.choices]

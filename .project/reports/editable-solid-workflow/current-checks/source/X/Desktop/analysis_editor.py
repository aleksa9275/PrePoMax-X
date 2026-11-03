"""Presentation for the existing static definition. C# owns engineering semantics."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile

from PyQt6 import QtCore, QtWidgets
from jobs import validation_command


def new_definition():
    # Labels and step controls only: physical properties, units and regions must
    # be chosen explicitly. No support/load is inferred from mesh geometry.
    return {'schemaVersion': 1, 'unitSystem': '',
        'materials': [{'name': 'Material-1', 'youngsModulus': '', 'poissonsRatio': ''}],
        'sections': [], 'step': {'name': 'Static-1', 'timePeriod': 1,
            'initialTimeIncrement': 1, 'minimumTimeIncrement': 1e-5,
            'maximumTimeIncrement': 1, 'maximumIncrements': 100, 'outputFrequency': 1,
            'constraints': [], 'loads': [], 'nodalHistorySets': [], 'elementHistorySets': []}}


def validate_definition(mesh_bytes, definition, command=None):
    """Use original model/deck validation; do not evaluate equations in Python."""
    with tempfile.TemporaryDirectory(prefix='prepomaxx-validation-') as name:
        folder = Path(name)
        mesh, analysis = folder / 'mesh.inp', folder / 'analysis.json'
        mesh.write_bytes(mesh_bytes)
        analysis.write_text(json.dumps(definition, allow_nan=False), encoding='utf-8')
        done = subprocess.run([*(command or validation_command()), str(mesh), str(analysis)],
                              capture_output=True, text=True, timeout=60)
        try:
            value = json.loads(done.stdout if done.returncode == 0 else done.stderr)
        except ValueError:
            raise ValueError(done.stderr.strip() or done.stdout.strip() or 'Validation host did not return an outcome')
        if done.returncode or value.get('success') is not True or value.get('solverExecuted') is not False:
            raise ValueError(value.get('error') or 'Original model/deck validation failed')
        return value


class Rows(QtWidgets.QWidget):
    def __init__(self, columns, defaults, rows, choices=None):
        super().__init__()
        self.columns, self.defaults, self.choices = columns, defaults, choices or {}
        layout = QtWidgets.QVBoxLayout(self)
        self.table = QtWidgets.QTableWidget(0, len(columns))
        self.table.setHorizontalHeaderLabels([label for key, label in columns])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
        buttons = QtWidgets.QHBoxLayout()
        add = QtWidgets.QPushButton('Add')
        remove = QtWidgets.QPushButton('Remove selected')
        add.clicked.connect(lambda: self.add(copy.deepcopy(self.defaults)))
        remove.clicked.connect(self.remove)
        buttons.addWidget(add)
        buttons.addWidget(remove)
        buttons.addStretch()
        layout.addLayout(buttons)
        for row in rows:
            self.add(row)

    def add(self, values):
        row = self.table.rowCount()
        self.table.insertRow(row)
        for column, (key, label) in enumerate(self.columns):
            value = values.get(key)
            text = '' if value is None else str(value)
            if key in self.choices:
                combo = QtWidgets.QComboBox()
                combo.addItem('Choose…', '')
                for name in self.choices[key]:
                    combo.addItem(name, name)
                index = combo.findData(text)
                if index == -1:
                    combo.addItem(text + ' (missing)', text)
                    index = combo.count() - 1
                combo.setCurrentIndex(index)
                self.table.setCellWidget(row, column, combo)
            else:
                self.table.setItem(row, column, QtWidgets.QTableWidgetItem(text))

    def remove(self):
        for row in sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True):
            self.table.removeRow(row)

    def values(self):
        rows = []
        for row in range(self.table.rowCount()):
            value = {}
            for column, (key, label) in enumerate(self.columns):
                widget = self.table.cellWidget(row, column)
                value[key] = widget.currentData() if widget else self.table.item(row, column).text().strip()
            rows.append(value)
        return rows


class AnalysisDialog(QtWidgets.QDialog):
    def __init__(self, parent, scene, mesh_bytes, definition, tab=0):
        super().__init__(parent)
        self.setWindowTitle('Configure static solid analysis')
        self.resize(820, 580)
        self.scene, self.mesh_bytes = scene, mesh_bytes
        self.original = copy.deepcopy(definition)
        self.definition = None
        self.validation = None
        layout = QtWidgets.QVBoxLayout(self)
        note = QtWidgets.QLabel('Static solid preview · regions use named sets from the imported mesh. '
            'Equations and quantities are evaluated by the original model services.')
        note.setWordWrap(True)
        layout.addWidget(note)
        self.tabs = QtWidgets.QTabWidget()
        layout.addWidget(self.tabs)
        model = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(model)
        self.units = QtWidgets.QComboBox()
        self.units.addItem('Choose mesh units…', '')
        self.units.addItem('mm · N · s · °C (stress: MPa)', 'mm-N-s-C')
        self.units.addItem('m · N · s · °C (stress: Pa)', 'm-N-s-C')
        self.units.setCurrentIndex(max(0, self.units.findData(definition['unitSystem'])))
        form.addRow('Mesh unit system', self.units)
        warning = QtWidgets.QLabel('Choosing units interprets the existing mesh coordinates; it does not rescale them. '
            'Enter quantities such as 210 GPa or 25 N, or original supported equations. '
            'Only mesh data is imported from INP; existing analysis definitions are not imported.')
        warning.setWordWrap(True)
        form.addRow(warning)
        inventory = QtWidgets.QLabel('\n'.join(
            [f"{len(scene['nodes'])} nodes · {len(scene['elements'])} elements",
             'Node sets: ' + ', '.join(item['name'] for item in scene.get('nodeSets', [])),
             'Element sets: ' + ', '.join(item['name'] for item in scene.get('elementSets', []))]))
        inventory.setWordWrap(True)
        form.addRow(inventory)
        issues = scene.get('warnings', []) + scene.get('omittedKeywords', [])
        if issues:
            notice = QtWidgets.QLabel('Reader notices: ' + '; '.join(map(str, issues)))
            notice.setWordWrap(True)
            form.addRow(notice)
        self.tabs.addTab(model, 'Model / units')
        self.materials = Rows([('name', 'Name'), ('youngsModulus', "Young’s modulus"),
            ('poissonsRatio', 'Poisson ratio')], {'name': '', 'youngsModulus': '', 'poissonsRatio': ''}, definition['materials'])
        self.tabs.addTab(self.materials, 'Materials')
        self.sections = Rows([('name', 'Name'), ('material', 'Material'), ('elementSet', 'Element set')],
            {'name': '', 'material': '', 'elementSet': ''}, definition['sections'],
            {'elementSet': [item['name'] for item in scene.get('elementSets', [])]})
        self.tabs.addTab(self.sections, 'Solid sections')
        nodes = [item['name'] for item in scene.get('nodeSets', [])]
        supports = [{**row, **{f'u{i}': value for i, value in enumerate(row['displacements'])}}
                    for row in definition['step']['constraints']]
        self.supports = Rows([('name', 'Name'), ('nodeSet', 'Node set'), ('u0', 'U1'), ('u1', 'U2'), ('u2', 'U3')],
            {'name': '', 'nodeSet': '', 'u0': '', 'u1': '', 'u2': ''}, supports, {'nodeSet': nodes})
        self.supports.layout().insertWidget(0, QtWidgets.QLabel('Blank displacement = free. Zero = fixed. Quantities use the chosen length unit.'))
        self.tabs.addTab(self.supports, 'Supports')
        loads = [{**row, **{f'f{i}': value for i, value in enumerate(row['forcePerNode'])}}
                 for row in definition['step']['loads']]
        self.loads = Rows([('name', 'Name'), ('nodeSet', 'Node set'), ('f0', 'F1 / node'), ('f1', 'F2 / node'), ('f2', 'F3 / node')],
            {'name': '', 'nodeSet': '', 'f0': '0', 'f1': '0', 'f2': '0'}, loads, {'nodeSet': nodes})
        self.loads.layout().insertWidget(0, QtWidgets.QLabel('Each entered force is applied to every node in its set; it is not a total force.'))
        self.tabs.addTab(self.loads, 'Nodal loads')
        step_page = QtWidgets.QWidget()
        step_form = QtWidgets.QFormLayout(step_page)
        self.step_fields = {}
        for key, label in [('name', 'Step name'), ('timePeriod', 'Time period [s]'),
                ('initialTimeIncrement', 'Initial increment [s]'), ('minimumTimeIncrement', 'Minimum increment [s]'),
                ('maximumTimeIncrement', 'Maximum increment [s]'), ('maximumIncrements', 'Maximum increments'),
                ('outputFrequency', 'Output frequency')]:
            field = QtWidgets.QLineEdit(str(definition['step'][key]))
            self.step_fields[key] = field
            step_form.addRow(label, field)
        self.nodal_history = self.history_list(nodes, definition['step']['nodalHistorySets'])
        self.element_history = self.history_list([item['name'] for item in scene.get('elementSets', [])], definition['step']['elementHistorySets'])
        step_form.addRow('U / RF histories', self.nodal_history)
        step_form.addRow('Stress histories', self.element_history)
        self.tabs.addTab(step_page, 'Step / output')
        self.tabs.setCurrentIndex(tab)
        self.message = QtWidgets.QLabel('Project saving is not available in this preview. Run inputs are retained with the job.')
        self.message.setWordWrap(True)
        layout.addWidget(self.message)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Apply |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        validate = buttons.addButton('Validate', QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
        validate.clicked.connect(self.validate_current)
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def history_list(names, selected):
        widget = QtWidgets.QListWidget()
        widget.setMaximumHeight(85)
        for name in dict.fromkeys([*names, *selected]):
            item = QtWidgets.QListWidgetItem(name, widget)
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.CheckState.Checked if name in selected else QtCore.Qt.CheckState.Unchecked)
        return widget

    def collect(self):
        value = copy.deepcopy(self.original)
        value['unitSystem'] = self.units.currentData()
        value['materials'], value['sections'] = self.materials.values(), self.sections.values()
        value['step']['constraints'] = [{'name': row['name'], 'nodeSet': row['nodeSet'],
            'displacements': [row[f'u{i}'] or None for i in range(3)]} for row in self.supports.values()]
        value['step']['loads'] = [{'name': row['name'], 'nodeSet': row['nodeSet'],
            'forcePerNode': [row[f'f{i}'] for i in range(3)]} for row in self.loads.values()]
        for key, field in self.step_fields.items():
            text = field.text().strip()
            try:
                value['step'][key] = text if key == 'name' else int(text) if key in ('maximumIncrements', 'outputFrequency') else float(text)
            except ValueError:
                raise ValueError('Enter a valid number for ' + key)
        for key, widget in [('nodalHistorySets', self.nodal_history), ('elementHistorySets', self.element_history)]:
            value['step'][key] = [widget.item(i).text() for i in range(widget.count())
                                  if widget.item(i).checkState() == QtCore.Qt.CheckState.Checked]
        return value

    def validate_current(self):
        try:
            value = self.collect()
            outcome = validate_definition(self.mesh_bytes, value)
            self.definition, self.validation = value, outcome
            self.message.setText('Valid static definition. Original model/deck checks passed; no solver was started.')
            return True
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            self.definition = self.validation = None
            self.message.setText(str(error))
            return False

    def apply(self):
        if self.validate_current():
            self.accept()

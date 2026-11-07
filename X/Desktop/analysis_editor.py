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
    changed = QtCore.pyqtSignal()

    def __init__(self, columns, defaults, rows, choices=None):
        super().__init__()
        self.columns, self.defaults, self.choices = columns, defaults, choices or {}
        layout = QtWidgets.QVBoxLayout(self)
        self.table = QtWidgets.QTableWidget(0, len(columns))
        self.table.setHorizontalHeaderLabels([label for key, label in columns])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.itemChanged.connect(lambda _: self.changed.emit())
        layout.addWidget(self.table)
        buttons = QtWidgets.QHBoxLayout()
        add = QtWidgets.QPushButton('Add')
        remove = QtWidgets.QPushButton('Remove selected')
        add.setAutoDefault(False)
        remove.setAutoDefault(False)
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
                combo.currentIndexChanged.connect(lambda _: self.changed.emit())
                self.table.setCellWidget(row, column, combo)
            else:
                self.table.setItem(row, column, QtWidgets.QTableWidgetItem(text))
        self.changed.emit()

    def remove(self):
        for row in sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True):
            self.table.removeRow(row)
        self.changed.emit()

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
        self.setWindowTitle('Configure solid analysis')
        self.resize(980, 680)
        self.scene, self.mesh_bytes = scene, mesh_bytes
        self.original = copy.deepcopy(definition)
        self.definition = None
        self.validation = None
        layout = QtWidgets.QVBoxLayout(self)
        note = QtWidgets.QLabel('Mechanical solid analysis · regions use named sets from the imported mesh. '
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
        self.pyramid_conversion = None
        if any(e.get('vtkCellType') in (14,27) for e in scene['elements']) or definition.get('pyramidConversion'):
            self.pyramid_conversion = QtWidgets.QComboBox()
            self.pyramid_conversion.setObjectName('pyramidConversion')
            self.pyramid_conversion.addItem('Choose original solver export…', None)
            self.pyramid_conversion.addItem('Collapsed wedges', 'wedges')
            self.pyramid_conversion.addItem('Collapsed hexahedrons', 'hexahedrons')
            self.pyramid_conversion.setCurrentIndex(max(0,self.pyramid_conversion.findData(definition.get('pyramidConversion'))))
            self.pyramid_conversion.currentIndexChanged.connect(self.mark_changed)
            form.addRow('Pyramid conversion', self.pyramid_conversion)
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
        # Original optional mechanical properties remain attached to named materials.
        properties=QtWidgets.QWidget();prop_layout=QtWidgets.QVBoxLayout(properties)
        material_names=[m['name'] for m in definition['materials']]
        self.mechanical_properties=Rows([('material','Material'),('density','Density'),('hardening','Plastic hardening')],
            {'material':'','density':'','hardening':'Isotropic'},
            [{'material':m['name'],'density':m.get('density',''),'hardening':m.get('hardening','Isotropic')} for m in definition['materials']],
            {'material':material_names,'hardening':['Isotropic','Kinematic','Combined']})
        prop_layout.addWidget(QtWidgets.QLabel('Density uses the selected unit system; quantities such as 1000 kg/m³ are accepted.'))
        prop_layout.addWidget(self.mechanical_properties)
        curves=[{'material':m['name'],'stress':r[0],'strain':r[1]} for m in definition['materials'] for r in (m.get('plasticCurve') or [])]
        self.plastic_curve=Rows([('material','Material'),('stress','True yield stress'),('strain','Plastic strain')],
            {'material':'','stress':'','strain':''},curves,{'material':material_names})
        prop_layout.addWidget(QtWidgets.QLabel('Optional plastic curve: begin at plastic strain 0; enter rows in increasing strain order.'))
        prop_layout.addWidget(self.plastic_curve);self.tabs.addTab(properties,'Density / plasticity')
        pressure_rows=[{'name':r['name'],'nodeSet':r.get('nodeSet',''),'elementSet':r.get('elementSet',''),
                        'face':'' if r.get('face') is None else str(r['face']),'magnitude':r['magnitude']} for r in (definition['step'].get('pressures') or [])]
        self.pressures=Rows([('name','Name'),('nodeSet','Boundary node set'),('elementSet','Element set'),('face','Face 1–6'),('magnitude','Pressure')],
            {'name':'','nodeSet':'','elementSet':'','face':'','magnitude':'0'},pressure_rows,
            {'nodeSet':nodes,'elementSet':[v['name'] for v in scene.get('elementSets',[])]})
        self.pressures.layout().insertWidget(0,QtWidgets.QLabel('Positive pressure acts inward. Choose a boundary node set OR an element set and its local face number.'))
        if any(e.get('vtkCellType')==27 for e in scene['elements']):
            caveat=QtWidgets.QLabel('Quadratic pyramids under pressure: hexahedron conversion matches the analytical example. '
                'Wedge conversion retains a measured discrepancy in the original solver.')
            caveat.setWordWrap(True);self.pressures.layout().insertWidget(1,caveat)
        self.tabs.addTab(self.pressures,'Pressure')
        gravity_rows=[{'name':r['name'],'elementSet':r['elementSet'],**{f'a{i}':v for i,v in enumerate(r['acceleration'])}} for r in (definition['step'].get('gravityLoads') or [])]
        self.gravity=Rows([('name','Name'),('elementSet','Element set'),('a0','Acceleration 1'),('a1','Acceleration 2'),('a2','Acceleration 3')],
            {'name':'','elementSet':'','a0':'0','a1':'0','a2':'0'},gravity_rows,{'elementSet':[v['name'] for v in scene.get('elementSets',[])]})
        self.gravity.layout().insertWidget(0,QtWidgets.QLabel('Every gravity-loaded element requires a material density. Acceleration uses mesh length / s².'))
        self.tabs.addTab(self.gravity,'Gravity')
        self.nonlinear=QtWidgets.QCheckBox('Geometric nonlinearity (NLGEOM)')
        self.nonlinear.setChecked(definition['step'].get('nonlinearGeometry',False))
        step_form.insertRow(0,self.nonlinear)
        eigen=QtWidgets.QWidget();eigen_form=QtWidgets.QFormLayout(eigen)
        self.analysis_kind=QtWidgets.QComboBox();self.analysis_kind.setObjectName('analysisKind')
        for label,key in [('Static','static'),('Frequency / mode shapes','frequency'),('Linear buckling','buckling')]:self.analysis_kind.addItem(label,key)
        self.analysis_kind.setCurrentIndex(max(0,self.analysis_kind.findData(definition['step'].get('kind','static'))))
        self.mode_count=QtWidgets.QSpinBox();self.mode_count.setRange(1,1000);self.mode_count.setValue(definition['step'].get('modes',10))
        self.frequency_lower=QtWidgets.QLineEdit('' if definition['step'].get('lowerFrequency') is None else str(definition['step']['lowerFrequency']))
        self.frequency_upper=QtWidgets.QLineEdit('' if definition['step'].get('upperFrequency') is None else str(definition['step']['upperFrequency']))
        self.buckling_accuracy=QtWidgets.QDoubleSpinBox();self.buckling_accuracy.setDecimals(10);self.buckling_accuracy.setRange(1e-10,1);self.buckling_accuracy.setValue(definition['step'].get('bucklingAccuracy',.0001))
        eigen_form.addRow('Analysis type',self.analysis_kind);eigen_form.addRow('Requested modes / load factors',self.mode_count)
        eigen_form.addRow('Lower frequency [Hz], blank = unspecified',self.frequency_lower);eigen_form.addRow('Upper frequency [Hz], blank = unspecified',self.frequency_upper)
        eigen_form.addRow('Buckling accuracy',self.buckling_accuracy)
        eigen_note=QtWidgets.QLabel('Frequency requires density and homogeneous supports; remove applied loads. Buckling uses homogeneous supports and a nonzero reference load. Mode amplitudes have arbitrary normalization. The original buckling search can omit factors below 1; reference-load scaling should be checked. Static time controls apply only to static analysis.')
        eigen_note.setWordWrap(True);eigen_form.addRow(eigen_note);self.tabs.addTab(eigen,'Analysis type / modes')
        def update_kind():
            kind=self.analysis_kind.currentData();static=kind=='static'
            for key,field in self.step_fields.items():field.setEnabled(static or key in ('name','outputFrequency'))
            self.nonlinear.setEnabled(static);self.mode_count.setEnabled(not static)
            self.frequency_lower.setEnabled(kind=='frequency');self.frequency_upper.setEnabled(kind=='frequency');self.buckling_accuracy.setEnabled(kind=='buckling')
            self.mark_changed()
        self.analysis_kind.currentIndexChanged.connect(update_kind)
        self.mode_count.valueChanged.connect(self.mark_changed);self.frequency_lower.textChanged.connect(self.mark_changed);self.frequency_upper.textChanged.connect(self.mark_changed);self.buckling_accuracy.valueChanged.connect(self.mark_changed)
        self.tabs.setCurrentIndex(tab)
        self.message = QtWidgets.QLabel('Project saving is not available in this preview. Run inputs are retained with the job.')
        self.message.setWordWrap(True)
        layout.addWidget(self.message)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Apply |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        validate = buttons.addButton('Validate', QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
        validate.setAutoDefault(False)
        validate.clicked.connect(self.validate_current)
        apply_button = buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Apply)
        apply_button.setDefault(True)
        apply_button.clicked.connect(self.apply)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        for rows in (self.materials, self.sections, self.supports, self.loads, self.mechanical_properties, self.plastic_curve, self.pressures, self.gravity):
            rows.changed.connect(self.mark_changed)
        self.materials.changed.connect(self.refresh_material_options)
        self.nonlinear.toggled.connect(self.mark_changed)
        self.units.currentIndexChanged.connect(self.mark_changed)
        for field in self.step_fields.values():
            field.textChanged.connect(self.mark_changed)
        self.nodal_history.itemChanged.connect(self.mark_changed)
        self.element_history.itemChanged.connect(self.mark_changed)
        update_kind()

    def refresh_material_options(self):
        names=[r['name'] for r in self.materials.values() if r['name']]
        for rows in (self.mechanical_properties,self.plastic_curve):
            rows.choices['material']=names
            for i in range(rows.table.rowCount()):
                combo=rows.table.cellWidget(i,0);current=combo.currentData()
                with QtCore.QSignalBlocker(combo):
                    combo.clear();combo.addItem('Choose…','')
                    for name in names:combo.addItem(name,name)
                    if current and current not in names:combo.addItem(current+' (missing)',current)
                    combo.setCurrentIndex(max(0,combo.findData(current)))

    def mark_changed(self, *args):
        self.definition = self.validation = None
        self.message.setText('Definition changed. Validate or Apply to run the original model/deck checks.')

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
        if self.pyramid_conversion is not None:
            choice=self.pyramid_conversion.currentData()
            if choice is None: value.pop('pyramidConversion',None)
            else: value['pyramidConversion']=choice
        value['materials'], value['sections'] = self.materials.values(), self.sections.values()
        by_name={m['name']:m for m in value['materials']}
        properties={}
        for row in self.mechanical_properties.values():
            name=row['material']
            if name not in by_name:
                if not row['density']:continue
                raise ValueError('Mechanical properties refer to a missing material: '+name)
            if name in properties:raise ValueError('Use one density/hardening row per material.')
            properties[name]=row
            if row['density']:by_name[name]['density']=row['density']
        for row in self.plastic_curve.values():
            name=row['material']
            if name not in by_name:raise ValueError('Plastic curve refers to a missing material: '+name)
            by_name[name].setdefault('plasticCurve',[]).append([row['stress'],row['strain']])
            by_name[name]['hardening']=properties.get(name,{}).get('hardening','Isotropic')
        pressures=[]
        for row in self.pressures.values():
            pressure={'name':row['name'],'magnitude':row['magnitude']}
            if row['nodeSet']:pressure['nodeSet']=row['nodeSet']
            if row['elementSet']:pressure['elementSet']=row['elementSet']
            if row['face']:
                try:pressure['face']=int(row['face'])
                except ValueError:raise ValueError('Enter an integer pressure face number 1–6.')
            pressures.append(pressure)
        if pressures or 'pressures' in value['step']:value['step']['pressures']=pressures
        gravity=[{'name':r['name'],'elementSet':r['elementSet'],'acceleration':[r[f'a{i}'] for i in range(3)]} for r in self.gravity.values()]
        if gravity or 'gravityLoads' in value['step']:value['step']['gravityLoads']=gravity
        if self.nonlinear.isChecked() or 'nonlinearGeometry' in value['step']:value['step']['nonlinearGeometry']=self.nonlinear.isChecked()
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
        kind=self.analysis_kind.currentData()
        if kind!='static' or 'kind' in value['step']:value['step']['kind']=kind
        if kind!='static' or 'modes' in value['step']:value['step']['modes']=self.mode_count.value()
        for key,field in [('lowerFrequency',self.frequency_lower),('upperFrequency',self.frequency_upper)]:
            if field.text().strip():value['step'][key]=float(field.text())
            else:value['step'].pop(key,None)
        if kind=='buckling' or 'bucklingAccuracy' in value['step']:value['step']['bucklingAccuracy']=self.buckling_accuracy.value()
        for key, widget in [('nodalHistorySets', self.nodal_history), ('elementHistorySets', self.element_history)]:
            value['step'][key] = [widget.item(i).text() for i in range(widget.count())
                                  if widget.item(i).checkState() == QtCore.Qt.CheckState.Checked]
        return value

    def validate_current(self):
        try:
            value = self.collect()
            outcome = validate_definition(self.mesh_bytes, value)
            self.definition, self.validation = value, outcome
            self.message.setText('Valid mechanical definition. Original model/deck checks passed; no solver was started.')
            return True
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            self.definition = self.validation = None
            self.message.setText(str(error))
            return False

    def apply(self):
        if self.validate_current():
            self.accept()

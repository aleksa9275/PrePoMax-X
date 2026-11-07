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
        self.setWindowTitle('Configure analysis')
        self.resize(980, 680)
        self.scene, self.mesh_bytes = scene, mesh_bytes
        self.original = copy.deepcopy(definition)
        self.definition = None
        self.validation = None
        layout = QtWidgets.QVBoxLayout(self)
        note = QtWidgets.QLabel('Solid / structural analysis · regions use named sets from the imported mesh. '
            'Equations and quantities are evaluated by the original model services.')
        note.setWordWrap(True)
        layout.addWidget(note)
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setUsesScrollButtons(True)
        self.tabs.setElideMode(QtCore.Qt.TextElideMode.ElideNone)
        layout.addWidget(self.tabs)
        model = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(model)
        self.units = QtWidgets.QComboBox()
        self.units.addItem('Choose mesh units…', '')
        self.units.addItem('mm · N · s · °C (stress: MPa)', 'mm-N-s-C')
        self.units.addItem('m · N · s · °C (stress: Pa)', 'm-N-s-C')
        self.units.setCurrentIndex(max(0, self.units.findData(definition['unitSystem'])))
        form.addRow('Mesh unit system', self.units)
        self.model_space = QtWidgets.QComboBox()
        self.model_space.setObjectName('modelSpace')
        for label, key in [('3D solid', 'ThreeD'), ('Plane stress (XY)', 'PlaneStress'),
                           ('Plane strain (XY)', 'PlaneStrain'), ('Axisymmetric (X = radius, Y = axis)', 'Axisymmetric')]:
            self.model_space.addItem(label, key)
        self.model_space.setCurrentIndex(max(0, self.model_space.findData(definition.get('modelSpace', 'ThreeD'))))
        self.model_space.currentIndexChanged.connect(self.mark_changed)
        form.addRow('Model space', self.model_space)
        space_note = QtWidgets.QLabel('Plane/axisymmetric models use U1/U2 and F1/F2. Leave U3 blank and F3 zero. '
            'Plane sections require positive thickness in the chosen length units. '
            'Axisymmetric nodal forces and reactions refer to the full revolution; pressure is force per area. '
            'Pressure faces S3–S6 select the original element edges (solver P1–P4).')
        space_note.setWordWrap(True)
        form.addRow(space_note)
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
        self.sections = Rows([('name', 'Name'), ('material', 'Material'), ('elementSet', 'Element set'), ('thickness', 'Thickness'), ('kind', 'Section kind'), ('offset', 'Shell offset')],
            {'name': '', 'material': '', 'elementSet': '', 'thickness': '', 'kind': 'solid', 'offset': ''}, [{**r, 'kind': r.get('kind', 'solid')} for r in definition['sections']],
            {'elementSet': [item['name'] for item in scene.get('elementSets', [])], 'kind': ['solid', 'shell', 'membrane', 'beam', 'truss', 'composite', 'mass', 'spring', 'gap']})
        self.tabs.addTab(self.sections, 'Sections')
        nodes = [item['name'] for item in scene.get('nodeSets', [])]
        supports = [{**row, **{f'u{i}': value for i, value in enumerate(row['displacements'])}, **{f'r{i}': value for i, value in enumerate(row.get('rotations') or [None]*3)}}
                    for row in definition['step']['constraints']]
        self.supports = Rows([('name', 'Name'), ('nodeSet', 'Node set'), ('u0', 'U1'), ('u1', 'U2'), ('u2', 'U3'), ('r0', 'UR1'), ('r1', 'UR2'), ('r2', 'UR3')],
            {'name': '', 'nodeSet': '', 'u0': '', 'u1': '', 'u2': '', 'r0': '', 'r1': '', 'r2': ''}, supports, {'nodeSet': nodes})
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
        self.nodal_history_label=QtWidgets.QLabel('U / RF histories')
        self.element_history_label=QtWidgets.QLabel('Stress histories')
        step_form.addRow(self.nodal_history_label, self.nodal_history)
        step_form.addRow(self.element_history_label, self.element_history)
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
        self.element_output=QtWidgets.QComboBox();self.element_output.addItems(['Default','TwoD','ThreeD'])
        self.element_output.setCurrentText(definition['step'].get('elementOutput','Default'))
        self.element_output.currentTextChanged.connect(self.mark_changed)
        step_form.addRow('Element result mesh (3D preserves expanded thickness)',self.element_output)
        eigen=QtWidgets.QWidget();eigen_form=QtWidgets.QFormLayout(eigen)
        self.analysis_kind=QtWidgets.QComboBox();self.analysis_kind.setObjectName('analysisKind')
        for label,key in [('Static','static'),('Frequency / mode shapes','frequency'),('Linear buckling','buckling'),('Heat transfer','heat-transfer'),('Implicit transient dynamics','dynamic'),('Modal transient dynamics','modal-dynamics')]:self.analysis_kind.addItem(label,key)
        self.analysis_kind.setCurrentIndex(max(0,self.analysis_kind.findData(definition['step'].get('kind','static'))))
        self.mode_count=QtWidgets.QSpinBox();self.mode_count.setRange(1,1000);self.mode_count.setValue(definition['step'].get('modes',10))
        self.frequency_lower=QtWidgets.QLineEdit('' if definition['step'].get('lowerFrequency') is None else str(definition['step']['lowerFrequency']))
        self.frequency_upper=QtWidgets.QLineEdit('' if definition['step'].get('upperFrequency') is None else str(definition['step']['upperFrequency']))
        self.buckling_accuracy=QtWidgets.QDoubleSpinBox();self.buckling_accuracy.setDecimals(10);self.buckling_accuracy.setRange(1e-10,1);self.buckling_accuracy.setValue(definition['step'].get('bucklingAccuracy',.0001))
        eigen_form.addRow('Analysis type',self.analysis_kind);eigen_form.addRow('Requested modes / load factors',self.mode_count)
        eigen_form.addRow('Lower frequency [Hz], blank = unspecified',self.frequency_lower);eigen_form.addRow('Upper frequency [Hz], blank = unspecified',self.frequency_upper)
        eigen_form.addRow('Buckling accuracy',self.buckling_accuracy)
        eigen_note=QtWidgets.QLabel('Frequency requires density and homogeneous supports; remove applied loads. Buckling uses homogeneous supports and a nonzero reference load. Mode amplitudes have arbitrary normalization. The original buckling search can omit factors below 1; reference-load scaling should be checked. Time controls apply to static and heat-transfer analysis.')
        eigen_note.setWordWrap(True);eigen_form.addRow(eigen_note);self.tabs.addTab(eigen,'Analysis type / modes')
        thermal_page=QtWidgets.QWidget();thermal_layout=QtWidgets.QVBoxLayout(thermal_page)
        thermal_layout.addWidget(QtWidgets.QLabel('Thermal power: mW for mm · N · s; W for m · N · s. Surface flux is positive inward. Nodal power applies to every selected node.'))
        self.thermal_properties=Rows([('material','Material'),('conductivity','Conductivity'),('specificHeat','Specific heat')],
            {'material':'','conductivity':'','specificHeat':''},
            [{'material':m['name'],'conductivity':m.get('conductivity',''),'specificHeat':m.get('specificHeat','')} for m in definition['materials']],{'material':material_names})
        thermal_layout.addWidget(self.thermal_properties)
        thermal_form=QtWidgets.QFormLayout();thermal_layout.addLayout(thermal_form)
        controls=definition['step'].get('thermal') or {}
        self.thermal_steady=QtWidgets.QCheckBox('Steady state');self.thermal_steady.setChecked(controls.get('steadyState',True))
        self.thermal_direct=QtWidgets.QCheckBox('Fixed time increments (Direct)');self.thermal_direct.setChecked(controls.get('direct',False))
        self.thermal_initial=QtWidgets.QLineEdit(controls.get('initialTemperature') or '')
        self.thermal_deltmx=QtWidgets.QLineEdit('' if controls.get('maximumTemperatureChange') is None else str(controls['maximumTemperatureChange']))
        thermal_form.addRow(self.thermal_steady);thermal_form.addRow(self.thermal_direct)
        thermal_form.addRow('Uniform initial temperature (required for transient)',self.thermal_initial)
        thermal_form.addRow('Maximum temperature change / increment (blank = original unlimited)',self.thermal_deltmx)
        self.temperatures=Rows([('name','Name'),('nodeSet','Node set'),('temperature','Temperature')],
            {'name':'','nodeSet':'','temperature':'0'},definition['step'].get('temperatures') or [],{'nodeSet':nodes})
        thermal_layout.addWidget(QtWidgets.QLabel('Prescribed temperatures'));thermal_layout.addWidget(self.temperatures)
        self.absolute_zero=QtWidgets.QLineEdit('' if controls.get('absoluteZero') is None else str(controls['absoluteZero']))
        self.stefan_boltzmann=QtWidgets.QLineEdit('' if controls.get('stefanBoltzmann') is None else str(controls['stefanBoltzmann']))
        thermal_form.addRow('Absolute zero [°C] (required for radiation)',self.absolute_zero)
        thermal_form.addRow('Stefan–Boltzmann [model power / area / K⁴]',self.stefan_boltzmann)
        thermal_scroll=QtWidgets.QScrollArea();thermal_scroll.setWidgetResizable(True);thermal_scroll.setWidget(thermal_page)
        self.tabs.addTab(thermal_scroll,'Heat transfer')
        heat_page=QtWidgets.QWidget();heat_layout=QtWidgets.QVBoxLayout(heat_page)
        heat_note=QtWidgets.QLabel('Nodal: power per node. Body: power / volume on an element set. Surface: power / area on complete exterior faces of a node set. Film: coefficient in power / (area · °C), with sink temperature. Radiation: emissivity [0,1] and sink temperature; enter physical constants on Heat transfer. Constant loads use original step semantics.')
        heat_note.setWordWrap(True);heat_layout.addWidget(heat_note)
        self.heat_loads=Rows([('name','Name'),('kind','Kind'),('region','Named region'),('magnitude','Power / flux / film coefficient'),('sinkTemperature','Film sink temperature')],
            {'name':'','kind':'nodal','region':'','magnitude':'0','sinkTemperature':''},definition['step'].get('heatLoads') or [],
            {'kind':['nodal','body','surface','film','radiation'],'region':list(dict.fromkeys(nodes+[v['name'] for v in scene.get('elementSets',[])]))})
        heat_layout.addWidget(self.heat_loads);self.tabs.addTab(heat_page,'Heat inputs / convection')
        for rows in (self.thermal_properties,self.temperatures,self.heat_loads):rows.changed.connect(self.mark_changed)
        for field in (self.thermal_initial,self.thermal_deltmx):field.textChanged.connect(self.mark_changed)
        for field in (self.thermal_steady,self.thermal_direct):field.toggled.connect(self.mark_changed)
        table_page=QtWidgets.QWidget();table_layout=QtWidgets.QVBoxLayout(table_page)
        table_layout.addWidget(QtWidgets.QLabel('Optional original thermal tables: positive values and strictly increasing temperatures for each material/property. Remove its scalar property before adding a table.'))
        table_rows=[{'material':m['name'],'property':key,'value':row[0],'temperature':row[1]} for m in definition['materials'] for key in ('conductivity','specificHeat','density') for row in (m.get(key+'Table') or [])]
        self.thermal_tables=Rows([('material','Material'),('property','Property'),('value','Property value'),('temperature','Temperature')],
            {'material':'','property':'conductivity','value':'','temperature':''},table_rows,{'material':material_names,'property':['conductivity','specificHeat','density']})
        table_layout.addWidget(self.thermal_tables);self.tabs.addTab(table_page,'Thermal property tables')
        amp_page=QtWidgets.QWidget();amp_layout=QtWidgets.QVBoxLayout(amp_page)
        amp_note=QtWidgets.QLabel('Original tabular amplitude values multiply the assigned quantities. Temperature amplitudes scale absolute entered temperature values, not temperature changes. Times are seconds; shifts and Step/Total time retain original keyword semantics. Original linear static analysis evaluates the final state; transient heat transfer follows its increments.')
        amp_note.setWordWrap(True);amp_layout.addWidget(amp_note)
        self.amplitude_definitions=Rows([('name','Name'),('timeSpan','Time span'),('shiftX','Time shift'),('shiftY','Value shift')],
            {'name':'','timeSpan':'StepTime','shiftX':'0','shiftY':'0'},[{'name':a['name'],'timeSpan':a.get('timeSpan','StepTime'),'shiftX':a.get('shiftX',0),'shiftY':a.get('shiftY',0)} for a in definition.get('amplitudes') or []],{'timeSpan':['StepTime','TotalTime']})
        amp_layout.addWidget(self.amplitude_definitions)
        points=[{'amplitude':a['name'],'time':str(row[0]),'value':str(row[1])} for a in definition.get('amplitudes') or [] for row in a['points']]
        self.amplitude_points=Rows([('amplitude','Amplitude name'),('time','Time [s]'),('value','Multiplier')],{'amplitude':'','time':'0','value':'0'},points)
        amp_layout.addWidget(self.amplitude_points)
        self.binding_sources=[('Support','constraints'),('Nodal force','loads'),('Nodal moment','moments'),('Pressure','pressures'),('Gravity','gravityLoads'),('Temperature BC','temperatures'),('Heat input','heatLoads'),('Temperature field','temperatureFields')]
        bindings=[{'kind':kind,'name':v['name'],'amplitude':v['amplitude']} for kind,key in self.binding_sources for v in definition['step'].get(key) or [] if v.get('amplitude')]
        bindings += [{'kind':'Coefficient / emissivity','name':v['name'],'amplitude':v['coefficientAmplitude']} for v in definition['step'].get('heatLoads') or [] if v.get('coefficientAmplitude')]
        self.amplitude_bindings=Rows([('kind','Target kind'),('name','Target name'),('amplitude','Amplitude name')],{'kind':'Heat input','name':'','amplitude':''},bindings,{'kind':[v[0] for v in self.binding_sources]+['Coefficient / emissivity']})
        amp_layout.addWidget(self.amplitude_bindings);self.tabs.addTab(amp_page,'Amplitudes')
        expansion_page=QtWidgets.QWidget();expansion_layout=QtWidgets.QVBoxLayout(expansion_page)
        expansion_note=QtWidgets.QLabel('Static mechanical thermal expansion uses an explicit uniform initial temperature and full nonoverlapping nodal temperature-field coverage. Supports and mechanical loads retain their original meaning. This is a prescribed temperature calculation; no thermal solution is inferred.')
        expansion_note.setWordWrap(True);expansion_layout.addWidget(expansion_note)
        expansion_form=QtWidgets.QFormLayout();expansion_layout.addLayout(expansion_form)
        self.mechanical_initial=QtWidgets.QLineEdit(definition['step'].get('initialTemperature') or '')
        expansion_form.addRow('Uniform initial temperature',self.mechanical_initial)
        erows=[{'material':m['name'],'coefficient':m['expansion'],'reference':m.get('expansionZeroTemperature','')} for m in definition['materials'] if m.get('expansion') is not None]
        self.expansion_properties=Rows([('material','Material'),('coefficient','Expansion coefficient [1/°C]'),('reference','Reference temperature')],{'material':'','coefficient':'','reference':''},erows,{'material':material_names})
        expansion_layout.addWidget(self.expansion_properties)
        self.temperature_fields=Rows([('name','Name'),('nodeSet','Node set'),('temperature','Prescribed temperature')],{'name':'','nodeSet':'','temperature':'0'},definition['step'].get('temperatureFields') or [],{'nodeSet':nodes})
        expansion_layout.addWidget(self.temperature_fields);self.tabs.addTab(expansion_page,'Thermal expansion / stress')
        for rows in (self.thermal_tables,self.amplitude_definitions,self.amplitude_points,self.amplitude_bindings,self.expansion_properties,self.temperature_fields):rows.changed.connect(self.mark_changed)
        for field in (self.absolute_zero,self.stefan_boltzmann,self.mechanical_initial):field.textChanged.connect(self.mark_changed)
        dynamics_page=QtWidgets.QWidget();dynamics_form=QtWidgets.QFormLayout(dynamics_page)
        note=QtWidgets.QLabel('Linear transient dynamics requires density and zero prescribed supports. Modal dynamics regenerates a stored frequency basis using these supports; physical loads act in the following dynamic step. Time increments and tabular loads use the existing controls.')
        note.setWordWrap(True);dynamics_form.addRow(note)
        controls=definition['step'].get('dynamics') or {}
        self.dynamics_alpha=QtWidgets.QLineEdit(str(controls.get('alpha',-.05)))
        self.dynamics_direct=QtWidgets.QCheckBox('Fixed time increments (Direct)');self.dynamics_direct.setChecked(controls.get('direct',False))
        self.dynamics_damping=QtWidgets.QComboBox();self.dynamics_damping.addItems(['Off','Rayleigh','Constant']);self.dynamics_damping.setCurrentText(controls.get('damping','Off'))
        self.dynamics_mass=QtWidgets.QLineEdit(str(controls.get('massDamping',0)))
        self.dynamics_stiffness=QtWidgets.QLineEdit(str(controls.get('stiffnessDamping',0)))
        self.dynamics_ratio=QtWidgets.QLineEdit(str(controls.get('modalDampingRatio',0)))
        self.dynamics_modes=QtWidgets.QSpinBox();self.dynamics_modes.setRange(1,1000);self.dynamics_modes.setValue(controls.get('basisModes',1))
        self.dynamics_basis=QtWidgets.QLineEdit(controls.get('basisName','Frequency-basis'))
        for label,widget in [('HHT alpha (implicit: −1/3 to 0)',self.dynamics_alpha),('',self.dynamics_direct),('Damping (Constant is modal only)',self.dynamics_damping),('Rayleigh mass coefficient',self.dynamics_mass),('Rayleigh stiffness coefficient',self.dynamics_stiffness),('Modal damping ratio',self.dynamics_ratio),('Stored basis modes',self.dynamics_modes),('Stored basis step name',self.dynamics_basis)]:dynamics_form.addRow(label,widget)
        self.tabs.addTab(dynamics_page,'Dynamics')
        line_page=QtWidgets.QWidget();line_layout=QtWidgets.QVBoxLayout(line_page)
        line_note=QtWidgets.QLabel('Beam: RECT/CIRC dimensions in length units and a nonparallel direction 1. Truss: dimension 1 is area. Composite S8R: one row per layer, in physical stacking order. Element connectivity defines shell normals.');line_note.setWordWrap(True);line_layout.addWidget(line_note)
        self.line_sections=Rows([('section','Section'),('shape','Shape'),('d0','Dimension 1 / area'),('d1','Dimension 2'),('n0','Direction X'),('n1','Direction Y'),('n2','Direction Z')],
            {'section':'','shape':'RECT','d0':'','d1':'','n0':'','n1':'','n2':''},
            [{'section':r['name'],'shape':r.get('shape','RECT'),'d0':(r.get('dimensions') or [''])[0],'d1':(r.get('dimensions') or ['',''])[1] if len(r.get('dimensions') or [])>1 else '',**{f'n{i}':v for i,v in enumerate(r.get('direction') or ['']*3)}} for r in definition['sections'] if r.get('kind') in ('beam','truss')], {'shape':['RECT','CIRC']})
        line_layout.addWidget(self.line_sections)
        self.composite_layers=Rows([('section','Section'),('material','Layer material'),('thickness','Layer thickness')],{'section':'','material':'','thickness':''},
            [{'section':r['name'],**layer} for r in definition['sections'] for layer in r.get('layers') or []])
        line_layout.addWidget(self.composite_layers);self.tabs.addTab(line_page,'Line / layer sections')
        self.moments=Rows([('name','Name'),('nodeSet','Node set'),('m0','M1 per node'),('m1','M2 per node'),('m2','M3 per node')],
            {'name':'','nodeSet':'','m0':'0','m1':'0','m2':'0'},[{**r,**{f'm{i}':v for i,v in enumerate(r['momentPerNode'])}} for r in definition['step'].get('moments') or []],{'nodeSet':nodes})
        self.tabs.addTab(self.moments,'Nodal moments')
        self.discrete_sections=Rows([('section','Section'),('mass','Mass per element'),('stiffness','Stiffness'),('dof','DOF'),('secondDof','Second DOF'),('clearance','Gap clearance'),('tensileForce','Gap tensile force'),('n0','Normal X'),('n1','Normal Y'),('n2','Normal Z')],
            {'section':'','mass':'','stiffness':'','dof':'0','secondDof':'0','clearance':'','tensileForce':'','n0':'','n1':'','n2':''},
            [{'section':r['name'],**r,**{f'n{i}':v for i,v in enumerate(r.get('direction') or ['']*3)}} for r in definition['sections'] if r.get('kind') in ('mass','spring','gap')])
        self.discrete_sections.layout().insertWidget(0,QtWidgets.QLabel('Leave material blank for discrete sections. SPRING1: DOF 1–3. SPRING2: two DOFs. SPRINGA: both zero. Gap: clearance, stiffness and normal. Mass uses the selected mass units.'))
        self.discrete_sections.changed.connect(self.mark_changed)
        self.tabs.addTab(self.discrete_sections,'Mass / spring / gap')
        for rows in (self.line_sections,self.composite_layers,self.moments):rows.changed.connect(self.mark_changed)
        for widget in (self.dynamics_alpha,self.dynamics_mass,self.dynamics_stiffness,self.dynamics_ratio,self.dynamics_basis):widget.textChanged.connect(self.mark_changed)
        self.dynamics_modes.valueChanged.connect(self.mark_changed);self.dynamics_direct.toggled.connect(self.mark_changed);self.dynamics_damping.currentTextChanged.connect(self.mark_changed)
        def update_kind():
            kind=self.analysis_kind.currentData();static=kind=='static';thermal=kind=='heat-transfer';eigen=kind in ('frequency','buckling')
            for key,field in self.step_fields.items():field.setEnabled(static or thermal or kind in ('dynamic','modal-dynamics') or key in ('name','outputFrequency'))
            for widget in (self.dynamics_modes,self.dynamics_ratio,self.dynamics_basis):widget.setEnabled(kind=='modal-dynamics')
            self.dynamics_alpha.setEnabled(kind=='dynamic');self.dynamics_direct.setEnabled(kind=='dynamic')
            self.thermal_tables.setEnabled(thermal or self.thermal_tables.table.rowCount()>0)
            for widget in (self.mechanical_initial,self.expansion_properties,self.temperature_fields):widget.setEnabled(static or (hasattr(widget,'table') and widget.table.rowCount()>0))
            for widget in (self.absolute_zero,self.stefan_boltzmann):widget.setEnabled(thermal)
            self.nonlinear.setEnabled(static);self.mode_count.setEnabled(eigen)
            self.frequency_lower.setEnabled(kind=='frequency');self.frequency_upper.setEnabled(kind=='frequency');self.buckling_accuracy.setEnabled(kind=='buckling')
            for widget in (self.thermal_properties,self.thermal_steady,self.thermal_direct,self.thermal_initial,self.thermal_deltmx,self.temperatures,self.heat_loads):widget.setEnabled(thermal)
            for widget in (self.supports,self.loads,self.pressures,self.gravity,self.plastic_curve):widget.setEnabled(not thermal or widget.table.rowCount()>0)
            for column in (1,2):self.materials.table.setColumnHidden(column,thermal)
            self.nodal_history_label.setText('Temperature / heat flow histories' if thermal else 'U / RF / V histories' if kind in ('dynamic','modal-dynamics') else 'U / RF histories')
            self.element_history_label.setText('Heat flux histories' if thermal else 'Stress histories')
            self.nodal_history.setToolTip('Temperature / reaction heat flow' if thermal else 'Displacement / reaction force')
            self.element_history.setToolTip('Integration-point heat flux' if thermal else 'Stress')
            self.mark_changed()
        self.analysis_kind.currentIndexChanged.connect(update_kind)
        self.mode_count.valueChanged.connect(self.mark_changed);self.frequency_lower.textChanged.connect(self.mark_changed);self.frequency_upper.textChanged.connect(self.mark_changed);self.buckling_accuracy.valueChanged.connect(self.mark_changed)
        for index in range(self.tabs.count()):self.tabs.setTabToolTip(index,self.tabs.tabText(index))
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
        for rows in (self.mechanical_properties,self.plastic_curve,self.thermal_properties,self.thermal_tables,self.expansion_properties):
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
        if self.model_space.currentData() != 'ThreeD' or 'modelSpace' in value:
            value['modelSpace'] = self.model_space.currentData()
        if self.pyramid_conversion is not None:
            choice=self.pyramid_conversion.currentData()
            if choice is None: value.pop('pyramidConversion',None)
            else: value['pyramidConversion']=choice
        value['materials'], value['sections'] = self.materials.values(), self.sections.values()
        for section in value['sections']:
            if not section.get('thickness'):section.pop('thickness', None)
            if not section.get('offset'):section.pop('offset', None)
            if section.get('kind')=='solid' and 'kind' not in next((r for r in self.original['sections'] if r['name']==section['name']),{}):section.pop('kind',None)
        sections_by_name={r['name']:r for r in value['sections']}
        seen=set()
        for row in self.line_sections.values():
            if row['section'] not in sections_by_name or row['section'] in seen:raise ValueError('Use one line section row per existing section.')
            seen.add(row['section']);section=sections_by_name[row['section']]
            if section.get('kind') not in ('beam','truss'):raise ValueError('Line controls require beam/truss section kind.')
            section['dimensions']=[row['d0']] if section['kind']=='truss' else [row['d0'],row['d1']]
            if section['kind']=='beam':section['shape']=row['shape'];section['direction']=[float(row[f'n{i}']) for i in range(3)]
        discrete_seen=set()
        for row in self.discrete_sections.values():
            name=row['section']
            if name not in sections_by_name or name in discrete_seen or sections_by_name[name].get('kind') not in ('mass','spring','gap'):raise ValueError('Use one discrete row per existing mass/spring/gap section.')
            discrete_seen.add(name);section=sections_by_name[name]
            for key in ('mass','stiffness','clearance','tensileForce'):
                if row[key]:section[key]=row[key]
            for key in ('dof','secondDof'):
                if row[key] and int(row[key]):section[key]=int(row[key])
            if any(row[f'n{i}'] for i in range(3)):section['direction']=[float(row[f'n{i}']) for i in range(3)]
        for row in self.composite_layers.values():
            if row['section'] not in sections_by_name or sections_by_name[row['section']].get('kind')!='composite':raise ValueError('Layer must name a composite section.')
            sections_by_name[row['section']].setdefault('layers',[]).append({'material':row['material'],'thickness':row['thickness']})
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
            'displacements': [row[f'u{i}'] or None for i in range(3)], **({'rotations':[row[f'r{i}'] or None for i in range(3)]} if any(row[f'r{i}'] for i in range(3)) else {})} for row in self.supports.values()]
        value['step']['loads'] = [{'name': row['name'], 'nodeSet': row['nodeSet'],
            'forcePerNode': [row[f'f{i}'] for i in range(3)]} for row in self.loads.values()]
        moments=[{'name':r['name'],'nodeSet':r['nodeSet'],'momentPerNode':[r[f'm{i}'] for i in range(3)]} for r in self.moments.values()]
        if moments or 'moments' in value['step']:value['step']['moments']=moments
        for key, field in self.step_fields.items():
            text = field.text().strip()
            try:
                value['step'][key] = text if key == 'name' else int(text) if key in ('maximumIncrements', 'outputFrequency') else float(text)
            except ValueError:
                raise ValueError('Enter a valid number for ' + key)
        if self.element_output.currentText()!='Default' or 'elementOutput' in value['step']:value['step']['elementOutput']=self.element_output.currentText()
        kind=self.analysis_kind.currentData()
        if kind!='static' or 'kind' in value['step']:value['step']['kind']=kind
        if kind in ('frequency','buckling') or 'modes' in value['step']:value['step']['modes']=self.mode_count.value()
        if kind in ('dynamic','modal-dynamics'):
            value['step']['dynamics']={'alpha':float(self.dynamics_alpha.text()),'direct':self.dynamics_direct.isChecked(),'damping':self.dynamics_damping.currentText(),'massDamping':float(self.dynamics_mass.text()),'stiffnessDamping':float(self.dynamics_stiffness.text()),'modalDampingRatio':float(self.dynamics_ratio.text()),'basisModes':self.dynamics_modes.value(),'basisName':self.dynamics_basis.text().strip()}
        elif 'dynamics' in value['step']:value['step'].pop('dynamics')
        if kind=='heat-transfer':
            for material in value['materials']:
                for key in ('youngsModulus','poissonsRatio'):
                    if not material.get(key):material.pop(key,None)
            seen=set()
            for row in self.thermal_properties.values():
                name=row['material']
                if name not in by_name:
                    if not row['conductivity'] and not row['specificHeat']:continue
                    raise ValueError('Thermal properties refer to a missing material: '+name)
                if name in seen:raise ValueError('Use one thermal property row per material.')
                seen.add(name)
                for key in ('conductivity','specificHeat'):
                    if row[key]:by_name[name][key]=row[key]
            controls={'steadyState':self.thermal_steady.isChecked(),'direct':self.thermal_direct.isChecked()}
            if self.thermal_initial.text().strip():controls['initialTemperature']=self.thermal_initial.text().strip()
            if self.thermal_deltmx.text().strip():controls['maximumTemperatureChange']=float(self.thermal_deltmx.text())
            for key,field in [('absoluteZero',self.absolute_zero),('stefanBoltzmann',self.stefan_boltzmann)]:
                if field.text().strip():controls[key]=float(field.text())
            value['step']['thermal']=controls
            value['step']['temperatures']=self.temperatures.values()
            value['step']['heatLoads']=[{key:v for key,v in row.items() if key!='sinkTemperature' or v} for row in self.heat_loads.values()]
        for key,field in [('lowerFrequency' ,self.frequency_lower),('upperFrequency',self.frequency_upper)]:
            if field.text().strip():value['step'][key]=float(field.text())
            else:value['step'].pop(key,None)
        if kind=='buckling' or 'bucklingAccuracy' in value['step']:value['step']['bucklingAccuracy']=self.buckling_accuracy.value()
        for row in self.thermal_tables.values():
            if row['material'] not in by_name:raise ValueError('Thermal table refers to a missing material: '+row['material'])
            by_name[row['material']].setdefault(row['property']+'Table',[]).append([row['value'],row['temperature']])
        seen=set()
        for row in self.expansion_properties.values():
            name=row['material']
            if name not in by_name or name in seen:raise ValueError('Use one expansion row per existing material.')
            seen.add(name);by_name[name]['expansion']=row['coefficient'];by_name[name]['expansionZeroTemperature']=row['reference']
        if self.mechanical_initial.text().strip():value['step']['initialTemperature']=self.mechanical_initial.text().strip()
        else:value['step'].pop('initialTemperature',None)
        fields=self.temperature_fields.values()
        if fields or 'temperatureFields' in value['step']:value['step']['temperatureFields']=fields
        amplitudes={}
        for row in self.amplitude_definitions.values():
            name=row['name']
            if name in amplitudes:raise ValueError('Duplicate amplitude name.')
            amplitudes[name]={'name':name,'timeSpan':row['timeSpan'],'shiftX':float(row['shiftX'] or 0),'shiftY':float(row['shiftY'] or 0),'points':[]}
        for row in self.amplitude_points.values():
            if row['amplitude'] not in amplitudes:raise ValueError('Amplitude table refers to a missing amplitude.')
            amplitudes[row['amplitude']]['points'].append([float(row['time']),float(row['value'])])
        if amplitudes or 'amplitudes' in value:value['amplitudes']=list(amplitudes.values())
        seen=set()
        for row in self.amplitude_bindings.values():
            key=dict(self.binding_sources).get(row['kind'],'heatLoads');property_key='coefficientAmplitude' if row['kind']=='Coefficient / emissivity' else 'amplitude'
            targets=[v for v in value['step'].get(key) or [] if v['name']==row['name']]
            identity=(key,row['name'],property_key)
            if len(targets)!=1 or identity in seen:raise ValueError('Amplitude target must name one existing definition without duplicate bindings.')
            seen.add(identity);targets[0][property_key]=row['amplitude']
        for key, widget in [('nodalHistorySets', self.nodal_history), ('elementHistorySets', self.element_history)]:
            value['step'][key] = [widget.item(i).text() for i in range(widget.count())
                                  if widget.item(i).checkState() == QtCore.Qt.CheckState.Checked]
        return value

    def validate_current(self):
        try:
            value = self.collect()
            outcome = validate_definition(self.mesh_bytes, value)
            self.definition, self.validation = value, outcome
            self.message.setText('Valid analysis definition. Original model/deck checks passed; no solver was started.')
            return True
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            self.definition = self.validation = None
            self.message.setText(str(error))
            return False

    def apply(self):
        if self.validate_current():
            self.accept()

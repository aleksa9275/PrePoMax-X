"""Original FrmMain tool strips.

Layout rows, items, icons, tool tips, combo items and the main-menu handler each
button delegates to come from original_main_menu.json (generate-main-menu.py).
Buttons run the same mapped handler as the original menu item; the result
deformation, complex, step/increment, colour-by and symbol controls port the
FrmMain toolbar code (InitializeDeformationComboBoxes, UpdateScaleFactorTextBoxState,
UpdateComplexControlStates, SetAllStepAndIncrementIds, UpdateSymbolsList,
UpdateColorByComboBox, UpdateResultsTypeIconStates, SetMenuAndToolStripVisibility).
"""
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets
from System import Enum, Single
from PrePoMax import ViewGeometryModelResults

from main_menu import MENU, leaves

ROOT = Path(__file__).resolve().parents[2]
_ICONS = {}


def original_icon(path):
    """Original .ico file from PrePoMax/Icons (repository or packaged Icons folder)."""
    if not path:
        return QtGui.QIcon()
    if path not in _ICONS:
        relative = Path(path)
        candidates = [ROOT / relative, Path(__file__).with_name('Icons') / Path(*relative.parts[2:])]
        found = next((c for c in candidates if c.is_file()), None)
        _ICONS[path] = QtGui.QIcon(str(found)) if found else QtGui.QIcon()
    return _ICONS[path]


def displayed_name(kind, value):
    from CaeGlobals import ExtensionMethods
    return str(ExtensionMethods.GetDisplayedName[kind](value))


class OriginalToolbarsWorkbench:
    STEP_BUTTONS = {'tsbFirstStepIncrement_Click': 'first', 'tsbPreviousStepIncrement_Click': 'previous',
                    'tsbNextStepIncrement_Click': 'next', 'tsbLastStepIncrement_Click': 'last'}

    # ------------------------------------------------------------------ build
    def build_original_toolbars(self):
        data = MENU['toolstrips']
        self.original_menu_nodes = {n['handler']: n for top in MENU['menus'] for n in leaves(top) if n.get('handler')}
        # PrePoMax-X toolbars go below the original rows.
        existing = [t for t in self.findChildren(QtWidgets.QToolBar) if t.parent() is self]
        for bar in existing:
            if self.toolBarBreak(bar):
                self.removeToolBarBreak(bar)
            self.removeToolBar(bar)
        self.original_strips = {}
        self.original_tools = {}
        self.original_tool_items = {}
        for index, row in enumerate(data['rows']):
            if index:
                self.addToolBarBreak()
            for name in row:
                strip = data['strips'][name]
                bar = QtWidgets.QToolBar(strip['text'] or name, self)
                bar.setObjectName(name)
                bar.setIconSize(QtCore.QSize(16, 16))
                self.addToolBar(QtCore.Qt.ToolBarArea.TopToolBarArea, bar)
                self.original_strips[name] = bar
                for item in strip['items']:
                    self._add_original_tool(bar, item)
        self.addToolBarBreak()
        # X-only selection controls stay visible; superseded X toolbars stay as hidden backends.
        self.viewport_toolbar.setWindowTitle('PrePoMax-X selection')
        for bar in existing:
            self.addToolBar(QtCore.Qt.ToolBarArea.TopToolBarArea, bar)
            bar.setVisible(bar is self.viewport_toolbar)
        for widget in (self.view, self.element_edges):
            action = next((a for a in self.viewport_toolbar.actions() if self.viewport_toolbar.widgetForAction(a) is widget), None)
            if action is not None:
                action.setVisible(False)
        self.animation_requested = False
        self.selected_symbol_index = {}
        self._initialize_result_controls()
        self.update_original_toolbar_state()

    def _add_original_tool(self, bar, item):
        kind, key = item['kind'], item['id']
        self.original_tool_items[key] = item
        if kind == 'Separator':
            self.original_tools[key] = bar.addSeparator()
            return
        if kind == 'Button':
            action = QtGui.QAction(original_icon(item.get('image')), item.get('text', ''), self)
            action.setToolTip(item.get('toolTip', item.get('text', '')))
            action.triggered.connect(lambda checked=False, i=item: self.guard(lambda: self.run_original_tool(i, 'left')))
            bar.addAction(action)
            if item.get('right'):
                button = bar.widgetForAction(action)
                button.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
                button.customContextMenuRequested.connect(
                    lambda pos, i=item: self.guard(lambda: self.run_original_tool(i, 'right')))
            self.original_tools[key] = action
            return
        if kind == 'Label':
            widget = QtWidgets.QLabel(item.get('text', ''))
            widget.setContentsMargins(4, 0, 3, 0)
        elif kind == 'ComboBox':
            widget = self.symbols if key == 'tscbSymbols' else self.result_boxes['Result'] if key == 'tscbResultNames' \
                else QtWidgets.QComboBox()
            if key not in ('tscbSymbols', 'tscbResultNames'):
                widget.addItems(item.get('items', []))
        elif kind == 'TextBox':
            widget = QtWidgets.QLineEdit(item.get('text', ''))
            widget.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
            widget.setMaximumWidth(64)
        else:
            raise ValueError('Unhandled original tool strip item ' + key)
        if item.get('toolTip'):
            widget.setToolTip(item['toolTip'])
        self.original_tools[key] = bar.addWidget(widget)
        setattr(self, 'tool_' + key, widget)

    def _initialize_result_controls(self):
        """FrmMain.InitializeDeformationComboBoxes / InitializeComplexComboBoxes and the control events."""
        from CaeResults import FeResults, DeformationScaleFactorTypeEnum, ComplexResultTypeEnum
        self.deformation_types = {displayed_name(DeformationScaleFactorTypeEnum, v): v for v in Enum.GetValues(DeformationScaleFactorTypeEnum)}
        self.complex_types = {displayed_name(ComplexResultTypeEnum, v): v for v in Enum.GetValues(ComplexResultTypeEnum)}
        variable, kind, factor = self.tool_tscbDeformationVariable, self.tool_tscbDeformationType, self.tool_tstbDeformationFactor
        variable.addItems([str(n) for n in FeResults.GetPossibleDeformationFieldOutputNames()])
        kind.addItems(list(self.deformation_types))
        kind.setCurrentIndex(2)  # Automatic
        self.tool_tscbComplex.addItems(list(self.complex_types))
        variable.currentIndexChanged.connect(lambda *_: self.guard(self.apply_deformation_controls))
        kind.currentIndexChanged.connect(lambda *_: self.guard(self.deformation_type_changed))
        factor.returnPressed.connect(lambda: self.guard(self.apply_deformation_controls))
        self.tool_tscbComplex.currentIndexChanged.connect(lambda *_: self.guard(self.complex_type_changed))
        self.tool_tstbAngle.returnPressed.connect(lambda: self.guard(self.complex_angle_entered))
        self.tool_tscbStepAndIncrement.currentIndexChanged.connect(lambda *_: self.guard(self.step_and_increment_changed))
        self.tool_tscbColorBy.currentIndexChanged.connect(lambda *_: self.guard(self.color_by_changed))
        try:
            self.symbols.currentTextChanged.disconnect()
        except TypeError:
            pass
        self.symbols.currentIndexChanged.connect(lambda *_: self.guard(self.symbols_changed))
        self.update_scale_factor_state()

    # ---------------------------------------------------------------- running
    def run_original_tool(self, item, button):
        handler = item.get(button)
        if handler is None and button == 'left':
            handler = item.get('handler')
        if handler is None:
            return
        if handler in self.original_menu_nodes:
            return self.run_original_item(self.original_menu_nodes[handler])
        c = self.controller
        if handler == 'TurnSectionViewOnOff':
            c.TurnSectionViewOnOff()
        elif handler == 'TurnExplodedViewOnOff':
            c.TurnExplodedViewOnOff(True)
        elif handler in self.STEP_BUTTONS:
            return self.step_increment(self.STEP_BUTTONS[handler])
        elif handler == 'tsbAnimate_Click':
            return self.original_animate()
        else:
            raise ValueError('Unmapped original tool strip handler ' + handler)
        self.refresh()

    def step_increment(self, where):
        box = self.tool_tscbStepAndIncrement
        if not box.isEnabled() or box.count() == 0:
            return
        index = {'first': 0, 'last': box.count() - 1, 'previous': box.currentIndex() - 1,
                 'next': box.currentIndex() + 1}[where]
        if 0 <= index < box.count():
            box.setCurrentIndex(index)

    def original_animate(self):
        """tsbAnimate: the animation controls (FrmAnimation) open for a deformed result view with steps."""
        c = self.controller
        if str(c.ViewResultsType) != 'Undeformed' and len(list(c.GetResultStepIDs())) > 0 and not self.animation_requested:
            self.animation_requested = True
            self.animation_toolbar.setVisible(True)
            self.update_original_toolbar_state()

    def close_animation(self):
        self.stop_animation()
        self.animation_requested = False
        self.animation_toolbar.setVisible(False)
        self.update_original_toolbar_state()

    # ------------------------------------------------------- result controls
    def update_scale_factor_state(self):
        enabled = self.deformation_types.get(self.tool_tscbDeformationType.currentText()) is not None and \
            str(self.deformation_types[self.tool_tscbDeformationType.currentText()]) == 'UserDefined'
        self.tool_tslDeformationFactor.setEnabled(enabled)
        self.tool_tstbDeformationFactor.setEnabled(enabled)

    def deformation_type_changed(self):
        self.update_scale_factor_state()
        self.apply_deformation_controls()

    def apply_deformation_controls(self):
        if getattr(self, '_syncing_tools', False) or not self.controller.ResultsInitialized:
            return
        try:
            factor = float(self.tool_tstbDeformationFactor.text().replace(',', '.'))
        except ValueError:
            raise ValueError('Enter a valid deformation scale factor.')
        kind = self.deformation_types[self.tool_tscbDeformationType.currentText()]
        self.results.Deformation(self.tool_tscbDeformationVariable.currentText(), str(kind), Single(factor))
        self.refresh()

    def complex_type_changed(self):
        self.update_angle_state()
        self.apply_complex_controls()

    def update_angle_state(self):
        enabled = str(self.complex_types.get(self.tool_tscbComplex.currentText(), '')) == 'RealAtAngle'
        self.tool_tslAngle.setEnabled(enabled)
        self.tool_tstbAngle.setEnabled(enabled)

    def complex_angle_entered(self):
        from CaeGlobals import Tools
        text = self.tool_tstbAngle.text().replace('°', '').strip().replace(',', '.')
        try:
            angle = float(text or 0)
        except ValueError:
            raise ValueError('Enter a valid angle.')
        self.tool_tstbAngle.setText(f'{float(Tools.GetPhase360(angle)):g} °')
        self.apply_complex_controls()

    def apply_complex_controls(self):
        if getattr(self, '_syncing_tools', False) or not self.controller.ContainsComplexResults:
            return
        angle = float(self.tool_tstbAngle.text().replace('°', '').strip().replace(',', '.') or 0)
        self.results.Complex(str(self.complex_types[self.tool_tscbComplex.currentText()]), Single(angle))
        self.refresh()

    def step_and_increment_changed(self):
        if getattr(self, '_syncing_tools', False):
            return
        text = self.tool_tscbStepAndIncrement.currentText()
        if not text or not self.controller.ResultsInitialized:
            return
        step, increment = (int(v) for v in text.replace(' ', '').split(','))
        current = self.controller.CurrentFieldData
        self.stop_animation(False)
        self.results.Field(current.Name, current.Component, step, increment)
        self.refresh()

    def set_all_step_and_increment_ids(self):
        """FrmMain.SetAllStepAndIncrementIds / SetStepAndIncrementIds."""
        box = self.tool_tscbStepAndIncrement
        box.clear()
        result = self.controller.CurrentResult
        if result is None or not self.controller.ResultsInitialized:
            return
        ids = result.GetAllExistingIncrementIds()
        pairs = ids.items() if isinstance(ids, dict) else ((k, ids[k]) for k in ids.Keys)
        for step, increments in pairs:
            for increment in increments:
                box.addItem(f'{step}, {increment}')
        field = self.controller.CurrentFieldData
        if field is not None:
            box.setCurrentText(f'{field.StepId}, {field.StepIncrementId}')

    # ---------------------------------------------------- symbols / color by
    def symbols_changed(self):
        if getattr(self, '_syncing_tools', False) or self.symbols.currentIndex() < 0:
            return
        c = self.controller
        c.ClearAllSelection()
        c.DrawSymbols(self.symbols.currentText(), False)
        self.selected_symbol_index[str(c.CurrentView)] = self.symbols.currentIndex()
        self.refresh()

    def update_symbols_list(self):
        """FrmMain.UpdateSymbolsList; a symbol set drawn by a command selects its name."""
        from PrePoMax import Globals
        c = self.controller
        box = self.symbols
        box.clear()
        box.addItem(str(Globals.SymbolNone))
        view = c.CurrentView
        if view == ViewGeometryModelResults.Model:
            box.addItem(str(Globals.SymbolModel))
            box.addItems([str(n) for n in c.GetStepNames()])
        elif view == ViewGeometryModelResults.Results:
            box.addItem(str(Globals.SymbolResult))
        drawn = c.GetDrawSymbolsForStep()
        index = box.findText(str(drawn)) if drawn else -1
        if index < 0:
            index = min(self.selected_symbol_index.get(str(view), box.count() - 1), box.count() - 1)
            box.setCurrentIndex(index)
            c.SetSymbolsName(box.currentText())
        else:
            box.setCurrentIndex(index)

    def color_by_changed(self):
        if getattr(self, '_syncing_tools', False):
            return
        name = self.tool_tscbColorBy.currentText()
        node = next((n for n in leaves(next(m for m in MENU['menus'] if m['id'] == 'tsmiView'))
                     if n['id'][len('tsmiAnnotate'):] in self.EXCLUSIVE_ANNOTATIONS and n['text'] == name), None)
        if node is None:
            from PrePoMax import AnnotateWithColorEnum
            for key in self.EXCLUSIVE_ANNOTATIONS:
                self._annotation_action(key).setChecked(False)
            self.controller.AnnotateWithColor = getattr(AnnotateWithColorEnum, 'None')
            self.refresh()
            return
        action = self.original_actions[node['id']]
        if not action.isChecked():
            action.setChecked(True)
            self.annotate_with_color(node)

    def update_color_by(self):
        """FrmMain.UpdateColorByComboBox."""
        name = 'None'
        for key in self.EXCLUSIVE_ANNOTATIONS:
            action = self._annotation_action(key)
            if action is not None and action.isChecked():
                name = action.text()
                break
        self.tool_tscbColorBy.setCurrentText(name)

    # ------------------------------------------------------------ enabling
    def update_original_toolbar_state(self):
        """FrmMain.SetMenuAndToolStripVisibility (tool strip part), UpdateResultsTypeIconStates,
        UpdateComplexControlStates."""
        if not hasattr(self, 'original_tools'):
            return
        c = self.controller
        tools = self.original_tools
        self._syncing_tools = True
        try:
            initialized = bool(c.ModelInitialized or c.ResultsInitialized)
            tools['tsbImport'].setEnabled(bool(c.ModelInitialized))
            tools['tsbSave'].setEnabled(initialized)
            view = c.CurrentView
            empty = (view in (ViewGeometryModelResults.Geometry, ViewGeometryModelResults.Model) and not c.ModelInitialized) or \
                    (view == ViewGeometryModelResults.Results and not c.ResultsInitialized)
            results = view == ViewGeometryModelResults.Results and not empty
            for action in self.original_strips['tsViews'].actions():
                action.setEnabled(not empty)
            tools['tsbFollowerView'].setEnabled(results)
            for key in ('tslColorBy', 'tscbColorBy'):
                tools[key].setEnabled(not empty)
            for key in ('tslSymbols', 'tscbSymbols'):
                tools[key].setEnabled(not empty and view != ViewGeometryModelResults.Geometry)
            self.update_symbols_list()
            self.update_color_by()
            for name in ('tsResultDeformation', 'tsResults'):
                self.original_strips[name].setEnabled(results)
            # Button check states
            for key, active in (('tsbSectionView', c.IsSectionViewActive()), ('tsbExplodedView', c.IsExplodedViewActive()),
                                ('tsbFollowerView', c.IsFollowerViewActive()), ('tsbTransformation', c.AreTransformationsActive())):
                tools[key].setCheckable(True)
                tools[key].setChecked(bool(active))
            kind = str(c.ViewResultsType) if results else ''
            undeformed = str(c.GetUndeformedModelType()) if kind in ('ColorContours', 'VectorPlot', 'TensorPlot') else ''
            for key, checked in (('tsbResultsUndeformed', kind == 'Undeformed'), ('tsbResultsDeformed', kind == 'Deformed'),
                                 ('tsbResultsColorContours', kind == 'ColorContours'),
                                 ('tsbResultsVectorPlot', kind in ('VectorPlot', 'TensorPlot')),
                                 ('tsbResultsUndeformedWireframe', undeformed == 'WireframeBody'),
                                 ('tsbResultsUndeformedSolid', undeformed == 'SolidBody')):
                tools[key].setCheckable(True)
                tools[key].setChecked(checked)
            if results:
                self.set_all_step_and_increment_ids()
                presentation = self.session.Presentation
                self.tool_tscbDeformationVariable.setCurrentText(str(presentation.GetDeformationVariable()))
                deformation = presentation.GetDeformationType()
                from CaeResults import DeformationScaleFactorTypeEnum
                self.tool_tscbDeformationType.setCurrentText(displayed_name(DeformationScaleFactorTypeEnum, deformation))
                self.tool_tstbDeformationFactor.setText(f'{float(presentation.GetDeformationFactor()):g}')
                self.update_scale_factor_state()
            # UpdateComplexControlStates
            complex_results = bool(c.ResultsInitialized and c.ContainsComplexResults)
            for key in ('tslComplex', 'tscbComplex', 'tslAngle', 'tstbAngle'):
                tools[key].setVisible(complex_results)
            if complex_results:
                from CaeResults import ComplexResultTypeEnum
                self.tool_tscbComplex.setCurrentText(displayed_name(ComplexResultTypeEnum, c.CurrentResult.ComplexResultType))
                self.tool_tstbAngle.setText(f'{float(c.CurrentResult.ComplexAngleDeg):g} °')
                self.update_angle_state()
            self.animation_toolbar.setVisible(results and self.animation_requested)
            if not results:
                self.animation_requested = False
            tools['tsbAnimate'].setEnabled(not self.animation_requested)
        finally:
            self._syncing_tools = False

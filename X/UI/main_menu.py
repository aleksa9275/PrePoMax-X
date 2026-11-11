"""Original FrmMain main menu.

Structure, text, shortcuts and each item's original entity selection (title,
controller getter, one/many, step level, min/max, confirmation text) come from
original_main_menu.json, generated from FrmMain by generate-main-menu.py. This
module only maps each original handler to the live original Controller call or
to the existing Qt editor for the original form.
"""
import json
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets
from System import Array, String, Byte
from PrePoMax import ViewGeometryModelResults

MENU = json.loads(Path(__file__).with_name('original_main_menu.json').read_text(encoding='utf-8'))
HOME_PAGE = 'https://prepomax.fs.um.si/'


def enum_value(kind, value):
    from System import Enum
    return Enum.ToObject(kind, value)


def leaves(node):
    if node.get('separator'):
        return
    if 'children' in node:
        for child in node['children']:
            yield from leaves(child)
    else:
        yield node


class EntityDialog(QtWidgets.QDialog):
    """Port of FrmSelectEntity: one or multiple named items, min/max checks."""

    def __init__(self, parent, title, names, multiple, preselected, minimum=1, maximum=None):
        super().__init__(parent)
        self.title, self.multiple, self.minimum, self.maximum = title, multiple, minimum, maximum
        self.setWindowTitle(title + ' Selection')
        layout = QtWidgets.QVBoxLayout(self)
        box = QtWidgets.QGroupBox('Available ' + title.lower())
        inner = QtWidgets.QVBoxLayout(box)
        self.list = QtWidgets.QListWidget()
        self.list.addItems(names)
        self.list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection if multiple
                                   else QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        chosen = [n for n in preselected if n in names] or names[:1]
        for i in range(self.list.count()):
            self.list.item(i).setSelected(self.list.item(i).text() in chosen)
        self.list.itemDoubleClicked.connect(lambda *_: self.accept())
        inner.addWidget(self.list)
        layout.addWidget(box)
        layout.addWidget(QtWidgets.QLabel('Select one or multiple items' if multiple else 'Select one item'))
        buttons = QtWidgets.QDialogButtonBox()
        buttons.addButton('Continue', QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton('Cancel', QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def names(self):
        return [i.text() for i in self.list.selectedItems()]

    def accept(self):
        names = self.names()
        if not names:
            return
        if self.multiple and len(names) < self.minimum:
            QtWidgets.QMessageBox.critical(self, 'Error', f'Select at least {self.minimum} {self.title.lower()}.')
            return
        if self.multiple and self.maximum is not None and len(names) > self.maximum:
            QtWidgets.QMessageBox.critical(self, 'Error', f'Select at most {self.maximum} {self.title.lower()}.')
            return
        super().accept()


class MainMenuWorkbench:
    # Original Edit/Create forms → (Qt editor kind, family)
    FORMS = {
        'NodeSet': ('model', 'Node sets'), 'ElementSet': ('model', 'Element sets'), 'Surface': ('model', 'Surfaces'),
        'Material': ('model', 'Materials'), 'Section': ('model', 'Sections'), 'Constraint': ('model', 'Constraints'),
        'SurfaceInteraction': ('model', 'Surface interactions'), 'ContactPair': ('model', 'Contact pairs'),
        'Distribution': ('model', 'Distributions'), 'Amplitude': ('model', 'Amplitudes'),
        'InitialCondition': ('model', 'Initial conditions'), 'Step': ('model', 'Steps'),
        'StepControls': ('model', 'Solution controls'), 'HistoryOutput': ('model', 'History outputs'),
        'FieldOutput': ('model', 'Field outputs'), 'BoundaryCondition': ('model', 'Boundary conditions'),
        'Load': ('model', 'Loads'), 'DefinedField': ('model', 'Defined fields'),
        'Analysis': ('results', 'Jobs'), 'ResultFieldOutput': ('results', 'Result fields'),
        'ResultHistoryOutput': ('results', 'Result histories'), 'MeshSetupItem': ('geometry', 'Mesh setup'),
        'ElementQuality': ('geometry', 'Element quality'),
    }
    TRANSFORMS = {'Translate', 'Rotate', 'Mirror', 'Scale'}
    # Selection targets that are FrmMain members compiled with their original forms (C11).
    ORIGINAL_TARGETS = {'SetColorForGeometryParts', 'SetColorForModelParts', 'SetColorForResultParts',
                        'SetTransparencyForGeometryParts', 'SetTransparencyForModelParts', 'SetTransparencyForResultParts',
                        'FindEdgesByAngleForGeometryParts', 'FindEdgesByAngleForModelParts', 'AnalyzeGeometry',
                        'MonitorAnalysis', 'EditMaterial', 'EditSurfaceInteraction', 'EditStepControls', 'EditAnalysis'}
    # Original Create handlers without entity selection → family
    CREATE = {
        'tsmiCreateNodeSet_Click': 'Node sets', 'tsmiCreateElementSet_Click': 'Element sets',
        'tsmiCreateSurface_Click': 'Surfaces', 'tsmiCreateModelReferencePoint_Click': 'Reference points',
        'tsmiCreateModelCoordinateSystem_Click': 'Coordinate systems', 'tsmiCreateMaterial_Click': 'Materials',
        'tsmiCreateSection_Click': 'Sections', 'tsmiCreateConstraint_Click': 'Constraints',
        'tsmiCreateSurfaceInteraction_Click': 'Surface interactions', 'tsmiCreateContactPair_Click': 'Contact pairs',
        'tsmiCreateDistribution_Click': 'Distributions', 'tsmiCreateAmplitude_Click': 'Amplitudes',
        'tsmiCreateInitialCondition_Click': 'Initial conditions', 'tsmiCreateStep_Click': 'Steps',
    }
    # Original creates that return when there is no mesh (FrmMain checks Mesh == null)
    NEEDS_MESH = {'Node sets', 'Element sets', 'Surfaces', 'Reference points', 'Materials', 'Constraints',
                  'Surface interactions', 'Contact pairs', 'Steps'}

    # ------------------------------------------------------------------ build
    def build_original_menus(self):
        bar = self.menuBar()
        self.legacy_menus = [a.menu() for a in bar.actions() if a.menu() is not None]
        bar.clear()
        self.original_actions = {}
        self.original_top = {}
        self.unmapped_handlers = []
        for top in MENU['menus']:
            menu = bar.addMenu(top['text'])
            self.original_top[top['id']] = menu
            self._fill(menu, top.get('children', []))
        self._add_extras()
        self.geometry_menus = list(self.original_top.values())
        for menu in self.original_top.values():
            menu.aboutToShow.connect(self.update_original_menu_state)
        self.update_original_menu_state()

    def _fill(self, menu, nodes):
        for node in nodes:
            if node.get('separator'):
                menu.addSeparator()
                continue
            if node.get('visible') is False:
                continue
            if 'children' in node or node['id'] == 'tsmiOpenRecent':
                sub = menu.addMenu(node['text'])
                if node['id'] == 'tsmiOpenRecent':
                    # Filled at run time from the original recent-files setting.
                    self.original_recent = sub
                    sub.aboutToShow.connect(self.rebuild_original_recent)
                self._fill(sub, node.get('children', []))
                continue
            action = menu.addAction(node['text'])
            if node.get('image'):
                from main_toolbars import original_icon
                action.setIcon(original_icon(node['image']))
            self.original_actions[node['id']] = action
            if node.get('shortcut'):
                action.setShortcut(QtGui.QKeySequence(node['shortcut'].replace('Alt+F4', 'Alt+F4')))
            if node['id'].startswith(('tsmiAnnotate', 'tsmiView')) and node['id'] not in ('tsmiViewIds',):
                action.setCheckable(True)
            handler = node.get('handler')
            if handler is None or not self._handler(node):
                self.unmapped_handlers.append(node['id'])
                action.setEnabled(False)
                action.setToolTip('Not available in PrePoMax-X yet')
            action.triggered.connect(lambda checked=False, n=node: self.guard(lambda: self.run_original_item(n)))

    def _add_extras(self):
        """PrePoMax-X additions keep their existing actions, placed in the closest original menu."""
        view = self.original_top['tsmiView']
        view.addSeparator()
        extra = view.addMenu('PrePoMax-X')
        for title, callback in [('Parallel projection', lambda: self.projection(True)),
                                ('Perspective projection', lambda: self.projection(False)),
                                ('Disable follower view', lambda: self.controller.RemoveCurrentFollowerView()),
                                ('Edit annotation text…', self.edit_annotation),
                                ('Expand tree', self.tree.expandAll), ('Collapse tree', self.tree.collapseAll)]:
            extra.addAction(title).triggered.connect(lambda checked=False, cb=callback: self.guard(cb))
        output = next((d for d in self.findChildren(QtWidgets.QDockWidget) if d.windowTitle() == 'Output'), None)
        if output is not None:
            extra.addAction(output.toggleViewAction())
        edit = self.original_top['tsmiEdit']
        edit.addSeparator()
        for title in ['Select by IDs…', 'Clear selection']:
            if title in self.application_actions:
                edit.addAction(self.application_actions[title])
        tools = self.original_top['tsmiTools']
        tools.addSeparator()
        for title in ['Run Python file…', 'Import materials…', 'Check model']:
            if title in self.application_actions:
                tools.addAction(self.application_actions[title])
        automation = getattr(self, 'automation_menu', None)
        if automation is not None:
            tools.addMenu(automation)
        results = self.original_top['tsmiResults']
        results.addSeparator()
        for title, callback in [('Open results file…', self.open_result_file), ('Units…', self.set_result_units),
                                ('View history data…', self.history_data), ('Deformation…', self.deformation_dialog),
                                ('Complex results…', self.complex_dialog), ('Export animation…', self.export_animation_dialog)]:
            results.addAction(title).triggered.connect(lambda checked=False, cb=callback: self.guard(cb))
        for family in ['Legend', 'Postprocessing', 'Annotations', 'Status block', 'Number format']:
            results.addAction(family + '…').triggered.connect(
                lambda checked=False, f=family: self.guard(lambda: self.presentation_dialog(f)))

    def rebuild_original_recent(self):
        self.rebuild_recent()
        self.original_recent.clear()
        for action in self.recent_menu.actions():
            self.original_recent.addAction(action)

    # ------------------------------------------------------- per-view enabling
    def update_original_menu_state(self):
        """FrmMain.SetMenuAndToolStripVisibility, top-level part."""
        c = self.controller
        top = self.original_top
        for menu in top.values():
            menu.setEnabled(False)
        for key in ['tsmiFile', 'tsmiResults', 'tsmiTools', 'tsmiHelp']:
            top[key].setEnabled(True)
        initialized = c.ModelInitialized or c.ResultsInitialized
        for node in MENU['menus'][0]['children']:
            action = self.original_actions.get(node['id'])
            if action is not None and node['id'] not in self.unmapped_handlers:
                action.setEnabled(initialized or node['id'] in ('tsmiNew', 'tsmiOpen', 'tsmiRunHistoryFile', 'tsmiExit'))
        if 'tsmiImportFile' in self.original_actions:
            self.original_actions['tsmiImportFile'].setEnabled(bool(c.ModelInitialized))
        if initialized:
            top['tsmiEdit'].setEnabled(True)
        # Tools items: enabled only for an initialized model/result. Original 3.0.0 never
        # re-enables Arrange/Remove Annotations after disabling them (recorded original bug).
        for key in ['tsmiQuery', 'tsmiFind', 'tsmiCaptureViewport', 'tsmiCaptureViewportAs']:
            self._enable(key, initialized)
        self.original_parameters_menu().setEnabled(bool(initialized))
        for key in ['tsmiArrangeAnnotations', 'tsmiRemoveAnnotations', 'tsmiFollowerView']:
            self._enable(key, False)
        for node in leaves(next(m for m in MENU['menus'] if m['id'] == 'tsmiResults')):
            self._enable(node['id'], False)
        view = c.CurrentView
        empty = (view in (ViewGeometryModelResults.Geometry, ViewGeometryModelResults.Model) and not c.ModelInitialized) or \
                (view == ViewGeometryModelResults.Results and not c.ResultsInitialized)
        if empty:
            self.update_original_toolbar_state()
            return
        if view == ViewGeometryModelResults.Geometry:
            enabled = ['tsmiView', 'tsmiGeometry', 'tsmiMesh']
        elif view == ViewGeometryModelResults.Model:
            enabled = ['tsmiView', 'tsmiModel', 'tsmiProperty', 'tsmiInteraction', 'tsmiInitialCondition',
                       'tsmiDistribution', 'tsmiAmplitude', 'tsmiStepMenu', 'tsmiAnalysis']
        else:
            enabled = ['tsmiView']
            self._enable('tsmiFollowerView', True)
            for node in leaves(next(m for m in MENU['menus'] if m['id'] == 'tsmiResults')):
                self._enable(node['id'], True)
        for key in enabled:
            if key in top:
                top[key].setEnabled(True)
        self.update_original_toolbar_state()

    def _enable(self, key, value):
        action = self.original_actions.get(key)
        if action is not None and key not in self.unmapped_handlers:
            action.setEnabled(bool(value))

    def original_parameters_menu(self):
        return next(a.menu() for a in self.original_top['tsmiTools'].actions() if a.menu() is not None and a.text() == 'Parameters')

    # ---------------------------------------------------------------- running
    def _handler(self, node):
        handler = node.get('handler')
        if handler in self.CREATE or handler in self.custom_handlers():
            return True
        select = node.get('select')
        if select is None:
            return False
        action = (select.get('inStep') or select).get('action') or {}
        target = (select.get('inStep') or select)['target']
        return bool(action) or target in self.custom_targets() or target in self.ORIGINAL_TARGETS

    def run_original_item(self, node):
        handler = node['handler']
        if handler in self.CREATE:
            family = self.CREATE[handler]
            if family in self.NEEDS_MESH and self.controller.Model.Mesh is None:
                return
            self.ensure_view(ViewGeometryModelResults.Model)
            return self.edit_definition(family, None, None)
        custom = self.custom_handlers().get(handler)
        if custom is not None:
            return custom(node)
        select = node['select']
        if 'inStep' in select:
            step = self.choose(select)
            if step is None:
                return
            inner = select['inStep']
            names = self.choose(inner, step)
            if names is None:
                return
            return self.apply_target(inner, names, step)
        if select['target'] in ('CreateHistoryOutput', 'CreateFieldOutput', 'CreateBoundaryCondition', 'CreateLoad',
                                'CreateDefinedField'):
            step = self.choose(select)
            if step is not None:
                family = {'CreateHistoryOutput': 'History outputs', 'CreateFieldOutput': 'Field outputs',
                          'CreateBoundaryCondition': 'Boundary conditions', 'CreateLoad': 'Loads',
                          'CreateDefinedField': 'Defined fields'}[select['target']]
                self.edit_definition(family, step, None)
            return
        names = self.choose(select)
        if names is not None:
            self.apply_target(select, names, None)

    def entity_names(self, select, step=None):
        getter = select['getter']
        generic = None
        if '<' in getter:
            getter, generic = getter[:-1].split('<')
        method = getattr(self.controller, getter)
        if generic:
            import CaeMesh
            method = method[getattr(CaeMesh, generic)]
        items = method(step) if step is not None and select.get('arguments') else method()
        return [] if items is None else [str(i.Name) for i in items]

    def choose(self, select, step=None):
        """SelectOneEntity / SelectMultipleEntities (and InStep variants)."""
        names = self.entity_names(select, step)
        multiple = select['mode'] == 'many'
        if not names or len(names) < select.get('minimum', 1):
            return None
        if len(names) == 1:
            if multiple and select.get('minimum', 1) != 1:
                return None
            return names if multiple else names[0]
        selected = [i.data(0, QtCore.Qt.ItemDataRole.UserRole) for i in self.tree.selectedItems()]
        preselected = [str(e.Name) for e in selected if e is not None and not e.Group]
        dialog = EntityDialog(self, select['title'], names, multiple, preselected, select.get('minimum', 1),
                              select.get('maximum'))
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return None
        chosen = dialog.names()
        return chosen if multiple else chosen[0]

    def confirm(self, text, names, step=None):
        message = text + (step + '?' if step is not None and text.endswith('step ') else '')
        if isinstance(names, (list, tuple)):
            message += '\n' + '\n'.join(names)
        result = QtWidgets.QMessageBox.warning(self, 'Warning', message, QtWidgets.QMessageBox.StandardButton.Ok |
                                               QtWidgets.QMessageBox.StandardButton.Cancel)
        return result == QtWidgets.QMessageBox.StandardButton.Ok

    def ensure_view(self, view):
        if self.controller.CurrentView != view:
            self.view.setCurrentText(str(view))

    def select_tree(self, family, names):
        wanted = set(names)
        self.tree.clearSelection()
        for item in self.walk_tree():
            entry = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if entry is not None and not entry.Group and entry.Family == family and str(entry.Name) in wanted:
                item.setSelected(True)

    def apply_target(self, select, names, step):
        target = select['target']
        custom = self.custom_targets().get(target)
        if custom is not None:
            custom(names, step)
            return self.refresh()
        action = select.get('action') or {}
        if 'form' in action:
            return self.open_original_form(action['form']['form'], target, names, step)
        many = isinstance(names, list)
        if 'confirm' in action and not target.startswith('Propagate'):
            if not self.confirm(action['confirm'], names if many else [names], step):
                return
        calls = [c for c in action.get('calls', []) if c.endswith('Command') or c.startswith(('Preview', 'CopyGeometry'))]
        if target.startswith('Propagate'):
            return self.propagate(select, step, names)
        if target.startswith('ShowOnly'):
            hide, show = [c for c in calls if c.startswith('Hide')][0], [c for c in calls if c.startswith('Show')][0]
            everyone = self.entity_names(select, step)
            others = [n for n in everyone if n not in names]
            if others:
                getattr(self.controller, hide)(Array[String](others))
            getattr(self.controller, show)(Array[String](names))
            return self.refresh()
        if target in self.ORIGINAL_TARGETS:
            # The original FrmMain member (FrmGetColor/FrmGetValue/FrmAnalyzeGeometry/FrmMonitor ...).
            if isinstance(names, list):
                return self.run_original_entry(target, step=step, parts=names)
            return self.run_original_entry(target, step=step, name=names)
        if target.startswith('SetColorFor'):
            from System.Drawing import Color
            color = QtWidgets.QColorDialog.getColor(parent=self)
            if color.isValid():
                getattr(self.controller, calls[0])(Array[String](names), Color.FromArgb(color.red(), color.green(), color.blue()))
            return self.refresh()
        if target.startswith('SetTransparencyFor'):
            value, ok = QtWidgets.QInputDialog.getInt(self, 'Transparency', 'Opacity (0 transparent, 255 opaque)', 255, 0, 255)
            if ok:
                getattr(self.controller, calls[0])(Array[String](names), Byte(value))
            return self.refresh()
        if target in ('MergeModelParts', 'MergeResultParts'):
            check = 'AreModelPartsMergeable' if target == 'MergeModelParts' else 'AreResultPartsMergeable'
            if not getattr(self.controller, check)(Array[String](names)):
                raise ValueError('Selected parts are of a different type and thus cannot be merged.')
            if not self.confirm(action['confirm'], names):
                return
        if not calls:
            raise ValueError('No original command for ' + target)
        command = getattr(self.controller, calls[-1])
        argument = Array[String](names) if many else names
        if step is not None:
            command(step, argument)
        else:
            command(argument)
        self.refresh()

    def propagate(self, select, step, name):
        family = {'PropagateBoundaryCondition': 'BoundaryConditions', 'PropagateLoad': 'Loads',
                  'PropagateDefinedField': 'DefinedFields', 'PropagateHistoryOutput': 'HistoryOutputs',
                  'PropagateFieldOutput': 'FieldOutputs'}[select['target']]
        steps = self.controller.Model.StepCollection
        exists = any(getattr(steps.GetStep(n), family).ContainsKey(name) for n in steps.GetNextStepNames(step))
        if exists and not self.confirm(select['action']['confirm'] + name + '?', None):
            return
        getattr(self.controller, select['target'] + 'Command')(step, name)
        self.refresh()

    def open_original_form(self, form, target, names, step):
        name = names[0] if isinstance(names, list) else names
        if form == 'PartProperties':
            family = 'Geometry parts' if 'Geometry' in target else 'Result parts' if 'Result' in target else 'Parts'
            if family == 'Result parts':
                return self.edit_geometry('Parts', name)
            return self.edit_geometry(family, name)
        if form in self.TRANSFORMS:
            family = 'Geometry parts' if 'Geometry' in target else 'Parts'
            self.ensure_view(ViewGeometryModelResults.Geometry if family == 'Geometry parts' else ViewGeometryModelResults.Model)
            self.select_tree(family, names if isinstance(names, list) else [names])
            return self.edit_geometry(form)
        if form in ('ReferencePoint', 'CoordinateSystem'):
            if 'Result' in target:
                return self.edit_results('Result reference points' if form == 'ReferencePoint' else 'Result coordinate systems', name)
            return self.edit_definition('Reference points' if form == 'ReferencePoint' else 'Coordinate systems', None, name)
        kind, family = self.FORMS[form]
        if kind == 'results':
            return self.edit_results(family, name)
        if kind == 'geometry':
            if family == 'Element quality':
                self.ensure_view(ViewGeometryModelResults.Model)
                self.select_tree('Parts', names if isinstance(names, list) else [names])
                return self.edit_geometry(family)
            return self.edit_geometry(family, name)
        self.ensure_view(ViewGeometryModelResults.Model)
        if family == 'Solution controls':
            return self.edit_definition(family, name, None)
        if family == 'Steps':
            return self.edit_definition(family, None, name)
        return self.edit_definition(family, step, name if step is not None or family not in self.authoring.StepFamilies else None)

    # ------------------------------------------------- handlers without selection
    def custom_handlers(self):
        c = self.controller
        r = lambda handler: (lambda node: handler())
        views = {
            'tsmiFrontView_Click': lambda: self.original_view('front', True), 'tsmiBackView_Click': lambda: self.original_view('front', False),
            'tsmiTopView_Click': lambda: self.original_view('top', True), 'tsmiBottomView_Click': lambda: self.original_view('top', False),
            'tsmiLeftView_Click': lambda: self.original_view('left', True), 'tsmiRightView_Click': lambda: self.original_view('left', False),
            'tsmiIsometricView_Click': lambda: self.original_isometric(), 'tsmiNormalView_Click': self.original_normal_view,
            'tsmiVerticalView_Click': self.original_vertical_view,
        }
        handlers = {k: r(v) for k, v in views.items()}
        handlers.update({
            'tsmiNew_Click': r(self.new_project), 'tsmiOpen_Click': r(self.choose_open),
            'tsmiRunHistoryFile_Click': r(self.open_history), 'tsmiImportFile_Click': r(self.import_any),
            'tsmiSave_Click': r(self.save), 'tsmiSaveAs_Click': r(self.save_as),
            'tsmiExportModel_Click': r(self.export_original_model),
            'tsmiExportResultFieldOutput_Click': r(self.export_field),
            'tsmiExportResultHistoryOutput_Click': r(lambda: self.run_original_entry('tsmiExportResultHistoryOutput_Click')),
            'tsmiExportTo3mf_Click': r(lambda: (self.update_export_view(), self.run_original_entry('tsmiExportTo3mf_Click'))), 'tsmiExportToPythonJournal_Click': r(self.export_journal),
            'tsmiCloseCurrentResult_Click': r(self.close_current_result), 'tsmiCloseAllResults_Click': r(self.close_results),
            'tsmiExit_Click': r(self.close),
            'tsmiUndo_Click': r(self.undo), 'tsmiRedo_Click': r(self.redo),
            'tsmiEditHistory_Click': r(lambda: self.run_original_entry('tsmiEditHistory_Click')),
            'tsmiRegenerateHistory_Click': r(lambda: self.regenerate_original(False, False)),
            'tsmiRegenerateHistoryUsingOtherFiles_Click': r(lambda: self.regenerate_original(True, False)),
            'tsmiRegenerateHistoryWithRemeshing_Click': r(lambda: self.regenerate_original(False, True)),
            'tsmiPythonScriptEditor_Click': r(lambda: self.toggle_dock(self.script_dock)),
            'tsmiXYPlotPanel_Click': r(lambda: self.toggle_dock(self.plot_dock)),
            'tsmiAdvisor_Click': r(lambda: self.toggle_dock(self.advisor_dock)),
            'tsmiEditUserViews_Click': r(lambda: self.run_original_entry('tsmiEditUserViews_Click')),
            'tsmiZoomToFit_Click': r(self.fit), 'tsmiBoxZoom_Click': r(self.start_box_zoom),
            'tsmiShowWireframeEdges_Click': r(lambda: self.set_edge_mode('Wireframe')),
            'tsmiShowElementEdges_Click': r(lambda: self.set_edge_mode('Element edges')),
            'tsmiShowModelEdges_Click': r(lambda: self.set_edge_mode('Model edges')),
            'tsmiShowNoEdges_Click': r(lambda: self.set_edge_mode('No edges')),
            'tsmiSectionView_Click': r(lambda: self.run_original_entry('tsmiSectionView_Click')),
            'tsmiExplodedView_Click': r(lambda: self.run_original_entry('tsmiExplodedView_Click')),
            'tsmiFollowerView_Click': r(lambda: self.run_original_entry('tsmiFollowerView_Click')),
            'tsmiShowAllParts_Click': r(lambda: self.visible_parts('Show')),
            'tsmiHideAllParts_Click': r(lambda: self.visible_parts('Hide')),
            'tsmiInvertVisibleParts_Click': r(lambda: self.visible_parts('Invert')),
            'tsmiResultsUndeformed_Click': r(lambda: self.results_view('Undeformed', 'None')),
            'tsmiResultsDeformed_Click': r(lambda: self.results_view('Deformed', 'None')),
            'tsmiResultsColorContours_Click': r(lambda: self.results_view('ColorContours', None)),
            'tsmiResultsVectorPlot_Click': r(lambda: self.results_view('VectorPlot', None)),
            'tsmiResultsUndeformedWireframe_Click': r(lambda: self.toggle_undeformed('WireframeBody')),
            'tsmiResultsUndeformedSolid_Click': r(lambda: self.toggle_undeformed('SolidBody')),
            'tsmiAnnotateAllSymbols_Click': self.annotate_all,
            'tsmiCreateMeshSetupItem_Click': r(lambda: self.edit_geometry('Mesh setup')),
            'tsmiEditModel_Click': r(self.edit_model),
            'tsmiEditCalculiXKeywords_Click': r(lambda: self.run_original_entry('tsmiEditCalculiXKeywords_Click')),
            'tsmiCreateBoundaryLayer_Click': r(lambda: self.model_tool('Boundary layer')),
            'tsmiRemeshElements_Click': r(lambda: self.model_tool('Remesh elements')),
            'tsmiThickenShellMesh_Click': r(lambda: self.model_tool('Thicken shell mesh')),
            'tsmiSplitPartMeshUsingSurface_Click': r(lambda: self.model_tool('Split mesh using surface')),
            'tsmiMergeCoincidentNodes_Click': r(lambda: self.model_tool('Merge coincident nodes')),
            'tsmiUpdateNodalCoordinatesFromFile_Click': r(self.update_coordinates),
            'tsmiRenumberAllNodes_Click': r(lambda: self.run_original_entry('tsmiRenumberAllNodes_Click')),
            'tsmiRenumberAllElements_Click': r(lambda: self.run_original_entry('tsmiRenumberAllElements_Click')),
            'tsmiSplitShell_Click': r(lambda: self.geometry_tool('Split shell')),
            'tsmiSplitSolid_Click': r(lambda: self.geometry_tool('Split solid')),
            'tsmiSplitPeriodicFaces_Click': r(lambda: self.geometry_tool('Split periodic faces')),
            'tsmiFuseFaces_Click': r(lambda: self.geometry_tool('FuseFaces')),
            'tsmiOffsetFace_Click': r(lambda: self.geometry_tool('Offset faces')),
            'tsmiDeleteFacesCAD_Click': r(lambda: self.geometry_tool('DeleteCadFaces')),
            'tsmiDefeature_Click': r(lambda: self.geometry_tool('Defeature')),
            'tsmiRepairGeometry_Click': r(lambda: self.geometry_tool('Repair geometry')),
            'tsmiFlipFaceNormalCAD_Click': r(lambda: self.geometry_tool('FlipNormal')),
            'tsmiDeleteStlPartFaces_Click': r(lambda: self.geometry_tool('DeleteStlFaces')),
            'tsmiMaterialLibrary_Click': r(lambda: self.run_original_entry('tsmiMaterialLibrary_Click')),
            'tsmiImportMaterial_Click': r(self.import_materials),
            'tsmiSearchContactPairs_Click': r(lambda: self.run_original_entry('tsmiSearchContactPairs_Click')),
            'tsmiCreateAnalysis_Click': r(lambda: self.run_original_entry('tsmiCreateAnalysis_Click')),
            'tsmiCreateResultReferencePoint_Click': r(lambda: self.edit_results('Result reference points')),
            'tsmiCreateResultCoordinateSystem_Click': r(lambda: self.edit_results('Result coordinate systems')),
            'tsmiCreateResultFieldOutput_Click': r(lambda: self.edit_results('Result fields')),
            'tsmiCreateResultHistoryOutput_Click': r(lambda: self.edit_results('Result histories')),
            'tsmiTransformation_Click': r(lambda: self.run_original_entry('tsmiTransformation_Click')),
            'tsmiAppendResults_Click': r(lambda: self.open_result_file(True)),
            'tsmiSettings_Click': r(lambda: self.run_original_entry('tsmiSettings_Click')),
            'tsmiEditParameters_Click': r(lambda: self.run_original_entry('tsmiEditParameters_Click')),
            'tsmiExportParameters_Click': r(lambda: self.parameters_file(False)),
            'tsmiImportParameters_Click': r(lambda: self.parameters_file(True)),
            'tsmiQuery_Click': r(lambda: self.run_original_entry('tsmiQuery_Click')), 'tsmiFind_Click': r(lambda: self.run_original_entry('tsmiFind_Click')),
            'tsmiArrangeAnnotations_Click': r(self.arrange_annotations),
            'tsmiRemoveAnnotations_Click': r(self.remove_annotations),
            'tsmiCaptureViewport_Click': r(self.capture_now),
            'tsmiCaptureViewportAs_Click': r(lambda: self.run_original_entry('tsmiCaptureViewportAs_Click')),
            'tsmiConvertOdbToFrd_Click': r(self.convert_odb),
            'tsmiBidirectionalMeshConverter_Click': r(self.bidirectional_mesh_converter),
            'tsmiAutomationServer_Click': r(self.toggle_automation),
            'tsmiHomePage_Click': r(lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl(HOME_PAGE))),
            'tsmiAbout_Click': r(lambda: self.run_original_entry('tsmiAbout_Click')),
        })
        for key in ['FaceOrientations', 'MeshTypes', 'Parts', 'Materials', 'Sections', 'SectionThicknesses',
                    'ReferencePoints', 'Constraints', 'ContactPairs', 'InitialConditions', 'BCs', 'Loads']:
            handlers['tsmiAnnotate' + key + '_Click'] = self.annotate_with_color
        for key in ['VertexIds', 'EdgeIds', 'SurfaceIds', 'PartIds', 'PartNames', 'NodeIds', 'ElementIds']:
            handlers['tsmiView' + key + '_Click'] = self.item_ids
        return handlers

    def custom_targets(self):
        c = self.controller
        return {
            'ExportGeometryParts': lambda names, step: self.export_original('Geometry', names),
            'ExportMeshParts': lambda names, step: self.export_original('Mesh', names),
            'ExportResultParts': lambda names, step: self.export_original('Results', names),
            'ExportMaterials': lambda names, step: self.export_materials(names),
            'CopyGeometryPartsToResults': lambda names, step: c.CopyGeometryPartsToResults(Array[String](names)),
            'SmoothGeometryPart': lambda name, step: c.SmoothGeometryPart(name),
            'CropGeometryPartWithCylinder': lambda name, step: c.CropGeometryPartWithCylinder(name),
            'CropGeometryPartWithCube': lambda name, step: c.CropGeometryPartWithCube(name),
            'GroupSplitCells': lambda names, step: self.compound_operation('Group split cells'),
            'FuseBodies': lambda names, step: self.compound_operation('Fuse bodies'),
            'PreviewEdgeMesh': lambda names, step: self.run_operation(self.geometry.Execute('Preview edge mesh', Array[String](names))),
            'CreatePartMeshes': lambda names, step: self.execute_geometry('Create mesh', Array[String](names)),
            'SwapPartGeometries': lambda names, step: c.SwapPartGeometriesCommand(names[0], names[1]),
            'CreateAndImportCompoundPart': lambda names, step: self.run_operation(self.geometry.Execute('Create compound', Array[String](names))),
            'RunAnalysis': lambda name, step: self.run_job(False, name=name),
            'CheckModel': lambda name, step: self.run_job(True, name=name),
            'ResultsAnalysis': lambda name, step: self.open_job(name),
            'KillAnalysis': lambda name, step: self.confirm('OK to kill selected analysis?', [name]) and c.KillJob(name),
            'ResultRepresentationOffResultPart': lambda names, step: c.SetResultRepresentationForResultPartsCommand(Array[String](names), False),
            'ResultRepresentationOnResultPart': lambda names, step: c.SetResultRepresentationForResultPartsCommand(Array[String](names), True),
            'PreviewInitialCondition': lambda name, step: self.preview(lambda: c.PreviewInitialCondition(name)),
            'PreviewBoundaryCondition': lambda name, step: self.preview(lambda: c.PreviewBoundaryCondition(step, name)),
            'PreviewLoad': lambda name, step: self.preview(lambda: c.PreviewLoad(step, name)),
            'PreviewDefinedField': lambda name, step: self.preview(lambda: c.PreviewDefinedField(step, name)),
        }

    # ------------------------------------------------------------ operations
    def toggle_dock(self, dock):
        dock.setVisible(not dock.isVisible())

    def import_any(self):
        from PrePoMax import ViewGeometryModelResults as V
        if not self.controller.ModelInitialized:
            raise ValueError('There is no model to import into. First create a new model.')
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Import', '', 'All supported (*.brep *.step *.stp *.iges *.igs *.stl *.inp *.unv *.vol *.mesh *.obj);;'
                                                        'Geometry (*.brep *.step *.stp *.iges *.igs *.stl);;Mesh (*.inp *.unv *.vol *.mesh *.obj)')
        if path:
            self.import_path(path, Path(path).suffix.lower() in ('.brep', '.step', '.stp', '.iges', '.igs', '.stl'))

    def export_original_model(self):
        path, chosen = QtWidgets.QFileDialog.getSaveFileName(self, 'Export model', '', 'Calculix files (*.inp);;Abaqus files (*.inp)')
        if path:
            self.application.Export(path, chosen.startswith('Abaqus'))

    def export_original(self, kind, names):
        from FileInOut.Output import ExportFormatTools, GeometryExportFormatEnum as G, MeshExportFormatEnum as M, ResultsExportFormatEnum as R
        table = {
            'Geometry': ([('STEP parts (*.stp)', G.Step), ('STEP assembly (*.stp)', G.StepAssembly), ('BREP parts (*.brep)', G.Brep),
                          ('BREP assembly (*.brep)', G.BrepAssembly), ('Stereolithography files (*.stl)', G.Stl), ('Mmg files (*.mesh)', G.Mmg)],
                         ExportFormatTools.GetGeometryFormat, self.controller.ExportGeometryPartsCommand),
            'Mesh': ([('CalculiX files (*.inp)', M.Calculix), ('Abaqus files (*.inp)', M.Abaqus), ('Gmsh mesh files (*.msh)', M.Gmsh),
                      ('Mmg files (*.mesh)', M.Mmg), ('Stereolithography files (*.stl)', M.Stl)],
                     ExportFormatTools.GetMeshFormat, self.controller.ExportMeshPartsCommand),
            'Results': ([('CalculiX files (*.inp)', R.Calculix), ('Stereolithography files (*.stl)', R.Stl)],
                        ExportFormatTools.GetResultsFormat, self.controller.ExportResultPartsCommand),
        }
        filters, resolve, command = table[kind]
        path, chosen = QtWidgets.QFileDialog.getSaveFileName(self, 'Export', '', ';;'.join(f for f, _ in filters))
        if not path:
            return
        index = next((i for i, (f, _) in enumerate(filters) if f == chosen), 0)
        fmt = resolve(path, filters[index][1])
        self.run_operation(__import__('System').Threading.Tasks.Task.Run(
            __import__('System').Action(lambda: command(Array[String](names), path, fmt))))

    def export_materials(self, names):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Export materials', '', 'Calculix files (*.inp)')
        if path:
            self.controller.ExportMaterials(Array[String](names), path)

    def close_current_result(self):
        if self.controller.AllResults.Count <= 1:
            return self.close_results()
        self.controller.RemoveCurrentResultsCommand()
        self.refresh()

    def regenerate_original(self, other_files, remeshing):
        # FrmMain.TryGetRegenerateType: the original FrmRegenerate when the history uses regeneration types.
        scope = self.in_ui_context(lambda: self.form_host.SelectRegenerateType(self.controller.IsRegenerateTypeUsed()))
        self.form_renderer.flush()
        if scope is None:
            return
        self.run_operation(self.application.Regenerate(other_files, remeshing, str(scope)))

    def results_view(self, view, undeformed):
        from CaeResults import UndeformedModelTypeEnum
        c = self.controller
        c.SetUndeformedModelType(getattr(UndeformedModelTypeEnum, undeformed) if undeformed else c.GetUndeformedModelType())  # 'None' via getattr
        if c.CurrentView == ViewGeometryModelResults.Results:
            self.result_boxes['View'].setCurrentText(view)
        self.refresh()

    def toggle_undeformed(self, kind):
        from CaeResults import UndeformedModelTypeEnum
        c = self.controller
        current = str(c.ViewResultsType)
        if current not in ('ColorContours', 'VectorPlot', 'TensorPlot'):
            return
        chosen = getattr(UndeformedModelTypeEnum, kind)
        if c.GetUndeformedModelType() == chosen:
            chosen = getattr(UndeformedModelTypeEnum, 'None')
        c.SetUndeformedModelType(chosen)
        self.results.Representation(current)
        self.refresh()

    EXCLUSIVE_ANNOTATIONS = ['FaceOrientations', 'MeshTypes', 'Parts', 'Materials', 'Sections', 'SectionThicknesses']
    SYMBOL_ANNOTATIONS = {'ReferencePoints': 'ReferencePoints', 'Constraints': 'Constraints', 'ContactPairs': 'ContactPairs',
                          'InitialConditions': 'InitialConditions', 'BCs': 'BoundaryConditions', 'Loads': 'Loads',
                          'DefinedFields': 'DefinedFields'}

    def _annotation_action(self, key):
        return self.original_actions.get('tsmiAnnotate' + key)

    def annotate_with_color(self, node):
        """FrmMain.ChangeAnnotationStatus: exclusive colorings, combinable symbols."""
        key = node['id'][len('tsmiAnnotate'):]
        action = self.original_actions[node['id']]  # Qt already toggled the check state
        if action.isChecked():
            if key in self.EXCLUSIVE_ANNOTATIONS:
                for other in list(self.EXCLUSIVE_ANNOTATIONS) + list(self.SYMBOL_ANNOTATIONS):
                    if other != key and self._annotation_action(other):
                        self._annotation_action(other).setChecked(False)
            else:
                for other in self.EXCLUSIVE_ANNOTATIONS:
                    self._annotation_action(other).setChecked(False)
        self.apply_annotation_status()

    def annotate_all(self, node):
        action = self.original_actions[node['id']]
        for key in self.EXCLUSIVE_ANNOTATIONS:
            self._annotation_action(key).setChecked(False)
        for key in self.SYMBOL_ANNOTATIONS:
            if self._annotation_action(key):
                self._annotation_action(key).setChecked(action.isChecked())
        self.apply_annotation_status()

    def apply_annotation_status(self):
        from PrePoMax import AnnotateWithColorEnum as A
        status = getattr(A, 'None')
        for key in self.EXCLUSIVE_ANNOTATIONS:
            if self._annotation_action(key).isChecked():
                status = getattr(A, {'FaceOrientations': 'FaceOrientation'}.get(key, key))
                break
        else:
            value = 0
            for key, flag in self.SYMBOL_ANNOTATIONS.items():
                if self._annotation_action(key) and self._annotation_action(key).isChecked():
                    value |= int(getattr(A, flag))
            if value:
                status = enum_value(A, value)
            all_symbols = self.original_actions.get('tsmiAnnotateAllSymbols')
            if all_symbols:
                all_symbols.setChecked(all(self._annotation_action(k).isChecked() for k in self.SYMBOL_ANNOTATIONS if self._annotation_action(k)))
        self.controller.AnnotateWithColor = status
        self.refresh()

    def item_ids(self, node):
        """FrmMain.ChangeVisibleItemIdsStatus."""
        from PrePoMax import ShowItemIdsEnum as S
        action = self.original_actions[node['id']]
        geometry = ['VertexIds', 'EdgeIds', 'SurfaceIds', 'PartIds', 'PartNames']
        mesh = ['NodeIds', 'ElementIds']
        key = node['id'][len('tsmiView'):]
        if action.isChecked():
            for other in (geometry if key in mesh else mesh):
                self.original_actions['tsmiView' + other].setChecked(False)
            if key == 'PartIds':
                self.original_actions['tsmiViewPartNames'].setChecked(False)
            elif key == 'PartNames':
                self.original_actions['tsmiViewPartIds'].setChecked(False)
        flags = {'VertexIds': 'Vertices', 'EdgeIds': 'Edges', 'SurfaceIds': 'Surfaces', 'PartIds': 'Parts',
                 'PartNames': 'PartNames', 'NodeIds': 'Nodes', 'ElementIds': 'Elements'}
        value = sum(int(getattr(S, flags[k])) for k in geometry + mesh if self.original_actions['tsmiView' + k].isChecked())
        self.controller.ShowItemIds = enum_value(S, value)
        self.refresh()

    def edit_model(self):
        if str(self.controller.Model.UnitSystem.UnitSystemType) == 'Undefined':
            return
        self.ensure_view(ViewGeometryModelResults.Model)
        self.edit_definition('Model properties', None, None)

    def model_tool(self, family):
        self.ensure_view(ViewGeometryModelResults.Model)
        self.edit_geometry(family)

    def geometry_tool(self, family):
        self.ensure_view(ViewGeometryModelResults.Geometry)
        self.edit_geometry(family)

    def find_edges_for(self, names):
        angle, ok = QtWidgets.QInputDialog.getDouble(self, 'Find edges', 'Angle [degrees]', 30, 0, 180, 3)
        if ok:
            self.run_operation(self.geometry.FindEdges(Array[String](names), angle))

    def preview(self, call):
        call()
        self.refresh()

    def arrange_annotations(self):
        if hasattr(self.scene, 'presentation') and hasattr(self.scene.presentation, 'arrange_annotations'):
            self.scene.presentation.arrange_annotations()
            self.render()

    def convert_odb(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Convert .odb to .frd', '', 'Abaqus result files (*.odb)')
        if path:
            self.run_operation(__import__('System').Threading.Tasks.Task.Run(
                __import__('System').Action(lambda: self.controller.ConvertOdbToFrd(path))))

    def bidirectional_mesh_converter(self):
        """Original launcher: the converter is a separate tool in <startup>/Tools."""
        import os
        import subprocess
        from System import AppContext
        startup = Path(str(AppContext.BaseDirectory))  # Application.StartupPath equivalent
        names = ['BidirectionalMeshConverter.exe'] + ([] if os.name == 'nt' else ['BidirectionalMeshConverter'])
        converter = next((startup / 'Tools' / n for n in names if (startup / 'Tools' / n).is_file()), None)
        if converter is None:
            raise FileNotFoundError('The Bidirectional Mesh Converter was not found.\n' + str(startup / 'Tools' / names[0]))
        temp = startup / 'Temp'
        if not temp.is_dir():
            raise FileNotFoundError("The temporary folder '" + str(temp) + "' was not found.")
        subprocess.Popen([str(converter)], cwd=str(converter.parent))

    def toggle_automation(self):
        if self.application.Automation.IsRunning:
            self.application.Automation.Stop()
        else:
            self.start_automation()

    def start_box_zoom(self):
        self.box_zoom_pending = True
        self.statusBar().showMessage('Drag a rectangle in the viewport to zoom.')

    # ------------------------------------------------- original camera views
    def _finish_camera(self):
        self.fit()

    def original_view(self, axis, positive):
        """vtkControl.SetFrontBackView / SetTopBottomView / SetLeftRightView."""
        camera = self.renderer.GetActiveCamera()
        f = camera.GetFocalPoint()
        if axis == 'front':
            d = 1 if positive else -1
            camera.SetPosition(f[0], f[1], f[2] + d)
            camera.SetViewUp(0, 1, 0)
        elif axis == 'top':
            d = 1 if positive else -1
            camera.SetPosition(f[0], f[1] + d, f[2])
            camera.SetViewUp(0, 0, -d)
        else:
            d = -1 if positive else 1
            camera.SetPosition(f[0] + d, f[1], f[2])
            camera.SetViewUp(0, 1, 0)
        self._finish_camera()

    def _closest_up(self):
        up = self.renderer.GetActiveCamera().GetViewUp()
        a = [abs(v) for v in up]
        m = max(a)
        sign = lambda v: (v > 0) - (v < 0)
        if m == a[0]:
            return (sign(up[0]), 0, 0)
        if m == a[1]:
            return (0, sign(up[1]), 0)
        return (0, 0, sign(up[2]))

    def original_isometric(self, positive=True):
        """vtkControl.SetIsometricView (closest of the eight octant directions)."""
        import math
        camera = self.renderer.GetActiveCamera()
        d = 1 if positive else -1
        camera.SetViewUp(*self._closest_up())
        f = camera.GetFocalPoint()
        normal = camera.GetViewPlaneNormal()
        octants = [(1, 1, 1), (-1, 1, 1), (-1, -1, 1), (1, -1, 1), (1, 1, -1), (-1, 1, -1), (-1, -1, -1), (1, -1, -1)]

        def angle(v):
            dot = sum(a * b for a, b in zip(normal, v)) / (math.sqrt(3) * math.sqrt(sum(a * a for a in normal)))
            return math.acos(max(-1, min(1, dot)))
        o = octants[min(range(4), key=lambda i: angle(octants[i]))]  # original compares quadrants I-IV
        camera.SetPosition(f[0] + d * o[0], f[1] + d * o[1], f[2] + d * o[2])
        camera.OrthogonalizeViewUp()
        up = camera.GetViewUp()
        i = max(range(3), key=lambda k: abs(up[k]))
        camera.SetViewUp(*[(1 if up[k] > 0 else -1) if k == i else 0 for k in range(3)])
        self._finish_camera()

    def original_normal_view(self):
        """vtkControl.SetNormalView: look along the dominant axis of the view direction."""
        camera = self.renderer.GetActiveCamera()
        direction = camera.GetViewPlaneNormal()
        i = max(range(3), key=lambda k: abs(direction[k]))
        delta = [0.0, 0.0, 0.0]
        sign = 1 if direction[i] > 0 else -1
        delta[i] = -sign if abs(direction[i]) == 1 else sign
        f = camera.GetFocalPoint()
        camera.SetPosition(f[0] + delta[0], f[1] + delta[1], f[2] + delta[2])
        self._finish_camera()

    def original_vertical_view(self):
        camera = self.renderer.GetActiveCamera()
        camera.SetViewUp(*self._closest_up())
        self._finish_camera()

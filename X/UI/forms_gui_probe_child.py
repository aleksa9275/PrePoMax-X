"""Executed UI evidence for the child-window forms and dialogs compiled whole (C11), run as steps of
forms_gui_probe.py on the imported public deck: each form opens through its FrmMain entry point at its designer
size; the original CodersLabTreeView is operated with Qt mouse input at the node rectangles the model reports;
modal dialogs (FrmGetValue, FrmGetColor, FrmParametersEditor, FrmMaterialLibrary, FrmSplash) run in their nested
modal loop and their original handlers change the model."""
import re
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtTest, QtWidgets

ROOT = Path(__file__).resolve().parents[2]
# Non-modal forms opened by FrmMain entry points (ShowForm / Show): (entry, arguments, form class).
CHILD_FORMS = [
    ('tsmiCreateMaterial_Click', {}, 'FrmMaterial'),
    ('tsmiCreateSurfaceInteraction_Click', {}, 'FrmSurfaceInteraction'),
    ('EditStepControls', {'step': 'Step-1'}, 'FrmStepControls'),
    ('tsmiCreateAnalysis_Click', {}, 'FrmAnalysis'),
    ('tsmiEditUserViews_Click', {}, 'FrmUserVew'),
    ('tsmiSectionView_Click', {}, 'FrmSectionView'),
    ('tsmiExplodedView_Click', {}, 'FrmExplodedView'),
    ('tsmiSettings_Click', {}, 'FrmSettings'),
    ('tsmiQuery_Click', {}, 'FrmQuery'),
    ('tsmiFind_Click', {}, 'FrmFind'),
    ('tsmiSearchContactPairs_Click', {}, 'FrmSearchContactPairs'),
]

# Forms whose own code sizes them when they are prepared (the designer size is not what WinForms shows either).
SELF_SIZING = {'FrmMaterial': 'PrepareForm moves the property tabs below the models tree and grows the form by the difference',
               'FrmUserVew': 'Load collapses the properties group (static _collapsed = true) and shrinks the form by its height'}


def source_size(cls):
    """ClientSize in the InitializeComponent of the file that declares the class."""
    for path in (ROOT / 'PrePoMax/Forms').rglob('*.cs'):
        text = path.read_text(encoding='utf-8-sig')
        if re.search(r'\bclass ' + cls + r'\b', text) and not path.name.endswith('.Designer.cs'):
            designer = path.with_name(path.stem + '.Designer.cs')
            sizes = re.findall(r'this\.ClientSize = new System\.Drawing\.Size\((\d+), (\d+)\);', designer.read_text(encoding='utf-8-sig'))
            return tuple(int(v) for v in sizes[-1])
    raise KeyError(cls)


class ChildFormsProbe:
    def __init__(self, app, window, check, report, snapshot):
        self.app, self.window, self.check, self.report, self.snapshot = app, window, check, report, snapshot
        self.c = window.controller
        self.host, self.renderer = window.form_host, window.form_renderer

    # Helpers -------------------------------------------------------------------------------------------------------------
    @staticmethod
    def walk(control):
        for child in control.Controls:
            yield child
            yield from ChildFormsProbe.walk(child)

    def by_name(self, form, name):
        return next(x for x in self.walk(form) if str(x.Name) == name)

    def widget(self, form, control):
        self.renderer.flush()
        self.app.processEvents()
        window = self.renderer.windows.get(form)
        return window, (window.widgets.get(control) if window else None)

    def open_forms(self):
        from System.Windows.Forms import Form
        return [f for f in Form.OpenForms if f.Visible]

    def entry(self, method, step=None, name=None, parts=None):
        from System import Array, String
        self.window.in_ui_context(lambda: self.host.InvokeEntry(method, step, name, None if parts is None else Array[String](parts), None))
        self.renderer.flush()

    def modal(self, method, operate, step=None, name=None, parts=None):
        """Runs a FrmMain entry point that shows a modal original form; operate(form) runs inside its modal loop
        and must close it. Returns the form and the error operate raised, if any."""
        from System.Windows.Forms import Form
        seen = {}

        def later():
            form = next((f for f in Form.OpenForms if f.Visible and f.Modal), None)
            if form is None:
                QtCore.QTimer.singleShot(50, later)
                return
            seen['form'] = form
            try:
                self.renderer.flush()
                self.app.processEvents()
                operate(form)
            except Exception as error:   # the dialog is closed so the probe does not hang
                seen['error'] = error
                if form.Visible:
                    self.renderer.guard(form.CloseByUser)
        QtCore.QTimer.singleShot(50, later)
        self.entry(method, step, name, parts)
        if 'error' in seen:
            raise seen['error']
        return seen.get('form')

    def click(self, form, name):
        self.renderer.guard(self.by_name(form, name).RaiseClick)
        self.renderer.flush()

    def tree_click(self, tree_widget, node, double=False):
        """Qt mouse input at the node's label rectangle (the original CodersLabTreeView hit-tests it)."""
        bounds = node.Bounds
        point = QtCore.QPoint(bounds.X + min(10, bounds.Width // 2), bounds.Y + bounds.Height // 2)
        viewport = tree_widget.viewport()
        if double:
            # What Qt delivers for a double click: press, release, press, double-click, release.
            QtTest.QTest.mouseClick(viewport, QtCore.Qt.MouseButton.LeftButton, QtCore.Qt.KeyboardModifier.NoModifier, point)
            for kind in (QtCore.QEvent.Type.MouseButtonPress, QtCore.QEvent.Type.MouseButtonDblClick, QtCore.QEvent.Type.MouseButtonRelease):
                buttons = QtCore.Qt.MouseButton.NoButton if kind == QtCore.QEvent.Type.MouseButtonRelease else QtCore.Qt.MouseButton.LeftButton
                event = QtGui.QMouseEvent(kind, QtCore.QPointF(point), QtCore.QPointF(viewport.mapToGlobal(point)), QtCore.Qt.MouseButton.LeftButton,
                                          buttons, QtCore.Qt.KeyboardModifier.NoModifier)
                QtWidgets.QApplication.sendEvent(viewport, event)
        else:
            QtTest.QTest.mouseClick(viewport, QtCore.Qt.MouseButton.LeftButton, QtCore.Qt.KeyboardModifier.NoModifier, point)
        self.renderer.flush()
        self.app.processEvents()

    @staticmethod
    def find_node(nodes, text):
        for node in nodes:
            if str(node.Text) == text:
                return node
            found = ChildFormsProbe.find_node(node.Nodes, text)
            if found is not None:
                return found
        return None

    def grid_set(self, form, label, text):
        from System.Windows.Forms import PropertyGrid, GridItemType
        grid = next(x for x in self.walk(form) if isinstance(x, PropertyGrid) and x.Visible)
        for item in PropertyGrid.Flatten(grid.Root):
            if item.GridItemType == GridItemType.Property and str(item.Label).lstrip('​\t') == label:
                self.renderer.guard(lambda: grid.SetValueFromText(item, text))
                self.renderer.flush()
                return
        raise KeyError(label + ' not in ' + type(form).__name__)

    # Steps ---------------------------------------------------------------------------------------------------------------
    def catalogue(self):
        c = self.c
        for method, arguments, cls in CHILD_FORMS:
            commands = c.GetCommands().Count
            self.entry(method, arguments.get('step'))
            form = next((f for f in self.open_forms() if type(f).__name__ == cls), None)
            self.check(method + ' opens the original ' + cls, form is not None)
            window = self.renderer.windows.get(form)
            self.renderer.flush()
            self.app.processEvents()
            expected = source_size(cls)
            self.report['forms'][method] = {'form': cls, 'title': str(form.Text), 'clientSize': [form.ClientSize.Width, form.ClientSize.Height],
                                            'designerSize': list(expected)}
            # PrepareForm may size the form for its content (e.g. FrmQuery); the window follows the form.
            self.check(method + ': drawn at the form\'s client size', window is not None and window.isVisible()
                       and (window.width(), window.height()) == (form.ClientSize.Width, form.ClientSize.Height))
            if cls in SELF_SIZING:
                self.report['forms'][method]['selfSizing'] = SELF_SIZING[cls]
            else:
                self.check(method + ': ' + cls + ' client size from the original designer', (form.ClientSize.Width, form.ClientSize.Height) == expected)
            self.snapshot('child-' + cls, form)
            cancel = next((x for x in self.walk(form) if str(x.Name) in ('btnCancel', 'btnClose') and x.Visible), None)
            self.renderer.guard(cancel.RaiseClick if cancel is not None else form.CloseByUser)
            self.renderer.flush()
            self.check(method + ': closing hides the form', not form.Visible and (window is None or not window.isVisible()))
            self.check(method + ': closing changes nothing in the model history', c.GetCommands().Count == commands)

    def material(self):
        """FrmMaterial: the original CodersLabTreeView selects a model by a Qt click; Add, property values, OK."""
        c = self.c
        self.entry('tsmiCreateMaterial_Click')
        form = next(f for f in self.open_forms() if type(f).__name__ == 'FrmMaterial')
        tree = self.by_name(form, 'tvProperties')
        _, tree_widget = self.widget(form, tree)
        names = [str(n.Text) for n in tree.Nodes]
        self.report['forms']['FrmMaterial'] = {'treeRoots': names}
        elastic = self.find_node(tree.Nodes, 'Elastic')
        self.check('FrmMaterial: the available models tree holds Elastic', elastic is not None)
        elastic.EnsureVisible()
        self.renderer.flush()
        self.tree_click(tree_widget, elastic)
        self.check('Qt click selects the node through CodersLabTreeView (its own multi-selection)', list(tree.SelectedNodes) == [elastic])
        self.click(form, 'btnAdd')
        added = [str(i.Text) for i in self.by_name(form, 'lvAddedProperties').Items]
        self.check('Add puts the selected model in the material (btnAdd_Click)', added == ['Elastic'])
        density = self.find_node(tree.Nodes, 'Density')
        density.EnsureVisible()
        self.renderer.flush()
        self.tree_click(tree_widget, density, double=True)
        added = [str(i.Text) for i in self.by_name(form, 'lvAddedProperties').Items]
        self.check('a double click adds a model (tvProperties_DoubleClick)', added == ['Elastic', 'Density'])
        lv = self.by_name(form, 'lvAddedProperties')
        from System import Array, Int32
        self.renderer.guard(lambda: lv.SelectByUser(Array[Int32]([0])))
        self.renderer.flush()
        self.grid_set(form, "Young's modulus", '210000')
        self.grid_set(form, "Poisson's ratio", '0.3')
        name = self.by_name(form, 'tbName')
        self.renderer.guard(lambda: (name.SetUserText('Steel_C11'), name.RaiseLeave()))
        prompts = len(self.window.auto_prompts)
        self.click(form, 'btnOK')
        self.check('OK with the default density is refused with the original message',
                   form.Visible and any('The value must be larger than 0.' in p for p in self.window.auto_prompts[prompts:])
                   and 'Steel_C11' not in [str(m) for m in c.GetMaterialNames()])
        self.renderer.guard(lambda: lv.SelectByUser(Array[Int32]([1])))
        self.renderer.flush()
        self.grid_set(form, 'Density', '7.85e-9')
        self.click(form, 'btnOK')
        material = c.GetMaterial('Steel_C11') if 'Steel_C11' in [str(m) for m in c.GetMaterialNames()] else None
        self.check('OK creates the material with its models (original Add)', material is not None and material.Properties.Count == 2 and not form.Visible)
        elastic_property = next(p for p in material.Properties if type(p).__name__ == 'Elastic')
        row = elastic_property.YoungsPoissonsTemp[0]
        values = [float(row[0].Value), float(row[1].Value)]
        self.report['forms']['FrmMaterial']['elastic'] = values
        self.check("the entered Young's modulus and Poisson's ratio reach the Elastic model", values == [210000.0, 0.3])
        QtTest.QTest.qWait(200)
        self.check('the material is in the model tree', any(str(e.Name) == 'Steel_C11' for e in self.tree_entries('Materials')))

    def user_views(self):
        """FrmUserVew: the CollapsableGroupBox +/- button (a Qt click at the original button rectangle) expands the
        properties group; OnCollapsedChanged grows the form back to its designer size."""
        self.entry('tsmiEditUserViews_Click')
        form = next(f for f in self.open_forms() if type(f).__name__ == 'FrmUserVew')
        group = self.by_name(form, 'gbProperties')
        _, widget = self.widget(form, group)
        self.check('User Views opens with the properties group collapsed', group.IsCollapsed)
        QtTest.QTest.mouseClick(widget, QtCore.Qt.MouseButton.LeftButton, QtCore.Qt.KeyboardModifier.NoModifier, QtCore.QPoint(15, 7))
        self.renderer.flush()
        self.app.processEvents()
        window = self.renderer.windows.get(form)
        self.check('a click on the +/- button expands the group (CollapsableGroupBox.OnMouseUp)', not group.IsCollapsed)
        self.check('the form grows back to its designer size (gbProperties_OnCollapsedChanged)',
                   (form.ClientSize.Width, form.ClientSize.Height) == source_size('FrmUserVew') and (window.width(), window.height()) == source_size('FrmUserVew'))
        self.renderer.guard(self.by_name(form, 'btnCancel').RaiseClick)
        self.renderer.flush()

    def tree_entries(self, family):
        result = []
        for item in self.window.walk_tree():
            entry = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if entry is not None and not entry.Group and entry.Family == family:
                result.append(entry)
        return result

    def get_value_dialogs(self):
        c = self.c
        part = str(c.GetModelPartNames()[0])

        def transparency(form):
            self.check('FrmGetValue title (PrepareForm)', str(form.Text).startswith('Set Transparency: '))
            self.grid_set(form, 'Transparency', '100')
            self.click(form, 'btnOK')
        self.modal('SetTransparencyForModelParts', transparency, parts=[part])
        self.check('FrmGetValue OK sets the part transparency (SetTransparencyForModelPartsCommand)',
                   c.Model.Mesh.Parts[part].Color.A == 100)

        def color(form):
            self.check('FrmGetColor title (PrepareForm)', str(form.Text).startswith('Set Part Color: '))
            self.grid_set(form, 'Color', '255, 10, 20, 30')
            self.click(form, 'btnOK')
        self.modal('SetColorForModelParts', color, parts=[part])
        rgb = c.Model.Mesh.Parts[part].Color
        self.check('FrmGetColor OK sets the part color (SetColorForModelPartsCommand)', (rgb.R, rgb.G, rgb.B) == (10, 20, 30))

        def renumber(form):
            self.check('renumber dialog title', str(form.Text) == 'Renumber Nodes')
            self.grid_set(form, 'Start node id', '1000')
            self.click(form, 'btnOK')
        self.modal('tsmiRenumberAllNodes_Click', renumber)
        self.check('Renumber Nodes renumbers from the entered id (RenumberNodesCommand)', min(int(i) for i in c.Model.Mesh.Nodes) == 1000)

        def cancel(form):
            self.click(form, 'btnCancel')
        before = c.GetCommands().Count
        self.modal('tsmiRenumberAllElements_Click', cancel)
        self.check('Cancel in FrmGetValue adds no command', c.GetCommands().Count == before)

    def parameters(self):
        c = self.c

        def edit(form):
            from System import Array, Int32
            self.check('FrmParametersEditor is the original modal form', type(form).__name__ == 'FrmParametersEditor' and form.Modal)
            grid = self.by_name(form, 'dgvData')
            headers = [str(col.HeaderText).lstrip('\u200b\t') for col in grid.Columns]
            self.report['forms']['FrmParametersEditor'] = {'columns': headers, 'widths': [col.Width for col in grid.Columns]}
            self.check('parameter grid columns from ViewEquationParameter', headers == ['Name', 'Value/Equation', 'Evaluates to', 'Description'])
            from forms_gui_probe_grid import edit_cell
            _, table = self.widget(form, grid)
            # Typed into the Qt cell editor: the new row, then the committed item's equation.
            edit_cell(self.app, table, grid.NewRowIndex, 0, 'thickness')
            self.renderer.flush()
            edit_cell(self.app, table, 0, 1, '=2*3')
            self.renderer.flush()
            values = [str(grid.GetCellText(0, i)) for i in range(grid.Columns.Count)]
            self.report['forms']['FrmParametersEditor']['row'] = values
            item = grid.Rows[0].DataBoundItem
            self.report['forms']['FrmParametersEditor']['error'] = str(item.Error) if item is not None and item.Error is not None else None
            self.check('the new parameter evaluates in the grid (EvaluateParameters)', values[0] == 'thickness' and values[2].startswith('6'))
            self.click(form, 'btnOK')
        self.modal('tsmiEditParameters_Click', edit)
        names = [str(k) for k in c.Model.Parameters.Keys]
        self.check('OK sets the parameters (SetParametersCommand)', 'thickness' in names)

    def settings(self):
        """FrmSettings: the settings pages list, the solver page's environment variables through the original
        EnvVarsUIEditor and modal FrmGetEnvVars (a row typed into its grid), OK -> FrmMain.UpdateSettings."""
        from System import Array, Int32
        c = self.c
        self.entry('tsmiSettings_Click')
        form = next(f for f in self.open_forms() if type(f).__name__ == 'FrmSettings')
        pages = self.by_name(form, 'lvSettings')
        names = [str(i.Text) for i in pages.Items]
        self.report['forms']['FrmSettings'] = {'pages': names}
        index = next(i for i, n in enumerate(names) if 'Solver' in n or 'Calculix' in n or 'CalculiX' in n)
        self.renderer.guard(lambda: pages.SelectByUser(Array[Int32]([index])))
        self.renderer.flush()
        from System.Windows.Forms import PropertyGrid, GridItemType
        grid = self.by_name(form, 'propertyGrid')
        row = next(i for i in PropertyGrid.Flatten(grid.Root) if i.GridItemType == GridItemType.Property and str(i.Label).lstrip('\u200b\t') == 'Environment variables')
        window, _ = self.widget(form, grid)

        def env(dialog):
            from forms_gui_probe_grid import edit_cell
            self.check('the environment variables editor shows the original modal FrmGetEnvVars', type(dialog).__name__ == 'FrmGetEnvVars')
            dgv = self.by_name(dialog, 'dgvEnvironmentVariables')
            self.report['forms']['FrmGetEnvVars'] = {'columns': [str(col.HeaderText).lstrip('\u200b') for col in dgv.Columns]}
            _, table = self.widget(dialog, dgv)
            # Columns Active, Name, Value (EnvironmentVariable): the new row's name, then its value.
            edit_cell(self.app, table, dgv.NewRowIndex, 1, 'OMP_NUM_THREADS')
            self.renderer.flush()
            edit_cell(self.app, table, 0, 2, '2')
            self.renderer.flush()
            self.click(dialog, 'btnOK')
        from System.Windows.Forms import Form

        def later():
            dialog = next((f for f in Form.OpenForms if f.Visible and f.Modal), None)
            if dialog is None:
                QtCore.QTimer.singleShot(50, later)
                return
            try:
                env(dialog)
            except Exception as error:
                self.report['envError'] = str(error)
                if dialog.Visible:
                    self.renderer.guard(dialog.CloseByUser)
        QtCore.QTimer.singleShot(50, later)
        self.renderer.edit_modal(window.widgets[grid], row)
        self.check('FrmGetEnvVars edit reached the solver settings (' + str(self.report.get('envError', '')) + ')',
                   any(str(v.Name) == 'OMP_NUM_THREADS' for v in (row.PropertyDescriptor.GetValue(grid.GetContext(row).Instance) or [])))
        self.click(form, 'btnOK')
        variables = list(c.Settings.Solver.EnvironmentVariables or [])
        self.check('Settings OK stores the settings (FrmMain.UpdateSettings)', not form.Visible and any(str(v.Name) == 'OMP_NUM_THREADS' and str(v.Value) == '2' for v in variables))

    def regenerate(self):
        """FrmMain.TryGetRegenerateType with regeneration types in use: the original FrmRegenerate."""
        from System.Windows.Forms import Form
        seen = {}

        def later():
            dialog = next((f for f in Form.OpenForms if f.Visible and f.Modal), None)
            if dialog is None:
                QtCore.QTimer.singleShot(50, later)
                return
            seen['form'] = type(dialog).__name__
            self.renderer.guard(self.by_name(dialog, 'rbFEModel').RaiseClick)
            self.click(dialog, 'btnOK')
        QtCore.QTimer.singleShot(50, later)
        chosen = self.window.in_ui_context(lambda: self.host.SelectRegenerateType(True))
        self.check('the regeneration type dialog is the original FrmRegenerate', seen.get('form') == 'FrmRegenerate')
        self.report['forms']['FrmRegenerate'] = {'chosen': str(chosen)}
        self.check('its choice is the regeneration type (RegenerateType)', chosen is not None and str(chosen) != 'All')

    def geometry(self, parts):
        """Geometry view: FrmAnalyzeGeometry (AnalyzeGeometry) and FindEdgesByAngleForGeometryParts (FrmGetValue)."""
        self.entry('AnalyzeGeometry', parts=parts)
        form = next((f for f in self.open_forms() if type(f).__name__ == 'FrmAnalyzeGeometry'), None)
        self.check('Analyze geometry opens the original FrmAnalyzeGeometry', form is not None)
        labels = {str(x.Name): str(x.Text) for x in self.walk(form) if type(x).__name__ == 'Label'}
        self.report['forms']['FrmAnalyzeGeometry'] = {'labels': labels}
        self.renderer.guard(form.CloseByUser)
        self.renderer.flush()

        def cancel(dialog):
            self.check('Find edges by angle asks the original FrmGetValue', type(dialog).__name__ == 'FrmGetValue')
            self.click(dialog, 'btnCancel')
        self.modal('FindEdgesByAngleForGeometryParts', cancel, parts=parts)

    def about(self):
        def close(form):
            self.check('About shows the original FrmSplash', type(form).__name__ == 'FrmSplash')
            self.renderer.guard(form.CloseByUser)
            self.renderer.flush()
        self.modal('tsmiAbout_Click', close)

    def library(self):
        def close(form):
            self.check('Material Library is the original modal FrmMaterialLibrary', type(form).__name__ == 'FrmMaterialLibrary')
            tree = self.by_name(form, 'cltvLibrary')
            self.report['forms']['FrmMaterialLibrary'] = {'libraryRoots': [str(n.Text) for n in tree.Nodes]}
            self.check('the library tree shows the model materials', any(str(n.Text) for n in tree.Nodes))
            self.renderer.guard(form.CloseByUser)
            self.renderer.flush()
        self.modal('tsmiMaterialLibrary_Click', close)

"""Executed UI evidence for the original property forms compiled whole (C9): each form is opened through the
FrmMain entry points (OriginalFormHost), drawn at its original designer geometry, operated through the same
events WinForms raises, and its original handlers create/replace the model items."""
import json
import time
import traceback
from pathlib import Path

from PyQt6 import QtCore, QtTest, QtWidgets
from System import EventArgs

DECKS = Path(__file__).resolve().parents[1] / 'Analysis/StaticDeck'
ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).resolve().parent / 'fixtures/cube.brep'
BASE_SIZES = {'FrmProperties': (334, 411), 'FrmPropertyListView': (334, 461), 'FrmPropertyDataListView': (334, 461)}
# Model-view forms: (FrmMain entry point, arguments, original ShowForm title).
MODEL_FORMS = [
    ('EditModel', {}, 'Edit Model'),
    ('tsmiCreateNodeSet_Click', {}, 'Create Node Set'),
    ('tsmiCreateElementSet_Click', {}, 'Create Element Set'),
    ('tsmiCreateSurface_Click', {}, 'Create Surface'),
    ('tsmiCreateModelReferencePoint_Click', {}, 'Create Model Reference Point'),
    ('tsmiCreateModelCoordinateSystem_Click', {}, 'Create Model Coordinate System'),
    ('CreateSection', {}, 'Create Section'),
    ('tsmiCreateConstraint_Click', {}, 'Create Constraint'),
    ('tsmiCreateContactPair_Click', {}, 'Create Contact Pair'),
    ('CreateInitialCondition', {}, 'Create Initial Condition'),
    ('tsmiCreateStep_Click', {}, 'Create Step'),
    ('CreateHistoryOutput', {'step': 'Step-1'}, 'Create History Output'),
    ('CreateFieldOutput', {'step': 'Step-1'}, 'Create Field Output'),
    ('CreateBoundaryCondition', {'step': 'Step-1'}, 'Create Boundary Condition'),
    ('CreateLoad', {'step': 'Step-1'}, 'Create Load'),
    ('CreateDefinedField', {'step': 'Step-1'}, 'Create Defined Field'),
    ('EditModelPart', {'name': 'PART'}, 'Edit Part: PART'),
    ('TranslateModelParts', {'parts': True}, 'Translate Parts: '),
    ('RotateModelParts', {'parts': True}, 'Rotate Parts: '),
    ('MirrorModelParts', {'parts': True}, 'Mirror Parts: '),
    ('ScaleModelParts', {'parts': True}, 'Scale Parts: '),
    ('ElementQuality', {'parts': True, 'gmsh': True}, 'Element Quality'),
    ('MergeCoincidentNodes', {}, 'Merge Coincident Nodes'),
    ('CreateBoundaryLayer', {}, 'Create Boundary Layer'),
    ('RemeshElements', {}, 'Remeshing Parameters'),
    ('ThickenShellMesh', {}, 'Thicken Shell Mesh'),
    ('tsmiSplitPartMeshUsingSurface_Click', {}, 'Split Part Mesh Using Surface'),
    ('tsmiCaptureViewportAs_Click', {}, 'Capture Viewport'),
    ('tsmiCreateDistribution_Click', {}, 'Create Distribution'),
    ('tsmiCreateAmplitude_Click', {}, 'Create Amplitude'),
]
GEOMETRY_FORMS = [
    ('CreateMeshSetupItem', {}, 'Create Mesh Setup Item'),
    ('EditGeometryPart', {'name': 'PART'}, 'Edit Part: PART'),
    ('TranslateGeometryParts', {'parts': True}, 'Translate parts: '),
    ('RotateGeometryParts', {'parts': True}, 'Rotate parts: '),
    ('MirrorGeometryParts', {'parts': True}, 'Mirror parts: '),
    ('ScaleGeometryParts', {'parts': True}, 'Scale parts: '),
    ('CreateSplitSolid', {}, 'Split Solid'),
    ('CreateSplitShell', {}, 'Split Face'),
    ('CreateOffsetFace', {}, 'Offset Face'),
    ('CreateRepairGeometry', {}, 'Repair Geometry'),
    ('CreateSplitPeriodicFaces', {}, 'Split Periodic Faces'),
    ('CreateSurfaceOperation', {'operation': 'FlipNormal'}, ''),
    ('CreateSurfaceOperation', {'operation': 'DeleteCadFaces'}, ''),
    ('CreateSurfaceOperation', {'operation': 'FuseFaces'}, ''),
]


def designer_size(name):
    """ClientSize of the form's own InitializeComponent, else of its original base form."""
    import re
    files = [p for p in (ROOT / 'PrePoMax/Forms').rglob(name + '*.cs') if p.stem in (name, name + '.Designer')]
    text = '\n'.join(p.read_text(encoding='utf-8-sig') for p in files)
    sizes = re.findall(r'this\.ClientSize = new System\.Drawing\.Size\((\d+), (\d+)\);', text)
    if sizes:
        width, height = (int(v) for v in sizes[-1])
        # A constructor may set the window height after InitializeComponent (FrmLoad: 560 + 3 * 19); the
        # client height is then that minus the WinForms frame (Form.FrameHeight).
        from System.Windows.Forms import Form
        override = re.search(r'this\.Height = ([0-9 +*]+);', text)
        if override:
            height = eval(override.group(1), {'__builtins__': {}}) - Form.FrameHeight
        return width, height
    base = re.search(r'class ' + name + r'\s*:\s*(?:UserControls\.)?(\w+)', text).group(1)
    return BASE_SIZES.get(base) or designer_size(base)


def values(collection):
    return list(collection.values()) if isinstance(collection, dict) else list(collection.Values)


def start(app, window, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    report = {'success': False, 'checks': [], 'forms': {},
              'scope': 'local native Qt workflow on public decks; not four-target acceptance'}
    started = time.monotonic()
    c = window.controller
    host = None
    renderer = None

    def check(name, value):
        if not value:
            raise AssertionError(name)
        report['checks'].append(name)

    def ready():
        if window.operation_task is not None:
            return False
        return True

    def form_window(form):
        renderer.flush()
        app.processEvents()
        return renderer.windows.get(form)

    def visible_form():
        return host.ActiveItemForm

    def grid_of(form):
        from System.Windows.Forms import PropertyGrid
        return next(ctrl for ctrl in walk(form) if isinstance(ctrl, PropertyGrid))

    def walk(control):
        for child in control.Controls:
            yield child
            yield from walk(child)

    def by_name(form, name):
        return next(ctrl for ctrl in walk(form) if str(ctrl.Name) == name)

    def grid_row(grid, label):
        from System.Windows.Forms import PropertyGrid as G
        for item in G.Flatten(grid.Root):
            if item.PropertyDescriptor is not None and str(item.PropertyDescriptor.DisplayName).lstrip('​\t') == label:
                return item
        raise KeyError(label)

    def snapshot(name, form):
        w = form_window(form)
        if w is None:
            return
        w.raise_()
        QtTest.QTest.qWait(50)
        w.grab().save(str(output / (name + '.png')))

    def import_model():
        nonlocal host, renderer
        host, renderer = window.form_host, window.form_renderer
        window.auto_prompts = []
        from CaeModel import ModelSpaceEnum
        from CaeGlobals import UnitSystemType
        c.New()
        c.SetNewModelPropertiesCommand(ModelSpaceEnum.ThreeD, UnitSystemType.MM_TON_S_C)
        window.refresh()
        window.import_path(str(DECKS / 'c3d10-force.inp'), False)

    def step_form():
        if not ready():
            return False
        window.show_original_form('tsmiCreateStep_Click', None, EventArgs.Empty)
        form = visible_form()
        check('FrmStep opened through FrmMain.tsmiCreateStep_Click', form is not None and type(form).__name__ == 'FrmStep')
        w = form_window(form)
        check('FrmStep drawn as an owned tool window', w is not None and w.isVisible())
        check('FrmStep title from FrmMain.ShowForm', str(form.Text) == 'Create Step')
        lv = by_name(form, 'lvTypes')
        names = [str(i.Text) for i in lv.Items]
        report['forms']['FrmStep'] = {'types': names, 'clientSize': [form.ClientSize.Width, form.ClientSize.Height]}
        check('FrmStep lists the original step types', 'Static Step' in names and 'Frequency Step' in names)
        lv.SelectByUser([names.index('Static Step')])
        renderer.flush()
        grid = grid_of(form)
        check('FrmStep property grid shows the static step', grid.SelectedObject is not None and 'Static' in type(grid.SelectedObject).__name__)
        snapshot('FrmStep', form)
        by_name(form, 'btnOK').RaiseClick()
        renderer.flush()
        check('OK runs the original OnApply: step created', 'Step-1' in [str(s.Name) for s in c.GetAllSteps()])
        check('OK hides the form (FrmProperties hide-on-close)', not form.Visible and not w.isVisible())

    def bc_form():
        window.show_original_form('CreateBoundaryCondition', 'Step-1')
        form = visible_form()
        check('FrmBC opened through FrmMain.CreateBoundaryCondition', form is not None and type(form).__name__ == 'FrmBC')
        w = form_window(form)
        check('FrmBC original client size 334 x 561', form.ClientSize.Width == 334 and form.ClientSize.Height == 561)
        check('FrmBC window at the original client size', w.width() == 334 and w.height() == 561)
        lv = by_name(form, 'lvTypes')
        names = [str(i.Text) for i in lv.Items]
        report['forms']['FrmBC'] = {'types': names}
        check('FrmBC lists Fixed and Displacement/Rotation', names[:2] == ['Fixed', 'Displacement/Rotation'])
        # Original ListViewWithSelection: the clicked type is painted and the list keeps no selection.
        lv.SelectByUser([1])
        renderer.flush()
        grid = grid_of(form)
        check('Displacement/Rotation shown in the grid', type(grid.SelectedObject).__name__ == 'ViewDisplacementRotation')
        check('ListViewWithSelection keeps no list selection after a click', lv.SelectedItems.Count == 0 and lv.SelectedItem is not None)
        from System.Windows.Forms import GridItemType
        categories = [str(i.Label).lstrip('\u200b\t') for i in grid.Root.GridItems if i.GridItemType == GridItemType.Category]
        report['forms']['FrmBC']['categories'] = categories
        check('grid categories in original order (DynamicTypeDescriptor ordering prefixes)', categories == ['Data', 'Region', 'DOF', 'Distribution', 'Time/Frequency', 'Orientation', 'Appearance'])
        selection_form = host.SelectItemSetForm
        check('Selection region shows FrmSelectItemSet (ShowHideSelectionForm)', selection_form.Visible)
        selection_window = form_window(selection_form)
        check('FrmSelectItemSet drawn as its own tool window', selection_window is not None and selection_window.isVisible())
        report['forms']['FrmSelectItemSet'] = {'title': str(selection_form.Text), 'clientSize': [selection_form.ClientSize.Width, selection_form.ClientSize.Height],
                                               'size': [selection_form.Size.Width, selection_form.Size.Height], 'min': [selection_form.MinimumSize.Width, selection_form.MinimumSize.Height],
                                               'max': [selection_form.MaximumSize.Width, selection_form.MaximumSize.Height], 'moreLess': str(by_name(selection_form, 'btnMoreLess').Text),
                                               'window': [selection_window.width(), selection_window.height()]}
        snapshot('FrmSelectItemSet', selection_form)
        # Region by node set
        grid.SetValueFromText(grid_row(grid, 'Region type'), 'Node set name')
        renderer.flush()
        check('Region type Node set hides FrmSelectItemSet', not selection_form.Visible)
        grid.SetValueFromText(grid_row(grid, 'Node set'), 'BOTTOM')
        grid.SetValueFromText(grid_row(grid, 'U1'), '0')
        renderer.flush()
        snapshot('FrmBC', form)
        by_name(form, 'btnOK').RaiseClick()
        renderer.flush()
        bcs = [str(b.Name) for b in values(c.GetStep('Step-1').BoundaryConditions)]
        report['forms']['FrmBC']['created'] = bcs
        check('original OnApply created the boundary condition', len(bcs) == 1)

    def cancel_form(form):
        from System.Windows.Forms import Button
        cancel = next((c for c in walk(form) if isinstance(c, Button) and str(c.Name) == 'btnCancel' and c.Visible), None)
        if cancel is not None:
            renderer.guard(cancel.RaiseClick)
        else:
            renderer.guard(form.CloseByUser)
        renderer.flush()

    def catalogue(entries, label):
        from System import Array, String
        parts = [str(p) for p in (c.GetGeometryPartNames() if label == 'geometry' else c.GetModelPartNames())]
        import os
        for method, arguments, title in entries:
            if arguments.get('gmsh') and not os.environ.get('PREPOMAXX_GMSH_LIBRARY'):
                report.setdefault('pending', []).append(method + ': needs the native Gmsh profile')
                continue
            commands = c.GetCommands().Count
            name = parts[0] if arguments.get('name') == 'PART' else arguments.get('name')
            window.in_ui_context(lambda: host.InvokeEntry(method, arguments.get('step'), name,
                                                          Array[String](parts) if arguments.get('parts') else None,
                                                          arguments.get('operation')))
            form = visible_form()
            key = method + ('/' + arguments['operation'] if 'operation' in arguments else '')
            check(key + ' opens an original form' + ('' if form is not None else ': ' + ' | '.join(window.auto_prompts[-1:])), form is not None)
            kind = type(form).__name__
            w = form_window(form)
            expected = designer_size(kind)
            entry = {'form': kind, 'title': str(form.Text), 'clientSize': [form.ClientSize.Width, form.ClientSize.Height],
                     'designerSize': list(expected), 'window': [w.width(), w.height()] if w else None,
                     'types': [str(i.Text) for i in by_name(form, 'lvTypes').Items] if any(str(x.Name) == 'lvTypes' for x in walk(form)) else None}
            from System.Windows.Forms import PropertyGrid as G, GridItemType
            grids = [x for x in walk(form) if isinstance(x, G)]
            if grids and grids[0].Root is not None:
                grid = grids[0]
                entry['rows'] = [[str(i.Label).lstrip('\u200b\t'), bool(i.PropertyDescriptor.IsReadOnly), bool(grid.CanEditText(i))]
                                 for i in G.Flatten(grid.Root) if i.GridItemType == GridItemType.Property]
            report['forms'][key] = entry
            check(key + ': ShowForm title ' + repr(title), str(form.Text).startswith(title.replace('PART', name or '')))
            check(key + ': ' + kind + ' client size from the original designer', (form.ClientSize.Width, form.ClientSize.Height) == expected)
            check(key + ': drawn at the original client size', w is not None and w.isVisible() and (w.width(), w.height()) == expected)
            snapshot(label + '-' + key.replace('/', '-'), form)
            cancel_form(form)
            check(key + ': Cancel hides the form and the selection form', not form.Visible and not w.isVisible() and not host.SelectItemSetForm.Visible)
            check(key + ': Cancel changes nothing in the model history', c.GetCommands().Count == commands)

    def model_catalogue():
        from CaeModel import SurfaceInteraction
        c.AddSurfaceInteractionCommand(SurfaceInteraction('Contact_law'))
        catalogue(MODEL_FORMS, 'model')

    def edit_mode():
        """Original edit rules: preselected type, list disabled, the edited item hidden (Internal) until the form
        closes, OK - New only when creating."""
        bc = [str(b.Name) for b in values(c.GetStep('Step-1').BoundaryConditions)][0]
        window.show_original_form('EditBoundaryCondition', 'Step-1', bc)
        form = visible_form()
        lv = by_name(form, 'lvTypes')
        check('edit title names the item (FrmMain.ShowForm)', str(form.Text) == 'Edit Boundary Condition: ' + bc)
        check('edit preselects the type and disables the list (PreselectListViewItem)', not lv.Enabled and lv.SelectedItem is not None
              and str(lv.SelectedItem.Text) == 'Displacement/Rotation')
        check('OK - New hidden while editing', not by_name(form, 'btnOkAddNew').Visible)
        check('edited BC hidden while the form is open (BoundaryConditionInternal)', c.GetBoundaryCondition('Step-1', bc).Internal)
        cancel_form(form)
        check('Cancel shows the BC again', not c.GetBoundaryCondition('Step-1', bc).Internal)
        window.show_original_form('CreateBoundaryCondition', 'Step-1')
        form = visible_form()
        by_name(form, 'lvTypes').SelectByUser([0])
        renderer.flush()
        grid = grid_of(form)
        grid.SetValueFromText(grid_row(grid, 'Region type'), 'Node set name')
        before = c.GetStep('Step-1').BoundaryConditions.Count
        renderer.guard(by_name(form, 'btnOkAddNew').RaiseClick)
        renderer.flush()
        check('OK - New creates the item and prepares the form again', c.GetStep('Step-1').BoundaryConditions.Count == before + 1
              and form.Visible and by_name(form, 'lvTypes').Enabled)
        cancel_form(form)

    def data_grid_forms():
        """FrmPropertyDataListView (C10): the original DataGridViewCopyPaste bound to the amplitude data points;
        cell edits, the new row, parse errors, copy/paste, plot (FrmDiagramView) and the original OnApply."""
        from System import Array, Int32
        from System.Windows.Forms import Keys, DataGridView, TabControl, Clipboard
        from forms_gui_probe_grid import grid_widget
        window.auto_prompts = []
        window.show_original_form('tsmiCreateAmplitude_Click', None, EventArgs.Empty)
        form = visible_form()
        check('FrmAmplitude opened through FrmMain.tsmiCreateAmplitude_Click', type(form).__name__ == 'FrmAmplitude' and str(form.Text) == 'Create Amplitude')
        check('single amplitude type preselected (Tabular)', grid_of(form).SelectedObject is not None and type(grid_of(form).SelectedObject).__name__ == 'ViewAmplitudeTabular')
        tabs = next(x for x in walk(form) if isinstance(x, TabControl))
        dgv = next(x for x in walk(form) if isinstance(x, DataGridView))
        w = form_window(form)
        qtabs = w.widgets[tabs]
        check('original tab pages Properties / Data points drawn', [qtabs.tabText(i) for i in range(qtabs.count())] == ['Properties', 'Data points'])
        headers = [str(col.HeaderText) for col in dgv.Columns]
        report['forms']['FrmAmplitude'] = {'headers': headers, 'rows': int(dgv.RowCount)}
        check('columns from AmplitudeDataPoint DisplayName with model units', headers == ['Time [s]\nFrequency [Hz]', 'Amplitude\n[/]'])
        check('one data point and the new row (AllowUserToAddRows)', dgv.RowCount == 2 and dgv.NewRowIndex == 1)
        renderer.guard(lambda: setattr(tabs, 'SelectedIndex', 1))
        renderer.flush()
        table = grid_widget(w, dgv)
        check('grid drawn with the cells and the new-row marker', table.rowCount() == 2 and table.item(0, 0).text() == '0'
              and table.verticalHeaderItem(1).text() == '*')
        # A user edit through the Qt cell editor: BeginEdit, typed text, EndEdit (new row -> BindingSource.AddNew).
        from forms_gui_probe_grid import edit_cell
        edit_cell(app, table, 1, 0, '1')
        renderer.flush()
        edit_cell(app, table, 1, 1, '=2*0.5')
        renderer.flush()
        report['forms']['FrmAmplitude']['afterEdit'] = [int(dgv.RowCount)] + [str(dgv.GetCellText(r, k)) for r in range(int(dgv.RowCount)) for k in range(2)] + list(window.auto_prompts)
        check('typing in the new row adds a data point', dgv.RowCount == 3 and str(dgv.GetCellText(1, 0)) == '1' and str(dgv.GetCellText(1, 1)) == '1')
        edit_cell(app, table, 0, 1, 'abc')
        renderer.flush()
        report['forms']['FrmAmplitude']['parseError'] = list(window.auto_prompts)
        from forms_gui_probe_grid import cancel_cell
        reopened = cancel_cell(app, table, 0, 1) if dgv.IsCurrentCellInEditMode else None
        renderer.flush()
        check('invalid cell text: original OnDataError message; the cell stays in edit mode with the text (WinForms)',
              len(window.auto_prompts) == 1 and reopened == 'abc')
        check('Escape cancels the edit and keeps the value', not dgv.IsCurrentCellInEditMode and str(dgv.GetCellText(0, 1)) == '0')
        # Copy (Ctrl+C) two rows, paste (Ctrl+V) at the new row: the original adds rows through the BindingSource.
        renderer.guard(lambda: dgv.SelectByUser(Array[Int32]([0, 0, 1, 1]), Array[Int32]([0, 1, 0, 1]), 0, 0))
        renderer.guard(lambda: dgv.RaiseKeyDown(Keys.Control | Keys.C))
        copied = str(Clipboard.GetText())
        report['forms']['FrmAmplitude']['copied'] = copied
        check('Ctrl+C copies the selected cells (tab separated, no header)', copied == '0\t0\r\n1\t1')
        renderer.guard(lambda: dgv.SelectByUser(Array[Int32]([2]), Array[Int32]([0]), 2, 0))
        Clipboard.SetText('2\t0.5\n3 0')
        renderer.guard(lambda: dgv.RaiseKeyDown(Keys.Control | Keys.V))
        renderer.flush()
        check('Ctrl+V pastes rows below the table (space or tab separated)', dgv.RowCount == 5 and str(dgv.GetCellText(3, 0)) == '3' and str(dgv.GetCellText(2, 1)) == '0.5')
        # Plot (Ctrl+P): the original FrmDiagramView with ZedGraph curves.
        renderer.guard(lambda: dgv.SelectByUser(Array[Int32]([0, 0, 1, 1, 2, 2, 3, 3]), Array[Int32]([0, 1, 0, 1, 0, 1, 0, 1]), 0, 0))
        renderer.guard(lambda: dgv.RaiseKeyDown(Keys.Control | Keys.P))
        renderer.flush()
        from System.Windows.Forms import Form
        plot = next((f for f in Form.OpenForms if type(f).__name__ == 'FrmDiagramView' and f.Visible), None)
        check('Ctrl+P shows the original FrmDiagramView', plot is not None and str(plot.Text) == 'Plot')
        from ZedGraph import ZedGraphControl
        pane = next(x for x in walk(plot) if isinstance(x, ZedGraphControl)).GraphPane
        curve = pane.CurveList[0]
        report['forms']['FrmDiagramView'] = {'x': list(curve.X), 'y': list(curve.Y), 'xTitle': str(pane.XAxis.Title.Text), 'yTitle': str(pane.YAxis.Title.Text),
                                             'size': [plot.ClientSize.Width, plot.ClientSize.Height]}
        check('plot curve from the selected rows', list(curve.X) == [0, 1, 2, 3] and list(curve.Y) == [0, 1, 0.5, 0])
        check('plot axes from the column headers; StartPlotAtZero', str(pane.XAxis.Title.Text).startswith('Time [s]') and not pane.XAxis.Scale.MinAuto and pane.XAxis.Scale.Min == 0)
        plot_window = form_window(plot)
        check('plot window drawn beside the form', plot_window is not None and plot_window.isVisible())
        snapshot('FrmDiagramView', plot)
        renderer.guard(plot.CloseByUser)
        renderer.flush()
        check('closing the plot hides it (original FormClosing)', not plot.Visible)
        # Context menu items of the original cmsCopyPaste, with the designer image of Plot from the .resx.
        strip = dgv.ContextMenuStrip
        texts = [str(i.Text) for i in strip.Items]
        check('context menu: Cut / Copy / Paste / Plot', texts[0].startswith('Cut') and texts[-1].startswith('Plot') and len(texts) == 5)
        check('Plot menu image read from DataGridViewCopyPaste.resx', renderer.icon(strip.Items[4].Image) is not None)
        snapshot('FrmAmplitude', form)
        by_name(form, 'btnOK').RaiseClick()
        renderer.flush()
        amplitudes = [str(n) for n in c.GetAmplitudeNames()]
        check('original OnApply created the amplitude', len(amplitudes) == 1)
        amplitude = c.GetAmplitude(amplitudes[0])
        report['forms']['FrmAmplitude']['created'] = [list(p) for p in amplitude.TimeAmplitude]
        check('amplitude holds the edited and pasted points', [list(p) for p in amplitude.TimeAmplitude] == [[0, 0], [1, 1], [2, 0.5], [3, 0]])
        window.show_original_form('EditAmplitude', amplitudes[0])
        form = visible_form()
        dgv = next(x for x in walk(form) if isinstance(x, DataGridView))
        check('edit shows the amplitude data points', str(form.Text) == 'Edit Amplitude: ' + amplitudes[0] and dgv.RowCount == 5)
        renderer.guard(lambda: dgv.SelectByUser(Array[Int32]([]), Array[Int32]([]), Array[Int32]([3]), 3, 0))
        renderer.guard(lambda: dgv.RaiseKeyDown(Keys.Control | Keys.C))
        check('a row selected through its header copies with the header text (EnableWithAutoHeaderText)',
              str(Clipboard.GetText()) == '\tTime [s]\nFrequency [Hz]\tAmplitude\n[/]\r\n\t3\t0')
        renderer.guard(lambda: dgv.RaiseKeyDown(Keys.Delete))
        renderer.flush()
        check('Delete removes the row selected through its header', dgv.RowCount == 4)
        by_name(form, 'btnOK').RaiseClick()
        renderer.flush()
        check('edit replaces the amplitude (Binding_ListChanged)', len(list(c.GetAmplitude(amplitudes[0]).TimeAmplitude)) == 3)

    def geometry_catalogue():
        import os
        if not os.environ.get('PREPOMAXX_GMSH_LIBRARY'):
            report.setdefault('pending', []).append('geometry forms: no native CAD profile supplied')
            report['success'] = True
            return
        from CaeModel import ModelSpaceEnum
        from CaeGlobals import UnitSystemType
        c.New()
        c.SetNewModelPropertiesCommand(ModelSpaceEnum.ThreeD, UnitSystemType.MM_TON_S_C)
        window.refresh()
        window.import_path(str(FIXTURE), True)

    def geometry_ready():
        import os
        if not os.environ.get('PREPOMAXX_GMSH_LIBRARY'):
            return
        if not ready():
            return False
        catalogue(GEOMETRY_FORMS, 'geometry')
        report['success'] = True

    steps = iter([import_model, step_form, bc_form, model_catalogue, edit_mode, data_grid_forms, geometry_catalogue, geometry_ready])
    current = [None]
    timer = QtCore.QTimer(window)

    def tick():
        try:
            if time.monotonic() - started > 300:
                raise TimeoutError('forms GUI workflow timed out')
            if current[0] is None:
                current[0] = next(steps)
            if current[0]() is not False:
                current[0] = None
        except StopIteration:
            timer.stop()
            finish()
        except Exception as error:
            report.update(error=str(error), traceback=traceback.format_exc())
            timer.stop()
            finish()

    def finish():
        if host is not None:
            host.CloseAllForms()
        (output / 'forms-gui.json').write_text(json.dumps(report, indent=2) + '\n')
        window.dirty = False
        window.close()
        app.exit(0 if report['success'] else 1)
    timer.timeout.connect(tick)
    timer.start(50)

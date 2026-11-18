"""FrmMain form hosting for the original forms: the generated OriginalFormHost (FrmMain members verbatim)
plus the main-window hooks it needs, the original picking path while a form is open, and the
create/edit entry points the menus and the model tree call."""
from PyQt6 import QtCore, QtWidgets
from System import Array, Int32, Double, String, Boolean, Func, Action
from System.Drawing import Point

from original_forms import OriginalFormRenderer

# Families and tools whose original form is compiled whole: (create entry, edit entry) in FrmMain.
FAMILY_ENTRIES = {
    'Node sets': ('tsmiCreateNodeSet_Click', 'EditNodeSet'),
    'Element sets': ('tsmiCreateElementSet_Click', 'EditElementSet'),
    'Surfaces': ('tsmiCreateSurface_Click', 'EditSurface'),
    'Reference points': ('tsmiCreateModelReferencePoint_Click', 'EditModelReferencePoint'),
    'Coordinate systems': ('tsmiCreateModelCoordinateSystem_Click', 'EditModelCoordinateSystem'),
    'Material orientations': ('CreateMaterialOrientation', 'EditMaterialOrientation'),
    'Sections': ('CreateSection', 'EditSection'),
    'Constraints': ('tsmiCreateConstraint_Click', 'EditConstraint'),
    'Contact pairs': ('tsmiCreateContactPair_Click', 'EditContactPair'),
    'Initial conditions': ('CreateInitialCondition', 'EditInitialCondition'),
    'Steps': ('tsmiCreateStep_Click', 'EditStep'),
    'History outputs': ('CreateHistoryOutput', 'EditHistoryOutput'),
    'Field outputs': ('CreateFieldOutput', 'EditFieldOutput'),
    'Boundary conditions': ('CreateBoundaryCondition', 'EditBoundaryCondition'),
    'Loads': ('CreateLoad', 'EditLoad'),
    'Defined fields': ('CreateDefinedField', 'EditDefinedField'),
    'Model properties': ('EditModel', 'EditModel'),
    'Mesh setup': ('CreateMeshSetupItem', 'EditMeshSetupItem'),
    'Parts': (None, 'EditModelPart'),
    'Geometry parts': (None, 'EditGeometryPart'),
    'Result parts': (None, 'EditResultPart'),
    'Result reference points': ('tsmiCreateResultReferencePoint_Click', 'EditResultReferencePoint'),
    'Result coordinate systems': ('tsmiCreateResultCoordinateSystem_Click', 'EditResultCoordinateSystem'),
    'Distributions': ('tsmiCreateDistribution_Click', 'EditDistribution'),
    'Amplitudes': ('tsmiCreateAmplitude_Click', 'EditAmplitude'),
    'Result fields': ('tsmiCreateResultFieldOutput_Click', 'EditResultFieldOutput'),
    'Result histories': ('tsmiCreateResultHistoryOutput_Click', 'EditResultHistoryOutput'),
    # Child-window forms (C11)
    'Materials': ('tsmiCreateMaterial_Click', 'EditMaterial'),
    'Surface interactions': ('tsmiCreateSurfaceInteraction_Click', 'EditSurfaceInteraction'),
    'Solution controls': (None, 'EditStepControls'),
    'Jobs': ('tsmiCreateAnalysis_Click', 'EditAnalysis'),
}
TOOL_ENTRIES = {
    'Split solid': ('CreateSplitSolid', None), 'Split shell': ('CreateSplitShell', None),
    'Offset faces': ('CreateOffsetFace', None), 'Repair geometry': ('CreateRepairGeometry', None),
    'Split periodic faces': ('CreateSplitPeriodicFaces', None),
    'FlipNormal': ('CreateSurfaceOperation', 'FlipNormal'), 'Defeature': ('CreateSurfaceOperation', 'Defeature'),
    'DeleteCadFaces': ('CreateSurfaceOperation', 'DeleteCadFaces'), 'DeleteStlFaces': ('CreateSurfaceOperation', 'DeleteStlFaces'),
    'FuseFaces': ('CreateSurfaceOperation', 'FuseFaces'),
    'Boundary layer': ('CreateBoundaryLayer', None), 'Remesh elements': ('RemeshElements', None),
    'Thicken shell mesh': ('ThickenShellMesh', None), 'Split mesh using surface': ('tsmiSplitPartMeshUsingSurface_Click', None),
    'Merge coincident nodes': ('MergeCoincidentNodes', None), 'Element quality': ('ElementQuality', None),
}
TRANSFORMS = ('Translate', 'Rotate', 'Mirror', 'Scale')


class StateTask:
    """FrmMain working state (SetStateWorking .. SetStateReady) seen by the workbench as a running operation."""

    def __init__(self, text):
        self.text = text
        self.IsCompleted = False
        self.IsCanceled = False
        self.IsFaulted = False
        self.Exception = None


class OriginalFormEditor:
    """The workbench's active-editor handle for a visible original form (FrmMain shows one at a time)."""

    def __init__(self, window, form):
        self.window, self.form = window, form

    def qt(self):
        return self.window.form_renderer.windows.get(self.form)

    def windowTitle(self):
        return str(self.form.Text)

    def raise_(self):
        w = self.qt()
        if w is not None:
            w.raise_()

    def activateWindow(self):
        w = self.qt()
        if w is not None:
            w.activateWindow()

    def setEnabled(self, value):
        self.form.Enabled = bool(value)
        self.window.form_renderer.sync_soon()

    def reject(self):
        # FrmProperties.btnCancel_Click (HideOrClose); forms without a Cancel button close as by the window button.
        from System.Windows.Forms import Button
        cancel = next((c for c in self.form.Controls if isinstance(c, Button) and str(c.Name) == 'btnCancel'), None)
        if cancel is not None and cancel.Visible:
            cancel.RaiseClick()
        else:
            self.form.CloseByUser()
        self.window.form_renderer.flush()


class OriginalFormHostWorkbench:
    def build_original_forms(self):
        from PrePoMax import OriginalFormHost
        self.form_host = OriginalFormHost(self.controller)
        h = self.form_host
        self.form_hooks = [
            Func[String, Boolean, Boolean](self.form_state_working),
            Action[String](self.form_state_ready),
            Action[Boolean](self.form_menus_active),
            Action(self.form_highlight_from_tree),
            Func[Boolean](lambda: False),
        ]
        h.StateWorkingHandler, h.StateReadyHandler, h.MenusActiveHandler, h.HighlightFromTreeHandler, h.CommitViewportEditHandler = self.form_hooks
        from PrePoMax import CaptureViewportProperties
        # FrmMain.CaptureViewport (port of the original member, results_workbench.capture_viewport) and
        # FrmMain.WriteDataToOutput.
        self.form_capture = Func[CaptureViewportProperties, Boolean](lambda properties: bool(self.capture_viewport(properties)))
        h.CaptureViewportHandler = self.form_capture
        self.form_output = Action[String](lambda text: self.write_output(str(text)))
        h.OutputHandler = self.form_output
        self.form_animation_menus_hook = Action[Boolean](self.form_animation_menus)
        h.AnimationMenusHandler = self.form_animation_menus_hook
        # FrmMain members the child-window forms call back that belong to the main window.
        from System import Object
        self.form_main_window = Func[String, Array[Object], Object](self.form_main_window_member)
        h.MainWindowHandler = self.form_main_window
        # WindowsFormsSynchronizationContext equivalent: original async handlers resume on this thread.
        from PrePoMaxX.UI import UiSynchronizationContext
        self.ui_post = Action[Action](lambda action: self.dispatcher.pending.put((lambda: self.guard(action.Invoke), None, None)))
        self.ui_context = UiSynchronizationContext.Create(self.ui_post)
        # Control.Invoke/BeginInvoke of the original forms marshal to this thread (WinForms message loop).
        from System.Windows.Forms import Control
        Control.SetUiThreadContext(self.ui_context)
        self.form_renderer = OriginalFormRenderer(self, h)
        self.sync_form_host_location()

    def in_ui_context(self, action):
        """Runs original form code with the UI synchronization context current (WinForms message dispatch)."""
        from System.Threading import SynchronizationContext
        previous = SynchronizationContext.Current
        SynchronizationContext.SetSynchronizationContext(self.ui_context)
        try:
            return action()
        finally:
            SynchronizationContext.SetSynchronizationContext(previous)

    # FrmMain hooks --------------------------------------------------------------------------------------------------------
    def form_main_window_member(self, member, arguments):
        """FrmMain members of the main window (viewport, results opening, settings/automation, annotations, tree)."""
        member, args = str(member), list(arguments)
        if member == 'Clear3DSelection':
            self.scene.show_selection([])
            self.render()
        elif member == 'ResultsAnalysis':
            # FrmMain.ResultsAnalysis: OpenResultsCommand (OpenAnalysisResults with CloseMonitorWindow), then the
            # history postprocessing when the results were accepted.
            def opened():
                self.result_opened()
                self.in_ui_context(lambda: self.form_host.Invoke('CloseMonitorWindow'))
                if self.session.Presentation.LastOpenResultsAccepted:
                    self.controller.RunHistoryPostprocessing(None)
                    self.refresh()
            self.run_operation(self.results.OpenJob(str(args[0])), opened)
        elif member == 'UpdateSettings':
            # FrmMain.UpdateSettings: the settings, then the automation server follows its port.
            self.controller.Settings = args[0]
            self.apply_preferences()
            self.persist_preferences()
            self.refresh()
        elif member == 'SetAutomationAccessToken':
            token = str(args[0] or '')
            automation = self.application.Automation
            running = bool(automation.IsRunning)
            if running:
                automation.Stop()
            self.controller.SaveAutomationAccessToken(token)
            if not token:
                self.write_output('The access token of the automation server was cleared, so the server cannot run until a new one is generated.')
                return None
            self.write_output('The access token of the automation server was set.')
            if running:
                automation.Start()
        elif member == 'GetRunningAutomationEndpointUrl':
            automation = self.application.Automation
            return String(str(automation.EndpointUrl or '') if automation.IsRunning else '')
        elif member == 'tsbRemoveAnnotations_Click':
            self.remove_annotations()
        elif member == 'PythonPanelShowFind':
            from System import Boolean
            return Boolean(False)
        elif member == 'IntersectSelectionWithList':
            entities = list(args[0])
            selected = [i.data(0, QtCore.Qt.ItemDataRole.UserRole) for i in self.tree.selectedItems()]
            names = [str(e.Name) for e in selected if e is not None and not getattr(e, 'Group', False)]
            return Array[String]([str(x.Name) for x in entities if str(x.Name) in names])
        else:
            raise NotImplementedError('FrmMain member not hosted: ' + member)
        return None

    def form_state_working(self, text, show_cancel_button):
        """FrmMain.SetStateWorking: only from the ready state; the workbench's operation lock and status apply."""
        if getattr(self, 'operation_task', None) is not None:
            return False
        self.form_state = StateTask(str(text))
        self.run_operation(self.form_state)
        if not show_cancel_button:
            self.cancel_operation.hide()
        return True

    def form_state_ready(self, text):
        """FrmMain.SetStateReady: ends the state started with the same text."""
        state = getattr(self, 'form_state', None)
        if state is not None and state.text == str(text):
            state.IsCompleted = True
            self.form_state = None

    def form_menus_active(self, active):
        # The visible item form is the workbench's active editor (blocks the conflicting actions).
        form = self.form_host.ActiveItemForm
        self.active_editor = None if active or form is None else OriginalFormEditor(self, form)
        # FrmMain.SetMenuAndToolStripVisibilityByItemForm: tree mouse, main menu and file tool strip off while
        # an item form is open; symbols tool strip disabled.
        self.tree.setEnabled(bool(active))
        self.menuBar().setEnabled(bool(active))
        strips = getattr(self, 'original_strips', {})
        for name in ('tsFile', 'tsSymbols'):
            if name in strips:
                strips[name].setEnabled(bool(active))
        if active:
            QtCore.QTimer.singleShot(0, lambda: self.guard(self.refresh))

    def form_animation_menus(self, active):
        """FrmMain.SetMenuAndToolStripVisibilityByAnimation: tree and main-menu mouse, file/symbol/deformation/results
        tool strips off while the original FrmAnimation runs."""
        self.tree.setEnabled(bool(active))
        self.menuBar().setEnabled(bool(active))
        strips = getattr(self, 'original_strips', {})
        for name in ('tsFile', 'tsSymbols', 'tsResultDeformation', 'tsResults'):
            if name in strips:
                strips[name].setEnabled(bool(active))
        if active:
            QtCore.QTimer.singleShot(0, lambda: self.guard(self.refresh))

    def form_highlight_from_tree(self):
        if hasattr(self, 'tree_selection_changed'):
            self.tree_selection_changed()

    def sync_form_host_location(self):
        position = self.pos()
        self.form_host.Location = Point(position.x(), position.y())

    # Presentation events forwarded by the headless FrmMain ---------------------------------------------------------------
    def form_presentation(self, name, arguments):
        if not hasattr(self, 'form_host'):
            return
        if name == 'SelectionChanged':
            ids = arguments[0] if len(arguments) else None
            self.form_host.SelectionChanged(ids)
        elif name == 'UpdateHighlight':
            self.form_host.UpdateHighlight()
        elif name == 'CloseAllForms':
            self.form_host.CloseAllForms()
        elif name == 'UpdateAnalysisProgress':
            # FrmMain.UpdateAnalysisProgress: the original FrmMonitor follows the job (and the nonpositive
            # Jacobian element set of a failed job).
            self.in_ui_context(lambda: self.form_host.Invoke('UpdateAnalysisProgress', str(arguments[0]), arguments[1]))
        self.form_renderer.sync_soon()

    # Entry points ---------------------------------------------------------------------------------------------------------
    def original_form_open(self):
        return self.form_host.ActiveItemForm is not None if hasattr(self, 'form_host') else False

    def show_original_form(self, method, *arguments):
        """Calls the FrmMain create/edit member by its original name."""
        self.sync_form_host_location()
        self.in_ui_context(lambda: self.form_host.Invoke(method, *arguments))
        self.form_renderer.flush()

    def run_original_entry(self, method, step=None, name=None, parts=None, operation=None):
        """Calls a FrmMain entry point (menu handlers without a family) with its original parameters."""
        from System import Array, String
        self.sync_form_host_location()
        self.in_ui_context(lambda: self.form_host.InvokeEntry(method, step, name, None if parts is None else Array[String](list(parts)), operation))
        self.form_renderer.flush()

    def open_original(self, family, step=None, name=None, parts=None):
        """Opens the original form of a family/tool through its FrmMain entry point; False when the family's
        form is not compiled yet (the caller keeps its own dialog)."""
        from System import Array, String
        from PrePoMax import ViewGeometryModelResults
        operation = None
        if family == 'Parts' and self.controller.CurrentView == ViewGeometryModelResults.Results:
            family = 'Result parts'
        elif family == 'Parts' and self.controller.CurrentView == ViewGeometryModelResults.Geometry:
            family = 'Geometry parts'
        if family in FAMILY_ENTRIES:
            create, edit = FAMILY_ENTRIES[family]
            # Solution controls are edited per step (FrmMain.EditStepControls(stepName)).
            method = edit if name is not None or (family == 'Solution controls' and step is not None) else create
        elif family in TOOL_ENTRIES:
            method, operation = TOOL_ENTRIES[family]
        elif family in TRANSFORMS:
            geometry = self.controller.CurrentView == ViewGeometryModelResults.Geometry
            method = family + ('GeometryParts' if geometry else 'ModelParts')
        else:
            return False
        if method is None:
            return False
        if self.original_form_open():
            window = self.form_renderer.windows.get(self.form_host.ActiveItemForm)
            if window is not None:
                window.raise_()
                window.activateWindow()
            return True
        self.sync_form_host_location()
        self.in_ui_context(lambda: self.form_host.InvokeEntry(method, step, name, None if parts is None else Array[String](list(parts)), operation))
        self.form_renderer.flush()
        return True

    # Original picking (FrmMain._vtk_SelectPointOrArea) --------------------------------------------------------------------
    def original_pick(self, point, direction, planes, completely_inside, operation, part_names):
        c = self.controller
        c.SelectPointOrArea(None if point is None else Array[Double](point), Array[Double](direction),
                            None if planes is None else Array[Array[Double]]([Array[Double](p) for p in planes]),
                            bool(completely_inside), operation, None if part_names is None else Array[String](part_names))
        ids = c.GetSelectionIds()
        self.form_host.PickedIds(ids)
        self.form_host.SelectionChanged(ids)
        self.selected = list(ids) if ids is not None else []
        self.scene.show_selection(self.session.Presentation.SelectionActors)
        self.render()
        self.form_renderer.flush()

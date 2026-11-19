"""The original PrePoMax main window drawn by Qt (M2): FrmMain, compiled whole, on the headless WinForms model.

The original Program constructs FrmMain and calls Application.Run(mainForm); with the Qt renderer attached
(X/App/PrePoMax/XRuntime.cs) Run executes this script with `form` = the FrmMain instance. FrmMain is shown through
the same generic renderer as every other original form (original_forms.py): the WinForms model lays out its
controls and each control is mirrored by a Qt widget at its bounds. The main window adds what only FrmMain has:
its menu strip, tool strips and status strip (Qt menus, tool bars and labels whose items are the original
ToolStripItems), and the original vtkControl in a native Qt widget (original_viewport.py). Every user input goes to
the original control (PerformClick, SelectedIndex, the key hook, ...); nothing of FrmMain is reimplemented here.
"""
import queue
import sys
import traceback

import clr
for _assembly in ('CaeGlobals', 'UserControls', 'vtkControl', 'PrePoMax', 'PrePoMaxX.FormsCompat'):
    clr.AddReference(_assembly)
import System
from System import Action, Func, String, Array, Object
from System.Drawing import Size, Point
from System.Windows.Forms import (Application, Form, Control, ToolStrip, MenuStrip, StatusStrip, ToolStripItem,
                                  ToolStripSeparator, ToolStripButton, ToolStripLabel, ToolStripComboBox,
                                  ToolStripTextBox, ToolStripDropDownItem, ToolStripMenuItem, ToolStripProgressBar,
                                  ToolStripStatusLabel, ToolStripItemDisplayStyle, ToolkitSynchronizationContext,
                                  IWin32Window, MessageBoxButtons, MessageBoxIcon, DialogResult, LowLevelKeyboardHook,
                                  Keys, ToolStripDropDownCloseReason)
from CaeGlobals import MessageBoxes, MessageBoxModeEnum
from PyQt6 import QtCore, QtGui, QtWidgets

import original_forms as of
import original_controls as oc


# Qt key -> WinForms key of a menu shortcut (ToolStripMenuItem.ShortcutKeys)
def qt_shortcut(keys):
    value = int(keys)
    if value == 0:
        return None
    code = value & 0xFFFF
    sequence = ''
    if value & int(Keys.Control):
        sequence += 'Ctrl+'
    if value & int(Keys.Shift):
        sequence += 'Shift+'
    if value & int(Keys.Alt):
        sequence += 'Alt+'
    name = System.Enum.GetName(Keys, System.Enum.ToObject(Keys, code))
    if name is None:
        return None
    name = {'Delete': 'Del', 'Return': 'Return', 'Escape': 'Esc', 'Oemplus': '+', 'OemMinus': '-', 'Next': 'PgDown',
            'Prior': 'PgUp'}.get(str(name), str(name))
    if len(name) == 2 and name[0] == 'D' and name[1].isdigit():
        name = name[1]
    return QtGui.QKeySequence(sequence + name)


class StripWidget(QtWidgets.QWidget):
    """A MenuStrip, ToolStrip or StatusStrip: its items as Qt actions and widgets, rebuilt when the item list changes
    and updated when an item changes (ToolStripItem notifies its strip)."""

    def __init__(self, window, strip, parent):
        super().__init__(parent)
        self.window, self.strip = window, strip
        self.renderer = window.renderer
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        if isinstance(strip, MenuStrip):
            self.bar = QtWidgets.QMenuBar(self)
            self.bar.setNativeMenuBar(False)
        else:
            self.bar = QtWidgets.QToolBar(self)
            self.bar.setIconSize(QtCore.QSize(16, 16))
            self.bar.setMovable(False)
            self.bar.setFloatable(False)
        layout.addWidget(self.bar)
        self.items = []
        self.entries = {}
        self.rebuild()

    def rebuild(self):
        items = list(self.strip.Items)
        if items != self.items:
            self.bar.clear()
            self.entries = {}
            self.items = items
            for item in items:
                self.entries[item] = self.add(item)
        self.update_items()

    def add(self, item):
        r = self.renderer
        if isinstance(item, ToolStripSeparator):
            return self.bar.addSeparator()
        if isinstance(self.strip, MenuStrip) and isinstance(item, ToolStripDropDownItem):
            menu = MenuWidget(self.window, item, self.bar)
            action = self.bar.addMenu(menu)
            return action
        if isinstance(item, ToolStripComboBox):
            combo = QtWidgets.QComboBox()
            combo.item = item
            combo.activated.connect(lambda index, i=item: r.input(lambda: i.ComboBox.RaiseSelectionChangeCommitted(index)))
            action = self.bar.addWidget(combo)
            action.widget_ = combo
            return action
        if isinstance(item, ToolStripTextBox):
            edit = QtWidgets.QLineEdit()
            edit.editingFinished.connect(lambda i=item, e=edit: r.input(lambda: i.TextBox.SetUserText(e.text())))
            action = self.bar.addWidget(edit)
            action.widget_ = edit
            return action
        if isinstance(item, ToolStripProgressBar):
            bar = QtWidgets.QProgressBar()
            bar.setMaximumWidth(max(60, item.Size.Width))
            bar.setTextVisible(False)
            action = self.bar.addWidget(bar)
            action.widget_ = bar
            return action
        if isinstance(item, ToolStripLabel) and not isinstance(item, ToolStripButton):
            label = QtWidgets.QLabel()
            label.setContentsMargins(4, 0, 4, 0)
            if isinstance(item, ToolStripStatusLabel) and item.Spring:
                label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
            label.mousePressEvent = lambda event, i=item: r.input(i.PerformClick)
            action = self.bar.addWidget(label)
            action.widget_ = label
            return action
        action = QtGui.QAction(self.bar)
        action.triggered.connect(lambda checked=False, i=item: r.input(i.PerformClick))
        if isinstance(item, ToolStripDropDownItem) and item.HasDropDownItems:
            action.setMenu(MenuWidget(self.window, item, self.bar))
        self.bar.addAction(action)
        return action

    def update_items(self):
        for item, action in self.entries.items():
            action.setVisible(bool(item.Visible))
            widget = getattr(action, 'widget_', None)
            if isinstance(widget, QtWidgets.QComboBox):
                self.update_combo(item, widget)
            elif isinstance(widget, QtWidgets.QLineEdit):
                if not widget.hasFocus() and widget.text() != str(item.Text):
                    widget.setText(str(item.Text))
                widget.setEnabled(bool(item.Enabled))
            elif isinstance(widget, QtWidgets.QProgressBar):
                widget.setRange(int(item.Minimum), int(item.Maximum))
                widget.setValue(int(item.Value))
            elif isinstance(widget, QtWidgets.QLabel):
                widget.setText(str(item.Text))
                widget.setEnabled(bool(item.Enabled))
            elif isinstance(item, ToolStripSeparator):
                continue
            else:
                text = of.visible_name(str(item.Text))
                icon = self.renderer.icon(item.Image)
                style = item.DisplayStyle
                action.setText(text)
                action.setToolTip(str(item.ToolTipText or text))
                if icon is not None and style != ToolStripItemDisplayStyle.Text:
                    action.setIcon(icon)
                action.setEnabled(bool(item.Enabled))
                checkable = isinstance(item, (ToolStripButton, ToolStripMenuItem)) and (item.CheckOnClick or item.Checked)
                action.setCheckable(bool(checkable))
                if checkable:
                    action.setChecked(bool(item.Checked))

    def update_combo(self, item, widget):
        texts = [str(x) for x in item.Items]
        widget.blockSignals(True)
        try:
            if [widget.itemText(i) for i in range(widget.count())] != texts:
                widget.clear()
                widget.addItems(texts)
            if widget.currentIndex() != item.SelectedIndex:
                widget.setCurrentIndex(int(item.SelectedIndex))
            widget.setEnabled(bool(item.Enabled))
            width = max(int(item.Size.Width), 40)
            widget.setFixedWidth(width)
        finally:
            widget.blockSignals(False)


class MenuWidget(QtWidgets.QMenu):
    """The drop-down of a ToolStripDropDownItem: built when it opens, after DropDownOpening (the original handlers
    enable and fill their items there), from the item's DropDownItems."""

    def __init__(self, window, item, parent):
        super().__init__(of.visible_name(str(item.Text)), parent)
        self.window, self.item = window, item
        self.renderer = window.renderer
        self.aboutToShow.connect(self.opening)
        self.aboutToHide.connect(lambda: self.renderer.input(self.item.RaiseDropDownClosed))
        # A menu bar shows only menus that have actions; the real items are added when it opens
        self.addAction('')

    def opening(self):
        self.renderer.input(self.item.RaiseDropDownOpening)
        self.clear()
        for child in self.item.DropDownItems:
            if not child.Visible:
                continue
            if isinstance(child, ToolStripSeparator):
                self.addSeparator()
                continue
            text = of.visible_name(str(child.Text))
            if isinstance(child, ToolStripDropDownItem) and child.HasDropDownItems:
                sub = MenuWidget(self.window, child, self)
                sub.setEnabled(bool(child.Enabled))
                icon = self.renderer.icon(child.Image)
                if icon is not None:
                    sub.setIcon(icon)
                self.addMenu(sub)
                continue
            action = self.addAction(text)
            icon = self.renderer.icon(child.Image)
            if icon is not None:
                action.setIcon(icon)
            action.setEnabled(bool(child.Enabled))
            if isinstance(child, ToolStripMenuItem):
                action.setCheckable(bool(child.CheckOnClick or child.Checked))
                action.setChecked(bool(child.Checked))
                shortcut = qt_shortcut(child.ShortcutKeys)
                if shortcut is not None:
                    action.setShortcut(shortcut)
                    action.setShortcutContext(QtCore.Qt.ShortcutContext.WidgetShortcut)
            action.triggered.connect(lambda checked=False, i=child: self.renderer.input(i.PerformClick))


class MainFormWindow(of.FormWindow):
    """FrmMain: a top-level window whose controls the generic form renderer builds and lays out."""

    def __init__(self, renderer, form, ui_context):
        QtWidgets.QDialog.__init__(self, None)
        self.setWindowFlags(QtCore.Qt.WindowType.Window | QtCore.Qt.WindowType.WindowMinMaxButtonsHint |
                            QtCore.Qt.WindowType.WindowCloseButtonHint)
        self.renderer, self.form, self.ui_context = renderer, form, ui_context
        self.setFont(of.original_font())
        self.widgets = {}
        self.syncing = False
        self.viewports = []
        renderer.main_window = self
        self.build(form, self)
        self.shortcuts = []
        self.install_shortcuts()
        self.sync()

    def in_ui_context(self, action):
        from System.Threading import SynchronizationContext
        previous = SynchronizationContext.Current
        SynchronizationContext.SetSynchronizationContext(self.ui_context)
        try:
            return action()
        finally:
            SynchronizationContext.SetSynchronizationContext(previous)

    def create(self, control, parent):
        import vtkControl as original
        if isinstance(control, original.vtkControl):
            from original_viewport import OriginalViewport
            viewport = OriginalViewport(parent, self.renderer.post, control=control)
            self.viewports.append(viewport)
            return viewport
        if isinstance(control, ToolStrip):
            return StripWidget(self, control, parent)
        return super().create(control, parent)

    def sync(self):
        # The window system and the user size the main window and the form follows it (resizeEvent); the window is
        # never sized from the form, or the two would grow each other by the frame
        self.syncing = True
        try:
            self.setWindowTitle(str(self.form.Text))
            self.setEnabled(bool(self.form.Enabled))
            for control, widget in list(self.widgets.items()):
                self.sync_control(control, widget)
        finally:
            self.syncing = False

    def refresh_control(self, control):
        widget = self.widgets.get(control)
        if isinstance(widget, StripWidget):
            widget.rebuild()
            return
        super().refresh_control(control)

    def install_shortcuts(self):
        """The menu shortcuts (ToolStripMenuItem.ShortcutKeys) work while the menus are closed, as in WinForms."""
        def walk(items):
            for item in items:
                if isinstance(item, ToolStripMenuItem):
                    yield item
                if isinstance(item, ToolStripDropDownItem):
                    yield from walk(item.DropDownItems)
        menu = self.form.MainMenuStrip
        if menu is None:
            return
        for item in walk(menu.Items):
            sequence = qt_shortcut(item.ShortcutKeys)
            if sequence is None:
                continue
            shortcut = QtGui.QShortcut(sequence, self)
            shortcut.activated.connect(lambda i=item: self.renderer.input(i.PerformClick) if i.Enabled else None)
            self.shortcuts.append(shortcut)

    def resizeEvent(self, event):
        QtWidgets.QDialog.resizeEvent(self, event)
        # The main window is resized by the user and the window system alike; the form follows the window
        if not self.syncing:
            size = event.size()
            self.renderer.input(lambda: setattr(self.form, 'ClientSize', Size(size.width(), size.height())))
            self.renderer.sync_soon()

    def closeEvent(self, event):
        if self.form.Visible:
            self.renderer.input(self.form.CloseByUser)
        if self.form.Visible:
            event.ignore()
            return
        for viewport in self.viewports:
            viewport.detach()
        event.accept()
        QtWidgets.QApplication.instance().quit()

    def reject(self):
        pass  # Escape belongs to FrmMain's key handling, not to closing the window

    def keyPressEvent(self, event):
        QtWidgets.QWidget.keyPressEvent(self, event)


class KeyHook(QtCore.QObject):
    """The application's keys for the original low-level keyboard hook (FrmMain's KeyboardHook)."""

    def eventFilter(self, obj, event):
        kind = event.type()
        if kind in (QtCore.QEvent.Type.KeyPress, QtCore.QEvent.Type.KeyRelease) and not event.isAutoRepeat():
            keys = oc.winforms_keys(event)
            if keys is not None:
                code = System.Enum.ToObject(Keys, int(keys) & 0xFFFF)
                LowLevelKeyboardHook.Raise(code, kind == QtCore.QEvent.Type.KeyPress)
        return False


PROBE_PROMPTS = None  # unattended checks: the message boxes shown, answered with their first button
PROBE_ANSWER = [None]  # ... or with this answer when the probe sets one that the box offers


def prompt(window, owner, text, caption, buttons, icon):
    mapping = {str(MessageBoxButtons.OK): [('OK', DialogResult.OK)],
               str(MessageBoxButtons.OKCancel): [('OK', DialogResult.OK), ('Cancel', DialogResult.Cancel)],
               str(MessageBoxButtons.YesNo): [('Yes', DialogResult.Yes), ('No', DialogResult.No)],
               str(MessageBoxButtons.YesNoCancel): [('Yes', DialogResult.Yes), ('No', DialogResult.No), ('Cancel', DialogResult.Cancel)],
               str(MessageBoxButtons.RetryCancel): [('Retry', DialogResult.Retry), ('Cancel', DialogResult.Cancel)],
               str(MessageBoxButtons.AbortRetryIgnore): [('Abort', DialogResult.Abort), ('Retry', DialogResult.Retry), ('Ignore', DialogResult.Ignore)]}
    if PROBE_PROMPTS is not None:
        PROBE_PROMPTS.append(str(caption) + ': ' + str(text))
        offered = [value for _, value in mapping[str(buttons)]]
        return PROBE_ANSWER[0] if PROBE_ANSWER[0] in offered else offered[0]
    box = QtWidgets.QMessageBox(window)
    box.setWindowTitle(str(caption or 'PrePoMax'))
    box.setText(str(text))
    icons = {str(MessageBoxIcon.Error): QtWidgets.QMessageBox.Icon.Critical,
             str(MessageBoxIcon.Warning): QtWidgets.QMessageBox.Icon.Warning,
             str(MessageBoxIcon.Question): QtWidgets.QMessageBox.Icon.Question,
             str(MessageBoxIcon.Information): QtWidgets.QMessageBox.Icon.Information}
    box.setIcon(icons.get(str(icon), QtWidgets.QMessageBox.Icon.NoIcon))
    choices = mapping.get(str(buttons))
    if choices is None:
        raise ValueError('Unhandled message box buttons: ' + str(buttons))
    answers = {}
    for label, value in choices:
        role = QtWidgets.QMessageBox.ButtonRole.RejectRole if label in ('Cancel', 'No') else QtWidgets.QMessageBox.ButtonRole.AcceptRole
        answers[box.addButton(label, role)] = value
    box.exec()
    return answers.get(box.clickedButton(), DialogResult.Cancel)


class EventLoopDrain(QtCore.QObject):
    """The WinForms message queue on the Qt event loop: the calls other threads post or send (Control.Invoke,
    BeginInvoke, awaits, notifications) are queued in .NET and run here, on the user-interface thread."""

    def __init__(self, ui_context):
        super().__init__()
        self.ui_context = ui_context
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.drain)
        self.timer.start(5)

    def drain(self):
        for error in self.ui_context.Drain():
            traceback.print_exception(Exception(str(error)))


def run(form):
    import os
    global PROBE_PROMPTS
    if os.environ.get('PREPOMAXX_UI_PROBE'):
        PROBE_PROMPTS = []
        import faulthandler
        faulthandler.dump_traceback_later(float(os.environ.get('PREPOMAXX_UI_PROBE_TIMEOUT', '240')), exit=True)
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv[:1] or ['PrePoMax'])
    app.setApplicationName('PrePoMax')
    ui_context = ToolkitSynchronizationContext.Install()
    events = EventLoopDrain(ui_context)

    class Placeholder(QtWidgets.QWidget):
        """The owner of the forms FrmMain shows while it loads, before its own window exists."""
        def in_ui_context(self, action):
            from System.Threading import SynchronizationContext
            previous = SynchronizationContext.Current
            SynchronizationContext.SetSynchronizationContext(ui_context)
            try:
                return action()
            finally:
                SynchronizationContext.SetSynchronizationContext(previous)
    renderer = of.OriginalFormRenderer(Placeholder(), None)
    renderer.post = lambda action: ui_context.PostAction(action)
    # Original message boxes and their unattended policy (CaeGlobals.MessageBoxes): a Qt box on this thread
    window_ref = {}

    def ui_prompt(owner, text, caption, buttons, icon):
        # Reached on this thread only: MessageBoxes hops here through its UiDispatcher (the original Form.Invoke)
        return prompt(window_ref.get('window'), owner, text, caption, buttons, icon)
    presenter = Func[IWin32Window, String, String, MessageBoxButtons, MessageBoxIcon, DialogResult](ui_prompt)
    MessageBoxes.InteractivePresenter = presenter
    MessageBoxes.UiDispatcher = ui_context.Dispatcher
    MessageBoxes.Mode = MessageBoxModeEnum.Interactive
    key_hook = KeyHook()
    app.installEventFilter(key_hook)
    exit_handler = Action(lambda: app.quit())
    Application.ExitHandler = exit_handler
    # Application.DoEvents of the original (FrmMain draws its menus and view while it starts)
    def do_events():
        if ui_context.IsUiThread:
            app.processEvents()
    events_handler = Action(do_events)
    Application.DoEventsHandler = events_handler
    # WinForms creates the controls of a shown form (and of a control added to it later) at once: FrmMain.Load adds
    # the view, which is loaded there, before Shown; the native window of the view follows when Qt shows it
    Form.CreateControlsOnShow = True
    window = None
    try:
        # Load and Shown run in the WinForms synchronization context: their awaits resume on this thread
        ui_context.Run(Action(form.Show))
        window = MainFormWindow(renderer, form, ui_context)
        window_ref['window'] = window
        renderer.windows[form] = window
        geometry = QtWidgets.QApplication.primaryScreen().availableGeometry()
        window.resize(min(1400, geometry.width()), min(900, geometry.height()))
        window.show()
        renderer.sync_soon()
        # Unattended checks (X/UI/app_gui_probe.py): PREPOMAXX_UI_PROBE names the probe script, which gets the
        # application, the window, FrmMain and the renderer once the window is shown
        import os
        probe = os.environ.get('PREPOMAXX_UI_PROBE')
        if probe:
            import importlib.util
            spec = importlib.util.spec_from_file_location('ui_probe', probe)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.PROMPTS = PROBE_PROMPTS
            module.PROMPT_ANSWER = PROBE_ANSWER
            QtCore.QTimer.singleShot(500, lambda: module.start(app, window, form, renderer))
        app.exec()
    finally:
        Application.ExitHandler = None
        Application.DoEventsHandler = None
        MessageBoxes.UiDispatcher = None
        app.removeEventFilter(key_hook)
        if window is not None and form.Visible:
            renderer.input(lambda: form.Close())


run(form)

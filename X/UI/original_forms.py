"""Qt renderer for the original PrePoMax forms (D062).

The original form classes run unchanged on the headless control model (X/UI/FormsCompat); this module
draws that control tree with Qt at the original designer geometry and feeds user input back through the
events WinForms would raise (Click, SelectedIndexChanged, PropertyValueChanged, FormClosing ...). It owns
no form behaviour: the original handlers decide what happens.
"""
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets
import System
from System import Array, Int32
from System.Drawing import Point, Size, Rectangle
from System.Windows.Forms import (Control, Form, GroupBox, ButtonBase, Button, CheckBox, RadioButton, Label, TextBoxBase,
                                  ListView, PropertyGrid, TabControl, TabPage, Panel, ComboBox, NumericUpDown,
                                  ControlNotifications, GridItemType, Keys, MouseButtons, OrderedNameComparer, Screen)

ROOT = Path(__file__).resolve().parents[2]
# Original forms use Segoe UI 9 pt at 96 DPI: 12 px text in 23 px buttons and 17 px list rows.
FONT_PIXELS = 12


def original_font():
    """Segoe UI 9 pt at 96 DPI where installed; otherwise the system UI font at the same pixel size, narrowed
    to Segoe UI's average advance so designer-sized labels keep their text."""
    font = QtGui.QFont('Segoe UI')
    if not QtGui.QFontInfo(font).exactMatch():
        font = QtWidgets.QApplication.font()
        font.setStretch(90)
    font.setPixelSize(FONT_PIXELS)
    return font


def qcolor(color):
    return QtGui.QColor(int(color.R), int(color.G), int(color.B), int(color.A))


def visible_name(text):
    return str(OrderedNameComparer.Visible(text or ''))


class PropertyGridWidget(QtWidgets.QWidget):
    """WinForms PropertyGrid look: categorized rows, value column, help pane with name and description."""

    def __init__(self, window, grid, parent):
        super().__init__(parent)
        self.window, self.grid = window, grid
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setIndentation(12)
        self.tree.setUniformRowHeights(True)
        self.tree.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tree.currentItemChanged.connect(self.current_changed)
        self.tree.itemExpanded.connect(lambda item: self.expanded(item, True))
        self.tree.itemCollapsed.connect(lambda item: self.expanded(item, False))
        self.tree.installEventFilter(self)
        layout.addWidget(self.tree, 1)
        self.help = QtWidgets.QLabel()
        self.help.setWordWrap(True)
        self.help.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft)
        self.help.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.help.setMinimumHeight(4 * FONT_PIXELS + 12)
        self.help.setMaximumHeight(4 * FONT_PIXELS + 12)
        self.help.setContentsMargins(4, 2, 4, 2)
        layout.addWidget(self.help)
        self.items = {}
        self.updating = False
        self.rebuild()

    def label_width(self):
        # TabEnabledPropertyGrid.SetLabelColumnWidth: label ratio (default 2.0 -> half of the width).
        ratio = float(getattr(self.grid, 'LabelRatio', 2.0) or 2.0)
        return max(40, int(self.tree.viewport().width() / ratio))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.tree.setColumnWidth(0, self.label_width())

    def rebuild(self):
        self.updating = True
        try:
            scroll = self.tree.verticalScrollBar().value()
            self.tree.clear()
            self.items = {}
            root = self.grid.Root
            if root is not None:
                for child in root.GridItems:
                    self.add(child, None)
            self.select_current()
            self.tree.setColumnWidth(0, self.label_width())
            self.tree.verticalScrollBar().setValue(scroll)
        finally:
            self.updating = False
        self.update_help()

    def add(self, grid_item, parent):
        item = QtWidgets.QTreeWidgetItem([visible_name(grid_item.Label), ''])
        item.setData(0, QtCore.Qt.ItemDataRole.UserRole, grid_item)
        (parent.addChild if parent is not None else self.tree.addTopLevelItem)(item)
        self.items[self.key(grid_item)] = item
        if grid_item.GridItemType == GridItemType.Category:
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
            item.setFirstColumnSpanned(True)
            item.setBackground(0, self.palette().window())
        else:
            self.value_editor(item, grid_item)
        for child in grid_item.GridItems:
            self.add(child, item)
        item.setExpanded(bool(grid_item.Expanded))

    @staticmethod
    def key(grid_item):
        parts = []
        while grid_item is not None and grid_item.GridItemType != GridItemType.Root:
            parts.append(str(grid_item.GridItemType) + ':' + str(grid_item.Label))
            grid_item = grid_item.Parent
        return '/'.join(reversed(parts))

    def value_editor(self, item, grid_item):
        grid = self.grid
        text = str(grid.GetText(grid_item) or '')
        descriptor = grid_item.PropertyDescriptor
        read_only = bool(descriptor.IsReadOnly) or bool(getattr(grid, 'ReadOnly', False))
        exclusive = False
        choices, exclusive = grid.GetStandardValues(grid_item, exclusive)
        choices = [str(c) for c in choices]
        editor_type = self.window.renderer.editor_type(descriptor)
        if read_only or (not grid.CanEditText(grid_item) and not choices and editor_type is None):
            item.setText(1, text)
            item.setForeground(1, QtGui.QBrush(QtGui.QColor(80, 80, 80)))
            return
        holder = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(holder)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        if choices:
            edit = QtWidgets.QComboBox()
            edit.setEditable(not exclusive)
            edit.addItems(choices)
            if text not in choices:
                edit.addItem(text)
            edit.setCurrentText(text)
            edit.activated.connect(lambda index, g=grid_item, w=edit: self.commit(g, w.currentText()))
            if not exclusive:
                edit.lineEdit().editingFinished.connect(lambda g=grid_item, w=edit: self.commit(g, w.currentText()))
        else:
            edit = QtWidgets.QLineEdit(text)
            edit.setFrame(False)
            edit.setReadOnly(not grid.CanEditText(grid_item))
            edit.editingFinished.connect(lambda g=grid_item, w=edit: self.commit(g, w.text()))
            completer_items = list(getattr(grid, 'AutocompleteItems', []) or [])
            if completer_items:
                completer = QtWidgets.QCompleter(completer_items, edit)
                completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
                edit.setCompleter(completer)
        edit.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        edit.installEventFilter(self)
        edit.setProperty('gridKey', self.key(grid_item))
        row.addWidget(edit, 1)
        if editor_type is not None:
            button = QtWidgets.QToolButton()
            button.setText('…')
            button.clicked.connect(lambda checked=False, g=grid_item: self.window.renderer.edit_modal(self, g))
            row.addWidget(button)
        self.tree.setItemWidget(item, 1, holder)

    def commit(self, grid_item, text):
        if self.updating:
            return
        if str(self.grid.GetText(grid_item) or '') == text:
            return
        self.window.renderer.guard(lambda: self.grid.SetValueFromText(grid_item, text))
        self.window.renderer.sync_soon()

    def current_changed(self, current, previous):
        if self.updating or current is None:
            return
        grid_item = current.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if grid_item is not None and self.grid.SelectedGridItem != grid_item:
            self.window.renderer.guard(lambda: setattr(self.grid, 'SelectedGridItem', grid_item))
        self.update_help()

    def expanded(self, item, value):
        if self.updating:
            return
        grid_item = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if grid_item is not None:
            self.grid.SetExpanded(grid_item, value)

    def select_current(self):
        selected = self.grid.SelectedGridItem
        item = self.items.get(self.key(selected)) if selected is not None else None
        if item is not None and self.tree.currentItem() is not item:
            self.tree.setCurrentItem(item)

    def update_help(self):
        selected = self.grid.SelectedGridItem
        if selected is None or selected.GridItemType == GridItemType.Root:
            self.help.setText('')
            return
        title = visible_name(selected.Label)
        description = ''
        if selected.PropertyDescriptor is not None:
            description = str(selected.PropertyDescriptor.Description or '')
        self.help.setText(f'<b>{QtCore.Qt.mightBeRichText(title) and title or title}</b><br>{description}')

    def eventFilter(self, watched, event):
        if event.type() == QtCore.QEvent.Type.KeyPress and event.key() == QtCore.Qt.Key.Key_Tab:
            # TabEnabledPropertyGrid Form_KeyDown: Tab moves to the next property row.
            if hasattr(self.grid, 'SelectNextGridItem') and self.grid.SelectNextGridItem():
                self.select_current()
                self.focus_value()
                return True
        return False

    def focus_value(self):
        item = self.tree.currentItem()
        widget = self.tree.itemWidget(item, 1) if item is not None else None
        if widget is not None:
            edit = widget.findChild(QtWidgets.QLineEdit) or widget.findChild(QtWidgets.QComboBox)
            if edit is not None:
                edit.setFocus()
                if isinstance(edit, QtWidgets.QLineEdit):
                    edit.selectAll()


class ListViewWidget(QtWidgets.QListWidget):
    """ListView (Details, one column): rows drawn with the item colours the original sets (ListViewWithSelection
    paints the chosen type itself and keeps no list-view selection)."""

    def __init__(self, window, view, parent):
        super().__init__(parent)
        self.window, self.view = window, view
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.setUniformItemSizes(True)
        self.setMouseTracking(True)
        self.itemPressed.connect(self.pressed)
        self.rebuild()

    def rebuild(self):
        self.clear()
        for item in self.view.Items:
            row = QtWidgets.QListWidgetItem(str(item.Text))
            row.setSizeHint(QtCore.QSize(10, ListView.RowHeight))
            back, fore = item.BackColor, item.ForeColor
            row.setBackground(QtGui.QBrush(qcolor(back)))
            row.setForeground(QtGui.QBrush(qcolor(fore)))
            self.addItem(row)

    def pressed(self, row):
        index = self.row(row)
        renderer = self.window.renderer
        renderer.guard(lambda: self.view.SelectByUser(Array[Int32]([index])))
        renderer.guard(lambda: self.view.RaiseMouse('up', MouseButtons.Left, 1, 4, index * ListView.RowHeight + 4))
        renderer.sync_soon()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        position = event.position().toPoint()
        self.view.RaiseMouse('move', getattr(MouseButtons, 'None'), 0, position.x(), position.y())
        self.window.renderer.sync_soon()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.view.RaiseMouseLeave()
        self.window.renderer.sync_soon()


class FormWindow(QtWidgets.QDialog):
    """One original form: a non-modal tool window owned by the main window (Form.Show(owner))."""

    def __init__(self, renderer, form):
        super().__init__(renderer.main_window)
        self.renderer, self.form = renderer, form
        self.setWindowFlag(QtCore.Qt.WindowType.Tool, True)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setModal(False)
        self.setFont(original_font())
        self.widgets = {}
        self.syncing = False
        self.build(form, self)
        self.sync()

    # Construction ---------------------------------------------------------------------------------------------------------
    def build(self, control, parent_widget):
        for child in control.Controls:
            widget = self.create(child, parent_widget)
            if widget is None:
                continue
            self.widgets[child] = widget
            container = widget.page_container if hasattr(widget, 'page_container') else widget
            if not isinstance(child, (ListView, PropertyGrid, TabControl)):
                self.build(child, container)

    def create(self, control, parent):
        r = self.renderer
        if isinstance(control, PropertyGrid):
            return PropertyGridWidget(self, control, parent)
        if isinstance(control, ListView):
            return ListViewWidget(self, control, parent)
        if isinstance(control, GroupBox):
            return QtWidgets.QGroupBox(str(control.Text), parent)
        if isinstance(control, CheckBox):
            from System.Windows.Forms import Appearance
            if control.Appearance == Appearance.Button:
                # Appearance.Button: a toggle button with the checkbox's image and text.
                widget = QtWidgets.QToolButton(parent)
                widget.setCheckable(True)
                widget.setText(str(control.Text))
                widget.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly if not str(control.Text) else QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            else:
                widget = QtWidgets.QCheckBox(str(control.Text), parent)
            widget.clicked.connect(lambda checked=False, c=control: r.input(c.RaiseClick))
            return widget
        if isinstance(control, RadioButton):
            widget = QtWidgets.QRadioButton(str(control.Text), parent)
            widget.setAutoExclusive(False)
            widget.clicked.connect(lambda checked=False, c=control: r.input(c.RaiseClick))
            return widget
        if isinstance(control, ButtonBase):
            widget = QtWidgets.QPushButton(str(control.Text), parent)
            widget.setAutoDefault(False)
            widget.clicked.connect(lambda checked=False, c=control: r.input(c.RaiseClick))
            return widget
        if isinstance(control, Label):
            widget = QtWidgets.QLabel(str(control.Text), parent)
            widget.setWordWrap(False)
            return widget
        if isinstance(control, TextBoxBase):
            widget = QtWidgets.QLineEdit(str(control.Text), parent)
            widget.editingFinished.connect(lambda c=control, w=widget: r.input(lambda: (c.SetUserText(w.text()), c.RaiseLeave())))
            return widget
        if isinstance(control, ComboBox):
            widget = QtWidgets.QComboBox(parent)
            widget.activated.connect(lambda index, c=control: r.input(lambda: c.RaiseSelectionChangeCommitted(index)))
            return widget
        if isinstance(control, NumericUpDown):
            widget = QtWidgets.QDoubleSpinBox(parent)
            widget.valueChanged.connect(lambda value, c=control: r.input(lambda: setattr(c, 'Value', System.Decimal(value))))
            return widget
        if isinstance(control, TabControl):
            widget = QtWidgets.QTabWidget(parent)
            pages = {}
            for page in control.TabPages:
                page_widget = QtWidgets.QWidget()
                widget.addTab(page_widget, str(page.Text))
                self.widgets[page] = page_widget
                self.build(page, page_widget)
                pages[page] = page_widget
            widget.currentChanged.connect(lambda index, c=control: r.input(lambda: setattr(c, 'SelectedIndex', index)))
            return widget
        # Panels and containers
        return QtWidgets.QFrame(parent)

    # State ----------------------------------------------------------------------------------------------------------------
    def sync(self):
        self.syncing = True
        try:
            form = self.form
            self.setWindowTitle(str(form.Text))
            client = form.ClientSize
            minimum, maximum = form.MinimumSize, form.MaximumSize
            # WinForms size limits are window sizes; Qt's are client sizes.
            self.setMinimumSize(max(0, minimum.Width - Form.FrameWidth), max(0, minimum.Height - Form.FrameHeight))
            self.setMaximumSize(maximum.Width - Form.FrameWidth if maximum.Width > 0 else 16777215,
                                maximum.Height - Form.FrameHeight if maximum.Height > 0 else 16777215)
            if self.width() != client.Width or self.height() != client.Height:
                self.resize(client.Width, client.Height)
            self.setEnabled(bool(form.Enabled))
            for control, widget in list(self.widgets.items()):
                self.sync_control(control, widget)
        finally:
            self.syncing = False

    def sync_control(self, control, widget):
        if isinstance(control, TabPage):
            return
        bounds = control.Bounds
        if isinstance(widget, QtWidgets.QGroupBox):
            widget.setTitle(str(control.Text))
        widget.setGeometry(bounds.X, bounds.Y, bounds.Width, bounds.Height)
        widget.setVisible(bool(control.Visible) or (not self.form.Visible))
        widget.setEnabled(bool(control.Enabled))
        tip = self.renderer.tooltip(control)
        if tip is not None:
            widget.setToolTip(tip)
        if isinstance(widget, QtWidgets.QToolButton) and isinstance(control, CheckBox):
            widget.setChecked(bool(control.Checked))
            icon = self.renderer.icon(control.Image)
            if icon is not None:
                widget.setIcon(icon)
        if isinstance(widget, (QtWidgets.QPushButton, QtWidgets.QCheckBox, QtWidgets.QRadioButton, QtWidgets.QLabel)):
            if widget.text() != str(control.Text):
                widget.setText(str(control.Text))
            if isinstance(control, ButtonBase):
                icon = self.renderer.icon(control.Image)
                if icon is not None:
                    widget.setIcon(icon)
        if isinstance(widget, (QtWidgets.QCheckBox, QtWidgets.QRadioButton)) and widget.isChecked() != bool(control.Checked):
            widget.setChecked(bool(control.Checked))
        if isinstance(widget, QtWidgets.QLineEdit) and not widget.hasFocus() and widget.text() != str(control.Text):
            widget.setText(str(control.Text))
            widget.setReadOnly(bool(control.ReadOnly))
        if isinstance(widget, QtWidgets.QComboBox) and isinstance(control, ComboBox):
            texts = [str(i) for i in control.Items]
            if [widget.itemText(i) for i in range(widget.count())] != texts:
                widget.blockSignals(True)
                widget.clear()
                widget.addItems(texts)
                widget.blockSignals(False)
            if widget.currentIndex() != control.SelectedIndex:
                widget.setCurrentIndex(control.SelectedIndex)
        if isinstance(widget, QtWidgets.QTabWidget) and widget.currentIndex() != control.SelectedIndex:
            widget.blockSignals(True)
            widget.setCurrentIndex(control.SelectedIndex)
            widget.blockSignals(False)

    def refresh_control(self, control):
        widget = self.widgets.get(control)
        if isinstance(widget, PropertyGridWidget):
            widget.rebuild()
        elif isinstance(widget, ListViewWidget):
            widget.rebuild()

    # Window events --------------------------------------------------------------------------------------------------------
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Only a user resize changes the form; Qt's own sizing on show does not (the form keeps its size).
        if not self.syncing and event.spontaneous() and self.isVisible() and self.renderer.user_resizing(self):
            size = event.size()
            self.renderer.input(lambda: setattr(self.form, 'ClientSize', Size(size.width(), size.height())))

    def moveEvent(self, event):
        super().moveEvent(event)
        if not self.syncing:
            position = self.pos()
            self.renderer.input(lambda: setattr(self.form, 'Location', Point(position.x(), position.y())))

    def closeEvent(self, event):
        # WinForms FormClosing (UserClosing): the original FrmProperties cancels it and hides the form.
        if self.form.Visible:
            self.renderer.input(self.form.CloseByUser)
        event.ignore() if self.form.Visible else event.accept()

    def reject(self):
        # Escape reaches the form's CancelButton only (WinForms); no CancelButton -> nothing happens.
        self.renderer.input(lambda: self.form.ProcessDialogKeyInput(Keys.Escape))

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
            focus = QtWidgets.QApplication.focusWidget()
            if isinstance(focus, QtWidgets.QPushButton):
                focus.click()
                return
            self.renderer.input(lambda: self.form.ProcessDialogKeyInput(Keys.Enter))
            return
        super().keyPressEvent(event)


class OriginalFormRenderer:
    """Keeps a Qt window for every visible original form and mirrors control-model notifications."""

    def __init__(self, main_window, host):
        self.main_window, self.host = main_window, host
        self.windows = {}
        self.dirty = set()
        self.refresh = set()
        self.pending = False
        self.icons = {}
        self.handler = System.Action[Control, System.String](self.notify)
        ControlNotifications.Changed += self.handler
        from System.Windows.Forms import DialogResult
        self.dialog_handler = System.Func[Form, DialogResult](self.show_dialog)
        Form.ShowDialogHandler = self.dialog_handler
        self.update_screens()

    def update_screens(self):
        rects = [QtWidgets.QApplication.primaryScreen().availableGeometry()] if QtWidgets.QApplication.primaryScreen() else []
        rects += [s.availableGeometry() for s in QtWidgets.QApplication.screens() if s is not QtWidgets.QApplication.primaryScreen()]
        Screen.SetScreens(Array[Rectangle]([Rectangle(r.x(), r.y(), r.width(), r.height()) for r in rects]))

    # Notifications -------------------------------------------------------------------------------------------------------
    def notify(self, control, prop):
        form = control.FindForm()
        if form is None:
            return
        self.dirty.add(form)
        if prop in ('SelectedObject', 'Refresh', 'Items', 'Expanded', 'Autocomplete', 'LabelRatio', 'Columns'):
            self.refresh.add(control)
        if prop == 'SelectedGridItem':
            self.refresh.add(('select', control))
        self.sync_soon()

    def sync_soon(self):
        if not self.pending:
            self.pending = True
            QtCore.QTimer.singleShot(0, self.sync)

    def sync(self):
        self.pending = False
        dirty, self.dirty = self.dirty, set()
        refresh, self.refresh = self.refresh, set()
        for form in dirty:
            window = self.windows.get(form)
            if form.Visible:
                if window is None or form.IsDisposed:
                    window = FormWindow(self, form)
                    self.windows[form] = window
                    refresh = {r for r in refresh if not (isinstance(r, tuple) and r[1].FindForm() == form) and (isinstance(r, tuple) or r.FindForm() != form)}
                else:
                    # Shown again (hide-on-close forms are reused): current state first.
                    for control in list(window.widgets):
                        window.refresh_control(control)
                window.sync()
                if not window.isVisible():
                    window.syncing = True
                    window.move(form.Location.X, form.Location.Y)
                    window.syncing = False
                    window.show()
                    window.raise_()
                    window.sync()
            elif window is not None:
                window.hide()
        for item in refresh:
            if isinstance(item, tuple):
                control = item[1]
                window = self.windows.get(control.FindForm())
                widget = window.widgets.get(control) if window else None
                if isinstance(widget, PropertyGridWidget):
                    widget.updating = True
                    try:
                        widget.select_current()
                    finally:
                        widget.updating = False
                    widget.update_help()
                continue
            window = self.windows.get(item.FindForm())
            if window is not None and window.isVisible():
                window.refresh_control(item)

    def show_dialog(self, form):
        """Form.ShowDialog: the form is shown application-modal and a nested event loop runs until it closes
        (WinForms: a DialogResult or Close ends the modal loop)."""
        form.Show()
        self.flush()
        window = self.windows.get(form)
        if window is not None:
            window.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        loop = QtCore.QEventLoop()
        timer = QtCore.QTimer()
        timer.timeout.connect(lambda: loop.quit() if not form.Visible else None)
        timer.start(20)
        if form.Visible:
            loop.exec()
        timer.stop()
        if window is not None:
            window.setWindowModality(QtCore.Qt.WindowModality.NonModal)
            window.hide()
        return form.DialogResult

    def flush(self):
        """Apply pending notifications now (probes and modal callers)."""
        for _ in range(5):
            if not (self.dirty or self.refresh):
                break
            self.sync()

    # Input ----------------------------------------------------------------------------------------------------------------
    def guard(self, action):
        try:
            return self.main_window.in_ui_context(action)
        except Exception as error:
            # WinForms reports an input the original handlers did not catch (e.g. an invalid grid value)
            # in a message box; it goes through the original MessageBoxes presenter.
            from authoring_widgets import message
            from CaeGlobals import MessageBoxes
            MessageBoxes.ShowError(message(error))

    def input(self, action):
        result = self.guard(action)
        self.sync_soon()
        return result

    # Resources -----------------------------------------------------------------------------------------------------------
    def icon(self, image):
        if image is None:
            return None
        path = str(image.Path)
        if path not in self.icons:
            self.icons[path] = QtGui.QIcon(str(ROOT / path))
        return self.icons[path]

    def user_resizing(self, window):
        """A spontaneous resize while a mouse button is held on the frame is the user's."""
        return QtWidgets.QApplication.mouseButtons() != QtCore.Qt.MouseButton.NoButton

    def tooltip(self, control):
        return None

    def editor_type(self, descriptor):
        from System.ComponentModel import EditorAttribute
        attribute = descriptor.Attributes[EditorAttribute]
        if attribute is None:
            return None
        name = str(attribute.EditorTypeName)
        return name.split(',')[0].split('.')[-1]

    def edit_modal(self, grid_widget, grid_item):
        editor = self.editor_type(grid_item.PropertyDescriptor)
        grid = grid_widget.grid
        if editor in ('FileNameEditor', 'FilteredFileNameEditor', 'CreateFileNameEditor'):
            current = str(grid.GetText(grid_item) or '')
            if editor == 'CreateFileNameEditor':
                path, _ = QtWidgets.QFileDialog.getSaveFileName(self.main_window, 'Select file', current)
            else:
                path, _ = QtWidgets.QFileDialog.getOpenFileName(self.main_window, 'Select file', current)
            if path:
                self.input(lambda: grid.SetValueFromText(grid_item, path))
        elif editor == 'FolderNameEditor':
            path = QtWidgets.QFileDialog.getExistingDirectory(self.main_window, 'Select folder', str(grid.GetText(grid_item) or ''))
            if path:
                self.input(lambda: grid.SetValueFromText(grid_item, path))
        elif editor == 'SinglePointDataEditor':
            from PrePoMaxX.UI import OriginalEditors
            self.input(lambda: OriginalEditors.EditSinglePoint(grid, grid_item))
        elif editor in ('ColorEditorEx', 'ColorEditor'):
            color = QtWidgets.QColorDialog.getColor(parent=self.main_window, options=QtWidgets.QColorDialog.ColorDialogOption.ShowAlphaChannel)
            if color.isValid():
                self.input(lambda: grid.SetValueFromText(grid_item, f'{color.alpha()}, {color.red()}, {color.green()}, {color.blue()}'))
        self.flush()

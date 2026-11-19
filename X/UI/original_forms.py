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
                                  ControlNotifications, GridItemType, Keys, MouseButtons, OrderedNameComparer, Screen,
                                  DataGridView, DataGridViewContentAlignment, DataGridViewAutoSizeColumnMode,
                                  ToolStripSeparator, Clipboard, TreeView, TrackBar, ScrollBar, ProgressBar, LinkLabel,
                                  PictureBox, SplitContainer)
from FastColoredTextBoxNS import FastColoredTextBox
from ZedGraph import ZedGraphControl, LegendPos
import original_controls as oc
from AutocompleteMenuNS import AutocompleteMenu

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


MISSING_VALUE_TOOLTIP = 'Select at least one item.'   # UserControls/ProperyGrid/MySite.cs MissingValueToolTip
MISSING_VALUES = System.Type.GetType('UserControls.IMissingPropertyValues, UserControls', True)
_MISSING_ICON = []


def missing_value_icon():
    """MySite.CreateMissingValueImage: an 8 x 8 red dot (antialiased ellipse 0, 0, 7, 7)."""
    if not _MISSING_ICON:
        pixmap = QtGui.QPixmap(8, 8)
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor('red'))
        painter.drawEllipse(QtCore.QRectF(0, 0, 7, 7))
        painter.end()
        _MISSING_ICON.append(QtGui.QIcon(pixmap))
    return _MISSING_ICON[0]


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
        missing = self.value_missing(descriptor)
        if missing:
            # 3.0.1 missing values (IMissingPropertyValues): the value text in MissingValueColor
            # (PropertyGridMissingValuePainter) and the red dot with its tooltip (MySite's PropertyValueUIItem)
            item.setIcon(0, missing_value_icon())
            item.setToolTip(0, MISSING_VALUE_TOOLTIP)
            item.setToolTip(1, MISSING_VALUE_TOOLTIP)
        if read_only or (not grid.CanEditText(grid_item) and not choices and editor_type is None):
            item.setText(1, text)
            item.setForeground(1, QtGui.QBrush(QtGui.QColor('red') if missing else QtGui.QColor(80, 80, 80)))
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
        if missing:
            palette = edit.palette()
            palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor('red'))
            edit.setPalette(palette)
            edit.setProperty('missingValue', True)
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

    def value_missing(self, descriptor):
        """IMissingPropertyValues.IsPropertyValueMissing of the selected object for this property (3.0.1)."""
        selected = self.grid.SelectedObject
        if selected is None or descriptor is None:
            return False
        if not MISSING_VALUES.IsInstanceOfType(selected):
            return False
        return bool(self.window.renderer.guard(lambda: MISSING_VALUES.GetMethod('IsPropertyValueMissing').Invoke(
            selected, Array[System.Object]([descriptor.Name]))))

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


def qt_alignment(alignment):
    """DataGridViewContentAlignment -> Qt alignment (NotSet: middle left)."""
    A = QtCore.Qt.AlignmentFlag
    value = int(alignment) or 16
    vertical = A.AlignTop if value < 16 else A.AlignVCenter if value < 256 else A.AlignBottom
    column = value if value < 16 else value >> 4 if value < 256 else value >> 8
    horizontal = {1: A.AlignLeft, 2: A.AlignHCenter, 4: A.AlignRight}.get(column, A.AlignLeft)
    return vertical | horizontal


class FragmentCompleter(QtCore.QObject):
    """Original AutocompleteMenu behaviour for an edit control: the fragment before the caret (the menu's
    SearchPattern) is completed from the menu's items while the menu is enabled; a snippet's '^' is the caret."""

    def __init__(self, edit, menu_for):
        super().__init__(edit)
        self.edit, self.menu_for = edit, menu_for
        self.model = QtCore.QStringListModel()
        self.completer = QtWidgets.QCompleter(self.model, edit)
        self.completer.setWidget(edit)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setCompletionMode(QtWidgets.QCompleter.CompletionMode.PopupCompletion)
        self.completer.activated[str].connect(self.insert)
        self.items = {}
        edit.textEdited.connect(self.update)

    def fragment(self, menu):
        import re
        text = self.edit.text()[:self.edit.cursorPosition()]
        match = re.search('(?:' + str(menu.SearchPattern) + ')+$', text)
        return match.group(0) if match else ''

    def update(self, _text=None):
        menu = self.menu_for()
        if menu is None:
            self.completer.popup().hide()
            return
        fragment = self.fragment(menu)
        if len(fragment) < int(menu.MinFragmentLength):
            self.completer.popup().hide()
            return
        self.items = {str(item): str(item.Text) for item in menu.SourceItems}
        self.model.setStringList(list(self.items))
        self.completer.setCompletionPrefix(fragment)
        self.completer.complete()

    def insert(self, shown):
        menu = self.menu_for()
        text = self.items.get(shown, shown)
        fragment = self.fragment(menu) if menu is not None else ''
        position = self.edit.cursorPosition()
        before, after = self.edit.text()[:position - len(fragment)], self.edit.text()[position:]
        caret = text.find('^')
        text = text.replace('^', '')
        self.edit.setText(before + text + after)
        self.edit.setCursorPosition(len(before) + (caret if caret >= 0 else len(text)))
        self.edit.textEdited.emit(self.edit.text())


class GridDelegate(QtWidgets.QStyledItemDelegate):
    """Cell editing through the grid model: BeginEdit (EditingControlShowing), typed text into the editing
    control (TextChanged), EndEdit on commit (parse/commit errors go to OnDataError), CancelEdit on Escape."""

    def createEditor(self, parent, option, index):
        view = self.parent()
        grid, renderer = view.grid, view.window.renderer
        if not renderer.guard(lambda: grid.BeginEditByUser(index.row(), index.column())):
            return None
        editor = QtWidgets.QLineEdit(parent)
        editor.setFrame(False)
        editor.setAlignment(qt_alignment(view.cell_alignment(index.column())))
        editor.textEdited.connect(lambda text: renderer.guard(lambda: grid.EditTextByUser(text)))
        editor.completion = FragmentCompleter(editor, lambda: AutocompleteMenu.ActiveFor(grid.EditingControl))
        return editor

    def setEditorData(self, editor, index):
        view = self.parent()
        if view.reopen is not None:
            editor.setText(view.reopen[2])
            return
        control = view.grid.EditingControl
        editor.setText(str(control.Text) if control is not None else str(index.data() or ''))

    def setModelData(self, editor, model, index):
        view = self.parent()
        grid, text = view.grid, editor.text()
        view.reopen = None
        view.window.renderer.input(lambda: (grid.EditTextByUser(text), grid.EndEdit()))
        if grid.IsCurrentCellInEditMode:
            # The value was rejected (OnDataError, Cancel): WinForms keeps the cell in edit mode with the text.
            view.reopen = (index.row(), index.column(), text)
            QtCore.QTimer.singleShot(0, view.reopen_editor)

    def destroyEditor(self, editor, index):
        view = self.parent()
        if view.grid.IsCurrentCellInEditMode and view.reopen is None:
            view.window.renderer.input(view.grid.CancelEdit)
        super().destroyEditor(editor, index)


class DataGridWidget(QtWidgets.QTableWidget):
    """DataGridView: the model's columns, rows (the new row marked '*'), cell text, selection and current cell;
    edits, selection, keys and the context menu go back through the WinForms events."""

    def __init__(self, window, grid, parent):
        super().__init__(parent)
        self.window, self.grid = window, grid
        self.updating = False
        self.reopen = None
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectItems)
        T = QtWidgets.QAbstractItemView.EditTrigger
        self.setEditTriggers(T.DoubleClicked | T.EditKeyPressed | T.AnyKeyPressed)
        self.setItemDelegate(GridDelegate(self))
        self.verticalHeader().setDefaultSectionSize(22)
        self.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setHighlightSections(False)
        self.setWordWrap(False)
        self.itemSelectionChanged.connect(self.selection_changed)
        # Rows selected through the row header are WinForms selected rows (RowHeaderSelect).
        self.header_rows = set()
        self.verticalHeader().sectionPressed.connect(self.header_pressed)
        self.verticalHeader().sectionEntered.connect(self.header_entered)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)
        self.rebuild()

    def mouseDoubleClickEvent(self, event):
        # WinForms CellMouseDoubleClick / CellDoubleClick (a read-only grid opens the original handler's form)
        index = self.indexAt(event.position().toPoint())
        if index.isValid():
            rect = self.visualRect(index)
            x, y = int(event.position().x()) - rect.x(), int(event.position().y()) - rect.y()
            QtCore.QTimer.singleShot(0, lambda r=index.row(), c=index.column(): self.window.renderer.input(lambda: self.grid.RaiseCellDoubleClick(r, c, x, y)))
        super().mouseDoubleClickEvent(event)

    def reopen_editor(self):
        if self.reopen is None:
            return
        row, column, _ = self.reopen
        index = self.model().index(row, column)
        self.setCurrentIndex(index)
        self.edit(index)
        self.reopen = None

    def cell_alignment(self, column):
        col = self.grid.Columns[column]
        alignment = col.DefaultCellStyle.Alignment
        return alignment if int(alignment) != 0 else self.grid.DefaultCellStyle.Alignment

    def rebuild(self):
        grid = self.grid
        if self.state() == QtWidgets.QAbstractItemView.State.EditingState:
            return
        self.updating = True
        try:
            columns = list(grid.Columns)
            rows = int(grid.RowCount)
            self.setColumnCount(len(columns))
            self.setRowCount(rows)
            header = self.horizontalHeader()
            for i, column in enumerate(columns):
                item = QtWidgets.QTableWidgetItem(str(column.HeaderText))
                item.setTextAlignment(qt_alignment(column.HeaderCell.Style.Alignment))
                self.setHorizontalHeaderItem(i, item)
                self.setColumnHidden(i, not column.Visible)
                if column.InheritedAutoSizeMode == DataGridViewAutoSizeColumnMode.Fill:
                    header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.Stretch)
                else:
                    header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.Interactive)
                    self.setColumnWidth(i, int(column.Width))
            new_row = int(grid.NewRowIndex)
            self.setVerticalHeaderLabels(['*' if r == new_row else '' for r in range(rows)])
            self.verticalHeader().setVisible(bool(grid.RowHeadersVisible))
            self.verticalHeader().setFixedWidth(int(grid.RowHeadersWidth))
            flags = QtCore.Qt.ItemFlag
            for r in range(rows):
                for c, column in enumerate(columns):
                    item = QtWidgets.QTableWidgetItem(str(grid.GetCellText(r, c)))
                    item.setTextAlignment(qt_alignment(self.cell_alignment(c)))
                    editable = not (grid.ReadOnly or column.ReadOnly)
                    item.setFlags(flags.ItemIsSelectable | flags.ItemIsEnabled | (flags.ItemIsEditable if editable else flags.NoItemFlags))
                    self.setItem(r, c, item)
            self.apply_selection()
        finally:
            self.updating = False

    def apply_selection(self):
        grid = self.grid
        wanted = set(zip([int(r) for r in grid.SelectionRows], [int(c) for c in grid.SelectionColumns]))
        current = (self.currentRow(), self.currentColumn())
        address = grid.CurrentCellAddress
        model = self.selectionModel()
        if address.Y >= 0 and address.Y < self.rowCount() and address.X < self.columnCount() and current != (address.Y, address.X):
            model.setCurrentIndex(self.model().index(address.Y, address.X), QtCore.QItemSelectionModel.SelectionFlag.NoUpdate)
        have = {(i.row(), i.column()) for i in self.selectedIndexes()}
        if have != wanted:
            selection = QtCore.QItemSelection()
            for r, c in wanted:
                if r < self.rowCount() and c < self.columnCount():
                    index = self.model().index(r, c)
                    selection.select(index, index)
            model.select(selection, QtCore.QItemSelectionModel.SelectionFlag.ClearAndSelect)

    def select_current(self):
        self.updating = True
        try:
            self.apply_selection()
        finally:
            self.updating = False

    def header_pressed(self, row):
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if not modifiers & (QtCore.Qt.KeyboardModifier.ControlModifier | QtCore.Qt.KeyboardModifier.ShiftModifier):
            self.header_rows = set()
        self.header_rows.add(row)
        self.selection_changed()

    def header_entered(self, row):
        if QtWidgets.QApplication.mouseButtons() & QtCore.Qt.MouseButton.LeftButton:
            self.header_rows.add(row)
            self.selection_changed()

    def selection_changed(self):
        if self.updating:
            return
        model = self.selectionModel()
        self.header_rows = {r for r in self.header_rows if model.isRowSelected(r, QtCore.QModelIndex())}
        indexes = self.selectedIndexes()
        rows = [i.row() for i in indexes]
        columns = [i.column() for i in indexes]
        header_rows = sorted(self.header_rows)
        current = self.currentIndex()
        grid = self.grid
        self.window.renderer.input(lambda: grid.SelectByUser(Array[Int32](rows), Array[Int32](columns), Array[Int32](header_rows), current.row(), current.column()))

    def mousePressEvent(self, event):
        # WinForms: a right click opens the context menu without changing the selection.
        if event.button() == QtCore.Qt.MouseButton.RightButton:
            return
        if not event.modifiers() & (QtCore.Qt.KeyboardModifier.ControlModifier | QtCore.Qt.KeyboardModifier.ShiftModifier):
            self.header_rows = set()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        key, modifiers = event.key(), event.modifiers()
        K = QtCore.Qt.Key
        keys = None
        if modifiers & QtCore.Qt.KeyboardModifier.ControlModifier and key in (K.Key_C, K.Key_X, K.Key_V, K.Key_P):
            keys = Keys.Control | getattr(Keys, chr(key))
        elif key in (K.Key_Delete, K.Key_Backspace) and self.state() != QtWidgets.QAbstractItemView.State.EditingState:
            keys = Keys.Delete
        if keys is not None:
            grid = self.grid
            handled = self.window.renderer.input(lambda: grid.RaiseKeyDown(keys))
            if handled or keys != Keys.Delete:
                return
        if key in (K.Key_Return, K.Key_Enter) and self.state() != QtWidgets.QAbstractItemView.State.EditingState:
            # WinForms: Enter moves to the cell below and stays in the grid.
            row = min(self.currentRow() + 1, self.rowCount() - 1)
            self.setCurrentCell(row, max(0, self.currentColumn()))
            return
        super().keyPressEvent(event)

    def context_menu(self, position):
        grid, renderer = self.grid, self.window.renderer
        index = self.indexAt(position)
        renderer.guard(lambda: grid.RaiseCellMouseDown(index.row(), index.column(), MouseButtons.Right, position.x(), position.y()))
        strip = grid.ContextMenuStrip
        if strip is not None:
            renderer.show_context_menu(strip, self.viewport().mapToGlobal(position), grid)


class GraphWidget(QtWidgets.QWidget):
    """ZedGraphControl drawn from its pane: the axis ranges and major steps the original code and AxisChange set
    (ZedGraph PickScale in the model; linear or log, X, Y and Y2), grids, curves (line style, circle symbols, missing
    points break the line), axis titles and the legend."""

    def __init__(self, window, control, parent):
        super().__init__(parent)
        self.window, self.control = window, control
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QtGui.QPalette.ColorRole.Window, qcolor(control.GraphPane.Fill.Color) if control.GraphPane.Fill.Type.ToString() != 'None' else QtGui.QColor('white'))
        self.setPalette(palette)

    @staticmethod
    def axis_map(scale, low, high, log):
        import math
        a, b = float(scale.Min), float(scale.Max)
        if log:
            a, b = math.log10(max(a, 1e-300)), math.log10(max(b, 1e-300))
            if b <= a:
                b = a + 1
            return lambda v: low + (math.log10(v) - a) / (b - a) * (high - low) if v > 0 else float('nan')
        if b <= a:
            b = a + 1
        return lambda v: low + (v - a) / (b - a) * (high - low)

    @staticmethod
    def ticks(scale, log):
        import math
        a, b, step = float(scale.Min), float(scale.Max), float(scale.MajorStep)
        if log:
            first, last = math.ceil(math.log10(max(a, 1e-300)) - 1e-9), math.floor(math.log10(max(b, 1e-300)) + 1e-9)
            step = max(1, int(round(step)))
            return [10.0 ** e for e in range(first, last + 1, step)][:200]
        if not (step > 0) or not math.isfinite(step) or (b - a) / step > 500:
            return [a, b]
        base = float(scale.BaseTic)
        start = base if base != System.Double.MaxValue and math.isfinite(base) else math.ceil(a / step - 1e-9) * step
        while start - step >= a - 1e-9 * step:
            start -= step
        values, v = [], start
        while v <= b + 1e-9 * step and len(values) < 500:
            values.append(0.0 if abs(v) < 1e-12 * step else v)
            v += step
        return values

    @staticmethod
    def label(value, step, log):
        import math
        if log:
            return f'{value:g}'
        if step <= 0 or not math.isfinite(step):
            return f'{value:g}'
        digits = max(0, -int(math.floor(math.log10(step)))) if step < 1 else 0
        return f'{value:.{digits}f}'

    def paintEvent(self, event):
        import math
        from ZedGraph import AxisType
        pane = self.control.GraphPane
        curves = [c for c in pane.CurveList if c.IsVisible]
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setFont(original_font())
        metrics = painter.fontMetrics()
        y2 = bool(pane.Y2Axis.IsVisible)
        legend = bool(pane.Legend.IsVisible) and len(curves) > 0
        top = 12 + (metrics.height() + 8 if legend else 0)
        x_title = str(pane.XAxis.Title.Text or '')
        title_lines = max(1, len(x_title.split('\n')))
        left, right, bottom = 70, 70 if y2 else 20, (1 + title_lines) * metrics.height() + 16
        plot = QtCore.QRectF(left, top, max(10, self.width() - left - right), max(10, self.height() - top - bottom))
        painter.fillRect(plot, qcolor(pane.Chart.Fill.Color) or QtGui.QColor('white'))
        logs = {name: getattr(pane, name).Type == AxisType.Log for name in ('XAxis', 'YAxis', 'Y2Axis')}
        px = self.axis_map(pane.XAxis.Scale, plot.left(), plot.right(), logs['XAxis'])
        py = self.axis_map(pane.YAxis.Scale, plot.bottom(), plot.top(), logs['YAxis'])
        py2 = self.axis_map(pane.Y2Axis.Scale, plot.bottom(), plot.top(), logs['Y2Axis'])
        xt, yt = self.ticks(pane.XAxis.Scale, logs['XAxis']), self.ticks(pane.YAxis.Scale, logs['YAxis'])
        y2t = self.ticks(pane.Y2Axis.Scale, logs['Y2Axis']) if y2 else []
        # Grids (dotted, as ZedGraph's dash 1/5).
        for axis, values, horizontal, mapping in ((pane.XAxis, xt, False, px), (pane.YAxis, yt, True, py)):
            if axis.MajorGrid.IsVisible:
                pen = QtGui.QPen(qcolor(axis.MajorGrid.Color) or QtGui.QColor('black'), 1)
                pen.setDashPattern([1, 5])
                painter.setPen(pen)
                for v in values:
                    p = mapping(v)
                    if math.isfinite(p):
                        if horizontal:
                            painter.drawLine(QtCore.QPointF(plot.left(), p), QtCore.QPointF(plot.right(), p))
                        else:
                            painter.drawLine(QtCore.QPointF(p, plot.top()), QtCore.QPointF(p, plot.bottom()))
        painter.setPen(QtGui.QPen(QtGui.QColor('black'), 1))
        painter.drawRect(plot)
        for x in xt:
            p = px(x)
            painter.drawLine(QtCore.QPointF(p, plot.bottom()), QtCore.QPointF(p, plot.bottom() - 5))
            text = self.label(x, float(pane.XAxis.Scale.MajorStep), logs['XAxis'])
            painter.drawText(QtCore.QPointF(p - metrics.horizontalAdvance(text) / 2, plot.bottom() + metrics.ascent() + 4), text)
        for y in yt:
            p = py(y)
            painter.drawLine(QtCore.QPointF(plot.left(), p), QtCore.QPointF(plot.left() + 5, p))
            text = self.label(y, float(pane.YAxis.Scale.MajorStep), logs['YAxis'])
            painter.drawText(QtCore.QPointF(plot.left() - metrics.horizontalAdvance(text) - 6, p + metrics.ascent() / 2 - 1), text)
        for y in y2t:
            p = py2(y)
            painter.drawLine(QtCore.QPointF(plot.right(), p), QtCore.QPointF(plot.right() - 5, p))
            text = self.label(y, float(pane.Y2Axis.Scale.MajorStep), logs['Y2Axis'])
            painter.drawText(QtCore.QPointF(plot.right() + 6, p + metrics.ascent() / 2 - 1), text)
        bold = QtGui.QFont(painter.font())
        bold.setBold(True)
        painter.setFont(bold)
        painter.drawText(QtCore.QRectF(plot.left(), plot.bottom() + metrics.height() + 6, plot.width(), title_lines * metrics.height() + 4), int(QtCore.Qt.AlignmentFlag.AlignHCenter), x_title)
        for title, x, angle in ((str(pane.YAxis.Title.Text or ''), 14, -90), (str(pane.Y2Axis.Title.Text or '') if y2 else '', self.width() - 14, 90)):
            if not title:
                continue
            painter.save()
            painter.translate(x, plot.center().y())
            painter.rotate(angle)
            painter.drawText(QtCore.QRectF(-plot.height() / 2, -metrics.height() / 2, plot.height(), metrics.height() + 4), int(QtCore.Qt.AlignmentFlag.AlignHCenter), title)
            painter.restore()
        painter.setFont(original_font())
        painter.setClipRect(plot.adjusted(-4, -4, 4, 4))
        dash = {'Dash': QtCore.Qt.PenStyle.DashLine, 'Dot': QtCore.Qt.PenStyle.DotLine, 'DashDot': QtCore.Qt.PenStyle.DashDotLine,
                'DashDotDot': QtCore.Qt.PenStyle.DashDotDotLine}
        missing = System.Double.MaxValue
        for curve in curves:
            color = qcolor(curve.Color) or QtGui.QColor('black')
            line = getattr(curve, 'Line', None)
            pen = QtGui.QPen(color, float(line.Width) if line is not None else 1)
            if line is not None:
                pen.setStyle(dash.get(str(line.Style), QtCore.Qt.PenStyle.SolidLine))
            mapy = py2 if curve.IsY2Axis else py
            segments, current = [], []
            for i in range(curve.Points.Count):
                point = curve.Points[i]
                x, y = float(point.X), float(point.Y)
                if x == missing or y == missing or not (math.isfinite(x) and math.isfinite(y)):
                    if current:
                        segments.append(current)
                    current = []
                    continue
                qx, qy = px(x), mapy(y)
                if not (math.isfinite(qx) and math.isfinite(qy)):
                    continue
                current.append(QtCore.QPointF(qx, qy))
            if current:
                segments.append(current)
            painter.setPen(pen)
            if line is None or line.IsVisible:
                for segment in segments:
                    painter.drawPolyline(QtGui.QPolygonF(segment))
            symbol = getattr(curve, 'Symbol', None)
            if symbol is not None and symbol.IsVisible and str(symbol.Type) != 'None':
                painter.setPen(QtGui.QPen(color, 1))
                painter.setBrush(QtGui.QBrush(qcolor(symbol.Fill.Color) if str(symbol.Fill.Type) != 'None' else QtGui.QColor('white')))
                radius = float(symbol.Size) / 2
                for segment in segments:
                    for point in segment:
                        painter.drawEllipse(point, radius, radius)
                painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.setClipping(False)
        if legend:
            entries = [(qcolor(c.Color) or QtGui.QColor('black'), str(c.Label.Text)) for c in curves if str(c.Label.Text)]
            widths = [34 + metrics.horizontalAdvance(text) + 12 for _, text in entries]
            x = plot.center().x() - sum(widths) / 2 if pane.Legend.Position == LegendPos.TopCenter else plot.left()
            y = 8 + metrics.height() / 2
            for (color, text), width in zip(entries, widths):
                painter.setPen(QtGui.QPen(color, 1))
                painter.drawLine(QtCore.QPointF(x, y), QtCore.QPointF(x + 28, y))
                painter.setBrush(QtGui.QBrush(QtGui.QColor('white')))
                painter.drawEllipse(QtCore.QPointF(x + 14, y), 3.5, 3.5)
                painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
                painter.setPen(QtGui.QPen(QtGui.QColor('black')))
                painter.drawText(QtCore.QPointF(x + 34, y + metrics.ascent() / 2 - 1), text)
                x += width
        painter.end()


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
            if not isinstance(child, (ListView, PropertyGrid, TabControl, DataGridView, ZedGraphControl, TreeView, TextBoxBase, FastColoredTextBox)):
                self.build(child, container)

    def create(self, control, parent):
        r = self.renderer
        if isinstance(control, PropertyGrid):
            return PropertyGridWidget(self, control, parent)
        if isinstance(control, ListView):
            return ListViewWidget(self, control, parent)
        if isinstance(control, DataGridView):
            return DataGridWidget(self, control, parent)
        if isinstance(control, ZedGraphControl):
            return GraphWidget(self, control, parent)
        if isinstance(control, TreeView):
            return oc.TreeWidget(self, control, parent)
        if isinstance(control, FastColoredTextBox):
            widget = oc.CodeEditor(self, control, parent)
            oc.AUTOCOMPLETE.install()
            oc.AUTOCOMPLETE.editors[control] = widget
            return widget
        if isinstance(control, SplitContainer):
            return oc.SplitFrame(self, control, parent)
        if isinstance(control, TrackBar):
            return oc.Slider(self, control, parent)
        if isinstance(control, ScrollBar):
            return oc.ScrollBarWidget(self, control, parent)
        if isinstance(control, ProgressBar):
            return QtWidgets.QProgressBar(parent)
        if isinstance(control, PictureBox):
            widget = QtWidgets.QLabel(parent)
            widget.setScaledContents(True)
            return widget
        if isinstance(control, LinkLabel):
            widget = QtWidgets.QLabel(f'<a href="#">{str(control.Text)}</a>', parent)
            widget.linkActivated.connect(lambda _link, c=control: r.input(c.RaiseLinkClicked))
            return widget
        if isinstance(control, TextBoxBase) and control.Multiline:
            return oc.OutputText(self, control, parent)
        if isinstance(control, GroupBox):
            if type(control).__name__ == 'CollapsableGroupBox':
                return oc.CollapsibleGroup(self, control, parent)
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
            return oc.SpinBox(self, control, parent)
        if isinstance(control, TabControl):
            widget = QtWidgets.QTabWidget(parent)
            # Every page the form ever added is built once; the shown tabs follow TabPages (forms remove and
            # re-add pages per item type).
            widget.page_widgets = {}
            for page in control.AllPages:
                page_widget = QtWidgets.QWidget()
                self.widgets[page] = page_widget
                self.build(page, page_widget)
                widget.page_widgets[page] = page_widget
            self.sync_tabs(control, widget)
            widget.currentChanged.connect(lambda index, c=control, w=widget: None if getattr(w, 'syncing_tabs', False) else r.input(lambda: setattr(c, 'SelectedIndex', index)))
            return widget
        # Panels and containers; a control with a Paint handler shows its own painting
        if control.HasPaintHandler:
            return oc.PaintedControl(self, control, parent)
        return QtWidgets.QFrame(parent)

    def sync_tabs(self, control, widget):
        pages = list(control.TabPages)
        for page in pages:
            if page not in widget.page_widgets:
                page_widget = QtWidgets.QWidget()
                self.widgets[page] = page_widget
                self.build(page, page_widget)
                widget.page_widgets[page] = page_widget
        shown = [widget.widget(i) for i in range(widget.count())]
        wanted = [widget.page_widgets[p] for p in pages]
        widget.syncing_tabs = True
        try:
            if shown != wanted:
                while widget.count():
                    widget.removeTab(0)
                for page in pages:
                    widget.addTab(widget.page_widgets[page], str(page.Text))
            for i, page in enumerate(pages):
                if widget.tabText(i) != str(page.Text):
                    widget.setTabText(i, str(page.Text))
            if widget.currentIndex() != control.SelectedIndex:
                widget.setCurrentIndex(control.SelectedIndex)
        finally:
            widget.syncing_tabs = False

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
        if isinstance(widget, (QtWidgets.QPushButton, QtWidgets.QCheckBox, QtWidgets.QRadioButton, QtWidgets.QLabel)) and not isinstance(control, (LinkLabel, PictureBox)):
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
        if isinstance(widget, QtWidgets.QTabWidget) and isinstance(control, TabControl):
            self.sync_tabs(control, widget)
        if isinstance(widget, (oc.SpinBox, oc.Slider, oc.ScrollBarWidget, oc.OutputText)):
            widget.sync()
        if isinstance(widget, QtWidgets.QProgressBar):
            from System.Windows.Forms import ProgressBarStyle
            if control.Style == ProgressBarStyle.Marquee:
                widget.setRange(0, 0)
            else:
                widget.setRange(control.Minimum, control.Maximum)
                widget.setValue(control.Value)
        if isinstance(control, PictureBox) and isinstance(widget, QtWidgets.QLabel):
            icon = self.renderer.icon(control.Image)
            if icon is not None and widget.pixmap().isNull():
                widget.setPixmap(icon.pixmap(bounds.Width, bounds.Height))
        if isinstance(control, LinkLabel) and isinstance(widget, QtWidgets.QLabel):
            widget.setText(f'<a href="#">{str(control.Text)}</a>')

    def refresh_control(self, control):
        widget = self.widgets.get(control)
        if isinstance(widget, PropertyGridWidget):
            widget.rebuild()
        elif isinstance(widget, (ListViewWidget, DataGridWidget)):
            widget.rebuild()
        elif isinstance(widget, GraphWidget):
            widget.update()
        elif isinstance(widget, oc.TreeWidget):
            widget.rebuild()
        elif isinstance(widget, oc.OutputText):
            widget.sync(scroll_to_end=True)
        elif isinstance(widget, oc.CodeEditor):
            widget.rebuild()
        elif isinstance(widget, oc.PaintedControl):
            widget.update()

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
        # The grid's copy/paste reaches the platform clipboard (text; private formats stay in the model).
        self.clipboard_get = System.Func[System.String](lambda: QtWidgets.QApplication.clipboard().text())
        self.clipboard_set = System.Action[System.String](lambda text: QtWidgets.QApplication.clipboard().setText(str(text)))
        Clipboard.GetTextHandler, Clipboard.SetTextHandler = self.clipboard_get, self.clipboard_set
        self.services = oc.ToolkitServices(self)
        self.update_screens()

    def show_context_menu(self, strip, global_position, owner=None):
        """The control's ContextMenuStrip: Opening (may cancel), then its visible items."""
        if not self.guard(lambda: strip.OpenFor(owner)):
            return
        menu = QtWidgets.QMenu(self.main_window)
        for item in strip.Items:
            if not item.Visible:
                continue
            if isinstance(item, ToolStripSeparator):
                menu.addSeparator()
                continue
            action = menu.addAction(str(item.Text))
            icon = self.icon(item.Image)
            if icon is not None:
                action.setIcon(icon)
            action.setEnabled(bool(item.Enabled))
            action.triggered.connect(lambda checked=False, i=item: self.input(i.PerformClick))
        menu.exec(global_position)

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
        if prop in ('SelectedObject', 'Refresh', 'Items', 'Expanded', 'Autocomplete', 'LabelRatio', 'Columns', 'Grid', 'Graph',
                    'Tree', 'TreeEdit', 'ScrollToEnd'):
            self.refresh.add(control)
        if isinstance(control, DataGridView) and prop == 'Layout':
            self.refresh.add(control)
        if isinstance(control, FastColoredTextBox):
            if prop in ('Text', 'Selection', 'Refresh', 'Layout'):
                self.refresh.add(control)
            if prop == 'ScrollToCaret':
                self.refresh.add(('caret', control))
            self.sync_soon()
            return
        if prop in ('SelectedGridItem', 'Selection'):
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
                if isinstance(widget, oc.CodeEditor):
                    widget.scroll_to_caret()
                    widget.viewport().update()
                    continue
                if isinstance(widget, DataGridWidget):
                    if control not in refresh:
                        widget.select_current()
                    continue
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
        path, name = str(image.Path), str(image.Name)
        key = path + '#' + name if path.endswith('.resx') else path
        if key not in self.icons:
            if path.endswith('.resx'):
                # Designer image stored in the form's .resx: base64 image bytes (no deserialization).
                import base64
                import xml.etree.ElementTree as ET
                pixmap = QtGui.QPixmap()
                for data in ET.parse(ROOT / path).getroot().iter('data'):
                    if data.get('name') == name and 'base64' in (data.get('mimetype') or ''):
                        pixmap.loadFromData(base64.b64decode(''.join((data.findtext('value') or '').split())))
                self.icons[key] = QtGui.QIcon(pixmap) if not pixmap.isNull() else None
            else:
                self.icons[key] = QtGui.QIcon(str(ROOT / path))
        return self.icons[key]

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
        elif editor == 'EnvVarsUIEditor':
            # The original editor shows the original modal FrmGetEnvVars.
            from PrePoMaxX.UI import OriginalEditors
            self.input(lambda: OriginalEditors.EditModal(grid, grid_item))
        elif editor == 'SinglePointDataEditor':
            from PrePoMaxX.UI import OriginalEditors
            self.input(lambda: OriginalEditors.EditSinglePoint(grid, grid_item))
        elif editor in ('ColorEditorEx', 'ColorEditor'):
            color = QtWidgets.QColorDialog.getColor(parent=self.main_window, options=QtWidgets.QColorDialog.ColorDialogOption.ShowAlphaChannel)
            if color.isValid():
                self.input(lambda: grid.SetValueFromText(grid_item, f'{color.alpha()}, {color.red()}, {color.green()}, {color.blue()}'))
        self.flush()

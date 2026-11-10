"""Qt widgets for the original controls added in C11 (child-window forms and dialogs).

TreeView (the original CodersLabTreeView), NumericUpDown, TrackBar, scroll bars, progress bars, link labels,
multiline/auto-scrolling text boxes and the collapsible group box are drawn from the headless control model
(X/UI/FormsCompat) and user input is fed back through the WinForms events, as in original_forms.py. The module also
installs the toolkit services of the model: UI timers, common file dialogs, text measurement, message-box closing
and the UI-thread marshalling of Control.Invoke/BeginInvoke.
"""
import re

import System
from PyQt6 import QtCore, QtGui, QtWidgets
from System.Windows.Forms import (Control, DialogResult, FileDialog, Keys, MessageBox, MouseButtons, ScrollEventType,
                                  TextRenderer, Timer)


def qcolor(color, fallback=None):
    if color is None or color.IsEmpty:
        return fallback
    return QtGui.QColor(color.R, color.G, color.B, color.A)


def mouse_button(button):
    return {QtCore.Qt.MouseButton.LeftButton: MouseButtons.Left, QtCore.Qt.MouseButton.RightButton: MouseButtons.Right,
            QtCore.Qt.MouseButton.MiddleButton: MouseButtons.Middle}.get(button, getattr(MouseButtons, 'None'))


def winforms_keys(event):
    """Qt key event -> WinForms Keys (key code | modifiers); None for keys the model does not route."""
    table = {QtCore.Qt.Key.Key_Up: Keys.Up, QtCore.Qt.Key.Key_Down: Keys.Down, QtCore.Qt.Key.Key_Left: Keys.Left,
             QtCore.Qt.Key.Key_Right: Keys.Right, QtCore.Qt.Key.Key_Home: Keys.Home, QtCore.Qt.Key.Key_End: Keys.End,
             QtCore.Qt.Key.Key_PageUp: Keys.PageUp, QtCore.Qt.Key.Key_PageDown: Keys.PageDown,
             QtCore.Qt.Key.Key_Delete: Keys.Delete, QtCore.Qt.Key.Key_F2: Keys.F2, QtCore.Qt.Key.Key_Return: Keys.Enter,
             QtCore.Qt.Key.Key_Enter: Keys.Enter, QtCore.Qt.Key.Key_Escape: Keys.Escape, QtCore.Qt.Key.Key_Space: Keys.Space,
             QtCore.Qt.Key.Key_Tab: Keys.Tab}
    key = event.key()
    code = table.get(key)
    if code is None and QtCore.Qt.Key.Key_A <= key <= QtCore.Qt.Key.Key_Z:
        code = getattr(Keys, chr(key))
    if code is None:
        return None
    modifiers = event.modifiers()
    if modifiers & QtCore.Qt.KeyboardModifier.ShiftModifier:
        code = code | Keys.Shift
    if modifiers & (QtCore.Qt.KeyboardModifier.ControlModifier | QtCore.Qt.KeyboardModifier.MetaModifier):
        code = code | Keys.Control
    if modifiers & QtCore.Qt.KeyboardModifier.AltModifier:
        code = code | Keys.Alt
    return code


def set_modifier_keys(event):
    keys = getattr(Keys, 'None')
    modifiers = event.modifiers()
    if modifiers & QtCore.Qt.KeyboardModifier.ShiftModifier:
        keys = keys | Keys.Shift
    if modifiers & (QtCore.Qt.KeyboardModifier.ControlModifier | QtCore.Qt.KeyboardModifier.MetaModifier):
        keys = keys | Keys.Control
    Control.ModifierKeys = keys


class TreeWidget(QtWidgets.QAbstractScrollArea):
    """TreeView drawn from the model rows: the native layout (row height, indent, +/- boxes, images, label
    rectangles) with the node colours the original CodersLabTreeView sets for its own selection."""

    def __init__(self, window, tree, parent):
        super().__init__(parent)
        self.window, self.tree = window, tree
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.verticalScrollBar().valueChanged.connect(self.scrolled)
        self.editor = None
        self.last_press = None

    def rebuild(self):
        rows = len(self.tree.RenderRows())
        page = max(1, (self.tree.ClientSize.Height - 4) // max(1, self.tree.ItemHeight))
        bar = self.verticalScrollBar()
        bar.blockSignals(True)
        bar.setRange(0, max(0, rows - page))
        bar.setPageStep(page)
        bar.setValue(self.tree.TopRow)
        bar.blockSignals(False)
        self.sync_editor()
        self.viewport().update()

    def scrolled(self, value):
        self.window.renderer.input(lambda: self.tree.UserScroll(value))

    def node_image(self, node, selected):
        images = self.tree.ImageList
        if images is None:
            return None
        key = str(node.SelectedImageKey if selected and node.SelectedImageKey else node.ImageKey or self.tree.ImageKey or '')
        index = node.SelectedImageIndex if selected and node.SelectedImageIndex >= 0 else node.ImageIndex
        if index < 0:
            index = self.tree.ImageIndex
        image = None
        if key and images.Images.ContainsKey(key):
            image = images.Images[key]
        elif 0 <= index < images.Images.Count:
            image = images.Images[index]
        return self.window.renderer.icon(image) if image is not None else None

    def paintEvent(self, event):
        tree = self.tree
        painter = QtGui.QPainter(self.viewport())
        painter.fillRect(self.viewport().rect(), qcolor(tree.BackColor, QtGui.QColor('white')))
        painter.setFont(self.font())
        metrics = painter.fontMetrics()
        rows = list(tree.RenderRows())
        top, height, indent = tree.TopRow, tree.ItemHeight, tree.Indent
        selected = tree.SelectedNode
        for i in range(top, len(rows)):
            node = rows[i]
            y = 2 + (i - top) * height
            if y > self.viewport().height():
                break
            x = tree.NodeIndentX(node)
            if node.Nodes.Count > 0 and tree.ShowPlusMinus:
                box = QtCore.QRect(x - indent // 2 - 4, y + height // 2 - 4, 8, 8)
                painter.setPen(QtGui.QColor(150, 150, 150))
                painter.drawRect(box)
                painter.setPen(QtGui.QColor('black'))
                painter.drawLine(box.left() + 2, box.center().y(), box.right() - 2, box.center().y())
                if not node.IsExpanded:
                    painter.drawLine(box.center().x(), box.top() + 2, box.center().x(), box.bottom() - 2)
            icon = self.node_image(node, node == selected)
            if icon is not None:
                size = tree.ImageList.ImageSize
                icon.paint(painter, QtCore.QRect(x, y + (height - size.Height) // 2, size.Width, size.Height))
            bounds = node.Bounds
            back = qcolor(node.BackColor)
            fore = qcolor(node.ForeColor, qcolor(tree.ForeColor, QtGui.QColor('black')))
            if node == selected and back is None and (self.hasFocus() or not tree.HideSelection):
                back, fore = self.palette().highlight().color(), self.palette().highlightedText().color()
            if back is not None:
                painter.fillRect(QtCore.QRect(bounds.X, bounds.Y, bounds.Width, bounds.Height), back)
            painter.setPen(fore)
            painter.drawText(QtCore.QRect(bounds.X + 3, bounds.Y, bounds.Width, bounds.Height),
                             int(QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignLeft), str(node.Text))
        painter.end()

    def sync_editor(self):
        node = self.tree.EditingNode
        if node is None:
            if self.editor is not None:
                self.editor.deleteLater()
                self.editor = None
            return
        if self.editor is None:
            self.editor = QtWidgets.QLineEdit(str(node.Text), self.viewport())
            self.editor.editingFinished.connect(self.finish_edit)
            self.editor.show()
            self.editor.setFocus()
            self.editor.selectAll()
        bounds = node.Bounds
        self.editor.setGeometry(bounds.X, bounds.Y, max(bounds.Width + 40, 80), bounds.Height)

    def finish_edit(self):
        editor = self.editor
        if editor is None:
            return
        text = editor.text()
        self.window.renderer.input(lambda: self.tree.UserEndEdit(False, text))

    def mousePressEvent(self, event):
        set_modifier_keys(event)
        position, button = event.position().toPoint(), mouse_button(event.button())
        # Qt sends the second press of a double click before its double-click event; Windows sends only
        # WM_LBUTTONDBLCLK, so that press is not passed on (the double-click event follows it).
        last = getattr(self, 'last_release', None)
        if last is not None and last[0].elapsed() <= QtWidgets.QApplication.doubleClickInterval() and \
                (last[1] - position).manhattanLength() <= QtWidgets.QApplication.startDragDistance():
            self.last_release = None
            return
        self.last_press = (position.x(), position.y())
        self.setFocus()
        self.window.renderer.input(lambda: self.tree.UserMouseDown(button, 1, position.x(), position.y()))

    def mouseDoubleClickEvent(self, event):
        set_modifier_keys(event)
        position, button = event.position().toPoint(), mouse_button(event.button())
        self.last_press = 'double'
        self.window.renderer.input(lambda: self.tree.UserMouseDown(button, 2, position.x(), position.y()))

    def mouseReleaseEvent(self, event):
        set_modifier_keys(event)
        position, button = event.position().toPoint(), mouse_button(event.button())
        clicks = 2 if self.last_press == 'double' else 1
        self.last_press = None
        if clicks == 1:
            timer = QtCore.QElapsedTimer()
            timer.start()
            self.last_release = (timer, position)
        else:
            self.last_release = None
        self.window.renderer.input(lambda: self.tree.UserMouseUp(button, clicks, position.x(), position.y()))
        if button == MouseButtons.Right and self.tree.ContextMenuStrip is not None:
            self.window.renderer.show_context_menu(self.tree.ContextMenuStrip, self.viewport().mapToGlobal(position))

    def mouseMoveEvent(self, event):
        position = event.position().toPoint()
        self.window.renderer.input(lambda: self.tree.UserMouseMove(position.x(), position.y()))

    def leaveEvent(self, event):
        self.window.renderer.input(self.tree.RaiseMouseLeave)

    def wheelEvent(self, event):
        steps = -event.angleDelta().y() // 120 * 3
        bar = self.verticalScrollBar()
        bar.setValue(max(bar.minimum(), min(bar.maximum(), bar.value() + steps)))

    def keyPressEvent(self, event):
        keys = winforms_keys(event)
        if keys is not None:
            set_modifier_keys(event)
            self.window.renderer.input(lambda: self.tree.RaiseKeyDown(keys))
            return
        super().keyPressEvent(event)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.viewport().update()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.viewport().update()


class SpinBox(QtWidgets.QDoubleSpinBox):
    """NumericUpDown: the range, increment and decimals of the model; typed or spun values are constrained."""

    def __init__(self, window, control, parent):
        super().__init__(parent)
        self.window, self.control = window, control
        self.setKeyboardTracking(False)
        self.valueChanged.connect(self.changed)
        self.sync()

    def sync(self):
        c = self.control
        self.blockSignals(True)
        self.setDecimals(int(c.DecimalPlaces))
        self.setRange(float(System.Decimal.ToDouble(c.Minimum)), float(System.Decimal.ToDouble(c.Maximum)))
        self.setSingleStep(float(System.Decimal.ToDouble(c.Increment)))
        self.setValue(float(System.Decimal.ToDouble(c.Value)))
        self.setReadOnly(bool(c.ReadOnly))
        self.blockSignals(False)

    def changed(self, value):
        self.window.renderer.input(lambda: self.control.UserSetValue(System.Decimal(value)))


class Slider(QtWidgets.QSlider):
    """TrackBar: user moves raise Scroll then ValueChanged."""

    def __init__(self, window, control, parent):
        from System.Windows.Forms import Orientation
        super().__init__(QtCore.Qt.Orientation.Vertical if control.Orientation == Orientation.Vertical else QtCore.Qt.Orientation.Horizontal, parent)
        self.window, self.control = window, control
        self.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.valueChanged.connect(self.changed)
        self.sync()

    def sync(self):
        c = self.control
        self.blockSignals(True)
        self.setRange(c.Minimum, c.Maximum)
        self.setSingleStep(c.SmallChange)
        self.setPageStep(c.LargeChange)
        self.setTickInterval(max(1, c.TickFrequency))
        self.setValue(c.Value)
        self.blockSignals(False)

    def changed(self, value):
        self.window.renderer.input(lambda: self.control.UserScroll(value))


class ScrollBarWidget(QtWidgets.QScrollBar):
    """HScrollBar/VScrollBar: WinForms reaches Maximum - LargeChange + 1; Scroll is raised with the event type."""

    def __init__(self, window, control, parent):
        from System.Windows.Forms import HScrollBar
        super().__init__(QtCore.Qt.Orientation.Horizontal if isinstance(control, HScrollBar) else QtCore.Qt.Orientation.Vertical, parent)
        self.window, self.control = window, control
        self.action = ScrollEventType.ThumbPosition
        self.actionTriggered.connect(self.triggered)
        self.valueChanged.connect(self.changed)
        self.sync()

    def sync(self):
        c = self.control
        self.blockSignals(True)
        self.setRange(c.Minimum, max(c.Minimum, c.Maximum - c.LargeChange + 1))
        self.setSingleStep(c.SmallChange)
        self.setPageStep(c.LargeChange)
        self.setValue(c.Value)
        self.blockSignals(False)

    def triggered(self, action):
        A = QtWidgets.QAbstractSlider.SliderAction
        self.action = {A.SliderSingleStepAdd: ScrollEventType.SmallIncrement, A.SliderSingleStepSub: ScrollEventType.SmallDecrement,
                       A.SliderPageStepAdd: ScrollEventType.LargeIncrement, A.SliderPageStepSub: ScrollEventType.LargeDecrement,
                       A.SliderToMinimum: ScrollEventType.First, A.SliderToMaximum: ScrollEventType.Last,
                       A.SliderMove: ScrollEventType.ThumbTrack}.get(action, ScrollEventType.ThumbPosition)

    def changed(self, value):
        kind = self.action
        self.window.renderer.input(lambda: self.control.UserScroll(kind, value))


class OutputText(QtWidgets.QPlainTextEdit):
    """Multiline TextBox (and the AutoScrollTextBox stand-in): the view follows the end only when it was at the end."""

    def __init__(self, window, control, parent):
        super().__init__(parent)
        self.window, self.control = window, control
        self.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.WidgetWidth if control.WordWrap else QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        self.setReadOnly(bool(control.ReadOnly))
        self.sync()

    def sync(self, scroll_to_end=False):
        text = str(self.control.Text).replace('\r\n', '\n')
        if self.toPlainText() == text and not scroll_to_end:
            return
        bar = self.verticalScrollBar()
        at_end = bar.value() >= bar.maximum() - 1
        position = bar.value()
        current = self.toPlainText()
        if text.startswith(current) and current:
            cursor = self.textCursor()
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
            cursor.insertText(text[len(current):])
        else:
            self.setPlainText(text)
        if at_end or scroll_to_end:
            bar.setValue(bar.maximum())
        else:
            bar.setValue(position)
        self.setReadOnly(bool(self.control.ReadOnly))

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if not self.isReadOnly() and self.toPlainText() != str(self.control.Text).replace('\r\n', '\n'):
            text = self.toPlainText().replace('\n', '\r\n')
            self.window.renderer.input(lambda: (self.control.SetUserText(text), self.control.RaiseLeave()))


class CollapsibleGroup(QtWidgets.QGroupBox):
    """GroupBox whose mouse release reaches the control (CollapsableGroupBox toggles on its +/- button)."""

    def __init__(self, window, control, parent):
        super().__init__(str(control.Text), parent)
        self.window, self.control = window, control

    def mouseReleaseEvent(self, event):
        position, button = event.position().toPoint(), mouse_button(event.button())
        self.window.renderer.input(lambda: self.control.RaiseMouse('up', button, 1, position.x(), position.y()))
        super().mouseReleaseEvent(event)


def qt_filter(winforms_filter):
    """'Text files|*.txt;*.csv|All|*.*' -> 'Text files (*.txt *.csv);;All (*.*)'."""
    parts = str(winforms_filter or '').split('|')
    return ';;'.join(f'{parts[i]} ({parts[i + 1].replace(";", " ")})' for i in range(0, len(parts) - 1, 2))


class ToolkitServices:
    """Installs the model's toolkit services: timers, file dialogs, text measurement, message-box closing and the
    UI-thread context of Control.Invoke/BeginInvoke."""

    def __init__(self, renderer):
        self.renderer = renderer
        self.timers = {}
        self.timer_handler = System.Action[Timer](self.timer_changed)
        Timer.StateChanged += self.timer_handler
        self.file_handler = System.Func[FileDialog, System.Windows.Forms.IWin32Window, DialogResult](self.file_dialog)
        FileDialog.ShowHandler = self.file_handler
        self.measure_handler = System.Func[System.String, System.Windows.Forms.FontSpec, System.Drawing.Size](self.measure)
        TextRenderer.MeasureHandler = self.measure_handler
        self.close_handler = System.Action[System.IntPtr](self.close_message_box)
        MessageBox.CloseHandler = self.close_handler
        self.metrics = {}

    def timer_changed(self, timer):
        qt = self.timers.get(timer)
        if not timer.Enabled:
            if qt is not None:
                qt.stop()
            return
        if qt is None:
            qt = QtCore.QTimer()
            qt.timeout.connect(lambda t=timer: self.renderer.input(t.RaiseTick))
            self.timers[timer] = qt
        qt.start(int(timer.Interval))

    def file_dialog(self, dialog, owner):
        filters = qt_filter(dialog.Filter)
        start = str(dialog.FileName or dialog.InitialDirectory or '')
        parent = self.renderer.main_window
        if dialog.IsSave:
            path, _ = QtWidgets.QFileDialog.getSaveFileName(parent, str(dialog.Title or 'Save As'), start, filters)
            paths = [path] if path else []
        elif getattr(dialog, 'Multiselect', False):
            paths, _ = QtWidgets.QFileDialog.getOpenFileNames(parent, str(dialog.Title or 'Open'), start, filters)
        else:
            path, _ = QtWidgets.QFileDialog.getOpenFileName(parent, str(dialog.Title or 'Open'), start, filters)
            paths = [path] if path else []
        if not paths:
            return DialogResult.Cancel
        dialog.FileName = paths[0]
        dialog.FileNames = System.Array[System.String](paths)
        return DialogResult.OK

    def measure(self, text, font):
        key = (str(font.Name), float(font.Size), bool(font.Bold))
        metrics = self.metrics.get(key)
        if metrics is None:
            from original_forms import original_font
            qfont = original_font()
            qfont.setPixelSize(max(1, round(float(font.Size) * 96 / 72)))
            qfont.setBold(bool(font.Bold))
            metrics = self.metrics[key] = QtGui.QFontMetrics(qfont)
        return System.Drawing.Size(metrics.horizontalAdvance(str(text)), metrics.height())

    def close_message_box(self, handle):
        # WM_CLOSE to the open box (from the AutoClosingMessageBox timer thread): the active modal message box is
        # closed on the user-interface thread (its Escape answer).
        def close():
            box = QtWidgets.QApplication.activeModalWidget()
            if isinstance(box, QtWidgets.QMessageBox):
                box.reject()
        self.renderer.main_window.dispatcher.post(close)

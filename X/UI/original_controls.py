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


# Code editor (C12): FastColoredTextBox drawn from the model --------------------------------------------------------------
QT_KEYS = None


def full_winforms_keys(event):
    """Every Qt key the code editor routes -> WinForms Keys (key code | modifiers); unknown keys give only the
    modifiers (their character still arrives as WM_CHAR)."""
    global QT_KEYS
    K, Q = Keys, QtCore.Qt.Key
    if QT_KEYS is None:
        QT_KEYS = {Q.Key_Up: K.Up, Q.Key_Down: K.Down, Q.Key_Left: K.Left, Q.Key_Right: K.Right, Q.Key_Home: K.Home,
                   Q.Key_End: K.End, Q.Key_PageUp: K.PageUp, Q.Key_PageDown: K.PageDown, Q.Key_Delete: K.Delete,
                   Q.Key_Insert: K.Insert, Q.Key_Backspace: K.Back, Q.Key_Return: K.Enter, Q.Key_Enter: K.Enter,
                   Q.Key_Escape: K.Escape, Q.Key_Space: K.Space, Q.Key_Tab: K.Tab, Q.Key_Backtab: K.Tab,
                   Q.Key_Period: K.OemPeriod, Q.Key_Comma: K.Oemcomma, Q.Key_Minus: K.OemMinus, Q.Key_Plus: K.Oemplus,
                   Q.Key_Equal: K.Oemplus, Q.Key_Slash: K.OemQuestion, Q.Key_Question: K.OemQuestion,
                   Q.Key_Semicolon: K.OemSemicolon, Q.Key_Colon: K.OemSemicolon, Q.Key_BracketLeft: K.OemOpenBrackets,
                   Q.Key_BracketRight: K.OemCloseBrackets, Q.Key_Backslash: K.OemPipe, Q.Key_Apostrophe: K.OemQuotes,
                   Q.Key_QuoteDbl: K.OemQuotes, Q.Key_QuoteLeft: K.Oemtilde, Q.Key_ParenLeft: K.D9, Q.Key_ParenRight: K.D0,
                   Q.Key_Underscore: K.OemMinus, Q.Key_Shift: K.ShiftKey, Q.Key_Control: K.ControlKey,
                   Q.Key_Meta: K.ControlKey, Q.Key_Alt: K.Menu}
        for i in range(1, 13):
            QT_KEYS[getattr(Q, f'Key_F{i}')] = getattr(K, f'F{i}')
    key = event.key()
    code = QT_KEYS.get(key)
    if code is None and Q.Key_A <= key <= Q.Key_Z:
        code = getattr(K, chr(key))
    if code is None and Q.Key_0 <= key <= Q.Key_9:
        code = getattr(K, f'D{chr(key)}')
    if code is None:
        code = getattr(K, 'None')
    modifiers = event.modifiers()
    if modifiers & QtCore.Qt.KeyboardModifier.ShiftModifier or key == Q.Key_Backtab:
        code = code | K.Shift
    if modifiers & (QtCore.Qt.KeyboardModifier.ControlModifier | QtCore.Qt.KeyboardModifier.MetaModifier):
        code = code | K.Control
    if modifiers & QtCore.Qt.KeyboardModifier.AltModifier:
        code = code | K.Alt
    return code


def editor_font(font):
    """The editor's monospace font (Consolas/Courier New on Windows; the platform fixed font when missing)."""
    qfont = QtGui.QFont(str(font.Name))
    if not QtGui.QFontInfo(qfont).fixedPitch():
        qfont = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.SystemFont.FixedFont)
    qfont.setPixelSize(max(1, round(float(font.Size) * 96 / 72)))
    return qfont


class CodeEditor(QtWidgets.QAbstractScrollArea):
    """FastColoredTextBox: the model's lines with their style runs, selection, caret, current line, line numbers
    and bookmarks; keys go to the model as WM_KEYDOWN/WM_CHAR and mouse positions as places."""

    def __init__(self, window, control, parent):
        super().__init__(parent)
        self.window, self.control = window, control
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.viewport().setCursor(QtCore.Qt.CursorShape.IBeamCursor)
        self.setFrameShape(QtWidgets.QFrame.Shape.Box if int(control.BorderStyle) != 0 else QtWidgets.QFrame.Shape.NoFrame)
        self.verticalScrollBar().valueChanged.connect(self.scrolled)
        self.horizontalScrollBar().valueChanged.connect(self.scrolled)
        self.font_key = None
        self.caret_on = True
        self.blink = QtCore.QTimer(self)
        self.blink.timeout.connect(self.toggle_caret)
        self.blink.start(500)
        self.update_metrics()

    def update_metrics(self):
        font = self.control.Font
        key = (str(font.Name), float(font.Size), int(self.control.Zoom))
        if key == self.font_key:
            return
        self.font_key = key
        self.qfont = editor_font(font)
        if int(self.control.Zoom) != 100:
            self.qfont.setPixelSize(max(1, round(self.qfont.pixelSize() * int(self.control.Zoom) / 100)))
        self.metrics = QtGui.QFontMetrics(self.qfont)
        self.char_width = max(1, self.metrics.horizontalAdvance('W'))
        self.char_height = max(1, self.metrics.height())

    def gutter_width(self):
        if not self.control.ShowLineNumbers:
            return 0
        digits = max(int(self.control.ReservedCountOfLineNumberChars), len(str(int(self.control.LinesCount))))
        return digits * self.char_width + 12

    def report_geometry(self):
        c = self.control
        c.CharWidth, c.CharHeight = self.char_width, self.char_height
        c.LeftIndent = self.gutter_width() + 3
        c.VerticalScrollValue = self.verticalScrollBar().value()
        c.HorizontalScrollValue = self.horizontalScrollBar().value()

    def rebuild(self):
        self.update_metrics()
        c = self.control
        lines = int(c.LinesCount)
        line_height = self.char_height + int(c.LineInterval)
        bar = self.verticalScrollBar()
        bar.setRange(0, max(0, lines * line_height - self.viewport().height() + line_height))
        bar.setSingleStep(line_height)
        bar.setPageStep(max(line_height, self.viewport().height()))
        longest = max((len(str(c.GetLineText(i))) for i in range(lines)), default=0) if lines < 20000 else 400
        hbar = self.horizontalScrollBar()
        hbar.setRange(0, max(0, self.gutter_width() + longest * self.char_width + 40 - self.viewport().width()))
        hbar.setPageStep(self.viewport().width())
        self.report_geometry()
        self.viewport().update()

    def scroll_to_caret(self):
        self.update_metrics()
        caret = self.control.Selection.Start
        line_height = self.char_height + int(self.control.LineInterval)
        top = caret.iLine * line_height
        bar = self.verticalScrollBar()
        if top < bar.value():
            bar.setValue(top)
        elif top + line_height > bar.value() + self.viewport().height():
            bar.setValue(top + line_height - self.viewport().height())
        x = self.gutter_width() + caret.iChar * self.char_width
        hbar = self.horizontalScrollBar()
        if x < hbar.value() + self.gutter_width():
            hbar.setValue(max(0, x - self.gutter_width() - 20))
        elif x > hbar.value() + self.viewport().width() - 10:
            hbar.setValue(x - self.viewport().width() + 40)
        self.report_geometry()

    def scrolled(self, _value):
        self.report_geometry()
        self.viewport().update()
        self.window.renderer.input(self.control.RaiseScroll)

    def toggle_caret(self):
        self.caret_on = not self.caret_on
        if self.hasFocus():
            self.viewport().update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.rebuild()

    def paintEvent(self, event):
        c = self.control
        painter = QtGui.QPainter(self.viewport())
        painter.setFont(self.qfont)
        back = QtGui.QColor(c.BackColor.R, c.BackColor.G, c.BackColor.B) if not c.BackColor.IsEmpty else QtGui.QColor('white')
        if not c.Enabled:
            back = back.darker(105)
        painter.fillRect(self.viewport().rect(), back)
        line_height = self.char_height + int(c.LineInterval)
        top = self.verticalScrollBar().value()
        left = self.gutter_width() + 3 - self.horizontalScrollBar().value()
        first = max(0, top // line_height)
        last = min(int(c.LinesCount) - 1, (top + self.viewport().height()) // line_height + 1)
        selection = c.Selection
        start, end = selection.Start, selection.End
        if (start.iLine, start.iChar) > (end.iLine, end.iChar):
            start, end = end, start
        fore_default = QtGui.QColor(c.ForeColor.R, c.ForeColor.G, c.ForeColor.B)
        current_line = qcolor(c.CurrentLineColor)
        selection_color = qcolor(c.SelectionColor) or QtGui.QColor(0, 0, 255, 60)
        if selection_color.alpha() == 255:
            selection_color.setAlpha(60)
        bookmarks = {int(b.LineIndex) for b in c.Bookmarks}
        for i in range(first, last + 1):
            y = i * line_height - top
            if current_line is not None and current_line.alpha() > 0 and i == c.Selection.Start.iLine and selection.IsEmpty:
                painter.fillRect(QtCore.QRect(0, y, self.viewport().width(), line_height), current_line)
            text = str(c.GetLineText(i))
            runs = list(c.GetLineRuns(i))
            for k in range(0, len(runs), 6):
                s, n, fore, bg, style, marker = runs[k:k + 6]
                x = left + s * self.char_width
                rect = QtCore.QRect(x, y, n * self.char_width, line_height)
                if bg:
                    painter.fillRect(rect, QtGui.QColor.fromRgba(bg & 0xffffffff))
                if marker:
                    painter.setPen(QtCore.Qt.PenStyle.NoPen)
                    painter.setBrush(QtGui.QColor.fromRgba(marker & 0xffffffff))
                    painter.drawRoundedRect(QtCore.QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5), 3, 3)
                    painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
                font = QtGui.QFont(self.qfont)
                font.setBold(bool(style & 1))
                font.setItalic(bool(style & 2))
                font.setUnderline(bool(style & 4))
                painter.setFont(font)
                painter.setPen(QtGui.QColor.fromRgba(fore & 0xffffffff) if fore else fore_default)
                for j, ch in enumerate(text[s:s + n]):
                    painter.drawText(QtCore.QRect(x + j * self.char_width, y, self.char_width, line_height),
                                     QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter, ch)
            painter.setFont(self.qfont)
            if start != end and start.iLine <= i <= end.iLine:
                a = start.iChar if i == start.iLine else 0
                b = end.iChar if i == end.iLine else len(text) + 1
                painter.fillRect(QtCore.QRect(left + a * self.char_width, y, max(0, b - a) * self.char_width, line_height), selection_color)
        # Gutter: line numbers and bookmarks
        gutter = self.gutter_width()
        if gutter:
            painter.fillRect(QtCore.QRect(0, 0, gutter, self.viewport().height()), back)
            painter.setPen(qcolor(c.LineNumberColor) or QtGui.QColor('teal'))
            for i in range(first, last + 1):
                y = i * line_height - top
                if i in bookmarks:
                    painter.fillRect(QtCore.QRect(1, y + 1, 6, line_height - 2), qcolor(c.BookmarkColor) or QtGui.QColor('powderblue'))
                painter.drawText(QtCore.QRect(0, y, gutter - 6, line_height),
                                 QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter, str(i + 1))
            painter.setPen(qcolor(c.ServiceLinesColor) or QtGui.QColor('silver'))
            painter.drawLine(gutter, 0, gutter, self.viewport().height())
        # Caret
        if self.hasFocus() and self.caret_on and c.CaretVisible:
            caret = c.Selection.Start
            x = left + caret.iChar * self.char_width
            y = caret.iLine * line_height - top
            painter.fillRect(QtCore.QRect(x, y, 2 if c.IsReplaceMode is False else self.char_width, line_height), qcolor(c.CaretColor) or QtGui.QColor('black'))
        painter.end()

    # Input --------------------------------------------------------------------------------------------------------------
    def focusNextPrevChild(self, next_):
        return False if self.control.AcceptsTab else super().focusNextPrevChild(next_)

    def event(self, event):
        # Every key goes to the editor's form first (WinForms ProcessCmdKey runs in the focused control's form);
        # the main window's menu shortcuts do not take keys from an original form.
        if event.type() == QtCore.QEvent.Type.ShortcutOverride:
            event.accept()
            return True
        # Tab and Backtab are editor keys (AcceptsTab), not focus moves.
        if event.type() == QtCore.QEvent.Type.KeyPress and event.key() in (QtCore.Qt.Key.Key_Tab, QtCore.Qt.Key.Key_Backtab) and self.control.AcceptsTab:
            self.keyPressEvent(event)
            return True
        return super().event(event)

    def keyPressEvent(self, event):
        keys = full_winforms_keys(event)
        set_modifier_keys(event)
        text = event.text()
        if event.key() == QtCore.Qt.Key.Key_Backtab:
            text = ''
        if event.modifiers() & (QtCore.Qt.KeyboardModifier.ControlModifier | QtCore.Qt.KeyboardModifier.MetaModifier):
            text = ''  # Ctrl+key: no character (WinForms delivers a control character the editor ignores)
        from System.Windows.Forms import KeyboardLayout
        self.caret_on = True
        self.window.renderer.input(lambda: (KeyboardLayout.SetCurrent(keys, text), self.control.RaiseKeyInput(keys, text)))
        self.window.renderer.flush()
        self.scroll_to_caret()
        self.viewport().update()

    def place_args(self, event):
        position = event.position().toPoint()
        return position.x(), position.y()

    def mousePressEvent(self, event):
        set_modifier_keys(event)
        if not self.hasFocus():
            self.setFocus()
        x, y = self.place_args(event)
        button = mouse_button(event.button())
        self.report_geometry()
        self.window.renderer.input(lambda: self.control.RaiseMouse('down', button, 1, x, y))
        self.viewport().update()

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.MouseButton.LeftButton:
            x, y = self.place_args(event)
            self.window.renderer.input(lambda: self.control.RaiseMouse('move', MouseButtons.Left, 0, x, y))
            self.viewport().update()

    def mouseReleaseEvent(self, event):
        x, y = self.place_args(event)
        button = mouse_button(event.button())
        self.window.renderer.input(lambda: (self.control.RaiseMouse('up', button, 1, x, y), self.control.RaiseMouse('click', button, 1, x, y)))
        if event.button() == QtCore.Qt.MouseButton.RightButton and self.control.ContextMenuStrip is not None:
            self.window.renderer.show_context_menu(self.control.ContextMenuStrip, event.globalPosition().toPoint(), self.control)
        self.viewport().update()

    def mouseDoubleClickEvent(self, event):
        x, y = self.place_args(event)
        self.window.renderer.input(lambda: self.control.RaiseMouse('doubleclick', MouseButtons.Left, 2, x, y))
        self.viewport().update()

    def wheelEvent(self, event):
        super().wheelEvent(event)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.window.renderer.input(self.control.RaiseEnter)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        popup = AUTOCOMPLETE.popup
        if popup is not None and popup.isVisible() and popup.menu.TextBox == self.control:
            return
        self.window.renderer.input(self.control.RaiseLeave)


class AutocompletePopup(QtWidgets.QListWidget):
    """FCTB AutocompleteMenu: the visible items under the fragment; the focussed item is the model's."""

    def __init__(self, editor, menu):
        super().__init__(editor.window)
        self.editor, self.menu = editor, menu
        self.setWindowFlags(QtCore.Qt.WindowType.ToolTip)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.itemClicked.connect(lambda item: self.click(item, False))
        self.itemDoubleClicked.connect(lambda item: self.click(item, True))

    def click(self, item, double):
        index = self.row(item)
        self.editor.window.renderer.input(lambda: self.menu.Items.UserClickItem(index, double))
        self.editor.setFocus()

    def sync(self):
        items = [str(i) for i in self.menu.Items.VisibleItems]
        if [self.item(i).text() for i in range(self.count())] != items:
            self.clear()
            self.addItems(items)
        self.setFont(editor_font(self.menu.Font))
        index = int(self.menu.Items.FocussedItemIndex)
        if 0 <= index < self.count():
            self.setCurrentRow(index)
            selected = qcolor(self.menu.Items.SelectedColor)
            if selected is not None:
                self.setStyleSheet(f'QListWidget::item:selected {{ background: {selected.name()}; color: white; }}')
        row_height = max(18, self.sizeHintForRow(0) if self.count() else 18)
        maximum, minimum = self.menu.MaximumSize, self.menu.MinimumSize
        width = max(minimum.Width, min(maximum.Width or 500, max(self.sizeHintForColumn(0) + 24, 120)))
        height = min(maximum.Height or 180, row_height * max(1, self.count()) + 4)
        self.resize(width, height)
        location = self.menu.Location
        editor = self.editor
        point = editor.viewport().mapToGlobal(QtCore.QPoint(location.X, location.Y + editor.char_height + 2))
        self.move(point)


class AutocompleteHost:
    """Shows the popup of whichever AutocompleteMenu the model opens."""

    def __init__(self):
        self.popup = None
        self.editors = {}
        self.handler = None

    def install(self):
        if self.handler is None:
            from FastColoredTextBoxNS import AutocompleteMenu
            self.handler = System.Action[AutocompleteMenu, System.String](self.changed)
            AutocompleteMenu.Changed += self.handler

    def changed(self, menu, kind):
        editor = self.editors.get(menu.TextBox)
        if editor is None:
            return
        if kind == 'Close':
            if self.popup is not None and self.popup.menu == menu:
                self.popup.hide()
            return
        if self.popup is None or self.popup.menu != menu:
            if self.popup is not None:
                self.popup.hide()
            self.popup = AutocompletePopup(editor, menu)
        self.popup.sync()
        self.popup.show()


AUTOCOMPLETE = AutocompleteHost()


class SplitFrame(QtWidgets.QFrame):
    """SplitContainer: the model lays out its panels; dragging the splitter moves it in the model."""

    def __init__(self, window, control, parent):
        super().__init__(parent)
        self.window, self.control = window, control
        self.dragging = False
        self.setMouseTracking(True)

    def splitter_hit(self, position):
        r = self.control.SplitterRectangle
        return QtCore.QRect(r.X, r.Y, r.Width, r.Height).adjusted(-1, -1, 1, 1).contains(position)

    def mousePressEvent(self, event):
        if not self.control.IsSplitterFixed and self.splitter_hit(event.position().toPoint()):
            self.dragging = True
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        from System.Windows.Forms import Orientation
        vertical = self.control.Orientation == Orientation.Vertical
        position = event.position().toPoint()
        if self.dragging:
            distance = position.x() if vertical else position.y()
            self.window.renderer.input(lambda: self.control.UserMoveSplitter(int(distance)))
            return
        hit = self.splitter_hit(position)
        self.setCursor(QtCore.Qt.CursorShape.SplitHCursor if hit and vertical else QtCore.Qt.CursorShape.SplitVCursor if hit else QtCore.Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event):
        self.dragging = False
        super().mouseReleaseEvent(event)


# Painted controls (M2): a control's own Paint drawn by Qt ----------------------------------------------------------------
_DASHES = {'Solid': QtCore.Qt.PenStyle.SolidLine, 'Dash': QtCore.Qt.PenStyle.DashLine, 'Dot': QtCore.Qt.PenStyle.DotLine,
           'DashDot': QtCore.Qt.PenStyle.DashDotLine, 'DashDotDot': QtCore.Qt.PenStyle.DashDotDotLine}


def _qpen(pen):
    qpen = QtGui.QPen(qcolor(pen.Color))
    qpen.setWidthF(max(float(pen.Width), 1.0) if float(pen.Width) > 0 else 1.0)
    qpen.setStyle(_DASHES.get(str(pen.DashStyle), QtCore.Qt.PenStyle.SolidLine))
    qpen.setCapStyle(QtCore.Qt.PenCapStyle.FlatCap)
    return qpen


def _qbrush(brush):
    color = getattr(brush, 'Color', None)
    return QtGui.QBrush(qcolor(color)) if color is not None else QtGui.QBrush()


def _rect(r):
    return QtCore.QRectF(float(r.X), float(r.Y), float(r.Width), float(r.Height))


def _points(points):
    return QtGui.QPolygonF([QtCore.QPointF(float(p.X), float(p.Y)) for p in points])


def _qfont(font):
    from original_forms import original_font
    qfont = original_font()
    qfont.setPixelSize(max(1, round(float(font.Size) * 96 / 72)))
    qfont.setBold(bool(font.Bold))
    qfont.setItalic(bool(font.Italic))
    return qfont


def _arrow_cap(painter, pen, start, end):
    """GDI+ AdjustableArrowCap at the end of a line: a triangle Width x Height pen widths with its tip on the end."""
    cap = pen.CustomEndCap
    if cap is None or type(cap).__name__ != 'AdjustableArrowCap':
        return
    width = max(float(pen.Width), 1.0)
    dx, dy = end.x() - start.x(), end.y() - start.y()
    length = (dx * dx + dy * dy) ** 0.5
    if length == 0:
        return
    ux, uy = dx / length, dy / length
    back = float(cap.Height) * width
    half = float(cap.Width) * width / 2
    base = QtCore.QPointF(end.x() - ux * back, end.y() - uy * back)
    triangle = QtGui.QPolygonF([end, QtCore.QPointF(base.x() - uy * half, base.y() + ux * half),
                                QtCore.QPointF(base.x() + uy * half, base.y() - ux * half)])
    painter.save()
    painter.setPen(QtCore.Qt.PenStyle.NoPen)
    painter.setBrush(qcolor(pen.Color))
    painter.drawPolygon(triangle)
    painter.restore()


def replay(painter, commands, size):
    """Draws the commands of a recording System.Drawing.Graphics (X/Domain/WinFormsCompat/Painting.cs)."""
    TextFormatFlags = System.Windows.Forms.TextFormatFlags
    for command in commands:
        name, a = str(command.Name), list(command.Arguments)
        if name == 'SmoothingMode':
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, str(a[0]) in ('AntiAlias', 'HighQuality'))
        elif name == 'Save':
            painter.save()
        elif name == 'Restore':
            painter.restore()
        elif name == 'SetClip':
            painter.setClipRect(_rect(a[0]))
        elif name == 'ResetClip':
            painter.setClipping(False)
        elif name == 'TranslateTransform':
            painter.translate(float(a[0]), float(a[1]))
        elif name == 'RotateTransform':
            painter.rotate(float(a[0]))
        elif name == 'ScaleTransform':
            painter.scale(float(a[0]), float(a[1]))
        elif name == 'ResetTransform':
            painter.resetTransform()
        elif name == 'Clear':
            painter.fillRect(QtCore.QRectF(0, 0, size.width(), size.height()), qcolor(a[0]))
        elif name == 'FillRectangle':
            painter.fillRect(_rect(a[1]), _qbrush(a[0]))
        elif name in ('DrawRectangle', 'DrawEllipse'):
            painter.save()
            painter.setPen(_qpen(a[0]))
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            (painter.drawRect if name == 'DrawRectangle' else painter.drawEllipse)(_rect(a[1]))
            painter.restore()
        elif name == 'FillEllipse':
            painter.save()
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.setBrush(_qbrush(a[0]))
            painter.drawEllipse(_rect(a[1]))
            painter.restore()
        elif name == 'DrawLine':
            start, end = QtCore.QPointF(float(a[1].X), float(a[1].Y)), QtCore.QPointF(float(a[2].X), float(a[2].Y))
            painter.save()
            painter.setPen(_qpen(a[0]))
            painter.drawLine(start, end)
            _arrow_cap(painter, a[0], start, end)
            painter.restore()
        elif name in ('DrawLines', 'DrawPolygon'):
            painter.save()
            painter.setPen(_qpen(a[0]))
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            (painter.drawPolyline if name == 'DrawLines' else painter.drawPolygon)(_points(a[1]))
            painter.restore()
        elif name == 'FillPolygon':
            painter.save()
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.setBrush(_qbrush(a[0]))
            painter.drawPolygon(_points(a[1]))
            painter.restore()
        elif name in ('DrawText', 'DrawString'):
            if name == 'DrawText':
                text, font, box, color, flags = str(a[0]), a[1], a[2], qcolor(a[3]), int(a[4])
            else:
                text, font, box = str(a[0]), a[1], a[3]
                color, flags = qcolor(getattr(a[2], 'Color', System.Drawing.Color.Black)), 0
            painter.save()
            painter.setFont(_qfont(font))
            painter.setPen(color)
            rect = _rect(box)
            align = QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
            if rect.width() <= 0 or rect.height() <= 0:
                rect = QtCore.QRectF(rect.x(), rect.y(), 100000, 100000)
            elif name == 'DrawText':
                align = QtCore.Qt.AlignmentFlag(0)
                align |= (QtCore.Qt.AlignmentFlag.AlignHCenter if flags & int(TextFormatFlags.HorizontalCenter) else
                          QtCore.Qt.AlignmentFlag.AlignRight if flags & int(TextFormatFlags.Right) else QtCore.Qt.AlignmentFlag.AlignLeft)
                align |= (QtCore.Qt.AlignmentFlag.AlignVCenter if flags & int(TextFormatFlags.VerticalCenter) else
                          QtCore.Qt.AlignmentFlag.AlignBottom if flags & int(TextFormatFlags.Bottom) else QtCore.Qt.AlignmentFlag.AlignTop)
            painter.drawText(rect, align, text)
            painter.restore()


class PaintedControl(QtWidgets.QFrame):
    """A control that paints itself (Paint handler, e.g. FrmSection's layup diagram): Qt asks the model to paint
    (Control.RenderPaint) and replays the recorded GDI+ calls; mouse input reaches the control as WinForms raises it."""

    def __init__(self, window, control, parent):
        super().__init__(parent)
        self.window, self.control = window, control
        self.pressed = None
        self.commands = 0

    def paintEvent(self, event):
        super().paintEvent(event)
        graphics = self.window.renderer.guard(lambda: self.control.RenderPaint())
        if graphics is None:
            return
        self.commands = graphics.Commands.Count
        painter = QtGui.QPainter(self)
        try:
            color = self.control.BackColor
            if int(color.A) > 0:
                painter.fillRect(self.rect(), qcolor(color))
            replay(painter, graphics.Commands, self.size())
        finally:
            painter.end()

    def mousePressEvent(self, event):
        position, button = event.position().toPoint(), mouse_button(event.button())
        self.pressed = button
        self.window.renderer.input(lambda: self.control.RaiseMouse('down', button, 1, position.x(), position.y()))

    def mouseReleaseEvent(self, event):
        position, button = event.position().toPoint(), mouse_button(event.button())
        clicked = self.pressed == button and self.rect().contains(position)
        self.pressed = None

        def raise_events():
            if clicked:
                self.control.RaiseClick()
                self.control.RaiseMouse('click', button, 1, position.x(), position.y())
            self.control.RaiseMouse('up', button, 1, position.x(), position.y())
        self.window.renderer.input(raise_events)

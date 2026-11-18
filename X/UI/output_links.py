"""Original FrmMain output links: FindOutputLinks, the tbOutput link drawing and tbOutput_LinkClicked.

Warning and error lines of the output panel show the geometry names (Controller.GetGeometryNameRanges)
and inverted-element reports (Controller.GetInvertedElementReferenceRanges, MessageInvertedElements) as
links; a click highlights them through Controller.HighlightGeometryNamedAt or
HighlightInvertedElementsNamedAt, unless an operation or a form is active.
"""
from PyQt6 import QtCore, QtGui, QtWidgets


def is_warning_or_error_line(text):
    """FrmMain.IsWarningOrErrorLine."""
    text = text.lstrip()
    return text.lower().startswith('warning') or text.lower().startswith('error')


class OutputLinkHighlighter(QtGui.QSyntaxHighlighter):
    """Draws the link ranges of each message line (OutputTextBox link drawing)."""

    def __init__(self, window):
        super().__init__(window.output.document())
        self.window = window
        self.link = QtGui.QTextCharFormat()
        self.link.setFontUnderline(True)
        self.link.setForeground(QtGui.QBrush(QtGui.QColor(0, 102, 204)))

    def highlightBlock(self, text):
        for start, length in self.window.output_link_ranges(text):
            self.setFormat(start, length, self.link)


class OutputLinkFilter(QtCore.QObject):
    def __init__(self, window):
        super().__init__(window.output.viewport())
        self.window = window

    def eventFilter(self, watched, event):
        kind = event.type()
        if kind == QtCore.QEvent.Type.MouseMove:
            on_link = self.window.output_link_at(event.position().toPoint()) is not None
            self.window.output.viewport().setCursor(QtCore.Qt.CursorShape.PointingHandCursor if on_link
                                                    else QtCore.Qt.CursorShape.IBeamCursor)
        elif kind == QtCore.QEvent.Type.MouseButtonRelease and event.button() == QtCore.Qt.MouseButton.LeftButton:
            found = self.window.output_link_at(event.position().toPoint())
            if found is not None:
                self.window.guard(lambda: self.window.output_link_clicked(*found))
        return False


class OutputLinksWorkbench:
    def build_output_links(self):
        self.output_error_lines = set()
        self.output.setMouseTracking(True)
        self.output.viewport().setMouseTracking(True)
        self.output_link_highlighter = OutputLinkHighlighter(self)
        self.output_link_filter = OutputLinkFilter(self)
        self.output.viewport().installEventFilter(self.output_link_filter)

    def write_output(self, text, error=False):
        """WriteDataToOutput/WriteErrorToOutput: each line is kept; error lines are messages."""
        text = str(text).replace('\r\n', '\n').replace('\r', '\n')
        if error:
            self.output_error_lines.update(text.split('\n'))
        self.output.appendPlainText(text)

    def output_link_ranges(self, text):
        """FindOutputLinks: links only on warning or error lines."""
        if not (is_warning_or_error_line(text) or text in getattr(self, 'output_error_lines', ())):
            return []
        c = self.controller
        ranges = []
        try:
            for found in (c.GetGeometryNameRanges(text), c.GetInvertedElementReferenceRanges(text)):
                if found is not None:
                    ranges += [(int(r[0]), int(r[1])) for r in found]
        except Exception:
            return []
        return ranges

    def output_link_at(self, point):
        cursor = self.output.cursorForPosition(point)
        text = cursor.block().text()
        position = cursor.positionInBlock()
        if any(start <= position < start + length for start, length in self.output_link_ranges(text)):
            return text, position
        return None

    def output_link_clicked(self, line, position):
        """tbOutput_LinkClicked: not while an operation runs or a form is open."""
        if getattr(self, 'operation_task', None) is not None or self.active_editor is not None:
            return
        c = self.controller
        if not c.HighlightGeometryNamedAt(line, position):
            c.HighlightInvertedElementsNamedAt(line, position)
        self.view.blockSignals(True)
        self.view.setCurrentText(str(c.CurrentView))
        self.view.blockSignals(False)
        self.refresh()
        self.render()

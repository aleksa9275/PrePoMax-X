"""The 3D view of the original PrePoMax (M1): vtkControl, compiled whole, in a native Qt widget.

vtkControl draws with vtkNative (VTK 9.7.1, upstream's C API). Its VtkNativeHost gets the native window of this
widget (an NSView on macOS, an X11 window on Linux) and VTK creates its OpenGL view inside it. On Windows VTK's
window takes the mouse and the keys itself; on Cocoa and X11 they reach this widget, which hands them to the view. The view half of the original FrmMain (OriginalViewHost) owns the control and takes the
controller's view calls; this widget only gives it a window, a size in device pixels and a user-interface thread.
"""
import platform
import System
from System import Action, IntPtr
from System.Drawing import Size
from PyQt6 import QtCore, QtWidgets
import vtkControl as original
from vtkControl.Native import VtkNativeInput

# The VTK key symbols the interaction style compares (vtkNativeInteractorStyle GetLegacyKeyCode) and those of the
# other keys a Win32 or Cocoa window reports
KEY_SYMBOLS = {QtCore.Qt.Key.Key_Left: 'Left', QtCore.Qt.Key.Key_Up: 'Up', QtCore.Qt.Key.Key_Right: 'Right',
               QtCore.Qt.Key.Key_Down: 'Down', QtCore.Qt.Key.Key_Escape: 'Escape', QtCore.Qt.Key.Key_Return: 'Return',
               QtCore.Qt.Key.Key_Space: 'space', QtCore.Qt.Key.Key_Delete: 'Delete', QtCore.Qt.Key.Key_Shift: 'Shift_L',
               QtCore.Qt.Key.Key_Control: 'Control_L', QtCore.Qt.Key.Key_Meta: 'Control_L', QtCore.Qt.Key.Key_Alt: 'Alt_L'}
BUTTONS = {QtCore.Qt.MouseButton.LeftButton: (VtkNativeInput.LeftButtonDown, VtkNativeInput.LeftButtonUp),
           QtCore.Qt.MouseButton.MiddleButton: (VtkNativeInput.MiddleButtonDown, VtkNativeInput.MiddleButtonUp),
           QtCore.Qt.MouseButton.RightButton: (VtkNativeInput.RightButtonDown, VtkNativeInput.RightButtonUp)}


class OriginalViewport(QtWidgets.QWidget):
    def __init__(self, parent, post, control=None):
        super().__init__(parent)
        for attribute in (QtCore.Qt.WidgetAttribute.WA_NativeWindow, QtCore.Qt.WidgetAttribute.WA_PaintOnScreen,
                          QtCore.Qt.WidgetAttribute.WA_NoSystemBackground, QtCore.Qt.WidgetAttribute.WA_OpaquePaintEvent):
            self.setAttribute(attribute)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.setMinimumSize(200, 150)
        self._wheel = 0
        self._post = Action[Action](lambda action: post(action))
        if control is None:
            # The workbench: the view half of FrmMain (OriginalViewHost) owns the control and marshals to this thread
            # through post (FrmMain.InvokeIfRequired)
            from PrePoMax import OriginalViewHost
            self.control = original.vtkControl()
            self.host = OriginalViewHost(self.control, self._post)
        else:
            # FrmMain compiled whole (main_form.py): the original FrmMain created the control and drives it
            self.control = control
            self.host = None
        self.attached = False

    # Qt draws nothing here: VTK owns the native window (no paint engine, no "paintEngine" warnings)
    def paintEngine(self):
        return None

    def pixel_size(self):
        ratio = self.devicePixelRatioF()
        return max(1, round(self.width() * ratio)), max(1, round(self.height() * ratio))

    def attach(self):
        """WinForms creates the window of the control when it is first shown: OnHandleCreated, then Load."""
        if self.attached:
            return
        self.attached = True
        if self.host is not None:
            # The workbench sizes the control in device pixels; in FrmMain the WinForms layout sizes it
            width, height = self.pixel_size()
            self.control.Size = Size(width, height)
        self.control.NativeHost.AttachNativeWindow(IntPtr(int(self.winId())))
        self.control.RaiseLoad()
        if self.host is None:
            # FrmMain loaded the control when it created it, before this window existed (WinForms creates the
            # handle first): the control sends its scene to the native view now that there is one
            self.control.EnableNativeMirror(True)
        # X11: VTK's window leaves its input to this widget; its exposure, size and the interaction style's timers
        # (the selection after a click, smooth zoom) come from its own display connection, pumped here
        if platform.system() == 'Linux':
            self._events = QtCore.QTimer(self)
            self._events.timeout.connect(self.control.NativeHost.ProcessEvents)
            self._events.start(10)

    def showEvent(self, event):
        super().showEvent(event)
        self.attach()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.host is None:
            return  # FrmMain: the widget follows the control's bounds (the WinForms layout), not the other way round
        width, height = self.pixel_size()
        self.control.Size = Size(width, height)

    def paintEvent(self, event):
        if self.attached:
            self.control.NativeHost.Refresh()

    # Input. A Win32 window delivers the mouse and the keys to VTK's interactor itself; VTK's Cocoa and X11 views
    # inside a parent leave them to the parent ("the superview handles the events"), so the widget hands them to
    # the interaction style of the native view (vtkn_view_handle_input) in display pixels, origin bottom left
    def _send(self, kind, event=None, position=None, key_code=0, key_symbol=None):
        view = self.control.NativeMirror if self.attached else None
        self.inputs = (getattr(self, 'inputs', []) + [str(kind)])[-20:]  # the last inputs, for the probes
        if view is None:
            return False
        point = position if position is not None else (event.position() if event is not None else QtCore.QPointF(0, 0))
        ratio = self.devicePixelRatioF()
        modifiers = QtWidgets.QApplication.keyboardModifiers() if event is None else event.modifiers()
        # Cocoa's interactor reports the Command key as control, as PrePoMax's Ctrl
        control = bool(modifiers & (QtCore.Qt.KeyboardModifier.ControlModifier | QtCore.Qt.KeyboardModifier.MetaModifier))
        shift = bool(modifiers & QtCore.Qt.KeyboardModifier.ShiftModifier)
        view.HandleInput(kind, round(point.x() * ratio), round((self.height() - point.y()) * ratio), control, shift,
                         int(key_code), key_symbol)
        return True

    def mousePressEvent(self, event):
        self.setFocus(QtCore.Qt.FocusReason.MouseFocusReason)
        if event.button() in BUTTONS and self._send(BUTTONS[event.button()][0], event):
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() in BUTTONS and self._send(BUTTONS[event.button()][1], event):
            event.accept()

    def mouseDoubleClickEvent(self, event):
        # The interaction style counts the clicks itself (the double click time of the platform)
        self.mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._send(VtkNativeInput.MouseMove, event):
            event.accept()

    def wheelEvent(self, event):
        # One wheel event per notch (WHEEL_DELTA 120), as Win32 and Cocoa wheels give them; trackpads add up
        self._wheel += event.angleDelta().y()
        while abs(self._wheel) >= 120:
            step = 120 if self._wheel > 0 else -120
            self._wheel -= step
            self._send(VtkNativeInput.WheelForward if step > 0 else VtkNativeInput.WheelBackward, event)
        event.accept()

    def leaveEvent(self, event):
        self._send(VtkNativeInput.Leave, None, QtCore.QPointF(0, 0))
        super().leaveEvent(event)

    def _key(self, kind, event):
        text = event.text()
        symbol = KEY_SYMBOLS.get(QtCore.Qt.Key(event.key()), text if len(text) == 1 and text.isprintable() else None)
        code = ord(text) if len(text) == 1 and ord(text) < 256 else 0
        position = self.mapFromGlobal(__import__('PyQt6.QtGui', fromlist=['QCursor']).QCursor.pos()).toPointF()
        return self._send(kind, None, position, code, symbol)

    def keyPressEvent(self, event):
        if not self._key(VtkNativeInput.KeyPress, event):
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if not self._key(VtkNativeInput.KeyRelease, event):
            super().keyReleaseEvent(event)

    def detach(self):
        """Before Qt destroys the native window: the view is released while its window still exists."""
        if not self.attached:
            return
        self.attached = False
        if getattr(self, '_events', None) is not None:
            self._events.stop()
            self._events = None
        self.control.NativeHost.DetachNativeWindow()

    def capture(self, path, magnification=1):
        """The view as drawn (vtkn_view_write_png of the native view)."""
        self.control.NativeMirror.WritePng(str(path), int(magnification))

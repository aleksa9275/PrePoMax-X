"""Experimental VTK-owned Cocoa child view, distinct from QVTK's Qt-owned view.

The parent address is a Qt NSView; VTK creates a plain child NSView inside it.
VTK's SetParentInfo path deliberately leaves pointer dispatch to its parent.
No change to the engineering model or choice of production frontend is implied.
"""
import sys

from PyQt6 import QtCore, QtWidgets
from vtkmodules.vtkRenderingCore import vtkRenderWindow
from vtkmodules.vtkRenderingUI import vtkGenericRenderWindowInteractor
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
import vtkmodules.vtkRenderingOpenGL2


class NativeCocoaView(QtWidgets.QWidget):
    clicked = QtCore.pyqtSignal(float, float)

    def __init__(self, parent):
        if sys.platform != 'darwin':
            raise RuntimeError('The experimental Cocoa child-view adapter requires macOS')
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_NativeWindow)
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.window = vtkRenderWindow()
        self.window.SetMultiSamples(0)
        self.window.SetParentInfo(str(int(self.winId())))
        self.interactor = vtkGenericRenderWindowInteractor()
        self.interactor.SetRenderWindow(self.window)
        self.interactor.SetInteractorStyle(vtkInteractorStyleTrackballCamera())
        self.pressed = None
        self.initialized = False
        self.finalized = False

    def GetRenderWindow(self):
        return self.window

    def render(self):
        if self.finalized:
            return
        scale = self.devicePixelRatioF()
        self.window.SetSize(max(1, round(self.width() * scale)), max(1, round(self.height() * scale)))
        if not self.initialized:
            self.interactor.Initialize()
            self.initialized = True
        self.window.SetPosition(0, 0)
        self.window.Render()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.initialized:
            self.render()

    def _event(self, event):
        position = event.position()
        scale = self.devicePixelRatioF()
        modifiers = event.modifiers()
        self.interactor.SetEventInformation(round(position.x() * scale),
            round((self.height() - position.y()) * scale) - 1,
            int(bool(modifiers & (QtCore.Qt.KeyboardModifier.ControlModifier | QtCore.Qt.KeyboardModifier.MetaModifier))),
            int(bool(modifiers & QtCore.Qt.KeyboardModifier.ShiftModifier)))

    def mousePressEvent(self, event):
        self._event(event)
        self.pressed = event.position()
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.interactor.LeftButtonPressEvent()
        elif event.button() == QtCore.Qt.MouseButton.MiddleButton:
            self.interactor.MiddleButtonPressEvent()
        elif event.button() == QtCore.Qt.MouseButton.RightButton:
            self.interactor.RightButtonPressEvent()

    def mouseMoveEvent(self, event):
        self._event(event)
        self.interactor.MouseMoveEvent()

    def mouseDoubleClickEvent(self, event):
        self.mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._event(event)
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.interactor.LeftButtonReleaseEvent()
            if self.pressed is not None and (event.position() - self.pressed).manhattanLength() <= 4:
                self.clicked.emit(*self.interactor.GetEventPosition())
        elif event.button() == QtCore.Qt.MouseButton.MiddleButton:
            self.interactor.MiddleButtonReleaseEvent()
        elif event.button() == QtCore.Qt.MouseButton.RightButton:
            self.interactor.RightButtonReleaseEvent()
        self.pressed = None

    def wheelEvent(self, event):
        self._event(event)
        if event.angleDelta().y() > 0:
            self.interactor.MouseWheelForwardEvent()
        elif event.angleDelta().y() < 0:
            self.interactor.MouseWheelBackwardEvent()

    def Finalize(self):
        if not self.finalized:
            self.interactor.Disable()
            self.window.Finalize()
            self.finalized = True

"""Qt/X11/Windows native VTK widget with the same click/drag boundary as Cocoa."""
from PyQt6 import QtCore
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera


class NativeQtView(QVTKRenderWindowInteractor):
    clicked = QtCore.pyqtSignal(float, float)

    def __init__(self, parent):
        super().__init__(parent)
        self.SetInteractorStyle(vtkInteractorStyleTrackballCamera())
        self.pressed = None

    def mousePressEvent(self, event):
        self.pressed = event.position()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == QtCore.Qt.MouseButton.LeftButton and self.pressed is not None:
            if (event.position() - self.pressed).manhattanLength() <= 4:
                self.clicked.emit(*self.GetRenderWindow().GetInteractor().GetEventPosition())
        self.pressed = None

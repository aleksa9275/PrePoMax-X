"""Rectangle gesture only; original Controller resolves the frustum and IDs."""
from PyQt6 import QtCore,QtWidgets

def press(view,event):
    if not getattr(view,'box_selection',False) or event.button()!=QtCore.Qt.MouseButton.LeftButton:return False
    view.box_origin=event.position().toPoint()
    if not hasattr(view,'rubber_band'):view.rubber_band=QtWidgets.QRubberBand(QtWidgets.QRubberBand.Shape.Rectangle,view)
    view.rubber_band.setGeometry(QtCore.QRect(view.box_origin,QtCore.QSize()));view.rubber_band.show();view.rubber_band.raise_();return True

def move(view,event):
    if getattr(view,'box_origin',None) is None:return False
    view.rubber_band.setGeometry(QtCore.QRect(view.box_origin,event.position().toPoint()).normalized());return True

def release(view,event):
    if getattr(view,'box_origin',None) is None:return False
    first=view.box_origin;last=event.position();scale=view.devicePixelRatioF();view.rubber_band.hide();view.box_origin=None
    view.area_selected.emit(first.x()*scale,(view.height()-first.y())*scale,last.x()*scale,(view.height()-last.y())*scale);return True


class AreaSelectionFilter(QtCore.QObject):
    selected=QtCore.pyqtSignal(float,float,float,float)
    def __init__(self,view):
        super().__init__(view);self.view=view;view.area_selected=self.selected;view.installEventFilter(self)
    def eventFilter(self,watched,event):
        types=QtCore.QEvent.Type
        if event.type()==types.MouseButtonPress:return press(self.view,event)
        if event.type()==types.MouseMove:return move(self.view,event)
        if event.type()==types.MouseButtonRelease:return release(self.view,event)
        return False

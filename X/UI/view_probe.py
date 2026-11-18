"""Probe access to the original 3D view (vtkControl on vtkNative, M1): its camera, the actors it draws, display
points and native pointer events delivered to VTK's own view, as a person's mouse would reach it."""
import platform
from pathlib import Path
from System import Array, Double, Int32
from PyQt6 import QtCore, QtGui, QtTest, QtWidgets


class ViewProbe:
    def __init__(self, app, window):
        self.app = app
        self.window = window
        self.vtk = window.vtk
        self.events = None
        if platform.system() == 'Darwin':
            import sys
            sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Desktop'))
            from viewport_probe import CocoaEvents
            self.events = CocoaEvents(window.viewport)

    @property
    def native(self):
        return self.vtk.NativeMirror

    # Camera (vtkControl.GetViewParameters / SetViewParameters, no animation)
    def camera(self):
        result = self.vtk.GetViewParameters(None, None, None, Double(0))
        values = list(result)[-4:]
        return tuple(tuple(values[i]) for i in range(3)) + (float(values[3]),)

    def look(self, position, focal_point, view_up):
        scale = self.camera()[3]
        self.vtk.SetViewParameters(False, Array[Double](list(map(float, position))), Array[Double](list(map(float, focal_point))),
                                   Array[Double](list(map(float, view_up))), Double(scale))
        self.vtk.SetZoomToFit(False)
        self.app.processEvents()

    def node_position(self, node_id):
        """The drawn position of a node in the animation frame shown (FrmMain.TryGetAnimationNodeData)."""
        found, coordinates, _ = self.window.viewport.host.TryGetAnimationNodeData(int(node_id), None, 0.0)
        return tuple(coordinates) if found else None

    def scalar_range(self):
        return tuple(self.native.GetScalarRange())

    def widget_names(self):
        return [str(n) for n in self.vtk.GetNativeMirrorWidgetNames()]

    # What the native view draws
    def actor_names(self):
        return [str(n) for n in self.native.GetActorNames()]

    def triangles(self, name):
        """The triangles of the drawn actor (vtkControl.GetVtkMaxActorData, what the 3MF export reads)."""
        for data in self.vtk.GetVtkMaxActorData():
            if str(data.Name) == name and data.Geometry is not None and data.Geometry.Cells.CellNodeIds is not None:
                return len(data.Geometry.Cells.CellNodeIds)
        return 0

    def size(self):
        width, height = self.native.GetSize(0, 0)
        return int(width), int(height)

    def render_info(self):
        return str(self.native.GetRenderInfo()).split('\n')[0]

    # Display points: VTK display pixels (origin bottom left) to widget points (origin top left)
    def to_widget(self, world):
        display = self.native.WorldToDisplay(Array[Double](list(map(float, world))))
        ratio = self.window.viewport.devicePixelRatioF()
        return display[0] / ratio, self.window.viewport.height() - display[1] / ratio

    def _send(self, kind, x, y):
        if self.events is None:
            # X11: VTK's window leaves the pointer to the widget (vtkNativeX11.cpp), so Qt events take the user's path
            viewport = self.window.viewport
            point = QtCore.QPointF(x, y)
            left = QtCore.Qt.MouseButton.LeftButton
            kind, button, buttons = {1: (QtCore.QEvent.Type.MouseButtonPress, left, left),
                                     2: (QtCore.QEvent.Type.MouseButtonRelease, left, QtCore.Qt.MouseButton.NoButton),
                                     6: (QtCore.QEvent.Type.MouseMove, QtCore.Qt.MouseButton.NoButton, left)}[kind]
            QtWidgets.QApplication.sendEvent(viewport, QtGui.QMouseEvent(kind, point, viewport.mapToGlobal(point), button,
                                             buttons, QtCore.Qt.KeyboardModifier.NoModifier))
            return
        self.events.height = self.window.viewport.height()
        self.events.send(kind, x, y)

    def hit_test(self, x, y):
        """The Cocoa view a click at the widget point reaches (diagnostics)."""
        if self.events is None:
            return None
        import ctypes as C
        from viewport_probe import Point
        e = self.events
        point = e.call(e.view, 'convertPoint:toView:', Point, (Point, C.c_void_p), (Point(x, y), None))
        content = e.call(e.window, 'contentView', C.c_void_p)
        hit = e.call(content, 'hitTest:', C.c_void_p, (Point,), (point,))
        if not hit:
            return None
        name = e.call(e.call(hit, 'className', C.c_void_p), 'UTF8String', C.c_void_p)
        return C.string_at(name).decode() + ('' if hit != e.view else ' (viewport)')

    def click(self, x, y):
        QtTest.QTest.qWait(self.app.doubleClickInterval() + 50)
        self._send(1, x, y)
        self._send(2, x, y)
        self.app.processEvents()
        self._raise_callback_errors()

    def drag(self, x, y, dx, dy, steps=7, button=QtCore.Qt.MouseButton.LeftButton):
        """A drag as the widget receives it (the middle button turns the view in PrePoMax)."""
        QtTest.QTest.qWait(self.app.doubleClickInterval() + 50)
        if button == QtCore.Qt.MouseButton.LeftButton:
            self._send(1, x, y)
            for i in range(1, steps + 1):
                self._send(6, x + dx * i / steps, y + dy * i / steps)
            self._send(2, x + dx, y + dy)
        else:
            viewport = self.window.viewport
            def event(kind, px, py, buttons):
                point = QtCore.QPointF(px, py)
                QtWidgets.QApplication.sendEvent(viewport, QtGui.QMouseEvent(kind, point, viewport.mapToGlobal(point), button,
                    buttons, QtCore.Qt.KeyboardModifier.NoModifier))
            event(QtCore.QEvent.Type.MouseButtonPress, x, y, button)
            for i in range(1, steps + 1):
                event(QtCore.QEvent.Type.MouseMove, x + dx * i / steps, y + dy * i / steps, button)
                self.app.processEvents()
            event(QtCore.QEvent.Type.MouseButtonRelease, x + dx, y + dy, QtCore.Qt.MouseButton.NoButton)
        self.app.processEvents()
        self._raise_callback_errors()

    def _raise_callback_errors(self):
        """An exception in a vtkControl event handler of the workbench (kept by its view_callback)."""
        errors = getattr(self.window, 'view_callback_errors', [])
        if errors:
            self.window.view_callback_errors = []
            raise errors[0]

    def count_pixels(self, path, predicate, step=2):
        image = self.png(path)
        count = 0
        for y in range(0, image.height(), step):
            for x in range(0, image.width(), step):
                if predicate(image.pixelColor(x, y)):
                    count += 1
        return count

    def highlighted_pixels(self, path):
        """Pixels of the primary highlight colour (red) in the drawn view."""
        return self.count_pixels(path, lambda c: c.red() > 200 and c.green() < 70 and c.blue() < 70)

    def dark_pixels(self, path):
        """Pixels of the edges (black lines) in the drawn view."""
        return self.count_pixels(path, lambda c: c.red() < 90 and c.green() < 90 and c.blue() < 90)

    def colored_pixels(self, path):
        """Pixels of drawn geometry: the background is a grey gradient, parts and symbols have colour or are dark."""
        return self.count_pixels(path, lambda c: max(c.red(), c.green(), c.blue()) - min(c.red(), c.green(), c.blue()) > 20
                                 or max(c.red(), c.green(), c.blue()) < 90)

    @staticmethod
    def darkened_pixels(before, after, step=1):
        """Pixels two saved pictures of the same view differ by lines drawn darker in the second (edges added)."""
        a, b = QtGui.QImage(str(before)), QtGui.QImage(str(after))
        count = 0
        for y in range(0, min(a.height(), b.height()), step):
            for x in range(0, min(a.width(), b.width()), step):
                p, q = a.pixelColor(x, y), b.pixelColor(x, y)
                if p.red() - q.red() > 20 and p.green() - q.green() > 20 and p.blue() - q.blue() > 20:
                    count += 1
        return count

    def png(self, path, transparent=False):
        """The view as vtkControl renders it to a picture (RenderToPNG)."""
        self.vtk.RenderToPNG(str(path), bool(transparent), 1)
        return QtGui.QImage(str(path))

"""Bounded native event, display and transport measurement probe.

Synthetic NSEvents are sent through this application's NSWindow, including its
native hit testing. This is not a human mouse/keyboard or cross-platform test.
"""
import ctypes as C
import hashlib
import json
from pathlib import Path
import platform
import resource
import statistics
import sys
import time

from PyQt6 import QtCore, QtTest


class Point(C.Structure):
    _fields_ = [('x', C.c_double), ('y', C.c_double)]


class CocoaEvents:
    def __init__(self, widget):
        self.lib = C.CDLL('/usr/lib/libobjc.A.dylib')
        self.lib.sel_registerName.argtypes = [C.c_char_p]
        self.lib.sel_registerName.restype = C.c_void_p
        self.lib.objc_getClass.argtypes = [C.c_char_p]
        self.lib.objc_getClass.restype = C.c_void_p
        self.view = int(widget.winId())
        self.window = self.call(self.view, 'window', C.c_void_p)
        self.number = self.call(self.window, 'windowNumber', C.c_long)
        self.event_class = self.lib.objc_getClass(b'NSEvent')
        self.event_number = 0

    def call(self, obj, selector, returns, arguments=(), values=()):
        function = C.CFUNCTYPE(returns, C.c_void_p, C.c_void_p, *arguments)(('objc_msgSend', self.lib))
        return function(obj, self.lib.sel_registerName(selector.encode()), *values)

    def send(self, kind, x, y):
        # Convert widget logical coordinates (top-left) into NSWindow points.
        flipped = self.call(self.view, 'isFlipped', C.c_bool)
        point = Point(x, y if flipped else self.height - y)
        location = self.call(self.view, 'convertPoint:toView:', Point,
                             (Point, C.c_void_p), (point, None))
        self.event_number += 1
        event = self.call(self.event_class,
            'mouseEventWithType:location:modifierFlags:timestamp:windowNumber:context:eventNumber:clickCount:pressure:',
            C.c_void_p,
            (C.c_ulong, Point, C.c_ulong, C.c_double, C.c_long, C.c_void_p, C.c_long, C.c_long, C.c_float),
            (kind, location, 0, time.monotonic(), self.number, None, self.event_number, 1, 1.0 if kind != 2 else 0.0))
        if not event:
            raise RuntimeError('NSEvent creation failed')
        self.call(self.window, 'sendEvent:', None, (C.c_void_p,), (event,))


def capture(widget):
    """Capture this widget's actual screen rectangle, including native subviews."""
    origin = widget.mapToGlobal(QtCore.QPoint(0, 0))
    return widget.screen().grabWindow(0, origin.x(), origin.y(), widget.width(), widget.height()).toImage()


def run(app, window, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    result = {'success': False, 'transport': window.transport, 'checks': [],
        'host': {'os': platform.system(), 'machine': platform.machine(), 'version': platform.mac_ver()[0]},
        'scope': 'Synthetic Cocoa NSWindow pointer dispatch, actual screen pixels and local transport measurements; not human input or release acceptance'}

    def check(name, passed):
        result['checks'].append({'name': name, 'passed': bool(passed)})
        if not passed:
            raise ValueError(name)

    try:
        if sys.platform != 'darwin':
            raise ValueError('This native event probe requires macOS')
        window.raise_()
        window.activateWindow()
        app.processEvents()
        events = CocoaEvents(window.vtk)
        events.height = window.vtk.height()
        window.renderer.SetWorldPoint(0.5, 0.5, 1, 1)
        window.renderer.WorldToDisplay()
        x, y, _ = window.renderer.GetDisplayPoint()
        scale = window.vtk.devicePixelRatioF() if window.transport == 'native-cocoa' else 1
        qx, qy = x / scale, window.vtk.height() - y / scale
        window.selection = None
        events.send(1, qx, qy)
        events.send(2, qx, qy)
        app.processEvents()
        check('NSWindow click resolves original element ID', window.selection and
              window.selection['elementId'] == window.scene['elements'][0]['id'])
        selected = window.selection
        check('NSWindow click resolves original node ID', selected['nearestVertexNodeId'] in
              {node['id'] for node in window.scene['nodes']})
        if window.fields.count() > 1:
            window.fields.setCurrentIndex(1)
            QtTest.QTest.qWait(app.doubleClickInterval() + 50)
            events.send(1, qx, qy)
            events.send(2, qx, qy)
            app.processEvents()
            node_id = window.selection['nearestVertexNodeId']
            field = window.scene['fields'][0]
            expected = next(iter(field['components'].values()))[window.scene['nodeIdsInValueOrder'].index(node_id)]
            result['fieldClick'] = {'selection': window.selection, 'expected': expected,
                                    'selectedArray': window.fields.currentData(),
                                    'viewportOrigin': [window.vtk.x(),window.vtk.y()]}
            check('NSWindow click preserves original field value', window.selection.get('nodalValue') == expected)
        camera = window.renderer.GetActiveCamera()
        before = camera.GetPosition()
        selection_before_drag = window.selection
        QtTest.QTest.qWait(app.doubleClickInterval() + 50)
        events.send(1, qx, qy)
        for offset in range(5, 46, 5):
            events.send(6, qx + offset, qy + offset / 2)
        events.send(2, qx + 45, qy + 22.5)
        app.processEvents()
        check('NSWindow drag rotates VTK camera', camera.GetPosition() != before)
        check('NSWindow drag does not select', window.vtk.pressed is None and window.selection == selection_before_drag)
        window.resize(1060, 680)
        app.processEvents()
        window.vtk.render()
        app.processEvents()
        expected_size = (round(window.vtk.width() * scale), round(window.vtk.height() * scale))
        actual_size = window.vtk.GetRenderWindow().GetSize()
        check('render size matches widget and device scale', tuple(actual_size) == expected_size)
        frame = capture(window.vtk)
        check('actual screen capture available', not frame.isNull())
        colors = {frame.pixelColor(x, y).rgb() for x in range(0, frame.width(), 12)
                  for y in range(0, frame.height(), 12)}
        check('actual screen contains mesh/contour pixels', len(colors) > 10 if window.fields.count() > 1 else len(colors) > 3)
        check('actual screen capture saved', capture(window).save(str(output / 'window.png')))
        result.update(selection=selected, devicePixelRatio=window.vtk.devicePixelRatioF(),
                      renderSize=actual_size, widgetSize=[window.vtk.width(), window.vtk.height()],
                      sourceSha256=window.scene['SourceSha256'])

        # Transport comparison uses one physical framebuffer size on both routes.
        # FrameBridge intentionally remains at its existing logical resolution;
        # use its rendered size as the common baseline and account for Retina.
        target = (800, 600)
        if window.transport == 'native-cocoa':
            window.vtk.setFixedSize(round(target[0] / scale), round(target[1] / scale))
        else:
            window.vtk.setFixedSize(*target)
        app.processEvents()
        window.vtk.render()
        samples = []
        for _ in range(35):
            camera.Azimuth(1)
            start = time.perf_counter()
            window.vtk.render()
            samples.append((time.perf_counter() - start) * 1000)
        result['smallMesh'] = {'nodes': window.grid.GetNumberOfPoints(), 'cells': window.grid.GetNumberOfCells(),
            'framebuffer': window.vtk.GetRenderWindow().GetSize(), 'medianRenderMs': statistics.median(samples),
            'p95RenderMs': sorted(samples)[int(len(samples)*.95)], 'frames': len(samples)}

        # Generate structured C3D8 input only. Original C# reader still decodes it.
        divisions = 30
        mesh = output / 'structured-27000.inp'
        def node(i, j, k):
            return 10 + 3 * (i + (divisions+1) * (j + (divisions+1)*k))
        with mesh.open('w') as stream:
            stream.write('*NODE\n')
            for k in range(divisions+1):
                for j in range(divisions+1):
                    for i in range(divisions+1):
                        stream.write(f'{node(i,j,k)},{i/divisions},{j/divisions},{k/divisions}\n')
            stream.write('*ELEMENT,TYPE=C3D8,ELSET=DENSE\n')
            element = 7001
            for k in range(divisions):
                for j in range(divisions):
                    for i in range(divisions):
                        ids = [node(i,j,k),node(i+1,j,k),node(i+1,j+1,k),node(i,j+1,k),
                               node(i,j,k+1),node(i+1,j,k+1),node(i+1,j+1,k+1),node(i,j+1,k+1)]
                        stream.write(str(element)+','+','.join(map(str,ids))+'\n')
                        element += 5
        start = time.perf_counter()
        window.load(mesh)
        load_seconds = time.perf_counter() - start
        check('larger mesh decoded by original reader', window.grid.GetNumberOfCells() == 27000 and
              window.grid.GetNumberOfPoints() == 29791)
        samples = []
        for _ in range(35):
            camera.Azimuth(1)
            start = time.perf_counter()
            window.vtk.render()
            samples.append((time.perf_counter() - start) * 1000)
        result['largerMesh'] = {'nodes': 29791, 'cells': 27000, 'loadSeconds': load_seconds,
            'framebuffer': window.vtk.GetRenderWindow().GetSize(), 'medianRenderMs': statistics.median(samples),
            'p95RenderMs': sorted(samples)[int(len(samples)*.95)], 'frames': len(samples),
            'fixtureSha256': hashlib.sha256(mesh.read_bytes()).hexdigest(),
            'maxResidentBytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        result['measurementScope'] = '35 synchronous render submissions at equal 800x600 framebuffer; not display FPS, CAD/solver throughput or general benchmark; peak RSS includes interpreter and readers are separate processes'
        # Repeated native view creation/destruction while Qt remains alive.
        if window.transport == 'native-cocoa':
            from native_cocoa import NativeCocoaView
            from vtkmodules.vtkRenderingCore import vtkRenderer
            for _ in range(5):
                child = NativeCocoaView(None)
                child.resize(240, 160)
                child.GetRenderWindow().AddRenderer(vtkRenderer())
                child.show()
                child.render()
                child.Finalize()
                child.Finalize()
                child.close()
                child.deleteLater()
                app.processEvents()
            check('five native create/render/finalize cycles', True)
        window.close()
        app.processEvents()
        check('window closes cleanly', not window.isVisible())
        result['success'] = True
    except Exception as error:
        result['error'] = str(error)
        window.close()
    (output / 'probe.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)
    app.exit(0 if result['success'] else 1)

# B002 — Qt/VTK candidate Cocoa embedding defects

3 November task 0043 update: an alternative `SetParentInfo` child-NSView route
with Qt → generic-VTK input forwarding passes visible packaged rendering,
original IDs/scalars, synthetic native NSWindow clicks/drag, 2x Retina resize
and repeated lifecycle checks. [Actual evidence and measured tradeoff](../reports/native-viewport-boundary.md).
The original QVTK adapters below remain rejected; this is an opt-in alternative,
not an original-adapter fix, general Qt/VTK compatibility statement, production
frontend choice or full input/performance/four-target acceptance.

2 November 2026, unshipped task 0037 candidate, macOS 26.7.1 ARM64,
VTK 9.5.2 / PyQt6 6.10.0 / Qt runtime 6.10.2 / CPython 3.12.14.
These are observations of this combination, not a general Qt/VTK incompatibility.

QVTKRenderWindowInteractor with default QWidget entered continuous Cocoa
expose/paint/render work; the 1.2-second test timer did not execute. A native
stack sample located `NSOpenGLViewBackingLayer display` → Qt synchronous expose
→ QWidget paint → vtkCocoaRenderWindow::Render. Processes were stopped.
Changing initialization order did not resolve the observation.

The supported QOpenGLWidget base allowed the timer, picker and field checks,
but window capture was black. Initial API-only self-test reported success:
that result is rejected by visual inspection. This is why the final check also
examines colors in the frame actually displayed by Qt.

Bounded workaround: offscreen native VTK GPU rendering copied into a Qt image.
The final displayed frame, IDs/coordinates/nodal value and resize pass, including
the packaged app with external dotnet/Python absent from PATH. This workaround
does not close direct embedding or frame-copy performance. Keep a genuine native
widget/C# binding comparison open before selecting the production frontend.

# Native desktop candidate — task 0037

2 November 2026. **Verified:** a local ARM64 `.app` opens a mesh or completed
C3D8 static FRD through original C# readers, displays native VTK contours and
resolves original FEM IDs/values. This is the first bounded desktop/package proof,
not completion of milestone B or a production frontend selection.

`X/Desktop/MeshScene` exposes the existing original INP mesh reader; the separate
existing Results Inspect host exposes original FRD fields. Python receives only
renderer data. Separate processes avoid mixing partial assembly closures.
Node-value lookup uses the original FRD value-order list, not sorted IDs. Native
VTK owns grid/mapping/picking/scalars/camera; Qt owns the window and controls.
No engineering algorithm, PMX format or application Controller is reimplemented.

The direct Qt/VTK adapter failed twice on this host: default QWidget stalled in
Cocoa expose/paint work; QOpenGLWidget returned valid API/picker results but a
black visible frame. [B002](../bugs/B002-qt-vtk-cocoa-host.md) records both failures
and rejects the initial API-only “success.” The current candidate renders via
native vtkCocoaRenderWindow offscreen and copies its image into Qt. The final
check also inspects displayed-frame colors; screenshots were visually reviewed.
This is a useful transport proof with an unmeasured per-frame copy cost.

The native-generated FRD passes **10 checks** in the packaged app: native window,
geometry, scalar display, element ID, nearest-vertex ID, coordinates/nodal value,
resize, visible frame and capture. The nonsequential INP fixture passes **8
checks**, selecting element **7001**, node **4**, coordinates **(0,0,1)**. Both
run with `PATH=/usr/bin:/bin` and an invalid external DOTNET_ROOT, exercising
bundled Python/Qt/VTK and self-contained C# hosts. These are programmatic picks,
not a claim of human mouse/DPI/graphics-driver acceptance on all targets.

The [package manifest](native-desktop-preview/package.json) records every regular
file hash, source identity, build commands and .NET 10.0.14 readers. Runtime:
CPython 3.12.14 ARM64, VTK 9.5.2, PyQt6 6.10.0, Qt runtime 6.10.2 (compile version
in self-test is 6.10.0), NumPy 2.3.5; wheel URLs/hashes and packaging requirements
are pinned in X/Desktop. PyInstaller 6.16.0 builds an approximately **659 MiB**
app, deliberately collecting broad VTK modules for this first proof. macOS
`codesign --verify --deep --strict` passes its ad-hoc signature. It is not
Developer-ID signed/notarized, installed/tested on a clean machine or public.

Local artifact:
`X/Desktop/artifacts/package-macos-arm64-final/dist/PrePoMax-X-Viewport.app`.
[Native result window](native-desktop-preview/packaged-native-frd.png),
[ID fixture window](native-desktop-preview/packaged-nonseq.png), associated JSON
and the rejected black frame are retained. Binary bundles stay outside Git.

**Recommendation/inference:** keep the original C# engineering/native-VTK split.
This candidate proves that a bundled native desktop can consume it now. Do not
select the frame-copy bridge as the final high-performance widget on this
evidence. A current C# native binding/host has not been built or compared; original
Windows ActiViz/VTK dependencies do not supply that Mac proof. Finish one bounded
native-widget/C# binding attempt before expanding production dialogs; avoid
another framework survey. The candidate can continue to exercise the vertical
workflow while that boundary is resolved.

**Next:** integrate a small model tree/job/results workflow, repeat the common
solid and shell corpus with native Linux workers, then produce the scoped alpha
package with save/reopen. Real input, DPI, lifecycle/large-model performance,
other element types, CAD/meshing, full Controller/results and clean-machine
installation/signing remain. Both correctness failures/tetra gate and every
four-target/release requirement stay explicit.

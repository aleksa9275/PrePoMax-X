# Native VTK rendering and FEM-ID smoke test

Task 0006, 2026-10-14 (Europe/Belgrade), `research/native-feasibility`.
**Verified observation:** an isolated Python VTK 9.5.2 runtime rendered and
selected an independently specified mesh natively on this Mac ARM64. Fourteen
checks pass. Original C#/ActiViz/vtkControl code and dependencies are unchanged.

## Runtime and retained evidence

The [PyPI release](https://pypi.org/project/vtk/9.5.2/) supplies the CPython 3.12
macOS 11+ ARM64 wheel used here. It is a pinned experimental candidate, not a
production upgrade from the original Kitware.VTK 5.8.0.607 dependency.
Wheel URL/archive hash, Python 3.12.14, NumPy 2.3.5, native-module hash,
renderer capabilities, fixture observations and script hash are retained in
[execution JSON](vtk-native-smoke/macos-arm64.json) and
[provenance](vtk-native-smoke/provenance.json).

The downloaded VTK module is a **Mach-O arm64** bundle (`file` check).
`vtkCocoaRenderWindow` reports Apple M5 Pro hardware acceleration and OpenGL
4.1 Metal. This is a native GPU rendering observation, not an emulated Windows
run. Installation used an isolated `/tmp/prepomaxx-vtk-runtime` target and
`--no-deps`; application packages and the bundled Python installation were not
modified. The existing workspace runtime supplies NumPy/Pillow. The initial
sandbox download failed DNS; an approved external download succeeded. Rendering
was run with approved macOS graphics access. First VTK import was slow but
completed; no failure or workaround was needed.

Setup/run commands are in the [probe README](../../X/Feasibility/Rendering/README.md).
No new GitLab job, native-library substitution or GUI framework was added.

## Contracts tested

Synthetic geometry is two adjoining linear quads in the XY plane, six nodes,
with FEM node IDs `[61,17,105,200,4,99]` and element IDs `[7001,9007]`.
It uses vtkUnsignedLongArray global IDs, matching the kind of arrays observed
in `vtkControl/vtkMax/Actor/vtkMaxActor.cs`. Source inspection of
`vtkControl/vtkControl.cs` identifies cell/point pickers, selected-frustum
extraction and global-ID readback. This Python driver exercises candidate
contracts; it does not execute or translate original vtkControl algorithms.

Fourteen assertions pass:

- Pinned VTK/native ARM64 host and nonsequential global-ID preservation.
- Selection by global element ID 9007 returns that element and its four node IDs.
- Independently specified displacement/scale produces the expected bounds and
  preserves node/element IDs.
- Clipping to x >= 0 produces the expected bounded geometry.
- Projected renderer cell picks return exact FEM IDs 7001 and 9007; a point pick
  returns node 61. A rectangular selected frustum returns nodes 61 and 200.
- Rendering produces mesh pixels; deformation changes the image; actor removal
  leaves only the background.

The three generated 640x480 images were visually inspected: original adjoining
quads, correctly shifted deformation, and background after actor removal.
[Original](vtk-native-smoke/synthetic-original.png),
[deformed](vtk-native-smoke/synthetic-deformed.png),
[released](vtk-native-smoke/synthetic-released.png).

**Verified mapping issue:** vtkClipDataSet returns no point or cell global-ID
arrays for this fixture. The bounds check passes, but selection provenance is
not preserved. Existing vtkControl has explicit ID-handling paths around
extraction/section geometry; a future port must test those paths individually.
Never infer that a successful render means FEM IDs survived every filter.

## Completion boundary and follow-up

Task 0006's initial synthetic binding/rendering/picking smoke experiment is
complete. It supports continuing the Python VTK candidate investigation, but
does not decide between a C# frontend and PyQt/Python VTK. The C# binding route
has not been experimentally compared here. Roadmap 2.1 remains open: genuine
pointer interaction, DPI/keyboard behavior, higher-order/volume/deformed-result
fixtures, clipping/highlight mappings, repeated lifecycle stress and Windows/
Linux/Intel-Mac differential validation are not covered by this smoke test.
Mac offscreen picks do not establish UI event behavior or old/new VTK parity.

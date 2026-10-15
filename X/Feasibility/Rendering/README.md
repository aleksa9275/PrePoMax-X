# Native VTK candidate smoke test

Task 0006 is an isolated Python VTK 9.5.2 experiment, not the original
vtkControl or a frontend choice. Production ActiViz/VTK files stay unchanged.
Use Python 3.12 ARM64 with NumPy and Pillow available. Install VTK only into a
disposable module directory; the measured wheel is
`vtk-9.5.2-cp312-cp312-macosx_11_0_arm64.whl`, SHA-256
`cce212b911d13fb0ca36d339f658c9db1ff27a5a730cdddd5d0c6b2ec24c15b1`.

Example setup/run on this host (Python path is host-specific):

```sh
/Users/aleksa/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m pip install --disable-pip-version-check --no-cache-dir --no-deps --only-binary=:all: --target /tmp/prepomaxx-vtk-runtime --report /tmp/prepomaxx-vtk-install.json vtk==9.5.2
/Users/aleksa/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 X/Feasibility/Rendering/vtk-smoke.py --module-dir /tmp/prepomaxx-vtk-runtime --install-report /tmp/prepomaxx-vtk-install.json --output-dir .project/reports/vtk-native-smoke
```

This needs network permission for setup and macOS graphics-service access for
the Cocoa offscreen run. It uses the existing workspace Python's NumPy/Pillow;
`--no-deps` deliberately avoids a production/runtime dependency install. A fresh
environment must provide those libraries too; see retained version evidence.
The temporary module directory can disappear; reinstall to rerun.

The synthetic two-quad mesh has nonsequential FEM IDs. Fourteen checks cover
ID selection/extraction, deformation, clipping bounds, native rendering,
programmatic cell/point/rectangle picks, image changes and actor removal.
Clipping **drops global-ID arrays** in this experiment; explicit provenance is
required before using cut geometry as a FEM selection source.

This is not genuine pointer/DPI interaction, a GUI framework selection,
execution of upstream vtkControl, Windows visual parity, higher-order/volume
rendering, a memory-leak test or roadmap 2.1 completion. See the
[report](../../../.project/reports/vtk-native-smoke.md).

Task 0012 adds `vtk-provenance.py` using the same pinned runtime. It tests normal
cell-data parent IDs through quadratic surface subdivision/clipping, treats new
cut vertices separately from original FEM nodes, mixed linear/quadratic/volume
geometry and 20 render/pick/finalize cycles. Coordinate node lookup is justified
only for its unique undeformed fixture, not a production topology solution.
Invoke it with `--module-dir /tmp/prepomaxx-vtk-runtime --output-dir /path/to/report`.
Actual pointer/DPI interaction and leak/platform/frontend proofs remain open.

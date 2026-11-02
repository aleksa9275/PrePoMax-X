# Native viewport candidate

The Mac package script is now a compatibility wrapper around the shared
[target build entry](../Build/README.md). All four RIDs are explicit there;
desktop render expectations come from the same target catalog included in the
app. Windows/Linux managed cross-builds do not establish native desktop support.

Qt/Python owns only this experimental window and VTK transport. Original C#
readers decode INP and FRD in separate processes, retaining their actual assembly
ownership. There is no second engineering parser/model or selected persistence
format. The results reader supports the existing bounded C3D8 static snapshot;
other analysis/mesh/UI functionality is not established by this preview.

    dotnet build X/Desktop/MeshScene/MeshScene.csproj -c Release --source X/Analysis/artifacts/offline-feed
    dotnet build X/Results/Inspect/Inspect.csproj -c Release --source X/Analysis/artifacts/offline-feed
    python3 -m venv /private/tmp/prepomaxx-desktop-runtime
    /private/tmp/prepomaxx-desktop-runtime/bin/python -m pip install --require-hashes -r X/Desktop/requirements-packaging-macos-arm64.txt
    /private/tmp/prepomaxx-desktop-runtime/bin/python X/Desktop/viewport.py X/Desktop/nonsequential-cube.inp

Use Open for INP/FRD, Fit, the scalar component selector, click for element/nearest
vertex IDs and nodal value, or drag to rotate using VTK's camera. Values remain
undeformed and in stored units. These controls are deliberately a bounded host
proof, not full vtkControl/Controller parity or an editing application.

The default QWidget QVTK adapter stalled on this Mac; QOpenGLWidget produced a
black displayed frame despite valid picker/API results. The current bridge
uses native VTK offscreen GPU rendering and copies a frame to Qt. It displays
real VTK geometry/contours, but its copy cost is not a final viewport performance
solution. Production frontend/binding selection remains explicit.

    /private/tmp/prepomaxx-desktop-runtime/bin/python X/Desktop/package-mac.py --output X/Desktop/artifacts/my-package

This builds an ad-hoc-signed local ARM64 `.app` with Python/Qt/VTK and separate
self-contained .NET 10.0.14 reader hosts. Preview-specific NuGet locks stay in
output, preserving default locks. The app can launch without an external SDK or
Python installation on PATH. It is not Developer-ID-signed/notarized or a tested
clean-machine installer. Final dependency/license/source packaging remains.
No binary or installer is published by this recipe.

`--self-test <report.json> --screenshot <window.png>` checks the bounded cube,
native rendering, actual frame colors, resize, exact IDs/value ordering, then
closes. It uses programmatic picks; genuine pointer, DPI, scale and other target
tests remain. [Evidence and candidate recommendation](../../.project/reports/native-desktop-preview.md).

Local workflow preview: **Solve example** executes the bundled cube through the
original C# deck/job service and opens its FRD. **Run static…** accepts a mesh plus
the existing bounded analysis JSON; **Cancel** uses cooperative stdin cancellation,
with retained output/error/outcome files and fresh job directories. **Job files**
opens the actual workspace. This is a static-solid preview, not full PMX editing.
The Mac --format dmg build needs an explicit --solver-build; the relocated runtime
closure and three self-contained hosts travel with it.
[Installation](INSTALL-macos.md) and [complete uninstall/reset](UNINSTALL-macos.md)
are included in the DMG. Apple container provides Linux workloads, not Mac GUI
acceptance; local native mounted/copy tests are kept distinct from a clean Mac.

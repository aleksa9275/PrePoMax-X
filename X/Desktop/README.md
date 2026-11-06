# Native viewport candidate

Task 0089 adds **Solid formulations…** and connects imported mixed solid meshes
to original configuration, native static solving and results: C3D4/C3D10/C3D10T,
C3D6/C3D15 and C3D8/C3D8R/C3D8I/C3D20/C3D20R. C3D5/C3D13 use an explicit
original collapsed-wedge/hexahedron choice in Configure → Model / units. Original
VTK permutations and restored pyramid display retain original mesh identities.
**Solve example…** offers the cube, all-formulation mixed solids and both pyramid
conversion routes. [Current behavior and evidence](../../.project/reports/solid-formulation-workflow.md).

**Mesh CAD…** offers **Linear C3D4** (default) and **Quadratic C3D10**.
Both connect to Configure… / Run analysis and original FRD results. C3D10 retains
all ten nodes, six-node CAD surfaces and midside regions; static solver decks
use the original PrePoMax node formatter and CalculiX's own element formulation.
**Export mesh…** preserves lossless mesh-only INP bytes with original-reader
readback. It omits analysis/project state.

The separate original PrePoMax quadratic measurement/integration discrepancy
remains unresolved and its measurement command stays gated. That is independent
of the verified native quadratic static solves. General curved quality, other
formulations/analysis families and full PMX graphs remain required parity work.
[Current calculations and checks](../../.project/reports/quadratic-native-static.md).
The final target is identical PrePoMax 3.0.0 functionality, including all mesh
types and calculations, except specifically unavailable solvers (D060).

With `--cad-native RUNTIME`, **CAD tools…** beside Open provides selected-part
translation, axis-angle rotation, mirror, explicit-center scaling, translated/
rotated copies, plane splitting, ShapeFix repair option 1 and selected/all-part
STEP export. Values use model units; rotation uses degrees.
Positive scale factors are bounded to 0.000001–1000; an identity-only scale is
refused. Copies retain all original parts and append 1–16 numbered outputs within
32 total parts. Copy k applies k translations or rotation angles. Each copy
requires one supported solid; overlapping copies are not joined. Geometry edits run in the
background; Cancel and closing stop the worker,
retaining the previous document on failure. Successful edits retain an owned
undo checkpoint and clear dependent mesh/analysis. Undo/redo restores exact CAD
bytes and requires remeshing; it does not restore mesh/analysis or replay PMX
history. The preview limits checkpoints to 32 and 256 MiB of authoritative inputs.
STEP export checks native solid measurements and unambiguous origins before
publishing a new filename, preserving the active mesh/analysis. All-part export
uses unchanged assembly gathering. Opened PMX geometry may be exported but cannot
be mutated through these tools. Submitted CAD jobs retain exact edit recipes and
inputs. STEP geometry exchange does not preserve arbitrary assembly metadata;
new native-session PMX save remains open.
[Checks and current candidate](../../.project/reports/cad-mirror-scale-copies.md).

Task 0044 adds a model tree and **Configure… / Run analysis** for the existing
static-solid definition. Units, isotropic elastic materials, solid sections,
displacement supports, forces per node, static increments and history requests
are edited in Qt controls, using named sets from the original INP reader.
The separate C# `validate-static` command constructs the original model objects
and calls the original deck writer without selecting/running a solver.
No engineering equations, mesh parser or PMX persistence are reimplemented here.
Each submitted job owns an immutable `inputs` snapshot and a new `solve` folder.
Project saving and creation of additional/picked sets remain pending.

Task 0043 adds an **opt-in Mac native child-view transport**, with the same
original C# readers/job services and unchanged VTK/Qt pins:

    /private/tmp/prepomaxx-desktop-runtime/bin/python X/Desktop/viewport.py X/Desktop/nonsequential-cube.inp --viewport native-cocoa

For a packaged app, pass the same option to
`PrePoMax-X-Viewport.app/Contents/MacOS/PrePoMax-X-Viewport`. It uses a VTK-owned
child NSView and forwards Qt input into VTK; the bridge remains the default.
`--viewport-probe <new-directory>` records synthetic native-window clicks/drag,
actual screen pixels, Retina size, lifecycle and a 27,000-cell transport sample.
These are automated events, not human/cross-platform input acceptance. The
[measured comparison and C# binding prerequisite](../../.project/reports/native-viewport-boundary.md)
do not select a production frontend or establish a speed win. The original
task 0042 DMG's verification is retained; its generated binary was removed under
the [storage retention policy](../../.project/reports/storage-cleanup.md).

The Mac package script is now a compatibility wrapper around the shared
[target build entry](../Build/README.md). All four RIDs are explicit there;
desktop render expectations come from the same target catalog included in the
app. Windows/Linux managed cross-builds do not establish native desktop support.

Qt/Python owns only this experimental window and VTK transport. Original C#
readers decode INP and FRD in separate processes, retaining their actual assembly
ownership. There is no second engineering parser/model or selected persistence
format. The results reader supports the connected 3D solid static workflows described
above; other analysis families and full UI orchestration remain outstanding.

    dotnet build X/Desktop/MeshScene/MeshScene.csproj -c Release --source X/Analysis/artifacts/offline-feed
    dotnet build X/Feasibility/Cad/Inspect/Inspect.csproj -c Release --source X/Analysis/artifacts/offline-feed
    dotnet build X/Results/Inspect/Inspect.csproj -c Release --source X/Analysis/artifacts/offline-feed
    python3 -m venv /private/tmp/prepomaxx-desktop-runtime
    /private/tmp/prepomaxx-desktop-runtime/bin/python -m pip install --require-hashes -r X/Desktop/requirements-packaging-macos-arm64.txt
    /private/tmp/prepomaxx-desktop-runtime/bin/python X/Desktop/viewport.py X/Desktop/nonsequential-cube.inp

Use Open for INP/FRD, Fit, the scalar component selector, click for element/nearest
vertex IDs and nodal value, or drag to rotate using VTK's camera. Values remain
undeformed and in stored units. These controls are deliberately a bounded host
proof, not full vtkControl/Controller parity or an editing application.

Use **Open INP / FRD / VIS** to inspect a VIS version 2 export up to 1 MiB.
The preview draws the CAD edges over the display tessellation. Click a face to
open its source face row in the model tree. The tree shows CAD measurements
in the units declared by the file, with the stored value in each measurement's
tooltip. VIS documents are read-only and the CAD IDs are source IDs.
[Original L-bracket fixture](../Feasibility/Cad/fixtures/l-bracket.vis).

On macOS, the local preview can also open STEP and BREP through the
original 3.0.0 Windows CAD tool supplied by the operator. Create an
isolated CrossOver Windows 10 64-bit bottle and supply the original
`Meshers/Netgen` directory from the pinned release. The launcher checks
all 38 runtime files before conversion. The same option enables STEP and
BREP in the open dialog.

    PrePoMax-X-Viewport.app/Contents/MacOS/PrePoMax-X-Viewport \
      --cad-reference "/path/to/Meshers/Netgen" cad-reference "/path/to/L_bracket_r.step"

This read-only preview accepts files up to 16 MiB whose split produces
up to 32 BREP parts. It converts and decodes every part in a temporary workspace before
opening the validated VIS scene. Each conversion stage has a 60-second
limit. Imports opened through the file dialog or command line run in the
background. The current document stays visible until conversion and decoding
finish. Use **Cancel** to stop the import. Closing the window waits for the
cancelled worker to finish. The macOS app carries the reference hash receipt, and CrossOver
and the Windows runtime are supplied separately.
[Reference replay and setup](../Feasibility/Cad/README.md).

A multi-part import displays all emitted parts together. Each model-tree
entry keeps that part's original CAD measurements. Clicking a face selects
both its part and its source face ID. Source node, triangle and edge IDs
remain scoped to their own part, including coincident nodes shared in
space. If any part fails or the import is cancelled, the prior document
stays visible.

`--cad-native /path/to/native-cad/runtime` enables the checked original
Netgen/OCCT native research build for STEP/BREP imports. It uses the same
background import, cancellation and source part/face picks as the reference
adapter. The receipt and runtime hashes are checked before and after conversion.
[Build and native comparison criteria](../Build/NativeCad/README.md).

With that native profile, **Mesh CAD…** accepts an explicit maximum size in
model units and creates first-order tetrahedra through the original meshing
parameter writer and VOL parser. All parts publish together. Source face/edge
node sets and domain element sets are available in **Configure…**; choose units,
material, sections and constraints explicitly, then **Run analysis**. Cancelling
or a failed mesh preserves the previous document. Jobs retain verified CAD,
BREP/VIS, VOL, parameters, native recipe and base/submitted mesh identities.
General CAD/mesh project persistence and broader element/analysis combinations remain outstanding
in this bounded preview. [Workflow and checks](../../.project/reports/native-cad-static-workflow.md).

After meshing, choose **CAD geometry**, then **Pick faces** or **Pick parts**.
Click to select; Ctrl/Command-click or multi-select source tree items to combine
regions. Orange surfaces show the selection. **Set from CAD…** creates named
node sets from faces/parts or element sets from parts, available in **Configure…**.
**Mesh** and **Results** restore those views without losing the edited model.
Jobs retain each region's source association. [Selection and checks](../../.project/reports/cad-region-selection.md).

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
original C# deck/job service and opens its FRD, retaining its editable definition
in the model tree. **Configure… / Run analysis** submits the edited definition;
**Cancel** uses cooperative stdin cancellation,
with retained output/error/outcome files and fresh job directories. **Job files**
opens the actual workspace. This is a static-solid preview, not full PMX editing.
The Mac --format dmg build needs an explicit --solver-build; the relocated runtime
closure and three self-contained hosts travel with it.
[Installation](INSTALL-macos.md) and [complete uninstall/reset](UNINSTALL-macos.md)
are included in the DMG. Apple container provides Linux workloads, not Mac GUI
acceptance; local native mounted/copy tests are kept distinct from a clean Mac.

`--editor-probe <new-directory>` drives the real Configure dialog, rejects an
invalid material reference, edits modulus/load, then solves baseline and edited
models. `X/Build/verify-editable-solid.py --app <copied-app> --output <new-dir>`
checks its retained deck and DAT values against the independent analytical cube,
including changed-load/displacement rejection controls and unchanged tolerances.

The checked original one-part CAD/C3D4 PMX subset now supports **Open static PMX…**
→ **Edit PMX…** → Save As → reopen → native solve. CAD/mesh/regions remain in
the original file; only the audited modulus/axial force values are editable.
The native CAD profile also displays the saved BREP. Jobs freeze the complete
source PMX. Arbitrary new native CAD-session save is still pending.
[Boundary and checks](../../.project/reports/desktop-cad-pmx.md).

Tasks 0071–0073 extend **Edit PMX…** for this CAD subset with Poisson's ratio,
density in tonne/mm³, signed global X/Y/Z force per node and region selectors
for the solid section, supports and load. Selectors use existing compatible
nonempty named sets; Save As preserves their names and membership, CAD, mesh
and history. Reopen the saved copy before running it. The all-zero load remains
outside the checked static deck contract. [Evidence](../../.project/reports/pmx-region-assignments.md).

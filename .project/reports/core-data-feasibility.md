# Task 0003 — Engineering data and compatibility boundaries

Updated 2026-10-14, Europe/Belgrade. Baseline
`de8f73032a72746e3d6d9afd53d9fbd289eb310a`.
**Verified observation: six unchanged source files build on native macOS ARM64;
30 data/math/stream checks and two CLI usage contracts pass. Linux x64 pending.**

## Authorization and branch

The maintainer approved continuing with a second bounded source-linked probe,
dependency analysis and PMX identity/fixture preparation, and authorized agent
commits/pushes to origin during this continuation. Task 0002 closing evidence
was committed/pushed as `8cc648a3`, with a rendered-log whitespace/hash correction
at `0020d0d8`. Task 0003 starts from that history on
`feature/core-data-feasibility`; no x/main merge occurred.

## Candidate boundaries

| Candidate | Source evidence and measured boundary |
|---|---|
| Matrix | CaeGlobals/CommonClasses/Matrix.cs uses framework math/arrays. Its Drawing2D import is unused in calculations. **Unchanged net10.0 compile succeeds**, zero packages. A textual import scan alone would have misclassified this file |
| Element geometry | GeometryTools.cs + original FeNode/Vec3D compile attempt fails CS0234 at GeometryTools.cs:15, System.Windows.Forms.VisualStyles. No import removal, namespace stub, package or platform retargeting applied |
| Full INP reader | CaeModel/FileInOut/Input/InpModel/InpFileReader.cs returns/populates FeModel/FeMesh and creates numerous element/material/step/constraint types; not a node-only parser. FeElement references concrete linear/parabolic element families. This is a source dependency observation, not a complete closure build or failed portability proof |
| Full FRD reader | FrdFileReader.Read returns FeResults; GetUnitSystem creates UnitSystem, parsing constructs mesh/element/field graphs and uses monolithic Tools. FrdStreamReader is a separate framework-only stream component; testing it does not test FRD interpretation or axisymmetric field normalization |
| DAT/cloud reader | DatFileReader reaches history-field names/results and element enums; CloudPointReader.Read calls Tools.ReadAllLines. Tools also contains WinForms paths and BinaryFormatter load helpers. Textual boundaries only; neither full reader was compiled here |
| Units | CaeGlobals/UnitSystem/UnitSystem.cs selects numerous string/equation converters and package-backed units. Not included or retargeted; metadata's unit string preservation is not numerical unit conversion |
| Geometry metadata | GeometryMetadata/Entity/Property compile unchanged with framework collections and legacy SerializationInfo signatures. Matching/applying metadata through GeometryMetadataMatcher and GeometryMetadataReader reaches BasePart/VisualizationData and is excluded |

Actual minimal candidate-build commands and diagnostics are in
[compiler-boundaries.json](core-data/compiler-boundaries.json). Temporary
SDK-library projects source-linked the listed files, used cleared NuGet feeds,
and ran `dotnet build <temporary>/Boundary.csproj --disable-build-servers -v:minimal`.
No original source/project files were modified. Additional dependencies after
the first compile boundary remain experimental questions.

## Implemented source slice and local evidence

`X/Feasibility/Data/DataProbe.csproj` explicitly links Matrix, IntegrationScale,
FrdStreamReader and the three GeometryMetadata classes. The source manifest
verifies SHA-256 against immutable upstream Git objects and current file bytes.
No packages/project references, namespace stubs, source patches or copied
engineering algorithms. Exploratory types belong to `PrePoMaxX.DataProbe`, not
the production CaeMesh assembly; they must not persist PMX objects.

```sh
python3 X/Feasibility/Data/run-data.py --expect-os macOS --expect-architecture Arm64 --output .project/reports/core-data/macos-arm64.json
```

[Mac evidence](core-data/macos-arm64.json): SDK 10.0.401, .NET 10.0.12, native
Arm64, 30 checks/zero failures and two process usage contracts. Independently
specified checks cover matrix inverse/pivot/product/transpose, nonsequential
entity IDs, values/units, array/copy/merge independence, canonical-value rules,
explicit metadata wire bytes and readback, truncated/unknown-field rejection,
scale weights and mixed text/binary/short-read/1 MiB-buffer behavior.

MatrixInverse on a singular example yields nonfinite values; negative thickness
and radius are preserved by IntegrationScale. These raw observations are
retained, not repaired. Four SYSLIB0050 warnings come from harness use of legacy
SerializationInfo/FormatterConverter; no warning suppression or unsafe
BinaryFormatter switch/package was added. Build log also retains the Mac
CSSM_ModuleLoad diagnostic; the build/tests succeed without a workaround.

The metadata compact block is produced/read through original GetObjectData and
the protected serialization constructor with explicitly constructed
SerializationInfo. No BinaryFormatter is invoked. This is not a PMX/NRBF
reader/writer, general safe-payload decoder, complete malformed-count test or
new production serialization choice. Thirty checks pass only the specified
contracts, not all possible geometry/stream/math inputs.

Five selected newer files are absent at the v2.6.0 task-0002 replay pin; Matrix
exists there. No six-file replay is claimed. Task 0002's actual seven-file
two-revision replay remains intact and is rerun by the next CI job.

## PMX/history work and Windows handoff

Verified source-only observations: Controller.SaveToPmx writes program/version
header, a length-prefixed Deflate graph/model block and separate results.
Its graph roots include Controller, jobs, tree state and SidePanelsState.
Controller's `_model`, `_allResults`, `_commands` and `_annotations` are retained
fields; `_form`, settings and many runtime fields are NonSerialized. Model,
mesh and result serialization/custom blocks and legacy readers must be preserved.
CommandsCollection writes PMH as a dumped List<Command>. RenamedTypeSerializationBinder
maps selected moved identities; it is not a full schema or relocation guarantee.

[Selected source identities](core-data/pmx-source-identities.json) record project
assembly names, declared assembly-version lines, source hashes and selected
root types. This is **not an observed serialized payload graph**. The new
metadata block tests cannot establish file/assembly compatibility.

Maintainer confirms Windows reference access. Prepared
[capture instructions](windows-fixture-capture.md), source-verified existing API
script, and [manifest template](core-data/windows-fixture-manifest.template.json).
The first input is repository cube.inp: eight nodes, one C3D8 element. Live
Windows fixture capture, actual type graphs, Windows comparison and PMX/PMH
round-trip remain pending. No settings/token file is requested.

## Linux verification and remaining gates

Prepared native hosted job `core-data-linux-x64` for the new feature branch.
It reruns task 0002's comparison regressions and both source revisions, then
runs task 0003 with Linux/X64 assertions and the Mac reference. Reports retain
tool/source/runtime/CI identifiers; image digest and native CPU evidence must
be retained from the actual log. Preparation is not a Linux pass.

Additional local validation: a deliberately changed metadata face-ID observation
was used as the reference for `run-data.py --reference`; it returned exit 1,
`comparison.matches: false` and retained all 30 measured checks. Python syntax,
source/tool hashes and YAML parsing were checked. Changed-document links and
`git diff --check` pass. The Windows script is syntax/API-source checked, not
live Windows tested.

Native-source recovery remains an independent prerequisite: existing notices
point to modified Netgen/NetGenMesher, QuadWild, Gmsh and QuadMesher sources.
This task does not recover/build/substitute those tools or contact maintainers.
No GUI, VTK, model/controller extraction or production dependency change is
included. Task 0003 completes its bounded probe/inventory/capture preparation
after native Linux evidence; the broader Windows/file/native/rendering gates
remain separate work.

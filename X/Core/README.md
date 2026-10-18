# Partial shared engineering libraries

Task 0020 adds a portable `CaeModel` slice and a usable standalone INP mesh tool:

```sh
dotnet run --project X/Core/MeshDeck -c Release -- inspect X/Core/MeshDeck/unit-cube.inp
dotnet run --project X/Core/MeshDeck -c Release -- measure X/Core/MeshDeck/unit-cube.inp
dotnet run --project X/Core/MeshDeck -c Release -- export-mesh X/Core/MeshDeck/unit-cube.inp new-mesh.inp
```

MeshDeck uses the original node, element/connectivity and set-label parser,
mechanically separated into partial InpFileReader in its original assembly.
The original CalElement writer retains formulation names and connectivity;
the transport writer retains coordinate roundtrip precision, IDs and sets.
The optional `--pyramids wedges|hexahedrons` export flag explicitly requests
the original collapsed-element conversion, including supported I/R input
aliases. Quadratic tetrahedra can be inspected/exported; their measurement
stays gated. Existing output files are refused. Formulation fallback warnings
are visible during inspect and refused for export.

This is **mesh-only**: materials, BCs, steps, surfaces and other omitted keywords
are listed in JSON and not written. INCLUDE, scoped parts/assemblies and
coordinate transforms require the full model reader and are rejected. Input
is bounded to 16 MiB and 200,000 nodes/elements; the reused measurement host
retains its 10,000-item limit. This is not full FeMesh/FeModel, PMX or a
solve/results workflow. Standalone reads serialize their existing parser state;
the original UI reader's concurrency policy is unchanged.

`source_layout.py` verifies exact method/attribute extraction against Git;
`workflow-sources.json` guards six added unchanged source files and the new
boundary code. StandardValueAttribute is separated unchanged from its editor
in CaeGlobals. All original net48 projects include their separated files;
their Windows full builds still require native verification. The selected
closure is now 48 files. The verifier adds 68 mesh workflow checks and 11 CLI
controls to the prior 150 accepted checks/28 CLI/four data controls. Ten Python
guard tests reject unreviewed source/fixture/adapter/boundary changes. The
development ZIP includes MeshDeck, its example, source and license.

Task 0019 adds pinned upstream replay against the RC2 source marker and the
17 October post-RC2 revision. The shared engineering bytes and mapping vectors
are identical at both pins. The verifier builds from temporary Git snapshots,
applies the same two proven boundary adapters, and runs the existing checks.
Unknown revisions and changed engineering files/vectors are refused until review.
This proves the selected slice only; the full application and distributed RC2
Windows ZIP have not been matched or validated by these checks.

```sh
python3 -m unittest discover -s X/Core -p test_upstream_replay.py
python3 X/Core/verify.py --upstream-revision 3.0.0-rc2 --output X/Core/artifacts/rc2.json
python3 X/Core/verify.py --upstream-revision post-rc2-2026-10-17 --output X/Core/artifacts/post-rc2.json
```

Reviewed names/full SHAs are in `upstream-replays.json`. No fetch, production
repin or branch change is performed by the verifier. CI fetches those two exact
objects from the fork before executing both replays. Native Windows and hosted
x64 replay execution require their own evidence; configured CI is not a pass.

Task 0017 local development build: original finite-element families and geometry
methods now compile into CaeMesh. A measurement CLI reports length/area/signed
volume, centroids, scalar field integrals and VTK/Gmsh connectivity. This is a
core command-line build; GUI, full mesh/result readers and CAD are still separate.

```sh
dotnet run --project X/Core/MeasureMesh -c Release -- X/Core/MeasureMesh/unit-tetra.json
python3 X/Core/package.py
python3 X/Core/check-package.py --archive X/Core/artifacts/development-build/PrePoMaxX-Core-development.zip --report X/Core/artifacts/development-build/verification.json
```

The package is written under `X/Core/artifacts/development-build/` and includes
both CLI tools, examples, matching source, license and a hash manifest. It
requires an installed native .NET 10 runtime. Its two published examples pass
Mac/Linux ARM64, and its extracted source rebuilds independently.
The native Linux x64 CI job also publishes this ZIP with package/verification
reports. Use that exact commit's job artifacts to download it. Archive verification
checks every manifest entry, rebuilds extracted source, runs both published
examples and the quadratic-tetrahedron gate, and rejects three altered archives.

The element suite has 95 accepted checks plus **two open correctness failures**
in unchanged original code: quadratic-tetrahedron affine integration gives
26.794910717854155 rather than 28; the quadratic-pyramid IsParabolic helper
returns false. The measurement host rejects quadratic tetrahedra and uses
explicit factories for the other 13 families. `elementTests.fullyAccepted`
stays false. Initial strict failure evidence is retained; no tolerance or
engineering algorithm was changed. Curved-element/full native Windows behavior
still requires follow-up. See `.project/reports/shared-element-kernel.md`.

Tasks 0013/0015/0017: callable engineering slices targeting .NET 10. The projects
source-link existing engineering files; they do not copy or rewrite algorithms.
Build with a .NET 10 SDK. No external packages or feeds are required.

```sh
dotnet build X/Core/PrePoMaxX.Core.slnx -c Release -m:1
dotnet run --project X/Core/MapFace -c Release --no-build -- X/Core/MapFace/equilateral.json
python3 X/Core/verify.py --output X/Core/artifacts/verification.json
```

On Windows use `python` for the installed interpreter. Optional verifier flags
`--expect-os Windows|Linux|Darwin` and `--expect-architecture X64|Arm64` assert
the actual native runner. `-m:1` avoids worker-process failures in restricted
Windows execution environments. The verifier builds in a temporary directory.
The first mapping slice at ac51fc77 passed native Windows x64, Mac ARM64,
Linux ARM64 and hosted Linux x64 (pipeline #2956616374). The expanded data slice
passes Mac/Linux ARM64 and hosted x64 at 236b1a2e (pipeline #2956740201);
native Windows execution of the expanded assembly slice is pending.

The `CaeGlobals` assembly contains the existing CaeException, Matrix and Vec3D.
`CaeMesh` references it and contains FeNode, TransfiniteSideTriple,
ThreeBlockGrid and the full ThreeBlockMapping implementation, plus
GeometryMetadata/Entity/Property and IntegrationScale/IntegrationScaleType.
It also contains FeElement, the dimensional base classes, 17 original concrete
element classes, vtkCellType and internal GeometryTools. CompareIntArray stays
in CaeGlobals. The solver element-name enums with DynamicTypeDescriptor UI
metadata and ElementTypeCount's full-mesh closure are not included yet.
The partial `CaeResults` assembly contains the original internal FrdStreamReader.
It stays internal; only `PrePoMaxX.CoreDataTests` is a friend assembly for tests.
This is the buffered stream utility, not the complete FRD results reader. Namespaces,
type names and assembly versions remain unchanged. These are partial libraries
for a separate portable host, **not replacements to copy into the existing
Windows application's folder**. They are not a PMX reader or complete core.

The first existing application-source change moves the unchanged CaeException
class from ExceptionTools.cs into its own file, included by the original net48
project. ExceptionTools and MessageBoxes remain in the Windows build. The
portable build can now report domain errors without referencing Windows forms.
Task 0017 additionally removes one unused WinForms VisualStyles import from
GeometryTools. Every other byte in that file is verified against the baseline;
all other added element/comparer sources are linked unchanged.

MapFace reads a JSON object with three `sideUv` and matching `sideXyz` point
arrays. Sides include both endpoints and form a closed loop. It returns inner
UV coordinates, boundary counts, quad connectivity and folded-quad count.
Boundary IDs run along the sides; inner IDs follow them. This host limits input
to 1 MiB and 512 boundary segments. It does not evaluate a CAD surface; an
in-process caller can supply the existing `Map` evaluator callback to obtain
inner XYZ coordinates. This JSON is a small tool input, not a document format.

Verification runs all 13 original vectors, independent centroid/area/topology/
numbering/evaluator/error checks and changed-coordinate/connectivity controls
(25 checks total), plus nine CLI usage/input-rejection checks. The verifier
also checks exact baseline engineering bytes and the mechanical exception
separation. The historical meshing probe still measures its pinned original
ExceptionTools compilation boundary from Git, separately from this library.

The verifier also executes all 30 existing DataProbe assertions through library
project references, with no engineering source compiled into the test assembly.
Checks/observations and two CLI usage controls must match the retained native
Windows data report. Seven type contracts check original assembly-qualified
names, visibility and serialization markers; the metadata interfaces are retained.
Four changed-evidence controls reject moved ownership, changed metadata wire
bytes, missing checks and a desktop dependency. Original algorithms and the 30
assertions are unchanged. `SHARED_CORE` only adds ownership reporting to the
reused harness. Four SYSLIB0050 test warnings are retained for the existing
SerializationInfo/FormatterConverter metadata assertions; no BinaryFormatter
or object deserialization is enabled.

For a supplemental check on native Windows x64:

```powershell
./X/Core/verify-legacy.ps1 -OutputDirectory ./X/Core/artifacts/legacy
```

That compiles the same slice against installed .NET Framework runtime assemblies
and executes geometry/error/type-identity checks under the legacy CLR. It is
not a full net48 solution build. Windows native validation is recorded in
`.project/reports/shared-core-first-slice.md`; expanded data evidence and the
exact offline Podman command are in `.project/reports/shared-core-data-slice.md`.
The existing native Linux x64 CI job automatically runs the expanded verifier
after a future authorized publication. Full PMX/history semantics,
interactive VTK, CAD/native-source recovery and release parity remain separate.

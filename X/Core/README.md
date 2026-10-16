# First shared engineering libraries

Task 0013: the first callable library slice, targeting .NET 10. The projects
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
The separate GitLab job is prepared for native Linux x64; it has not run yet.

The `CaeGlobals` assembly contains the existing CaeException, Matrix and Vec3D.
`CaeMesh` references it and contains FeNode, TransfiniteSideTriple,
ThreeBlockGrid and the full ThreeBlockMapping implementation. Namespaces,
type names and assembly versions remain unchanged. These are partial libraries
for a separate portable host, **not replacements to copy into the existing
Windows application's folder**. They are not a PMX reader or complete core.

The only existing application-source change moves the unchanged CaeException
class from ExceptionTools.cs into its own file, included by the original net48
project. ExceptionTools and MessageBoxes remain in the Windows build. The
portable build can now report domain errors without referencing Windows forms.

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

For a supplemental check on native Windows x64:

```powershell
./X/Core/verify-legacy.ps1 -OutputDirectory ./X/Core/artifacts/legacy
```

That compiles the same slice against installed .NET Framework runtime assemblies
and executes geometry/error/type-identity checks under the legacy CLR. It is
not a full net48 solution build. Windows native validation is recorded in
`.project/reports/shared-core-first-slice.md`; Mac ARM64, Linux ARM64 and hosted
Linux x64 must still execute this new library build. Full PMX/history semantics,
interactive VTK, CAD/native-source recovery and release parity remain separate.

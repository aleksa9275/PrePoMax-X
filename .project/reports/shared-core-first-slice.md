# First shared engineering implementation

2026-10-16, research/native-feasibility. The maintainer requested finishing the
supplied model's comparison and proceeding to building. Task 0013 implements
the first reusable library slice; it does not wait for full release acceptance.
Changes remain uncommitted and are not integrated into x/main.

Publication continuation: the maintainer subsequently authorized commit/push
and MacBook handoff in task 0014. The Windows synthetic C++ compiler gap noted
below has since been closed by the final pass; historical infrastructure
diagnostics remain retained. See the Windows report's closeout section.

## Delivered behavior

`X/Core/PrePoMaxX.Core.slnx` builds partial .NET 10 CaeGlobals/CaeMesh libraries,
a MapFace executable and regression tests. A host can now call the existing
full ThreeBlockMapping implementation without Windows forms or a native
mesher. The supplied equilateral JSON example produces six boundary nodes,
one inner node at (1, sqrt(3)/3), three quads and zero folded quads.
The in-process API retains the existing surface-evaluation callback.

The explicit source closure is CaeException, Matrix, Vec3D, FeNode,
TransfiniteSideTriple, ThreeBlockGrid and ThreeBlockMapping. Original math and
mapping files are source-linked byte-for-byte from baseline de8f7303. No
engineering algorithm was copied, moved or translated. The only existing
source change moves the unchanged CaeException class out of ExceptionTools.cs
into CaeException.cs and includes it in the original CaeGlobals net48 project.
Windows presentation methods stay unchanged. Namespace, constructors, assembly
ownership and version 1.0.0.0 are retained.

These partial assemblies are for a separate portable host. They must not be
installed over the full Windows application's assemblies. The small JSON host
input is not a proposed PMX/document format. No frontend or serializer is chosen.

## Verification

[Native Windows evidence](shared-core/windows-x64.json): SDK 10.0.402, native
x64 process. The solution builds with zero warnings and zero errors using
serial MSBuild. All 25 checks pass, including:

- All 13 original mapping vectors, with exact connectivity/fold counts and
  zero maximum inner-coordinate deviation on this runner.
- Independent equilateral centroid, area, manifold edges, Euler topology,
  boundary numbering, scale/translation and surface callback checks.
- Invalid geometry/count/evaluator domain errors and exception/type identity.
- Changed-coordinate/connectivity controls and absence of Windows/presentation
  assembly references in the portable libraries.

Nine CLI checks pass: usage, missing input, malformed JSON, null root, missing
sides, null side, size limit, open boundary and invalid block counts. The valid
sample is checked independently and its input hash remains unchanged. An early
negative test caught an unhandled InvalidDataException; the explicit catch was
added and the complete verifier rerun. A Windows text-encoding mismatch in the
source verifier was corrected by reading UTF-8 explicitly.

[Legacy Windows evidence](shared-core/legacy-windows.json): the same source
slice compiles against installed .NET Framework runtime assemblies and runs
under CLR 4.0.30319.42000. Geometry, domain-error and assembly-qualified
CaeException identity checks pass. This is a source-slice regression check,
not a full original net48 application/solution build. The reproducible route
is `X/Core/verify-legacy.ps1`; the portable verifier is `X/Core/verify.py`.

Parallel MSBuild initially returned failure with no compiler diagnostic in the
restricted environment. Serial `-m:1` builds and publish succeed. A published
Windows mapping host was executed successfully with the example JSON. No
package/runtime upgrades were introduced into the production solution.

The historical meshing probe now explicitly recognizes only the mechanical
exception separation and measures its old baseline boundary using original Git
bytes. It still rejects other source changes. Its Windows execution reaches
the same [missing C++17 compiler result](shared-core/meshing-infrastructure.json),
not a passed native C++ check. The PMX suite still has one sandbox hardlink
creation error; it was not skipped or weakened.

## Native model evidence and next implementation boundary

The [supplied model follow-up](windows-reference-validation.md#supplied-private-model-follow-up)
closes the intended native read/save/reopen and results-enabled/disabled
comparison: model bytes are unchanged; result payloads match the CrossOver
save; observed job/member changes recur consistently. Private models remain
outside Git. This is sufficient to proceed with this limited mapping slice;
it is not full persistence/clone/history equivalence.

Next run this exact new library verifier natively on Mac ARM64 and Linux ARM64,
then the prepared GitLab Linux x64 job when publication is authorized. Hosted
CI configuration is prepared, not executed. Expand the next shared model/deck
boundary incrementally after those runs. Interactive VTK/frontend selection,
custom mesher-source recovery, CAD behavior, full history/clone/persistence and
release parity remain separate requirements. No commit, push, merge, F001
implementation or upstream communication was performed.

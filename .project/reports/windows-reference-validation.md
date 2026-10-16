# Native Windows reference checkpoint — 2026-10-16

Task 0011 continued on `research/native-feasibility` from `f1e757f1` after the
maintainer authorized the planned Windows work. This is a bounded native
reference/probe checkpoint. Production source, project files and algorithms are
unchanged. No commit, push, integration or architectural selection was made.

## Reference and environment

Verified observation: Windows x64 on an AMD Ryzen 5 3450U, build
26300.9457, display version 26H2. Python 3.12.14 is the bundled interpreter.
The system's Python aliases cannot execute; no .NET SDK was initially present.
An isolated SDK 10.0.402/runtime 10.0.13 was prepared with Microsoft's official
`dotnet-install.ps1` under the disposable workspace, without changing system PATH.
No compiler or production native-tool version was substituted.

The available desktop copies are 2.5.1 dev, 2.6.0, 2.6.1 dev, 2.6.2 dev and
3.0.0 RC1. Their executable hashes are retained in
[manifest](windows-reference/manifest.json). This checkpoint used a separate
2.6.0 copy without the user's settings, tokens or models. All eight application/
managed/VTK hashes in the prior official CrossOver provenance match. All six
solver/runtime hashes also match. A binary-to-source-commit correspondence is
not independently established by that match.

The actual 2.6.0 help has no script/RPC switches; ordinary GUI import/save/open/
export and existing native regeneration were used. The application has no work
directory in fresh settings. Initial opens reported that missing directory;
the disposable copy was configured to use its PMX folder. Later regenerated
readback completed without that error. User installations were not modified.

## Controlled persistence and history

Shareable INP inputs/exports are in [fixtures](windows-reference/fixtures/).
PMX and PMH stay outside Git because command records contain local paths.
Their hashes and byte lengths are in the manifest. No private production model
was used or searched for during capture.

The mesh-only cube was imported with `MM_TON_S_C` units, saved to
`cube-mesh.pmx`, reopened and exported again. Both exports preserve node IDs
1–8, their eight unit-cube coordinates, element ID 1/C3D8 and connectivity 1–8.
The original input element set `Cube` survives. The generated part is named
`Solid_part-1`; that is original-application behavior, not an imposed rename.

The controlled definitions fixture was imported into a new 3D/MM_TON_S_C model.
Its expected values were specified before import:

| Entity | Expected and observed after save/reopen and history regeneration |
|---|---|
| Material XSTEEL | E 210000 MPa, Poisson ratio 0.3, density 7.85e-9 ton/mm³ |
| Solid section | Material XSTEEL assigned to element set XSOLID = [1] |
| NALL | Nodes [1,2,3,4,5,6,7,8] |
| X0 / Y0 / Z0 / X1 | [1,4,5,8] / [1,2,5,6] / [1,2,3,4] / [2,3,6,7] |
| Static step | Initial increment 1 s, total time 1 s |
| Displacement_rotation-1/2/3 | X0/U1=0, Y0/U2=0, Z0/U3=0 |
| Concentrated_force-1 | X1/U1 direction, 25 N per node; total 100 N |

Original 2.6.0 imports the requested step name `XSTATIC` as `Step-1` and assigns
the generated BC/load/section names. The exported static card additionally has
the original defaults Inc=100, minimum increment 1e-5 and maximum 1e30. These
observations are explicit; preservation of the requested import step name is
not claimed.

Undo of Import prompted for regeneration; Regenerate all left the empty model
with its 3D/unit properties. The menu then showed Undo—Set new model properties
and Redo—Import file. Redo restored one part, five node sets, one material,
one section/static step, three BCs and one load. This exercises an atomic INP
import history; individual GUI creation/edit commands remain outside this case.

A separate copy was regenerated through the original native command:

```powershell
& '<reference>\PrePoMax.com' --r1 '<capture>\definitions-regenerated.pmx' -g No -o Yes -w '<capture>'
```

The original PMX remained unchanged. The regenerated copy opened in the GUI.
Its exported snapshot and every nonvolatile deck line match the reopened
original. The controlled checker passes **30 expected/observed checks and three
negative controls** (changed connectivity, material value and section region).
See [semantic evidence](windows-reference/capture-semantics.json).

The history editor shows Clear, Set new model properties, Import file, Save to
file and Export model to Calculix in that order. After final export, Undo targets
that export and Redo is disabled; the active history is at its end. PMH was
copied from the reference application's own `history.pmh`, not a user project.

The legacy process prints successful completion but exits `4294967295`
(`0xFFFFFFFF`). Retain this failed process-status contract separately from the
verified functional regeneration. Context source at release pin
`9e91252563739ee5304cea16c34863dfb17a74d5`, `PrePoMax/Program.cs:Main`, ends
with `Process.GetCurrentProcess().Kill()`; this corroborates the observation
without proving exact producer source. [Actual command/log](windows-reference/regeneration.json).

Safe NRBF inventories pass for cube/original definitions/regenerated definitions.
The scalar comparison matches 22/23 selected types; the only changed member is
`CaeModel.FeModel._hashName`. Source constructors create that identifier randomly.
Material/step/BC/load scalar records match. Scalar comparison alone does not
prove associations; the explicit deck snapshots provide the bounded association
check here. Neither establishes universal PMX compatibility.

## Native compute and tooling results

| Check | Native Windows outcome |
|---|---|
| Core baseline and pinned 2.6.0 replay | Each 23 checks + 2 CLI contracts pass; all portable observations exactly match Mac |
| Engineering data | 30 checks + 2 CLI contracts pass; exactly matches Mac |
| Evidence regression suite | 6/6 pass after isolating Windows host discovery in the mocked-subprocess tests |
| PMX synthetic suite | 23 pass; one infrastructure error creating a hard link; full 24-test gate remains open |
| PMX scalar controls | 3/3 pass |
| Shell-junction fixture contracts | Four cases and two regression controls pass; still not CAD meshing |
| Structured kernel | Source identities verified; not executed because a native C++17 compiler is absent |
| Exact bundled CalculiX 2.22 | Seven analytical checks + altered-displacement negative control pass, exit 0 |

The solver is the original bundled Windows executable with identical runtime
DLLs, run single-threaded. Displacements match the CrossOver reference exactly;
maximum printed force/stress differences are approximately 1.61e-13 N and
1.12e-12 MPa. The retained input, DAT/FRD/STA/CVG and report are in
[solver evidence](windows-reference/solver/reference.json). This is a synthetic
native solve, not full application/results-reader parity.

Two measured research-test fixes were made: use `sys.executable` rather than
the unusable `python3` alias; mock host discovery in two CI-orchestration tests
because Python's Windows discovery invokes `ver`, otherwise inflating the
mocked probe call count. Before-fix evidence is retained. The hardlink test was
not skipped, weakened or reported as passed. Same-file CLI refusal was also
checked independently; it does not replace the hardlink case.

The clone originally materialized LF Git text as CRLF. Repository-local
`core.autocrlf=false` and `core.eol=lf` were set. Only files differing from Git
by line endings were restored to exact Git bytes; the actual test edits were
preserved. Source-hash failures are retained as infrastructure observations,
not accepted by changing manifests. Sandbox temp/NuGet access required isolated
temporary, CLI-home and AppData directories. No feeds/packages were added.

## Remaining gates at the first checkpoint

Task 0011's controlled cube/import-history checkpoint is recorded, with its
legacy exit-status limitation. The overall Windows gate stays open for the
hardlink test outside the restricted sandbox, a pinned native C++ toolchain and
structured-kernel/compiler-mode execution. Individual entity-edit histories,
private legacy model comparisons and job/environment policy, PMX with/without
saved results, CAD T-junction/gap meshing and genuine VTK/DPI/pointer interaction
also remain open. Other application versions are identified, not validated.
No frontend, serializer, native compiler policy or F001 implementation is selected.

Reproduce the controlled checker and native solve using their READMEs under
`X/Feasibility/Data` and `X/Feasibility/Solver`. The app bundle, SDK and PMX/PMH
corpus are in the session's disposable `work/windows-reference` outside Git.
Maintainer retains commit/push control.

## Supplied private model follow-up

2026-10-16: the newly supplied file is byte-identical to the CrossOver input
(80e3c303a0719317af9d23016a4f70fe5f5acb91d731e704ec45dcbbfe2e0379).
The same original 2.6.0 binary opens it natively, displays the model and saved
results, saves a separate copy and reopens with the results visible. The old
2.5.1-dev version warning appears on initial opening. The original is unchanged.

The native save preserves the custom model/mesh block. Its inflated result
mesh/node lookup and all four field payload hashes exactly match the CrossOver
save. All original field bytes survive the documented datatype insertion; the
33-byte opaque history trailer also matches. Native and CrossOver inventories
have identical non-string type rows, including members/array shapes/counts.
Only System.String record count differs: 210 native versus 228 CrossOver.
This does not establish equality of every graph value/reference association.

The same 27/29 shallow engineering type comparisons match. Changes are confined
to the job executable/work directory/CPU/environment settings and the added
FeModel keyword-override member. Stable 2.6 Controller.cs lines 12273-12302
unconditionally copy the current solver settings into jobs, consistent with
this observed drift in both environments. That is a source-based explanation;
the exact source correspondence of the release binary is not established.

A second Save As with the isolated app's “Save results in .pmx files” set to No
produces a 1,559,989-byte file. It reopens with the same model and no result
fields. The model block is unchanged and the remaining four bytes encode a
zero result count. The results-enabled file is 16,374,353 bytes. All private
PMX files and raw UI data remain outside Git. Metadata/comparisons are under
[private-model evidence](windows-reference/private-model/manifest.json).

The 24-test PMX rerun still has 23 passes and one sandbox-denied hardlink error.
The native C++ compiler remains unavailable; full histories, CAD and candidate
interactive VTK are separate release gates. No private history regeneration or
production-model solve was attempted. The maintainer explicitly requested moving
to building: [task 0013](../tasks/0013-shared-core-first-slice.md) now implements
the first shared-library slice. Earlier unchanged-source/research-only notes
above describe the prior checkpoint, not this newly authorized implementation.

## Final native C++ closeout

The maintainer requested completing useful remaining Windows work before MacBook
handoff and publishing the reviewed changes. A portable compiler was unpacked
inside the disposable workspace, with process-local PATH only. The
[official LLVM-MinGW release](https://github.com/mstorsjo/llvm-mingw/releases/tag/20261006)
asset `llvm-mingw-20261006-ucrt-x86_64.zip` is 190,836,485 bytes; its SHA-256
`317492c456aa27ee607a5919f1d2d38dcdc1112516a24d0bf4b00d078f52d17a`
matches the release asset digest. Actual compiler is Clang 23.1.3 targeting
x86_64-w64-windows-gnu. [Provenance](windows-reference/compiler-provenance.json).

Both [compiler-default](windows-reference/meshing-native-default.json) and
[explicit contraction-off](windows-reference/meshing-native-fp-off.json) runs
pass all 13 upstream vectors, 17 independent native geometry/error checks,
seven managed count/grid checks and 1,728 exact C#/C++ count comparisons. The
historical pinned ExceptionTools/MessageBoxes compile boundary is still measured
separately; the new shared library already removes it through class separation.
No production compiler defaults changed. This does not resolve the recorded
Linux ARM64 GCC contraction sensitivity or establish a complete CAD mesher.

The remaining hardlink case needs an ordinary Windows process outside the
restricted sandbox. It remains an infrastructure error, not an accepted pass.
No further Windows-only gate blocks the approved next shared-core increment.
Mac ARM64/Linux ARM64 library runs, hosted Linux x64 CI and the next measured
model/deck boundary can proceed. Full CAD/VTK/history/serialization gates remain
release work. Task 0014 and the MacBook handoff define publication/continuation.

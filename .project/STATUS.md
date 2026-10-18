# Project status

## Current — task 0021 authorized publication

2026-10-18: maintainer explicitly requests commit/push of completed task 0019/
0020 changes to origin/research/native-feasibility. Publication/remote and exact
native x64 CI/artifact verification are in progress. Existing Mac/Linux ARM64
evidence and both correctness failures/gate remain. [Publication report](reports/mesh-workflow-publication.md).
After publication/closing evidence, explain next steps and wait for maintainer
approval before new feature work; this supersedes prior continuation wording.

## Latest — task 0020 portable mesh input/export implemented locally

2026-10-18: maintainer requests proceeding while preparing Windows. New
MeshDeck inspect/measure/export-mesh loads actual standalone INP node/element/
set data through the mechanically separated original parser and reuses the
original CalElement writer. Partial CaeModel and the unchanged enum metadata
attribute retain original assembly/net48 ownership. Source closure is 48 files.
Current/RC2/post-RC2 snapshots each pass native Mac/Linux ARM64: previous 150
accepted checks plus 68 mesh checks, 39 CLI controls/four data controls and ten
source/replay tests. Both correctness failures/measurement gate remain.
Portable outcomes/tool fingerprints match across all six runs.

Runnable three-tool source/binary ZIP and Windows instructions are prepared;
full evidence/package checks: [mesh workflow report](reports/portable-mesh-deck-workflow.md).
All task 0019/0020 changes remain **uncommitted**; no new publication/integration.
Native Windows/new-commit hosted x64 and full net48/RC2 oracle remain pending.
This is mesh-only, not complete material/BC/step/deck/solve/results or persistence/
CAD/VTK parity. User-started Podman remains running. Next work expands original
model/deck behavior toward the accepted workflow; remaining gates stay explicit.

## Latest — task 0019 RC2 sync and portable replay

2026-10-18: new maintainer instruction supersedes task 0018's stop boundary.
Local/origin master fast-forwarded de8f7303 → f6273e39, remotely verified;
research branch remains 2f2eca94. RC2 marker is 912fb3d0; ten later commits
already add composite model/results/API/UI behavior. Selected engineering
bytes/vectors are unchanged. Both new pins and the working slice pass native
Mac ARM64: 25 mapping/30 data/95 accepted elements, 28 CLI/four data controls;
seven replay guard tests pass. Both original correctness failures/host gate
remain. New pinned replay/CI tooling and records are **uncommitted**.

After the maintainer started Podman, native Linux ARM64 retry also passes all
three builds and seven replay guard tests; portable engineering/CLI outcomes
and tooling fingerprints match Mac exactly. The user-started VM remains running.
[Current report](reports/upstream-3.0.0-rc2.md) and verification.json retain all
six reports and comparisons. Native Windows/hosted x64 replay remains pending.
Git-object merge rehearsal has no conflicts; no branch integration performed.
Patched Netgen DLL and new model/results serialization fields need explicit
parity work. [Impact, evidence and faster implementation route](reports/upstream-3.0.0-rc2.md).
Older task boundaries below are historical.

## Latest — task 0018 publication and downloadable CI build complete

Task 0017/0018 published at **b83fa49f**; remote SHA verified. Native x64
pipeline **#2956835416 passed both jobs**: 25 mapping/30 data/95 accepted element
checks, CLI/gate controls and actual ZIP source-rebuild/manifest/tamper checks.
Both known correctness failures remain explicit; no numerical fix is claimed.
Downloaded ZIP/source/tool fingerprints independently verified against the
published commit. The x64-produced bundle also rebuilds/runs on native Mac ARM64.
[Pinned download/evidence](reports/shared-core-build-delivery.md).

This closes the requested small task. Usage rose from 72% to 87% before closing
records; no reset used. No further feature work in this budgeted continuation.
Native Windows new-slice and existing GUI/persistence/CAD/VTK/native-source/
compiler-policy gates remain. Podman is stopped. Older checkpoints follow.

## Current publication — task 0018

2026-10-16: maintainer explicitly requests committing/pushing task 0017 and
choosing one small task within 20% of the five-hour allowance. Task 0018 adds
downloadable native Linux x64 CI development bundles with manifest/hash checks,
extracted-source rebuild, published CLI samples/tetrahedron gate and three
tamper controls. Initial account usage was 72%; no reset used. Publication and
exact-commit hosted artifact verification are in progress. Existing numerical
algorithms and the two open correctness checks remain unchanged.

## Latest local work — task 0017 finite-element kernel and runnable CLI bundle

2026-10-16: completed the next bounded local build after publishing task 0015.
Original dimensional/linear/parabolic element families and GeometryTools now
compile in partial CaeMesh; CompareIntArray stays in CaeGlobals. The only added
production-source edit removes an unused WinForms VisualStyles import. All
37 selected engineering-source identities/bytes are guarded. New MeasureMesh
calls existing geometry/integration/connectivity methods and preserves IDs.

Mac/native Linux ARM64 each pass 95 accepted element/host checks, the prior 55
mapping/data checks, 28 CLI controls and four evidence-rejection controls.
**Two independent correctness checks remain failed** in original source:
quadratic tetrahedron affine integral 26.794910717854155 versus expected 28,
and quadratic-pyramid IsParabolic classification false. Initial failures and
quadrature-moment diagnosis are retained. No algorithm/tolerance changed;
quadratic tetrahedra are blocked in the new host. Full element acceptance is
false. [Report](reports/shared-element-kernel.md).

A runnable local .NET 10 development ZIP contains MapFace/MeasureMesh,
examples, corresponding source and license. Published examples run on Mac and
Linux ARM64; extracted source rebuilds. Task 0017 is **uncommitted**. Native
Windows/new-commit x64, correctness resolution and GUI/full persistence/CAD/VTK/
native-source/compiler-policy gates remain. Podman is stopped. Last published
closing evidence is 1f1f51c4; its pipeline #2956771332 also passed. No new
frontend/default serializer or integration decision was made.

## Current publication — task 0016 complete

2026-10-16: maintainer explicitly requests committing/pushing task 0015 and
continuing bounded shared-core implementation toward a working build. The
reviewed local data slice/evidence is published at **236b1a2e** on the origin
research branch. Exact-commit **pipeline #2956740201 passed both jobs**; downloaded
shared-core JSON matches published source/tool hashes and all Mac/Linux ARM64
portable outcomes (25 mapping/30 data/seven type contracts/11 CLI/four controls).
[Publication evidence](reports/shared-core-data-publication.md). Expanded native Windows
and the existing full-application release gates remain pending. Older
uncommitted-only statements below describe the prior checkpoint.

## Latest — Mac continuation and shared data libraries

2026-10-16 (Europe/Belgrade): inspected clean Mac checkout at f1e757f1 before
fetching. Bundle prerequisite/checksum verified; imported auxiliary ref and
fast-forwarded to **ac51fc77449da26d9c25ddedd924feda2a55e7db**. Authorized push
to origin/research/native-feasibility succeeded; remote SHA verified.
[Pipeline #2956616374](https://gitlab.com/aleksa9275/pre-po-max-x/-/pipelines/2956616374)
passed both research and shared-core native Linux x64 jobs. The exact first
slice passes Mac ARM64/Linux ARM64 (25 mapping checks/nine CLI controls each),
matching retained Windows outcomes, vectors, source and tool fingerprints.
The hosted shared-core JSON and sanitized job traces are retained locally.

[Task 0015](tasks/0015-shared-core-data-slice.md) completes the bounded local
data increment: partial CaeMesh now owns unchanged geometry metadata and
IntegrationScale; partial CaeResults owns the unchanged internal FrdStreamReader.
Mac/native Linux ARM64 pass 30 reused data checks, seven type contracts,
two data CLI controls and four verifier rejection controls, retaining 25 mapping
checks/nine mapping CLI controls. Data checks and observations match the native
Windows source-linked reference. Four existing SYSLIB0050 metadata-test warnings
are retained; no unsafe serialization is enabled. The isolated old DataProbe
also still passes 30 checks/two CLI controls on Mac.

New implementation/evidence remain **uncommitted**. Native Windows and exact
new-commit Linux x64 execution of the expanded assembly slice remain pending;
the ac51fc77 pipeline does not cover these edits. [Report/commands](reports/shared-core-data-slice.md).
No additional production source/project edits, frontend/default serializer,
F001, x/main/upstream or release-policy changes. Private transfer untouched
outside Git. Podman VM is stopped. CAD/interactive VTK, full persistence/history/
clone, matching custom native-source recovery and Linux ARM64 GCC default -O2
contraction sensitivity remain explicit gates. Older sections are historical.

## Latest — native private-model comparison and first shared libraries

2026-10-16: maintainer supplied the same 2.5.1-dev PMX (hash verified) and
explicitly requested proceeding to building. Native original 2.6.0 read/save/
reopen displays the model and embedded results. Model/mesh bytes are unchanged;
inflated result mesh and all four field payloads exactly match the CrossOver
save. All non-string type-inventory rows match CrossOver; only the string-record
count differs (210 native / 228 CrossOver). The same 27/29 shallow engineering
types match the original; job/settings and new keyword member changes recur.
The stable 2.6 source's unconditional application of solver settings explains
the observed job-field policy as a source-based inference. A separate save with
results disabled reopens with the model, no result fields and identical model
bytes. The supplied original remains unchanged and outside Git.

[Task 0013](tasks/0013-shared-core-first-slice.md) begins implementation on the
planned branch: partial CaeGlobals/CaeMesh .NET 10 libraries, an executable
mapping host and 25 mapping checks (including all 13 upstream vectors), plus
nine CLI checks. Existing algorithms are source-linked unchanged. Only
CaeException moves into a separate source file, included in the original net48
project. The shared slice also compiles/runs geometry/error/type-identity checks
under the legacy Windows CLR. [Report](reports/shared-core-first-slice.md).

Mac ARM64/Linux ARM64/native Linux x64 runs of the new library remain next;
a complementary Linux x64 CI job is prepared, not executed. The Windows C++17
gap is now closed for the synthetic kernel: pinned portable LLVM-MinGW 20261006
(Clang 23.1.3) passes 13 vectors, 17 native/seven managed checks and all 1,728
count comparisons, with defaults and explicit contraction off. Production
compiler policy is unchanged. Sandbox hardlink, full histories/CAD/VTK and release gates remain explicit.
They are not represented as passing and do not hold up this approved slice.
The maintainer now authorizes commit/push of this work and immediate MacBook
handoff (task 0014). Publication status and exact commits are recorded in that
task/handoff; do not infer a remote push from the earlier implementation checks.
No frontend/serializer selection or integration. Older sections below retain
historical checkpoints and authorization.

## Current Windows continuation — 2026-10-16

Maintainer authorized the planned Windows work on research/native-feasibility.
[Task 0011](tasks/0011-windows-reference-validation.md) now has a controlled
native cube/import-history checkpoint and
[retained evidence](reports/windows-reference-validation.md). Original 2.6.0
reference hashes match CrossOver. Save/reopen, undo/redo and regenerated exports
pass 30 explicit semantic checks and three negative controls. Legacy regeneration
prints success but exits 0xFFFFFFFF; that process contract remains a limitation.

Both core pins and data pass on native Windows x64 and exactly match Mac portable
observations. Six evidence regressions, three PMX scalar controls and four shell
fixtures/two controls pass. The exact bundled CalculiX 2.22 passes seven native
analytical checks plus its negative control. PMX record inspections pass; its
24-test suite has 23 passes and one sandbox hardlink-creation error. C++17 is
absent, so structured-kernel Windows execution remains open. Broader history,
private-model/job policy, saved-results, CAD and VTK/DPI gates remain pending.

Repository-local LF configuration/source-byte restoration and two measured
research-test portability fixes are recorded. New controlled export/native
solver checkers and evidence remain uncommitted; no production source/project,
dependency, GUI/schema policy, integration or publication change. The following
2026-10-15 sections retain historical state.

Updated: 2026-10-15 (Europe/Belgrade). **Phase 0 and bounded tasks 0002–0010
complete within their recorded scopes. New tasks 0004–0007 add native-source/
build-boundary audit, structured kernel execution, native VTK smoke evidence
and shell-junction fixtures. PMX inspection now also passes Linux ARM64;
structured-kernel/rendering execution remains Mac ARM64 only. Earlier core/data
probes passed Linux x64 gates. Windows compatibility, matching native sources,
full application/UI/platform parity and production integration remain open.
Actual legacy PMX inventory and a user-confirmed CrossOver read/save/reopen cycle
are now available; native Windows validation remains pending.**

## Current continuation — local preparation and hosted verification complete

Maintainer now explicitly authorizes commit/push of completed research to origin
(task 0012), superseding earlier uncommitted-only instructions for this one
publication. [Local completion report](reports/local-preparation-completion.md):

- Selected PMX shallow records: 27/29 types match; job execution settings and a
  new keyword-override member differ. No full semantic/history equivalence.
- Linux ARM64 GCC -O2 fails right_45_45 (12/13). Explicit contraction-off and
  -O0 pass 13/13. Default failure is retained; production policy remains open.
  With the explicit control the public research suite passes, matching Mac.
- Nine VTK provenance/mixed-order/lifecycle checks pass on native Mac; no real
  pointer/DPI/platform or leak claim. Seven analytical checks pass using the
  exact bundled CalculiX 2.22 through CrossOver; no native Mac solve claim.
- Mac data/structured checks and native/header audit rerun successfully within
  their scopes; matching custom source recovery remains blocked on availability.

Research commit **24c790ac** is published on origin/research/native-feasibility.
Push pipeline **#2951491552/job #17205619186 passed** on native AMD EPYC 9B45
x64. All public research checks pass with compiler defaults; six downloaded
artifacts independently checked. [Hosted evidence](reports/research-linux-x64.md).
Closing evidence publication completes task 0012 and ends this commit/push
exception; future agent commits/pushes require a new instruction. Task 0011 is
the next Windows continuation. Earlier milestone paragraphs
below retain their historical authorization/publication state; this section
defines the current continuation. Production sources/x/main remain unchanged.

## Repository

`origin` is the maintainer's PrePoMax-X fork; `upstream` is official PrePoMax. Last synchronization on 2026-10-13 found zero new commits. Local `master` remains equivalent to the recorded upstream ref at `de8f73032a72746e3d6d9afd53d9fbd289eb310a`; no new fetch or upstream write was performed for the Podman adjustment.

`x/main` contains reviewed Phase 0 records at `c840aceb8cc007e1a151b5e35fed2f413f6451e4`; implementation commit `92a491cd` remains on `feature/core-feasibility`. The maintainer pushed it and reported a failed pipeline. The agent has not pushed or merged feature implementation. The maintainer committed and pushed the complete Podman/CI tooling and evidence as `822bae2528be6e38df6d472fc979c36b9f3e4d27` (commit title: Phase 0 verification). The maintainer authorized the agent to commit/push the closing evidence and next bounded probe/investigation during the current 2026-10-14 continuation. Normal maintainer workflow resumes afterward; x/main integration remains separately gated.

Naming remains PrePoMax-X and X/x throughout. At the last release check (2026-10-13), official download was 3.0.0 RC1; stable 2.6.0 is a reference branch, not a tag. Release availability was not rechecked for this tooling task. Phase 0 history/evidence is preserved in [initial audit](reports/initial-audit.md).

## Actual verification

The new experiment links seven unchanged upstream source files: five STL implementation files, Vec3D and FeNode. The net10.0 build has zero package or original-project references, zero errors and three retained upstream-source warnings. Original engineering/application source and project files are unchanged.

On native macOS ARM64, both the audit baseline and isolated stable 2.6.0 replay passed **23 analytical/STL checks and two CLI process contracts each**. Cube inspection returns 12 triangles and bounds [0,0,0]–[1,1,1]. Source/fixture hashes and build/runtime evidence are in [core report](reports/core-feasibility.md) and its JSON records. The two commits have identical selected source; replay mechanics are verified, adaptation to changed source is not.

Linux: maintainer installed Podman/Podman Desktop; an applehv ARM64 VM was initialized and local tests now use Podman. Later on 2026-10-14 the maintainer authorized complementary GitLab native Linux x64 CI preparation. Both pinned revisions pass **23 analytical/STL checks plus two CLI contracts each** on Linux ARM64, with portable observations matching the macOS records. The recipe, runner and [Podman verification report](reports/podman-verification.md) retain architecture/image/runtime/source evidence. **Task 0002's native Linux x64 gate passed on 2026-10-14:** manual GitLab pipeline #2947482796/job #17176590675 at feature commit 822bae25, hosted amd64 runner on an Intel Xeon CPU, SDK 10.0.402/.NET 10.0.13. Both pinned revisions pass 23 checks plus two CLI contracts each and exactly match Mac portable observations; six comparison regressions pass. Downloaded JSON, tooling/reference hashes and runner/image/CPU provenance were independently checked and retained in [native x64 report](reports/gitlab-linux-x64.md). Windows/reference comparisons, whole-core, PMX, Controller, VTK, CAD/meshing and solver execution remain untested here.

Cached-image ARM64 reruns pass. The supplemental Linux amd64 image builds, but .NET/MSBuild crashes under the existing QEMU route before tests; a structured failure report is retained. No translated x64 pass is claimed. Podman's VM was stopped cleanly after verification; its machine and image cache remain installed.

Existing Phase 0 results remain: 37 offline runner tests, two API/source audits and nine Git sync safety tests passed; original Windows solution build failed on Mac due to missing VC/net48 targets. Those are historical results, not rerun as part of the bounded probe.

## Scope and next gate

**Next session: native Windows is expected to be available.** Read the
[Windows handoff](handoffs/windows-next-session.md) and prepared
[task 0011](tasks/0011-windows-reference-validation.md) before work. Use the
research/native-feasibility branch containing task 0012; verify its publication
status rather than starting from the default branch. Begin with pinned
original-app cube/definitions/history capture, then
portable probes. No Windows result is claimed yet. Maintainer corrected the
required targets to **Windows x64, Linux x64, Linux ARM64 and Apple M-series
macOS ARM64**; “x86” means x64. Intel Macs are excluded, Linux ARM64 required.

2026-10-15: [task 0010](tasks/0010-pmx-linux-verification.md) is complete.
All 24 synthetic PMX tests pass in the cached offline Linux ARM64 container;
both private reference inventories exactly match Mac portable observations.
Input hashes unchanged; runtime assembly addition is separately guarded, no
payload assemblies loaded. Startup/initial comparison diagnostics are retained;
the VM stopped successfully. This new probe still needs native Linux x64/Windows
execution. [Evidence](reports/pmx-linux-verification.md) and
[preparation exit gates](reports/preparation-exit-gates.md) define the next bounded
work: semantic project/history snapshots, matching native-source recovery,
interactive rendering and a pinned analytical solve/CAD shell-junction baseline.
Tasks 0004–0010 remain uncommitted; no production change, push or integration.

2026-10-15: [task 0008](tasks/0008-pmx-record-inspection.md) and
[task 0009](tasks/0009-crossover-reference.md) are complete within bounded scopes.
Supplied header is **PrePoMax v2.5.1 dev**, 1,638 records/215 types decoded on
native Mac without application assemblies/BinaryFormatter. Twenty-four synthetic
tests pass. Input unchanged/outside Git. [Schema proposal](proposals/portable-document-schema.md)
records openness to a versioned cross-platform format; production stays undecided.

CrossOver 26.2 now has dedicated bottle **PrePoMax-X-reference-2.6**, official
2.6.0 portable bundle and persistent reference copies. Human confirmed model
display, separate Save As and model/results display after reopening. Custom
model/mesh and result mesh/node-lookup blocks match exactly; four result fields
preserve original bytes with the documented datatype Int32 insertion. Opaque
history trailer matches. NRBF member/type changes need semantic/job-field review.
This is supplementary original-application evidence, not native platform/numerical
parity. No meshing/solver/regeneration ran. See [PMX evidence](reports/pmx-record-inspection.md)
and [CrossOver instructions](reports/crossover-reference.md). Tasks 0004–0009
remain uncommitted on research/native-feasibility; no pushes/integration.

Task 0007's [shell-junction fixture preparation](reports/shell-junction-fixtures.md)
is complete: four hand-authored S4 inputs, geometry/intent manifest and two
checker regressions. Connected, coincident-disconnected, unsplit-plate and gap
contracts are explicit. They are not CAD, live mesher or Windows reference files.
All new task 0004–0007 work is uncommitted on research/native-feasibility; F001
remains Proposed. Do not infer implementation or commit/push authorization.

Task 0006's [native VTK smoke experiment](reports/vtk-native-smoke.md) is complete:
14 synthetic geometry/rendering/ID-selection checks pass on Mac ARM64 with an
isolated pinned Python VTK 9.5.2 wheel. Render/deformation/removal images inspected.
Programmatic cell/point/rectangle picks return expected FEM IDs; clipping drops
global-ID arrays. Genuine UI/DPI interaction, Windows/platform rendering parity
and frontend/binding selection remain open. Original vtkControl/ActiViz unchanged.

Task 0005's [structured meshing experiment](reports/structured-meshing-feasibility.md)
is complete on Mac ARM64: 13 original C++ vector cases, 17 independent native
checks and seven unchanged C# count/grid checks pass; 1,728 count cases match
across languages. Full C# Mapping reaches an ExceptionTools/MessageBoxes compile
boundary. No production sources were changed; full CAD meshing and F001 remain
pending. New-probe Linux/Windows execution has not run.

Task 0004's [native feasibility audit](reports/native-feasibility.md) is complete
on `research/native-feasibility`, under the maintainer's 2026-10-14 authorization
to progress through bounded pre-Windows steps. Gmsh C and plain C++/Q-Morph
declarations compile on Mac ARM64; original C++/CLI wrapper fails at msclr.
Matching custom source recovery is still open, including inaccessible patched
Gmsh, external NetGenMesher/nglib and QuadWild forks, and QuadMesher implementation.
Forty binary/archive hashes and a QuadWild checksum discrepancy are recorded.
The completed audit is uncommitted; no native CAD engine or mesher ran.

Maintainer input recorded on 2026-10-14: [F001, automatic shell-junction
connectivity](features/F001-automatic-shell-connectivity.md), starting with a
shell T-profile on a plate and reducing manual compound-part preparation.
Status is Proposed; priority, connection policy and implementation remain
unset. See the [feature register](features/README.md). Windows reference capture
will be undertaken later when the maintainer returns to the Windows machine;
no new PMX/history or meshing fixture has been captured.

[Task 0002](tasks/0002-core-feasibility.md) remains bounded. Local Podman tests require no publication. Root/experiment GitLab CI YAML is restored under the later authorization, limited to relevant pushes or manual web runs on `feature/core-feasibility`. The new `run-ci.py` executes both pinned probes with Linux/X64 assertions, compares the same portable observations as Podman, and retains JSON diagnostics plus selected non-secret CI identifiers. Local macOS ARM64 rehearsal and native Linux x64 hosted execution passed both revisions. The manual web pipeline executed the configuration successfully; a separate semantic lint command was not run. Subsequent push pipeline #2947646455 at 0020d0d8 passed, verifying push-trigger execution as well. See [CI preparation](reports/gitlab-verification.md). Hosted settings were not changed and the historical failed pipeline was not deleted. After the maintainer signed in, authenticated inspection confirmed pipeline #2944154347 failed before job creation because GitLab required identity verification: zero jobs, no probe execution. Instance runners are enabled; runner #54907241 with tag `saas-linux-small-amd64` is online/active; personal namespace usage shows 0/400 compute minutes for October 2026. Successful execution of the new pipeline confirms the earlier identity restriction no longer blocks this run. This is an account eligibility failure, not evidence of a source/build/test failure or malformed YAML.

Task 0002 is complete within its seven-file scope. Review the newly retained native x64 evidence and uncommitted handoff updates. Feature implementation remains on `feature/core-feasibility`; integrating it into `x/main` and beginning a further bounded implementation task require authorization. The maintainer has now explicitly authorized agent commits/origin pushes for this continuation, covering the closing evidence and next bounded dependency/probe/PMX identity investigation. Windows reference access is available; capture still needs to occur.

Task 0003 is published on `feature/core-data-feasibility` at da264eef from evidence commit 0020d0d8. Its six-file unchanged Matrix/metadata/scaling/FRD-stream probe passes 30 checks plus two CLI contracts on Mac ARM64 and native GitLab Linux x64, with exactly matching observations. Push pipeline #2947730759/job #17178539405 also reran both original probes and six regressions successfully. Downloaded data/core JSON, actual native runner/image/CPU provenance and independent hash/comparison checks are retained. GeometryTools hits a measured WinForms compile boundary while Matrix builds unchanged. Source-only PMX identity inventory and Windows capture instructions are prepared; actual Windows payload graphs/round-trip remain pending. See [task 0003](tasks/0003-core-data-feasibility.md) and [data report](reports/core-data-feasibility.md). PyQt/Python VTK + shared C# and a C# frontend remain production candidates; no GUI/binding/serializer commitment made. Native-source recovery remains an independent parity prerequisite. [Roadmap](ROADMAP.md), [decision register](DECISIONS.md).

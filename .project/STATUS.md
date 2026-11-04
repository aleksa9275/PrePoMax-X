# Project status

## Current — task 0052: original L-bracket CAD reference

The pinned Windows 3.0.0 executable under CrossOver passed the L-bracket
STEP geometry checks. Repeat captures and direct NetGenMesher replays
matched byte for byte. The released Netgen executable matches the checkout,
with `nglib.dll` the sole difference among 38 bundled executable/DLL files.
Matching native CAD source and execution remain open. The task 0051 installer
was removed and its verification and rebuild archive were retained.
[Task record](tasks/0052-l-bracket-cad-reference.md) ·
[Verification](reports/l-bracket-cad-reference.md).

## Current — task 0051: Ubuntu desktop installer

The native desktop archive now wraps as an internal Ubuntu 24.04 .deb for
ARM64 and x64. A fresh ARM64 container installed through APT and ran the
INP and checked PMX workflows as an ordinary user. Remove, reinstall and
purge preserved all tested project and job files. Pipeline #3028114125
passed all six automatic jobs, including the installed x64 INP workflow
and APT lifecycle. A Mac parity follow-up
can start with the tracked L-bracket STEP reference and CAD source recovery.
[Task record](tasks/0051-ubuntu-desktop-deb.md) ·
[Verification](reports/ubuntu-desktop-deb.md).

## Current — task 0050: native Linux desktop archive

The shared desktop and checked static PMX workflow now build as a native Linux
archive. The extracted ARM64 archive runs the shipped INP example and the
retained PMX edit/save/reopen/solve workflow under X11 in a separate Ubuntu
runtime container. The saved PMX, executed deck and decoded fields match the
task 0049 reference. Exact-commit GitLab pipeline #3028048004 passed all six
automatic jobs, including x64 packaging and the extracted INP workflow.
Physical desktop and distro package acceptance remain open; a Debian-family
install/uninstall proof is the next packaging increment.
[Task record](tasks/0050-linux-desktop-preview.md) ·
[Verification](reports/linux-desktop-preview.md).

## Current — task 0049: reopened PMX native solve

The opt-in macOS preview displays a supported static PMX in the model tree and
viewport and runs it through the native CalculiX job. The checked PMX deck
builder preserves density, step frequency and field outputs. Jobs retain the
reopened project's hash and frozen inputs. PMX edits use the two-value Save As
dialog. The native Linux desktop package is the next delivery increment.
[Task record](tasks/0049-static-pmx-native-solve.md) ·
[Verification](reports/static-pmx-native-solve.md).

## Current — task 0048: desktop static PMX

The opt-in macOS ARM64 preview opens, edits and saves a supported result-free
static-solid PMX 3.0.0 project. The desktop validates Young's modulus and axial
force edits, publishes a new PMX, and leaves the source file untouched. The
saved fixture matches the file previously reopened and resaved by the official
Windows 3.0.0 executable through CrossOver. Task 0048 is separate from the INP
viewport and job path. General project, results and command-history persistence,
full 3.0.0 parity, native Linux desktop packaging and release gates remain open.
[Task record](tasks/0048-desktop-static-pmx.md) ·
[Verification](reports/desktop-static-pmx.md).

The maintainer will run their workflow when the fully operational 3.0.0 parity
candidate is ready. Notify them when Developer ID and notarization require their
involvement.

## Current — task 0047: session named set authoring

The desktop now creates node and element sets from original IDs or a picked
ID, validates through the original C# reader, and freezes them into jobs.
The source macOS desktop and native cube solve pass. The local ARM64 DMG
passed mounted and copied-app verification. The packaged set and solve
workflow passes through both viewports. Task 0048 supersedes the local image.
[Task 0047 report](reports/session-named-set-authoring.md).
The task 0045 cleanup removed 17 temporary directories while preserving the
reference archive, fixtures, and receipts. General PMX compatibility remains
open. [Cleanup receipt](reports/pmx-3.0.0-reference/cleanup-2026-11-04.json).

## Current — task 0045: original PMX compatibility

D057 selects full original .pmx compatibility. The first milestone is
bidirectional original-Windows readback for a static-solid model, followed by
broader coverage against the verified 3.0.0 baseline. The prior synthetic
exchange proof verified input and deck preservation on macOS. General PMX
model reconstruction and writing remain pending. The official
3.0.0 archive is pinned by hash. Three controlled PMX captures through CrossOver
include a reopened static-solid model and one reopened result. Exact upstream
source correspondence and a controlled nonempty history fixture are pending.
The portable project probe now binds the original binary mesh to its graph,
recovers units, named sets, parts and the captured static definitions, and
matches all 104 raw embedded result values against the source FRD by node ID.
Mac and Linux ARM64 receipts match byte for byte. A real original-app
material/load edit now has a reopened deck and numerical reference for the
future writer proof. The history reader matches 96 raw DAT series and
recovers the official Profile command order and cursor. The original app
confirmed the two saved Profile result series through CrossOver. The two
pinned static captures now reconstruct through original engineering objects
and reproduce the official-export native Mac solver fields. The controlled
portable writer generates the same edited PMX bytes on Mac and Linux ARM64.
The original Windows app under CrossOver reopens and resaves it, and its
export reproduces the official edited reference deck and solver fields. The
writer now handles variable-length decimal edits in both pinned graph layouts
by identifying the three string records without fixed offsets. Both generated
files pass original-app readback for the independent decimal reference. The
writer now discovers the three edit records through the model graph and
handles a third pinned project with a duplicated node set and new record IDs.
The writer now rejects shared target equation containers and string records
while reproducing the verified output hashes for those inputs. An opt-in
shape-checked workflow now edits, reopens and rebuilds a deck from an unlisted
result-free static-solid PMX. Mac and Linux ARM64 receipts match, and the
official Windows executable under CrossOver resaves the edit with matching
native Mac solver fields. Task 0045 remains open for general FeModel
reconstruction, visualization, command replay and broader bidirectional
original Windows interoperability. Task 0048 wraps the verified subset in the
macOS desktop.
[Compatibility plan](reports/supported-project-persistence.md).

## Current — task 0046: completed-preview storage retention

Maintainer reports the task 0044 preview seems to work and requests cleanup before
the next task. [Task 0046 plan/outcome](reports/storage-cleanup.md) prunes reviewed
ignored package/test/cache payloads while preserving tracked source/evidence,
small build records, all jobs and useful shared solver/runtime/dependency inputs.
Earlier keep-DMG instructions are superseded by D056. Old local app/DMG/host links
below describe historical verified payloads; rebuild before reuse after pruning.
User installed app/state/private models are outside this cleanup. This is storage
maintenance, not new application/platform/release acceptance. The task 0045
proof follows this cleanup. Both correctness failures/tetra gate and all release gates stay.

Completed: 74 generated directories removed; observed **41.98 GiB** free-space
gain, **230 GiB available**. All 292 retained evidence files and nine pinned
solver/runtime hashes verify; shared tool/cache inputs and Mac build recipe remain.

## Current — task 0044: editable static solid workflow

Model tree and Configure / Run analysis now edit explicit units, original
isotropic elastic materials/solid sections, displacement supports, forces per
node, static increments and requested history sets. Named-set inventory comes
from the original INP reader; original C# `validate-static` builds/validates the
deck without a solver. Jobs freeze input mesh/definition into a new workspace,
then use the existing original solve/cancel/status/FRD path. Accepted edits remain
in the tree after results load. Stale validation clears on edit; unsaved-session
discard prompts protect edits. No engineering parser/math or project format is
reimplemented in Python.

Seven real-Qt/original-C# editor checks, four process/snapshot/cancel/failure
checks, eight build checks and affected current-source Analysis/Execution pass.
The first packaged real-editor comparison passes 18 GUI checks and 15 deck/
numerical/control checks: E=105 GPa and 50 N/node reach the executed deck, giving
200 MPa stress and fourfold displacement with unchanged absolute tolerances.
[Final artifact, actual verification and publication](reports/editable-solid-workflow.md).
Final configuration coverage found/fixed B004: histories-off runs must not
require nonempty DAT, while requested DAT and FRD/STA remain strict. Native Mac
history-on/off workflow passes 15 checks and the copied edited model's FRD fields
match exactly with histories off. The current DMG passes both editor viewport
proofs. A null-capture incident is retained; strict native retry passes after the
maintainer confirmed the Mac was unlocked/awake. No security setting changed.
Implementation 0583a2bd and B004 repair **921b24a6** are published/remote-verified.
Final exact-commit pipeline **3022312183 passes all six automatic Linux x64 jobs**,
including 15 native history-on/off checks; compatibility stays manual. Hosted
archives were not downloaded. Closing publication is evidence/documents only.

Scope: imported mesh named sets and the existing bounded static-solid definition.
No additional/picked-set authoring, project save/reopen, full PMX/history/CAD/
meshing or production frontend choice. Both prior tested DMGs, both correctness
failures/tetra gate and all release requirements remain. Next: explicit supported
save/reopen boundary and persistence decision.

## Current — task 0043: native viewport boundary

Maintainer selects **PrePoMax 3.0.0 parity**, followed by future upstream release
tracking and open-source Mac/Linux maintenance independent of upstream adoption.
[Version/coverage record](PARITY.md), D054. Exact stable-release correspondence
remains pending; no source baseline/mirror change was made.

Opt-in `--viewport native-cocoa` renders through a VTK-owned child NSView without
frame copying, with Qt input forwarding and Retina coordinates. The actual DMG's
copied app passes 11 solve/render checks, 7 analytical checks/control, 12 native
event/display/lifecycle/larger-mesh checks and 11 default-bridge checks. Eight build
and three process checks pass. [Report/artifact/comparison](reports/native-viewport-boundary.md).
No speed win, C# native-host execution or production frontend decision is claimed.
Original task 0042 DMG remains byte-identical. Implementation **7514c88c** is
remote-verified; exact-commit pipeline **3022061388 passes all six automatic
Linux x64 jobs** (compatibility manual). Hosted archives were not downloaded here.
Next: editable solid model tree/material/support/load workflow; supported save/
reopen follows with an explicit persistence decision. Both correctness failures/
tetra gate and all full-parity/four-target/release requirements remain.

Agent continuation: [current handoff](handoffs/native-macos-next-session.md)
records the verified artifact, published implementation, pending gates and next
bounded task. No feature implementation is left mid-change.

## Current — task 0042: local Mac solver-controls DMG

Maintainer requests an unnotarized local DMG and explicitly wants desktop solver
controls first. Common QProcess controls invoke the original C# static-deck/job/
results services with start/cancel/status/output and automatic FRD loading.
The explicit native CPU profile/runtime closure is relocated into the app.
Implementation **b6ec65d7** is remote-verified; exact-commit pipeline **3020068825
passes all six automatic Linux x64 jobs** (compatibility manual). The local final
DMG identifies that clean commit and passes mounted/copy/eject/signature/hash
checks. Copied-app native cube: eleven GUI checks, seven original analytical
checks/control; actual packaged-host cancellation/failure/tamper checks pass.
[Artifact/evidence/scope](reports/local-macos-dmg.md).

The **248.2 MiB local DMG** is in
`X/Build/artifacts/task0042-macos-dmg/dist/PrePoMax-X-Preview-arm64.dmg`.
[Full uninstall/reset guide](../X/Desktop/UNINSTALL-macos.md) is included in it.
Maintainer reports the local preview test went well and as expected (3 November
2026); a separate cleanup/clean-OS test is not inferred. Next: the proposed
[bounded viewport binding](tasks/0043-native-viewport-boundary.md), then an editable
solid workflow and supported save/reopen. No Developer-ID/notarization/clean-host or
full product/release acceptance; both known failures/tetra gate and B002 remain.
Apple container is Linux-only, not a Mac GUI test environment.

## Current — task 0041: shared target builds and native Linux CPU workflow

[Shared build entry](../X/Build/README.md) publishes the same mesh/results/job
hosts for all four RIDs, using one catalog and target-native helpers. The Mac
package command remains a wrapper. Mac hosts/solver/common cube workflow and
packaged viewport pass; Windows x64/Linux ARM64 cross-publication succeeds with
execution explicitly pending. Seven build-boundary controls pass.
[Evidence/scope](reports/shared-target-builds.md).

Implementation **a893005c** is published/remote-verified. Exact-commit pipeline
**3019959774 passes all five automatic native Linux x64 jobs**; compatibility
stays manual. Downloaded artifacts identify clean source, matching native source
manifests/recipe/catalog and actual ELF/native solve. The twelve common cube
checks and rejection control pass; four FRD fields and 96 DAT histories compare
with Mac within recorded bounds. This is Ubuntu compute evidence, not a
Debian/Fedora/Arch desktop or installer pass.

CI-only **0411ae23** separates the slower source build into an affected-input job;
GUI-only changes retain the short checks. Pipeline **3019992604 passes all six
automatic jobs**.
No native Windows/Linux ARM64 execution or release gate closure is claimed.
Both known failures/tetra gate remain. Next: bounded native viewport binding,
then Mac model/job/results workflow and relocatable signed preview packaging.

## Current — task 0040: pipeline regression fixed and hosted-verified

Signed-in GitLab inspection finds pipeline **3019186769**, one failed job:
**shared-core-linux-x64 / 17675531644**. Analysis/execution/results/research pass;
compatibility is manual. Downloaded diagnostics expose B003: the previous B001
fix changed exported block name CUBE to null. Missing package warnings follow
the earlier verifier failure. [Diagnosis/evidence](reports/core-pipeline-regression.md).

The shared writer now preserves inline block names and emits explicit set members
only where not already inline. Core CLI equality remains strict. Current Mac
Core/Analysis pass (69 mesh / 333 accepted analysis checks); native solve again
passes twelve checks and its negative control without duplicate stresses.
Repair **f4e388a5** is published/remote-verified. Exact-commit pipeline
**3019257012 passes all five automatic native Linux x64 jobs**; compatibility
remains manual. Downloaded Core evidence matches Mac source/tools, retains CUBE
and passes 69 mesh checks; actual development ZIP bytes/125 entries independently
verify against hosted package reports. Task 0040 is complete; next is the shared
target/build entry and Mac workflow under the revised plan. Both existing
correctness failures/tetra gate and all other platform/release gates remain.

## Current — task 0039: macOS-first, shared-source delivery plan

Maintainer reports a failed GitLab pipeline and clarifies that macOS delivery
speed must retain Windows/Linux awareness and the same source per target.
[Revised plan](proposals/accelerated-native-delivery.md): four RID builds from one
application/engineering tree, small native/OS build helpers and Debian/Fedora/Arch
package wrappers. Mac preview is the critical path; Linux x64 engineering feedback
continues now, other-target compilation comes early, full native UI/install tests
come at checkpoints. Linux ARM64 remains required; Arch Linux ARM is explicit.

First engineering item: obtain the exact failed job/commit/log and fix its owning
layer; no cause or hosted pass is known. The report was requested; no CI/code
changes are guessed from a failure notification. Independent Mac work need not
wait for unavailable runner/access infrastructure. [Task 0039](tasks/0039-shared-source-delivery-plan.md)
is documentation only. Existing native Mac cube/viewport evidence remains bounded;
no new frontend/default solver/format choice or platform acceptance is implied.
Both known correctness failures/tetra gate and all final release gates remain.

## Current — tasks 0037/0038: native solve and packaged desktop candidate

Original definitions → native Mac ARM64 CalculiX 2.22/SPOOLES → original FRD/DAT/
monitor readers now passes the analytical cube: twelve workflow checks plus the
altered-displacement control. [Evidence/limits](reports/native-cpu-workflow.md).
B001 duplicate set emission is fixed; current analysis **332** checks, execution
**49** checks/13 rejection controls and ten replay/nine analysis guards pass.
Both pre-existing correctness failures/tetra gate remain explicit.

A local **.app** bundles Python/Qt/VTK and self-contained C# readers. It displays
the native-generated results and nonsequential IDs with external Python/dotnet
absent from PATH; 10/8 candidate checks pass. [Evidence/artifact](reports/native-desktop-preview.md).
Direct Qt embedding has B002; the working native-VTK frame-copy bridge remains a
candidate with performance/input/DPI limits. No frontend/default backend/format
decision. This does not complete milestone B or a clean-machine installer.

The earlier tooling/plan/review checkpoint **66e3ca0f** and new implementation
checkpoint **384edea2** are published and independently verified on
origin/research/native-feasibility. [Publication record](reports/native-delivery-publication.md).
The master mirror is unchanged. Hosted CI is unverified: available GitLab browser is
unauthenticated/404 and glab is unavailable. Do not claim a hosted pass.

Next: resolve the bounded native widget/C# binding comparison, integrate tree/job/
results controls and save/reopen into a scoped preview; port the pinned solver
recipe and common solid/shell workflow to native Linux workers. Runtime relocation,
PaStiX/performance, native Windows/net48/RC2, CAD/full graph, four-target/signing/
installer/Homebrew and complete corresponding-source gates remain.

All older local/uncommitted descriptions below are historical for published work.

## Current — task 0036: first delivery-speed increment implemented

[Profiles and commands](../X/Checks/README.md) now run current-source checks by
selected area or explicit historical compatibility. All four fast suites pass
native Mac ARM64 in 43.36 s; results compatibility passes all three pins, and seven
orchestration regressions pass. Both known correctness failures/tetra gate remain.
Each run retains source identity, patch/changed code, logs and verifier reports.
[Task/evidence](tasks/0036-development-check-profiles.md).

CI is prepared for four current-source verifiers instead of twelve, package
archive caching, documentation-change skipping and optional manual compatibility.
It is not published/hosted-verified. No production source/solver/frontend policy
changes. Next: native-VTK host/package proof and native CPU solver build. All work
is local/uncommitted; final platform/release requirements remain.

## Current — 2026-11-02 accelerated delivery plan

[Task 0035](tasks/0035-accelerated-delivery-plan.md) completes the requested
[short conclusions](reports/prepomac-evaluation.md) and
[delivery plan](proposals/accelerated-native-delivery.md). Native installers and
a vertical desktop workflow take priority; CalculiX remains primary, Code_Aster/
GPU/new features are deferred. Development uses affected/current-source checks;
historical/full-platform coverage moves to relevant integrations/candidates.
Reproducible bug manifests and final correctness/release requirements stay.

Next implementation: fast versus compatibility verification profiles with shared
caching, then a bounded native-VTK host/installer proof and native SPOOLES build.
The frontend/default format/solver profile remain explicit decisions. Existing
CI YAML and application code are unchanged. Records are local/uncommitted.

## Current — 2026-11-02 detailed PrePoMac evaluation

[Task 0034](tasks/0034-prepomac-evaluation.md) completes the maintainer-requested
[solver/UI/Linux/VM comparison](reports/prepomac-evaluation.md) at PrePoMac
fb5a89db / release v3.0-mac.4. Actual ZIP checksum, ARM64 CalculiX 2.23 binary
metadata, exact-commit Mac build/release API status and 40 reviewed source hashes
are retained. Bounded extracted methods run on Mac; analytical formula/syntax/
literal-case checks pass. Local Linux execution failed on Podman forwarding;
the VM was stopped, and no Linux/application/numerical/performance pass is claimed.

PrePoMac supplies a broad working desktop adaptation, with WinForms/Avalonia
compatibility and custom VTK/OpenGL behavior. Its Code_Aster adapter is a limited
linear-static translator, forces amd64 Docker, downgrades several element orders,
can omit/change model content, and does not establish full solver parity or VM
speed. Its native Mac binary lacks PaStiX/PARDISO; that packaging does not establish
a general SPOOLES-only CalculiX restriction. Maintainer accepts considering a
Linux VM solver worker when performance warrants it; no production route is
selected. Recommendations retain shared original engineering/native-VTK direction
and selective reuse. All existing correctness/release gates remain; research
records only, uncommitted, no integration/contact/publication.

## Current — 2026-11-02 continuation and upstream review

Maintainer resumes and requests status/upstream updates. [Task 0033](tasks/0033-continuation-upstream-review.md)
and [review evidence](reports/upstream-2026-11-02.md) confirm published research
HEAD d0e73e63 and origin/master f6273e39. Upstream master is now 2a25db82
(20 October), still RC2: two new fixes, but divergent from the retained mirror
(nine old-only/two new-only commits). Old composite history is retained on the
new upstream Composites branch f6080786. Normal sync refuses this divergence;
no local mirror/research branch integration or push occurred. Tracking refs were
fetched; preserve exact replay pins and review branch separation before syncing.

New community PrePoMac reports native Mac desktop/experimental Linux support with
different rendering/meshing/backend choices. It warrants source/fixture assessment;
it has not been locally validated or adopted. Prior bounded implementation/test
evidence remains the checkpoint below; no new solver/full-desktop acceptance.
Both correctness failures/tetra gate and all remaining release requirements stay.
This review changes records only, left uncommitted under normal publication policy.

## Current — tasks 0030/0031 published; task 0032 closes evidence

2026-10-18: implementation **62c7de1b** is independently verified on origin
research/native-feasibility. Exact-commit pipeline **#2960686368 passes all five
native Linux x64 jobs**. Three actual hosted results previews identify clean SHA,
78 checks/nine CLI controls per pin and matching ten source/tool/dependency/FRD/
DAT/test groups against both ARM64 hosts. Archive retrieval failed; semantic
preview verification is retained without claiming raw-byte/archive verification.
[Publication and next work](reports/results-publication.md). Closing changes are
records/evidence only; task 0032 ends here and normal publication policy resumes.
Both correctness failures/tetra gate and all native solver/Windows/net48/RC2/
full-graph/persistence/UI/CAD/source/four-target/installers/Homebrew gates remain.
Earlier uncommitted wording is historical after this publication.

## Current — task 0031 DAT inspection / 0032 publication

2026-10-18: maintainer authorizes next bounded task and committing/pushing current
work. Original DAT block/numeric/component decoding and history entries now power
bounded static-shaped inspect-dat histories, retaining step/increment/time and
node/element/integration-point identities. Full net48 orchestration/persistence
remain mechanically preserved. DAT parsing cannot establish job completion.
[Scope/tests/evidence](reports/portable-dat-histories.md), [actual publication/CI](reports/results-publication.md).
Publish tasks 0030/0031 under task 0032; earlier uncommitted wording is historical
after remote verification. Both correctness failures/tetra gate and all native
solver/Windows/net48/RC2/full-graph/persistence/UI/CAD/source/four-target/installer
gates remain. No backend/default/precision/GPU/frontend/format decision.

## Current — task 0030 portable original FRD fields complete locally

2026-10-18: maintainer resumes after reset. Original FRD/Field/FieldData/
FieldComponent and invariant helpers now support a callable bounded C3D8 static
snapshot and inspect-frd CLI, preserving original ownership and legacy net48
orchestration. Current/RC2/post-RC2 each pass 39 results checks/five CLI controls
and rerun 331 accepted analysis checks on Mac/Linux ARM64. Six results, nine
analysis, four job and ten replay source guards pass. Source/tool/package/field/
CLI outcomes match across hosts; both known correctness failures/tetra gate
remain. [Report/evidence/limits](reports/portable-frd-fields.md).

No solver executes; no fresh numerical/native Windows/net48/RC2/full workflow
or release acceptance. Full FeResults/part/material graph, DAT histories and
native CPU solver/source recovery remain next. X64 CI is prepared but not run;
all changes stay uncommitted, with no new publication/default/backend/precision/
GPU/frontend/serializer decision. Published checkpoint remains 6c51ced6; closing
pipeline #2960615926 passed. The earlier feature stop is lifted for this local
continuation; normal maintainer publication workflow resumes.

## Current — task 0029 publication and exact-commit evidence verified

2026-10-18: implementation **993f9263** is on origin/research/native-feasibility;
independent remote verification confirms it. Pipeline **#2960594131 passes all
four native Linux x64 jobs**. Downloaded analysis/execution artifacts verify
clean exact-commit HEAD and matching source/tool/dependency/Mac outcomes for
current/RC2/post-RC2: 331 accepted analysis checks and 47 execution/planning
checks, 13 CLI rejection controls each. Both correctness failures remain explicit.
[Publication/evidence/reset handoff](reports/analysis-execution-publication.md).
Closing changes are documentation/evidence only. Stop features until resumed.
Native Windows/net48/RC2/full workflow/native solver and all release gates remain.
Older uncommitted descriptions below are historical after this publication.

## Current — tasks 0028 complete locally / 0029 publication authorized

2026-10-18: maintainer requests one bounded task then commit/push all current work
and stop until resumed after reset. Modern-only CPU planner/CLI calculates 75%
of process-available CPUs, explicit manual total and fair per-job allocation.
Current/RC2/post-RC2 pass 47 execution/monitor/planning checks, two positive plans
and 13 CLI rejection controls each on Mac/Linux ARM64. Tools/sources/outcomes
compare; host counts 18 and 4 yield automatic budgets 13 and 3. No solver launch,
settings migration, running scheduler or reference-thread change. [Evidence](reports/portable-thread-planning.md).

Publication review passes nine analysis/four execution/ten replay guards,
unchanged 1188-file CalculiX source verification, current Mac analysis rerun
(331 accepted checks, both correctness failures retained) and content/whitespace
checks. Task 0029 publishes tasks 0022–0028 normally to origin research only;
[actual SHA/hosted state/reset handoff](reports/analysis-execution-publication.md).
No claim of hosted success until verified. All Windows/net48/RC2/native-solver/
full-workflow/four-target/installer gates remain. Stop features after publication.

## Historical checkpoint — task 0027 solver advice/threads/GPU research complete

2026-10-18: maintainer requests recommendations by analysis, a 75% available-
thread default and NVIDIA/AMD/Apple GPU research. [Report/proposed design](reports/solver-guidance-threads-gpu.md)
documents existing-backend-first advice, conditional MUMPS fallback, automatic
thread budgeting/manual override and concrete GPU distinctions. NVIDIA CUDA
routes exist; SuperLU_DIST HIP is a separate AMD integration candidate; no
reviewed Metal direct-solver route identified. Apple specification 4.1 parsed
locally confirms no double scalar type. Library availability is not integration.
No backend/default/precision settings changed and no new benchmark performed.

Task 0022–0027 changes remain uncommitted; no publication authorized. Native CPU
build/provenance and later regression/scaling comparisons remain necessary.
D042 licensing/functionality criterion, both correctness failures/tetra gate and
all Windows/net48/RC2/four-target/full-workflow/installer gates remain.

## Historical checkpoint — task 0026 PARDISO-free assessment complete

2026-10-18: maintainer rejects machine-bound Panua licensing; a new alternative
is needed only if omitting PARDISO cripples functionality. D042 narrows D041's
complete proprietary-backend requirement. Located the September 2024 `aleksa`
forum discussion leading to Matej's PARDISO default recommendation. Published
observations show both faster PaStiX runs and serious memory/correctness risks;
no universal slowdown or PARDISO-exclusive analysis category is established.
Original 2.22 modal/buckling PaStiX branches can call PARDISO in combined builds.
[Assessment and later comparison scope](reports/without-pardiso-assessment.md).

Recommendation: investigate existing SPOOLES/PaStiX before integrating a new
backend. No default/precision/profile change or numerical tests in this research
increment; own comparisons deferred as requested. Native build provenance,
correctness/capacity and all Windows/net48/RC2/full-workflow/four-target/release
gates remain. Task 0022–0026 changes are uncommitted; no publication authorized.

## Historical policy checkpoint — task 0025 exact solver research complete

2026-10-18: direct archive verification proves RC2 ccx_dynamic.exe is byte-
identical to the official CalculiX 2.22 Windows binary. Its five DLLs match the
prior native Windows reference. No PrePoMax-specific replacement kernel is
established. The official README identifies Rafał Brzegowy and canonical source.
PrePoMax GUI defaults to PARDISO; executable-default cube uses PaStiX. All six
choices pass 7 analytical checks each through the exact Windows program/runtime
in the existing Mac CrossOver bottle. This is not native ARM/full parity.

[Report and concrete recovery route](reports/exact-solver-provenance.md): exact
PaStiX/Scotch source/build/ABI/transitive recipe remains missing; native ARM64
Intel MKL/PARDISO availability is the full-stack blocker. Compatibility/worker
and native-compute routes are distinct unselected options; no backend/default/
numerical policy changes. All task 0022–0025 edits remain uncommitted; research
only in this increment, all existing correctness/release gates retained.

## Current — task 0024 native job boundary/source organization, local and uncommitted

2026-10-18: original CaeJob job/enum ownership and legacy Windows behavior are
mechanically preserved. Modern native process execution, stdout/stderr, actual
exit, deadline/cancellation, descendant cleanup, concurrency and pinned solver
preflight are callable; original STA/CVG monitor data is inspectable. All three
source modes pass 33 new checks/four CLI controls on native Mac/Linux ARM64;
four source guards pass and six-run fingerprints/results match. Linux container
checks use an init reaper. Earlier 331-check analysis source/tool pins are unchanged.

Official CalculiX 2.22 source is recovered under ThirdParty/Sources with original
license and per-file/archive pins (1188 files). Matching native PaStiX/BLAS/patch/
compiler/ABI/runtime provenance remains unproven; **no native numerical solve
or solver substitution occurs**. New hosted x64, native Windows/full net48/RC2
and all correctness/release gates remain. All task 0022–0024 edits are uncommitted.
[Task](tasks/0024-native-job-boundary.md), [evidence/blocker/next work](reports/native-job-boundary.md).

Maintainer requires a clean final repository with all third-party corresponding
source and a public package release branch; [repository map](REPOSITORY_LAYOUT.md)
records additive source/patch/build layout and planned x/release immutable-artifact
publication. No public branch/push is performed here. Continue original FRD/DAT
field import in parallel with matching native-source/build recovery.

## Historical checkpoint — task 0023 complete static analysis deck, local and uncommitted

2026-10-18: original section/BC/load/static-step/output types and writers now
produce a complete bounded C3D8 linear-elastic deck. Explicit units, named
regions, exact section coverage and unsupported-definition rejection are exposed
through a typed boundary and no-overwrite CLI. Generated cube preserves reference
IDs/material/12 constrained DOFs/four 25 N forces (100 N total) and required
outputs. No solver has run in this increment.

Current/RC2/post-RC2 pass native Mac/Linux ARM64: **331 accepted checks per
build**, eight material/21 static CLI controls and four semantic negative
controls; nine analysis/ten existing replay guards pass. Offline core passes
independently. Six-run sources, dependencies, tools and portable outcomes match.
Both known correctness failures and tetra measurement gate remain.
[Task 0023](tasks/0023-static-analysis-deck.md), [evidence/next increment](reports/static-analysis-deck.md).

All task 0022/0023 changes remain **uncommitted**; no new publication, hosted
x64/Windows/net48/RC2/full workflow or installer acceptance. Continue accepted
matching-native-solver execution → original results work. Native installers,
Homebrew, signing and four-target/release requirements remain explicit.
Earlier approval stops/material-only checkpoints below are historical.

## Historical checkpoint — task 0022 material foundation complete locally

2026-10-18: maintainer accepts the proposed sequence and requires an installable
native desktop application. [Installer/Homebrew requirements](RELEASE.md) now
specify Windows EXE/MSI, macOS DMG, Linux DEB/RPM or equivalent and Homebrew.
Apple Developer ID can be provided. Task 0021's approval stop is superseded.

[Task 0022](tasks/0022-analysis-material-foundation.md) source-links original
equations/unit converters/materials and original material keyword writers in an
expanded partial build. Current/RC2/post-RC2 each pass native Mac/Linux ARM64:
44 material checks plus all 218 previous checks (262 accepted), eight material
CLI controls and both correctness failures/measurement gate retained. Post-RC2
lamina/composite behavior is distinguished using exact upstream overlay bytes.
Source/dependency/tool/outcome comparisons match across hosts. Seven analysis
source guards/ten existing replay guards and an independent offline core pass
on Mac. [Evidence and remaining work](reports/analysis-material-foundation.md).

All task 0022 changes remain **uncommitted**. Native x64 CI is prepared, not run;
native Windows/full net48/RC2 oracle and remaining release gates stay open.
The new CLI writes only a material fragment. Continue accepted step 1 with
original section/BC/load/step and complete analysis deck generation, then native
solve/results. No new publication/frontend/default format/numerical policy.

## Current — task 0021 publication verified; next features await approval

2026-10-18: task 0019/0020 implementation is published at **47f17be6** on
origin/research/native-feasibility; remote SHA independently verified. Exact-
commit pipeline **#2960334103 passes both native Linux x64 jobs**. Current,
RC2 and post-RC2 each pass 218 accepted checks, 39 CLI/four data controls and
retain both original correctness failures/measurement gate. Downloaded reports
match all 48 source/36 tool hashes and Mac ARM64 portable outcomes. The CI ZIP
verifies 125 entries and all 90 packaged sources against the published commit.
[Publication evidence/download](reports/mesh-workflow-publication.md).

Publication/closing evidence only is authorized. **Wait for maintainer approval**
of [proposed next work](proposals/next-native-workflow.md) before implementing
model/deck/solve/results. No next feature started. Native Windows/full net48/RC2
and full-workflow/release gates remain. Earlier uncommitted/continuation state
below records historical task checkpoints; implementation is now published.

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

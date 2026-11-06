# PrePoMax-X contributor and agent instructions

2026-11-06 maintainer sequencing, D061: achieve full PrePoMax 3.0.0 parity
first; implement numerical fixes and improvements afterward. Read
.project/reports/deferred-correctness-improvements.md for recorded issues and
proposals. Defer the suggested combined correctness increment; continue larger
original-functionality milestones. Preserve original algorithms/tolerances,
explicit failures and existing safeguards. Port/integration repairs needed to
match original behavior remain in scope. All original functions remain required;
deferral closes no parity/correctness/platform/release gate. D057/D058/D059/D060
remain in force.

Task 0090 connects density/plastic hardening, pressure/gravity, original geometric
nonlinear static controls and increment/plastic-strain results through the solid
desktop workflow. Read .project/reports/nonlinear-loaded-solids.md and its receipt
for actual checks/candidate/publication. B006 retains the original quadratic
pyramid-to-wedge pressure accuracy failure; hexahedron conversion passes that
case. Keep original algorithms/tolerances and D029/D057/D058/D059, all remaining
original functionality, full PMX and every four-target/release requirement open.

Task 0089 connects all original mechanical 3D tetrahedron/wedge/hexahedron
formulations, mixed solid meshes and both explicit original pyramid conversions
through desktop configuration, native solve, original FRD/VTK mapping and mesh
export/reopen. Read .project/reports/solid-formulation-workflow.md and its receipt
for actual scope/checks/candidate/publication. Other element/mesher/calculation/
model/PMX functionality remains required. Preserve D029 original measurement/
classifier failures, D057/D058/D059 and all four-target/release requirements.

2026-11-06 delivery cadence reaffirmation: prioritize larger, usable functional
milestones and substantial implementation. Use focused checks during development
and representative workflow/regression checks at integration boundaries. Reuse
existing tests; add coverage for meaningful behavior/defects, not every line.
Full repeated platform/package/viewports sweeps belong at candidate milestones.
Measure progress by delivered original functions, not test counts. See D050 and
.project/TEST_STRATEGY.md. The unchanged final specification is ALL original
PrePoMax functions on all required platforms; the unavailable Intel/PARDISO
solver is the sole solver exception. D060 reaffirms the original scope.

2026-11-06 maintainer clarification, D060: require IDENTICAL PrePoMax 3.0.0
functionality, including ALL mesh types and ALL calculations, except specifically
unavailable solvers. Preview/static boundaries never reduce the final scope.
Tasks 0087/0088 add native C3D10 static calculations and desktop configure/solve/
results. Read .project/reports/quadratic-native-static.md and its receipt.
CalculiX's independent C3D10 formulation is no longer blocked by the separate
original PrePoMax measurement discrepancy. Preserve the original measurement
gate/failure and pyramid classifier failure, original algorithms and existing
tolerances. General curved quality, other mesh/calculation families, exact
native parity, full PMX and all D057/D058/D059/four-target/release gates remain.
The task 0084–0086 blanket solver refusal below is historical and superseded.

Tasks 0084–0086 add native C3D10 CAD meshing, preview, midside CAD regions and
mesh-only INP export. Read .project/reports/quadratic-cad-preview.md and its
receipt for source, actual checks and the retained candidate. Quadratic numerical
measurement, static solve and curved Jacobian/quality remain blocked; original
affine integration still fails (26.794910717854155 versus 28), and pyramid
classification still fails. Original algorithms/tolerances are unchanged. Linear
C3D4/C3D8 analysis remains operational. Keep D029/D057/D058/D059, exact native
parity, native-session PMX and every four-target/release gate open.

Tasks 0081–0083 add original CAD mirror, positive uniform/non-uniform scaling
and translated/rotated copies with owned undo/redo and frozen numbered outputs.
Read .project/reports/cad-mirror-scale-copies.md for actual source, verification,
publication and retained candidate. Originals remain byte-identical for copy
operations; partial/extra/cancelled outputs cannot replace the model. Native
Mac/Linux ARM64 analytical workflows pass, while their six-body meshes differ
and exact mesh/deck/field parity remains open. Native-session PMX, both known
correctness failures, quadratic tetrahedra and all release gates remain open.
Preserve D058/D059.

Tasks 0078–0080 add bounded owned CAD undo/redo, original axis-angle rotation
and checked whole-model STEP assembly export. Read
.project/reports/cad-history-rotation-export.md for actual source, checks,
publication and retained candidate. Undo/redo restores exact CAD bytes and
invalidates dependent mesh/analysis; exports preserve the active model and
check unique solid correspondence before a new-file publication. Mac/Linux
ARM64 and both copied Mac viewports pass the combined analytical workflow.
Native-session PMX, strict native equality, both correctness failures,
quadratic tetrahedra and all parity/release gates remain open. Preserve D058/D059.

Tasks 0074–0077 add native desktop CAD translation, plane split, controlled
ShapeFix repair and selected-part STEP export. Read
.project/reports/desktop-cad-editing.md for actual native/reference checks,
current candidate and publication. Successful edits invalidate dependent mesh/
analysis; failures/cancellation preserve it. Jobs freeze edit inputs/recipes.
PMX geometry mutation remains refused; STEP exchange is not native-session PMX
persistence. General defective repair, general PMX, correctness/tetrahedron,
parity and all release gates remain open. Preserve D058/D059.

Tasks 0071–0073 broaden checked original CAD/C3D4 PMX persistence with Poisson's
ratio/density, signed vector forces and compatible existing section/support/load
region reassignment. Read .project/reports/pmx-material-properties.md,
.project/reports/pmx-vector-loads.md and .project/reports/pmx-region-assignments.md
for actual checks, current candidate and publication. New native-session
serialization, new/deleted sets, general PMX and all correctness, quadratic
tetrahedron, parity and release gates remain open. Preserve D058/D059.

Tasks 0069/0070 add original CAD/C3D4 PMX projection and controlled native edit/
save/reopen/solve, with original-app readback. Read .project/reports/cad-pmx-reference.md
and .project/reports/desktop-cad-pmx.md. The original CalNode E8 formatter is
shared for this CAD PMX compatibility path; standalone mesh export is unchanged.
New native CAD-session serialization/general PMX remain open, along with all
correctness, quadratic-tetrahedron, parity and release gates. Preserve D058/D059.

Task 0068 adds visual CAD face/part region selection, original-reader set unions,
highlighting and CAD/mesh/result switching. Read
.project/reports/cad-region-selection.md and the native CAD handoff for actual
checks/publication/candidate. Next is an explicit original-PMX-compatible CAD/mesh
persistence boundary. D058 forbids hosted CI; D059 defers Linux x64 to Windows/
Podman near finishing. Keep both correctness failures, quadratic tetrahedra and
all full parity/release gates open.

Task 0067 completes the bounded native CAD → C3D4 mesh → static native solve →
original FRD desktop path on Mac/Linux ARM64, with original VOL/parameter code
and frozen CAD job inputs. Read .project/reports/native-cad-static-workflow.md
and .project/handoffs/native-cad-next-session.md. D058 forbids hosted CI runs or
retries without explicit maintainer instruction. D059 defers Linux x64 tests to
Podman on Windows near finishing. Normal research-branch publication remains
authorized with CI skipped. General CAD/mesh persistence, both correctness
failures, quadratic tetrahedra, full 3.0.0 parity and all release gates stay open.

Tasks 0060–0062 add bounded multi-part reference conversion, part-scoped
source identities and desktop display/picking of all emitted parts.
The two-body original Windows app capture and repeat tool outputs
match. Read .project/reports/multipart-cad-preview.md for checks and
publication. Matching native C++ sources, native CAD execution,
Windows geometry selection numbering and all correctness, tetrahedron,
parity and release gates remain open.

Task 0059 runs CAD import and VIS decoding in a background worker,
with cancellation and deferred window closing. The previous document
is retained until success. Read .project/reports/responsive-cad-import.md
for verification and publication. The reference runtime, matching native
C++ source requirement and all existing correctness, tetrahedron,
parity and release gates remain.

Tasks 0057 and 0058 replay the pinned original STEP/BREP conversion
and connect it to the macOS preview via the opt-in CrossOver reference
tool. The original L-bracket BREP and VIS bytes match. Read
.project/reports/cad-reference-import.md for scope and checks.
Matching native C++ source, native CAD execution, Windows legacy
verification and the correctness, tetrahedron, parity and release gates
remain open.

Task 0056 identifies upstream a55b39c6 as the binary drop matching all
38 bundled 3.0.0 Netgen runtime files. Its managed partial-triangulation
and unmatched-kernel-ID fixes are ported. Read
.project/reports/vis-kernel-id-parity.md for checks and publication.
Matching native C++ source and native STEP/BREP import remain open,
alongside Windows legacy verification and all existing correctness,
tetrahedron, parity and release gates.

Tasks 0054 and 0055 carry source edge IDs through the original VIS merge
and open read-only VIS geometry in the native desktop. The L-bracket
displays CAD edges and canonical measurements, with face picks using
source IDs. Read .project/reports/desktop-vis-geometry.md for checks and
publication. Matching native CAD source recovery and STEP/BREP import,
full 3.0.0 parity, both correctness failures, the tetrahedron gate and
release acceptance remain open.

Task 0053 shares the original VIS metadata, tessellation and merge code
with a portable probe. The task 0052 L-bracket VIS matches the original
capture on macOS ARM64, Linux ARM64 and native GitLab Linux x64.
Read .project/reports/portable-vis-reader.md for checks and publication.
Windows part creation and selection numbering follow this boundary.
Native CAD source recovery, full 3.0.0 parity, both correctness failures,
the tetrahedron gate and release acceptance remain open.

Task 0052 removed the verified Ubuntu .deb and kept its evidence, jobs and
task 0050 rebuild archive. Original Windows 3.0.0 under CrossOver passes
the L-bracket STEP geometry checks and yields repeatable BREP/VIS outputs
through its bundled NetGenMesher. The original `nglib.dll` differs from
the checkout. Read .project/reports/l-bracket-cad-reference.md before
attempting the portable VIS boundary or matching native CAD source recovery.
Keep full 3.0.0 parity, both correctness failures, the tetrahedron gate and
release acceptance open.

Task 0051 adds an internal Ubuntu 24.04 .deb around the native Linux
preview. ARM64 passes APT install, ordinary-user INP and PMX solve/render,
remove, reinstall and purge in a disposable container. User project and job
bytes survive all lifecycle operations. Read
.project/reports/ubuntu-desktop-deb.md for the retained installer, native x64
CI and the next Mac CAD reference fixture. Keep all 3.0.0 parity,
correctness, tetrahedron and release gates. The maintainer will test the
fully operational Mac candidate and should be notified when notarization
requires their involvement.

Task 0050 adds a native Linux desktop archive for both Linux targets. The
extracted ARM64 preview passes the INP and checked static PMX workflows in a
separate Ubuntu 24.04 runtime container with Xvfb/Mesa. The saved PMX, executed
deck and original decoded results match task 0049. Read
.project/reports/linux-desktop-preview.md for the retained archive, native x64
CI, dependency setup and cleanup. The next packaging proof is a native
Debian-family install/uninstall. Keep the current Mac image and the Linux
ARM64 archive while needed; both correctness failures, the tetrahedron gate,
full 3.0.0 workflow and all release acceptance remain open.

Task 0049 connects a checked result-free C3D8 PMX to the macOS model tree,
viewport and native CalculiX job. Both copied-app viewports pass the full
reopen/solve workflow and match the original 3.0.0 export's decoded fields.
Read .project/reports/static-pmx-native-solve.md for evidence, publication,
the retained image and cleanup. The next delivery increment is native Linux
desktop packaging. The maintainer's workflow test remains reserved for the
fully operational 3.0.0 candidate. Keep all general PMX, correctness and
release gates. Notify the maintainer when notarization needs their involvement.

2026-11-04 task 0048: the maintainer wants maximum progress toward full
PrePoMax 3.0.0 parity and will test their workflow at that candidate. Notify
them when Developer ID and notarization require their involvement. The opt-in
macOS preview now opens and saves the checked result-free static-solid PMX
subset. Both copied-app viewport probes pass and the edited PMX bytes match the
prior official 3.0.0 original-app readback. The task 0045 and 0047 checkpoint
and task 0048 implementation are published to origin/research/native-feasibility.
Read .project/reports/desktop-static-pmx.md for the retained image, exact CI
evidence and cleanup. Next is feeding the reopened PMX into the viewport and
native job path, followed by native Linux desktop packaging. Broader PMX
compatibility, both known correctness failures, the tetra gate and all parity
and release requirements remain open.

2026-11-03 task 0046 retention direction: maintainer reports task 0044 seems to
work and requests deleting unnecessary tested .app/.dmg/build copies to reclaim
storage before task 0045. Read .project/reports/storage-cleanup.md and its actual
execution/post-check receipts. This supersedes earlier keep-DMG instructions:
historical generated payload paths are purged, while source/evidence, small build
metadata, jobs, installed user app/state and reusable solver/tool caches remain.
Do not rebuild or retain old previews merely to satisfy historical handoff text.
For future work keep one candidate for verification/user testing, prune duplicates
promptly, and remove generated binaries after user confirmation. No app/numerical/
format/frontend/release gate change. Task 0045 is still prepared, not started.

2026-11-03 task 0044: maintainer requests proceeding after task 0043. Editable
static-solid model tree/controls now use original C# validation and frozen job
inputs, with actual changed-material/load native numerical evidence. Read
.project/reports/editable-solid-workflow.md for the final DMG, source snapshot,
checks and actual publication/CI. Imported named-set assignments are supported;
new/picked sets and project save/reopen remain pending. Task 0045 prepares an
explicit persistence decision/proof; do not relabel job JSON as PMX or silently
select a default format. Keep both earlier DMGs, D051/D053/D054 scope, both known
correctness failures/tetra gate and all full-parity/four-target/release gates.
Final task 0044 coverage fixes B004: require DAT only for requested histories;
retain strict FRD/STA and requested-DAT checks. Current repaired DMG is
X/Build/artifacts/task0044-current-delivery/dist/PrePoMax-X-Preview-arm64.dmg.
Both viewport editor proofs and copied field-only checks pass. Earlier capture
failure remains retained; strict native retry passes after maintainer display
confirmation. Read the report for actual repair publication/CI and current artifact.
Final repair 921b24a6 is remote-verified; exact-commit pipeline 3022312183 passes
all six automatic native Linux x64 jobs (15 native history-on/off checks;
compatibility manual; no hosted archive download). Closing follow-up is docs/
evidence only. Task 0044 is complete; task 0045 is prepared, not started.

2026-11-03 task 0043 continuation: maintainer selects PrePoMax 3.0.0 as parity
target and wants ongoing open-source macOS/Linux distributions tracking future
upstream releases even without upstream adoption (D054; .project/PARITY.md).
Task 0043 implements an opt-in native Cocoa child-view adapter with Qt input;
packaged solve/render, native-window event/Retina/lifecycle/larger-mesh evidence
is in .project/reports/native-viewport-boundary.md. Keep the tested task 0042 DMG
unchanged. Bridge stays default; no production frontend choice or performance
win is claimed, and no current C# host was executed. Read the report for actual
publication details and artifact/source-snapshot identity. Implementation
7514c88c is remote-verified; exact-commit pipeline 3022061388 passes all six
automatic Linux x64 jobs (compatibility manual; no hosted archive download).
Next is the editable
solid workflow, then explicitly agreed save/reopen. Preserve all prior gates
and D051/D053 scope; 3.0.0 stable correspondence is not yet verified.

2026-11-03 agent handoff: read
.project/handoffs/native-macos-next-session.md for the published checkpoint,
local-only DMG/runtime paths, evidence, pending gates and next bounded task 0043.
The maintainer reports the local preview test passed. No task 0043 implementation
is in progress; preserve the tested DMG and existing D051/D053 scope.

2026-11-03 task 0042: maintainer requests a local DMG while Developer-ID signing/
notarization are unavailable, explicitly choosing desktop solver controls first
and a complete uninstall/reset guide. This reorders the bounded workflow/package
slice before the remaining viewport binding attempt; B002 is still open. Read
.project/tasks/0042-local-macos-solver-dmg.md and .project/reports/local-macos-dmg.md
for actual artifact/verification/publication. Local preview signing is ad-hoc;
no Gatekeeper/quarantine change or clean-Mac/public-release claim. Apple container
is Linux-only. Implementation b6ec65d7 is remote-verified; exact-commit pipeline 3020068825 passes
all six automatic Linux x64 jobs (compatibility manual). Final local DMG identifies
clean b6ec65d7; actual mounted/copied/ejected app solve/render/signature/identity
checks pass, as do packaged-host cancel/failure/tamper checks. Read the report for
artifact SHA/path and the full uninstall/reset guide. Binary stays local/ignored.
Existing D051/D053 research publication scope/gates remain.

Task 0041 continuation: maintainer requests next steps after verified CI repair.
X/Build supplies one target catalog/entry for osx-arm64/win-x64/linux-x64/linux-arm64,
common self-contained C# hosts, native Mac/Linux solver helpers and the preserved
Mac package wrapper. Read X/Build/README.md and .project/reports/shared-target-builds.md
for actual results/publication. Cross-publishing is not native execution; planned
Debian/Fedora/Arch formats and unset platform floors are not support acceptance.
Implementation a893005c passes exact-commit pipeline 3019959774; downloaded
native Linux x64 cube/source/recipe evidence matches the bounded Mac comparison.
CI split 0411ae23 uses an affected-input native job; pipeline 3019992604 passes
all six automatic Linux x64 jobs. No frontend/default/backend/format/
precision choice or release-gate closure. Existing D051 publication scope remains.

2026-11-02 task 0040: user supplied signed-in GitLab access. Failed 384edea2
pipeline 3019186769 has one failure, shared-core-linux-x64 job 17675531644:
actual CLI roundtrip lost block name CUBE after B001's fix. Other four automatic
jobs passed. Read .project/reports/core-pipeline-regression.md and B003. Preserve
inline block names, filter their already-emitted labels from explicit sets, retain
strict CLI equality/B001 stress-row checks. Mac Core/Analysis and native solve pass.
Repair f4e388a5 is remote-verified; pipeline 3019257012 passes all five automatic
native Linux x64 jobs. Downloaded Core source/tools match Mac and the actual
125-entry development ZIP bytes/hash verify. Compatibility stays manual. Task
0040 is complete; next is task 0039's shared target/build entry and Mac workflow.
Writer changes
need both affected Core and Analysis consumers. No weakening tests/tolerances or
new platform/release acceptance; existing D051 publication scope/gates remain.

2026-11-02 latest planning direction, task 0039: maximize native Mac delivery
speed from one shared source tree with Windows x64 and Linux x64/ARM64 awareness
now. Debian/Fedora/Arch are package/test layers, not application forks; Arch Linux
ARM is an explicit environment. Read .project/proposals/accelerated-native-delivery.md
for the revised target/adapters/build/test sequence. Maintainer reports failed
GitLab CI; exact job/commit/log was requested and is not yet diagnosed. Do not
claim a hosted pass or guess a fix, disable Linux checks or weaken tolerances.
This task is planning only; no application/CI/frontend/default/backend/format/
precision change. D051 publication authorization and all existing gates remain.

2026-11-02 tasks 0037/0038: native Mac ARM64 CalculiX 2.22/SPOOLES research build
and original deck → solve → FRD/DAT workflow pass the bounded analytical cube.
The first solve exposed/fixed B001 duplicate set emission in MeshDeckWriter;
332 current analysis checks, 49 execution checks and existing source guards pass.
Both original correctness failures/tetra gate remain. A local ad-hoc-signed Mac
viewport app displays original-reader data without external Python/dotnet on PATH;
B002 direct Qt embedding fails, so its VTK frame-copy bridge stays experimental.
Implementation is published/remote-verified at 384edea2 on origin research;
master is unchanged and hosted CI is unverified (GitLab session signed out).
Read .project/reports/native-cpu-workflow.md and native-desktop-preview.md, tasks
0037/0038 and current STATUS for actual publication. No production frontend/default
backend/format/precision choice or full release acceptance. Preserve four targets,
runtime/source/installer requirements; do not claim hosted CI without verification.
Earlier local/uncommitted descriptions are historical after confirmed publication.

2026-11-02 continuation/publication authorization: maintainer requests proceeding
with desktop-host/native solver steps and committing/pushing useful work with
progress documentation. Publish reviewed checkpoints normally to
origin/research/native-feasibility; verify actual remote and relevant CI. Preserve
all existing work, both known failures/tetra gate and release requirements. No
upstream/master/x/main/release write, force push or silent frontend/format/
precision choice. This supersedes prior leave-uncommitted wording for this
continuation. Use bounded task records and the lighter verification cadence.

2026-11-02 implementation start: task 0036 adds X/Checks/check.py fast/current
and explicit compatibility profiles, retained failure/source manifests and prepared
CI separation. All four current suites pass on Mac ARM64 in 43.36 s; selected
results compatibility passes all three pins. Both known failures/tetra gate stay.
Read X/Checks/README.md and .project/tasks/0036-development-check-profiles.md.
CI changes are local and not hosted-verified; no commit/push. Next is the bounded
native-VTK host/package proof and native CPU solver build under the accepted plan.

2026-11-02 delivery-speed direction: maintainer prioritizes installable native
software and requests less repetitive testing with reliable cross-platform bug
tracing. Read task 0035 and .project/proposals/accelerated-native-delivery.md.
Code_Aster is optional/deferred; CalculiX with existing open backends remains
primary, PARDISO need not block initial delivery. Use changed-area/current-source
checks for routine work; broaden for shared numerical/interop/persistence changes.
Historical-pin replay, full platform sweeps and release-only checks belong at
affected integrations/milestones, not every edit. Preserve useful tests, numerical
tolerances, both known failures and tetra measurement gate. Missing checks stay
pending, not passed. Final four-target/parity/installers/Homebrew requirements
remain. First installer is an internal scoped preview, not final parity. The
plan is recorded; task 0036 now prepares the CI profile changes. Frontend/default format/
native solver profile remain explicit decisions; normal commit/push policy stays.

2026-10-18 publication verified: tasks 0030/0031 FRD/DAT implementation is on
origin/research/native-feasibility at 62c7de1bea234acc7aea16ee7c11283822f86501.
Exact-commit pipeline #2960686368 passes all five native Linux x64 jobs. Three
hosted results JSON previews identify clean SHA and match ten source/tool/package/
field/history/test groups against retained Mac/Linux ARM64 evidence (78 checks,
nine CLI controls per pin). Archive download was unavailable; do not claim raw
archive verification. Read .project/reports/results-publication.md and task 0032.
This closing publication is documentation/evidence only; normal maintainer commit/
push policy resumes. Both correctness failures/tetra gate and all native solver/
Windows/net48/RC2/full-graph/UI/persistence/CAD/source/four-target/installer gates
remain. Next engineering priority is reproducible native CPU solver recovery and
a real deck → solve → FRD/DAT workflow. No further feature work in task 0032.

2026-10-18 current instruction: maintainer explicitly requests the next bounded
task and then commit/push current code to GitLab within remaining usage. Task
0031 adds original DAT static-shaped history inspection; task 0032 reviews and
publishes tasks 0030/0031 normally to origin/research/native-feasibility and
records exact-commit hosted/artifact evidence. This supersedes earlier uncommitted
wording for this publication only. Read .project/reports/portable-dat-histories.md
and .project/reports/results-publication.md for actual completion/publication.
Preserve both correctness failures/tetra gate and all Windows/net48/RC2/native
solver/full-graph/UI/persistence/CAD/source/four-target/installer gates. No upstream,
x/main/release write, force push, frontend/default serializer/backend/precision/
GPU decision. DAT parsing alone cannot establish solver completion. Finish this
publication task without widening feature scope; normal publication policy resumes.

2026-10-18 latest continuation: maintainer explicitly resumes after reset,
lifting task 0029's feature stop for accepted local implementation. Task 0030
adds original FRD decoding/field types/invariants in their original assemblies,
a bounded raw C3D8 static snapshot and inspect-frd CLI. Original FeResults/
FeMesh orchestration stays in net48 legacy partials; original Tools helpers are
mechanically extracted. All three source pins pass Mac/Linux ARM64: 39 results
checks/five CLI controls plus rerun 331 accepted analysis checks; both known
correctness failures/tetra gate retained. Read .project/reports/portable-frd-fields.md.
Source/tool/package/field outcomes match across hosts. New x64 CI is prepared,
not run; native Windows/full net48/RC2 and all release gates remain. Task 0030
stays uncommitted; no new publication/default/solver/GPU/serializer decision.
Continue original DAT/results and reproducible native CPU solver recovery.

2026-10-18 publication complete: implementation tasks 0022–0028 are published at
993f9263f8770bee5b75d2cca3b07baaf2c1097e on origin/research/native-feasibility.
Exact-commit pipeline #2960594131 passes all four native Linux x64 jobs.
Downloaded three-pin analysis/execution reports match source/tools/dependencies
and retained Mac outcomes (331 analysis accepted, 47 execution/planning checks,
13 CLI rejection controls; both correctness failures retained). Closing task 0029
is documentation/evidence only. Read .project/reports/analysis-execution-publication.md.
STOP feature work until maintainer resumes after reset. No production CPU
scheduler/default migration, native solver acceptance or release-gate closure.
Earlier uncommitted wording is historical for this publication.

2026-10-18 latest publication boundary: maintainer explicitly authorizes one
bounded task (~15 percentage points of remaining usage), then commit/push all
current work and continue after reset. Task 0028 implements the portable read-only
75% CPU planner/CLI (47 checks and 13 rejection controls per pin on Mac/Linux
ARM64). It does not apply settings, schedule jobs or change reference runs.
Task 0029 covers review, normal origin/research/native-feasibility publication,
exact-commit hosted checks/artifacts and closing evidence/reset handoff. This
supersedes earlier uncommitted-only wording for tasks 0022–0028. No upstream/
x/main/release write or force push. Read .project/reports/analysis-execution-publication.md
for actual SHA/status. STOP feature work after publication until maintainer
resumes; preserve both correctness failures/tetra gate and all release gates.

2026-10-18 latest, task 0027: maintainer requests research on solver advice,
75%-of-available-thread defaults and NVIDIA/AMD/Apple GPU optimization. Read
.project/reports/solver-guidance-threads-gpu.md. Solver advice and a 75% default
are requested product direction; this increment only researches the concrete
design. No settings/default/precision changes, integration, numerical benchmark
or publication. Existing SPOOLES/modified PaStiX first; MUMPS only if required
under D042. NVIDIA CUDA is documented; AMD SuperLU_DIST HIP requires another
adapter; no reviewed Apple Metal direct-solver route identified (MSL 4.1 has no
double scalar type). Proposed thread budget has manual override/concurrent-job
coordination and is not a utilization/speed guarantee. Preserve all existing
uncommitted work, both correctness failures/tetra gate and every release gate.

2026-10-18 latest solver policy, task 0026: maintainer rejects Panua's machine-
fingerprint licensing. A new alternative is needed only if omitting PARDISO
cripples useful functionality. This narrows the earlier task 0025/D041 requirement
to reproduce every proprietary backend. Research recommends assessing existing
CalculiX SPOOLES/PaStiX first; no new solver integration or production default/
precision change is selected. Read .project/reports/without-pardiso-assessment.md.
Historical forum evidence identifies correctness and capacity risks, not a proven
PARDISO-exclusive analysis category. In original 2.22 arpack/arpackbu code,
PaStiX-labelled selections can call PARDISO when both are compiled in; later
comparisons must verify actual dispatch. Our numerical comparisons are deferred
by the maintainer. Task 0026 is research/documentation only; all changes remain
uncommitted. Preserve both correctness failures/tetra gate and all release gates.

2026-10-18 exact solver clarification: maintainer explicitly requires complete
identical solver software adjusted for cross-platform use, and requested research
only. Task 0025 proves RC2 ccx_dynamic.exe matches the official 2.22 Windows
binary; all five DLLs match the old reference. Six choices pass the bounded cube
through existing Mac CrossOver; this is not native ARM acceptance. GUI default
is PARDISO, distinct from this executable's PaStiX default. Exact PaStiX/Scotch/
ABI/transitive build recipe remains missing; native ARM Intel MKL/PARDISO is an
identified gap. Read .project/reports/exact-solver-provenance.md. Do not silently
replace/drop backends, rewrite solver keywords, select remote/compatibility
architecture or claim fully native identical dependencies. Research changes are
uncommitted, with no contacts/publication/production change. Existing correctness
and release gates remain; earlier broad continuation does not select that policy.

2026-10-18 continuation: task 0024 native job/preflight/original STA-CVG boundary
passes 33 new checks plus four CLI controls per mode on native Mac/Linux ARM64
(current/RC2/post-RC2), four source guards, with matching fingerprints/outcomes.
Official CalculiX 2.22 source is under ThirdParty/Sources with pinned unchanged
bytes/license; exact native PaStiX/BLAS/patch/compiler/ABI/runtime chain remains
unproven. No native numerical solve/substitution is claimed. Continue original
FRD/DAT field work and matching native-source/build recovery. All task 0022–0024
changes remain uncommitted; no new publication or policy choice is authorized.
The maintainer requires all third-party corresponding source in organized folders
and a public package-manager/release branch; .project/REPOSITORY_LAYOUT.md records
the map and planned x/release lane. No public branch/push is performed. Read
.project/reports/native-job-boundary.md; retain both correctness failures, the
tetra host gate and every Windows/net48/RC2/four-platform/release requirement.

2026-10-18 next sequence accepted: maintainer approves
`.project/proposals/next-native-workflow.md` and requires an installable desktop
PrePoMax-X: Windows EXE/MSI, macOS ARM64 DMG, Linux x64/ARM64 DEB/RPM or similar,
and Homebrew installation. Apple Developer ID enrollment is available. Continue
local implementation in tested increments. Tasks 0022/0023 now generate a
bounded complete C3D8 static deck through original types/writers; all three
source modes pass native Mac/Linux ARM64 (331 accepted checks per build, both
known correctness failures/measurement gate retained). Current evidence is
`.project/reports/static-analysis-deck.md`. All task 0022/0023 changes remain
uncommitted. Continue matching native solver execution and original results
under the accepted sequence. No new publication/frontend/default serializer/
numerical/native-tool policy is authorized; Windows/net48/RC2 and all installable
desktop/four-platform/release gates remain. Earlier task 0021 stop is superseded.

2026-10-18 publication complete: task 0019/0020 implementation is published at
47f17be6657b470cff814d50b97c79fada52040a on origin/research/native-feasibility.
Exact-commit pipeline #2960334103 passes both native Linux x64 jobs; downloaded
source/tool/outcome fingerprints and 125-entry package verify. Task 0021 closes
publication with documentation/evidence only. STOP for maintainer approval of
`.project/proposals/next-native-workflow.md` before further feature work. Earlier
uncommitted/continue wording is historical. Both correctness failures and all
Windows/net48/RC2/full-workflow/release gates remain.

Read `.project/PROJECT.md`, `.project/STATUS.md`, `.project/DECISIONS.md` and the task record before changing anything. These tracked records, rather than conversational memory, define the handoff.

## Current authorization

2026-10-18 publication and approval boundary: maintainer explicitly requests
committing/pushing completed task 0019/0020 changes. Task 0021 covers review,
normal origin/research/native-feasibility publication, exact-commit CI/artifact
verification and closing evidence. After publishing, explain the proposed next
steps and STOP for maintainer approval before implementing them. This latest
instruction supersedes earlier open-ended local implementation continuation.
Retain both correctness failures/measurement gate and all release requirements;
no x/main/upstream write, force push or architecture/numerical-policy change.

2026-10-18 implementation continuation: maintainer asks to proceed while
preparing Windows for GitLab. Task 0020 completes the first portable INP mesh
input/measurement/export increment with original parser/writer reuse and
mechanically checked partial extraction/type ownership. Current/RC2/post-RC2
pass on Mac/Linux ARM64, with both correctness failures/host gate retained.
All task 0019/0020 changes remain uncommitted. Continue local implementation
toward the accepted mesh/deck/solve/results workflow; full model/results,
net48/RC2 Windows and release gates remain. No push/integration or production
frontend/default serializer/native-tool/numerical-policy change is implied.

2026-10-18 RC2 continuation: maintainer requests syncing the fork with Matej's
3.0.0 RC2, comparing the code and accelerating implementation toward a native
3.0.0 release near upstream stable. Task 0019 supersedes the task 0018 stop for
this continuation. Local/origin master now mirror f6273e39 (normal ff-only
push, remote verified); RC2 source marker 912fb3d0 is distinct from ten later
commits. New shared replay/CI tooling and evidence remain uncommitted under
normal maintainer publication workflow. Continue local implementation toward
a usable shared mesh/deck/solve/results workflow; preserve source/type ownership,
both correctness failures/host gate and all release requirements. No x/main
integration, upstream write, force push, frontend/default serializer choice,
algorithm/tolerance or silent native-tool substitution is implied.

Task 0018 is complete: task 0017/CI build-delivery published at b83fa49f,
pipeline #2956835416 passes both native x64 jobs, downloaded ZIP/source/tool
checks and Mac execution verified. Closing evidence publication is included.
Stop at this boundary. Further feature work/commits/pushes require a new
maintainer instruction. Both correctness failures and release gates remain.

2026-10-16 bounded publication request: maintainer explicitly authorizes commit/
push of task 0017 and selection of a small task within 20% of the five-hour
allowance. Task 0018 packages the existing development ZIP as a verified native
Linux x64 CI artifact and covers this publication/closing evidence. Retain the
two correctness failures and host gate; no numerical algorithm change, frontend/
default serializer, upstream write, force push or x/main integration.

Current local checkpoint is task 0017: original element kernel and a runnable
development CLI/source bundle pass their bounded Mac/Linux ARM64 checks. Two
strict original-source correctness checks remain failed and recorded; quadratic
tetrahedra are gated by the host. Do not silently change algorithms/tolerances or
claim full acceptance. Task 0017 stays uncommitted. Published data slice is
236b1a2e, closing evidence 1f1f51c4 (both hosted pipelines passed).

Task 0016 publication is now verified at 236b1a2e; exact-commit native x64
pipeline #2956740201 passes both jobs and downloaded shared-core evidence
matches source/tool/outcome fingerprints. Closing evidence publication completes
that task. Subsequent bounded engineering work is authorized locally; keep its
implementation uncommitted unless the maintainer requests its publication.

2026-10-16 publication and implementation continuation: maintainer explicitly
requests committing/pushing the completed task 0015 work and continuing toward
a working build. Task 0016 covers this publication and hosted evidence follow-up.
Continue bounded shared-core implementation on research/native-feasibility;
preserve existing algorithms/type ownership and documented release gates.
The instruction does not select a frontend/default serializer or authorize
x/main integration, upstream writes, force pushes or silent native-tool changes.

2026-10-16 Mac continuation: maintainer explicitly authorized importing the
verified Windows bundle and publishing reviewed ac51fc77 to origin/research/native-feasibility.
That publication and exact-commit hosted CI are now verified. Task 0015 bounds
the next geometry-metadata/IntegrationScale/FRD-stream shared-library increment
and Mac/native Linux ARM64 checks. Its implementation remains uncommitted;
future implementation commits/pushes require a new instruction. Preserve original
source algorithms/type ownership and all release gates. No x/main integration,
upstream write, force push, frontend/default serializer or F001 decision.

2026-10-16 Windows closeout/publication: the maintainer explicitly requested
committing and pushing this work, completing useful remaining Windows checks,
and preparing immediate MacBook continuation. Task 0014 covers this publication
and handoff. It supersedes earlier leave-uncommitted restrictions for the
reviewed Windows/reference/shared-core changes and their closing evidence.
Publish only to origin/research/native-feasibility, without force; do not merge
x/main, write upstream or select a frontend/serializer. Windows Credential
Manager currently returns Access denied inside the execution sandbox; do not
claim a push succeeded without remote verification. Preserve private files
outside Git. Read .project/handoffs/macbook-next-session.md for the next work.

2026-10-16 implementation continuation: the maintainer supplied the original
private PMX and explicitly requested finishing testing and proceeding to build.
Task 0013 authorizes the first bounded shared-library implementation on the
planned research/native-feasibility branch. It supersedes historical
research-only restrictions for this slice: mechanically separate CaeException,
keep its original net48 project inclusion/type identity, source-link existing
math/node/structured-mapping code into partial portable libraries, add a small
callable host and regression checks. Do not widen this into a full Controller,
frontend, serializer, CAD bridge or F001 rewrite. No commit/push, x/main merge
or upstream communication was requested. Preserve all existing local work.
Native private-model/results comparison is now recorded in the Windows report;
remaining release gates do not prevent this approved bounded implementation.

2026-10-15 local completion instruction: the maintainer explicitly authorized
completing remaining feasible testing/preparation with resources on this Mac,
then committing and pushing the reviewed research to the origin fork. Task 0012
bounds this continuation. This supersedes earlier leave-uncommitted instructions
for this publication only. No production refactoring, frontend/default serializer
choice, F001 integration, x/main merge, upstream write or force push is authorized.
The exception ends after task 0012 publication and its hosted evidence follow-up.
Task 0012's research is published at 24c790ac; native Linux x64 pipeline
#2951491552 passed. This closing evidence publication ends that exception.
Resume prepared task 0011 on Windows; future agent commits/pushes need a new
explicit instruction. The older uncommitted-only statements below are historical.

Phase 0 is complete. On 2026-10-13 the maintainer authorized the recommended first milestone, a new implementation branch and promotion of the reviewed Phase 0 records into `x/main`. Task `.project/tasks/0002-core-feasibility.md` defines the bounded scope: source-linked STL/vector/node probe, tests/provenance, upstream replay, local Podman verification and complementary GitLab native Linux x64 CI on `feature/core-feasibility`.

Task 0002 is complete within its bounded scope: both source pins pass on macOS ARM64, Podman Linux ARM64 and GitLab native Linux x64. Evidence is in `.project/reports/gitlab-linux-x64.md`. Task 0003 (`.project/tasks/0003-core-data-feasibility.md`) completed its bounded probe/inventory/capture preparation on `feature/core-data-feasibility`: unchanged engineering data/math/stream probe, measured dependency boundaries and PMX source-identity/Windows fixture preparation. Original production files, BinaryFormatter behavior and assembly ownership remain unchanged. On 2026-10-14 the maintainer first authorized replacing GitLab CI with local Podman verification, then authorized retaining Podman and restoring complementary GitLab native Linux x64 checks. The maintainer handles all pushes and normally commits; leave changes uncommitted unless explicitly asked to commit. Preserve existing application source/project files and algorithms; do not introduce production dependencies, begin broad controller/GUI/serialization refactoring or select a frontend. Further implementation or feature integration into `x/main` requires authorization. Never push without explicit authorization, force-push, delete branches or overwrite uncommitted work. Proposals in the broader specification remain unapproved commitments.

Current continuation exception (2026-10-14): the maintainer explicitly authorized the agent to commit and push to the origin fork this time. This covers closing task 0002 evidence and the next bounded dependency/source-linked-probe/PMX identity investigation approved in the conversation. It does not authorize force pushes, upstream writes, x/main integration, a frontend/serializer choice or broad production refactoring. This scoped continuation ends with the task 0003 evidence publication; future agent commits/pushes require a new explicit instruction. Normal maintainer commit/push workflow resumes afterward.

2026-10-14 pre-Windows continuation: the maintainer authorized completing bounded
steps from the proposed native/core/rendering/fixture work, stopping at completed
task boundaries before usage runs out. Tasks 0004–0007 on
`research/native-feasibility` now record completed native-source/header audit,
structured-kernel probe, isolated synthetic VTK smoke test and shell T-junction
fixture preparation. This does not authorize production refactoring, F001
implementation, a frontend/binding choice, integration, commits or pushes.
Windows comparisons and matching-source/native-tool recovery remain pending.

2026-10-15 continuation: the maintainer supplied a private PMX, authorized
continuing pre-Windows work and investigating an adjusted cross-platform schema,
and explicitly requested a CrossOver reference attempt. Tasks 0008–0009 record
completed read-only inspection and original Windows 2.6.0 read/save/reopen through
a separate CrossOver bottle, with human confirmation and bounded byte comparisons.
The schema remains proposed; this is not native platform acceptance, production
refactoring/format authorization or permission to publish a PR. Preserve private
models outside Git and the original unchanged. Maintainer controls commits/pushes.

The 2026-10-15 testing/preparation continuation completed task 0010: PMX tests
and reference inventories also pass on Linux ARM64. Remaining preparation exit
gates are recorded separately; no broader implementation/commit authorization.

## Repository conventions

- Current continuation: read `.project/handoffs/macbook-next-session.md` and
  tasks 0013/0014. Native Windows model/results and structured-kernel capture
  are completed within scope; do not restart the earlier Windows preparation.
  Check publication status in STATUS and the actual remote before transfer.
- Required targets (maintainer correction, 2026-10-15): Windows x64, Linux x64,
  Linux ARM64 and Apple M-series macOS ARM64. “x86” explicitly means 64-bit
  Intel/AMD. Intel Macs and 32-bit x86 are outside scope; Linux ARM64 is required.

- The project is **PrePoMax-X**. Use `X`/`x` for project-specific cross-platform naming and prefixes, including `x/main`.
- `origin`: maintainer's fork. `upstream`: official `https://gitlab.com/MatejB/PrePoMax.git`. Detect the default each time; currently `master`.
- `master`: exact upstream mirror, fast-forward only. No PrePoMax-X commits here.
- `x/main`: reviewed cross-platform integration. `feature/*`, `integration/*`, `research/*`: scoped work. These user-requested prefixes override generic agent branch conventions.
- Read `.project/UPSTREAM_SYNC.md` before synchronization. Git merge success is not compatibility evidence.
- Preserve upstream paths, type and assembly identities, command semantics, units, numbering and file formats wherever possible. Keep platform adapters at boundaries; preserve attribution and licenses.

## Evidence and verification

Label conclusions as verified observation, architectural inference or experimental question. Cite paths, symbols, pinned commits and primary sources. A textual scan includes unused imports and comments; it cannot establish portability. Run only checks suited to the change; distinguish offline checks from live application, rendering, meshing and numerical tests. Record commands, outcomes, missing fixtures and infrastructure in `.project/reports/` and update STATUS/task records.

Existing modern automation gateways, mesher runners and command journals should be investigated before inventing replacements. `-g No` still creates WinForms/VTK and is not a platform-neutral headless backend. Never enable unsafe serialization or change mesher/solver versions silently to make a build pass.

No delegation is required by these instructions. Keep this file and `.project/` in the repository. Upstream `.gitignore` ignores `AGENTS.md`; it was explicitly force-added for this project without changing upstream ignore rules.

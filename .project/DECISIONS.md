# Decision register

D068 — Sync with upstream 3.0.2 before CI, 2026-11-23: upstream moved 51 commits past
the 3.0.1 pin (version 3.0.2 at `6703b1cb`, not released yet), among them a new storage
format without BinaryFormatter, HiGHS instead of lp_solve and new meshers. The maintainer
chose to sync before M3 CI, together with housekeeping and release basics, and to
have a macOS build on 3.0.2 before asking upstream about collaboration. Files of
older versions are read by upstream's own legacy reader (PrePoMax.LegacyImport) with a
small opt-in hook so every type a file names is bound by our reviewed allowlist (never
unrestricted deserialization); our own NRBF reader is retired. The 3.0.1 release stays
the Windows behavioural reference until 3.0.2 is released.

D067 — Avalonia, macOS first, 2026-11-21: after the M3-1 spike (one runtime, the native
3D view with real input and picking, modal loops, Retina, overlays per D066 on macOS
ARM64) the maintainer chose Avalonia for the .NET front end and its order: macOS, the
maintainer's working machine, first, to M2's level and beyond (M3-1a); then Linux on the
local Podman machine, Linux ARM64 with Xvfb probes and VNC for manual checks (M3-1b), as
the UI does not depend on the CPU architecture; Linux x64 with the per-architecture
native builds after that; Windows in M3. The Qt front end stays usable for real projects
(`X/App/local_app.py`) until Avalonia matches it. The Avalonia version for the renderer
(11.3.x as in the spike, or 12.x) is pinned when the renderer moves into X/App.

D066 — Overlays follow the display scale, 2026-11-21: on a Retina Mac the 3D view
draws in device pixels (sharp), while the original vtkControl places and sizes its
overlays (scale bar, axes, legends, texts, status block) in control units. Rather than
draw VTK at control units magnified, as Windows does for the original (not DPI aware),
which crashed VTK's Cocoa pixel readback, the maintainer chose to scale the overlays now
instead of after parity (an exception to D061's order). The C# widget wrappers of
vtkControl (VtkNativeWidget, VtkNativeScalarBar) convert overlay geometry between
control units and device pixels by VtkNativeView.DisplayScale; mouse and pick
coordinates stay device pixels. The scale is 1 on Windows, so the original is unchanged
there; it fixes high-DPI displays on every platform whose front end draws in device
pixels.

D065 — One runtime for the front end (M3-1), 2026-11-19: the Qt front end of
X/App is drawn by Python (PyQt6 through Python.NET), so the original .NET code and
the renderer share one process with two runtimes, the GIL and a cross-thread queue;
M2's deadlocks came from that boundary. The maintainer chose to replace it before
CI: M3-1 renders the same FormsCompat control model from .NET (toolkit chosen by a
spike: Avalonia with a native host for vtkNative, or Qt 6 through a thin C ABI
shim), moves the GUI probes and packages to X/App and retires the Python renderer
and the workbench hosts. CPython stays only for the original's own Python features.
Layout in M3-1 is ported from the MIT-licensed dotnet/winforms layout engines
into FormsCompat (not reimplemented), and checked by a per-form control-bounds
comparison against the original application.
M3–M5 keep their content and order after M3-1.

D064 — GitHub as the project home, 2026-11-18: upstream moved to
github.com/PrePoMax/PrePoMax (the GitLab project is archived; its history was
rewritten before archiving). The maintainer forked it as
github.com/aleksa9275/PrePoMax-X and moved the working copy there. The 146
PrePoMax-X commits were replayed unchanged onto upstream's own history at
`eb6aff0c` (the content our GitLab base `de8f7303` already had; trees identical
before and after), so the fork shares Matej Borovinšek's history and a later pull
request shows only PrePoMax-X work. The GitLab fork stays as a read-only archive
(`gitlab` remote, branch `research/native-feasibility` at `e08df83f`).
CI moves to GitHub Actions (M3); D058's GitLab quota hold no longer applies.
Pull requests or issues upstream need explicit maintainer instruction.

D063 — Target 3.0.1 with upstream's native VTK port, 2026-11-17: PrePoMax 3.0.1
(15 Nov) supersedes 3.0.0 as the parity target, and upstream's post-3.0.1
`vtkNative` (a flat C API over VTK 9.7, called through P/Invoke, ActiViz removed)
is adopted now rather than after release. The code base is upstream `master`
pinned per sync — first `1e2f83f2` (3.0.1 + vtkNative + `Dev/` reorganization);
the 3.0.1 release is the behavioural reference. Consequences: the original
`vtkControl` is to run on vtkNative built for macOS/Linux (its Windows-only
window embedding/input made portable — a candidate upstream contribution)
instead of the planned 165-member adapter; the interim Python VTK renderer and its
VTK 9.5.2 wheel are retired once the original viewport runs, so a package ships
one VTK. Each later upstream sync pins an exact commit. D060's scope now reads
"identical PrePoMax functionality" at the pinned upstream revision.

D062 — Whole-code reuse strategy and simplified process, 2026-11-08: the
maintainer accepts the assessment that slice-porting plus a reimplemented Python
application layer fragmented progress. Direction: **maximum reuse of existing
original code and practices.** Phase A builds the whole original domain
assemblies (CaeGlobals, CaeMesh, CaeModel, CaeResults, CaeJob) for .NET 10 on all
targets while keeping the net48 build working. Phase B runs the original
Controller/Commands without WinForms (main-form dependency behind an interface)
and reuses the original PMX serialization with a strict type allowlist. Phase C
builds the cross-platform UI reusing the original forms/property-view classes
and the existing native VTK viewport work; the UI framework is chosen at the
start of Phase C with reuse as the criterion. The existing Python/Qt desktop is
retained as the working preview until superseded. Process: short AGENTS.md,
replace-not-append STATUS.md, one report per milestone, progress measured
against `PARITY_INVENTORY.md`; pre-2026-11-08 logs moved to `.project/history/`.
After parity, all recorded bugs and compiler warnings are reviewed and fixed
(D061). D057–D061 remain in force.

D061 — Parity first, correctness improvements afterward, 2026-11-06: the
maintainer explicitly directs recording discovered discrepancies and proposed
fixes, continuing as is toward full PrePoMax 3.0.0 parity, then implementing fixes
and improvements. The proposed combined correctness increment is deferred;
continue larger original-functionality milestones now. Preserve original
algorithms/conversions/tolerances, explicit failed checks, existing measurement
safeguards and reference evidence. Necessary port/integration repairs to match
original behavior and all missing original functions remain in scope. Deferral
does not mark failures passed, omit original functionality or close exact-parity/
correctness/four-target/release gates. D060's sole unavailable Intel/PARDISO
exception and D057/D058/D059 remain. See the
[post-parity backlog](reports/deferred-correctness-improvements.md), covering
D029's integration/classifier findings, B006 pressure accuracy, small solver
field differences and native mesher reproducibility.

D060 — Reaffirmed original full-functionality requirement, 2026-11-06: the maintainer requires
**IDENTICAL PrePoMax 3.0.0 functionality, including all mesh types and all
calculations, with the unavailable Intel/PARDISO solver as the sole exception**. Bounded previews are development
increments, never a reduced final product or authorization to omit element,
analysis, material, load, result, editing or persistence functionality. This is the original specification, not an expansion or authorized scope change.
Do not generalize the Intel solver exception to other backends or analysis types. Preserve shared
original behavior and record any implementation limitation as outstanding work.
Tasks 0087/0088 separate the original PrePoMax quadratic measurement discrepancy
from native CalculiX's independent C3D10 formulation and deliver real quadratic
static calculations. This supersedes tasks 0084–0086's blanket solver refusal;
D029's original measurement failure/gate and pyramid classifier failure remain.
Do not change original quadrature, solver algorithms or existing tolerances.
D057 original PMX, D058 hosted hold, D059 deferred Linux x64 and all required
four-target/full-functionality/distribution/release acceptance remain open.

D059 — Deferred Linux x64 verification, 2026-11-05: the maintainer resumes
task 0067 and chooses Podman on a Windows machine for Linux x64 testing at
the finishing phase. Continue native Mac/Linux ARM64 development and local
verification now. Linux x64 remains pending until that actual environment is
executed. D058's hosted CI hold remains; this does not authorize a hosted run,
change any engineering check or close platform/release acceptance.

D058 — Hosted runner quota hold, 2026-11-05: the maintainer warns that the
first uncached x64 CAD build consumes the remaining monthly CI allowance and
hosted CI will be unavailable for the next 25 days. Let the current test finish;
start no further hosted runs without explicit maintainer instruction. Ordinary
pushes must consume zero runner minutes. Preserve the complete test/job matrix
behind manually requested web pipelines, use native Mac/Linux ARM64 local
verification and retained tool caches, and keep unexecuted x64/Windows/release
checks pending. This narrows D051's hosted verification cadence for the quota
hold without changing its research-branch publication authorization, engineering
tests/tolerances or release requirements. No automatic re-enable date or hidden
retry is selected. [Task 0065](tasks/0065-ci-quota-milestones.md).

D057 — Original PMX compatibility, 2026-11-03. The maintainer selects full
original .pmx compatibility and reusability for task 0045. Require original
Windows PrePoMax 3.0.0 interoperability in both directions, preserve editable
project semantics, and check older inputs accepted by that reference.
Deliver the static-solid interoperability proof first and broaden coverage
before claiming full compatibility. The exchange prototype remains research
evidence. [Task 0045](tasks/0045-supported-project-persistence.md).

D056 — Accepted generated-artifact retention/cleanup, 2026-11-03: maintainer
reports task 0044 seems to work and requests removing unnecessary tested apps/
DMGs before proceeding. Older keep-tested-DMG instructions are superseded for
generated payload retention. Prune reviewed ignored historical package/test/cache
copies; preserve source, tracked evidence, small provenance, jobs/private models,
installed user app/state and useful shared build inputs. Keep at most the current
image while needed for user testing; remove it after confirmation. Record removed
availability and actual space; historical hashes are not current payload presence.
No security/uninstall/application/format/frontend/numerical change or release-gate
closure. [Task 0046/report](reports/storage-cleanup.md); task 0045 remains next.

D055 — Accepted first editable solid desktop slice, 2026-11-03: maintainer
requests proceeding after task 0043. Task 0044 edits the existing bounded static
definition through a model tree/Qt controls and original INP set inventory.
Original C# objects/writer validate and generate the deck; submitted mesh and
definition are frozen per job. This is session editing with retained run inputs,
not a new PMX format or supported project save/reopen. Imported named-set
assignments are supported; picked/new-set authoring remains pending. Original
solver/version/thread profile, engineering semantics, production frontend and
all correctness/four-target/release requirements remain. D051 publication scope
continues. [Actual implementation/evidence](reports/editable-solid-workflow.md).

D054 — Accepted parity target and ongoing open-source maintenance, 2026-11-03:
maintainer specifies PrePoMax 3.0.0 as the functionality target and intends to
follow future upstream releases while maintaining macOS/Linux distributions,
independently of whether upstream accepts the contribution. Preserve one shared
engineering implementation and required Windows x64/Linux x64/Linux ARM64/macOS
ARM64 targets. Track each exact upstream release, feature delta, compatibility
and native acceptance; do not equate an RC/source assembly version with verified
stable release correspondence. Task 0043 is now authorized for implementation.
Existing D051 publication and D053 local-preview boundaries continue; no silent
production frontend/persistence/backend choice or upstream communication.

D053 — Local Mac DMG before notarization, 2026-11-03: maintainer requests a
local-installable DMG while signing/notarization are unavailable and explicitly
chooses desktop solver controls before the first DMG. Task 0042 prioritizes a
bounded static mesh/analysis → native solve/cancel/status → FRD desktop preview
with relocated native runtimes and ad-hoc signing. Developer-ID/notarization and
clean-host/full release acceptance remain pending. This reorders the next slice
ahead of the remaining viewport binding attempt without choosing the frame-copy
bridge as production. Apple Linux containers cannot validate a Mac GUI/DMG.
Existing normal origin-research publication authorization continues; no security
setting/quarantine bypass or upstream/master/x/main/release write.

D052 — Accepted delivery-order/shared-source clarification, 2026-11-02:
maintainer requests maximum speed toward native macOS while designing for Windows
and Debian/Fedora/Arch Linux now, with later staged testing and ideally the same
source compiled for different targets. Keep one application/engineering source
tree and target-specific adapters/build/package data; retain all four OS/CPU
targets including Linux ARM64. [Task 0039 plan](proposals/accelerated-native-delivery.md)
proposes the sequence and test cadence; it does not select a frontend/format/
production backend or claim distro/version/runtime acceptance. The reported CI
failure needs exact job evidence; no assumed diagnosis or tolerance/test weakening.
Task 0039 changes documents only; existing D051 checkpoint publication scope stays.

D051 — Accepted implementation continuation and checkpoint publication,
2026-11-02: maintainer explicitly requests proceeding with the next desktop-host
and native solver steps, documenting progress and committing/pushing useful
work. Reviewed checkpoints may publish normally to origin/research/native-feasibility,
with remote/CI verification. Earlier uncommitted restrictions are historical for
this continuation; no upstream/master/x/main/release write, force push, numerical
policy/default format or production frontend selection is implied.

D050 — Accepted delivery priority and lighter development cadence, 2026-11-02:
maintainer confirms native installable software as the main goal, treats
Code_Aster as optional, and requests less stringent repetition with cross-platform
testing/bug tracing. CalculiX/open backends remain primary; PARDISO need not block
initial delivery, while actual native capability/correctness remains unproved.
Use affected/current-source checks for routine progress; broaden for affected
numerical/interop/persistence behavior and at integration/release milestones.
Keep useful tests/tolerances, both known failures/tetra gate, pending-platform
honesty and final four-target/parity/package requirements. The concrete
[plan](proposals/accelerated-native-delivery.md) proposes an early internal
installer preview then an engineering alpha; it does not select a frontend,
format, native build/profile or numerical change. Task 0035 is planning only;
CI/application code stays unchanged, normal publication policy remains.

Maintainer reaffirmation, 6 November 2026: work in larger functional milestones
that deliver usable original feature families through the shared application.
Group related implementation into one substantial step; do not split each
transport, guard or UI control into a separate delivery task. During development,
reuse existing tests and run focused checks where they resolve a real risk or
failure. Run representative end-to-end and affected regressions at integration
boundaries; reserve full platform sweeps, repeated copied-app checks and package
rebuilds for meaningful candidate milestones. Add tests for substantive behavior
or defects, not every changed line. Report progress in completed user functions
and remaining functionality. Testing checks progress toward the working product;
it is not the project objective. Existing numerical expectations remain intact.

D049 — Accepted PrePoMac investigation and VM execution-option research,
2026-11-02: maintainer requests detailed solver/UI/Linux evaluation and is willing
to use a Linux VM on Mac if it provides better solver performance. This allows
evaluating optional solver workers; it does not choose a production worker,
backend/default/precision/frontend/renderer/serializer or close native desktop
targets. [Task 0034 report](reports/prepomac-evaluation.md) verifies source/release
fb5a89db and actual ZIP/bundled ARM64 2.23 solver metadata, plus bounded Mac
method/formula checks. Linux local diagnostics are not-run after infrastructure
failure. Code_Aster is a limited different-FEM-engine translation, not general
CalculiX parity; its SPOOLES-only package does not prove a general backend limit.
Native-VTK/shared-core retention and selective reuse are recommendations, not new
architecture commitments. Both correctness failures/tetra gate and all existing
release gates remain. Research stays uncommitted; normal publication policy.

D048 — Verified results publication and bounded evidence transport, 2026-10-18:
tasks 0030/0031 publish normally to origin research at 62c7de1b; remote verified,
master unchanged. Exact-commit pipeline #2960686368 passes all five native Linux
x64 jobs. Actual hosted artifact preview JSON identifies clean commit and ten
source/tool/package/test/FRD/DAT groups match both ARM64 hosts for all three pins,
78 checks/nine CLI controls each. Archive downloads unavailable; semantic preview
hash comparison is independently reproduced, not described as archive verification.
Task 0032 closes with records only. Normal maintainer publication policy resumes;
no correctness/release gate closure or native solver/default/frontend/format choice.
[Evidence and method](reports/results-publication.md).

D047 — Accepted bounded DAT implementation and scoped publication, 2026-10-18:
maintainer asks the next task then commit/push within remaining usage. Task 0031
reuses original DAT splitter/repair/numeric decoding and HistoryResultEntries,
mechanically preserving net48 orchestration/persistence. Static-shaped history
inspection keeps raw values and metadata with explicit guards; DAT completion
is not inferable. Task 0032 publishes completed tasks 0030/0031 and verifies
exact-commit hosted/artifact evidence normally on origin research only. Prior
uncommitted wording is superseded for this publication; no upstream/x/main/
release write/force or solver/default/precision/GPU/frontend/serializer choice.
Both correctness failures/tetra gate and all remaining release requirements stay.
[Implementation](reports/portable-dat-histories.md), [publication](reports/results-publication.md).

D046 — Accepted post-reset local results implementation, 2026-10-18: maintainer
explicitly resumes, lifting task 0029's stop. Task 0030 preserves original FRD
ASCII/binary decoding, field types/math and assembly ownership through mechanical
partials; bounded 3D C3D8 static snapshot/CLI rejects unsupported/incomplete/
ambiguous fields. Full legacy net48 orchestration remains; no unit inference or
global converter mutation. All three pins pass Mac/Linux ARM64: 39 results
checks/five CLI controls plus 331 accepted analysis regressions. Six results
source guards and prior guards pass; fingerprints/outcomes match. Both strict
correctness failures/tetra gate remain. Work stays uncommitted; no new publication
or native solver/default/GPU/serializer selection. Continue original DAT/full
results and reproducible native CPU solver work, retaining all release gates.
[Evidence](reports/portable-frd-fields.md).

D045 — Verified analysis/execution publication, 2026-10-18: tasks 0022–0028
published normally to origin/research/native-feasibility at 993f9263; remote
verified, master unchanged. Exact-commit pipeline #2960594131 passes all four
native x64 jobs. Downloaded analysis/execution reports match source/tools/
dependencies and retained Mac outcomes for all three pins. 331 accepted analysis
and 47 execution/planning checks per pin; both correctness failures remain.
Task 0029 closes with documentation/evidence only. Stop feature work until
maintainer resumes; all native solver/Windows/net48/RC2/release gates remain.
[Publication](reports/analysis-execution-publication.md).

D044 — Accepted bounded thread-planning implementation and publication,
2026-10-18: maintainer requests one small task within remaining usage then commit/
push current work and continue after reset. Task 0028 implements callable modern-
only CPU advice and read-only CLI; 47 checks/13 rejection controls pass each pin
on Mac/Linux ARM64, with tools/source/outcome comparison. No active scheduling,
settings migration or pinned reference-thread change. Task 0029 authorizes normal
origin research-branch publication of tasks 0022–0028 and closing hosted evidence.
Earlier leave-uncommitted restrictions are superseded for this publication only.
No x/main/upstream/release write, force push or solver/numerical-policy change.
Stop after publication/reset handoff until maintainer resumes. Both correctness
failures/tetra gate and all release requirements remain.
[Implementation](reports/portable-thread-planning.md), [publication](reports/analysis-execution-publication.md).

D043 — Requested solver advice/thread product direction; GPU research,
2026-10-18: maintainer asks for recommendations by analysis and 75% available
CPU threads, with research into NVIDIA/AMD/Apple GPU support and candidate native
libraries. Task 0027 is research/design only. Propose capability/evidence-aware
advice, manual override and max(1,floor(0.75*available logical CPUs)) shared across
jobs; it is not a utilization cap or speed guarantee. Existing SPOOLES/modified
PaStiX first, MUMPS only if required under D042. NVIDIA CUDA paths documented;
AMD HIP via SuperLU_DIST requires integration; no reviewed Apple Metal direct-
solver path identified. No new library/default/precision/affinity/GPU policy is
implemented or benchmarked; detailed rule table/rounding/order are proposals.
No publication. Preserve both correctness failures/tetra gate and all release
requirements. [Research and proposal](reports/solver-guidance-threads-gpu.md).

D042 — Accepted licensing/functionality criterion; research recommendation,
2026-10-18: maintainer rejects Panua machine-fingerprint licensing and requires
a new alternative only if omission of PARDISO cripples useful functionality.
This narrows D041's prior all-backend identity requirement; preserve original
CalculiX engineering semantics and transparent capability reporting. Research
recommends existing SPOOLES/PaStiX evaluation before another backend integration.
No PARDISO-exclusive analysis class was identified in reviewed paths, but native
correctness/capacity/performance are not accepted. In original 2.22 source,
PaStiX modal/buckling selections can use PARDISO when both macros are defined.
Own comparisons are deferred; no solver/default/precision/architecture changes
or publication are performed/selected. Both correctness failures/tetra gate and
all release requirements remain. [Assessment](reports/without-pardiso-assessment.md).

D041 — Verified exact RC2 solver identity, native full-stack decision pending,
2026-10-18: task 0025 proves RC2 uses the unchanged official CalculiX 2.22 Windows
executable and the same five runtime DLLs as the recorded reference. Six backend
choices pass the bounded cube through existing Mac CrossOver; no native ARM/full
solver acceptance. Canonical core source/provider and GUI PARDISO default are
identified. Exact static-library revisions/build/ABI recipe remain incomplete;
Intel MKL/PARDISO has no identified native ARM64 distribution. Maintainer requires
complete identical software: do not hide this through dropped/rewritten solver
choices or a substituted backend. Exact-binary compatibility/worker execution
and native alternative dependencies need an explicit architecture/policy choice,
not inferred approval. No production change/contact/publication occurs.
[Research report](reports/exact-solver-provenance.md).

D040 — Verified bounded native job/source recovery, 2026-10-18: task 0024 keeps
original job/enum/monitor ownership and net48 methods, adds a modern platform
partial/CLI and organized unchanged CalculiX 2.22 source. Current/RC2/post-RC2
pass 33 new process/preflight/monitor checks and four CLI controls on Mac/Linux
ARM64; four mechanical guards pass. Matching native solver/PaStiX/BLAS/patch/ABI/
runtime source chain remains open; no native solve or alternate solver/backend
is accepted. Linux checks require an init reaper; earlier analysis fingerprints
and both correctness failures remain. Work stays uncommitted. Continue original
FRD/DAT field import and source/build recovery, retaining all release gates.
[Evidence](reports/native-job-boundary.md).

D039 — Accepted final repository/source and release organization, 2026-10-18:
maintainer requires all third-party sources in appropriate folders and a public
release branch serving Homebrew/other package managers and native installers.
REPOSITORY_LAYOUT.md records the readable map, additive ThirdParty/Sources
recovery, separate patches/build/cache/artifact areas and planned x/release lane
with immutable versioned artifacts. No public branch/push is performed; original
upstream paths and exact-source/native build/release gates remain. Continue local
implementation under the accepted solver/results sequence.

D038 — Verified bounded complete static deck, 2026-10-18: task 0023 reuses
original section/BC/load/static-step/output types/writers behind mechanically
checked core/legacy partials. The explicit-unit no-overwrite CLI preserves the
analytical cube's IDs/material/12 constrained DOFs/100 N force/output semantics.
Current/RC2/post-RC2 pass 331 accepted checks per build on native Mac/Linux ARM64;
source/dependency/tool/outcome fingerprints match. Nine analysis/ten replay guards
and independent offline-core checks pass. Managed Color retains only Primitives;
full net48/Windows remains unverified. Both original correctness failures/gate
remain. All task 0022/0023 changes are uncommitted. No solver is executed here;
continue matching native execution/results under accepted D036 and all release
gates. [Evidence](reports/static-analysis-deck.md).

D037 — Verified bounded equation/material component, 2026-10-18: task 0022
source-links original types/algorithms and exact upstream NCalc/UnitsNet versions
in an isolated expanded build. Native Mac/Linux ARM64 current/RC2/post-RC2 pass
262 accepted checks/eight material CLI controls with both known failures/gate
retained. Original post-RC2 lamina/composite changes are separately pinned and
exercised; no numerical fix is imported into the baseline. Formatting extraction
and four unused-import removals preserve original net48/type ownership. This
local component writes a material fragment, not a full analysis deck or installer.
CI is prepared, new Windows/hosted execution pending; no publication authorized.
Continue the accepted sequence and retain all release delivery/compatibility gates.

D036 — Accepted next implementation and installable desktop objective,
2026-10-18: maintainer accepts proposals/next-native-workflow.md. Proceed through
original model/deck, matching native solver and original result readers in tested
increments; Windows can follow local portable coding. Task 0022 begins equations/
materials. End-user delivery requires Windows EXE/MSI, macOS DMG, Linux DEB/RPM
or equivalent and Homebrew across the required architectures. Apple Developer ID
will be available if needed. RELEASE.md records installation/upgrade/signing/
clean-machine acceptance. No new publication, frontend/default serializer,
algorithm/tolerance or silent tool-version decision. D034/D035's stop is lifted
for this accepted sequence; all correctness/native Windows/release gates remain.

D035 — Verified publication, proposed implementation remains unapproved,
2026-10-18: task 0019/0020 published at 47f17be6; pipeline #2960334103 passes
both native Linux x64 jobs. Downloaded evidence and source/tool/125-entry ZIP
checks match the published source and retained Mac outcomes. Task 0021 closing
changes are documentation/evidence only. Proposed model/deck → native solver →
results sequence is recorded in proposals/next-native-workflow.md; wait for
maintainer approval. Native Windows and all correctness/release gates remain.

Use accepted/proposed/deferred labels; a proposal in a spec is not an architectural commitment.

D034 — Accepted publication, new implementation awaits approval, 2026-10-18:
maintainer requests committing/pushing task 0019/0020 work and receiving a next-
step explanation afterward. Task 0021 authorizes normal origin research-branch
publication plus exact-commit CI/artifact verification and closing evidence.
Do not start proposed model/deck/solver/results or host/persistence features
until the maintainer reads and approves them. Keep both correctness failures/
measurement gate, source ownership and remaining release gates unchanged.

D033 — Accepted local implementation continuation, 2026-10-18: maintainer asks
to proceed while preparing Windows for GitLab. Task 0020 delivers original INP
mesh parsing through a mechanically checked partial reader and a CaeModel
library slice, original element deck formatting, explicit input/output adapters
and a usable mesh CLI. Preserve original assembly/net48 ownership and algorithms;
separate framework-only StandardValueAttribute unchanged from its UI editor.
Mac/Linux ARM64 current/RC2/post-RC2 pass 218 accepted checks/39 CLI controls
with two original correctness failures retained. New source/binary package and
Windows follow-up are prepared. All implementation stays uncommitted; no frontend/
default serializer, x/main, publication, native-tool or numerical-policy change.
Mesh-only completion does not establish full model/deck/solve/results parity.

D032 — Accepted RC2 sync/implementation continuation, 2026-10-18: maintainer
requests syncing the fork, comparing Matej's 3.0.0 RC2 and accelerating coding
toward a cross-platform release near upstream stable. Task 0019 supersedes the
0018 stop for this continuation. Sync origin/master by normal ff-only update
to f6273e39; preserve RC2 marker 912fb3d0 separately from later composites work.
Add reviewed snapshot replay while retaining baseline/source/behavior gates.
Further implementation/evidence remains uncommitted under normal workflow;
no x/main merge, upstream write, force push, frontend/default serializer or
numerical/tolerance/native-tool substitution is selected. Whole-application
release parity remains open. Use a real mesh/deck/solve/results workflow as the
recommended next implementation milestone; host/persistence choices need proof.

D031 — Verified element/build publication, 2026-10-16: b83fa49f is pushed and
remote-verified; pipeline #2956835416 passes both native x64 jobs. Downloaded
framework-dependent ZIP has verified source/tool fingerprints and rebuilds/runs
on Mac ARM64. Both open original-source correctness failures remain, with the
tetrahedron host gate. Task 0018 closes within its budgeted scope; no broader
feature, numerical-policy, frontend/serializer or integration decision follows.

D030 — Accepted bounded publication/build-delivery task, 2026-10-16: maintainer
requests committing/pushing task 0017 and a small task within 20% of the
five-hour allowance. Task 0018 delivers the existing framework-dependent core
ZIP through native x64 CI with checksum/source-rebuild/CLI/gate verification.
Retain the two numerical/classifier failures; no algorithm, frontend/default
format, native-tool or integration policy is selected. Stop at this boundary.

D029 — Local element-kernel increment, 2026-10-16: under the maintainer's
continued-build instruction, task 0017 source-links original element families
and GeometryTools with one exact unused WinForms import removal, preserving
algorithms/type ownership. Mac/Linux ARM64 accepted-scope checks pass, but two
strict original-source correctness failures remain: quadratic tetra integration
bias and missing pyramid classification. Retain failures/source-moment evidence;
gate quadratic tetrahedra in the development host instead of changing numerical
code/tolerances. This is not full element acceptance. The runnable CLI/source
bundle is local; new Windows/x64 and existing release gates remain pending.

D028 — Verified data-slice publication/native x64 acceptance, 2026-10-16:
236b1a2e is pushed and remote-verified. Pipeline #2956740201 passes both jobs;
the downloaded shared-core artifact independently matches published source/tool
hashes and ARM64 mapping/data/type/CLI outcomes. Native Windows execution of
this new assembly slice is still pending; earlier probe data agreement is not
a substitute. Task 0016 includes this closing evidence publication.

D027 — Accepted publication/implementation continuation, 2026-10-16: maintainer
requests committing/pushing completed task 0015 and continuing toward a working
build. Task 0016 publishes the reviewed increment and its hosted evidence to
origin/research/native-feasibility. Continue shared engineering implementation
incrementally; no frontend/default serializer, x/main, upstream write, forced
history or silent native-tool substitution is selected. The encouraging earlier
CrossOver/native Windows payload agreement remains scoped evidence.

D026 — Accepted Mac continuation, 2026-10-16: maintainer authorizes exact-range
Windows bundle import/publication and the handoff's bounded shared data increment.
Reviewed ac51fc77 is remotely verified; both hosted native x64 jobs pass.
First shared mapping libraries now pass all four targets within scope. Task
0015 retains metadata/scaling in CaeMesh and the internal FRD utility in CaeResults;
existing 30 data checks match Windows observations on native Mac/Linux ARM64.
New increment stays uncommitted and needs native Windows/new-commit x64 follow-up.
This does not choose serialization/UI or close full persistence/history/CAD/VTK/
native-source/compiler-policy gates. No further implementation push is authorized.

D025 — Accepted Windows closeout/publication instruction, 2026-10-16:
maintainer explicitly authorizes committing/pushing reviewed Windows/reference/
shared-core work to origin/research/native-feasibility and preparing immediate
MacBook continuation. Task 0014 includes closing evidence and transfer fallback.
No force push, upstream write, x/main integration or frontend/serializer choice.
Windows-only checks needed for this increment are complete; Mac/Linux execution
of the new libraries is next. Remote publication and hosted CI must be verified,
not inferred from local commits or configuration.

D024 — Bounded implementation authorized, 2026-10-16: maintainer requested
finishing supplied-model testing and proceeding to build. Task 0013 starts
partial source-linked shared libraries and a callable mapping host on the
planned branch. Mechanical CaeException separation removes the proven Windows
presentation dependency while retaining existing code/type/assembly identity.
The tested PMX comparison supports proceeding with this limited slice; it does
not establish a portable serializer or complete platform acceptance. Frontend,
full Controller extraction, native integration, x/main and publication stay
outside the current implementation. Preserve remaining release gates.

| ID | Status | Decision / rationale / revisit condition |
|---|---|---|
| D001 | Phase 0 completed; scoped authorization advanced | Phase 0 stayed documentation/repository maintenance only. Maintainer authorized task 0002 on 2026-10-13; broader implementation still requires review |
| D002 | Accepted by task scope; locally established | Keep `master` as clean ff-only upstream mirror, `x/main` separate, Phase 0 on feature/project-initialization; no push/merge without approval |
| D003 | Provisional observation | Analyze master at de8f73032a72746e3d6d9afd53d9fbd289eb310a; stable 3.0 is not yet available. Switch baseline using the audit's release-correspondence and regression gate |
| D004 | Proposed, maintainer approval required | Strategy C transition with Strategy A discipline: retained Windows frontend, shared source/behavior, narrow platform services; avoid independent FEM/controller fork |
| D005 | Proposed, proof required | Preserve VTK filters/ID mapping/selection; select an open-source binding/host after native interactive experiment and license review |
| D006 | Deferred | GUI framework: compare a C# frontend/VTK route with PyQt6 + Python VTK + shared C# backend as full production candidates; decide only after VTK/DPI/input/data-exchange/required-platform proofs |
| D007 | Experiment target accepted; production target deferred | Task 0002 uses net10.0 for a bounded seven-file probe. Production core/build boundaries require broader dependency and file-format evidence |
| D008 | Deferred, critical | Legacy compatible PMX/PMH/settings/material reader/writer and clone strategy; preserve serialized identities initially. No unsupported BinaryFormatter dependency silently introduced |
| D009 | Required before parity implementation/release | Recover matching custom native sources/patches and exact solver/CPython/runtime pins; don't substitute stock binaries and claim equivalence |
| D010 | Proposed | Per-field fixture-based tolerances, exact semantic comparisons, native target runners and Windows oracle; acceptance thresholds need measured repeatability and review |
| D011 | Maintainer Git workflow accepted; other actions deferred | Maintainer normally handles commits/pushes. The 2026-10-14 continuation explicitly authorizes agent commits/origin pushes for task 0002 closing evidence and the next bounded probe/investigation; default maintainer workflow resumes afterward. x/main integration, protected-branch policy, scheduled Hermes work and publishing remain separate approval actions |
| D012 | Accepted, explicit maintainer instruction | Use PrePoMax-X and X/x project naming throughout; the local integration branch is named x/main. Apply this convention to future project documentation, tooling and branches |
| D013 | Bounded task complete, verified 2026-10-14 | Task 0002 on feature/core-feasibility: source-linked STL/vector/node probe, source hash/closure manifest and replay. Mac ARM64, Podman Linux ARM64 and GitLab native Linux x64 pass both source pins, with matching portable observations. Pipeline #2947482796 at 822bae25; see native x64 report. No GUI choice, whole-core portability claim or feature integration authorization |
| D014 | Authorized and performed locally | Reviewed Phase 0 records fast-forwarded into x/main at c840aceb; implementation branch created from it. Maintainer later pushed feature commit 92a491cd; feature implementation is not integrated into x/main |
| D015 | Updated authorization 2026-10-14, explicit maintainer instruction | Retain local Podman testing and prepare complementary GitLab native Linux x64 CI (supersedes the earlier local-only instruction). Retain image/runtime/source provenance and compare structured results. Translated amd64 on an ARM VM is supplemental evidence, not native Linux x64 acceptance. CI configuration/local rehearsal is not a hosted pass |

| D016 | Bounded proof complete 2026-10-14 | Task 0003 on feature/core-data-feasibility: dependency/compiler boundaries, unchanged six-file Matrix/metadata/scaling/FRD-stream probe and PMX source-identity/Windows capture preparation. Mac ARM64 and native Linux x64 pass 30 checks plus two CLI contracts with matching observations; actual Windows capture/PMX compatibility remain pending. No full reader, production serializer or x/main integration commitment |

Review requested at handoff: approve/adjust D004 and the bounded feasibility tasks 1.1/1.2/2.1 plus source recovery 5.1. D005–D008 remain gates rather than immediate commitments. The maintainer handles commits and pushes; agents must not ask to push as a prerequisite for local verification.

D017 — Bounded pre-Windows investigation authorized and audit completed,
2026-10-14: maintainer authorized progressing through the proposed steps,
starting with native source/build feasibility and stopping at completed task
boundaries before usage runs out. Task 0004 records native header/interop checks
and matching-source gaps; native-source recovery/full builds remain open.
No production dependencies, frontend/interop decision, F001 implementation,
x/main integration or commit/push permission follows from this continuation.

D018 — Bounded proofs complete 2026-10-14: task 0005's native structured kernel
and unchanged managed count/grid slice pass on Mac ARM64; task 0006's isolated
Python VTK 9.5.2 synthetic rendering/picking passes 14 checks and exposes clipping
ID loss; task 0007 defines four checked shell-junction fixtures. These establish
specific contracts, not whole-core/native-tool/UI parity. Full C# mapping reaches
the ExceptionTools/MessageBoxes boundary. GUI/binding and F001 implementation
choices remain deferred; Windows/native source/platform gates stay open.

D019 — Research authorization and legacy evidence, 2026-10-15: maintainer
supplied a PMX and accepts investigating an adjusted cross-platform schema with
eventual upstream contribution in mind. Task 0008 decodes actual 2.5.1-dev
records without application reconstruction; production schema remains undecided.
Task 0009's isolated CrossOver Windows 2.6.0 read/save/reopen is human-confirmed,
with guarded byte comparisons and explicit NRBF changes. Native platform/full
semantics remain open. No commits/pushes, messages or PR publication authorized.

D020 — Bounded Linux PMX repetition complete, 2026-10-15: task 0010 passes
24 synthetic tests and both private record inventories on native-architecture
Linux ARM64 in Podman. Portable observations match Mac exactly; one additional
runtime support assembly is guarded separately. No semantic persistence, history,
Windows/Linux x64 or production-format conclusion follows. Preparation exit
gates define next research, with semantic snapshots/history as the next priority.

D021 — Accepted maintainer target correction and next-session handoff,
2026-10-15: required targets are Windows x64, Linux x64, Linux ARM64 and Apple
M-series macOS ARM64. Maintainer explicitly clarified “x86” as 64-bit Intel/AMD.
Intel Macs and 32-bit x86 are excluded; Linux ARM64 is required. This supersedes
the initial target matrix and lower-priority ARM Linux statements in historical
reports. Windows is expected next session; task 0011/handoff are prepared with
capture pending. Uncommitted research must be carried to that checkout; no new
commit/push/integration or architectural-choice authorization.

D022 — Accepted local completion/publication instruction, 2026-10-15: maintainer
explicitly authorizes completing feasible local preparation then committing and
pushing reviewed research to origin. Task 0012 includes hosted evidence follow-up
and ends this exception; later commits/pushes need a new instruction. No upstream
write, force push, x/main integration, frontend/default-format choice or broad
production change. Selected PMX scalar comparisons expose job settings drift;
Linux ARM64 mapping is contraction-sensitive; VTK provenance/lifecycle and the
bundled 2.22 analytical solver reference pass within bounded scopes. None closes
native Windows, full semantics/history, native-source or production-policy gates.

D023 — Verified research publication/native x64 evidence, 2026-10-15:
24c790ac published to origin/research/native-feasibility; push pipeline
#2951491552/job #17205619186 passes on AMD EPYC 9B45 with compiler defaults.
Six downloaded artifacts independently checked. Task 0012 is complete within
its bounded investigation/publication scope; closing evidence publication ends
the scoped agent commit/push exception. Task 0011 remains the next native Windows
checkpoint; no production/integration/format/GUI decision follows.

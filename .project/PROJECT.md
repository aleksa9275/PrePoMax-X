# PrePoMax-X project charter

2026-11-03 local preview: task 0042 delivers a local ad-hoc-signed, unnotarized
Mac DMG with desktop solver controls, relocated native CPU runtimes and full
uninstall/reset instructions. Exact-source copied-app solve/render/analytical
checks pass; b6ec65d7 pipeline 3020068825 passes six automatic Linux x64 jobs.
This internal static-solid preview is not full PMX/CAD/meshing or clean-OS/release
acceptance. [Artifact and actual evidence](reports/local-macos-dmg.md).

2026-11-03 shared-build checkpoint: task 0041 implements the common four-RID entry,
Mac/Linux native solver adapters and Mac package wrapper. Implementation a893005c
passes exact-commit Linux x64 CI; downloaded cube/native-source evidence compares
with Mac. Windows/Linux ARM64 publications are compile-only. The next desktop
increment remains a bounded viewport binding attempt and Mac workflow, with
clean-machine/runtime/signing and other native targets pending.
[Actual evidence/publication](reports/shared-target-builds.md).

2026-11-02 CI closeout: task 0040 repairs the shared exporter regression at
f4e388a5. Exact-commit Linux x64 pipeline 3019257012 passes all five automatic jobs;
downloaded Core fingerprints and development package bytes verify. [Evidence](reports/core-pipeline-regression.md).
The shared-source/macOS-first sequence resumes with its target/build entry;
desktop/distro/full release acceptance and both correctness failures stay open.

2026-11-02 delivery clarification: macOS ships first from shared source with
Windows x64 and Linux x64/ARM64 built into the architecture. Debian/Fedora/Arch
are packaging/test environments, not separate application implementations.
[Revised sequence](proposals/accelerated-native-delivery.md), task 0039, keeps
Linux engineering feedback early and broad desktop/install testing at checkpoints.
The reported failed GitLab job requires its actual log before diagnosis.

2026-11-02 engineering checkpoint: [native CPU workflow](reports/native-cpu-workflow.md)
completes the bounded original deck/solve/results path on Mac ARM64, and a
[packaged native viewport candidate](reports/native-desktop-preview.md) displays
its results. Real integration found B001 (fixed) and B002 (direct embedding open).
Explicit research build profiles and the candidate frame bridge do not choose
production solver/frontend defaults. [STATUS](STATUS.md) records checks and
publication; final platform/functionality/release requirements remain.

2026-11-02 priority: deliver installable native software faster, with CalculiX
primary and Code_Aster deferred. [Delivery plan](proposals/accelerated-native-delivery.md)
brings desktop/packaging integration forward and replaces repeated daily full
matrices with affected checks and milestone coverage. Final capabilities,
correctness and four-target delivery remain; [current status](STATUS.md) tracks
the next implementation. No frontend/default format/solver profile is selected.

2026-11-02 continuation: maintainer requests detailed PrePoMac comparison and
permits considering a Linux VM on Mac for better solver performance. The
[evaluation](reports/prepomac-evaluation.md) pins source/release fb5a89db and
verifies its ZIP and bundled ARM64 CalculiX 2.23 metadata. It identifies useful
desktop/Linux/packaging work, a limited Code_Aster static translator and remaining
renderer/model/resource/lifecycle differences. VM evaluation is not a production
worker/backend/frontend selection; no solver/performance acceptance or integration
occurs. Original shared behavior, both correctness failures/tetra gate and all
four-target/desktop/release requirements remain. Changes are local/uncommitted.

2026-10-18 results publication: tasks 0030/0031 implementation **62c7de1b** is
on origin research; exact-commit pipeline **#2960686368** passes all five native
Linux x64 jobs. Hosted FRD/DAT artifact previews verify against Mac/Linux ARM64
sources/tools/engineering outcomes, 78 checks/nine CLI controls per pin. Archive
transport was unavailable; do not claim archive-byte checks. [Publication/evidence](reports/results-publication.md)
closes task 0032 without feature expansion. Both correctness failures/tetra gate
and all native solver/Windows/net48/RC2/full-desktop/release requirements remain.

2026-10-18 task 0031/0032: maintainer requests the next bounded task and explicit
commit/push. Original DAT parsing/history entries now support stored static-shaped
component histories/inspect-dat, preserving net48 orchestration/persistence. DAT
cannot establish job completion. Publish together with task 0030 FRD work under
the scoped [publication task](tasks/0032-results-publication.md). [DAT evidence](reports/portable-dat-histories.md)
and [actual publication/CI](reports/results-publication.md) distinguish local and
hosted acceptance. Both correctness failures/tetra gate and all release gates
remain; no solver/frontend/default/format/GPU choice follows.

2026-10-18 resumed implementation: task 0030 provides original-owned FRD
C3D8 static mesh/field inspection and original derived invariants. ASCII and
binary float/double checks pass all three pins on native Mac/Linux ARM64:
39 results checks/five CLI controls plus 331 accepted analysis regressions per
build; both known correctness failures/tetra gate remain. [Evidence](reports/portable-frd-fields.md).
Legacy net48 orchestration is preserved; full FeResults/DAT/native solver remain
next. Work is local/uncommitted; no new publication or policy choice. The older
task 0029 stop is lifted by the maintainer's explicit post-reset continuation.

2026-10-18 publication verified: tasks 0022–0028 implementation is published at
993f9263; exact-commit pipeline #2960594131 passes all four native Linux x64
jobs. Downloaded three-pin analysis/execution reports match published source/
tools/dependencies and retained Mac outcomes. Task 0029 closing evidence is
recorded in [publication/reset handoff](reports/analysis-execution-publication.md).
Stop feature work until maintainer resumes. Both correctness failures and all
native solver/Windows/net48/RC2/four-target/full-workflow/installer gates remain.

2026-10-18 latest: maintainer authorizes bounded task 0028 then committing/pushing
all tasks 0022–0028 and stopping until continuation after reset. Portable CPU
planning/CLI passes 47 checks/13 rejection controls per pin on Mac/Linux ARM64;
no running scheduler/settings/reference-thread change. [Implementation](reports/portable-thread-planning.md).
Task 0029 [publication/reset record](reports/analysis-execution-publication.md)
covers normal origin research publication and actual hosted verification. Earlier
uncommitted-only restrictions are superseded for this publication; no x/main/
upstream/release write, force push or numerical-policy change. All gates remain.

2026-10-18 latest, task 0027/D043: maintainer requests solver advice by analysis
and a 75% available-thread default, plus GPU feasibility research. The
[research/design](reports/solver-guidance-threads-gpu.md) distinguishes existing
backends from future adapters, proposes explained recommendations/manual override
and a coordinated thread budget, and documents NVIDIA/AMD/Apple differences.
No production/default/precision change, new benchmark or publication. CPU-native
delivery first remains recommended; MUMPS/new adapters conditional under D042.
Both correctness failures/tetra gate and all release requirements remain.

2026-10-18 latest, task 0026/D042: maintainer excludes machine-bound Panua
licensing and requires a new alternative only if omitting PARDISO cripples
functionality. This narrows the earlier all-backend identity requirement below.
[Assessment](reports/without-pardiso-assessment.md) recommends evaluating existing
CalculiX SPOOLES/PaStiX before adding another backend. No PARDISO-exclusive
analysis class was found in reviewed paths; correctness, memory/capacity and
practical performance remain open. Actual modal/buckling dispatch needs special
care. Own comparisons are deferred; no production/default/precision change,
publication or new backend integration occurs. All release gates remain.

2026-10-18 latest: task 0025 exact solver research proves RC2 uses the unchanged
official CalculiX 2.22 Windows executable and previous five runtime DLLs. Six
choices pass the synthetic cube through existing Mac CrossOver, not native ARM.
[Research report](reports/exact-solver-provenance.md) identifies original binary
provider/core source, PARDISO GUI versus PaStiX executable defaults, missing exact
static-library build recipe and native ARM Intel MKL/PARDISO gap. Maintainer
requires complete identical software; no silent solver/backend change or implied
remote/compatibility architecture choice. This increment is research/report only;
all work remains uncommitted and existing correctness/release gates remain.

2026-10-18 continuation: task 0024 adds a tested portable native process/solver
preflight and original STA/CVG boundary, with all three pins passing 33 new
checks on Mac/Linux ARM64. [Current evidence and native solver blocker](reports/native-job-boundary.md).
Official CalculiX 2.22 source is recovered; matching native build/patch/runtime
provenance and actual numerical solve remain pending. All local changes stay
uncommitted. Maintainer explicitly requires an organized final repository with
all third-party sources and a public release branch for packages/package managers;
[repository map](REPOSITORY_LAYOUT.md) records the layout and planned x/release
lane. Continue accepted original FRD/DAT/results and native-source/build work.

2026-10-18 accepted direction: maintainer approves the next model/deck → native
solve → results sequence and makes native desktop installation an explicit end
goal. Required deliverables are Windows x64 EXE/MSI, macOS ARM64 DMG and Linux
x64/ARM64 DEB/RPM or similar, plus Homebrew installation. See [release delivery](RELEASE.md).
Apple Developer ID enrollment can be provided. Tasks 0022/0023 now generate a
bounded complete static deck through original model types/writers. All three
pins pass on native Mac/Linux ARM64 (331 accepted checks per build); both known
correctness failures remain. [Current evidence](reports/static-analysis-deck.md).
Implementation is uncommitted. Continue matching native solve/results locally
without further approval stops between accepted increments. No new publication
authorization.
The task 0021 approval stop and older uncommitted checkpoint text are historical.

Latest checkpoint: task 0019/0020 is published at **47f17be6**; exact-commit
pipeline #2960334103 passes both native Linux x64 jobs and downloaded evidence/
source/package independently verify. Task 0021 closes publication. New feature
work must wait for approval of [the next sequence](proposals/next-native-workflow.md).
Earlier uncommitted/continue descriptions below are historical; both original
correctness failures and all release gates remain.

2026-10-18 publication: maintainer requests committing/pushing completed RC2
replay and mesh workflow work under [task 0021](tasks/0021-mesh-workflow-publication.md).
Verify the remote/CI/artifacts and publish closing evidence, then explain the
proposed next steps and wait for approval before new implementation. Existing
correctness and release gates remain. [Publication state](reports/mesh-workflow-publication.md).

2026-10-18 implementation: [task 0020](tasks/0020-portable-mesh-deck-workflow.md)
adds reusable original INP mesh input, a CaeModel library slice and an actual
mesh inspect/measure/export CLI. Native Mac/Linux ARM64 and both upstream pins
pass 218 accepted checks per run, with both correctness failures retained.
[Current behavior, source boundaries and Windows follow-up](reports/portable-mesh-deck-workflow.md).
Implementation remains uncommitted; the complete solve/results/native UI/
persistence/CAD workflow remains under development and release gates stay open.

2026-10-18: maintainer authorizes a fresh RC2 fork sync/impact review and faster
implementation toward upstream 3.0.0. Task 0019 supersedes the prior stop for
this continuation. Local/origin master now mirror f6273e39 (22 new commits,
including 12 through RC2 and ten afterward). Both source pins pass the selected
shared slice on native Mac/Linux ARM64 with existing correctness failures retained.
Implementation/evidence stays local; no x/main/frontend/serializer/release
decision follows. [Current impact and priorities](reports/upstream-3.0.0-rc2.md).

Current checkpoint: task 0017/0018 is published at b83fa49f and pipeline
#2956835416 passes both native x64 jobs. A verified CLI/source development ZIP
is downloadable from its job; actual downloaded source/hash checks and Mac
execution also pass. [Evidence](reports/shared-core-build-delivery.md).
Stop at this task boundary; native Windows/new correctness/release gates remain.

Publication continuation: maintainer requests commit/push of task 0017 and
one small task within the stated allowance. Task 0018 makes the runnable core
ZIP available as a verified native x64 CI artifact, without changing numerical
algorithms or release gates. Earlier uncommitted-only statements are historical.

Local build checkpoint: [task 0017](tasks/0017-shared-element-kernel.md) delivers
a runnable measurement/mapping CLI bundle and original finite-element source
closure, tested on Mac/Linux ARM64. It remains uncommitted. Two original-source
correctness checks fail and remain explicit; quadratic tetrahedra are gated in
the host. [Current evidence](reports/shared-element-kernel.md). This is progress
toward the native application, not a full GUI/CAD/persistence/release build.

Publication checkpoint: task 0015 is now committed/pushed as 236b1a2e;
pipeline #2956740201 passed both native Linux x64 jobs, with downloaded source/
tool/outcome verification. Task 0016 closes this publication; expanded native
Windows remains pending. [Evidence](reports/shared-core-data-publication.md).
The maintainer requests continued bounded engineering implementation toward
a working build; frontend/default format/integration/release gates remain.

Current checkpoint, 2026-10-16 Europe/Belgrade: reviewed Windows ac51fc77 is
published and exact-commit pipeline #2956616374 passed both native x64 jobs.
The first shared slice now passes all four required platforms. [Task 0015](tasks/0015-shared-core-data-slice.md)
adds unchanged metadata/scaling/FRD-stream source to their original partial
assemblies and passes existing data contracts on Mac/Linux ARM64. Its changes
remain uncommitted; native Windows/new-commit x64 follow-up is pending.
[Current evidence and next steps](reports/shared-core-data-slice.md).
Earlier publication/pending paragraphs below retain historical checkpoints.

Current entry point: [MacBook continuation](handoffs/macbook-next-session.md),
[task 0014](tasks/0014-windows-publication-mac-handoff.md). The maintainer now
authorizes committing/pushing the reviewed Windows/shared-core work and its
handoff. Native Windows C++ tests also pass both measured compiler modes.
Publication must be verified: Windows sandbox credential access is denied.
The handoff includes an exact-range Git-bundle fallback if necessary.

2026-10-16 implementation update: maintainer requested finishing the supplied
PMX comparison and beginning building. Native Windows now reproduces the
CrossOver model/results payload observations. [Task 0013](tasks/0013-shared-core-first-slice.md)
delivers the first partial shared libraries and mapping host, with bounded
existing-source changes; see [implementation evidence](reports/shared-core-first-slice.md).
This supersedes older research-only scope for that slice. Whole-application,
GUI/schema and release parity decisions remain separate. Work stays uncommitted
on research/native-feasibility; the maintainer controls publication.

Record updated: 2026-10-16, Europe/Budapest. Task 0011 now has a controlled native
Windows cube/import-history checkpoint; see its updated task and
[Windows report](reports/windows-reference-validation.md). Full Windows
acceptance remains open. Phase 0 and bounded tasks 0002–0010
are complete within their scopes; task 0012 completes further local preparation
and research publication, including native Linux x64 hosted evidence.
Later tasks establish native source/build
boundaries, structured-kernel execution, synthetic native VTK behavior and
shell-junction fixture contracts. Windows compatibility and full application/
native-tool parity remain open; feature integration and broader implementation
remain gated. Tasks 0008–0009 add actual PMX record inspection, schema research
and a user-confirmed original-application reference cycle through CrossOver.

PrePoMax-X is an open-source cross-platform adaptation of [PrePoMax](https://gitlab.com/MatejB/PrePoMax). Preserve FEM functionality, numerical meaning, file compatibility and the ability to follow upstream releases. Minimize permanent divergence; this project is not an independently developed FEM application.

Required release targets (maintainer clarification, 2026-10-15): **Windows x64,
Linux x64, Linux ARM64 and macOS ARM64 on Apple M-series**. The maintainer's
“x86” means 64-bit Intel/AMD (x64), not 32-bit x86. Intel Macs are outside scope;
Linux ARM64 is required, not optional. Native operation is the goal; Wine,
Windows VMs and Rosetta do not qualify as final portability solutions.

Naming convention: **PrePoMax-X**, with `X`/`x` for project-specific cross-platform names and prefixes. The long-lived integration branch is `x/main`.

The maintainer authorized task 0002 and promotion of reviewed Phase 0 records
into x/main. Tasks 0002/0003 remain on their feature branches; later research is
on research/native-feasibility. A new 2026-10-15 instruction explicitly authorizes
completing feasible local preparation and committing/pushing that research to
origin, including hosted evidence follow-up (task 0012). This scoped exception
ends with task 0012 publication; normal maintainer commit/push control resumes
afterward. Original production files/algorithms remain unchanged; no production
schema, GUI, dependency or integration choice is made. Keep Podman and
complementary GitLab native Linux x64 evidence; preserve history/uncommitted work.
Root GPL v3 and Matej Borovinšek's
attribution remain authoritative; notices/source obligations travel with components.

## Where to start

| Record | Responsibility |
|---|---|
| [MacBook continuation](handoffs/macbook-next-session.md), [task 0014](tasks/0014-windows-publication-mac-handoff.md) | Start here: shared-library native Mac/Linux runs, publication state and next bounded implementation |
| [Next Windows session](handoffs/windows-next-session.md), [task 0011](tasks/0011-windows-reference-validation.md) | Resume here when Windows becomes available; prepared, execution pending |
| [Task 0012](tasks/0012-local-preparation-completion.md), [local completion](reports/local-preparation-completion.md) | Scalar PMX comparisons, compiler sensitivity, VTK provenance/lifecycle, analytical solver and research publication |
| [Research Linux x64 acceptance](reports/research-linux-x64.md) | Passed native hosted suite on 24c790ac; implementation/artifact identities checked |
| [STATUS](STATUS.md), [task 0001](tasks/0001-initial-repository-audit.md), [completed task 0002](tasks/0002-core-feasibility.md), [task 0003](tasks/0003-core-data-feasibility.md) | Current state, verification, handoff and first runnable milestone |
| [initial audit](reports/initial-audit.md) | Repository/baseline facts and investigation limits |
| [ARCHITECTURE](ARCHITECTURE.md) | Existing project graph and reuse evidence |
| [DEPENDENCIES](DEPENDENCIES.md), [dependency matrix](reports/dependency-matrix.md) | Native/managed inventory and supply-chain gaps |
| [Task 0004](tasks/0004-native-feasibility.md), [native feasibility](reports/native-feasibility.md) | Matching-source access, binary identity and measured native interop/build boundaries |
| [Task 0005](tasks/0005-structured-meshing-feasibility.md), [structured meshing](reports/structured-meshing-feasibility.md) | Unchanged native mapping execution, managed count/grid contracts and remaining compile boundary |
| [Task 0006](tasks/0006-vtk-native-smoke.md), [native VTK smoke](reports/vtk-native-smoke.md) | Synthetic native rendering and FEM-ID picks; full UI/platform parity remains open |
| [Task 0007](tasks/0007-shell-junction-fixtures.md), [shell fixture report](reports/shell-junction-fixtures.md) | Explicit F001 geometry/connectivity cases for later Windows/CAD mesher comparisons |
| [Task 0008](tasks/0008-pmx-record-inspection.md), [PMX inspection](reports/pmx-record-inspection.md) | Actual legacy record/type/reference inventory and bounded byte comparisons |
| [Task 0009](tasks/0009-crossover-reference.md), [CrossOver reference](reports/crossover-reference.md) | Original Windows app read/save/reopen, separate from native platform acceptance |
| [Task 0010](tasks/0010-pmx-linux-verification.md), [Linux PMX evidence](reports/pmx-linux-verification.md), [preparation exit gates](reports/preparation-exit-gates.md) | Repeated record inspection and prioritized remaining checks before implementation |
| [Schema proposal](proposals/portable-document-schema.md) | Versioned document/legacy compatibility direction; production format undecided |
| [PORTABILITY_AUDIT](PORTABILITY_AUDIT.md) | Obstacles and file-format contract |
| [MIGRATION_STRATEGIES](MIGRATION_STRATEGIES.md) | Alternative architectures and recommendation |
| [MIGRATION_SPEC](MIGRATION_SPEC.md) | Proposed interfaces and proof-of-concept gates |
| [TEST_STRATEGY](TEST_STRATEGY.md) | Equivalence tests and platform acceptance |
| [UPSTREAM_SYNC](UPSTREAM_SYNC.md) | Safe mirror and separate integration procedure |
| [ROADMAP](ROADMAP.md), [DECISIONS](DECISIONS.md) | Dependency-aware work and approval status |
| [Feature proposals](features/README.md) | Maintainer ideas and desired behavior, separate from approved implementation tasks |

Provisional analysis baseline: `de8f73032a72746e3d6d9afd53d9fbd289eb310a`, upstream `master` on this date. Final stable 3.0 migration baseline is not yet available. See the audit for stable 2.6 and RC1 commit identities; do not infer stability from an assembly version of 3.0.0.

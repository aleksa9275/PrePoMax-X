# PrePoMax-X project charter

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

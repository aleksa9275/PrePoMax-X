# PrePoMax-X project charter

Record updated: 2026-10-15, Europe/Belgrade. Phase 0 and bounded tasks 0002–0010
are complete within their scopes; task 0012 completes further local preparation
and research publication, including native Linux x64 hosted evidence. Task 0011 awaits Windows.
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

# PrePoMax-X project charter

Record date: 2026-10-13, Europe/Belgrade. Phase 0 is complete; the first bounded core-feasibility milestone is authorized.

PrePoMax-X is an open-source cross-platform adaptation of [PrePoMax](https://gitlab.com/MatejB/PrePoMax). Preserve FEM functionality, numerical meaning, file compatibility and the ability to follow upstream releases. Minimize permanent divergence; this project is not an independently developed FEM application.

Required release targets: Windows x64, macOS ARM64, macOS x64, Linux x64. Linux ARM64 is desirable after the required targets. Native operation is the goal; Wine, Windows VMs and Rosetta do not qualify as final portability solutions.

Naming convention: **PrePoMax-X**, with `X`/`x` for project-specific cross-platform names and prefixes. The long-lived integration branch is `x/main`.

The maintainer authorized task 0002 and promotion of the reviewed Phase 0 documentation into `x/main`. Implementation stays on `feature/core-feasibility` and is limited to additive source-linked probes, tests/provenance and Linux CI preparation. Existing application code/projects and engineering algorithms remain unchanged. Broader architecture commitments, production dependencies, subsequent integration and public pushes remain pending approval. Preserve history and uncommitted work. Root GPL v3 license and Matej Borovinšek's attribution remain authoritative; third-party notices and corresponding-source obligations travel with distributed components.

## Where to start

| Record | Responsibility |
|---|---|
| [STATUS](STATUS.md), [task 0001](tasks/0001-initial-repository-audit.md), [proposed task 0002](tasks/0002-core-feasibility.md) | Current state, verification, handoff and first runnable milestone |
| [initial audit](reports/initial-audit.md) | Repository/baseline facts and investigation limits |
| [ARCHITECTURE](ARCHITECTURE.md) | Existing project graph and reuse evidence |
| [DEPENDENCIES](DEPENDENCIES.md), [dependency matrix](reports/dependency-matrix.md) | Native/managed inventory and supply-chain gaps |
| [PORTABILITY_AUDIT](PORTABILITY_AUDIT.md) | Obstacles and file-format contract |
| [MIGRATION_STRATEGIES](MIGRATION_STRATEGIES.md) | Alternative architectures and recommendation |
| [MIGRATION_SPEC](MIGRATION_SPEC.md) | Proposed interfaces and proof-of-concept gates |
| [TEST_STRATEGY](TEST_STRATEGY.md) | Equivalence tests and platform acceptance |
| [UPSTREAM_SYNC](UPSTREAM_SYNC.md) | Safe mirror and separate integration procedure |
| [ROADMAP](ROADMAP.md), [DECISIONS](DECISIONS.md) | Dependency-aware work and approval status |

Provisional analysis baseline: `de8f73032a72746e3d6d9afd53d9fbd289eb310a`, upstream `master` on this date. Final stable 3.0 migration baseline is not yet available. See the audit for stable 2.6 and RC1 commit identities; do not infer stability from an assembly version of 3.0.0.

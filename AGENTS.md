# PrePoMax-X contributor and agent instructions

Read `.project/PROJECT.md`, `.project/STATUS.md`, `.project/DECISIONS.md` and the task record before changing anything. These tracked records, rather than conversational memory, define the handoff.

## Current authorization

Phase 0 is complete. On 2026-10-13 the maintainer authorized the recommended first milestone, a new implementation branch and promotion of the reviewed Phase 0 records into `x/main`. Task `.project/tasks/0002-core-feasibility.md` defines the bounded scope: source-linked STL/vector/node probe, tests/provenance, upstream replay, local Podman verification and complementary GitLab native Linux x64 CI on `feature/core-feasibility`.

Local implementation for task 0002 is authorized. On 2026-10-14 the maintainer first authorized replacing GitLab CI with local Podman verification, then authorized retaining Podman and restoring complementary GitLab native Linux x64 checks. The maintainer handles all pushes and normally commits; leave changes uncommitted unless explicitly asked to commit. Preserve existing application source/project files and algorithms; do not introduce production dependencies, begin broad controller/GUI/serialization refactoring or select a frontend. Further implementation or feature integration into `x/main` requires authorization. Never push, force-push, delete branches or overwrite uncommitted work. Proposals in the broader specification remain unapproved commitments.

## Repository conventions

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

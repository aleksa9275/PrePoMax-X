# PrePoMax-X contributor and agent instructions

Read `.project/PROJECT.md`, `.project/STATUS.md`, `.project/DECISIONS.md` and the task record before changing anything. These tracked records, rather than conversational memory, define the handoff.

## Current authorization

2026-10-15 local completion instruction: the maintainer explicitly authorized
completing remaining feasible testing/preparation with resources on this Mac,
then committing and pushing the reviewed research to the origin fork. Task 0012
bounds this continuation. This supersedes earlier leave-uncommitted instructions
for this publication only. No production refactoring, frontend/default serializer
choice, F001 integration, x/main merge, upstream write or force push is authorized.
The exception ends after task 0012 publication and its hosted evidence follow-up.

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

- Next Windows session: read `.project/handoffs/windows-next-session.md` and task
  `.project/tasks/0011-windows-reference-validation.md`. Windows will be available; capture is
  pending. Check publication status in STATUS before transfer; task 0012 now
  authorizes publishing the research branch so it can be fetched on Windows.
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

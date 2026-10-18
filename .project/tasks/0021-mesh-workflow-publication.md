# Task 0021 — Publish RC2 replay and portable mesh workflow

2026-10-18, Europe/Belgrade. Maintainer explicitly requests committing and
pushing completed changes, then explaining the next work. Further feature
steps must wait until the maintainer reads and approves the proposal. This
supersedes the task 0019/0020 uncommitted-only restriction for publication and
closing evidence. It does not authorize beginning the proposed next features.

Publish reviewed task 0019/0020 implementation, evidence and handoffs only to
origin/research/native-feasibility, with a normal non-force push. Preserve all
source/type ownership, both correctness failures/measurement gate and remaining
release gates. No x/main merge, upstream write, frontend/default serializer,
native-tool substitution or algorithm/tolerance change.

Scope: verify the exact outgoing diff and retained evidence, remote ancestry,
source/replay guards and clean staging; commit/push; verify the remote SHA and
exact-commit native x64 CI/downloaded artifacts. Publish closing evidence and
make the Windows Git continuation current. Explain the next model/deck, solver,
results and host/persistence steps as a proposal and stop for approval.

Initial local/remote checkpoint: research/native-feasibility at
2f2eca945c8acad0c3b902537f95055e67be6a42; task 0019/0020 changes uncommitted.
Existing evidence: six Mac/Linux ARM64 builds, 218 accepted checks/39 CLI/four
data controls per build, ten replay guards, both retained correctness failures,
same-ZIP native Mac/Linux source rebuild and 125 manifest checks.

Status: publication in progress. [Publication evidence](../reports/mesh-workflow-publication.md).

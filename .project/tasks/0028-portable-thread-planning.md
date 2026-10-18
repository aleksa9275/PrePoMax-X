# Task 0028 — Portable 75% solver thread planning

2026-10-18. Maintainer authorizes selecting a bounded task using about 15
percentage points of the remaining usage, then committing/pushing current work
and continuing only after reset. Exact usage cost cannot be guaranteed. Select
the requested CPU recommendation foundation from task 0027: a portable callable
planner and read-only CLI with automatic/manual counts and planned concurrent-
job allocation. This is not an active job scheduler or production GUI migration.

Read PROJECT/STATUS/DECISIONS/task 0027 before edits. Preserve every existing
uncommitted change and source/assembly identity. Modern-only CaeJob code must
not enter the original net48 build. Keep reference run-static one-thread controls;
no numerical/default-backend/precision/GPU/affinity changes or solver benchmarks.
Validate allocation bounds, fairness, deterministic integer rounding and malformed
CLI controls on native Mac/Linux ARM64 and all three source pins. Preserve both
correctness failures/tetra gate and all release requirements.

Task 0029 covers review/publication of tasks 0022–0028, exact-commit hosted
verification where available and reset handoff. Publish normally only to
origin/research/native-feasibility; no force, upstream/x/main/release write.
Stop after publication/handoff; no further feature work before continuation.

## Completed locally

Implemented modern-only immutable CaeJob.SolverThreadPlan and read-only
thread-plan CLI. All three source pins pass native Mac/Linux ARM64: 47 checks,
two positive CLI plans and 13 rejection controls per build. Final fingerprints/
outcomes compare; host CPU counts are independently validated. No reference
solver setting or numerical behavior change. [Evidence](../reports/portable-thread-planning.md).
Task 0029 owns publication and closing handoff.

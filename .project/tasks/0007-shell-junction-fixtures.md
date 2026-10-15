# Task 0007 — Shell T-junction connectivity fixtures

Status: bounded fixture preparation complete on 2026-10-14. Authorized by the maintainer's 2026-10-14 instruction to
progress through bounded pre-Windows steps, including preparation for the
shell-connectivity proposal. Branch remains research/native-feasibility.

Define the shell plate/web geometry and four independently specified S4 mesh
cases: connected reference, coincident but disconnected, unsplit plate and
intentional gap. Retain units/connection intent and exact expected IDs, areas
and shared-edge contracts. Add a small fixture-only checker and negative
regressions so later Windows inspection has precise expected observations.

This is F001 fixture preparation, not an automatic meshing implementation,
production INP parser, CAD model, solver problem or Windows reference capture.
No physical weld/contact formulation or connection-default policy is selected.
No production changes, new dependencies, commits, pushes or x/main integration.

Acceptance: all four explicit topology/geometry contracts checked; deliberately
broken connectivity/coordinates rejected; exact fixture hashes and commands
retained. Keep F001's behavior proposal and live CAD/mesher acceptance pending.

## Outcome

Four fixture contracts and two rejection regressions pass. Geometry, units,
connection intent, IDs, areas/gap and exact file hashes retained in the manifest.
See [report](../reports/shell-junction-fixtures.md). Windows imports, PMX/history,
CAD creation and actual mesh/solver comparisons remain pending. No F001 behavior
implementation or production changes.

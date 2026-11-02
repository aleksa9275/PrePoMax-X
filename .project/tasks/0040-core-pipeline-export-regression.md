# Task 0040 — Diagnose and repair the 384edea2 pipeline failure

2 November 2026. Maintainer supplies signed-in GitLab access and identifies
384edea2. Pipeline 3019186769 has one failed job: shared-core-linux-x64,
17675531644. Analysis/execution/results/research pass; compatibility is manual.
Downloaded retained core diagnostics identify export/reopen element-block name
loss (CUBE → null) introduced by B001's prior fix. Geometry, node/element IDs,
sets and formulation remain equal. This is shared exporter behavior.

Bounded continuation: retain inline element-block names, emit explicit set members
only where not already supplied inline, preserve the existing full CLI roundtrip
assertion, and test residual membership plus the native analytical solve. Do not
weaken comparisons/tolerances or revert to duplicate solver histories. Use current
Core/Analysis checks and exact-commit native Linux CI after normal authorized
research publication. Preserve both existing failures/tetra gate and all release
requirements; no unrelated feature, dependency or production policy change.

Local outcome: original Core CLI roundtrip passes with CUBE preserved; mesh
checks 69/analysis accepted total 333. Native cube passes twelve checks and its
negative control. Development publish/smoke and 125-entry package verification,
ten replay/nine analysis guards pass. [Evidence/publication](../reports/core-pipeline-regression.md).

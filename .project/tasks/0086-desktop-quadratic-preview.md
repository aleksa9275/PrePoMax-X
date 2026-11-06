# Task 0086 — Desktop quadratic preview and export

Authorized 6 November 2026 by the request about quadratic meshes and three more
tasks. Add desktop mesh-order controls, quadratic rendering/picking/regions and checked new-file INP export, with explicit disabled C3D10 analysis. Verify native Mac/Linux ARM64 and both copied Mac viewports, linear analytical workflows and PMX regressions; publish with CI skipped and retain one candidate.

Preserve D029 original-kernel numerical behavior, both correctness failures,
quadratic measurement/solve and curved-quality gates, D057, D058 hosted CI hold,
D059 Windows/Podman x64 deferral and all four-target/parity/release gates.

Completed within the preview/export boundary on 6 November 2026. Implementation
`76fbb7d7` is pushed/remote-verified with CI skipped. Both native hosts and copied
Mac viewports pass 27 quadratic workflow checks, 52 desktop tests per host and
linear/PMX regressions. Numerical quadratic/curved-quality and both original
correctness gates remain. Final source/candidate, exact checks and retention are
recorded in [the report](../reports/quadratic-cad-preview.md) and its receipt.

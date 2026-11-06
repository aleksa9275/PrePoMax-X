# Task 0085 — Native quadratic CAD meshing

Authorized 6 November 2026 by the request about quadratic meshes and three more
tasks. Expose an explicit second-order native mesh profile using original MeshingParameters and Netgen second-order generation. Retain frozen parameters/order and safe mesh export with verified original INP readback; preserve linear default and all numerical gates.

Preserve D029 original-kernel numerical behavior, both correctness failures,
quadratic measurement/solve and curved-quality gates, D057, D058 hosted CI hold,
D059 Windows/Podman x64 deferral and all four-target/parity/release gates.

Completed within the preview/export boundary on 6 November 2026. Implementation
`d365fbba` is pushed/remote-verified with CI skipped. Both native hosts and copied
Mac viewports pass 27 quadratic workflow checks, 52 desktop tests per host and
linear/PMX regressions. Numerical quadratic/curved-quality and both original
correctness gates remain. Final source/candidate, exact checks and retention are
recorded in [the report](../reports/quadratic-cad-preview.md) and its receipt.

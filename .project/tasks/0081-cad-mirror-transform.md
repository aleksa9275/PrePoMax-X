# Task 0081 — Original CAD mirror transform

Authorized 6 November 2026 as part of three further bounded tasks. Add selected-part reflection about an explicit plane using the original BREP_TRANSFORM Mirror command. Validate finite point/nonzero normal, analytical geometry and identities, original input preservation, undo/redo and native first-order remesh/solve.

Preserve D057 original PMX compatibility, D058 hosted CI hold, D059 Windows/Podman
Linux x64 deferral, both known correctness failures, quadratic tetrahedra, strict
native parity differences and all four-target/installer/signing/release gates.
Publish normally to origin/research/native-feasibility with CI skipped. Keep
one current verified candidate; preserve all projects/jobs/evidence/shared tools.

Completed within this boundary on 6 November 2026. Implementation `ba5a3900`
is pushed/remote-verified with CI skipped. Mac/Linux ARM64 pass 99 native CAD
checks and 50 desktop tests; both source desktops and copied Mac viewports pass
91 combined workflow checks. PMX regressions pass 28/17 on both hosts. The Mac
six-solid mesh has 402 nodes/898 C3D4, Linux 402/900; exact parity remains open.
Current candidate, source/payload identities and retention are recorded in
[the report](../reports/cad-mirror-scale-copies.md) and its verification receipt.

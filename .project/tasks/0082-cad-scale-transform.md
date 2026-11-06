# Task 0082 — Original CAD scale transform

Authorized 6 November 2026 as part of three further bounded tasks. Add explicit-center positive uniform/non-uniform scaling through original BREP_TRANSFORM Scale. Bound finite non-singular factors in the preview; check analytical volume, centroid, bounds and identities without changing kernel/mesh/solver precision.

Preserve D057 original PMX compatibility, D058 hosted CI hold, D059 Windows/Podman
Linux x64 deferral, both known correctness failures, quadratic tetrahedra, strict
native parity differences and all four-target/installer/signing/release gates.
Publish normally to origin/research/native-feasibility with CI skipped. Keep
one current verified candidate; preserve all projects/jobs/evidence/shared tools.

Completed within this boundary on 6 November 2026. Implementation `fb9da6c4`
is pushed/remote-verified with CI skipped. Mac/Linux ARM64 pass 99 native CAD
checks and 50 desktop tests; both source desktops and copied Mac viewports pass
91 combined workflow checks. PMX regressions pass 28/17 on both hosts. The Mac
six-solid mesh has 402 nodes/898 C3D4, Linux 402/900; exact parity remains open.
Current candidate, source/payload identities and retention are recorded in
[the report](../reports/cad-mirror-scale-copies.md) and its verification receipt.

# Task 0079 — Native CAD axis-angle rotation

Authorized 6 November 2026 as the second of three further tasks. Expose the
original BREP_TRANSFORM rotation with explicit center, nonzero axis and degrees.
Use the existing background/atomic publication and new geometry undo boundary.
Check analytical volume, centroid and bounds, unaffected bytes, malformed inputs,
remeshing and frozen rotation provenance on native Mac/Linux ARM64.

No kernel/precision/default-format change. Keep D057/D058/D059 and all
correctness/tetrahedron/four-target/parity/release gates open.

Completed within this boundary on 6 November 2026. Implementation `ec24d84d`
is published/remote-verified on origin/research/native-feasibility with CI skipped.
Native Mac/Linux ARM64 pass 50 CAD transactions and 49 desktop checks; Linux and
both copied Mac viewports pass all 62 combined workflow checks. CAD PMX/C3D8
regressions pass 28/17 on both hosts. Current candidate, exact source/payload
identity, strict parity differences and cleanup are recorded in
[the final report](../reports/cad-history-rotation-export.md) and its receipt.

# Task 0080 — Checked whole-model STEP geometry exchange

Authorized 6 November 2026 as the third of three further tasks. Export all owned
CAD bodies into one STEP through original native unchanged-assembly/export commands,
retaining source-solid origins and checking every solid on native readback.
Refuse body loss/changed supported geometry and existing destinations; preserve
the active mesh, analysis and unsaved state. This is geometry exchange; original
assembly metadata and native-session PMX serialization remain separate.

Verify native Mac/Linux ARM64, all three real desktop features, edited geometry
remeshing/analytical solve, PMX regressions and both copied Mac viewports. Publish
with CI skipped and retain one current candidate. Preserve D057/D058/D059,
strict parity differences and all correctness/tetrahedron/release requirements.

Completed within this boundary on 6 November 2026. Implementation `390cf08b`
is published/remote-verified on origin/research/native-feasibility with CI skipped.
Native Mac/Linux ARM64 pass 50 CAD transactions and 49 desktop checks; Linux and
both copied Mac viewports pass all 62 combined workflow checks. CAD PMX/C3D8
regressions pass 28/17 on both hosts. Current candidate, exact source/payload
identity, strict parity differences and cleanup are recorded in
[the final report](../reports/cad-history-rotation-export.md) and its receipt.

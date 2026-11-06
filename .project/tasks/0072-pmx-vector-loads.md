# Task 0072 — Persistent PMX signed vector loads

Authorized 6 November 2026 as the second of three further bounded tasks.
Implemented; Mac interoperability/native workflow passes. Linux ARM64 and the
combined package follow at task 0073 closeout. [Evidence](../reports/pmx-vector-loads.md).
Extend the checked original CAD/C3D4 PMX editor from positive axial force to
finite signed global three-axis force per node. Keep magnitude consistent
with the original CLoad owner, preserve shared zero equations, and verify
original-app reopen/resave plus native deck/result behavior. Keep the older
C3D8 writer contract and standalone mesh precision unchanged.

Preserve D057/D058/D059, all correctness/tetrahedron and parity/release gates.

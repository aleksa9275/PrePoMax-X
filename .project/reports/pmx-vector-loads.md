# Persistent original PMX signed vector forces

Task 0072 extends the checked CAD/C3D4 PMX editor with signed global X/Y/Z
force per node. The magnitude is calculated and formatted by the original CLoad
and EquationContainer owners through the existing portable C# host. Shared zero
strings retain their values; supports and all mesh/CAD data remain unchanged.
The older C3D8/positive-axial writer contracts and mesh precision are unchanged.

The test vector is `(-3, 4, -12) N`, with magnitude 13 N. Negative axial loads
and a repeated edit with fractional multiaxis forces also pass. Nonfinite,
oversized, malformed and all-zero loads are refused before publication. The
last refusal preserves the existing static deck's nonzero-force requirement.
The first implementation's magnitude serialization error was caught by the
strict contract test and corrected before publication; initial receipts remain.

Fifteen final Mac contract/interoperability checks and twenty-one real desktop
checks pass. Original PrePoMax 3.0.0 reopens/resaves equal projected engineering,
CAD and mesh semantics; its exported deck and the native reconstruction give
exactly equal decoded result fields through the same native solver.
[Verification](pmx-vector-loads-verification.json).

Detailed local evidence: `/tmp/prepomaxx-task0072-evidence`. Combined Linux ARM64
verification and the current Mac package pass at [task 0073 closeout](pmx-region-assignments.md). No hosted
CI runs; D058/D059, both correctness failures, quadratic tetrahedra, general PMX,
new native-session serialization and all parity/release gates stay open.

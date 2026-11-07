# B007 — Original buckling search omits lower factors near its shift

Open inherited solver behavior, tasks 0092–0094, 7 November 2026. A linear
elastic C3D20 cantilever column (1 × 0.5 × 10 mm, E=1000 MPa, nu=0) has a
0.1 N compressive reference load distributed over its eight top nodes. The first
three factors are 2.5661845, 10.216758 and 22.811197. Increasing only the
reference load tenfold to 1 N should divide all corresponding linear buckling
factors by ten. The original solver instead reports 1.0216758, 2.2811198 and
6.18587, omitting the lower mode expected near 0.25661845. Its first reported
mode corresponds to the second mode from the smaller reference-load run.

Native Mac and fingerprint-checked original Windows CalculiX 2.22 through
CrossOver reproduce these results on identical decks. Original `arpackbu.c`
sets `sigma=1`, requests `which="LM"` in the shifted buckling problem, and has
the shift plausibility/refinement loop commented out. This supports search-shift
selection as the cause; no complete corrective solver patch has been established.

D061: record and defer numerical changes until full PrePoMax 3.0.0 functionality
parity. Preserve the original solver and all requested modes. The example's
explicit 0.1 N reference load yields a lowest reported factor above one and
matches the slender Euler approximation within 0.2%; this is a fixture choice,
not automatic rescaling or a fix. The analysis editor notes the observed search
limitation. Do not claim the returned factors always include the lowest positive
critical factor or close full numerical acceptance.

Post-parity proposal: review the original shift selection/refinement and mode
selection criteria; validate corrected extraction with reference-load scaling
and multiple competing modes before changing the solver. Preserve original
reference outputs for compatibility comparisons.

Evidence: `/tmp/prepomaxx-task0092-0094-evidence/native-deadload/column-buckling`,
`source-gui/workflow.json` and `windows-reference/verification.json` under the
same evidence root. The [milestone report](../reports/eigenmodes-results-tools.md)
and its receipt retain actual input/output identities and comparisons.

# B011 — C4 linear cube nodal-stress diagnostic remains false

9 November 2026; D061 numerical diagnostic, cause unresolved. No algorithm,
solver, field conversion or tolerance is changed.

The original Controller imports `windows-reference/fixtures/definitions.inp`,
exports its unit cube with 100 total force and runs pinned CalculiX 2.22/SPOOLES.
Mac and Linux ARM64 give node 2 U1 = `0.00047619000542908907`, S11 =
`99.99600219726562`. The original result equation `=2*STRESS.S11` gives
`199.99200439453125` and exactly doubles the loaded source field.

The independent doubled-stress expectation is 200 with absolute tolerance 0.001;
that check **fails**. It remains separately false in C4 service receipts rather
than being included in the UI/service pass count. The strict PMX opened by the
original Windows 3.0.0 reference gives the identical three values and preserves
the equation and table history through resave/native readback. This proves data
and equation consistency; it does not isolate solver/extrapolation/reader causes
or establish an original-Windows solve for this new diagnostic.

Evidence: `/private/tmp/prepomaxx-c4`, C4 milestone report/receipt. Post-parity:
isolate the deck, integration-point/nodal FRD output and original result mapping
against an original Windows solve, then repair the responsible layer. Keep the
analytical expectation and tolerance unchanged.

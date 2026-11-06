# B005 — Lossless mesh coordinates exceed CalculiX numeric field width

6 November 2026, task 0087's curved C3D10 calculation. The mesh-only writer uses
G17 to preserve coordinates. A real imported CAD coordinate becomes
`6.8000000000000001E-15`; that exceeds the solver's numeric field width and
CalculiX exits 201 at `*NODE`, before assembling any element. This issue can
affect either mesh order. Failure is retained in
`/tmp/prepomaxx-task0087-evidence/native-mac3/curved/solve/run.json`.

Static solver decks now call the same original `CalNodeFormatting.Write3D`
E8 formatter used by original PrePoMax and the existing CAD PMX adapter. Mesh
exchange remains G17 and exact mesh readback remains required. Input orientation
validation uses the original coordinates; CalculiX checks the formatted deck's
Jacobians when assembling. This is an explicit original-format compatibility
repair, not a new coordinate-precision policy or a change to solver arithmetic.

A regression checks original node formatting and unchanged lossless exchange.
The curved native solve and identical input deck through the pinned original
Windows solver both complete. Exact native/Windows fields remain separately
compared, not assumed from matching inputs. [Evidence](../reports/quadratic-native-static.md).

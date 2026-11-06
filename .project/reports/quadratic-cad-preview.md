# Quadratic CAD mesh preview

Tasks 0084–0086 add checked C3D10 mesh transport, native second-order CAD
meshing and desktop preview/export. This is mesh preview, not numerical
acceptance: original ParabolicTetraElement.Integrate affine-field discrepancy,
quadratic-pyramid classification, measurement/static-solve/curved-quality and
all full parity/release gates remain open. Implementation is in progress.

Task 0084 passes the current analysis suite, including four new quadratic
topology/refusal checks. The verifier expected-count contract now includes
58 analysis tests. An initial count-only failure is retained; no engineering
tolerance or original failed expectation changed. Task 0085 passes 11 native
checks each for the two-body BREP and curved STEP: ten-node identity, original
readback, midside CAD sets, preserved source bytes and frozen order/analysis
refusal. Two-body mesh: linear 70 nodes/130 tetrahedra; quadratic 330/130.

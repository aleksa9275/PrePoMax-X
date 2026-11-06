# Task 0075 — Native desktop CAD plane splitting

Authorized 6 November 2026 as the second of four further tasks. Add explicit
part/plane-origin/normal controls around original BREP_SPLIT. Retain untouched
parts, split output/source-solid origins and input recipes. Validate all resulting
parts before replacing the document; clear dependent mesh/selection only on
success. Check the original two-equal-solids reference and malformed inputs.
Share task 0074's cancellation and document-lifetime boundary.

Use local Mac/Linux ARM64 and CI-skipped research publication. Preserve
D057/D058/D059 and all correctness/tetrahedron/parity/release gates.

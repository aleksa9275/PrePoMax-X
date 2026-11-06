# Task 0074 — Native desktop CAD translation

Authorized 6 November 2026 as the first of four further tasks. Bring the task
0066 original BREP_TRANSFORM translation into the native desktop for an explicit
owned CAD part. Run in the background with cancellation; publish a fully decoded
new document only on success. Preserve all unaffected parts and original inputs.
Invalidate dependent mesh/regions/analysis only after successful geometry edits;
freeze edit inputs/recipes in subsequent jobs. Refuse geometry mutation of an
opened PMX because its general geometry rewrite boundary remains unsupported.

Verify native Mac/Linux ARM64, original reference hashes/analytical geometry,
failure/cancellation/lifecycle behavior, and one combined final Mac candidate.
Keep D057/D058/D059 and all correctness/tetrahedron/parity/release gates.

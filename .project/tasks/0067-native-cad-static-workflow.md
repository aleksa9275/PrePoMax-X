# Task 0067 — Native CAD to static results workflow

Prepared next increment under the maintainer's native CAD/meshing continuation.
Task 0063 supplies original native import/meshing and task 0064 connects CAD
inspection. Complete one bounded desktop path from checked CAD through a native
first-order mesh, original engineering objects/deck, CalculiX and original results.

- Retain owned BREP parts and input/source identities for the document lifetime;
  failed/cancelled replacement keeps the previous document and its files.
- Add explicit mesh controls through the original meshing-parameter writer and
  an owned cancellable native process. Keep source part/face/domain IDs and
  publish all resulting mesh data atomically.
- Share the original VOL parser and node permutations without moving legacy
  `FeMesh` orchestration into Python or rewriting engineering algorithms. Keep
  Windows/net48 type ownership and original behavior checked mechanically.
- Extend the bounded static/FRD interfaces only as needed for first-order C3D4,
  preserving their original writers and result decoding. Keep quadratic
  tetrahedra blocked and both existing correctness failures open.
- Verify a small analytical first-order solid, native solve and decoded fields;
  retain the mesher parameters, deck, mesh hash and source CAD association in
  the job. Preserve current INP, checked PMX, C3D8 and reference CAD workflows.

Use Mac/Linux ARM64 local builds and the retained OCCT cache for routine work.
Reserve hosted x64 CAD/kernel/package checks for the integration milestone under
task 0065's quota policy. General CAD/project persistence, broad analyses, native
Windows acceptance and full 3.0.0/four-target/release requirements stay separate.

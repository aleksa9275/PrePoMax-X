# Native CAD mirror, scaling and transform copies

Tasks 0081–0083 extend native CAD authoring through the original recovered
BREP_TRANSFORM protocol. Read the task records for the bounded acceptance
criteria. Implementation and verification are in progress. Native-session PMX
persistence, exact native parity and all existing correctness/release gates
remain open; D058/D059 remain in force.

Task 0081: thirteen native Mac checks pass for an off-origin oblique mirror,
positive volume, centroid/bounds, original face/edge/vertex IDs, untouched part
bytes, origin mapping and malformed inputs. Combined desktop/Linux checks
follow in task 0083. No new original Windows execution is claimed.

Task 0082: twenty-two native Mac checks pass for explicit-center uniform and
non-uniform scaling: analytical volumes/centroids/bounds, face/edge/vertex IDs,
untouched inputs, origins and invalid factors. Positive factors are bounded
to 0.000001–1000 and an identity-only scale is refused. The original kernel
converts non-uniform surfaces to splines; no geometric formatter was changed.

Task 0083: translated/rotated numbered outputs retain every original part byte,
append part-scoped copies and record all original output hashes. The preview
allows 1–16 copies within 32 total parts; incomplete/extra/cancelled output
inventories are discarded before publication. Mac/Linux ARM64 pass 99 native
transactions and 50 desktop checks. Both source desktops pass 91 combined
workflow checks through eight edits, undo/redo, six-solid remeshing, STEP readback
and affine/unit-stress solve. Mac has 402 nodes/898 C3D4; Linux has 402/900.
Strict mesh/deck/field equality remains open; native analytical acceptance is
separate. Final copied-app and PMX/retention evidence follows at closeout.

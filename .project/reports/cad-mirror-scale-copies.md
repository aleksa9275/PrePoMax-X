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

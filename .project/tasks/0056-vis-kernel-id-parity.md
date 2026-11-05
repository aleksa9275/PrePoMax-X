# Task 0056 — VIS kernel ID parity

Compare the bundled 3.0.0 CAD runtime hashes against reachable upstream
history and identify the corresponding binary drop. Port its managed
partial-triangulation fix into the shared VIS reader and legacy FeMesh
renumbering. Verify that a free triangle side joining nonadjacent polyline
nodes does not acquire the source edge ID. Keep the original L-bracket
comparison exact.

Record source availability separately from the verified binary drop.
Native STEP/BREP execution requires the corresponding C++ sources and
build recipe.

[Verification and source provenance](../reports/vis-kernel-id-parity.md).

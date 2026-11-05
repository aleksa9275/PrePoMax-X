# Task 0070 — Native desktop CAD PMX persistence

Completed 6 November 2026. [Implementation/evidence](../reports/desktop-cad-pmx.md).

The maintainer authorizes the next two tasks after task 0068. Task 0069 supplies
an original CAD/C3D4 PMX reference and safe graph/binary projection. This task
implements a first editable interoperability slice around that verified boundary.

- Open the checked single-part result-free original CAD PMX without remeshing.
  Preserve original BREP, geometry/mesh IDs, named regions, meshing data and history.
- Edit the audited modulus/axial force values, validate original engineering decks,
  publish only a new PMX, then close/reopen and solve with the native backend.
- Preview saved CAD through the explicit native CAD profile; preserve the model
  when switching CAD/mesh/results, and refuse unsupported data without replacement.
- Freeze the complete submitted PMX in jobs in addition to mesh/deck identities.
- Verify native Mac/Linux ARM64, original-app readback/resave and current C3D8,
  CAD-region and PMX regressions. Publish with CI skipped and retain one candidate.

This bounded editor preserves original history but does not replay it. Saving an
arbitrary newly authored native CAD/mesh/region session, general PMX, transformed/
multipart graphs and results/history breadth remain separate increments. D057
original compatibility remains the policy. D058 blocks hosted CI; D059 defers
Linux x64 to Windows/Podman near finishing. Keep all correctness/tetra/release gates.

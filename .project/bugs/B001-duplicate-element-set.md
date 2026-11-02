# B001 — duplicated element-set membership in mesh/deck adapter

Fixed in task 0038, 2 November 2026. First published affected implementation:
47f17be6657b470cff814d50b97c79fada52040a, `MeshDeckWriter.WriteMesh`.
Observed on native macOS ARM64 with recovered CalculiX 2.22; other targets not
executed for this reproduction.

Minimal inputs: `X/Analysis/StaticDeck/cube-mesh.inp` and `cube-analysis.json`.
Expected: one SOLID member and eight integration-point stress rows. Actual:
the adapter wrote both `*Element, ... Elset=SOLID` and `*Elset, Elset=SOLID`; native
CalculiX emitted sixteen rows, and the original bounded DAT reader correctly
rejected duplicate row identity. Mesh re-import tests had deduplicated membership
and therefore missed the solver-visible error.

Fix: let original CalElement format elements without an inline set name; emit
the mesh's explicit sets once. Original keyword/parser algorithms remain intact.
One named regression checks this exact deck defect; the real native workflow now
checks eight stresses, displacements/reactions and original DAT import. Tolerances
are unchanged. This is separate from both pre-existing element correctness bugs.
See [workflow evidence](../reports/native-cpu-workflow.md).

Task 0040 follow-up: removing inline names caused B003 metadata loss. The refined
fix preserves the name/membership inline and writes only residual explicit set
members. B001's single-membership regression and actual native solve remain.

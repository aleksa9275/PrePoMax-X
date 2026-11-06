# Deferred correctness fixes and improvements

Maintainer direction, 6 November 2026, D061: record the findings/proposals and
continue the existing implementation toward full PrePoMax 3.0.0 parity first.
Implement fixes and improvements after that milestone. These proposals are a
post-parity backlog, not the next engineering increment. The earlier suggestion
of a combined correctness increment is superseded by this sequencing decision.

The target remains IDENTICAL original functionality on all four targets, with
the unavailable Intel/PARDISO solver as the sole exception (D060). Preserve
original algorithms, conversions and existing tolerances during the parity
phase. Continue necessary port/integration repairs to reproduce original
behavior; this deferral does not defer missing original functionality. Keep
known failures explicit, existing measurement safeguards and reference evidence
intact. Deferral does not mark an analytical failure passed or close a numerical,
exact-parity, platform or release gate. Do not let these inherited findings halt
unrelated functional implementation.

## Recorded findings and proposed post-parity work

| Finding | Evidence/status | Deferred proposal |
|---|---|---|
| D029 quadratic tetrahedron measurement integration | Straight tetrahedron, volume 4, affine field 2+x+2y+3z: integral 26.794910717854155 versus exact 28 (4.30% low). Original quadrature weights sum to 1/6, but each first moment is 0.03915606399552952 versus exact 1/24. Source-level discrepancy; original code unchanged. | Correct the point/weight table against independently verified moments; check straight and curved elements before enabling the affected measurement path. Native CalculiX C3D10 solving uses its separate formulation and remains operational. |
| D029 quadratic pyramid classification | Both original FeElement.IsParabolic overloads omit ParabolicPyramidElement. Explicit current dispatch avoids the helper; no resulting numerical field corruption has been demonstrated in the current workflow. | Include the quadratic pyramid in both overloads and check affected callers. |
| B006 quadratic pyramid → collapsed wedge under pressure | Maximum displacement error 3.7943e-5 mm and stress error 0.047 MPa against the 1 MPa analytical case. Reproduced on native Mac/Linux ARM64 and by the pinned original Windows solver through CrossOver. Hexahedron conversion passes that case; both routes remain selectable. Underlying cause unresolved. | Isolate equivalent pressure forces, degenerate-element stiffness and stress extrapolation using integration-point/nodal output, then correct the responsible conversion or solver routine. The hexahedron route is the current example's explicit workaround, not a proven general numerical correction. |
| Small identical-deck solver field differences | Latest native/original Windows comparisons: displacement values identical, maximum stress differences approximately 1e-12 to 1.41e-6 MPa. Earlier curved case has displacement differences about 2e-16. No engineering error established from these differences alone; precise cause unproved. | Investigate build/compiler/backend/arithmetic-order effects. Make a numerical change only if the cause and need are demonstrated; retain exact comparisons and existing accuracy bounds. |
| Cross-platform CAD meshing differences | One six-body fixture: Mac 402 nodes/898 C3D4 elements, Linux ARM64 402/900. Both meet its analytical checks. Other curved CAD meshes also differ. Exact native mesh/deck/field parity remains open; positional result arrays from different meshes are not comparable. | Audit native dependencies, build options, ordering and supported reproducibility controls. Compare geometry and fields at common locations while diagnosing exact-mesh differences; no claim that these measures guarantee identical topology. |

Sources: [original element findings](shared-element-kernel.md),
[B006](../bugs/B006-quadratic-pyramid-wedge-pressure.md),
[latest native/original comparisons](nonlinear-loaded-solids.md),
[curved quadratic comparison](quadratic-native-static.md) and
[Mac/Linux mesh differences](cad-mirror-scale-copies.md).

Already repaired port/integration defects remain repaired: duplicate element-set
emission/stress rows (B001), exported block identity loss (B003), field-only job
output classification (B004), solver node-format overflow (B005), and original
FRD/VTK display-order integration. This decision does not revert those repairs.
No numerical/application/build/test change is made by this record.

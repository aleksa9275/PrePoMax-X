# B006 — Original quadratic pyramid wedge conversion under pressure

Open correctness finding, task 0090, 6 November 2026. The mixed pressure example
has E=1000 MPa, nu=0, complete top-face pressure -1 MPa (outward tension), bottom
axial support and zero lateral displacement. The affine analytical result is
U3=0.001z and S33=1 MPa. Original C3D13 → collapsed C3D15 wedge conversion gives
maximum displacement error 3.7943000000000026e-5 mm and stress error 0.047 MPa.
All other mechanical solid types and the linear pyramid pass the same case.
The quadratic pyramid → collapsed C3D20 hexahedron route also passes.

Native Mac/Linux ARM64 reproduce the same discrepancy. The fingerprint-checked
original Windows CalculiX 2.22 executable, given the exact native deck through
CrossOver, produces identical displacements and stress differences below 1e-12.
The generated face correspondence agrees with original GetPyramidFaceConversion
and original face-node identities. This supports an inherited conversion/solver
accuracy issue; the underlying numerical cause has not been resolved.

Retain both original selectable conversion routes and unchanged algorithms.
Do not widen the analytical tolerance or claim complete numerical acceptance.
The bundled pressure example explicitly chooses hexahedrons, and the editor
notes the measured wedge discrepancy when quadratic pyramids are present.
The integrated workflow records this original-route check as false separately
from functional execution. D029's two original kernel failures remain separate.

[Report](../reports/nonlinear-loaded-solids.md) and
[receipt](../reports/nonlinear-loaded-solids-verification.json) retain input/output
hashes, native and original reference paths, comparison bounds and actual results.

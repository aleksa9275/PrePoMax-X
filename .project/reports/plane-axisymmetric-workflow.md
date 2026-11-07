# Plane stress/strain and axisymmetric element workflows

Tasks 0103/0104 connect all original CPS/CPE/CAX triangle and quadrilateral
formulations (3, 6, 4, 4R, 8, 8R) through explicit model-space configuration,
original solid sections, native static jobs, original FRD/DAT results and mesh
export/reopen. This is steps 1/2 of the maintainer-requested element-family plan.

## Delivered behavior

Configure → Model / units selects ThreeD, PlaneStress, PlaneStrain or Axisymmetric.
Plane sections require explicit positive thickness in the chosen length units.
The original SolidSection/CalSolidSection implementation writes the section;
CalNode's original two-dimensional E8 formatting is shared at the boundary.
Coordinates must lie in XY; axisymmetric X is nonnegative radius and Y is the axis.
Model space and every formulation must agree. U3 constraints and nonzero F3 or
third gravity components are refused before original 2D setters could erase them.

Solid formulations… retains topology-compatible plane-family choices and all
existing 3D choices. Changing CPS/CPE/CAX requires matching explicit model space;
coordinates, connectivity, named sets and input source remain unchanged.
Pressure uses original 2D element edges S3–S6 and CalDLoad's P1–P4 mapping.
Complete exterior-edge node sets and explicit element-set edges are supported.
Nodal forces/reactions are full-revolution quantities for axisymmetric models;
pressure remains force per area. No extra 180 multiplier is applied to forces.

The original header model-space marker reaches FRD decoding. The portable reader
uses the original Controller/FRD decisions, field lists and factors for segment
reaction heat flux and mass-normalized modes; ordinary static forces and physical
displacements are not rescaled. Expanded 3D output remains a segment. Geometry,
field math, numerical algorithms and existing tolerances remain original.

Solve example… includes three mixed-family tension examples (all six forms per
model space), plus an open-ended internally pressurized CAX8R thick cylinder.
The model tree, original field invariants, deformation/outline, DAT graph/table/
CSV and mesh-only export/reopen are connected. General PMX is step 8, and broader
family/analysis combinations remain step 6; the newly connected 2D deck path
explicitly requires a static step.

## Actual verification

[Receipt](plane-axisymmetric-verification.json) records actual checks and paths.
Mac and cached native Linux ARM64 complete all four desktop workflows (87 checks
each). Their decks, decoded result meshes and fields match exactly. The pinned
original Windows CalculiX 2.22 via CrossOver agrees on identical decks within the
existing 1e-6 absolute/relative comparison bounds. Maximum field difference is
about 4.97e-9. Original Windows axisymmetric coordinates differ in tiny out-of-plane
residuals (maximum 2.4e-20); strict original/native mesh equality stays false there.
This is not native Windows application or Linux x64 acceptance.

Plane stress and plane strain reproduce the independent free-response elasticity
solutions, including plane-strain S33=nu*S22 and thickness-dependent pressure
resultants. The cylinder uses E=1000, nu=.25, radii 1/2 and pressure 1. Lamé radial
and hoop stress errors are below .000957; radial displacement error is about
2.99e-7, including original two-degree-segment nodal projection. Refining the
initial 16 radial intervals to 32 meets the unchanged .002 stress bound; the
initial failure remains in evidence.

The coarse all-family axisymmetric model deliberately retains CAX3/CAX4R
continuum discrepancies (maximum axial displacement errors about 5.728e-5 and
2.266e-5) as diagnostics. The pinned original solver reproduces them. Strict
exact-continuum patch diagnostics remain false; compatibility is not full
numerical acceptance. Even the other axisymmetric radial fields retain the
original segment projection; no numerical fix or tolerance change is hidden.

Affected current Analysis/Results/Execution suites and 213-source ownership checks
pass. Seven new desktop behavior tests join 76 passing desktop tests; the four
job-boundary tests pass separately with the current host explicitly selected.
Initial headless OpenGL failure and missing default test-host setup are retained,
followed by actual native-display/current-host checks. Source screenshots were
visually inspected. Full copied-package checks are reserved for the combined
candidate after the additionally requested shell/beam milestones; the task0102
candidate remains available meanwhile. No hosted CI was run under D058.

All existing D029/B006/B007, coarse conductivity diagnostics, D057–D061, original
algorithms/tolerances, full PMX, four-target and distribution/release requirements
remain open. Native x64 remains deferred under D059.

Combined delivery: the current app is `/tmp/prepomaxx-task0106-current-delivery/PrePoMax-X Preview.app` at source 4c8b9a47. Its copied
plane/axisymmetric regression passes all 87 checks; both viewports and the other
structural workflows are verified in the [combined delivery](structural-elements-workflow.md).
The old task0102 payload is superseded and pruned; all inputs/evidence remain.

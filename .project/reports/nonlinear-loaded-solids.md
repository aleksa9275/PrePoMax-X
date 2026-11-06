# Nonlinear and distributed-load solid workflows

Task 0090 connects density, plastic hardening, pressure, gravity and geometric
nonlinearity to the desktop solid model, original keyword writers, native solver
and original result decoder. This is one functional delivery milestone. The
required final product remains IDENTICAL PrePoMax 3.0.0 functionality on all four
targets, with the unavailable Intel/PARDISO solver as the sole exception.

## Usable behavior

Configure… now has Density / plasticity, Pressure and Gravity tabs, plus the
original geometric-nonlinearity setting on Step. Material density, stress/plastic-
strain curves and original Isotropic/Kinematic/Combined hardening choices flow
through original C# types and converters. The integrated plastic example checks
isotropic hardening. Gravity requires density on every loaded element. Values
retain the original equation and unit evaluation; densities use t/mm³ or kg/m³
and acceleration uses mm/s² or m/s² for the two existing model unit systems.

Pressure selects complete exterior faces using a named boundary node set,
including quadratic midside nodes, or an explicit element set and original face
number S1–S6. Positive pressure acts inward, as in original CalculiX. Original
face-node identities determine correspondence after pyramid conversion. Derived
face element sets belong to the frozen job, preserving the submitted mesh.
Original CalDLoad/CalGravityLoad/CalDensity/CalPlastic emit solver keywords.

The Results toolbar selects step/increment/time and retains the selected field
component when switching increments. Equivalent plastic strain is the original
FRD PE / PE field. Only the selected frame is copied into VTK arrays. The reader
now accepts up to 4096 fields within its existing 64 MiB limit, allowing the
100-field plastic example; the original decoder/invariants are unchanged.

Solve example… adds four bundled, editable input pairs under
`X/Analysis/StaticDeck`: pressure-solids, gravity-column, plastic-tension and
finite-tension. The pressure model covers all ten mechanical solid formulations
plus linear/quadratic pyramids. The other examples use a two-element C3D20
column. The pressure example explicitly selects hexahedron conversion because
of the original wedge-conversion accuracy issue below. Both original conversion
choices remain available, with a visible note in the pressure editor.

## Integration and original comparison

[Receipt](nonlinear-loaded-solids-verification.json) records actual runs. Native
Mac and Linux ARM64 complete the real editor → frozen job → solve → original FRD
→ rendered results workflow for pressure with both pyramid conversions, gravity,
plastic yielding/hardening and finite tension. Plastic and finite tension each
produce 20 increments. The existing Linux PMX save/reopen/solve workflow passes
using the rebuilt affected deck consumer. Linux uses the cached offline native
ARM64 container and available Qt fallback after xcb reports a missing dependency;
this is not a Linux installer or native x64 acceptance claim.

Analytical checks use pressure U3=0.001z / S33=1 MPa; gravity U3=0.001(z-z²/2) /
S33=1-z; and plastic tension S33=1.8181818 MPa / equivalent plastic strain
0.008181818. Free axial unknowns remain between end constraints. New fixture
bounds are 1e-8 displacement, 1e-4 stress and 1e-6 plastic strain, accounting for
original printed/extrapolated output. Existing numerical tolerances are intact.
Finite tension checks the prescribed end motion, Nlgeom keyword and actual
nonlinear stress response, and compares all increments to the original binary.
Raw FORC remains original nodal solver output; body-load sums are not relabelled
as mechanically complete support reactions.

Identical decks also execute with the fingerprint-checked original Windows
CalculiX 2.22 runtime through the retained CrossOver bottle. All five comparisons
pass, including identical mesh identities and displacement values. Maximum stress
differences are approximately 1.2e-12 MPa for pressure/gravity, 9.4e-9 MPa for
plasticity and 1.41e-6 MPa for finite tension. All plastic-strain values match.
This establishes the recorded bounded original-binary comparison, not bitwise
field equality, native Windows acceptance or complete original-app parity.

Affected current analysis, results and execution suites pass, along with existing
desktop regressions and source-ownership/build guards. Initial integration checks
exposed a results project closure missing newly shared original types and a
validation response expectation missing the new load/nonlinear metadata. Both
were repaired and the affected checks rerun. The original PE component name was
also corrected against real solver output. All actual logs are retained.

## Open correctness and parity

[B006](../bugs/B006-quadratic-pyramid-wedge-pressure.md) records a newly measured
original quadratic-pyramid pressure discrepancy. C3D13 converted to a collapsed
C3D15 wedge misses the affine pressure solution by 3.7943e-5 mm displacement and
0.047 MPa stress. The original Windows binary reproduces it. The hexahedron
conversion passes this case; other formulations pass under both routes. The
workflow receipt deliberately records this check as false and overall numerical
acceptance as false even when functional integration succeeds. No solver
algorithm, original conversion or accuracy tolerance is changed to hide it.

D029's original quadratic measurement failure and pyramid classifier failure
also remain unchanged. General curved quality, exact native equality, full PMX
(including these new native-session definitions), other materials/loads/contact,
all other analysis families, shell/beam/2D/axisymmetric workflows, every original
mesher/model/results operation and all four-target/distribution/release gates
remain required work. D057/D058/D059 remain in force. Hosted CI is held; native
Linux x64 is deferred to Windows/Podman near finishing.

## Candidate and publication

Source integration is complete. Publication and copied candidate verification
are being recorded in the receipt before this task is closed.

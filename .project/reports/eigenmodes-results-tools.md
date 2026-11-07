# Frequency, buckling and result inspection tools

Tasks 0092–0094 deliver three connected functional milestones toward identical
PrePoMax 3.0.0 functionality. D061 keeps inherited numerical fixes/improvements
deferred until full parity. Original algorithms and existing tolerances remain;
the unavailable Intel/PARDISO solver is the sole final-functionality exception.

## Task 0092 — Frequency analysis

Configure… → Analysis type / modes selects Frequency, a mode count and optional
lower/upper frequencies in Hz. Original FrequencyStep data/equations/serialization
and CalFrequencyStep keywords remain shared; only original legacy support-type
methods move mechanically to their original net48 partial. Assembly/serialized
ownership and original methods remain intact. Every section requires density,
linear elasticity and homogeneous displacement supports. Applied loads are
refused for this ordinary frequency workflow. Native jobs preserve their inputs.

Solve example… → Frequency — axial rod modes supplies a 152-node/12-C3D20
rectangular rod with E=1000 MPa, density 0.001 t/mm³, nu=0 and axial unknowns.
The first three stored frequencies are 250.00005, 463.1218 and 750.01227 Hz.
The first is within 0.001 Hz of the independent 250 Hz rod solution. Its nodal
shape agrees with the analytical sine to relative error about 1.05e-6, checked
at 1e-5. The transverse distribution of other eigenmodes is retained; the three
numbers are not incorrectly labelled as three purely longitudinal harmonics.
The frame selector displays original mode numbers and frequency units.

## Task 0093 — Linear buckling

Configure… → Analysis type / modes selects Buckling, a requested factor count
and the original accuracy setting. Original BuckleStep/CalBuckleStep generate
the analysis. Homogeneous supports and a nonzero reference load are required.
The existing concentrated-force/pressure/gravity adapters preserve original
load semantics. Eigenvalue jobs require nonempty FRD/DAT; static jobs keep their
existing strict FRD/STA and requested-history DAT contract. A successful process
is not numerical acceptance.

Solve example… → Buckling — cantilever column supplies 248 nodes/20 C3D20
cells, cross-section 1 × 0.5 mm and length 10 mm, E=1000 MPa, nu=0. Eight top
nodes each receive -0.0125 N, total -0.1 N. The stored factors are 2.5661845,
10.216758 and 22.811197. The lowest is about 0.16% from the slender Euler
approximation 2.5702095; the comparison bound is 2% because the 3D solid column
and slender beam approximation are distinct models. No existing tolerance was
changed. The FRD reference-load state at zero is labelled separately from the
three buckling modes, retaining original increment identities.

[B007](../bugs/B007-buckling-search-shift.md) records an inherited original
solver search limitation: tenfold reference-load scaling can omit a lower mode
below the original unit search shift. Native Mac and original Windows binaries
agree. The bundled load is explicit, with no automatic rescaling. The editor
notes the limitation; solver changes are deferred under D061. Do not claim the
returned factors always include the lowest critical factor.

## Task 0094 — Deformation, animation and histories

Results now offer a Deformed checkbox, signed display scale and an undeformed
wireframe outline. Display points use original decoded displacement components
and original node-value identities with x + scale*u; field magnitudes/invariants,
connectivity and authoritative coordinates remain unchanged. All transported
midside nodes deform. Eigenvector amplitudes retain original normalization and
are explicitly described as arbitrary. Original IDs remain on the displayed VTK
points/cells for picking. Disabling deformation restores original coordinates.

Play supports increment sequence animation and a sinusoidal current-shape cycle;
pause restores the full selected deformation. Changing the scene stops animation.
These are viewport operations, independent of engineering results or persistence.

Histories… opens ordinary nodal/integration-point DAT histories through the
original C# decoder. A searchable series selector, plotted curve and original-
value table retain step, set, component, node/element and integration-point
identity. Export selected/all CSV preserves stored times/values and series
metadata, publishing atomically to a new file and refusing existing destinations.
DAT quantities remain as stored; no unit inference or force reinterpretation is
added. The plastic example exercises 20 increments. Eigenvalue/participation DAT
tables, arbitrary derived histories, interactive plot operations and movie export
remain additional required results work; modal values are currently in the FRD
frame selector. This does not claim complete original result preprocessing.

## Integration and original comparison

The [receipt](eigenmodes-results-tools-verification.json) records actual source,
native/reference workflows and candidate/publication state. Mac source completes
the combined frequency/buckling/plastic-history workflow. Final Linux ARM64
completes the same workflow plus the analytical sine check and graph layout.
The Linux PMX save/reopen/solve regression passes with rebuilt affected hosts.
Linux uses the existing offline native ARM64 image and Qt fallback; neither a
new Linux package nor native Windows/x64 platform acceptance is claimed.

Identical native frequency/buckling decks and the larger reference-load diagnostic
execute in the existing CrossOver bottle with fingerprint-checked original
Windows CalculiX 2.22 and its five DLLs. Stored frequencies/factors match exactly.
Eigenvectors may have arbitrary nonzero amplitude/sign, so comparisons record
modal assurance and displacement-derived scalar alignment of original raw vector/
tensor components. Observed shape MAC is essentially 1; maximum relative raw-
field residual is about 6.1e-9. Comparison bounds are eigenvalue relative 1e-5,
MAC >=0.99999 and aligned raw field relative L2 <=0.001. Raw fields are retained;
this is not bitwise equality or exhaustive modal/degenerate-eigenspace acceptance.

Affected current analysis/results/execution suites, existing 52 desktop
regressions, 12 ownership and 9 build guards pass. An existing modal-rejection
check now verifies original frequency classification because frequency is
intentionally supported. The unrelated mathematical checks remain intact.
The static-only test helper casts its known static fixture after the shared
factory begins returning original Step. Earlier failed integration logs remain.

The source Python environment was missing package source/metadata files; all
20 exact pinned runtime/packaging wheels were restored from the existing local
pip cache with SHA256 checks. The retained task 0090 app still started. Stale,
unowned Podman sockets were removed after confirming the VM stopped and no
process owned them; its disk/configuration were preserved. No dependencies were
upgraded and no hosted runner or external package download was used.

## Remaining parity and delivery

Ordinary single-step linear elastic solid eigenproblems are implemented here.
Prestressed/perturbation sequences, cyclic/complex frequencies, modal storage/
restart and downstream dynamics, other analysis/element/material/contact/load
families, all original meshers and model operations, general/native-session PMX,
full result operations and large-model limits remain mandatory work. Existing
D029 integration/classification failures, B006 pressure accuracy and B007 search
behavior remain explicit and deferred, alongside exact native/four-target/
distribution/release acceptance. D057/D058/D059/D060/D061 remain in force.

Implementation is ready for research publication and one copied Mac candidate.
Final candidate checks, cleanup and actual publication will be recorded here
and in the receipt before these three tasks are closed.

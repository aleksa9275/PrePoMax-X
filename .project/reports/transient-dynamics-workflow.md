# Original implicit and stored-basis modal transient dynamics

Tasks 0101/0102 connect two original calculation families through the desktop:
linear implicit transient solid dynamics and stored-basis modal transient solid
dynamics. Original DynamicStep, ModalDynamicsStep, Damping/ModalDamping,
CalDynamicStep/CalModalDynamicsStep and damping keyword writers remain the
engineering implementation. No integration, eigensolver, tolerance, numerical
precision or solver-default changes are made. Original model-dependent support
methods move mechanically to guarded net48 partials with unchanged serialized
fields and assembly ownership. D061's parity-first sequencing remains in force.

Configure… offers both analysis kinds and a Dynamics tab: original implicit HHT
alpha (default −.05, bounded −1/3 to 0), fixed/automatic implicit increments,
Off/Rayleigh damping, and modal Off/Constant/Rayleigh damping with stored basis
count/name. Existing time, density, named zero-displacement supports, mechanical
loads, output and tabular-amplitude controls feed the calculation. Density is
required for every section. Nonlinear/plastic dynamics, nonhomogeneous/time-
variable supports, initial velocity and relative-to-absolute conversion remain
explicitly outside this implemented transport; all remain required for parity.
Modal increments use the original modal dt/period semantics; implicit Direct
and HHT controls do not apply to modal dynamics.

Modal jobs regenerate their frequency basis in the same frozen job/deck, using
original `*Frequency, Storage=Yes`, then emit the original modal step. Supports
belong to the basis and are inherited without duplicate modal BC changes. The
job requires its own nonempty `.eig`, FRD, DAT and STA; a prior basis file cannot
satisfy the job. Basis eigenvectors retain their arbitrary amplitude and mode
identity in the selector; physical displacement/velocity frames retain step 2
and their original time/increment identities. Ordinary frequency/buckling and
all earlier static/thermal/PMX workflows retain their existing boundaries.

Original FRD decoding now admits VELO and ENER component layouts. Implicit
energy output uses the original DynamicStep default. Modal output adds original
velocity; no synthesized energy or velocity field is created. Original DAT
velocity datasets flow through the shared decoder and history entry operations.
A complete, finite, ordered four-table stored-frequency preamble is checked
before the original step-2 history parser runs. The API explicitly returns
`ExcludedBasisTables`, and the history dialog identifies this exclusion. Unknown,
partial, nonfinite or inconsistent preambles fail. Existing 8-MiB, 256-dataset,
250000-sample limits, original value semantics and unknown-record rejection
remain unchanged. Histories offer graph/table/CSV; physical frames support
selection, deformed shape, undeformed outline and increment animation. Playback
cycles within the selected original step, preventing physical transient frames
from wrapping into the arbitrary-amplitude frequency basis. Visual inspection
exposed this integration defect after initial checks; a focused regression and
stronger end-to-end assertion now enforce the separation.

## Independent verification examples

Four examples use the original unit C3D8 cube, E=1000, nu=0, rho=.001, lateral
DOFs fixed and one axial end clamped. A ramp reaches total force 1 at t=.0064;
64 increments have dt=.0001. The symmetric axial response has consistent mass
M=rho*V/3=.001/3, stiffness K=EA/L=1000 and omega=sqrt(3000000), frequency
275.6644477. One stored symmetric axial mode spans the applied load exactly.
Undamped and 5%-damped examples exercise both procedures. Implicit damping uses
Rayleigh mass coefficient 2*zeta*omega; modal damping uses original constant
ratio .05. These are explicit example settings, not changed product defaults.

The independent oracle solves M*u''+C*u'+K*u=t/T: modal response uses the closed
form damped ramp solution, implicit alpha=0 uses an independently implemented
average-acceleration Newmark recurrence. Every nodal displacement/velocity and
DAT history sample is checked, with displacement bound 2e-8, velocity/history
2e-5, and implicit strain-energy density against .5*E*u² at 1e-7. Observed FRD
errors are below 4.6e-9 displacement and 5.1e-7 velocity; DAT error below 5e-8.
Implicit continuum discretization differences (up to 2.13e-6 displacement and
.00430 velocity) are retained separately and not mislabelled as solver defects.

## Actual checks and delivery

Source Mac ARM64 and cached native Linux ARM64 desktop workflows pass all four
examples, including frozen inputs, original mode/time identities, physical frame
animation, velocity graph/table/CSV and original strain energy. Identical-deck
pinned original Windows CalculiX 2.22 comparisons through CrossOver pass; basis
frequencies and eigenvector MAC are checked separately from physical fields.
This is not native Windows application acceptance. Linux x64 remains deferred
under D059, hosted CI is skipped under D058. Affected engineering and desktop
checks and candidate publication/verification are recorded in the
[receipt](transient-dynamics-verification.json). Implementation `60471505` and final playback repair `57e19d2c` are pushed and
remote-verified on origin/research/native-feasibility with CI explicitly skipped.
Current Analysis/Results/Execution suites, 73 desktop regressions (including eight
dynamics behaviors), 12 ownership guards and nine build guards pass. Initial
closure/build and verifier-count failures remain in the evidence logs. Original
engineering source closure is 213 entries; existing numerical gates stay open.

The retained candidate is `/tmp/prepomaxx-task0102-delivery/PrePoMax-X Preview.app`;
its sibling `Native CAD Preview.command` enables the retained native CAD runtime.
Both copied viewports pass all four dynamics cases (86 checks each); copied
thermal, thermomechanical, eigenmode, nonlinear-solid and PMX regressions pass.
Actual native Cocoa screen/ID/scalar/resize checks pass. All 2466 payload file
hashes, 2276 symlinks, exact source identity `57e19d2c`, empty source patch and
ad-hoc signature verify. Configuration, graph/table and physical contour images
were visually inspected, including the corrected final step-2 animation.

The old task 0100 app, initial superseded task 0102 copy and duplicate package
payloads are pruned after verification. Logical bytes removed total about 10.08 GB;
measured free space increases about 8.88 GB. Current candidate, jobs/models, raw
reference outputs, screenshots, logs/source manifests, installed user state and
shared tools/caches remain. The old launcher forwards to the current candidate.
The local Linux VM is restored to its initial stopped state.

All other original calculations/elements/material/contact/model/CAD/mesher/
results/automation and general native-session PMX functions remain required.
General multi-step editing/basis reuse, initial conditions, nonlinear/explicit/
cyclic/modal damping-table breadth and other dynamics controls remain open.
D029/B006/B007 and the coarse conductivity accuracy diagnostic remain open;
D057/D058/D059/D060/D061 and all four-target/distribution/release obligations
are preserved. Unavailable Intel/PARDISO remains the sole solver exception.

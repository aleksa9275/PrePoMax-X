# Radiation, amplitudes and temperature-driven solid stress

Tasks 0098–0100 deliver three connected original-functionality milestones:
nonlinear radiation/thermal material tables, tabular amplitudes, and prescribed-
temperature solid expansion/stress. Original material, amplitude, load, initial/
defined-field and keyword classes remain authoritative. No solver, integration,
extrapolation or original numerical tolerance changes. D061's parity-first
sequencing and every existing correctness/parity/four-target/release gate remain.

## Task 0098 — radiation and temperature-dependent heat transfer

Heat inputs / convection now includes non-cavity RadiationHeatTransfer. Its
magnitude is emissivity in [0,1], with a sink temperature and complete exterior
faces selected by a named boundary node set. Heat transfer edits explicit
absolute zero and Stefan–Boltzmann constants in model units; both are required
for radiation. The original ModelProperties/CalPhysicalConstants and
CalRadiationHeatTransfer emit these definitions. Input emissivity is checked
before the original setter, preserving its original clamping behavior without
silently clamping tool input. Below-absolute-zero temperatures are refused.

Thermal property tables supports conductivity, specific heat and density with
original equations and quantity converters. Rows must have positive finite values
and strictly increasing temperatures; scalar and table definitions for one
property cannot coexist. Original Material.TemperatureDependent and material
keyword writers retain interpolation and solver behavior. Transient calculations
still require density and specific heat, scalar or table. This is isotropic
solid heat transfer; cavity radiation and anisotropic materials remain required.

## Task 0099 — tabular amplitudes

Amplitudes edits named original AmplitudeTabular definitions, ordered time/value
points, original StepTime/TotalTime and ShiftX/ShiftY, with target bindings. They
can attach to the implemented displacement, force, pressure, gravity, temperature
boundary, nodal/body/surface heat-input and prescribed-temperature adapters.
Film coefficients and radiation emissivity have their separate original amplitude
references. Missing/duplicate definitions or targets and malformed/unordered
points fail before solving. Existing snapshot adapters preserve amplitude names.

Original CalAmplitude and BC/load/defined-field writers emit the definitions.
Temperature amplitude multipliers apply to the entered absolute temperature,
not an inferred temperature change. Original linear static analysis evaluates the
final state; setting small static time increments does not turn it into transient
analysis. The UI explains this. The heat-transfer example demonstrates a stored
pulse history; nonlinear/dynamic amplitude breadth remains subject to its own
original calculations, with full dynamic/modal/multistep functionality still due.

## Task 0100 — prescribed-temperature expansion and stress

Thermal expansion / stress edits original constant isotropic expansion and its
explicit reference temperature, a uniform initial temperature, and named-region
DefinedTemperature values for a static mechanical step. Current transport
requires full, nonoverlapping nodal temperature-field coverage. Original
CalThermalExpansion, CalInitialTemperature and CalDefinedTemperature emit the
calculation. Supports and mechanical loads retain their original meaning.
Original displacement, strain, stress, reaction, deformation and DAT histories
remain available. This does not infer or run a coupled thermal calculation.

Original preview/model-dependent members and file-temperature path handling stay
in mechanically guarded net48 partials, retaining original assembly ownership,
serialized names and Windows behavior. ModelProperties' mesh-formulation
extension methods stay in its legacy file. Its original CaeResults slip-wear enum
remains in CaeResults; the expanded analysis dependency check admits that exact
owner only in ANALYSIS_SLICE. The base Core guard stays unchanged. Shared integration
orchestration validates admission and delegates to original keywords.

## Runnable examples and independent verification

Solve example… offers six new cases; the new definitions appear in the model
tree and editable tabs. Times, units, inputs and original result identities are
frozen with each job. Histories remain original-value graph/table/CSV operations.

| Example | Independent result and observed behavior |
|---|---|
| Radiation surface cooling | Unit rod, k=.01 mW/(mm·°C), bottom 100 °C, top radiating to 20 °C, emissivity .8, sigma=5.670374419e-11 mW/(mm²·K⁴), absolute zero=-273.15. Scalar conduction/radiation balance gives top 70.34777316 °C and heat flow .29652227 mW. Temperature bound 5e-5 °C, boundary heat balance 1e-6 mW. |
| Variable conductivity | k(T)=1+.01T, ends 0/100 °C: T=100(sqrt(1+3z)-1). 32 C3D20 cells and forty explicit original increments give maximum stored nodal error .00134386 °C, below the new fixture's .002 °C bound. |
| Pulsed heating | Insulated unit volume, rho=.001, c=1000, initial 10 °C, unit body power times triangular amplitude (0,0),(.5,2),(1,0). Integrated energy gives final 11 °C. Twenty original backward-Euler increments satisfy the independent discrete energy balance within 1e-5 °C. Maximum continuum-time error .05 °C is the expected finite-step error, checked at .0501 without changing the solver. |
| Scaled static force | Original unit cube, E=1000 MPa, nu=.3, total reference force 100 N; amplitude ends at .5. Original single final frame gives sigma11=50 MPa, u1=.05x and u2/u3=-.015y/z. All displacement values checked at 2e-7 mm; original nodal extrapolation at .005 MPa, integration-point stress at 1e-4 MPa. |
| Free thermal expansion | Unit cube, E=1000, nu=.3, alpha=1e-5 /°C, reference/initial 20 °C, final 120 °C with symmetry supports: u=.001x and stress zero. Displacement bound 2e-7 mm; stress bound 1e-8 MPa. |
| Restrained thermal expansion | Same cube with axial end restraint: u1=.0013x, u2=.0013y, u3=0, sigma33=-1 MPa. Displacement bound 2e-7 mm; original nodal stress extrapolation bound 5e-5 MPa, integration-point stress at 1e-4 MPa. |

The coarse conductivity diagnostic is retained. Original one-increment defaults
produce maximum temperature error .07975413 °C against the same analytical
solution and fail the .002 °C check; explicit increments .05 and .025 reduce it
to .00264386 and .00134386 °C. The original Windows solver reproduces the coarse
result. Only the runnable example's explicit original controls are refined;
there is no automatic rescaling, default/tolerance change or numerical repair.
Further investigation is recorded in the post-parity backlog. A successful
functional solve never marks that retained coarse accuracy check passed.

## Actual verification, publication and remaining work

The [receipt](radiation-amplitudes-thermal-stress-verification.json) records actual
native/reference workflows, candidate, publication and cleanup. Mac and Linux
ARM64 complete all six desktop workflows. Pinned original Windows CalculiX 2.22
through CrossOver agrees on identical decks, meshes, field/history metadata and
values. Maximum decoded field difference is about 2.03e-7, including derived
principal values near degeneracy; raw histories differ by at most about 1.7e-12.
No native Windows application or Linux x64 acceptance is claimed. Hosted CI
remains off under D058; D059 still defers Linux x64.

Current Analysis/Results/Execution engineering suites, 65 desktop regressions
(including seven new admission/editor behaviors), 12 ownership and nine build
guards pass. The guard/test updates account for newly supported original
functionality and its original assembly dependency; existing numerical checks
and D029/B006/B007 failures remain unchanged. Initial build/assertion failures
and native diagnostics remain retained. Configuration/history/contour captures
were visually inspected. Publication and the copied candidate are pending the
final delivery checkpoint in the receipt.

Required remaining work includes coupled/sequential temperature-displacement,
nonuniform initial fields, file/result-derived temperatures, mechanical thermal
property tables, anisotropy, cavity radiation, additional amplitude forms,
other element/analysis/material/contact/model/mesher/results functions,
general/native-session PMX, automation, large-model limits, exact native parity
and every original four-target/installer/release obligation. D057/D058/D059/
D060/D061 remain in force; unavailable Intel/PARDISO remains the sole solver
exception. These scoped increments remove no final-functionality requirement.

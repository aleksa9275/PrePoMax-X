# Connected original thermal analysis

Tasks 0095–0097 deliver three substantial original-functionality milestones:
steady conduction, transient conduction and thermal inputs/convection. They use
original CaeModel material/step/BC/load data, equation/unit conversion and
CalculiX keyword classes, the existing native solver/job path, and original
FRD/DAT decoding. No thermal element, integration, extrapolation or solver
algorithm is rewritten. D061's deferred numerical work stays deferred.

## Task 0095 — steady heat transfer

Configure… → Analysis type / modes now includes Heat transfer. Heat transfer
edits conductivity, specific heat, initial temperature, steady/transient selection,
original Direct/automatic time controls and Deltmx. Temperature boundaries edit
constant prescribed values on named node sets. Sections assign thermal materials
to the imported solid mesh. Conductivity must be positive; a steady problem
requires a temperature boundary or positive convection to a sink. Mechanical
properties/supports/loads must be removed explicitly when changing analysis type.
Original mesh identity and all midside nodes remain intact.

The native jobs request original NT/RFL/HFL outputs. Temperature, heat-flux vector
components/magnitude and stored nodal heat flow appear in the viewport with
original node/element IDs. Unsupported/unconfigured inputs fail before solving;
solver failures retain the original job outcome. Heat-transfer jobs retain the
strict FRD/STA and requested-history DAT contract. They are not misclassified as
eigenvalue jobs. The definition JSON is frozen job configuration, not PMX.

## Task 0096 — transient heat transfer

Transient calculations additionally require density, specific heat and an explicit
uniform initial temperature. The original initial-temperature and HeatTransferStep
keywords drive the solver. Time period, increments, automatic/Direct controls,
maximum increments, output frequency and optional maximum temperature change
are editable. Stored frames support selection and increment animation. Thermal
DAT histories use the existing searchable graph, original-value table and atomic
new-file CSV export. No inferred units or reinterpretation of stored RFL is added.

## Task 0097 — heat inputs and convection

The desktop supports original CFlux (power per selected node), BodyFlux
(power/volume on an element set), DFlux (inward power/area on complete exterior
faces selected by a boundary node set), and FilmHeatTransfer (positive film
coefficient and sink temperature on those faces). Face topology and all midside
nodes determine exterior membership; job-owned surface/face-set keywords are
created without changing the model. Missing/incomplete regions and overlapping
loads of the same kind fail. Surface flux and convection may share faces as
original distinct physical contributions. Radiation and arbitrary amplitudes
remain required additional functionality.

Original shared classes retain their assembly/serialized ownership. Only preview
methods and model-dependent constructors move mechanically into net48 legacy
partials. Existing Windows methods, serialization names and numerical bodies
remain intact. `thermal_layout.py` reproduces these extractions from the pinned
original source; ownership checks include both halves and original project entries.
The new mesh-independent constructors accept constant named-region snapshots.

## Runnable examples and analytical checks

Solve example… offers six thermal cases in mm · N · s · °C. Power is mW,
conductivity mW/(mm·°C), heat flux mW/mm², specific heat mJ/(t·°C), and film
coefficient mW/(mm²·°C). The m · N · s system uses W, m, kg and J consistently.
Original quantity converters also accept explicit compatible unit strings.

| Example | Independent result |
|---|---|
| Steady conduction | 1 mm rod, k=1, ends 0/100 °C: T=100z, qz=-100 mW/mm² |
| Transient heating | Insulated unit volume, rho=0.001, cp=1000, generation 1: T=10+t °C; 20 increments to 11 °C |
| Surface heat flux | Bottom 0 °C, top input 10 mW/mm²: T=10z, qz=-10 |
| Body heat generation | Both ends 0, generation 8 mW/mm³: T=4z(1-z), qz=8z-4 |
| Convection cooling | Bottom 100, top sink 20, h=2: top 46.6666667 °C, qz=160/3 |
| Nodal heat input | Four top C3D8 nodes at 2.5 mW each: T=10z, total 10 mW |

Five cases use four original C3D20 cells/56 nodes; nodal heating uses four C3D8
cells/20 nodes. These are verification/example fixtures, not an application mesher.
All stored node/time temperatures are checked against the equations above within
5e-5 °C; the largest observed discrepancy is the 6-digit FRD convection value
(3.3333e-5 °C). Original extrapolated nodal flux differs by at most 0.005 mW/mm²
in the 100 mW/mm² case, checked at 0.006; uniform integration-point DAT flux
is independently checked at 1e-4. Existing tolerances and extrapolation stay intact.

Stored RFL must be interpreted with the original solver convention. For quadratic
body heating it sums to -11/3 mW at each prescribed end. Consistent body-source
contributions on those boundary nodes are 1/3 mW per end (Q × end-cell volume / 6).
Subtracting those gives -4 mW/end and the independent 8 mW heat balance. Raw
FRD/DAT RFL is preserved. Native and original Windows results reproduce this;
this is not a new correction or a general RFL postprocessing implementation.

## Verification and remaining scope

The [receipt](thermal-analysis-workflow-verification.json) records actual commands,
source/native/reference/candidate evidence, publication and cleanup. Mac and
Linux ARM64 each complete the six-case native desktop workflow with analytical
fields/heat balance, frozen inputs, original IDs, all thermal frames and history
plot/table/CSV. Native Mac and pinned original Windows CalculiX 2.22 through
CrossOver agree on identical decks, node/element identities, field/history
metadata and values; maximum decoded field difference is about 3.72e-13.
This is not native Windows application/platform acceptance or bitwise equality.

Affected current Analysis, Results and Execution engineering suites pass, as do
58 desktop regressions (including six thermal behavior tests), 12 analysis
ownership guards and nine build guards. Initial infrastructure/assertion logs
remain retained. Affected source packages stay pinned. Hosted CI is held under
D058; Linux x64 remains deferred under D059. Candidate packaging/publication is
pending the final integration checkpoint recorded in the receipt.

Single-step isotropic constant-property solid heat transfer and constant thermal
inputs are implemented here. Coupled/sequential thermoelasticity, nonuniform
initial temperatures, temperature-dependent/anisotropic properties, radiation,
amplitudes, shell/2D/axisymmetric thermal workflows, thermal pyramid conversions,
all other original analysis/element/material/contact/model/mesher/result tools,
general/native-session PMX and large-model acceptance remain required work.
Original D029, B006 and B007 failures are unchanged and deferred. D057/D058/D059/
D060/D061, exact parity, four-target/installers and full release gates remain open.

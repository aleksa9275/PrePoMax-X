# Remaining element-family milestones: delivered workflows and open acceptance

Tasks 0107–0110 implement the requested remaining four work areas after tasks
0103–0106. The eight-step plan is a delivery sequence, not a reduction of D060's
full original-functionality target. This increment connects discrete elements,
broader calculations, imported-mesh editing/boundary creation and checked original
PMX family exchange. **Full milestone-8 acceptance remains open**, including new
native-session PMX writing and the required Windows/Linux x64/platform/release
checks. General original mesher/editing and calculation breadth also remain.

[Actual receipt](element-family-completion-verification.json) identifies source,
commands, jobs, retained failures, candidate, publication and cleanup. D057–D061
remain in force. No numerical algorithm, existing tolerance or solver exception
is changed. D029/B006/B007/B008, coarse conductivity and axisymmetric findings
remain explicit.

## Discrete elements — task 0107 / milestone 5

Exact MASS, SPRING1, SPRING2, SPRINGA and GAPUNI input records construct the original
MassElement/LinearSpringElement/LinearGapElement classes. Original CalElement,
MassSectionData/CalMassSection, LinearSpringSectionData/CalLinearSpringSection and
GapSectionData/CalGapSection own emitted definitions. There is no prefix alias
fallback, node reordering or material attached to a discrete section.

Configure → Sections adds mass/spring/gap kinds; leave their material blank.
Configure → Mass / spring / gap supplies mass per element, stiffness, spring DOFs,
gap clearance/direction and optional tensile force. Quantities use the original
unit/equation converters (tonnes with mm/N/s; kilograms with m/N/s). Translational
SPRING1 DOFs are 1–3; SPRING2 supplies both DOFs; SPRINGA follows its two-node axis.
No automatic surface spring distribution, reference-point mass expansion or local
coordinate-system breadth is claimed by this imported-element boundary.

Examples verify spring displacement F/k=.01, gap compression -.01, the two lowest
four-mass-chain frequencies and a force-driven m=2, k=1000 transient. The .005 s
step produces maximum displacement error below 5e-5 against
u=.01(1-cos(sqrt(500)t)); this is the new fixture's time-discretization check,
not a relaxed existing comparison bound.

Original CalculiX deliberately omits MASS and one-node springs from FRD topology.
A frozen heading records original/output counts and explicit omission count;
readers validate these without inventing elements or field values. A pure ground
spring has no FRD nodes/values. The desktop keeps its source mesh visible and
makes original DAT nodal histories available. Original IDs remain in picking;
presentation vertices/lines for the original empty-VTK discrete classes change no
engineering data. Mesh export/reopen retains exact types and source connectivity.

## Calculation combinations — task 0108 / milestone 6

The blanket static-only family restrictions are removed. The existing original
static/frequency/buckling/implicit/modal step writers and their safeguards are
used for compatible imported families. New actual workflows cover beam, shell,
plane and axisymmetric frequencies, a shared-node solid/spring series-stiffness
model and implicit beam transient response with velocities and histories.
Frequency examples use original FRD modes; the bounded DAT time-history reader
does not relabel eigenvalue-number tables as physical-time histories.

Explicit original field/history-output descriptors preserve PMX output names and
variable flags instead of silently substituting defaults. The DAT boundary now
allows up to 4096 datasets within the unchanged 8 MiB/250000-scalar limits; the
80-frame beam example exposed the former 256-dataset transport limit. Unknown,
duplicate, malformed and over-limit data remain refused. Original DAT algorithms
and field/invariant math are unchanged.

A tiny one-DOF ARPACK example printed *ERROR but exited zero with nonempty output
headers. The job runner now retains failure whenever CalculiX explicitly reports
an error; the real-process regression covers this case. Completed file transport
continues to establish no numerical acceptance.

The beam stored-basis modal transient example still fails on Mac/Linux ARM64 and
with the pinned Windows solver through CrossOver. Its original zero-load DOF
initialization requirement is emitted through the original user-keyword route;
this does not resolve the remaining crash. The diagnostic menu entry stays
explicit. Job failure retains model and frozen inputs. See [B009](../bugs/B009-modal-beam-and-invariant-diagnostics.md).
Other original calculation/material/orientation/interaction combinations remain
required; admitting a step is not exhaustive acceptance of every combination.

## Mesh authoring — task 0109 / milestone 7

Edit mesh… provides translation, axis-angle rotation, positive scaling, complete
ID renumbering and extraction of complete exterior surface/edge meshes. Original
FeMesh point transformation bodies are mechanically moved into a shared partial;
`mesh_edit_layout.py` guards them and the retained full FeMesh against the exact
prior checkpoint. The existing CAD numbering repairs remain preserved.

Original element face ordering supplies shell/membrane/plane triangles/quads and
linear/quadratic beam/truss edges. Extracted nodes retain source IDs; new boundary
elements have explicit new IDs. All selected midsides must be present, internal
faces are excluded and incompatible formulations are refused. Existing native
CAD meshing may supply the source mesh; export/reopen INP before editing a
CAD-owned mesh, so edits cannot corrupt its geometry/recipe ownership.

Up to 20 owned mesh snapshots support exact-byte undo/redo. Failed validation or
publication preserves the active model/history, renumbering updates every named
set, and extraction clears incompatible analysis assignments. Physical load
vectors remain in their selected global coordinates. Every edited mesh is read
back by the original guarded reader before adoption/new-file publication.
General direct CAD surface/line meshing, remeshing, extrusion/revolution, other
original mesh tools/backends and selection breadth remain parity work. This
boundary is not a claim that all original mesh authoring is finished.

## PMX/platform compatibility — task 0110 / milestone 8

The new safe NRBF projection never instantiates serialized application types or
replays command history. The original binary mesh prefix maps all 14 original
serialized line/surface/solid topologies to unchanged original factories. Graph
part membership, enum formulation values, named sets, units, sections, global
supports/forces, static controls and output definitions are checked before native
solve. Original effective selection regions can be projected while their saved
selection/history bytes remain unchanged.

Six original-app projects cover shells, mixed solid topologies, plane stress,
plane strain, axisymmetric and membrane models. They pass original PMX open →
identical Save As → reopen → native solve. Original graph/model/history bytes are
preserved. The pinned original Windows 3.0.0 executable reopens each copied PMX;
its re-exported model semantics match the original captures. The source archive
and executable hashes are retained. This remains CrossOver reference evidence,
not native Windows application acceptance.

The family PMX dialog is read/solve/exact-copy only. **It does not serialize new
native sessions or edit these broader graphs.** Existing checked static-solid/CAD
PMX editing continues through its previous contracts. Result-bearing projects,
custom keywords, richer materials, other model/step families and full bidirectional
new-session persistence remain required. No tool/job JSON is called PMX.

Mac and Linux ARM64 complete 135 family checks and 58 original-PMX checks each.
Their emitted decks and decoded topology match exactly; existing numerical
comparison bounds pass, with modal sign comparison where needed. Exact field
identity is recorded separately. The Linux VM is restored stopped. Windows x64
and Linux x64/native-display/four-target acceptance remain open under D059 and the
available environment. No hosted CI is run under D058.

Original Windows solver comparisons retain one strict failure: beam transient
SGN_MAX_ABS_PRI at a near-pure-shear point changes sign between approximately
±1.5048901e-6. The raw stress tensors, Mises and Tresca agree within existing bounds;
principal extremes tie in magnitude to stored precision. The observed signed
invariant difference 3.0097802e-6 fails the unchanged bound. No sign normalization
or tolerance change is made; B009 records the unresolved interpretation/cause.
All other recorded comparison values meet existing bounds. Full numerical,
exact-native, full-functionality, PMX, distribution and release acceptance remain
false.

## Verification and delivery

Current Core/Analysis/Execution checks pass. The six added results regressions
bring Results to 90 checks; its final run passes. All 95 desktop tests pass with
the current source host supplied, including discrete controls, exact mesh
undo/redo, publication refusal and zero-exit solver-error handling. Nine build
tests and three PMX topology/enum transport tests pass. Initial build/test setup
failures and raw logs remain in the receipt; missing historical binaries and
headless Mac OpenGL were corrected as test setup, not passed over.

Implementation **1580fa9c2405c4652374eeb664df963a22acd078** is committed, pushed
and exact-remote verified on origin/research/native-feasibility with CI skipped.
The retained internal preview is
`/tmp/prepomaxx-task0110-current-delivery/PrePoMax-X Preview.app`; its sibling
`Native CAD Preview.command` uses the existing native CAD runtime. Use Solve
example… for the new families, Configure → Mass / spring / gap for their section
controls and Edit mesh… for imported-mesh authoring.

Both copied viewports complete all 135 new-family checks and 58 family-PMX checks.
Copied prior regressions pass: structural 164, plane 87, dynamics 86, thermal 132,
thermomechanical 84, eigenmode 64, nonlinear 70 and existing PMX 17. Actual Cocoa
screen rendering, original-ID/scalar picking and resize pass ten checks on the
mass/spring mode result. Representative actual screenshots are visually inspected.
All **2521 payload file hashes**, **2276 symlinks**, exact code identity, empty
source patch and ad-hoc signature verify. The package's dirty flag comes only
from the four pre-existing Finder files; no changed code is bundled.

The task0106 app, duplicate new dist/build/host/cache payloads and this session's
extracted original Windows reference app are pruned after verification. Source,
models, jobs, raw reference outputs, screenshots, metadata and shared solver/
Python/.NET/PMX/Podman caches remain. Installed user app/state are untouched. The
retained candidate is rehashed and signature-verified after cleanup. About 5.58 GB
logical data is removed, with about 4.99 GB measured free-space gain. Generated
older CAD launchers forward to the current candidate. The reusable original ZIP
remains; historical extracted payloads need not be rebuilt merely because their
paths occur in retained evidence.

These delivered boundaries do not close the open work listed above or any
D057–D061/full numerical/PMX/four-target/distribution/release gate.

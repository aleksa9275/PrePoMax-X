# PrePoMax release parity tracking

Maintainer direction, 3 November 2026 (D054): **3.0.0 is the initial parity
target**. Continue tracking future upstream releases and maintaining open-source
macOS/Linux distributions even if upstream does not accept the contribution.
Windows x64, Linux x64, Linux ARM64 and Apple Silicon macOS ARM64 remain required.

Original specification reaffirmed, 6 November 2026 (D060): **IDENTICAL functionality,
including every original mesh type and calculation; the unavailable Intel/PARDISO
solver is the sole exception**. Static-solid or preview-only delivery is an intermediate
checkpoint. Nothing in the coverage table below removes a missing capability
from the final requirement. A failed PrePoMax measurement check does not prove
that the separate CalculiX formulation is unavailable.

D061 sequencing, 6 November 2026: deliver full original functionality first,
then implement the [recorded correctness fixes and improvements](reports/deferred-correctness-improvements.md).
Inherited failures remain explicit and original algorithms/tolerances remain
during the parity phase. Necessary port/integration repairs still proceed.
Deferral closes no numerical, exact-parity, platform or release gate.

## Mandatory breadth

| Original area | Required scope, still open beyond the verified increments |
|---|---|
| Elements and meshes | All original line/beam/spring/gap, triangle/quadrilateral, tetrahedron/pyramid/wedge/hexahedron families; linear and quadratic forms and every supported formulation alias, including shell, membrane, plane and axisymmetric uses. Original pyramid conversion, element ordering, sets, surfaces, parts and mesh operations must retain their semantics. Sources: `CaeMesh/Elements`, original mesh/input/output owners. |
| Meshing | Every original mesher, setup item, order, CAD midside behavior, mesh refinement/control, structured/extruded/revolved/transfinite and mesh editing workflow, as present in verified 3.0.0. Current native tetrahedral delivery does not substitute for the others. |
| Calculations | Original static/nonlinear, frequency/complex-frequency, buckling, dynamic/modal/steady-state dynamics, heat transfer, coupled/uncoupled temperature-displacement, boundary-displacement and slip-wear steps, with their original supported combinations. Sources: `CaeModel/Steps`; exact stable-release correspondence remains required. |
| Model semantics | All original materials, sections/composites, constraints/interactions/contact, amplitudes, initial/defined fields, coordinate systems, supports, mechanical/thermal loads, controls and outputs. Unsupported portable JSON fields remain missing implementation, not product exclusions. |
| Application workflows | Full geometry/mesh/model/results operations, original PMX interoperability in both directions, undo/history/replay, imports/exports, selection, deformation/animation, plots/histories, automation and original numerical tools. |
| Solver exception | The unavailable Intel/PARDISO solver is the sole exception. Preserve all other original backends and calculation capabilities; implementation gaps remain outstanding work. |

This is a required-breadth index, not a claim that a source-file inventory proves
stable 3.0.0 behavior or exhaustive workflow acceptance. Add reference/native
fixtures as the shared original owners are connected; do not lower the target.

## Release identity

| Item | Current state |
|---|---|
| Product functionality target | PrePoMax 3.0.0 |
| Official Windows download | [Upstream downloads](https://prepomax.fs.um.si/downloads/) lists 3.0.0 dated 2 November 2026. [Downloaded archive and executable hashes](reports/pmx-3.0.0-reference/official-archive.json) |
| Verified stable 3.0.0 commit and binary correspondence | Pending; do not label an RC or assembly version as verified stable |
| Retained RC2 source marker | 912fb3d08014f246d48bef14d62a2cba0fdf5bb0 |
| Retained post-RC2 mirror/source pin | f6273e39983e06042ae8b06e9a3dd0f729ea4b91 |
| Read-only upstream HEAD check, 3 November | master at 2a25db82896aa0aa51666eb550df19d3950a8630; no tags advertised; GitLab release API returned an empty list |
| Upstream-history handling | Existing [divergence review](reports/upstream-2026-11-02.md) still applies; no reset/merge/mirror rewrite in task 0043 |

An empty release API and lack of tags do not establish that stable 3.0.0 does not
exist. Exact release/source correspondence remains a pending acceptance item.
The existing replay pins and engineering reference remain explicit meanwhile.

## Current workflow coverage

These are coverage boundaries, not a percentage estimate or an exhaustive list
of upstream commands. Add per-feature fixtures as each original workflow moves
into the shared application; preserve intentional upstream behavior and units.

| Area | Verified bounded coverage | Remaining parity work |
|---|---|---|
| Mesh input/decks | Original INP reader, IDs, bounded mesh export and all original mechanical 3D solid formulation choices for static decks, with the recorded nonlinear/distributed-load increment, including mixed meshes and explicit pyramid conversions; solver nodes use original CalNode formatting, exchange retains G17 | Full import/export/model graph and supported element/analysis combinations |
| Materials/analysis editing | Model tree/Qt editor for original static-solid units/materials/sections/supports/nodal loads/step controls, plus density/plastic hardening, pressure/gravity, geometric nonlinearity and increment/plastic-strain results; original C# validation and real edited solve, plus session set creation from IDs or a picked ID and CAD face/part region multi-selection | Arbitrary mesh multi-pick, set replacement/deletion, broader assignments/materials/loads/steps and full original model operations |
| Native solve | Mac ARM64/Linux x64 analytical static cube; Mac/Linux ARM64 mixed original mechanical 3D solid static workflows; desktop start/cancel/status | Analysis/backend breadth, capacity/performance and native other-target acceptance |
| Visualization | INP/C3D8/C3D4 FRD, contours, original IDs/values; opt-in direct Mac child-view proof | Full vtkControl pipeline, clipping/highlighting, deformation, input/DPI/performance and other native desktops |
| Results/history | Original bounded 3D solid static FRD fields/invariants and original collapsed-pyramid restoration and static-shaped DAT histories | Full original results orchestration, shell/dynamic outputs and interactive histories |
| Persistence | Mac/Linux ARM64 checked C3D8 and one-part CAD/C3D4 PMX open/edit/save/reopen/solve, with original-app readback and immutable PMX jobs. Tasks 0071–0073 add Poisson's ratio/density, signed vector forces and compatible existing named-region reassignment, with exact original-export/native decoded fields | New native-session serialization and the full project/results/history corpus under D057 |
| CAD/meshing | Original custom Netgen/OCCT import, linear meshing, CAD regions and static results on Mac/Linux ARM64. Tasks 0074–0077 add selected-part translation, plane split, controlled ShapeFix repair and STEP export/reopen, with three-body edited remesh/analytical solve and frozen recipes. Tasks 0078–0080 add bounded owned CAD undo/redo, axis-angle rotation and all-body STEP export with native solid correspondence. Tasks 0081–0083 add mirror, positive uniform/non-uniform scale and translated/rotated copies with six-solid analytical workflow and frozen outputs. Tasks 0084–0086 add native C3D10 mesh transport; tasks 0087/0088 connect original configuration, native static calculations, ten-node results and export/reopen with full midside topology | Native x64 deferred to Windows/Podman (D059), strict visualization and edited-deck/field byte differences, new native-session PMX persistence, broad CAD/defective repair, remaining meshers and Windows behavior |
| Automation | Existing upstream API/gateway/journal investigated | Portable scripting, command history/replay and MCP workflow parity |
| Engineering correctness | Strict accepted-scope checks retained; tasks 0087/0088 verify native C3D10 force-driven/curved static calculations independently of PrePoMax measurement | Both known element failures and quadratic-tetrahedron measurement gate remain; general curved quality and full calculation parity are open |
| Distribution | Internal ad-hoc Mac DMG, native Linux archive and Ubuntu 24.04 installer proof; shared four-RID hosts | Native Windows installer, Linux distro coverage and physical desktop acceptance, signing/clean OS/Homebrew and complete corresponding sources/notices |

## Future release cadence

For every upstream release, record its exact source/artifact identity, compare
features and engineering/persistence/native deltas, adapt shared owners and
platform boundaries, then run the affected Windows-reference/native corpus.
Publish version-aligned project packages only after their declared scope passes.
Upstream contribution acceptance does not determine whether this maintenance
continues. Preserve upstream history, attribution, sources and licenses.
No automated release monitor, upstream message or public package channel has
been created by recording this policy.

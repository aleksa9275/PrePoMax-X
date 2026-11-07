# PrePoMax release parity tracking

7 November 2026, tasks 0107–0110: [remaining element-family workflows](reports/element-family-completion.md)
connect discrete sections, broader family calculations, imported-mesh editing/
boundary creation and checked original PMX family read/solve/exact-copy Save As.
Full milestone-8/new-session PMX serialization, general mesher/tool/calculation
breadth and four-target acceptance remain open. B009 joins the retained original
findings; all earlier obligations below remain unchanged.


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

Tasks 0092–0094 connect ordinary solid frequency/buckling and deformation,
frame/shape animation and original DAT history plot/table/CSV inspection.
[Actual bounded coverage and remaining work](reports/eigenmodes-results-tools.md).
B007's original search behavior is recorded and deferred under D061; full
analysis/results functionality and every acceptance gate remain required.

## Current workflow coverage

These are coverage boundaries, not a percentage estimate or an exhaustive list
of upstream commands. Add per-feature fixtures as each original workflow moves
into the shared application; preserve intentional upstream behavior and units.

| Area | Verified bounded coverage | Remaining parity work |
|---|---|---|
| Mesh input/decks | Original bounded INP parsing/export, original mechanical solid formulations/conversions, imported CPS/CPE/CAX, shell/membrane, beam/truss and discrete MASS/SPRING/GAP workflows with preserved IDs/connectivity | Full original import/export/model graph, every alias/combination and original mesh-operation semantics |
| Materials/analysis editing | Original C# validation through model tree/Qt controls for reported static/nonlinear, mechanical/thermal/dynamic controls, sections/layers, supports/forces/moments/pressure/gravity, amplitudes, regions and outputs | Full original materials/orientations, constraints/contact/interactions, fields/loads/controls, assignments and supported calculation combinations |
| Native solve | Real Mac/Linux ARM64 solid/plane/axisymmetric/shell/line/discrete representative workflows, frozen jobs, cancellation/status; historical native x64 subset evidence | Complete calculation/backend/capacity/performance coverage and current native Windows/Linux x64 application acceptance; B009 remains explicit |
| Visualization | Both copied Mac viewport transports, original IDs/scalars, CAD regions, reported deformation/outline/frame/mode animation and actual Cocoa screen/picking/resize | Complete original rendering/selection/clipping/highlighting/editing tools and full native desktop/DPI/performance acceptance |
| Results/history | Original bounded FRD mesh/fields/invariants including shell/layer/line transport, thermal/velocity/energy fields and original DAT time histories with plots/tables/CSV in the reported workflows | Full original results graph/tools/output families, mode-history tables and persistence/orchestration, all supported original result combinations |
| Persistence | Restricted editable original C3D8 and CAD/C3D4 PMX contracts; broader static-family PMX read/solve/exact-byte Save As, native reopen and original-app readback | New native-session original-compatible serialization, broader graph editing, result/history/command persistence and the full accepted-version corpus under D057 |
| CAD/meshing | Original custom Netgen/OCCT import; reported selected CAD transforms/copies/split/repair/history/STEP exchange; native C3D4/C3D10 tetrahedral meshing and regions; imported-mesh transforms/renumbering/exterior boundary extraction and undo/redo | Remaining original meshers/backends/setup/controls and surface/line/structured/extruded/revolved/refinement tools, general CAD/repair, full native persistence, exact mesher reproducibility and Windows/x64 behavior |
| Automation | Original API/gateway/journal inspected; internal native workflow probes exercise delivered boundaries | Portable original scripting/API/MCP, command history/replay and full automation/application parity |
| Engineering correctness | Original algorithms/tolerances and strict recorded checks; independent/reference comparisons within declared workflows; zero-exit explicit solver-error handling repaired | D029/B006/B007/B008/B009 and thermal/axisymmetric findings, original T2D3 refusal, general quality/numerical/combination acceptance; improvements follow functional parity under D061 |
| Distribution | Shared four-RID hosts, current internal ad-hoc Mac ARM64 app, earlier Linux archive/Ubuntu installer proofs | Full native four-target/physical desktop/clean-machine install-upgrade-uninstall acceptance, Windows/Linux package breadth, Homebrew, Mac signing/notarization, corresponding sources/notices and stable release/source identity |

Tasks 0103/0104 add the connected plane stress/strain and axisymmetric static
workflows for all original triangle/quad formulations. [Scope, diagnostics and
actual checks](reports/plane-axisymmetric-workflow.md). Subsequent increments
connect shells/beams and discrete elements; broader family/calculation
combinations, mesh authoring and full PMX remain required.

Tasks 0105/0106 add imported shell/membrane/beam/truss static workflows,
rotations/moments and original layered/expanded results. [Actual scope and B008
diagnostics](reports/structural-elements-workflow.md). Full element-family,
material/orientation/calculation/mesher/PMX and platform acceptance remains open.

For the consolidated remaining requirements and a candid completion assessment,
read [full-completion-status.md](reports/full-completion-status.md). No percentage
is inferred from the number of tasks or workflow checks.

## Future release cadence

For every upstream release, record its exact source/artifact identity, compare
features and engineering/persistence/native deltas, adapt shared owners and
platform boundaries, then run the affected Windows-reference/native corpus.
Publish version-aligned project packages only after their declared scope passes.
Upstream contribution acceptance does not determine whether this maintenance
continues. Preserve upstream history, attribution, sources and licenses.
No automated release monitor, upstream message or public package channel has
been created by recording this policy.

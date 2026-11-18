# PrePoMax-X portable static analysis increment

> **D062 (8 November 2026):** this area now builds against the whole original
> assemblies in [`X/Domain`](../Domain). Paragraphs below about extracted slices,
> layout guards, source pins and upstream replays describe retired tooling and
> are kept as history. Run `python3 X/Checks/check.py --area <area>`.

Tasks 0092/0093 add `step.kind` = `frequency` or `buckling` (default `static`),
`modes`, optional `lowerFrequency`/`upperFrequency` in Hz, and `bucklingAccuracy`.
Original FrequencyStep/BuckleStep and keyword writers are shared unchanged
through mechanically verified partial extraction. Ordinary homogeneous supports,
linear elasticity and density for frequency/nonzero reference load for buckling
are required. The axial-frequency and column-buckling INP/JSON pairs are runnable
examples. [Actual scope, comparisons and inherited search behavior](../../.project/reports/eigenmodes-results-tools.md).
All other original functionality remains required; D061 keeps numerical fixes
deferred. Existing static input/commands remain compatible.

Task 0090 extends this workflow with optional material `density`,
`plasticCurve` stress/plastic-strain pairs and original `hardening` choices;
step `nonlinearGeometry`, `pressures` and `gravityLoads`. Pressure chooses either
`nodeSet` for complete exterior faces or `elementSet` plus `face` 1–6. Gravity
uses `elementSet` and three `acceleration` quantities, requiring density. See the
four runnable pressure-solids/gravity-column/plastic-tension/finite-tension pairs
and [integration evidence](../../.project/reports/nonlinear-loaded-solids.md).
Original types/converters/keywords and pyramid face correspondence are shared.
B006 retains the original quadratic-pyramid wedge-pressure accuracy discrepancy;
the pressure example explicitly selects hexahedron conversion. All other original
functionality, PMX and release requirements remain open.

Task 0089 connects all original mechanical solid formulation choices for the
existing linear-static definition, including mixed meshes and explicit original
C3D5/C3D13 conversion. Optional `pyramidConversion` in the analysis definition is
`wedges` or `hexahedrons`; omission refuses a pyramid solve. The original
CalElement conversion and original solver formulations are used unchanged.
`mixed-solids.inp/.json` and `mixed-pyramids.inp/.json` are runnable examples.
[Milestone evidence](../../.project/reports/solid-formulation-workflow.md).

Tasks 0087/0088 support C3D10 **native linear-static calculation**, alongside
C3D8/C3D4, with original deck keywords and original ten-node FRD decoding.
CalculiX owns its quadratic formulation and integration-point Jacobian checks;
no original solver or PrePoMax numerical algorithm is changed. The static writer
checks positive tetrahedron corner orientation without calling the failing
quadratic measurement path. The separate PrePoMax measurement gate and pyramid
classifier failure remain visible; neither is an accepted final functionality
exclusion. All mesh/calculation families are required under D060.
[Current evidence](../../.project/reports/quadratic-native-static.md).

Solver node records use the shared original CalNode E8 formatter, avoiding
CalculiX numeric-field overflow (B005). Mesh-only exchange remains G17.
`StaticDeck/c3d10-force.inp` and `c3d10-force.json` are a force-driven analytical
unit tetrahedron with four free displacement unknowns. Use them with the same
`build-static`/`run-static` commands as the cube. Curved CAD fixture generation,
real solves and original-result checks are in
`X/Desktop/verify_quadratic_analysis.py`; this is test preparation, not a second
product engineering implementation. Original/source/PMX/release gates remain.

This source-linked superset builds original CaeGlobals/CaeMesh/CaeResults/
CaeModel types in their original assemblies. There is one engineering source
implementation. Keep its output directories separate from X/Core and never copy
partial DLLs over an original installed application.

The callable `CaeModel.StaticAnalysisDeckWriter.Write` now writes a complete,
bounded 3D linear-static deck from original mesh/material/solid-section/
displacement/concentrated-force/static-step/output objects. The first supported
formulation is full-integration C3D8, temperature-independent isotropic elasticity,
global translations and force **per node**, with named element/node sets. Every
element must belong to exactly one section. Unsupported definitions, overlapping
regions/DOFs, omitted model keywords, invalid numeric values and unsupported
flags are rejected before writing. This increment generates solver input; it
does not run the solver or provide a desktop application.

With a native .NET 10 SDK, from the repository root:

    dotnet build X/Analysis/PrePoMaxX.Analysis.slnx -c Release
    dotnet X/Analysis/StaticDeck/bin/Release/net10.0/PrePoMaxX.StaticDeck.dll build-static X/Analysis/StaticDeck/cube-mesh.inp X/Analysis/StaticDeck/cube-analysis.json new-cube.inp

The example reuses the retained analytical cube: eight nodes, one C3D8 element,
E = 210000 MPa, nu = 0.3, twelve constrained node/DOFs, and 25 N on each of four
loaded nodes (100 N total). It includes original static incrementation and
field/history output. Original default element fields add E and NOE to the
reference's S output. IDs, connectivity and named references are preserved.

Tool JSON must specify `mm-N-s-C` or `m-N-s-C`; the mesh coordinates are assumed
to use the declared length unit. Quantity strings use the original unit/equation
converters. A null displacement component means free. Force components are per
node, never automatically divided by the node count. This JSON is CLI
configuration, not an application persistence-format decision. Unknown,
duplicate and missing properties are rejected. Output must be a new file;
input files and existing outputs are preserved.

The smaller material-only command remains available:

    dotnet X/Analysis/MaterialDeck/bin/Release/net10.0/PrePoMaxX.MaterialDeck.dll write-isotropic Steel "210 GPa" 0.3 new-material.inp --pressure-unit MPa

Typed export snapshots evaluated quantities in the caller's culture before
calling the original invariant-culture keyword writers. Source equations are
preserved. Original data classes retain their names, serialized fields and
assembly ownership. Mechanically verified partial files keep preview/model/
copy capabilities in the original net48 build. Portable data assemblies do not
include those capabilities or unsafe cloning. Original Color fields use managed
System.Drawing.Primitives; System.Drawing.Common/GDI, WinForms and VTK remain
outside this slice. This does not establish full net48 or Windows acceptance.

Verification retains source/package/tool fingerprints and native-host command
logs. Each source mode runs 44 material + 69 static-deck + 218 existing checks
(331 accepted), eight material CLI controls, 21 static CLI controls and four
independent reference-semantics rejection controls. Both earlier correctness
failures are recorded separately and remain failures. Nine analysis guards
verify extraction, closure, dependencies and legacy project inclusion.

    python3 X/Analysis/verify-analysis.py --expect-os Darwin --expect-architecture Arm64 --output X/Analysis/artifacts/current-macos-arm64.json
    python3 X/Analysis/run-podman.py --output-dir X/Analysis/artifacts/linux-arm64

The cached Podman image and package archives are prerequisites for the last
command; it requires a native ARM64 Linux server/image, disables network access,
and mounts this repository read-only. Native Linux x64 CI is prepared as
`analysis-workflow-linux-x64`; local ARM64 results are not a hosted x64 pass.

The verifier restores to temporary storage and can use an existing NuGet cache
at X/Analysis/artifacts/packages (or --package-cache) as an offline local feed.
First restore uses official NuGet only. Exact upstream package versions NCalc
1.3.8 and UnitsNet 4.89.1 are locked by packages.lock.json, and actual package/
asset bytes are pinned in dependency-artifacts.json. Raw archive SHA512 and
NuGet signed-package contentHash are distinct and recorded separately.

NCalc retains NU1701: this old framework package has no declared modern target.
Bounded runtime tests passing do not establish full modern-framework support.
UnitsNet uses its same-version netstandard2.0 asset in the modern build; original
net48 keeps its existing net40 reference. No package/version change is made in
production net48 projects. Full package-source/license/signing redistribution
review remains required before end-user bundling. Cached packages/binaries are
ignored, not committed. Original source attribution and root GPLv3 remain.

The post-RC2 replay uses exact reviewed upstream Material/ElasticLamina changes
and the new original CompositeStrength type in an isolated source overlay.
Tests deliberately distinguish the tightened lamina stability check and the
new strength-equation capability. Since M0 (3.0.1, D063) the
baseline contains these changes and `verify-analysis.py` runs the post-RC2 mode. Both earlier
element correctness failures and the quadratic-tetrahedron measurement gate
remain. Native solve/results, persistence/UI/CAD and actual native installers remain
subsequent accepted work. See .project/RELEASE.md.

Tasks 0095–0097 add original HeatTransferStep, temperature/initial-temperature
objects and keyword writers, CFlux/BodyFlux/DFlux/FilmHeatTransfer, conductivity,
specific heat and thermal outputs. `ThermalAnalysisDeckWriter` validates the
portable integration; original thermal physics/formatting remains in its original
classes. `thermal_layout.py` guards mechanical extraction of legacy preview/model
methods, including the unchanged net48 entry points and serialized ownership.
See the [thermal workflow report](../../.project/reports/thermal-analysis-workflow.md).

Tasks 0098–0100 share original ModelProperties/physical constants, radiation,
thermal tables, tabular amplitudes and prescribed-temperature expansion.
Original preview/file/model methods remain in guarded net48 legacy files.
See the [milestone report](../../.project/reports/radiation-amplitudes-thermal-stress.md).


Tasks 0107–0110 add section kinds `mass`, `spring`, `gap` with blank material and
original mass/stiffness/DOF/clearance/normal controls. Exact MASS, SPRING1/2/A and
GAPUNI mesh records are preserved. Thirteen new examples connect discrete,
shared-node solid/spring, beam/shell/plane/axisymmetric frequency and implicit
transient workflows. The modal-beam example is a retained failure diagnostic.
Optional original `step.fieldOutputs` / `historyOutputs` descriptors preserve
explicit output names/flags; shorthand history sets remain compatible.
[Actual scope, original findings and open acceptance](../../.project/reports/element-family-completion.md).

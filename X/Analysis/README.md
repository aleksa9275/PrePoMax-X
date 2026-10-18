# PrePoMax-X portable static analysis increment

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

    python3 -m unittest discover -s X/Analysis -p test_analysis_layout.py
    python3 X/Analysis/verify-analysis.py --expect-os Darwin --expect-architecture Arm64 --output X/Analysis/artifacts/current-macos-arm64.json
    python3 X/Analysis/verify-analysis.py --upstream-revision 3.0.0-rc2 --output X/Analysis/artifacts/rc2.json
    python3 X/Analysis/verify-analysis.py --upstream-revision post-rc2-2026-10-17 --output X/Analysis/artifacts/post-rc2.json
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
new strength-equation capability. These bytes are not silently applied to the
baseline branch; original algorithms are exercised as pinned. Both earlier
element correctness failures and the quadratic-tetrahedron measurement gate
remain. Native solve/results, persistence/UI/CAD and actual native installers remain
subsequent accepted work. See .project/RELEASE.md.

# Task 0012 — Remaining local preparation

2026-10-15, Europe/Belgrade. Maintainer explicitly authorized remaining feasible
local tests/preparation and commit/push of the research branch. No original
application projects/sources/algorithms, frontend/default-format choices or
x/main integration changed. Windows task 0011 remains prepared, not executed.

## PMX scalar records — useful agreement and actual settings drift

Verified execution: [private scalar comparison](local-completion/pmx-shallow-values.json)
compares 159 shallow records across 29 selected exact serialized types. Twenty-
seven types match, including equation containers, units, materials, shell sections,
static steps, BC/load records and output/control records. This compares scalar
bindings within each record; references contribute only their type/array shape.
No raw private values or keyed fingerprints are retained. Three synthetic
[binding controls](local-completion/pmx-values-tests.json) pass, including scalar
mutation and swapped-member rejection. No payload assemblies/BinaryFormatter.

**Verified changes:** AnalysisJob `_environmentVariables`, `_executable`,
`_numCPUs` and `_workDirectory` differ. The old environment list has one entry;
the saved list is null. Its key is outside the small thread-setting allowlist
and remains redacted. FeModel gains `_calculixKeywordOverrides`. These are not
normalized away or called fully equivalent.

Source observation: pinned Controller.ApplySettings (Controller.cs around
19000–19048) replaces non-overridden job executable/work directory/CPU/environment
settings from the current session. Architectural inference: this is a plausible
explanation of the observed job drift, not a verified exact-source mapping for
the released 2.6.0 binary or approval to discard custom job settings. Windows
capture must record override flags and intended execution-environment policy.

Limit: identical shallow record multisets do not prove array contents, region/
material associations, order, aliasing, full mesh/results reconstruction or
history replay. Earlier guarded custom-block comparisons are complementary,
not a substitute. Preserve this distinction in future schema work.

## Structured mapping — compiler-sensitive Linux ARM64 result

Verified execution: fresh [Mac checks](local-completion/meshing-macos-arm64.json)
pass all 13 original C++ vectors, 17 independent native and seven managed checks,
1,728 exact count comparisons and existing negative/CLI controls. Sources remain
unchanged at `de8f73032a72746e3d6d9afd53d9fbd289eb310a`.

The cached Linux SDK image lacked a C++ compiler. An explicit research-only layer
installed g++/dependencies (no existing packages upgraded), preserving the base
SDK image. [Actual image inspection](local-completion/linux-arm64/image.json)
records ID `27c38b4417f399491c60ba15f35bf450ffcea6d57c78ccbc5ce3c9fb05cfcc88`.
Tests mount the checkout read-only with network disabled and disposable `/tmp`.
Compiler is GCC 13.3/aarch64-linux-gnu; .NET SDK/runtime remain 10.0.402/10.0.13.

The first default -O2 run **fails** right_45_45 at deviation about 0.0617397;
12/13 vectors pass. [Original failure](local-completion/linux-arm64/initial-failure-meshing.json)
and [suite failure](local-completion/linux-arm64/initial-failure-research.json)
are retained. [Explicit controls](local-completion/linux-arm64/fp-contraction.json):

| Unchanged checker flags | Outcome |
|---|---|
| -O0 | 13/13 pass |
| -O2 | 12/13 pass |
| -O2 -ffp-contract=off | 13/13 pass |
| -O2 -ffp-contract=fast | 12/13 pass |

Verified observation: contraction mode changes this result. Exact optimizer/
instruction/iterative-solver cause is an investigation question; no production
algorithm, tolerance or compiler policy was changed. The probe's optional
`--fp-contract-off` explicitly records the diagnostic choice and leaves default
behavior unchanged. This compiler-sensitivity issue remains a parity risk.

With that explicit control, the [Linux ARM64 suite](local-completion/linux-arm64/research.json)
passes 24 PMX tests, three binding controls, four shell contracts/two negative
controls, all structured checks and the unchanged data probe's 30 checks/two CLI
contracts. Structured portable observations match Mac (native area tolerance
1e-12, source/count signatures/check outcomes exact). The earlier full C# mapping
boundary remains CS0103/MessageBoxes; no full mapping extraction was attempted.
The additive native Linux x64 CI job uses compiler defaults; hosted outcome is
recorded separately after publishing. A local rehearsal is not a hosted pass.

## VTK provenance and lifecycle

Verified execution: [nine native Mac checks](local-completion/vtk-provenance/provenance.json)
pass on the same pinned VTK 9.5.2 wheel. The temporary runtime had disappeared;
it was restored and its wheel SHA-256 exactly matches task 0006. A synthetic
linear quad, quadratic quad and tetra retain ordinary cell-data parent element
IDs through surface subdivision and clipping. Generated clip vertices are
kept distinct from original FEM nodes; an unknown parent ID is rejected.
All corner/midside nodes deform correctly. Twenty create/render/pick/remove/
finalize cycles select the expected quadratic element. The
[mixed-element image](local-completion/vtk-provenance/mixed-elements.png) was
visually inspected.

This demonstrates a candidate provenance contract, not a production fix. Simple
coordinate lookup is justified only for this fixture's unique undeformed nodes;
production needs explicit topology/parametric provenance. Programmatic input
cannot close actual pointer, Retina/DPI, embedded-host or memory-leak/platform
acceptance. Native computer control is unavailable in this session; no GUI
framework was selected to manufacture an apparent interaction pass.

## Analytical solver reference

Verified execution: exact official-bundle **CalculiX 2.22** runs through the
existing CrossOver bottle on [the synthetic uniaxial cube](../../X/Feasibility/Solver/uniaxial-cube.inp).
[Seven checks](local-completion/solver-crossover/reference.json) pass: exact node
coverage, analytical displacement components, eight integration-point stresses,
100 MPa axial stress with zero transverse/shear, -100 N supported reaction and
global nodal-force balance. A mutated displacement is rejected. OMP/MKL were
single-threaded. Solver/MKL dependency/input/output hashes and actual console
diagnostics are retained, along with synthetic DAT/FRD/STA/CVG files.

This is a Windows solver reference through a compatibility layer, not native
Mac/Linux execution, original PrePoMax result-reader validation, source recovery
or general nonlinear/contact/meshing equivalence. No alternative solver/version
was substituted. Repeat this exact fixture/binary on native Windows first.

## What still needs external resources or Windows

- Native Windows PMX/deck semantic snapshots, history/undo/redo and with/without-
  results corpus; resolve observed job-settings drift and source/build identity.
- Matching patched Gmsh, NetGenMesher/nglib, QuadWild and QuadMesher sources.
  Source/access failures and the unsent recovery packet remain unchanged.
- Native solver/source/dependency builds and actual CAD shell-junction meshing;
  F001 remains Proposed. No original mesher or history regeneration ran here.
- Real pointer/DPI/host rendering on required platforms, with provenance rules
  and source/license closure, before frontend/interop selection.
- Review contraction sensitivity across Windows/Linux x64/ARM64 and native
  compiler variants before accepting a numerical build recipe.

Native source/header checks were rerun with the same expected C/C++/C++-CLI
outcomes and existing QuadWild checksum discrepancy. Fresh Mac data checks also
match the earlier reference. Private models/raw graphs and bundled executables
remain outside Git. Publication includes research sources, synthetic fixtures,
metadata and documentation only; see STATUS for commit/hosted follow-up.
Local attributes preserve exact solver-output/downloaded-source bytes, including
their original whitespace, so recorded hashes survive Windows checkout.

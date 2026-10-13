# Functional equivalence and platform acceptance

The original Windows application, pinned to the same upstream commit and exact native/solver versions, is the oracle. A successful build or Git merge proves neither engineering equivalence nor file compatibility.

## Existing assets and actual execution

`APIs/Python/Test_Scripts/Run_Tests.py` discovers command headers, expected exit codes, TEST PASSED markers and run JSON expectations. It handles multiple filters and adds `Test_Analysis.py` when a results test needs its output. `Models/` contains CAD/BREP/STL/INP fixtures. Broad suites cover materials/sections/loads/BCs/steps/constraints/outputs/geometry/mesh validity, jobs, results, selection and RPC/MCP. There is no standalone C# test project or repository CI pipeline at the audited baseline.

Actual Phase 0 results on macOS ARM64:

| Check | Result / limit |
|---|---|
| `python3 -m unittest -v test_runner_offline` from test-script directory | 37 passed; header parsing, launch command construction, report/output checks and fixture dependency management; **not live PrePoMax** |
| `python3 APIs/Python/Test_Scripts/Audit_API_Coverage.py` | exit 0; no missing replacements/unmapped commands/missing ToPython/emitted-name drift; documented exclusions remain |
| `python3 APIs/Python/Test_Scripts/Audit_API_Documentation.py` | exit 0; 462 argument strings, 484 signature rows, 126 example calls, 47 agent paths checked; zero drift, one documented exception |
| `dotnet build PrePoMax.sln --no-restore -p:Configuration=Release -p:Platform=x64 -v:minimal` | failed: MSB4278 missing Visual C++ targets; MSB3644 missing net48 reference assemblies, 11 errors. Initial sandbox invocations stalled and were terminated; outside-sandbox diagnostic completed in 0.42 s |
| Phase 0 maintenance tooling | Nine disposable-Git safety tests passed; real dirty-tree refusal plus committed-tree dry-run and normal no-op sync succeeded; master difference 0/0 and cp/main unchanged |
| Live FEM, meshing, solver, persistence, UI, rendering and selection | **Not run.** No native PrePoMax host exists here yet; Windows VTK/toolchain/runtime and pinned solver are absent |

## Regression tiers

| Tier | Fixtures / assertions | Prerequisites |
|---|---|---|
| 0: static/build | Complete project graph, prohibited API/native dependencies, API/document coverage, reproducible build closure | Available now for scans/offline Python; Windows environment for baseline build |
| 1: managed engineering | Nodes/connectivity/sets/surface orientation; equations and units; element geometry, material tables, deck semantics; FRD/DAT parsing and derived invariants | Source-linked portable slice + Windows snapshot exports |
| 2: project/history compatibility | PMX corpus from representative old versions and final 3.0; results included/excluded, history regenerate, rename binder, commands, material/settings imports, large models | Corpus absent in current checkout; capture via Windows reference, commit provenance and rights to fixtures |
| 3: geometry/meshing | STEP/IGES/BREP/STL import, topology mapping, split/fuse/repair/offset; Netgen/Gmsh/MMG/QuadWild/QMorph mesh families, constrained nodes, Jacobians and invalid-model refusals | Exact modified native sources and matched per-target binaries |
| 4: solver/numerical | Same INP parsed keywords/set membership; static/dynamic/nonlinear/modal/buckling/thermal/contact/axisymmetric/complex and wear examples; output/monitor/cancel/error/timeout | Pinned CalculiX and numerical dependencies on each target; start single-threaded |
| 5: rendering/selection | Known node/element/face IDs; point/rectangle picks, clipping, occlusion, deformed/second-order meshes, scalar contours/legend/camera; export and DPI | Interactive native VTK host + real display/GPU and Windows oracle |
| 6: end-to-end automation/UI | Existing Python suites, journals, run.json/exit codes, MCP tools/busy/read-only/refusal/token/origin/session rules; user import→mesh→load→solve→results workflows | Same feature/capability set and isolated settings/workspaces; no user model changes |
| 7: packaging | Fresh-machine launch, native architecture/dependency closure, notices+matching source, Unicode/space paths, limited permissions, signed/notarized Mac package when distributing | Build/CI runners per required target and release approval |

GUI automation augments API tests: scripted selection on rendered state and real pointer tests must both pass. MCP tests can inspect tool capabilities and call existing APIs but do not prove dialog layout, focus, keyboard navigation or actual picking. Captured Windows screenshots are supplementary artifacts, not numerical or selection correctness evidence.

## Differential comparisons and tolerances

Keep the same upstream commit, solver source/version, native patch set, model units, thread count and input deck. Store provenance/hashes plus machine-readable snapshots. Use exact equality for entity counts/IDs/connectivity/set membership/step names/keyword values where deterministic. Normalize line endings/path separators and irrelevant output ordering only; never normalize away loads, orientations, units or constraints.

For numerical field/history values use `abs(a-b) <= atol + rtol * max(abs(a), abs(b))` with per-field units/scales. Proposed starting tolerances: parser comparisons rtol 1e-12 for doubles or 1e-6 for float storage; deterministic linear solver regression rtol 1e-6 and a fixture-specific nonzero absolute tolerance. These are **reviewable starting values**, not universal FEM accuracy guarantees. Establish baseline repeatability before approving them. For modes account for sign and near-degenerate eigenspaces (frequency comparison plus MAC/subspace measures); do not compare raw eigenvectors blindly. Nonlinear/contact/parallel cases need convergence and equilibrium/energy acceptance, with thresholds justified per fixture and reviewed for any relaxation.

Mesh topology may legitimately differ across compilers/nondeterministic algorithms; fixed-boundary constraints, element validity, region mappings and problem-level solution must remain within declared contracts. Do not call different node counts a numerical difference until the meshing-input and native-version causes are identified.

Classify every failure: numerical drift, application/command error, unsupported platform capability, infrastructure/missing dependency, selection mapping error or rendering appearance difference. Unsupported/skipped required capability fails release parity; a skip is never a pass. Rendering comparisons use backend-specific masks/thresholds for antialiasing and text, while exact machine-readable picks/IDs/scalar values remain decisive. Record unknowns instead of increasing tolerances to hide them.

## Required target matrix

| Target | Required acceptance | Infrastructure |
|---|---|---|
| Windows x64 | Legacy reference builds/runs; new services preserve old UI and suite results; new frontend, if offered, meets same parity | Windows VS/MSBuild C++ tools, net48 pack, ActiViz 5.8, released base folders and exact solver; not available on this Mac |
| macOS ARM64 | Native ARM64 process and native tools (no Wine/Rosetta), PMX round-trip, all required numerical/mesh workflows, interactive selection and Retina lifecycle | Current Mac can run offline checks and later feasibility experiments; native dependency/source gaps unresolved |
| macOS x64 | Same contracts under native x64 with matching tools; no assumption that ARM success establishes Intel support | Intel Mac or suitable native runner required; current ARM Mac is not proof |
| Linux x64 | Same core/native workflows; documented X11/Wayland support and interactive picking; headless tests truly avoid WinForms | Linux runner/container for compute and physical/virtual display+GPU for rendering |
| Linux ARM64 | Same gates when supported; otherwise explicit lower-priority status with no unsupported parity claim | ARM Linux runner; every native dependency must be rebuilt/validated |

Public release requires zero unexplained failures in mandatory corpus, complete bidirectional same-baseline file tests, passing required feature workflows and no required silent skips. Windows-only optional solver integrations (Abaqus/FEMaster) need an explicit support policy, not accidental loss. Capture a feature matrix before presenting a release as preserving all functionality.

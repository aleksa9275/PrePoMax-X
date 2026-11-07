# Functional equivalence and platform acceptance

**Current cadence (D062, 2026-11-08):** focused checks for the changed area while
developing; at each phase milestone run the representative workflows and the
original-app comparisons; full four-platform/package sweeps only for release
candidates. Earlier dated sections below are historical context.

Maintainer reaffirmation, 6 November 2026: work in larger functional milestones
that deliver usable original feature families through the shared application.
Group related implementation into one substantial step; do not split each
transport, guard or UI control into a separate delivery task. During development,
reuse existing tests and run focused checks where they resolve a real risk or
failure. Run representative end-to-end and affected regressions at integration
boundaries; reserve full platform sweeps, repeated copied-app checks and package
rebuilds for meaningful candidate milestones. Add tests for substantive behavior
or defects, not every changed line. Report progress in completed user functions
and remaining functionality. Testing checks progress toward the working product;
it is not the project objective. Existing numerical expectations remain intact.

## Development cadence — 2026-11-02

Maintainer requests faster installable-product delivery and less repeated
testing. The [delivery plan](proposals/accelerated-native-delivery.md) sets the
current cadence: changed-area/current-source checks during development; affected
consumer/engineering checks for numerical, interop and persistence changes;
small cross-platform workflow checks at integration milestones; historical-pin
replays for affected upstream/dependency/extraction changes; full declared
candidate/platform acceptance before release. Older multi-host/three-pin task
reports record the evidence actually obtained, not a requirement to repeat that
matrix on every edit. Existing CI is unchanged until the profile implementation.

Reuse existing tests and cached matching builds. Keep failed-run fixtures/logs
with a compact source/tool/platform/command manifest and one owning-layer
regression per new defect. Documentation/styling changes do not require numerical
runs. Broaden checking only for affected behavior, a failure or a milestone.
Both known correctness failures/tetra gate remain; no tolerance relaxation,
hidden skip or claim that a pending platform passed. The release tiers below
remain the final acceptance requirements, not daily development blockers.

2026-10-18 task 0031 DAT adds canonical displacement/force/stress/strain history
checks using original parsing/entries, including independent cube expectations,
multiple increments/steps, exponent repair, identity/order/culture/path/concurrency
and malformed/unsupported input. Combined FRD/DAT target: 78 checks/nine CLI
rejections on all three pins, Mac/Linux ARM64 and exact-commit native x64 CI.
DAT has no completion trailer: parsing complete stored rows alone is not job/
coverage acceptance. Original analysis 331 accepted checks and both correctness
failures/tetra gate remain; full Windows/net48/RC2 and release gates remain.
[Evidence](reports/portable-dat-histories.md), [hosted publication](reports/results-publication.md).

2026-10-18 task 0030: 39 original FRD/field checks and five CLI controls pass
all three source pins on native Mac/Linux ARM64; prior 331 analysis checks rerun
with both known correctness failures retained. Six results source guards verify
extraction/ownership and reject decoder/math/helper edits. Original Windows cube,
independent binary float/double fixtures, explicit ID order, culture, malformed/
truncated controls and pure-shear invariants are covered. Full net48/Windows,
other analysis/result families and actual native solver acceptance remain open.
[Evidence](reports/portable-frd-fields.md).

2026-10-18 release delivery requirement: [RELEASE.md](RELEASE.md) defines the
required native installer/Homebrew matrix and install/upgrade/uninstall/
clean-machine acceptance. [Task 0022 evidence](reports/analysis-material-foundation.md)
adds equation/unit/material checks and reruns all existing checks against the
expanded assemblies on native Mac/Linux ARM64. Both correctness failures/gate
and the native Windows/full-application/four-platform release requirements remain.

The original Windows application, pinned to the same upstream commit and exact native/solver versions, is the oracle. A successful build or Git merge proves neither engineering equivalence nor file compatibility.

Maintainer-directed local workflow (2026-10-14): retain Podman for local Linux compute checks and prepare complementary GitLab CI on a native Linux x64 hosted runner (later authorization supersedes the earlier local-only instruction). Task 0002's runnable entry point is `python3 X/Feasibility/Core/run-podman.py`; its [README](../X/Feasibility/Core/README.md) describes setup, offline reuse and architecture selection. Keep actual image/runtime/source evidence. An ARM64 Linux VM on Apple Silicon establishes native Linux ARM64 behavior; translated amd64 is supplemental and does not replace native x64 acceptance. Container compute tests do not establish GUI/GPU behavior. The maintainer handles commits/pushes; local test execution must not depend on publication; hosted CI requires the maintainer to publish the reviewed feature-branch changes. See [CI preparation](reports/gitlab-verification.md); a local rehearsal or YAML parse cannot close the hosted/native x64 gate. Actual native x64 acceptance is now recorded in [the hosted execution report](reports/gitlab-linux-x64.md): both pins passed on an Intel amd64 runner, with independently checked artifacts. Broader parity tiers remain unproved.

## Existing assets and actual execution

`APIs/Python/Test_Scripts/Run_Tests.py` discovers command headers, expected exit codes, TEST PASSED markers and run JSON expectations. It handles multiple filters and adds `Test_Analysis.py` when a results test needs its output. `Models/` contains CAD/BREP/STL/INP fixtures. Broad suites cover materials/sections/loads/BCs/steps/constraints/outputs/geometry/mesh validity, jobs, results, selection and RPC/MCP. There is no standalone C# test project or repository CI pipeline at the audited baseline.

Actual Phase 0 results on macOS ARM64:

| Check | Result / limit |
|---|---|
| `python3 -m unittest -v test_runner_offline` from test-script directory | 37 passed; header parsing, launch command construction, report/output checks and fixture dependency management; **not live PrePoMax** |
| `python3 APIs/Python/Test_Scripts/Audit_API_Coverage.py` | exit 0; no missing replacements/unmapped commands/missing ToPython/emitted-name drift; documented exclusions remain |
| `python3 APIs/Python/Test_Scripts/Audit_API_Documentation.py` | exit 0; 462 argument strings, 484 signature rows, 126 example calls, 47 agent paths checked; zero drift, one documented exception |
| `dotnet build PrePoMax.sln --no-restore -p:Configuration=Release -p:Platform=x64 -v:minimal` | failed: MSB4278 missing Visual C++ targets; MSB3644 missing net48 reference assemblies, 11 errors. Initial sandbox invocations stalled and were terminated; outside-sandbox diagnostic completed in 0.42 s |
| Phase 0 maintenance tooling | Nine disposable-Git safety tests passed; real dirty-tree refusal plus committed-tree dry-run and normal no-op sync succeeded; master difference 0/0 and x/main unchanged |
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
| Linux x64 | Same core/native workflows; documented X11/Wayland support and interactive picking; headless tests truly avoid WinForms | Linux runner/container for compute and physical/virtual display+GPU for rendering |
| Linux ARM64 | Required: same core/native workflows, interactive picking and file/numerical parity as Linux x64 | ARM Linux runner; every native dependency must be rebuilt/validated; current Podman compute checks do not establish GUI/GPU behavior |

Maintainer correction, 2026-10-15: required targets are Windows x64, Linux x64,
Linux ARM64 and Apple M-series macOS ARM64. “x86” was explicitly clarified as
64-bit Intel/AMD; 32-bit x86 and Intel Macs are outside the target matrix.

Public release requires zero unexplained failures in mandatory corpus, complete bidirectional same-baseline file tests, passing required feature workflows and no required silent skips. Windows-only optional solver integrations (Abaqus/FEMaster) need an explicit support policy, not accidental loss. Capture a feature matrix before presenting a release as preserving all functionality.

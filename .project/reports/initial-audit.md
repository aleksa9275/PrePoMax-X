# Phase 0 initial repository audit

Audit date: **2026-10-13 (Europe/Belgrade)**. Source baseline: **de8f73032a72746e3d6d9afd53d9fbd289eb310a**. Recommendations are reviewable proposals; implementation has not begun.

## Repository inspection and safe changes

Initial checkout: clean `master` tracking origin/master, no uncommitted/untracked work. Origin: `git@gitlab.com:aleksa9275/pre-po-max-x.git`; origin/HEAD points to master. Local master and origin/master both at the baseline above; origin/v2.6.0 at `9e91252563739ee5304cea16c34863dfb17a74d5`. No tags existed. `git rev-parse --is-shallow-repository` returned false.

Official `git ls-remote --symref https://gitlab.com/MatejB/PrePoMax.git HEAD refs/heads/master 'refs/tags/*'` advertised master at exactly the same baseline and no tag refs. Added upstream, fetched all branches/tags and set upstream/HEAD to detected master. Upstream exposes master and v2.6.0 branches. `git merge-base master upstream/master` equals baseline; left/right count is `0 0`. This verifies genuine complete upstream history in the local fork, not merely a copied source tree. GitLab's server-side fork-parent metadata was not queried successfully; local history identity is the verified claim.

Created local `cp/main` at upstream/master and removed automatic upstream tracking from it to avoid a development push destination pointing at upstream. Created/switched to `feature/project-initialization` from cp/main. Neither mirror nor cp/main has Phase 0 documentation. No branches were deleted/rewritten; no merge into cp/main or remote push occurred. Feature commit identity can be obtained from `git log -1 feature/project-initialization`; it cannot be included as its own hash in its contents.

Relevant initial config: nonbare, filemode true, ignorecase true, precomposeunicode true; remote origin fetch `+refs/heads/*:refs/remotes/origin/*`, branch.master.remote origin, branch.master.merge refs/heads/master. No custom hooksPath returned. Retained origin and upstream push URLs unchanged; policy and scripts forbid upstream pushes. Ordinary Git remains capable of pushing, so future branch protections/scoped credentials need a separate approved policy. No credential values were recorded.

No existing AGENTS.md was found in the repository or inspected parent directories, and no tracked agent instructions existed. `.gitignore` explicitly ignores AGENTS.md/CLAUDE.md/agent notes and `Tests/`. Added tracked root instructions with an explicit force-add while preserving upstream ignore rules. Read the shipped application-agent skill as repository documentation context, not as authorization to contact/run another application. Existing README, Python overview, Licenses inventory, native notices, solution/projects, packages/configuration and build targets were inspected.

## Release and baseline facts

| Item | Verified state |
|---|---|
| Latest downloadable release | **v3.0.0 RC1**, 12 October 2026, [official downloads](https://prepomax.fs.um.si/downloads/) |
| Latest stable listed | **v2.6.0**, 1 September 2026; immutable release branch tip `9e91252563739ee5304cea16c34863dfb17a74d5`, commit message `v2.6.0 - final` |
| 3.0 release marker | `cb08b54a095c699da1976199b88e039b69a56631`, 12 October, `v3.0.0 RC1` |
| Default development tip | `de8f73032a72746e3d6d9afd53d9fbd289eb310a`; follows RC marker/merge with API-guide corrections |
| Exact stable 3.0 tag/commit | **Not available/established.** No tags advertised or fetched. AssemblyVersion/FileVersion 3.0.0 is not stability proof; Globals includes ReleaseCandidate |
| GitLab release objects | Release page yielded no usable listing; no assertion about all server-side release objects. Official downloadable artifact listing and Git refs are the verified sources |

Use current master as provisional analysis baseline because it exposes the 3.0 architecture/API; use stable 2.6 for historical reference. Do not freeze implementation to 2.6 while assuming 3.0 shares its interfaces. Switch to stable 3.0 only when upstream labels an artifact stable, a corresponding immutable commit (and tag if one exists) is identified, application/native/solver hashes are pinned, source obligations are resolved and Windows fixture/regression capture succeeds. If upstream does not create a tag, record the exact verified release commit; do not invent an official tag or equate a version string with release correspondence.

## Recent architectural changes relevant to migration

The [official 3.0 feature page](https://prepomax.fs.um.si/version-3-0-0/) describes Python execution/history conversion, API help and MCP, expanded CAD splitting/fusing/repair/offset operations, automatic/sweep meshing, QuadWild, OCCT 8.0.1, and new model/result/UI behavior. Its heading says Version 3.0.0 while downloads explicitly says RC1; stability assessment follows the download label.

Repository corroboration: `APIs/Python`, `PrePoMax/Python`, gateway interfaces and journal emitters; `PrePoMax/Rpc`, `PrePoMax/Mcp`; `PrePoMax/Meshing/Base/IMesherRunner` and four mesher runners; substantive sweep/transfinite code and custom native protocols. The architecture is richer than the README's simple “UI communicates exclusively with Controller” description alone suggests.

Selected observed commits:

- `8fd1ceab`: added Python API support; `090f1a03`: set version 3.0.0.
- `174807b9`: fixes found through headless automation sessions; evidence of tested upstream workflows, not proof those tests run here.
- `21d22cef`: child mesher/solver termination on application exit; platform process containment needs preservation.
- `470ffb1b`, `2399664b`: persistent pick identity/remesh behavior and results-area pick IDs.
- `0648a3c0`: pick/VTK-state reads on UI thread; current implementation must preserve render-thread ownership.
- `199afab5`, `d1b1515d`, `8c7ae1eb`: contact energy/history modes/axisymmetric normalization/results changes; numerical fixtures must cover them.
- `eb554576`: multiple test filters and analysis fixture dependency for result tests.

VTK remains ActiViz 5.8 despite the new release; no migration to modern VTK/Metal was found. Source notices show newly expanded modified native dependencies, so binary version numbers alone no longer identify behavior. Python/MCP are implemented, not merely planned; automation still runs through Controller/FrmMain and a Windows offscreen UI when `-g No`.

## Inspection coverage and reproducible artifacts

At the upstream baseline: **2,938 tracked files, 1,920 C# files, 14 solution projects**. The read-only inventory scanned **1,998** tracked C#/C++/header/project/target files, including vendored SDK headers. It inventories every project framework/reference and textual portability signals. [static inventory](static-inventory.json) retains the baseline snapshot/project graph/counts; run `.project/scripts/repository-inventory.py` for full per-file signal lines after future changes. Counts include project files/comments/generated sources/unused imports and must not be interpreted as a count of actual incompatible classes.

All **50** tracked DLL/EXE/LIB files were classified with `file` and hashed with SHA-256 in [native inventory](native-inventory.tsv). Signatures verify Windows-only supplied artifacts (including MMGS i386 and MMG3D x64); native dependencies were not executed. Native version claims are from notices, not runtime probes. No tracked native implementation build system/source closure for the custom NetGenMesher/QuadWild/QuadMesher was found.

Read representative implementations across model/material/element/equation, mesh/Gmsh/lp_solve, jobs/processes, persistence/binder/settings/history, controller/commands/gateways, RPC/MCP/Python engine and VTK host/picking/clipping/export. Detailed conclusions live in ARCHITECTURE/PORTABILITY_AUDIT/DEPENDENCIES; this record avoids duplicating them.

Existing tests: 69 `Test_*.py` live scripts, 37 offline runner unit tests, two Audit scripts and 45 model fixtures. No C# test project, root CI pipeline, PMX/PMH/FRD/DAT/material-library corpus or native Mac/Linux binary closure was found. No tracked production source/build/dependency configuration was changed in Phase 0.

## Actual verification and limitations

Machine: Darwin arm64, macOS 26.7; .NET SDK 10.0.401 / MSBuild 18.9.11, .NET runtime 10.0.12. No other .NET architecture/workloads were listed; no global.json exists. SDK availability does not make net48/Windows runtimes available.

Executed 37 offline unittest checks (passed), API coverage audit (exit 0), API documentation audit (exit 0). Attempted unchanged Release|x64 solution build without restore: failed with MSB4278 and MSB3644 (11 errors). Sandbox build attempts stalled; diagnostic retry outside sandbox completed, and the two stalled audit processes were terminated. No production dependency was installed to mask this failure. No numerical solve, mesh generation, PMX round-trip, live MCP/Python application workflow, Windows build or VTK selection test ran. Tests requiring original Windows application and exact native tools remain a roadmap prerequisite.

Initial upstream network read failed under sandbox DNS restrictions; authorized escalated Git read/fetch operations succeeded. A failed web retrieval of a source page is not proof that its repository is unavailable. Corresponding source/version/license details not independently retrieved are marked unresolved.

## Initial risk register

| Risk | Impact / likelihood estimate | Evidence strength / next reduction |
|---|---|---|
| Missing modified native sources | Critical / high blocker likelihood | Verified absence in checkout/notices; recover exact sources and reproduce Windows first (5.1) |
| PMX/commands tied to serialization/type identity | Critical / high | Verified dump/clone code, Microsoft runtime change; capture corpus and demonstrate compatible reader/writer/clone (1.2) |
| VTK binding/host/selection/license viability | Critical / uncertain | Windows-only legacy refs and extensive VTK pipeline verified; native interactive proof and licensing decision (2.1) |
| Controller/UI coupling drives divergence | High / high | Direct FrmMain references/commands/gateways; introduce small shared services and track patch size (3.2) |
| Native versions/topology change numerical semantics | High / medium-high | Patched Gmsh/Netgen/QuadWild, two OCCT versions; pinned topology/mesh/solver differential tests |
| False headless/automation portability | High / high | FrmMain/VTK constructed for batch, ACL/thread dependencies; native session/transport tests |
| Dual frontends drift on upstream GUI features | High / medium | Recommended transition has two presentation layers; single behavior source + explicit feature matrix/integration process |
| Intel Mac/Linux ARM64 native closure | High / unknown | No matching assets/proofs; platform runners and source builds, ARM64 Linux lower priority |

Estimates prioritize experiments; they are not measured failure probabilities. Main answer: engineering algorithms have strong reuse potential; current engineering assemblies/controller/VTK host are not independently portable. Minimal permanent divergence is plausible through boundary adapters and retained Windows reference, but feasibility is conditional on file compatibility, interactive VTK and native-source recovery.

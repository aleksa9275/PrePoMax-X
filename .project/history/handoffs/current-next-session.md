# Current continuation handoff — 8 November 2026

This is the current entry point for another agent. Older handoffs retain historical
facts and superseded instructions; do not resume their old "next task", rebuild
removed previews, or treat their "current app" paths as current availability.

## Read first and preserve the scope

1. Root `AGENTS.md`, then `.project/DECISIONS.md` D057–D061.
2. [Current completion assessment](../reports/full-completion-status.md).
3. [Tasks 0107–0110 workflow report](../reports/element-family-completion.md) and
   [machine-readable receipt](../reports/element-family-completion-verification.json).
4. [Full required parity](../PARITY.md), [test cadence](../TEST_STRATEGY.md),
   [release requirements](../RELEASE.md) and
   [deferred findings](../reports/deferred-correctness-improvements.md).

The final target is ALL original PrePoMax 3.0.0 functions, all original mesh types
and calculations, on Windows x64/macOS ARM64/Linux x64/Linux ARM64. Unavailable
Intel/PARDISO is the sole solver exception. No feature exclusion is created by a
bounded preview, copied PMX, test count or unresolved original failure.

D061 requires functionality/parity first, numerical fixes afterward. Preserve
original algorithms/tolerances and explicit failures. Necessary port/integration
repairs remain in scope. Do not normalize away B009's signed-principal mismatch,
relabel tool/job JSON as PMX, loosen gates or declare the modal-beam crash fixed.

D058 forbids hosted CI without explicit maintainer instruction. Publication on
`origin/research/native-feasibility` remains authorized with `[skip ci]` and
`git push -o ci.skip`; verify the actual remote SHA. No master/main/x/main/release
write or force push. D059 reserves Linux x64 verification for Windows/Podman near
finishing. CrossOver is reference evidence, never native Windows acceptance.

## Exact checkpoint and working state

- Checkout: `/Users/aleksa/Documents/GitLab/pre-po-max-x`.
- Branch: `research/native-feasibility`.
- Application implementation: `1580fa9c2405c4652374eeb664df963a22acd078`.
- Prior closing documentation: `c278676af270393d61e6b4c7035b607f374480e3`.
- Both were pushed and exact-remote verified. This handoff is a subsequent
  documentation/reproduction-only checkpoint; identify its commit with
  `git log -1 --format='%H %s' -- .project/handoffs/current-next-session.md`.
- Before this handoff, only four pre-existing untracked Finder files remained:
  `.DS_Store`, `PrePoMax/.DS_Store`, `X/.DS_Store`, `X/Build/.DS_Store`. Leave them
  untouched. Inspect status first; preserve any later user/agent changes.
- No feature implementation is in progress. The current user request is handoff
  and a candid full-completion assessment, not another feature increment.
- Next unused task number at inspection: **0111**; recheck before reserving it.

Do not reset, replace the checkout or blindly repeat old setup. Reuse the current
checkout unless the maintainer requests a worktree. No subagents were used in
these increments; current instructions forbid proactive delegation.

## What is delivered, and what is not

There is a usable native engineering preview, not a feature-complete replacement
or release candidate. Original-source libraries/keywords/solver/readers connect:

- Native CAD import, selected editing/history/STEP exchange and C3D4/C3D10 meshing.
- Imported solid, plane/axisymmetric, shell/membrane, beam/truss and discrete
  MASS/SPRING1/SPRING2/SPRINGA/GAPUNI workflows within the reported boundaries.
- Representative static/nonlinear, frequency/buckling, thermal, thermal expansion,
  implicit/modal-solid dynamics and cross-family jobs, fields/histories/animation.
- Named regions, selected imported-mesh transforms/renumbering and complete
  exterior surface/edge extraction with exact-byte undo/redo.
- Restricted editable original C3D8 and CAD/C3D4 PMX contracts. Broader static
  family PMX can be read, solved and copied with exact original bytes, including
  original-app readback; **this does not save newly authored native sessions or
  edit those broader graphs**.

The eight element-family milestones were approached with bounded workflows.
Steps 6–8 and broader breadth remain open. Do not count eight numbered work areas
as eight completed parity gates. No defensible whole-project percentage or ETA is
currently measured; the parity table is not an exhaustive command-level inventory.

## Recommended next implementation direction

Subject to the maintainer's next direction, prioritize **native project ownership
and original-compatible save/reopen for newly authored sessions**, starting with
one useful mechanical subset and broadening toward every family. This is a
major usability/parity gap: a native-created model currently cannot be generally
saved as an editable original PMX project. Reuse original FeModel/FeMesh/project
semantics and the existing safe framing/projection contracts; don't turn an
analysis DTO into a substitute project format.

A concrete next increment should prove native creation/edit → original PMX save →
fresh native reopen → original Windows app editable readback → equivalent deck,
solve and results, with failed/cancelled saves preserving the previous document.
State the supported graph explicitly and retain all other PMX obligations.
Original command history/result serialization must be handled deliberately;
never execute serialized history or instantiate untrusted payload types merely
to open a file. Read `X/Desktop/pmx_project.py`, `X/Feasibility/Pmx/README.md`,
D057, and the three PMX helper projects before implementation.

Subsequent substantial work areas (not a promise of one task each) are remaining
original meshers/tools; materials/orientations/constraints/contact/load/calculation
combinations; full results/selection/automation/history; then finishing native
platform/installer/source-notice acceptance. Numerical improvements remain after
functional parity under D061 and before final acceptance of the affected gates.

## Source map

| Boundary | Start here |
|---|---|
| Analysis configuration and original object creation | `X/Analysis/StaticDeck/Program.cs` |
| Original mechanical keywords and family/section admission | `CaeModel/FileInOut/Output/Calculix/StaticAnalysisDeckWriter.cs` |
| Exact standalone mesh/discrete input | `CaeModel/FileInOut/Input/InpModel/InpFileReader.MeshData.cs` |
| FRD/DAT bounded transports | `X/Results/CaeResults/FrdSnapshot.Portable.cs`, `DatSnapshot.Portable.cs` |
| Owned imported-mesh editing | `X/Desktop/MeshScene/MeshEditCommands.cs`, `X/Desktop/mesh_editor.py`, `viewport.py` |
| Shared original point transforms and extraction guard | `CaeMesh/FeMesh.Transformations.cs`, `X/Analysis/mesh_edit_layout.py` |
| Desktop and immutable native jobs | `X/Desktop/analysis_editor.py`, `viewport.py`, `jobs.py`; `X/Execution/Solve/Program.cs` |
| Existing PMX edits / new read-solve-exact-copy boundary | `X/Desktop/pmx_project.py`, `X/Feasibility/Pmx/StaticGraph.Families.cs`, `inspect-family-project.py`, `X/Feasibility/PmxMesh/FamilyMesh.cs` |
| Latest family fixtures/probes | `X/Desktop/element_family_fixtures.py`, `element_family_probe.py`, `family_pmx_probe.py` |
| Shared builds and packaging | `X/Build/build.py`, `X/Build/targets.json`, `X/Build/platforms/` |

Original objects retain assembly/type ownership and source guards. The shared
modern slice is not the full legacy graph. Do not copy its partial DLLs over an
original installed application.

## Current artifact and local-only evidence

Presence checked on 8 November; the candidate's deep/strict ad-hoc signature
verifies. These are local paths, not Git contents or public release artifacts:

| Item | Location / status |
|---|---|
| One retained Mac preview | `/tmp/prepomaxx-task0110-current-delivery/PrePoMax-X Preview.app` |
| Native CAD launcher | Sibling `Native CAD Preview.command` |
| Package manifests / source identity / logs | `/tmp/prepomaxx-task0110-package` |
| Latest jobs, original captures, failed comparisons, screenshots, recipes | `/tmp/prepomaxx-task0107-0110-evidence` |
| Mac Qt/VTK/Python runtime | `/tmp/prepomaxx-desktop-runtime/bin/python` |
| Native CAD runtime | `/tmp/prepomaxx-task0063-recipe/runtime` |
| Verified shared Mac solver build | `X/Build/artifacts/task0041-final-mac-solver/solver` |
| Linux tool/solver cache | `/private/tmp/prepomaxx-task0067-evidence/linux` |
| Original Windows solver | CrossOver bottle `PrePoMax-X-reference-2.6`, `C:\PrePoMax-X-reference\App\Solver\ccx_dynamic.exe` |
| Previously cached original 3.0.0 ZIP | **Absent** at `/tmp/prepomaxx-task0045-official-3.0.0.zip` on 8 November |

The source/receipts are committed; the candidate, raw jobs/captures and useful
caches above do not travel with a clone. Temporary paths may disappear. Do not
assume a recorded hash means the payload still exists. The latest original-app
extraction and superseded apps were intentionally removed. Read the pinned
archive/executable identity in
[the pinned identity record](../reports/pmx-3.0.0-reference/official-archive.json)
when reacquiring the reference.
The six successful original PMX capture scripts/public synthetic inputs are now
also preserved in
[tracked reproduction inputs](../reports/element-family-completion/reproduction/README.md).
Original PMX binaries are local only; keep any private models outside Git.

Current app code is exactly 1580fa9c; later documentation commits do not require
repackaging it. Package manifests verify 2521 files/2276 symlinks and an empty
source patch. Its dirty flag records the four Finder files. Both copied viewports,
prior regressions and actual Cocoa screen/ID/scalar/resize checks passed. Keep one
candidate; verify its successor before pruning it. Source/evidence/jobs/shared
caches and installed user app/state must survive cleanup.

## Verification: reuse established entry points

Do not rerun all suites merely for this handoff or a documentation change.
For an actual shared implementation change, use affected/current checks:

```sh
python3 X/Checks/check.py --output /tmp/prepomaxx-next-current-checks
# Or select a changed area with --area analysis / results / core / execution.
```

Use a new output directory. Source builds require the native .NET 10 SDK and
pinned dependency cache/offline feed (see `X/Analysis/README.md`). A new machine
needs those dependencies restored/verified; local ignored caches are not in Git.

For real desktop tests on this Mac, build current shared hosts first and run on
the native display (not `QT_QPA_PLATFORM=offscreen`, which cannot initialize this
Mac's native VTK OpenGL context):

```sh
DESKTOP_TEST_SOLVE_HOST="$PWD/X/Execution/Solve/bin/Release/net10.0/PrePoMaxX.Solve" \
  /tmp/prepomaxx-desktop-runtime/bin/python -m unittest discover -s X/Desktop -p 'test_*.py'
```

The historical default host in `test_jobs.py` was cleaned up; supply the current
host. Last complete desktop result: 95 tests. Core/Analysis/Execution current
checks passed; final Results passed 90, source-layout 12, build 9, PMX topology/
enum 3. The initial Results test compile failed on `List.Values.Length`, was
corrected to `Count`, and its final run passes. Original numerical gates remain.
These are recorded results, not freshly rerun by this documentation handoff.

For the current copied app, new integration controls are:

```text
PrePoMax-X-Viewport --element-family-probe <new-output-directory>
PrePoMax-X-Viewport --family-pmx-probe <six-original-capture-directories> <new-output-directory>
```

Add `--viewport native-cocoa` for the opt-in Mac adapter. The family probe
includes the intentionally failing beam modal-transient case and checks explicit
failure/model retention. Avoid repeated crash probes/visible Wine debug dialogs
merely to reconfirm known evidence. Use the existing reports and diagnostics.
Development-source desktop probes need an explicitly selected current solver
registry/hosts; `jobs.solver_command` intentionally refuses an implicit source
solver. Previous ad-hoc source launchers reference the removed task0106 app:
update them to the retained task0110 candidate before reuse.

Packaging, when a new candidate is actually warranted:

```sh
/tmp/prepomaxx-desktop-runtime/bin/python X/Build/build.py package \
  --target osx-arm64 --format app \
  --solver-build X/Build/artifacts/task0041-final-mac-solver/solver \
  --pmx-preview --output /private/tmp/prepomaxx-next-package
```

Use a fresh output path. The old standalone solver directory without a shared
`target` build manifest is not a substitute for the path above. Verify copied
payload/source/signature and representative workflows at candidate boundaries;
full repeated platform/package sweeps are not the routine edit cadence.

Linux ARM64 uses the retained image `localhost/prepomaxx-task0067-gui:arm64`.
The last run restored `podman-machine-default` stopped; inspect current state
before using it. Recipes/logs are under the evidence root's `linux/` directory
and `linux-final.py`. Mount Mac temporary data through **`/private/tmp`**, not
VM-local `/tmp`; source is mounted read-only, the container uses `--network none`.
Use the shell wrapper around `xvfb-run` so it is not PID 1. Preserve initial
`gvproxy`/mount failures rather than silently claiming success. A diagnostic
same-session VM start succeeded without resetting/changing VM configuration;
stop only a VM started/owned by the test and restore its prior state.

## Explicit findings to carry forward

- D029: original quadratic integration/measurement and pyramid-classifier
  findings remain; native C3D10 solver behavior is independently available.
- B006: original quadratic-pyramid-to-wedge pressure accuracy failure.
- B007: original buckling search-shift omission.
- B008: quadratic membrane/truss/circular beam and stored-force diagnostics;
  original T2D3 solver refusal.
- Coarse conductivity, coarse CAX3/CAX4R and axisymmetric segment projection.
- B009: modal beam crashes on native Mac/Linux ARM64 (139) and the original
  Windows solver under CrossOver (initial 5; final zero-load-basis deck timed
  out in its crash debugger). Windows symbols identify `nonlinmpc_` called by
  `dyna`; the zero-load basis DOF requirement is emitted but does not resolve it.
- B009 also retains a strict original/native signed maximum principal-stress
  sign-tie mismatch at t=.45, node 32, difference 3.0097802e-6. Raw tensors and
  other invariants agree within existing bounds. The recorded comparison stays
  false; no sign/tolerance normalization. Numerical acceptance remains false.
- The separate zero-exit ARPACK error completion issue **was repaired** in the
  job runner; nonempty headers and exit zero cannot override explicit *ERROR.

The governing report/receipt names actual checks and their limits. Missing,
failed, unavailable or deferred mandatory capability is not a pass and not a
new exception to the full original-functionality requirement.

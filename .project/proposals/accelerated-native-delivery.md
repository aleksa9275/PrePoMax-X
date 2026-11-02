# Accelerated native delivery plan

2 November 2026. [Task 0035](../tasks/0035-accelerated-delivery-plan.md).
Maintainer direction: installable native software first, CalculiX primary,
Code_Aster optional, less repeated testing with reliable cross-platform diagnosis.
Milestones below are planned work, not completed software or selected frameworks.

## Focus

Keep original engineering behavior, shared services and native VTK. Reuse useful
PrePoMac platform/packaging work selectively. Complete a desktop workflow rather
than accumulating inspection tools. Existing SPOOLES/PaStiX are the open-backend
route; PARDISO need not block initial delivery. Native correctness/capacity still
needs proving. Preserve the 2.22 reference; any proposed 2.23 move is explicit.

Defer Code_Aster, GPU integration, distributed/remote workers, broad solver
benchmarks and new engineering features. A Linux solver VM stays an option for
a demonstrated build/performance need. Windows x64, Mac ARM64 and Linux x64/ARM64
remain the desktop targets; final functionality/parity requirements stay intact.

## Change the order of work

| Milestone | Deliverable | Evidence sufficient to advance |
|---|---|---|
| A. Faster development loop | Fast/current-source and compatibility profiles, cached builds, compact diagnostic manifest | Relevant checks run without rebuilding unrelated suites; a failed fixture can be replayed |
| B. Installable desktop preview | Native VTK viewport, file opening, model tree, mesh/retained-result display, selection; self-contained package early | Install/launch on a clean Mac without SDK/source; open a fixture and pick its known ID; prepare other target package recipes |
| C. Usable analysis alpha | Original definitions → deck → native CalculiX → FRD/DAT → contours/history → supported save/reopen | A solid and a shell complete that workflow, with fixed displacement/reaction/ID expectations |
| D. Cross-platform alpha | Same workflow and package layout on Windows and both Linux architectures | Execute the common corpus on native target workers; separately check actual UI and installation |
| E. Full product | Expand CAD/meshing, analysis/results, legacy PMX/history and remaining workflows; finish signing/installers/Homebrew | Required parity corpus plus clean-machine install/upgrade/uninstall on all four targets |

B is an internal desktop preview; C is a scoped engineering alpha. Neither is
labelled completed parity. These early artifacts expose real integration and
installation problems sooner. Public distribution keeps normal maintainer
authorization. Native solver work starts alongside B in the work queue: the
viewport need not wait for PaStiX, and solver execution need not wait for every
dialog. Reuse original gateways, commands, writers/readers and runners; keep one
application/engineering behavior layer.

Bound the three unresolved decisions:

- **Frontend:** one short implementation comparison using the existing native
  VTK fixture. Compare the C# host/binding route with Qt/Python VTK, already partly
  exercised. Demonstrate launch, input/resize, exact picking, scalar display and
  feasible packaging; end with a concrete recommendation. Select the production
  route explicitly before expanding dialogs. Defer exhaustive lifecycle/DPI
  stress to integration. Test a PrePoMac compatibility hybrid only for a concrete
  shortcut that preserves the chosen VTK route; avoid another framework survey.
- **Solver:** build a pinned native CPU SPOOLES profile at a known reference
  thread count and connect a real solve. Recover PaStiX as the performance route
  without blocking the first UI installer. Record the actual native recipe; exact
  reproduction of unavailable proprietary Windows backend internals is not a
  first-delivery prerequisite. Do not silently change precision or backend choices.
- **Persistence:** include a small original-model save/reopen proof in C, not
  after the whole UI. Preserve IDs, units and results. Default format, legacy
  import and clone behavior remain explicit decisions; PrePoMac does not authorize
  restoring unsafe serialization. Expand historical compatibility during E.

Timebox a failed feasibility attempt to one focused implementation block; retain
the blocker, try the other established route or present a concrete choice. Avoid
open-ended environment retries/source archaeology. Calendar estimates should
follow measured host/native-build proofs. Track installable artifacts and user
workflows instead of increasing test counts.

## Lighter checking cadence

Current Core/Analysis/Execution/Results CI runs three source versions each: twelve
verifier invocations, plus research and packaging. The projects also rebuild
overlapping source closures. Preserve that coverage, but move repeated historical
replays outside the ordinary development loop. We have not measured a total
speed-up percentage. Missing host/solver/persistence integration remains a larger
delivery risk than test runtime alone.

| Trigger | Run now | Defer |
|---|---|---|
| Ordinary change | Changed-area build and relevant existing checks on the active native host | Unchanged suites, other source versions and full platform matrix |
| New defect/behavior | One useful regression for the real failure/contract; affected downstream checks | Tests that simply mirror implementation |
| Shared math/units/deck/results, interop or persistence | Current-source engineering/consumer regressions appropriate to the risk | Unrelated historical/UI/native-tool suites |
| Integration checkpoint, about daily during active coding | Build and small workflow smoke on available target workers once per candidate | Historical replays unless affected |
| Upstream/dependency/extraction change | Relevant source/legacy ownership guards, dependency checks and affected historical replays | Unaffected pins/components |
| Alpha/release candidate | Exact candidate artifact, common workflows, interactive/install checks on every claimed target; full declared release corpus | Nothing required for that candidate's stated scope |

Aim for a warm-cache fast loop under five minutes; measure it first. Build once
and reuse outputs when source/dependency/configuration keys match. Use one reviewed
active baseline for daily work; retain historical pins/evidence. Do not follow
moving upstream HEAD. Resolve the current upstream divergence as its own bounded
integration task.

Documentation changes need content/link checks; styling needs visual inspection.
A parser fix needs its valid/malformed fixtures and relevant consumers. Source
extraction/legacy guards run when those boundaries change. Full third-party
inventories rerun when their inputs change. Keep full suites callable for periodic
runs and investigations; a future periodic CI job is not configured by this plan.

Do not weaken numerical tolerances, delete useful tests or hide known failures.
Retain the two existing failure reproductions and tetra measurement gate.
Unrelated implementation can progress with those explicit known results.

## Cross-platform coverage and bug tracing

Use Mac ARM64 for the local loop, existing GitLab native Linux x64 after authorized
publication, the existing ARM64 VM/container or another ARM worker for Linux ARM64,
and native Windows when its checkout/runner is available. No new runner or
successful execution is assumed. An unavailable platform remains pending; it does
not block unrelated local development, but cannot be called verified/released.

Use a small common corpus: analytical solid, thin shell, nonsequential-ID mesh/
result selection, malformed/unsupported input, cancellation/nonzero exit and
supported save/reopen. Add fixtures for actual bugs or new capabilities. Share
fixture IDs, units, tool profiles and expected outcomes. Headless compute belongs
in routine CI; actual picking, graphics, DPI and install behavior need native UI
sessions at milestone/candidate checkpoints. Containers alone do not prove GUI
or other CPU-architecture behavior.

Each run retains one manifest: source commit/dirty-tree identity, fixture version,
OS/architecture/runtime, tool build IDs, arguments, thread settings, units,
exit/status and output locations. Keep necessary failed-run inputs/logs. Reuse
pinned dependency manifests. A dirty-tree hash alone cannot reproduce source:
retain the relevant patch/new files locally, excluding private files/secrets.

Each new bug gets a stable task/issue reference, minimal fixture, expected/actual
result, first known bad build and affected platforms. Add one regression at its
owning layer; verify the fix on the failing platform and a comparison platform
when available. Export user model data only through an explicit user action.

Keep task outcomes short: **changed / checked / open / next**. One current status
entry links generated evidence. Detailed reports belong to milestones/difficult
bugs. Keep the charter stable and record actual decisions without copying every
test transcript. Preserve historical evidence.

## Immediate next task

Implement A with existing test projects/verifiers: fast/current-source versus
compatibility profiles, shared caching and a compact manifest. Do not invent
another test framework. Record timings, then start B's bounded VTK host/package
proof and the native SPOOLES build, converging on C. This planning task changes
neither current CI YAML nor application code and authorizes no public write or
implicit frontend/serializer/numerical-policy choice.

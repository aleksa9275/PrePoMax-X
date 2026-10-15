# Project status

Updated: 2026-10-15 (Europe/Belgrade). **Phase 0 and bounded tasks 0002–0010
complete within their recorded scopes. New tasks 0004–0007 add native-source/
build-boundary audit, structured kernel execution, native VTK smoke evidence
and shell-junction fixtures. PMX inspection now also passes Linux ARM64;
structured-kernel/rendering execution remains Mac ARM64 only. Earlier core/data
probes passed Linux x64 gates. Windows compatibility, matching native sources,
full application/UI/platform parity and production integration remain open.
Actual legacy PMX inventory and a user-confirmed CrossOver read/save/reopen cycle
are now available; native Windows validation remains pending.**

## Current continuation — local work complete, publication follow-up

Maintainer now explicitly authorizes commit/push of completed research to origin
(task 0012), superseding earlier uncommitted-only instructions for this one
publication. [Local completion report](reports/local-preparation-completion.md):

- Selected PMX shallow records: 27/29 types match; job execution settings and a
  new keyword-override member differ. No full semantic/history equivalence.
- Linux ARM64 GCC -O2 fails right_45_45 (12/13). Explicit contraction-off and
  -O0 pass 13/13. Default failure is retained; production policy remains open.
  With the explicit control the public research suite passes, matching Mac.
- Nine VTK provenance/mixed-order/lifecycle checks pass on native Mac; no real
  pointer/DPI/platform or leak claim. Seven analytical checks pass using the
  exact bundled CalculiX 2.22 through CrossOver; no native Mac solve claim.
- Mac data/structured checks and native/header audit rerun successfully within
  their scopes; matching custom source recovery remains blocked on availability.

The additive native Linux x64 research job is prepared for publication. Hosted
outcome/remote identity will be recorded after push. Earlier milestone paragraphs
below retain their historical authorization/publication state; this section
defines the current continuation. Production sources/x/main remain unchanged.

## Repository

`origin` is the maintainer's PrePoMax-X fork; `upstream` is official PrePoMax. Last synchronization on 2026-10-13 found zero new commits. Local `master` remains equivalent to the recorded upstream ref at `de8f73032a72746e3d6d9afd53d9fbd289eb310a`; no new fetch or upstream write was performed for the Podman adjustment.

`x/main` contains reviewed Phase 0 records at `c840aceb8cc007e1a151b5e35fed2f413f6451e4`; implementation commit `92a491cd` remains on `feature/core-feasibility`. The maintainer pushed it and reported a failed pipeline. The agent has not pushed or merged feature implementation. The maintainer committed and pushed the complete Podman/CI tooling and evidence as `822bae2528be6e38df6d472fc979c36b9f3e4d27` (commit title: Phase 0 verification). The maintainer authorized the agent to commit/push the closing evidence and next bounded probe/investigation during the current 2026-10-14 continuation. Normal maintainer workflow resumes afterward; x/main integration remains separately gated.

Naming remains PrePoMax-X and X/x throughout. At the last release check (2026-10-13), official download was 3.0.0 RC1; stable 2.6.0 is a reference branch, not a tag. Release availability was not rechecked for this tooling task. Phase 0 history/evidence is preserved in [initial audit](reports/initial-audit.md).

## Actual verification

The new experiment links seven unchanged upstream source files: five STL implementation files, Vec3D and FeNode. The net10.0 build has zero package or original-project references, zero errors and three retained upstream-source warnings. Original engineering/application source and project files are unchanged.

On native macOS ARM64, both the audit baseline and isolated stable 2.6.0 replay passed **23 analytical/STL checks and two CLI process contracts each**. Cube inspection returns 12 triangles and bounds [0,0,0]–[1,1,1]. Source/fixture hashes and build/runtime evidence are in [core report](reports/core-feasibility.md) and its JSON records. The two commits have identical selected source; replay mechanics are verified, adaptation to changed source is not.

Linux: maintainer installed Podman/Podman Desktop; an applehv ARM64 VM was initialized and local tests now use Podman. Later on 2026-10-14 the maintainer authorized complementary GitLab native Linux x64 CI preparation. Both pinned revisions pass **23 analytical/STL checks plus two CLI contracts each** on Linux ARM64, with portable observations matching the macOS records. The recipe, runner and [Podman verification report](reports/podman-verification.md) retain architecture/image/runtime/source evidence. **Task 0002's native Linux x64 gate passed on 2026-10-14:** manual GitLab pipeline #2947482796/job #17176590675 at feature commit 822bae25, hosted amd64 runner on an Intel Xeon CPU, SDK 10.0.402/.NET 10.0.13. Both pinned revisions pass 23 checks plus two CLI contracts each and exactly match Mac portable observations; six comparison regressions pass. Downloaded JSON, tooling/reference hashes and runner/image/CPU provenance were independently checked and retained in [native x64 report](reports/gitlab-linux-x64.md). Windows/reference comparisons, whole-core, PMX, Controller, VTK, CAD/meshing and solver execution remain untested here.

Cached-image ARM64 reruns pass. The supplemental Linux amd64 image builds, but .NET/MSBuild crashes under the existing QEMU route before tests; a structured failure report is retained. No translated x64 pass is claimed. Podman's VM was stopped cleanly after verification; its machine and image cache remain installed.

Existing Phase 0 results remain: 37 offline runner tests, two API/source audits and nine Git sync safety tests passed; original Windows solution build failed on Mac due to missing VC/net48 targets. Those are historical results, not rerun as part of the bounded probe.

## Scope and next gate

**Next session: native Windows is expected to be available.** Read the
[Windows handoff](handoffs/windows-next-session.md) and prepared
[task 0011](tasks/0011-windows-reference-validation.md) before work. Use the
research/native-feasibility branch containing task 0012; verify its publication
status rather than starting from the default branch. Begin with pinned
original-app cube/definitions/history capture, then
portable probes. No Windows result is claimed yet. Maintainer corrected the
required targets to **Windows x64, Linux x64, Linux ARM64 and Apple M-series
macOS ARM64**; “x86” means x64. Intel Macs are excluded, Linux ARM64 required.

2026-10-15: [task 0010](tasks/0010-pmx-linux-verification.md) is complete.
All 24 synthetic PMX tests pass in the cached offline Linux ARM64 container;
both private reference inventories exactly match Mac portable observations.
Input hashes unchanged; runtime assembly addition is separately guarded, no
payload assemblies loaded. Startup/initial comparison diagnostics are retained;
the VM stopped successfully. This new probe still needs native Linux x64/Windows
execution. [Evidence](reports/pmx-linux-verification.md) and
[preparation exit gates](reports/preparation-exit-gates.md) define the next bounded
work: semantic project/history snapshots, matching native-source recovery,
interactive rendering and a pinned analytical solve/CAD shell-junction baseline.
Tasks 0004–0010 remain uncommitted; no production change, push or integration.

2026-10-15: [task 0008](tasks/0008-pmx-record-inspection.md) and
[task 0009](tasks/0009-crossover-reference.md) are complete within bounded scopes.
Supplied header is **PrePoMax v2.5.1 dev**, 1,638 records/215 types decoded on
native Mac without application assemblies/BinaryFormatter. Twenty-four synthetic
tests pass. Input unchanged/outside Git. [Schema proposal](proposals/portable-document-schema.md)
records openness to a versioned cross-platform format; production stays undecided.

CrossOver 26.2 now has dedicated bottle **PrePoMax-X-reference-2.6**, official
2.6.0 portable bundle and persistent reference copies. Human confirmed model
display, separate Save As and model/results display after reopening. Custom
model/mesh and result mesh/node-lookup blocks match exactly; four result fields
preserve original bytes with the documented datatype Int32 insertion. Opaque
history trailer matches. NRBF member/type changes need semantic/job-field review.
This is supplementary original-application evidence, not native platform/numerical
parity. No meshing/solver/regeneration ran. See [PMX evidence](reports/pmx-record-inspection.md)
and [CrossOver instructions](reports/crossover-reference.md). Tasks 0004–0009
remain uncommitted on research/native-feasibility; no pushes/integration.

Task 0007's [shell-junction fixture preparation](reports/shell-junction-fixtures.md)
is complete: four hand-authored S4 inputs, geometry/intent manifest and two
checker regressions. Connected, coincident-disconnected, unsplit-plate and gap
contracts are explicit. They are not CAD, live mesher or Windows reference files.
All new task 0004–0007 work is uncommitted on research/native-feasibility; F001
remains Proposed. Do not infer implementation or commit/push authorization.

Task 0006's [native VTK smoke experiment](reports/vtk-native-smoke.md) is complete:
14 synthetic geometry/rendering/ID-selection checks pass on Mac ARM64 with an
isolated pinned Python VTK 9.5.2 wheel. Render/deformation/removal images inspected.
Programmatic cell/point/rectangle picks return expected FEM IDs; clipping drops
global-ID arrays. Genuine UI/DPI interaction, Windows/platform rendering parity
and frontend/binding selection remain open. Original vtkControl/ActiViz unchanged.

Task 0005's [structured meshing experiment](reports/structured-meshing-feasibility.md)
is complete on Mac ARM64: 13 original C++ vector cases, 17 independent native
checks and seven unchanged C# count/grid checks pass; 1,728 count cases match
across languages. Full C# Mapping reaches an ExceptionTools/MessageBoxes compile
boundary. No production sources were changed; full CAD meshing and F001 remain
pending. New-probe Linux/Windows execution has not run.

Task 0004's [native feasibility audit](reports/native-feasibility.md) is complete
on `research/native-feasibility`, under the maintainer's 2026-10-14 authorization
to progress through bounded pre-Windows steps. Gmsh C and plain C++/Q-Morph
declarations compile on Mac ARM64; original C++/CLI wrapper fails at msclr.
Matching custom source recovery is still open, including inaccessible patched
Gmsh, external NetGenMesher/nglib and QuadWild forks, and QuadMesher implementation.
Forty binary/archive hashes and a QuadWild checksum discrepancy are recorded.
The completed audit is uncommitted; no native CAD engine or mesher ran.

Maintainer input recorded on 2026-10-14: [F001, automatic shell-junction
connectivity](features/F001-automatic-shell-connectivity.md), starting with a
shell T-profile on a plate and reducing manual compound-part preparation.
Status is Proposed; priority, connection policy and implementation remain
unset. See the [feature register](features/README.md). Windows reference capture
will be undertaken later when the maintainer returns to the Windows machine;
no new PMX/history or meshing fixture has been captured.

[Task 0002](tasks/0002-core-feasibility.md) remains bounded. Local Podman tests require no publication. Root/experiment GitLab CI YAML is restored under the later authorization, limited to relevant pushes or manual web runs on `feature/core-feasibility`. The new `run-ci.py` executes both pinned probes with Linux/X64 assertions, compares the same portable observations as Podman, and retains JSON diagnostics plus selected non-secret CI identifiers. Local macOS ARM64 rehearsal and native Linux x64 hosted execution passed both revisions. The manual web pipeline executed the configuration successfully; a separate semantic lint command was not run. Subsequent push pipeline #2947646455 at 0020d0d8 passed, verifying push-trigger execution as well. See [CI preparation](reports/gitlab-verification.md). Hosted settings were not changed and the historical failed pipeline was not deleted. After the maintainer signed in, authenticated inspection confirmed pipeline #2944154347 failed before job creation because GitLab required identity verification: zero jobs, no probe execution. Instance runners are enabled; runner #54907241 with tag `saas-linux-small-amd64` is online/active; personal namespace usage shows 0/400 compute minutes for October 2026. Successful execution of the new pipeline confirms the earlier identity restriction no longer blocks this run. This is an account eligibility failure, not evidence of a source/build/test failure or malformed YAML.

Task 0002 is complete within its seven-file scope. Review the newly retained native x64 evidence and uncommitted handoff updates. Feature implementation remains on `feature/core-feasibility`; integrating it into `x/main` and beginning a further bounded implementation task require authorization. The maintainer has now explicitly authorized agent commits/origin pushes for this continuation, covering the closing evidence and next bounded dependency/probe/PMX identity investigation. Windows reference access is available; capture still needs to occur.

Task 0003 is published on `feature/core-data-feasibility` at da264eef from evidence commit 0020d0d8. Its six-file unchanged Matrix/metadata/scaling/FRD-stream probe passes 30 checks plus two CLI contracts on Mac ARM64 and native GitLab Linux x64, with exactly matching observations. Push pipeline #2947730759/job #17178539405 also reran both original probes and six regressions successfully. Downloaded data/core JSON, actual native runner/image/CPU provenance and independent hash/comparison checks are retained. GeometryTools hits a measured WinForms compile boundary while Matrix builds unchanged. Source-only PMX identity inventory and Windows capture instructions are prepared; actual Windows payload graphs/round-trip remain pending. See [task 0003](tasks/0003-core-data-feasibility.md) and [data report](reports/core-data-feasibility.md). PyQt/Python VTK + shared C# and a C# frontend remain production candidates; no GUI/binding/serializer commitment made. Native-source recovery remains an independent parity prerequisite. [Roadmap](ROADMAP.md), [decision register](DECISIONS.md).

# Project status

Updated: 2026-10-14 (Europe/Belgrade). **Phase 0 complete; task 0002 implemented, macOS ARM64 and Podman Linux ARM64 passed. Native Linux x64 acceptance remains pending.**

## Repository

`origin` is the maintainer's PrePoMax-X fork; `upstream` is official PrePoMax. Last synchronization on 2026-10-13 found zero new commits. Local `master` remains equivalent to the recorded upstream ref at `de8f73032a72746e3d6d9afd53d9fbd289eb310a`; no new fetch or upstream write was performed for the Podman adjustment.

`x/main` contains reviewed Phase 0 records at `c840aceb8cc007e1a151b5e35fed2f413f6451e4`; implementation commit `92a491cd` remains on `feature/core-feasibility`. The maintainer pushed it and reported a failed pipeline. The agent has not pushed or merged feature implementation. The Podman tooling and complementary GitLab native Linux x64 preparation are uncommitted for maintainer review. Maintainer handles all pushes and normally commits.

Naming remains PrePoMax-X and X/x throughout. At the last release check (2026-10-13), official download was 3.0.0 RC1; stable 2.6.0 is a reference branch, not a tag. Release availability was not rechecked for this tooling task. Phase 0 history/evidence is preserved in [initial audit](reports/initial-audit.md).

## Actual verification

The new experiment links seven unchanged upstream source files: five STL implementation files, Vec3D and FeNode. The net10.0 build has zero package or original-project references, zero errors and three retained upstream-source warnings. Original engineering/application source and project files are unchanged.

On native macOS ARM64, both the audit baseline and isolated stable 2.6.0 replay passed **23 analytical/STL checks and two CLI process contracts each**. Cube inspection returns 12 triangles and bounds [0,0,0]–[1,1,1]. Source/fixture hashes and build/runtime evidence are in [core report](reports/core-feasibility.md) and its JSON records. The two commits have identical selected source; replay mechanics are verified, adaptation to changed source is not.

Linux: maintainer installed Podman/Podman Desktop; an applehv ARM64 VM was initialized and local tests now use Podman. Later on 2026-10-14 the maintainer authorized complementary GitLab native Linux x64 CI preparation. Both pinned revisions pass **23 analytical/STL checks plus two CLI contracts each** on Linux ARM64, with portable observations matching the macOS records. The recipe, runner and [Podman verification report](reports/podman-verification.md) retain architecture/image/runtime/source evidence. **Task 0002's native Linux x64 acceptance gate is still pending.** Windows/reference comparisons, whole-core, PMX, Controller, VTK, CAD/meshing and solver execution remain untested here.

Cached-image ARM64 reruns pass. The supplemental Linux amd64 image builds, but .NET/MSBuild crashes under the existing QEMU route before tests; a structured failure report is retained. No translated x64 pass is claimed. Podman's VM was stopped cleanly after verification; its machine and image cache remain installed.

Existing Phase 0 results remain: 37 offline runner tests, two API/source audits and nine Git sync safety tests passed; original Windows solution build failed on Mac due to missing VC/net48 targets. Those are historical results, not rerun as part of the bounded probe.

## Scope and next gate

[Task 0002](tasks/0002-core-feasibility.md) remains bounded. Local Podman tests require no publication. Root/experiment GitLab CI YAML is restored under the later authorization, limited to relevant pushes or manual web runs on `feature/core-feasibility`. The new `run-ci.py` executes both pinned probes with Linux/X64 assertions, compares the same portable observations as Podman, and retains JSON diagnostics plus selected non-secret CI identifiers. Local macOS ARM64 rehearsal passed both revisions; hosted execution and GitLab semantic lint remain pending. See [CI preparation](reports/gitlab-verification.md). Hosted settings were not changed and the historical failed pipeline was not deleted. After the maintainer signed in, authenticated inspection confirmed pipeline #2944154347 failed before job creation because GitLab required identity verification: zero jobs, no probe execution. Instance runners are enabled; runner #54907241 with tag `saas-linux-small-amd64` is online/active; personal namespace usage shows 0/400 compute minutes for October 2026. Whether the earlier identity restriction is now cleared remains unconfirmed without a new run. This is an account eligibility failure, not evidence of a source/build/test failure or malformed YAML.

Review the uncommitted tooling/evidence changes, publish them through the maintainer workflow, then inspect the native x64 GitLab job and its two JSON artifacts. A native Linux x64 Podman engine remains an alternative route. Record actual runner architecture/provenance and comparison results before closing the gate. The agent must leave changes uncommitted and never push unless the maintainer changes that instruction explicitly.

After that, review the next managed source slice and begin PMX/history corpus/type-identity investigation before assembly separation. PyQt/Python VTK + shared C# and a C# frontend remain production candidates; no GUI/binding/serializer commitment made. Native-source recovery remains an independent parity prerequisite. [Roadmap](ROADMAP.md), [decision register](DECISIONS.md).

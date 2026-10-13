# Project status

Updated: 2026-10-13 (Europe/Belgrade). **Phase 0 complete; task 0002 authorized and implemented locally, with macOS ARM64 checks passed and Linux execution pending.**

## Repository

`origin` is the maintainer's PrePoMax-X fork; `upstream` is official PrePoMax. Synchronization on this date found zero new commits. Clean `master` remains equivalent to upstream at `de8f73032a72746e3d6d9afd53d9fbd289eb310a`. No upstream writes occurred.

The maintainer authorized the recommended approach, promotion of reviewed Phase 0 records and a new branch. `x/main` was fast-forwarded to documentation commit `c840aceb8cc007e1a151b5e35fed2f413f6451e4`; `feature/core-feasibility` was created from it. Probe implementation remains on this feature branch. No feature implementation merge or public push has been performed by the agent. Exact feature commit: `git log -1 feature/core-feasibility`.

Naming remains PrePoMax-X and X/x throughout. Latest official download remains 3.0.0 RC1; stable 2.6.0 is a reference branch, not a tag. Stable 3.0 correspondence remains unestablished. Phase 0 history/evidence is preserved in [initial audit](reports/initial-audit.md).

## Actual verification

The new experiment links seven unchanged upstream source files: five STL implementation files, Vec3D and FeNode. The net10.0 build has zero package or original-project references, zero errors and three retained upstream-source warnings. Original engineering/application source and project files are unchanged.

On native macOS ARM64, both the audit baseline and isolated stable 2.6.0 replay passed **23 analytical/STL checks and two CLI process contracts each**. Cube inspection returns 12 triangles and bounds [0,0,0]–[1,1,1]. Source/fixture hashes and build/runtime evidence are in [core report](reports/core-feasibility.md) and its JSON records. The two commits have identical selected source; replay mechanics are verified, adaptation to changed source is not.

Linux: no local Docker/Podman/Linux VM/QEMU route found. GitLab hosted Linux x64 job is prepared, YAML parsed, but not executed or published. Runner access/enablement/quota cannot be verified anonymously: project runner endpoint returned 401. **Task 0002's Linux acceptance gate is pending; do not call this a completed cross-platform milestone.** Windows/reference comparisons, whole-core, PMX, Controller, VTK, CAD/meshing and solver execution remain untested here.

Existing Phase 0 results remain: 37 offline runner tests, two API/source audits and nine Git sync safety tests passed; original Windows solution build failed on Mac due to missing VC/net48 targets. Those are historical results, not rerun as part of the bounded probe.

## Scope and next gate

[Task 0002](tasks/0002-core-feasibility.md) is authorized for local implementation/commits. Public fork pushes still require approval of concrete branch/diff; no automatic publishing or integration. The next concrete gate is publishing `feature/core-feasibility` to origin, executing its Linux x64 CI checks for both source revisions and reviewing the resulting artifacts.

After that, review the next managed source slice and begin PMX/history corpus/type-identity investigation before assembly separation. PyQt/Python VTK + shared C# and a C# frontend remain production candidates; no GUI/binding/serializer commitment made. Native-source recovery remains an independent parity prerequisite. [Roadmap](ROADMAP.md), [decision register](DECISIONS.md).

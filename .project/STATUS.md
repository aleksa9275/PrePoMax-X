# Project status

Updated: 2026-10-13 (Europe/Belgrade). **Phase 0 deliverables complete; cross-platform implementation has not begun.** Await maintainer review/authorization.

Repository: origin is the PrePoMax-X fork, upstream is official PrePoMax. Detected default `master`; clean mirror and cp/main pinned at de8f73032a72746e3d6d9afd53d9fbd289eb310a. Documentation/maintenance scripts are on `feature/project-initialization` only, locally committed. No remote push or cp/main merge. Exact feature commit: `git log -1 feature/project-initialization`.

Release: latest download 3.0.0 RC1 (12 October); latest stable 2.6.0 (1 September). No upstream tags advertised/fetched. Stable 3.0 commit/tag not established. [Baseline and evidence](reports/initial-audit.md).

Verification: 37 existing offline runner tests and two source/API audits passed. Nine isolated Git sync-safety tests passed. Unchanged solution build failed with 11 errors for absent Visual C++ targets and net48 reference assemblies on macOS ARM64. No numerical/meshing/live-app/PMX/VTK/Windows acceptance test performed.

Maintenance live checks: dirty checkout correctly refused before fetch. After initial local commit `4856ca5c0e36e9be8cbe646fb19bed6ca2cb2510`, both `upstream-sync.py --dry-run` and normal mode succeeded against official upstream: detected master, zero new commits, mirror already equivalent. Verified mirror difference `0 0`, cp/main unchanged at baseline and clean feature checkout. The final verification record is a separate local follow-up commit; use Git for its exact hash. No public branch was created remotely.

Primary blockers to future parity: legacy serialization/deep clones and type identities; Windows/native assembly dependency closure; unavailable custom native sources; VTK binding/host/license/selection feasibility. See [portability audit](PORTABILITY_AUDIT.md) and [dependency matrix](reports/dependency-matrix.md).

Recommended proposal: shared behavior/core and separate frontends during transition, retaining original Windows frontend and isolating adapters. No GUI/renderer/serializer framework commitment made.

Next authorized work ends at Phase 0. Proposed first implementation tasks after approval: managed .NET slice feasibility (1.1), PMX/history/type compatibility (1.2), interactive native VTK proof (2.1); start native-source recovery (5.1) alongside them. [Roadmap](ROADMAP.md), [pending decisions](DECISIONS.md).

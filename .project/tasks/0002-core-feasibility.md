# Task 0002 — First runnable upstream-source feasibility milestone

Status: proposed; implementation authorization pending. Proposed: 2026-10-13 (Europe/Belgrade).

## Objective

Produce a small native command-line probe using the actual upstream C# source, with reproducible checks on macOS ARM64 and Linux x64. Establish a repeatable upstream-update test before broad core/controller extraction. This proves a bounded source slice, not that the whole engineering core is portable.

Proposed working branch: `feature/core-feasibility`. Proposed .NET target: net10.0 for this experiment, subject to dependency findings; no GUI framework selection is included. The experiment must not alter production algorithms or make its exploratory assembly a new persistent file-format identity.

## Authorization and repository preparation

Before implementation, obtain maintainer approval of this task. Separately approve promoting the existing Phase 0 documentation/maintenance commits into `x/main` so new feature work can start from the documented integration branch. No automatic merge or public push is authorized by this proposal.

Once approved: inspect working tree/remotes, run guarded upstream synchronization, identify the exact current analysis commit and release state, and record it in the task result. If upstream has changed since the audit, inspect relevant source/dependency changes before proceeding. Preserve `master` as upstream-only and keep all work on the dedicated feature branch.

## Scope and source components

Start with `STL/` (ASCII/binary STL import/export), `CaeGlobals/CommonClasses/Vec3D.cs`, and `CaeMesh/Nodes/FeNode.cs` (coordinates and transformations). Inspect their actual compile closure; include only necessary upstream dependencies. Use the existing cube STL fixture under `APIs/Python/Test_Scripts/Models/`, plus independently specified geometry/transform cases.

Add isolated SDK-style build/test/command-line projects in an X-owned directory, proposed `X/Feasibility/Core/`. Link upstream source files in their existing locations instead of copying/translating them. Preserve source paths, namespaces and algorithms. Do not retarget the original solution wholesale, move existing code, build a substitute mesh model or silently stub failed dependencies. If an additional type would require an application-source change or new dependency outside this scope, report the exact boundary for review.

The probe should read a supplied STL and report triangle count and bounds, and exercise the original node/vector transformations against analytically known coordinates. Use structured output for cross-platform comparison. It does not load/save PMX, run a solver, import CAD, or claim full FE mesh/model support.

## Expected modifications

- Additive experiment build configuration, CLI and meaningful fixture checks; no production dependency changes.
- A source-closure manifest listing included upstream paths, source hashes and excluded/blocked components with reasons. Verify included files remain byte-identical to the recorded upstream commit.
- A Linux check job if a suitable GitLab runner is available, or an explicitly documented native Linux/VM test route. Check infrastructure availability rather than claiming a job passed because configuration exists.
- Result report with commands, native architecture, pinned source/dependency/runtime versions, actual test outcomes and required future adapters.
- Update STATUS, task record and decision entries with evidence; no GUI/serializer commitment.

## Acceptance criteria and tests

1. Probe builds and runs natively on the current Mac ARM64 using actual upstream source. The normal upstream solution remains unchanged.
2. Existing cube STL and explicit ASCII/binary cases produce expected triangle counts/bounds and round-trip geometry within the format's declared precision; orientation and malformed-file behavior are checked.
3. Original FeNode/Vec3D translation, rotation and mirror routines match independently calculated coordinates. Tests cover non-origin transforms and preserve node IDs.
4. The same probe and fixtures execute on Linux x64 with equivalent structured output. If Linux infrastructure is unavailable, report that acceptance gate pending; do not mark the milestone cross-platform complete.
5. Produce a per-platform result record and an explicit list of what was proved. Windows checks can be added when its reference environment is available; no Windows equivalence claim without execution.
6. Demonstrate update resilience by applying the same source-link build to a second real upstream revision of this slice, recording its immutable commit and inspecting any differences. If source changes, test expected behavior before declaring compatibility. Do not manufacture an upstream change or treat a successful merge as a successful replay.

Upstream replay must operate in an isolated checkout/experiment context and cannot modify `master` or integrate into `x/main` automatically. Prefer build-manifest-only changes where possible; any required source patches are reviewed and enumerated.

## Maintenance design

Keep X-owned probes/adapters/frontends separate from upstream files. Keep domain/application behavior in upstream C# wherever feasible; reuse existing IPython gateways and command semantics for later services. Track per-change source patches and feature counterparts. Avoid duplicating Controller or translating engineering algorithms to Python.

The pinned audit comparison from `upstream/v2.6.0` to `upstream/master` includes 228 changed files under `PrePoMax/Forms/` or `UserControls/`, 30 under `vtkControl/`, and 300 under engineering/shared-library directories. These are path-based counts including additions/deletions, not effort estimates or predictions about future work. They demonstrate that frontend changes must be expected alongside core changes.

For a new upstream release: update clean mirror, classify changes, replay probes and reference tests on an integration branch, review adapter/GUI behavior, then approve development integration. Limit unavoidable upstream edits to narrow boundaries and preserve the original Windows build as an oracle.

## Follow-on work and early prerequisites

- PMX/history compatibility: acquire Windows-generated fixtures and capture serialized type/assembly graphs before broad assembly separation. Do not change serialization as part of this task.
- Interactive VTK/frontend comparison: evaluate PyQt6 + Python VTK + shared C# backend as a full production candidate alongside a C# frontend + VTK binding route. Require exact node/face/element picking, rectangle selection, deformation, clipping and DPI behavior before selecting a host.
- Native-source recovery: identify matching NetGenMesher/Netgen, modified QuadWild/Gmsh and QuadMesher sources/build recipes now; missing sources can block parity independently of managed-core progress. Contacting maintainers remains a separately authorized action.

Review after completion: approve the next source slice/services based on measured dependency boundaries, verify file-compatibility work can proceed, and select rendering experiments. A small successful probe is the start of the project, not proof of a finished portable core.

# Task 0019 — Sync upstream RC2 and measure portable-core impact

Publication update, 2026-10-18: implementation/evidence published at 47f17be6;
exact-commit native Linux x64 pipeline #2960334103 and downloaded artifacts pass.
[Task 0021 publication record](../reports/mesh-workflow-publication.md) supersedes
historical uncommitted status below. New features wait for maintainer approval.

2026-10-18, Europe/Belgrade. Maintainer requests syncing the fork with Matej's
3.0.0 RC2, comparing changes, identifying necessary adjustments and accelerating
implementation toward a cross-platform 3.0.0 near the upstream stable release.
This supersedes task 0018's stop boundary for this work. The requested fork
sync authorizes a normal fast-forward of origin/master; implementation/evidence
changes stay local for review under the normal maintainer publication workflow.
No x/main integration, upstream write, force push, frontend/default serializer,
numerical/tolerance change or native-tool substitution is implied.

Scope: detect current upstream default; preserve the exact master mirror;
separate RC2 source marker 912fb3d08014f246d48bef14d62a2cba0fdf5bb0 from
post-RC2 master f6273e39983e06042ae8b06e9a3dd0f729ea4b91; inspect engineering,
persistence, UI/API and native changes. Add executable pinned replay of the
existing shared libraries against both source revisions, retaining source
guards, assembly ownership, all checks and both open correctness failures.
Prepare the implementation priorities and identify unresolved release gates.

Initial state: clean research/native-feasibility at
2f2eca945c8acad0c3b902537f95055e67be6a42. Local/origin master both de8f7303.
Upstream has 12 commits through RC2 and 10 afterward. Official downloads page
lists RC2 dated 17 October 2026. A source version marker is not proof of exact
correspondence with the distributed Windows binary.

Status: complete within sync/impact/replay scope. Origin/master is remotely
verified at f6273e39. No-conflict Git-object merge rehearsal; development/x/main
branches not integrated. Working-tree/RC2/post-RC2 builds pass on native Mac
and Linux ARM64: 25 mapping/30 data/95 accepted element checks, 28 CLI/four data
controls, seven replay guard tests. Portable outcomes and tooling fingerprints
match exactly across hosts; both correctness failures remain. Initial Podman
startup failure was resolved by the maintainer starting it; retry succeeded and
that VM is left running. Native Windows/hosted x64 replay remains pending;
configured CI is not a hosted pass. New tooling/evidence stays uncommitted.
Evidence and implementation priorities: ../reports/upstream-3.0.0-rc2.md.

# PrePoMax release parity tracking

Maintainer direction, 3 November 2026 (D054): **3.0.0 is the initial parity
target**. Continue tracking future upstream releases and maintaining open-source
macOS/Linux distributions even if upstream does not accept the contribution.
Windows x64, Linux x64, Linux ARM64 and Apple Silicon macOS ARM64 remain required.

## Release identity

| Item | Current state |
|---|---|
| Product functionality target | PrePoMax 3.0.0 |
| Verified stable 3.0.0 commit and binary correspondence | Pending; do not label an RC or assembly version as verified stable |
| Retained RC2 source marker | 912fb3d08014f246d48bef14d62a2cba0fdf5bb0 |
| Retained post-RC2 mirror/source pin | f6273e39983e06042ae8b06e9a3dd0f729ea4b91 |
| Read-only upstream HEAD check, 3 November | master at 2a25db82896aa0aa51666eb550df19d3950a8630; no tags advertised; GitLab release API returned an empty list |
| Upstream-history handling | Existing [divergence review](reports/upstream-2026-11-02.md) still applies; no reset/merge/mirror rewrite in task 0043 |

An empty release API and lack of tags do not establish that stable 3.0.0 does not
exist. Exact release/source correspondence remains a pending acceptance item.
The existing replay pins and engineering reference remain explicit meanwhile.

## Current workflow coverage

These are coverage boundaries, not a percentage estimate or an exhaustive list
of upstream commands. Add per-feature fixtures as each original workflow moves
into the shared application; preserve intentional upstream behavior and units.

| Area | Verified bounded coverage | Remaining parity work |
|---|---|---|
| Mesh input/decks | Original INP reader, IDs, bounded mesh export and static C3D8 deck | Full import/export/model graph and supported element/analysis combinations |
| Materials/analysis editing | Original shared types/writers callable through services | Model tree and original-definition UI, broader assignments/loads/steps |
| Native solve | Mac ARM64/Linux x64 analytical static cube; desktop start/cancel/status | Analysis/backend breadth, capacity/performance and native other-target acceptance |
| Visualization | INP/C3D8 FRD, contours, original IDs/values; opt-in direct Mac child-view proof | Full vtkControl pipeline, clipping/highlighting, deformation, input/DPI/performance and other native desktops |
| Results/history | Original bounded FRD fields/invariants and static-shaped DAT histories | Full original results orchestration, shell/dynamic outputs and interactive histories |
| Persistence | Legacy reference/inventory evidence retained | Explicit supported save/reopen, full PMX/PMH/settings/history and compatibility |
| CAD/meshing | Original source/native inventory and research fixtures retained | Matching custom sources/builds, native import/repair/mesh and full geometry/selection behavior |
| Automation | Existing upstream API/gateway/journal investigated | Portable scripting, command history/replay and MCP workflow parity |
| Engineering correctness | Strict accepted-scope checks retained | Both known element failures and quadratic-tetrahedron measurement gate remain |
| Distribution | Internal ad-hoc Mac DMG; shared four-RID hosts | Native Windows/Linux desktop/package acceptance, signing/clean OS/Homebrew and complete corresponding sources/notices |

## Future release cadence

For every upstream release, record its exact source/artifact identity, compare
features and engineering/persistence/native deltas, adapt shared owners and
platform boundaries, then run the affected Windows-reference/native corpus.
Publish version-aligned project packages only after their declared scope passes.
Upstream contribution acceptance does not determine whether this maintenance
continues. Preserve upstream history, attribution, sources and licenses.
No automated release monitor, upstream message or public package channel has
been created by recording this policy.

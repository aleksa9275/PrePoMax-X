# Task 0004 — Native CAD/mesher source and build feasibility

Status: bounded audit complete on 2026-10-14. Matching-source recovery and native
CAD/mesher builds remain pending. Authorized 2026-10-14 by the maintainer's instruction to
progress through the proposed pre-Windows steps, starting with the native
source/build recommendation and stopping at completed task boundaries before
usage runs out. Branch: `research/native-feasibility`, based on c11a73d9.
Existing uncommitted feature-proposal records are preserved.

## Bounded scope

1. Inspect matching native-source availability for patched Gmsh, NetGenMesher/
   Netgen, modified QuadWild and QuadMesher. Record immutable public references
   where accessible and distinguish upstream references from matching forks.
2. Hash and inspect shipped native binary formats, source/header identities and
   contradictory provenance notices. Measure native compiler/header boundaries
   without changing original files or replacing native tools.
3. Investigate existing mesher runners, process gateways and C++/CLI wrapper;
   document viable build/interop routes and required source recovery inputs.
4. Retain reproducible offline evidence and a source-recovery checklist. Complete
   the investigation even if exact corresponding sources cannot be retrieved;
   keep source recovery and native CAD/meshing parity explicitly pending.

No production refactoring, new production dependencies, frontend selection,
mesher/solver substitutions, x/main integration, maintainer messages, commits
or pushes are authorized by this task. Full native builds need matching sources
and prerequisite tooling; header compilation is not a native mesher build.

## Acceptance and handoff

An evidence-backed component matrix, actual compiler outcomes, binary/header
hashes, accessible source references or precise access failures, recovery inputs
and next bounded task. Update STATUS/DECISIONS and dependency records. Run only
checks appropriate to this additive investigation; Windows, live CAD/meshing,
numerical equivalence and source-to-binary correspondence remain separate gates.

## Result

See [native feasibility report](../reports/native-feasibility.md) and its measured
JSON. Seventeen source identities match the pinned baseline; three compiler
measurements match expectations. Forty binary/archive identities retained.
Published patched Gmsh branch is inaccessible (authenticated browser 404);
NetGenMesher/modified nglib, modified QuadWild and QuadMesher need matching source
inputs. Public QuadWild v0.0.2 source commit pinned, without claiming correspondence
to PrePoMax's modified binaries. Actual quad_from_patches hash exposes an upstream
README/notice discrepancy. No native mesher was linked, built or run.

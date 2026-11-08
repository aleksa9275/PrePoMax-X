# Project status

_Replace this file as work progresses; history is in git and `.project/history/`._

## Where we are (8 November 2026)

- **Phase A build and verification closeout complete:** whole original domain
  assemblies build for .NET 10. Established engineering suites, 95 desktop
  regressions and 164 structural workflow checks pass on Mac/Linux ARM64.
  The two known original element correctness failures remain failed.
- **Native Gmsh baseline:** patched 4.13.0 + static OCCT 7.7.0 builds on both
  ARM64 hosts; each passes 18 adapter checks and 7 runtime rejection controls.
  Lookup now enforces source/version/kernel/library fingerprints. Gmsh 4.15.2
  remains an unadopted candidate; its patch/C API compatibility looks feasible.
- **Q-Morph correction:** the original wrapper is dormant (private, uncalled,
  "not offered yet"). Exact QuadMesher sources/license remain unresolved after
  GitHub/GitLab searches; no missing exposed original meshing option is established.
- **Evidence:** [closeout report](reports/phase-a-closeout.md),
  [receipt](reports/phase-a-closeout-verification.json),
  [initial Phase A build](reports/phase-a-domain-libraries.md).
- **Inventory:** 108 selected source entries at A; 237 commands and 72 forms
  at zero B/C/V. A means compilation, not runtime or whole-product parity.
  [Inventory](PARITY_INVENTORY.md) excludes abstract/enum/unused-file count artifacts.
- **Working preview:** retained Python/Qt candidate `1580fa9c` is unchanged;
  bounded prior workflows remain evidence, not original Controller/UI parity.
- **Original findings:** D029, B006–B009 and the other numerical diagnostics
  remain open under D061; [backlog](reports/deferred-correctness-improvements.md).

## Phases

| Phase | Content | State |
|---|---|---|
| A | Whole CaeGlobals/CaeMesh/CaeModel/CaeResults/CaeJob, net48 kept | build + ARM64 closeout verified |
| B | Original Controller/Commands headless; allowlisted original PMX/clone | next |
| C | Cross-platform UI reusing original forms/property classes + native VTK | later |
| Fixes | Recorded original bugs and ordinary compiler warnings | after parity |
| Release | Four targets, installers, signing, sources/notices | later |

## Next step

Phase B: run original Controller/Commands against `X/Domain`, isolate main-form/
VTK dependencies, reuse original PMX serialization with a strict allowlist, and
repair reached clone/Windows API paths. The recorded API portability repairs are
required port work; ordinary original numerical fixes/warnings stay post-parity.
Recover experimental QuadMesher sources before activating a native implementation.

Full original application/API/PMX/mesher parity, the complete Windows/net48 build,
native Windows, deferred Linux x64 and four-target release acceptance remain open.
The two new original-solver comparisons are CrossOver evidence, not Windows acceptance.

## Environment

- .NET 10: Mac SDK 10.0.403; local Linux test SDK 10.0.402.
- Closeout sources/builds/logs: `/private/tmp/prepomaxx-phase-a-closeout` (local
  cache, not distributed source/payload). Offline Gmsh recipe: `X/Build/Gmsh`.
- Podman was restored to stopped. Preview/cache locations remain in the historical
  handoff; use this status and D062 for current direction.
- Hosted CI remains on hold (D058); publish with `[skip ci]` / `-o ci.skip`.

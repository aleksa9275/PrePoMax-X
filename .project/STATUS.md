# Project status

_Replace this file as work progresses; history is in git and `.project/history/`._

## Where we are (8 November 2026)

- **Phase B headless implementation complete.** Whole original Controller,
  every Commands compile item, mesher runners, Python gateways/journal and APIs
  build for .NET 10. The original Windows form and the portable host share the
  generated `IControllerHost` contract. Original model algorithms remain shared.
- **Original persistence works through an explicit allowlist.** Restricted NRBF
  supplies original PMX/history/cloning; no unrestricted .NET 10 formatter.
  Representative bidirectional original Windows 3.0.0 PMX exchange passes through
  CrossOver, including results and identical queried displacement. A solid deck
  exported by the original app matches the native export apart from CRLF/LF endings.
- **Mac/Linux ARM64:** all 12 focused Controller workflow stages and 20 persistence
  checks pass per host, including saved-state picked-selection replay, native
  Gmsh meshing, CalculiX solve/results, 3MF and surface filters. Established core,
  analysis, execution and results regressions pass within their accepted scope;
  the two original D029 correctness failures remain failed. All eleven original
  C# assemblies pass the C# 7.3/net48 compile-only check.
- Evidence: [Phase B report](reports/phase-b-controller.md),
  [receipt](reports/phase-b-controller-verification.json),
  [host usage](../X/Controller/README.md),
  [persistence boundary](../X/Persistence/README.md).
- **Phase A closeout remains valid:** whole original domain assemblies,
  engineering suites and native pinned Gmsh adapter checks on both ARM64 hosts.
  [Report](reports/phase-a-closeout.md).
- **No native version upgrade:** patched Gmsh 4.13.0 remains the baseline;
  4.15.2 is unadopted. Exact dormant Q-Morph wrapper sources/license remain
  unresolved; no missing exposed original meshing option is established.
- Inventory: 108 selected model/mesh entries AB; 237 Commands entries A,
  236 structurally B (the abstract base is A); 72 forms await C. B is reachability,
  not verification of every feature. No full-family V acceptance is inferred.
- Retained Python/Qt candidate `1580fa9c` is unchanged. No installed original
  application was overwritten. No new application/package candidate was created.
- D029, B006–B009 and other original numerical diagnostics remain open under D061;
  [backlog](reports/deferred-correctness-improvements.md).

## Phases

| Phase | Content | State |
|---|---|---|
| A | Whole domain libraries, original net48 kept | build + ARM64 closeout verified |
| B | Original Controller/Commands headless; allowlisted PMX/history/clone | implemented; representative ARM64/reference workflows verified |
| C | Cross-platform UI reusing original forms/property classes + native VTK | next |
| Fixes | Recorded original bugs and ordinary compiler warnings | after parity |
| Release | Four targets, installers, signing, sources/notices | later |

## Next step

Phase C: connect the original Controller/Commands and original form/property
behaviour to the cross-platform application host and native VTK viewport. Reuse
the Phase B runtime/persistence services; provide real camera/rendering/editor
services and retain original command/history semantics. The development headless
script entry point is not the finished CLI/RPC/MCP application host.

Continue representative original-app/PMX coverage as feature families are connected.
Exhaustive PMX/mesher/solver/feature matrices, native Windows, deferred Linux x64,
source/stable-binary correspondence and four-target release acceptance remain
open. CrossOver is reference evidence, not native Windows acceptance. Original
numerical findings remain deferred under D061.

## Environment

- .NET 10: Mac SDK 10.0.403; Linux verification SDK 10.0.402.
- Local Phase B logs/profiles/reference evidence: `/private/tmp/prepomaxx-phase-b`.
  These are temporary evidence, not distributed runtime payloads.
- Podman restored to stopped. Keep the single existing preview candidate.
- Hosted CI hold remains (D058): publish `[skip ci]` / `git push -o ci.skip`.

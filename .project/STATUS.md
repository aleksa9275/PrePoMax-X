# Project status

_Replace this file as work progresses; history is in git and `.project/history/`._

## Where we are (8 November 2026)

- **C1 UI foundation implemented.** Original PMX open → native VTK render/pick →
  existing material edit → original undo/redo → save/reopen works through the
  original Controller. The thin Qt/PyQt6 UI directly accesses the same C# objects
  through embedded Python.NET. Original material view classes, converters and
  shared form validation remain the implementation.
- **C1 verification:** Mac ARM64 native Cocoa display and Linux ARM64 under Xvfb
  each pass 20 property/Controller and 18 GUI checks. Original Windows 3.0.0 via
  CrossOver opens/resaves the edited PMX; exported deck content matches apart
  from CRLF/LF. Native readback retains the edit. All eleven original C# assemblies
  pass the C# 7.3/net48 compile-only check. Focused Controller/persistence and UI
  build checks pass. Xvfb is supplemental virtual-display evidence.
- [C1 report](reports/phase-c1-ui-foundation.md),
  [receipt](reports/phase-c1-ui-verification.json),
  [run/verify instructions](../X/UI/README.md).
- **Phase B remains implemented:** whole original Controller, every Commands
  compile item, mesher runners, Python gateways/journal and APIs build for .NET 10.
  Original PMX/history/cloning use restricted NRBF with an explicit allowlist.
  [Phase B report](reports/phase-b-controller.md).
- **Phase A/B ARM64 closeouts remain valid.** Previous native Gmsh/CalculiX/results,
  3MF/surface and engineering checks are retained. C1 changes no engineering
  algorithm or native version. Two original D029 correctness failures remain
  failed; D061 fixes stay deferred.
- Patched Gmsh 4.13.0 remains the baseline; 4.15.2 is unadopted. Exact dormant
  Q-Morph wrapper sources/license remain unresolved; no missing exposed original
  meshing option has been established.
- Inventory: 108 selected model/mesh entries AB; 237 Commands entries A,
  236 structurally B; three commands now C. All 72 complete form entries remain
  pending: C1's shared material editing is partial form reuse. No full-family V
  acceptance is inferred. [Inventory](PARITY_INVENTORY.md).
- Retained Python/Qt preview `1580fa9c` is unchanged. C1 is a development host;
  no new package/installer candidate was created or installed original overwritten.

## Phases

| Phase | Content | State |
|---|---|---|
| A | Whole domain libraries, original net48 kept | build + ARM64 closeout verified |
| B | Original Controller/Commands headless; allowlisted PMX/history/clone | implemented; representative ARM64/reference workflows verified |
| C1 | UI foundation and representative original-code workflow | implemented; bounded Mac/Xvfb/reference checks passed |
| C2–C5 | Model authoring; geometry/meshing; analysis/results; remaining integration | next |
| Fixes | Recorded original bugs and ordinary compiler warnings | after parity |
| Release | Four targets, installers, signing, sources/notices | later |

## Next step

C2: connect the complete model tree and original form/property behaviour for
selection/set authoring, materials/sections/interactions and analysis definitions.
Extend the C1 host with original Controller commands and history. Complete
material/property creation, table-row controls and temperature switching; do not
count the existing-value editor as a complete original material form.

Then C3 geometry/meshing, C4 jobs/results and full viewport presentation, C5 remaining
application/automation integration and parity audit. The development hosts are
not the finished original CLI/RPC/MCP application surface.

Continue representative original-app/PMX comparisons. Full feature/backend/PMX
matrices, native Windows, deferred Linux x64, physical Linux GPU/Wayland and human
GUI acceptance, source/stable-binary correspondence and four-target distribution
remain open. CrossOver is reference evidence, not native Windows acceptance.
D029/B006–B009 and other numerical diagnostics remain under the
[post-parity backlog](reports/deferred-correctness-improvements.md).

## Environment

- .NET 10: Mac SDK 10.0.403; Linux verification SDK 10.0.402.
- VTK 9.5.2, PyQt6 6.10.0, Qt 6.10.2, Python.NET 3.1.0; explicit CPython 3.12 profiles.
- C1 evidence: `/private/tmp/prepomaxx-c1`; previous B evidence retained separately.
  Temporary profiles/build outputs are not distributed runtimes.
- Podman restored to stopped. Keep the single existing preview candidate.
- Hosted CI hold remains (D058): publish `[skip ci]` / `git push -o ci.skip`.

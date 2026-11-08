# Project status

_Replace this file as work progresses; history is in git and `.project/history/`._

## Where we are (8 November 2026)

- **C2 core model authoring implemented.** The C1 host now exposes the model tree,
  model properties/parameters, sets/surfaces, reference points/coordinate systems,
  materials/sections/constraints, interactions/contacts, distributions/amplitudes,
  initial conditions, steps, BCs/loads/defined fields, outputs and solution controls.
  Original factories, descriptors, validation, command dispatch and PMX/history
  remain the implementation. Tree folders/order and modeless viewport picking work.
- **C2 verification:** Mac ARM64 and Linux ARM64/Xvfb each pass 33 C2 authoring +
  18 GUI checks, plus C1's 20 property + 18 GUI regressions. The factory/property
  matrix covers all 12 step families, including the wear boundary-step sequence.
  Original Windows 3.0.0 via CrossOver opens/resaves the authored PMX and exports
  identical deck content apart from CRLF/LF. Native readback retains engineering
  definitions, picked set history and tree layout. All eleven original C# assemblies
  pass C# 7.3/net48 compile-only checks; focused Controller/persistence/UI checks pass.
- [C2 report](reports/phase-c2-model-authoring.md),
  [receipt](reports/phase-c2-ui-verification.json), [run/verify](../X/UI/README.md).
- **C1 foundation remains valid:** Qt/PyQt6 widgets access the same live original
  C# objects through embedded Python.NET; native VTK renders original actor data.
  [C1 report](reports/phase-c1-ui-foundation.md).
- **Phase A/B closeouts remain valid:** whole domain/Controller/Commands assemblies,
  explicit allowlisted original PMX/history/cloning, representative ARM64 native
  meshing/solve/results/export and original-app interoperability.
  [Phase B report](reports/phase-b-controller.md).
- Inventory: 108 selected model/mesh entries AB, 82 now C; 237 Commands entries A,
  236 structurally B, 83 now C. All 72 full-form entries remain unaccepted: core
  authoring reuse is not complete control/form parity. V remains zero; no whole
  feature-family acceptance is inferred. [Inventory](PARITY_INVENTORY.md).
- No numerical algorithm/tolerance or native version changed. D029's two original
  failures and D061 findings remain open. Patched Gmsh 4.13.0 remains the baseline;
  4.15.2 is unadopted. Exact dormant Q-Morph wrapper sources/license remain unresolved.
- Retained Python/Qt preview `1580fa9c` is unchanged. The new host remains a
  development application; no new installer/package candidate or hosted CI run.

## Phases

| Phase | Content | State |
|---|---|---|
| A | Whole domain libraries, original net48 kept | build + ARM64 closeout verified |
| B | Original Controller/Commands headless; allowlisted PMX/history/clone | implemented; representative ARM64/reference workflows verified |
| C1 | Native UI foundation | representative workflow verified |
| C2 | Original-code core model authoring | implemented; representative Mac/Xvfb/reference checks passed |
| C3 | Geometry/meshing UI | next |
| C4 | Jobs/results and complete viewport presentation | pending |
| C5 | Remaining application/automation and complete UI parity audit | pending |
| Fixes | Recorded numerical bugs and compiler warnings | after parity |
| Release | Four targets, installers, signing, sources/notices | later |

## Next step

C3: connect original geometry/mesh setup/property classes and Controller commands
for CAD import/editing, mesh controls/options, mesh creation and editing. Reuse
existing pinned native tool adapters and runtime profiles; do not recreate the
engineering model or change backend versions.

C4 completes jobs/results and viewport presentation; C5 covers remaining original
application/automation, material libraries/curve plotting, full selection-tool/
keyboard/focus/preferences and form-control parity. The development hosts are
not the finished original CLI/RPC/MCP surface.

Continue representative original-app comparisons. Exhaustive feature/backend/PMX
matrices, native Windows, deferred Linux x64, physical Linux/GPU/Wayland and human
input, source/stable-binary correspondence and four-target distribution remain
open. CrossOver is reference evidence, not native Windows acceptance. Recorded
numerical findings remain under the [D061 backlog](reports/deferred-correctness-improvements.md).

## Environment

- .NET 10: Mac SDK 10.0.403; Linux verification SDK 10.0.402.
- VTK 9.5.2, PyQt6 6.10.0, Qt 6.10.2, Python.NET 3.1.0; explicit CPython 3.12 profiles.
- C2 evidence: `/private/tmp/prepomaxx-c2`. Temporary builds/profiles are not
  distributed runtimes. Prior A/B/C1 evidence is retained separately.
- Podman restored to stopped. Keep the single existing preview candidate.
- Hosted CI hold remains (D058): `[skip ci]` / `git push -o ci.skip`.

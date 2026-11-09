# Project status

_Replace this file as work progresses; history is in git and `.project/history/`._

## Where we are (9 November 2026)

- **C4 core jobs/results and native viewport implemented.** Original analysis
  setup/run/check/monitor/kill, result field/history tools, coordinate systems/
  reference points, part editing/exports and strict result PMX workflows are
  connected. Units/prompts, calculations, job lifecycle, parsers and command
  history remain original C#. Native tools/solver profiles are explicit.
- Native VTK presents scalars/legends/status, symbols/annotations/measurements,
  vector/tensor plots, deformation, undeformed copies, section cuts/CAD caps/
  hatching, result patterns, original animation frames, PNG capture/sequences and
  Ogg Theora video. Exact platform AVI support and full viewport/form parity
  remain open. UI tasks preserve output and lock document mutations.
- **C4 milestone:** Mac ARM64 and Linux ARM64/Xvfb each pass 41 service + 35 GUI
  checks, C1 20+18, C2 33+18, C3 25+21 (including the added CAD-cap check).
  Isolated original Windows 3.0.0 opens/resaves result projects; native strict
  readback preserves fields, equation/table outputs and result feature definitions.
  All eleven net48 assemblies compile; nine focused Controller stages, including
  20 strict-persistence checks, pass. See [C4 report](reports/phase-c4-jobs-results.md)
  and [receipt](reports/phase-c4-ui-verification.json).
- **Analytical stress diagnostic remains failed:** 199.99200439453125 versus
  expected 200, absolute tolerance .001; loaded-source doubling and original/native
  PMX values agree. Cause unresolved, no tolerance/algorithm change
  ([B011](bugs/B011-c4-linear-cube-stress-diagnostic.md)). Active-child cancellation
  passes; pre-start cancellation remains [B012](bugs/B012-analysis-cancellation-before-start.md),
  concurrent CAD cancellation remains [B010](bugs/B010-concurrent-cad-cancellation.md).
- Earlier A/B/C1/C2/C3 closeouts remain: whole original assemblies,
  Controller/Commands, allowlisted PMX/history, original engineering and native
  viewport/authoring/CAD/mesh workflows. Model/mesh inventory: 108 AB, 87 C;
  Commands: 237 A, 236 B, 175 C. All 72 full forms unaccepted; V remains zero.
  [Inventory](PARITY_INVENTORY.md). These counts are availability, not full parity.
- D029 and all D061 numerical findings remain open. Patched Gmsh 4.13.0 and
  CalculiX 2.22 remain pinned. Gmsh 4.15.2 is unadopted; dormant Q-Morph wrapper
  source/license remains unresolved. No new installer/package candidate or CI run.
  The single retained preview `1580fa9c` is unchanged.

## Phases

| Phase | Content | State |
|---|---|---|
| A | Whole domain libraries; original net48 kept | ARM64 closeout verified |
| B | Original Controller/Commands; allowlisted PMX/history/clone | representative ARM64/reference workflows verified |
| C1 | Native UI foundation | representative workflow verified |
| C2 | Core model authoring | implemented; representative ARM64/reference checks passed |
| C3 | Core geometry/meshing | implemented; representative ARM64/reference checks passed |
| C4 | Core jobs/results and viewport presentation | implemented; representative ARM64/reference checks passed |
| C5 | Remaining application/automation; complete UI parity audit | next |
| Fixes | Recorded numerical/original bugs and compiler warnings | after parity |
| Release | Four targets, installers, signing, sources/notices | later |

## Next step

C5: finish remaining original application/automation surfaces, libraries and
plotting, then audit every form/control, tree/selection action, keyboard/focus and
preference against the original. Close remaining result-component/history and
viewport/export details, including platform AVI support; do not infer complete
parity from core C1–C4 adapters. Continue maximum original-code reuse and strict
PMX persistence. Full backend/edit/export/animation/cancellation/corpus matrices,
physical/native platforms and distribution acceptance remain open. CrossOver is
reference evidence; Linux x64 remains deferred to Windows Podman (D059).

## Environment

- .NET 10: Mac SDK 10.0.403; Linux verification SDK 10.0.402.
- VTK 9.5.2, PyQt6 6.10.0, Qt 6.10.2, Python.NET 3.1.0; explicit CPython 3.12.
- C4 evidence: `/private/tmp/prepomaxx-c4`; temporary builds are not distributions.
- Podman restored to stopped; keep one preview candidate.
- Hosted CI hold D058: `[skip ci]` / `git push -o ci.skip`.

# Project status

_Replace this file as work progresses; history is in git and `.project/history/`._

## Where we are (9 November 2026)

- **C5 application tools implemented; original UI source audit recorded.** Original
  settings, material libraries, command/PMH editing and Python journals, keyword
  editing, script panel/Stop, RPC/MCP automation, query/Find/contact search, advisor,
  saved/follower views, plotting and result-component actions are connected.
  Original Controller, property views, calculations, serializers and commands own
  engineering state. [C5 report](reports/phase-c5-application-tools.md).
- C5 final focused Mac ARM64 and Linux ARM64/Xvfb each pass **31 service + 40 GUI
  checks**, including authenticated/busy/read-only MCP, current-user pipe ping,
  Python Stop, strict files/PMX, rectangle picking, colored native 3MF, RGBA capture
  and result-component removal. All six exported AVI frames decode on both hosts.
  The Linux check image adds missing `libpulse0`; Qt/VTK/engine pins are unchanged.
- C1 20+18, C2 33+18, C3 25+21 and C4 41+35 representative regressions pass on both
  ARM64 hosts. Original Windows 3.0.0 in isolated CrossOver opens/resaves a C5 PMX
  and reads its material library; native strict readback retains script/plot state,
  the material and user keyword. All eleven original net48 assemblies compile;
  ten focused Controller stages pass, including strict persistence/native 3MF.
  [Receipt](reports/phase-c5-ui-verification.json). CrossOver is reference evidence.
- **Full UI parity is not accepted.** The [source audit](reports/phase-c5-ui-audit.json)
  inventories all 72 forms, 993 designer fields and 796 event subscriptions, with
  source fingerprints, adapters and open comparison work. This is source coverage,
  not verification of every control. All full forms remain C/V pending. Selected
  model/mesh entries: 108 AB, 88 C; Commands: 237 A, 236 B, 227 C; V remains zero.
  [Inventory](PARITY_INVENTORY.md).
- B011's analytical stress diagnostic remains **failed**: 199.99200439453125 vs
  expected 200, absolute tolerance .001. D029 and the other D061 numerical/original
  findings remain open. B010 concurrent CAD and B012 pre-start job cancellation
  remain; active Python Stop is a different check. No numerical expectation changed.
- Patched Gmsh 4.13.0, CalculiX 2.22 and lib3mf 2.4.1 remain explicit/pinned.
  Gmsh 4.15.2 is unadopted; dormant Q-Morph wrapper source/license is unresolved.
  No new installer/preview or hosted CI run. Retained preview `1580fa9c` is unchanged.

## Phases

| Phase | Content | State |
|---|---|---|
| A | Whole original domain libraries; net48 retained | ARM64 closeout verified |
| B | Original Controller/Commands; allowlisted PMX/history | representative ARM64/reference workflows verified |
| C1 | Native UI foundation | representative workflow verified |
| C2 | Core model authoring | implemented; representative ARM64/reference checks passed |
| C3 | Core geometry/meshing | implemented; representative ARM64/reference checks passed |
| C4 | Core jobs/results and viewport | implemented; representative ARM64/reference checks passed |
| C5 | Application/automation and UI audit | application tools implemented; full parity audit findings remain open |
| Fixes | Recorded numerical/original bugs and warnings | after parity |
| Release | Four targets, installers, signing, sources/notices | later |

## Next step

Close the C5 audit's remaining behavioral comparisons and implementation details
before declaring Phase C complete: all original form/control/selection/filter/
keyboard/focus/DPI/clipboard interactions, complete complex/all-analysis/backend
and viewport/export/animation matrices, and large projects. Native Windows codec
selection and portable AVI >2 GiB/OpenDML remain open. The source audit alone does
not close these items. Then perform the D061 correctness/warning sweep.

Broader original PMX corpus, physical Linux/GPU/Wayland/human-input acceptance,
native Windows, deferred Linux x64 on Windows Podman (D059), installers/signing and
full distribution acceptance remain open. No additional final-scope exception.

## Environment

- .NET 10: Mac SDK 10.0.403; Linux verification SDK 10.0.402.
- VTK 9.5.2, PyQt6 6.10.0, Qt 6.10.2, Python.NET 3.1.0; explicit CPython 3.12.
- C5 evidence: `/private/tmp/prepomaxx-c5`; temporary builds are not distributions.
- Podman stopped after verification; keep one preview candidate.
- Hosted CI hold D058: `[skip ci]` / `git push -o ci.skip`.

# Project status

_Replace this file as work progresses; history is in git and `.project/history/`._

## Where we are (9 November 2026)

- **C3 core geometry/meshing UI implemented.** Original part properties/transforms,
  CAD split/offset/repair/surface operations, compound/cell/subpart controls, all
  ten mesh setup types (nine in 2D), native mesh/preview commands, mesh editing,
  quality/geometry analysis and imports/exports are connected through original
  views, rules, Controller and Commands. Element edges render from original faces.
- Native operations/CAD history run on .NET tasks with Qt-thread presentation,
  output and locked document mutations. Modeless drafts retain native picking.
  Repeated native jobs/history now allocate separate logs without overwriting
  evidence or changing native work paths. Original stop is exposed; concurrent
  CAD-stage cancellation is unaccepted ([B010](bugs/B010-concurrent-cad-cancellation.md)).
- **C3 verification:** Mac ARM64 and Linux ARM64/Xvfb each pass 25 service +
  20 GUI checks. Each also passes C1's 20 service + 18 GUI and C2's 33 service +
  18 GUI regressions. The synthetic cube meshes to 241 nodes/677 linear tetrahedra;
  separate CAD translation/split/group/rename and PMX workflows pass.
- Original Windows 3.0.0 via isolated CrossOver opens/resaves both meshed and
  split/grouped CAD projects; native readback preserves data. Mesh export matches
  after normalizing only CRLF/LF and the original per-export random heading ID.
  All eleven net48/C# 7.3 assemblies compile; 49 process regressions and nine
  focused Controller stages (20 strict persistence checks) pass.
- [C3 report](reports/phase-c3-geometry-meshing.md),
  [receipt](reports/phase-c3-ui-verification.json), [run/verify](../X/UI/README.md).
  C1/C2 and Phase A/B closeouts remain valid: whole original assemblies,
  Controller/Commands, allowlisted original PMX/history, shared native viewport
  and representative engineering workflows.
- Inventory: 108 selected model/mesh entries AB, 87 C; 237 Commands A, 236 B,
  136 C. All 72 full-form entries remain unaccepted; V remains zero. UI availability
  is not complete form/backend/four-target acceptance. [Inventory](PARITY_INVENTORY.md).
- No numerical algorithm/tolerance or native version changed. D029's original
  failures and D061 findings remain open. Patched Gmsh 4.13.0 remains selected;
  4.15.2 is unadopted. Dormant Q-Morph wrapper sources/license remain unresolved.
- Retained preview `1580fa9c` is unchanged. This is a development host; no new
  installer/package candidate or hosted CI run.

## Phases

| Phase | Content | State |
|---|---|---|
| A | Whole domain libraries, original net48 kept | build + ARM64 closeout verified |
| B | Original Controller/Commands headless; allowlisted PMX/history/clone | representative ARM64/reference workflows verified |
| C1 | Native UI foundation | representative workflow verified |
| C2 | Original-code core model authoring | implemented; representative ARM64/reference checks passed |
| C3 | Core geometry/meshing UI | implemented; representative ARM64/reference checks passed |
| C4 | Jobs/results and complete viewport presentation | next |
| C5 | Remaining application/automation and complete UI parity audit | pending |
| Fixes | Recorded numerical/original bugs and compiler warnings | after parity |
| Release | Four targets, installers, signing, sources/notices | later |

## Next step

C4: connect original job setup/run/monitor/cancel and results tools, then complete
native viewport glyphs/annotations, contours/legends, deformation, animation and
captures. Reuse original Controller, property classes, solver/native profiles and
result readers; preserve original numerical behavior and strict PMX persistence.

C5 completes original application/automation, libraries/plotting, full tree/
selection/keyboard/focus/preferences and form-control parity. Exhaustive CAD,
mesh-type/backend/edit/export/cancellation matrices, broader original PMX corpus,
native Windows, deferred Linux x64, physical Linux/GPU/Wayland/human input,
source/stable-binary correspondence and four-target distribution remain open.
CrossOver is reference evidence, not native Windows acceptance. Recorded numerical
findings remain in the [D061 backlog](reports/deferred-correctness-improvements.md).

## Environment

- .NET 10: Mac SDK 10.0.403; Linux verification SDK 10.0.402.
- VTK 9.5.2, PyQt6 6.10.0, Qt 6.10.2, Python.NET 3.1.0; explicit CPython 3.12 profiles.
- C3 evidence: `/private/tmp/prepomaxx-c3`. Temporary builds/profiles are not
  distributed runtimes. Prior A/B/C1/C2 evidence is retained separately.
- Podman restored to stopped. Keep the single existing preview candidate.
- Hosted CI hold remains (D058): `[skip ci]` / `git push -o ci.skip`.

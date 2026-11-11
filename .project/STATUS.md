# Project status

_Replace this file as work progresses; history is in git and `.project/history/`._

## Where we are (11 November 2026)

- **C6 original main window.** The menu bar is now the original `FrmMain` menu:
  16 menus, 313 release-visible items, generated from FrmMain with the original
  entity selection, confirmations and per-view enabling; every reachable item runs
  through the original Controller in the GUI probe (Geometry/Model/Results views).
  Standard views use the original Y-up convention (the earlier Z-up was a port bug).
  The original scale bar, unit-system label, invariant number format and result
  selector sizing replace the visible review defects. PMX size caps now scale with
  the file, so large original projects load. [C6 report](reports/phase-c6-main-window.md).
- **C7 original tool strips and model tree.** The five FrmMain tool strips with the
  original icons, and the ModelTree's Geometry / FE Model / Results tabs with the
  original layout, counts, node images, search box and context-menu rules, generated
  from the original sources. [C7 report](reports/phase-c7-toolbars-tree.md).
- **C8 tree remainder and model/mesh evidence.** Tree rename, drag and drop,
  original groups, Group Cells / Fuse Bodies, keys, mouse-over highlight, keyword
  counts and the recovered Parts icon; output-panel links; part highlighting in the
  headless host. Executed UI evidence for 18 model/mesh entries (element classes,
  mass/spring/gap elements, InvertedElements, MassSection, Damping).
  [C8 report](reports/phase-c8-tree-elements.md).
- **C9 original forms compiled whole.** 39 original form classes (the FrmProperties /
  FrmPropertyListView family, FrmNewModel, FrmSelectItemSet) and the FrmMain form-hosting
  members now run unchanged on a headless WinForms control model drawn by Qt; menus and tree
  open them through the original FrmMain entry points, and viewport picks inside them use the
  original `Controller.SelectPointOrArea`. 38 forms are ABC.
  [C9 report](reports/phase-c9-original-forms.md).
- **C10 data grid forms compiled whole.** FrmAmplitude, FrmDistribution, FrmResultFieldOutput
  and FrmResultHistoryOutput with the original FrmPropertyDataListView, DataGridViewCopyPaste
  (cell edit, new row, copy/paste, plot, delete) and FrmDiagramView, on a headless
  DataGridView/BindingSource model. 43 classes compiled whole; 42 forms ABC. Export → History
  Output now opens the original export form (the port showed a viewer).
  [C10 report](reports/phase-c10-data-grid-forms.md).
- **C11 child-window forms and dialogs compiled whole.** 25 more original forms (material,
  surface interaction, step controls, analysis, monitor, animation, query, find, the view forms,
  transformation, settings, parameters, material library, value/colour/regenerate dialogs, ...) with
  the original CodersLabTreeView, CollapsableGroupBox and AnalysisProgressView, on new TreeView,
  timer/scroll-bar/table-layout and ZedGraph-scaling models. Menus, tree and toolbars open them
  through their FrmMain members; the C5 toolkit dialogs they replace are no longer reachable.
  68 classes compiled whole; 66 forms ABC. [C11 report](reports/phase-c11-child-forms.md).
- **C12 code editor forms, beams, Command base.** FrmCalculixKeywordEditor and FrmEditCommands (with
  FrmViewObjectProperties) compiled whole with the original CalculixInpTextBox/PythonEditorTextBox on a
  FastColoredTextBox model; Edit History and CalculiX Keywords open the originals. Beam element classes have
  executed UI evidence (CAD shell free edges, second-order Netgen shell mesh). 70 classes compiled whole; 69
  forms ABC. lp_solve (GmshCaller interval assignment) is missing on macOS/Linux.
  [C12 report](reports/phase-c12-editor-forms.md).
- **P1 desktop packages.** `X/Build/build_ui.py` builds every native input from its pinned recipe (new:
  lp_solve 5.5.2.11, Mmg 5.5.2/5.7.0, CPython 3.12.14 lock, hash-pinned UI wheels) and packages the X/UI
  app: macOS ARM64 DMG and Linux ARM64 tar.gz (self-checks pass: real solve, CAD, all meshers incl. the
  lp_solve shell mesh; Linux on a clean Ubuntu 24.04), Windows x64 zip (cross-packaged, not run; Gmsh and
  CalculiX missing). QuadWild has no macOS/Linux build (fork source). Manual testing guide:
  [MANUAL_TESTING.md](MANUAL_TESTING.md). [P1 report](reports/phase-p1-desktop-packages.md).
- C1–C5 remain as verified on 9 November ([C5 report](reports/phase-c5-application-tools.md)).
  Full remaining-work list, split into manual and agent work:
  [REMAINING_WORK.md](REMAINING_WORK.md).
- **Full UI parity is not accepted.** Forms 69/72 C, 0 V (FrmMain, FrmPythonStop open; FrmSelectEntity AB).
  Inventory: model/mesh 108/108 C; Commands 237 A / 237 B / 231 C (six are compatibility-only with no
  original UI path); V remains zero. [Inventory](PARITY_INVENTORY.md).
- B011's analytical stress diagnostic remains **failed** (199.99200439453125 vs
  200, absolute .001). D029, B006–B012 and the other D061 findings remain open.
- Patched Gmsh 4.13.0, CalculiX 2.22 and lib3mf 2.4.1 remain explicit/pinned.
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
| C6 | Original main menu, viewport defects, size limits | implemented; Mac ARM64 checks pass |
| C7 | Original tool strips and three-tab model tree | implemented; Mac ARM64 checks pass |
| C8 | Tree remainder, output links, model/mesh UI evidence | implemented; Mac ARM64 checks pass |
| C9 | Original form classes compiled whole (39), FrmMain form hosting | implemented; Mac ARM64 checks pass |
| C10 | Data grid forms compiled whole (DataGridView model, plot window) | implemented; Mac ARM64 checks pass |
| C11 | Child-window forms and dialogs compiled whole (TreeView, ZedGraph scaling) | implemented; Mac ARM64 checks pass |
| C12 | Code editor forms (FastColoredTextBox model), beam elements, Command base | implemented; Mac ARM64 checks pass |
| P1 | Desktop packages (macOS DMG, Linux tar.gz, Windows zip), rebuildable runtime profiles | Mac and Linux ARM64 packages self-checked; Windows not run |
| Fixes | Recorded numerical/original bugs and warnings | after parity |
| Release | Four targets, installers, signing, sources/notices | later |

## Next step

Maintainer's manual testing round ([MANUAL_TESTING.md](MANUAL_TESTING.md)): the macOS and Linux ARM64
packages, the Windows zip, a Linux x64 package built with `build_ui.py` in Podman on Windows, the original
net48 build in Visual Studio. Then FrmMain whole (ModelTree, side panels, Python console/stop, vtkControl
adapter, FrmSelectEntity handlers), the clean-organization pass (retire the C1–C5 toolkit dialogs/legacy
menus and old hosts), the D061 correctness/warning sweep, then the move to GitHub and an upstream PR.

## Environment

- .NET 10: Mac SDK 10.0.403; Linux verification SDK 10.0.402.
- VTK 9.5.2, PyQt6 6.10.0, Qt 6.10.2, Python.NET 3.1.0; explicit CPython 3.12.
- Runtime for the GUI verifier: a package (`python3 X/UI/verify-ui.py --output <dir>/verify.json --package
  X/Build/artifacts/ui-packages/PrePoMax-X.app --gui`); packages from `X/Build/build_ui.py`.
- Retained candidate (git-ignored): `X/Build/artifacts/ui-packages/` (macOS DMG + extracted app, Linux
  ARM64 tar.gz, Windows zip); native inputs for repackaging in `X/Build/artifacts/ui-inputs/`.
- Podman stopped after verification.
- Hosted CI hold D058: `[skip ci]` / `git push -o ci.skip`.

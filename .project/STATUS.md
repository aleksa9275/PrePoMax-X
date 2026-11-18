# Project status

_Replace this file as work progresses; history is in git and `.project/history/`._

## Where we are (18 November 2026)

- **M0 upstream 3.0.1 + vtkNative, GitHub home** (D063, D064). The repository now lives at
  github.com/aleksa9275/PrePoMax-X, a fork of github.com/PrePoMax/PrePoMax; our 146 commits sit on
  upstream's own history and upstream `1e2f83f2` (3.0.1 plus the native VTK port) is merged. Domain,
  Controller and UI build and verify on the new base; FrmMaterialOrientation compiles whole; 24 reviewed
  3.0.1 types joined the PMX allowlist. The viewport is still the interim Python VTK renderer (3.0.0 rules)
  until M1. [M0 report](reports/phase-m0-upstream-3.0.1.md).
- Before M0 (3.0.0 base): C6–C12 put the original main menu, tool strips, model tree and 70 original form
  classes on a headless WinForms model drawn by Qt; P1 packaged macOS/Linux/Windows test builds
  ([P1](reports/phase-p1-desktop-packages.md), [manual testing](MANUAL_TESTING.md) — those packages are
  3.0.0-based). Earlier phase reports: [C6](reports/phase-c6-main-window.md) …
  [C12](reports/phase-c12-editor-forms.md).
- **Full parity is not accepted.** Inventory: model/mesh 111 A / 108 C; commands 242 A / 231 C; forms
  73 / 71 compiled / 69 C; V zero. New 3.0.1 items are A only (no executed evidence yet).
  [Inventory](PARITY_INVENTORY.md). B011 stays **failed** (D061); D029, B006–B012 open.
- Plan to release (M1–M5) and manual items: [REMAINING_WORK.md](REMAINING_WORK.md).

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
| M0 | GitHub home, upstream 3.0.1 + vtkNative merged (`1e2f83f2`) | Mac ARM64 checks and UI verification pass |
| M1 | VTK 9.7, vtkNative on macOS/Linux, original vtkControl in Qt | next |
| M2–M5 | 3.0.1 features and FrmMain whole; CI; original comparison; fixes, installers, release | planned |
| Fixes | Recorded numerical/original bugs and warnings | after parity |
| Release | Four targets, installers, signing, sources/notices | later |

## Next step

M1: a pinned VTK 9.7 recipe and `vtkNative` built for macOS ARM64 and Linux (its Win32 window embedding,
interactor and widget input made portable), the original `vtkControl` compiled whole and embedded in a Qt
widget, then the geometry and results GUI probes on the original renderer. In parallel when the maintainer
agrees: GitHub Actions (M3).

## Environment

- Repository: `origin` github.com/aleksa9275/PrePoMax-X, `upstream` github.com/PrePoMax/PrePoMax, `gitlab`
  archive. Branch `research/native-feasibility`; `[skip ci]` until CI exists.
- This Mac: .NET SDK 11.0.100 only (runtime 11.0.0); net10.0 projects build with it and checks run with
  `DOTNET_ROLL_FORWARD=Major`. Packages ship self-contained .NET 10.0.14. Homebrew Python 3.15.
- UI runtime for verification: the P1 macOS app in the former GitLab working copy,
  `~/Documents/GitLab/pre-po-max-x/X/Build/artifacts/ui-packages/PrePoMax-X.app` (git-ignored there):
  `python3 X/UI/verify-ui.py --output <dir>/verify.json --package <that app> --gui`.
- VTK 9.5.2 (Python wheel, interim renderer), PyQt6 6.10.0 / Qt 6.10.2, Python.NET 3.1.0, CPython 3.12.14 in
  packages; patched Gmsh 4.13.0, CalculiX 2.22, lib3mf 2.4.1 pinned.

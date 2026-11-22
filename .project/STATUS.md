# Project status

_Replace this file as work progresses; history is in git and `.project/history/`._

## Where we are (22 November 2026)

- **M3-1: one runtime for the front end, macOS and Linux ARM64** (D065, D067). The original application (`X/App`) runs
  on Avalonia in its own .NET runtime with the original `vtkControl` in a native host (Cocoa, X11). Packages: a
  macOS `PrePoMax-X.app` (`X/App/package_mac.py`) and a Linux folder and tar.gz (`X/App/package_linux.py`), with no
  PyQt and no installed .NET. Both pass the app probe (16/16) and the probe areas (124 + 4 + 9 + 5). Both also pass
  four upstream Python tests including QuadWild, with the repository out of reach (macOS `sandbox-exec`, Linux a
  Podman session). Upstream's full suite: 61 of 81 on macOS and 60 of 81 on Linux on the same layout. The PyQt
  workbench, the Qt front end and the Headless host are retired. B015 (Retina right-click pick) is fixed.
  [Report](reports/phase-m3-1-front-end.md).
- **M2: the original application compiled whole** (`X/App`): the whole `PrePoMax` and `UserControls` assemblies —
  Controller, Commands, all 73 forms, FrmMain and the original `Program` — on the headless WinForms model. The
  original command line runs upstream's composite scripts through upstream's own runner (4 of 4 pass, including the
  `-r/-p` regeneration script), and FrmMain is shown in Qt with its original menus, tool strips, tree, view and
  forms (`X/UI/main_form.py`, GUI probe 9 checks). Part 1: 3.0.1 composites (FrmSection Layers, FrmMaterialOrientation),
  original painting replayed by Qt, missing property values, Netgen pin confirmed, QuadWild for macOS from the
  published fork. Closeout: the Netgen and Gmsh pins are the 3.0.1 sources; `-g No` runs draw FrmMain's view off screen; upstream's suite through the original command line passes 63 of 81 (the rest: Windows-only test content, the automation server, B013, B014); with B013 fixed (20 November) 64 of 81.
  [M2 report](reports/phase-m2-composites-painting.md).
- **M1 original vtkControl on vtkNative** (D063). The 3D view of X/UI is the original `vtkControl`, compiled
  whole, drawing through upstream's `vtkNative` on VTK 9.7.1 (pinned recipe `X/Build/Vtk`), embedded in a Qt
  widget on macOS (Cocoa) and Linux (X11); the 137 view members of the original FrmMain run unchanged in
  `OriginalViewHost`. The interim Python VTK renderer and its wheel are removed (one VTK per package). vtkNative needed two small portable changes
  (Win32 files guarded; X11 input to the parent and an event pump). All eight GUI probes pass on macOS ARM64
  and Linux ARM64 (Xvfb) with the M0 counts. [M1 report](reports/phase-m1-original-vtkcontrol.md).
- M0: GitHub home (fork of github.com/PrePoMax/PrePoMax), upstream `1e2f83f2` (3.0.1 + vtkNative) merged.
  [M0 report](reports/phase-m0-upstream-3.0.1.md).
- Before M0 (3.0.0 base): C6–C12 put the original main menu, tool strips, model tree and 70 original form
  classes on a headless WinForms model drawn by Qt; P1 packaged macOS/Linux/Windows test builds
  ([P1](reports/phase-p1-desktop-packages.md), [manual testing](MANUAL_TESTING.md) — those packages are
  3.0.0-based). Earlier phase reports: [C6](reports/phase-c6-main-window.md) …
  [C12](reports/phase-c12-editor-forms.md).
- **Full parity is not accepted.** Inventory: model/mesh 111 A / 110 C; commands 242 A / 232 C; forms
  73 / 73 compiled whole / 71 C; V zero. The 3.0.1 composite items have executed evidence (M2).
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
| M1 | VTK 9.7, vtkNative on macOS/Linux, original vtkControl in Qt | Mac and Linux ARM64 GUI probes pass on the original renderer |
| M2 | 3.0.1 features, FrmMain whole, Netgen/QuadWild from the published sources | done on macOS ARM64: every form compiled whole, composite scripts pass via the original command line, full upstream suite 63/81; Linux QuadWild open |
| M3-1a | Avalonia front end for X/App on macOS, M2's Qt front end matched and bettered (D065, D067) | done on macOS ARM64: app probe 16/16, probe areas 124+4+9+5 (bundle checked with the repository blocked), bounds comparison with 3.0.1 (Wine Mono evidence), the maintainer's real project, `PrePoMax-X.app` without PyQt (preview branch `release/macos-arm64-preview`) |
| M3-1b | The same on Linux via the local Podman machine (ARM64; Xvfb probes, VNC), then retire PyQt | done on Linux ARM64: app probe 16/16 and probe areas 124+4+9+5 in a Podman session without the repository, upstream suite 60/81 (macOS 61/81, same layout), QuadWild on Linux, Linux package without PyQt; PyQt workbench, Qt front end and Headless host retired; the maintainer's VNC check pending |
| M3–M5 | CI; original comparison; fixes, installers, release | planned |
| Fixes | Recorded numerical/original bugs and warnings | after parity |
| Release | Four targets, installers, signing, sources/notices | later |

## Next step

**M3** ([plan](REMAINING_WORK.md)): GitHub Actions for win-x64, linux-x64, linux-arm64 and osx-arm64:
- component builds (`X/Build/build_ui.py`), `X/Checks/check.py`, and the X/App packages with their probes (Linux in the
  `X/Build/Linux` images);
- the bounds comparison on Windows;
- the front end's first Windows run (Win32 native host).

Still open:
- the maintainer's check of the Linux app over VNC;
- B014, and the automation server on Unix;
- B013's round trip with the original 3.0.1, and the 15 forms that need a live controller for the bounds comparison;
- a VTK/QuadWild rebuild without build paths in the binaries; notarization (release);
- the macOS preview's refresh (B015, .NET pin);
- the retired-era `X/Desktop` preview (cleanup, M5).

## Environment

- Repository: `origin` github.com/aleksa9275/PrePoMax-X, `upstream` github.com/PrePoMax/PrePoMax, `gitlab`
  archive. Branch `research/native-feasibility`; `[skip ci]` until CI exists.
- This Mac: .NET SDK 11.0.100 only (runtime 11.0.0); net10.0 projects build with it and checks run with
  `DOTNET_ROLL_FORWARD=Major`. Packages ship self-contained .NET 10.0.14. Homebrew Python 3.15.
- Verification of the app: `python3 X/App/verify-app.py --output <dir>/app.json --launcher <package launcher> --scripts`
  (macOS: the `.app`'s `Contents/MacOS/PrePoMax-X`, best under `sandbox-exec` with the repository denied; Linux: start
  a session with `python3 X/Build/Linux/session.py start --package <PrePoMax-X folder> --work <dir>` and pass
  `<dir>/launch.sh`). Native components come from the P1 packages in the former GitLab working copy
  (`~/Documents/GitLab/pre-po-max-x/X/Build/artifacts/ui-packages`). Podman machine `prepomax-podman` (8 CPUs,
  15 GiB, 93 GB).
- VTK 9.7.1 (vtkNative), Avalonia 11.3.23, Python.NET 3.1.0, CPython 3.12.14 with numpy in packages; patched
  Gmsh 4.13.0, CalculiX 2.22, lib3mf 2.4.1 pinned. Local working app: `X/Build/artifacts/app-mac`
  (`X/App/local_app.py`). Native runtimes in `X/Build/artifacts`: CalculiX for macOS `solver-m2`, QuadWild
  `quadwild-mac-arm64` and `quadwild-linux-arm64`, vtkNative `vtk-mac-arm64` and `vtknative-linux-arm64-m3` (on M1's
  VTK in `vtk-linux-arm64/vtk`).

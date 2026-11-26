# Project status

_Replace this file as work progresses; history is in git and `.project/history/`._

## Where we are (26 November 2026)

- **M3-3: upstream `58b6a6a1`, macOS first** (in progress). Upstream rewrote its history after 3.0.2 (same files,
  new IDs: `6703b1cb` = `72a4cb06`); `2a5ca73a` records that (no file changes), `055b6b76` merges the 16 new commits
  without conflicts. `master` stays at `6703b1cb` (only a force push would make it mirror upstream again). Port: the
  view font (Windows registry, `windows.h`) split into `VtkNativeViewFont.Windows.cs` and a portable lookup in
  `X/Domain/vtkControl`, POSIX branch in `vtkNativeFonts.cpp` (macOS draws Arial from the system files); in-place
  editor rewrites (B023 open: not laid exactly over the view text); `PaintSuspended`, new sources, host contract,
  retired enum out of the allowlist. vtkNative rebuilt (`artifacts/vtk-mac-arm64-303`). macOS ARM64 local app:
  check.py six areas pass; `verify-app.py --scripts --legacy-pmx` 12/12 (forms 126/126). Published as macOS
  preview 7 (`release/macos-arm64-preview` `3b91189b`, source `f759bf90`, zip `ad46753a…`); the unpacked package under
  `sandbox-exec` (repository, Homebrew, .NET denied; fresh HOME): `verify-app.py --scripts --legacy-pmx` 12/12 (app probe
  16/16; forms 126/126, geometry 4/4, results 9/9, elements 5/5), `verify_solvers.py` on 4 and 8 threads as preview 6
  (only the recorded thin-plate mixed-precision case differs); ccx unchanged (`87f99211…`). The 3.0.1 release data
  (`materials.lib`, Models, the ODB script) came from preview 6's bundle, all 67 files checked against its `bundle.json`
  (the extracted release in /tmp had been cleaned). Not run: upstream's full suite. Next: Linux.
  F002 (Accelerate behind PARDISO) recorded as a deferred wishlist item.
- **M3-2: the solver as the Windows release builds it; the dark appearance** (D069, D070; macOS ARM64). The maintainer
  found PaStiX missing (B018); an audit of the release's `ccx_dynamic.exe` and native files found more gaps than
  PARDISO: external behaviours (B019, fixed), multithreaded SPOOLES (B020) and the Bidirectional Mesh Converter
  (B021, no public source). CalculiX is now built i8 with PaStiX4CalculiX (its CUDA-optional branch; OpenBLAS ILP64,
  hwloc, Scotch, PaRSEC static; `X/Build/Pastix`), multithreaded, and with external behaviours; PaStiX agrees with
  SPOOLES (`X/Build/Pastix/verify_solvers.py`), and its mixed-precision failure on thin shells matches the Windows
  binary (`PASTIX_MIXED_PRECISION=0` fixes both). Multithreaded SPOOLES raced on ARM64 (B022); fixed by a
  patch to SPOOLES's thread hand-over (`ThirdParty/Build/patches`), so SPOOLES is multithreaded on every target. `build_ui.py`: `pastix` stage and stage
  fingerprints. Dark appearance: a toolbar toggle switching the running app, the viewport in warm light greys, light
  unchanged. Published as macOS preview 6 (`release/macos-arm64-preview` `fef674d0`, source `5e612cb5`;
  preview 5 `38b23b8c` had serial SPOOLES).
  [Report](reports/phase-m3-2-solver-appearance.md).
- **M3-0: upstream 3.0.2** (D068). Upstream `master` `6703b1cb` (version 3.0.2, not released yet; 51 commits on
  `1e2f83f2`) is merged (`d5f3b24c`): storage without BinaryFormatter, HiGHS instead of lp_solve, new structured quad
  meshers, Change Element Order, body force and edge loads, Show Nodes. Files of older versions are read by upstream's
  `PrePoMax.LegacyImport` with an opt-in hook so every type goes through our allowlist (the X build fails closed); our
  own NRBF reader is retired. Real files open again (the 3.0.1 example models, the maintainer's 2.5.1 model).
  Original-area divergence 175 files (was 192). HiGHS 1.16.0 recipe, NetgenMesher re-pinned to the published
  `01e30ce0`, vtkNative rebuilt. All six non-app check areas pass; the macOS package from `c3a0cb88` passes under
  `sandbox-exec`: app probe 16/16, probe areas 124+4+9+5, older files open; upstream's suite (102 scripts): 77 of 108 (3.0.1: 61 of 81; B016 to triage). Housekeeping: X/Desktop and its
  packaging, the lp_solve recipe and the Qt-era plan items retired. Release basics: build paths mapped in
  `build_ui.py`, `bundle.json` `buildPaths` (61 files in this bundle, from components built before the maps).
  Published 23 November: macOS preview 4, the Linux preview (`release/linux-preview`: build kit for x86-64/ARM64
  and the ARM64 package, verified like the macOS one; x86-64 not built yet), tag `preview-3.0.2-1`, `master` at
  upstream 3.0.2; `release/linux-arm64-preview` removed. [Report](reports/phase-m3-0-upstream-3.0.2.md).
- **M3-1: one runtime for the front end, macOS and Linux ARM64** (D065, D067). The original application (`X/App`) runs
  on Avalonia in its own .NET runtime with the original `vtkControl` in a native host (Cocoa, X11). Packages: a
  macOS `PrePoMax-X.app` (`X/App/package_mac.py`) and a Linux folder and tar.gz (`X/App/package_linux.py`), with no
  PyQt and no installed .NET. Both pass the app probe (16/16) and the probe areas (124 + 4 + 9 + 5). Both also pass
  four upstream Python tests including QuadWild, with the repository out of reach (macOS `sandbox-exec`, Linux a
  Podman session). Upstream's full suite: 61 of 81 on macOS and 60 of 81 on Linux on the same layout. The PyQt
  workbench, the Qt front end and the Headless host are retired. B015 (Retina right-click pick) is fixed. The
  maintainer checked the Linux app over VNC on 22 November: everything looks good and works.
  Published 22 November as binary previews: `release/macos-arm64-preview` preview 3 (`2f8ca0ba`, source
  `6c776763`) and `release/linux-arm64-preview` (`baef284f`, source `bf56de9c`). The macOS branch was deleted by
  mistake during that publication (an empty refspec) and restored at the maintainer's commit `e7e56bba` first.
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
| M3-1b | The same on Linux via the local Podman machine (ARM64; Xvfb probes, VNC), then retire PyQt | done on Linux ARM64: app probe 16/16 and probe areas 124+4+9+5 in a Podman session without the repository, upstream suite 60/81 (macOS 61/81, same layout), QuadWild on Linux, Linux package without PyQt; PyQt workbench, Qt front end and Headless host retired; the maintainer's VNC check passed |
| M3-0 | Upstream 3.0.2 (`6703b1cb`): storage, HiGHS, Netgen, vtkNative; housekeeping; release basics (D068) | done: macOS and Linux ARM64 packages verified and published (suite 77/108, B016 open); Linux x86-64 kit untested |
| M3-2 | PaStiX, external behaviours, solver audit (D070); dark appearance (D069) | done on macOS ARM64 (see report); Linux after macOS is complete and local Forgejo CI exists |
| M3–M5 | CI; original comparison; fixes, installers, release | planned |
| Fixes | Recorded numerical/original bugs and warnings | after parity |
| Release | Four targets, installers, signing, sources/notices | later |

## Next step

0. Finish macOS (the maintainer's order, D070): B016 triage; B021 needs
   upstream. Then local Forgejo CI, then Linux (PaStiX stage and the appearance toggle untested there).
1. The maintainer asks upstream about collaboration (with the macOS 3.0.2 build); open questions for upstream: the
   NetgenMesher revision behind 3.0.2's `nglib.dll`, the legacy-reader hook and the GmshCommon additions.
2. Testers' feedback (enable issues on the fork); the first x86-64 run of `X/Build/Linux/build-package.sh`; B016
   triage (four possible port defects first).
3. **M3** ([plan](REMAINING_WORK.md)): GitHub Actions for win-x64, linux-x64, linux-arm64 and osx-arm64 — every native
   component from source through `build_ui.py` (no build paths), `check.py`, the packages and their probes; Windows
   first: the front end's Win32 native host, MSVC Gmsh/CalculiX, the bounds comparison.

Still open: B014 and the automation server on Unix; B013's round trip with the original; notarization (release).

## Environment

- Repository: `origin` github.com/aleksa9275/PrePoMax-X, `upstream` github.com/PrePoMax/PrePoMax, `gitlab`
  archive. Branch `research/native-feasibility`; `[skip ci]` until CI exists.
- This Mac: .NET SDK 11.0.100 only (runtime 11.0.0); net10.0 projects build with it and checks run with
  `DOTNET_ROLL_FORWARD=Major`. Packages ship self-contained .NET 10.0.14. Homebrew Python 3.15.
- Verification of the app: `python3 X/App/verify-app.py --output <dir>/app.json --launcher <package launcher> --scripts
  --legacy-pmx <folder of older .pmx files>`
  (macOS: the `.app`'s `Contents/MacOS/PrePoMax-X`, best under `sandbox-exec` with the repository denied; Linux: start
  a session with `python3 X/Build/Linux/session.py start --package <PrePoMax-X folder> --work <dir>` and pass
  `<dir>/launch.sh`). Native components come from the P1 packages in the former GitLab working copy
  (`~/Documents/GitLab/pre-po-max-x/X/Build/artifacts/ui-packages`). Podman machine `prepomax-podman` (8 CPUs,
  15 GiB, 93 GB).
- VTK 9.7.1 (vtkNative), Avalonia 11.3.23, Python.NET 3.1.0, CPython 3.12.14 with numpy in packages; patched
  Gmsh 4.13.0, CalculiX 2.22 (i8, PaStiX4CalculiX `1b15d792`), lib3mf 2.4.1, HiGHS 1.16.0, NetgenMesher `01e30ce0` pinned. Kept in `X/Build/artifacts`
  (cleanup 23 November) are only the macOS packaging inputs: VTK prefix `vtk-m1/vtk`, vtkNative `vtk-mac-arm64-302`,
  Netgen `netgen-mac-arm64-302` (with its OCCT install), HiGHS `highs-mac-arm64`, QuadWild `quadwild-mac-arm64`,
  CalculiX `solver-pastix` (i8, PaStiX, SPOOLES MT; `solver-m2` the previous SPOOLES-only build) with the PaStiX stack
  `pastix-dev`, the download cache, and `app-mac/app/settings.bin` and `app-mac/work` (the maintainer's
  settings and jobs; `X/App/local_app.py` rebuilds the local app around them). Linux packages come from
  `X/Build/Linux/build-package.sh` (Podman image `prepomax-x-package-build:1`; tests in `prepomax-x-run:24.04`).
  Old-file check: `Runner --open-legacy <files>` (X/Controller/Runner).

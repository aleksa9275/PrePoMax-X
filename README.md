# PrePoMax-X for macOS (Apple Silicon) — preview

This branch holds a **binary preview** of PrePoMax-X for macOS on Apple Silicon (ARM64). It contains no source
code. The source is the [`research/native-feasibility`](https://github.com/aleksa9275/PrePoMax-X/tree/research/native-feasibility)
branch of this repository at commit `f759bf90` (full: see `bundle.json` inside the app).

PrePoMax-X ports [PrePoMax](https://github.com/PrePoMax/PrePoMax), the open-source pre- and post-processor for the
CalculiX finite element solver, to macOS, Linux and Windows. This is **not** a rewrite: the original PrePoMax code
(3.0.2, upstream `master` at `58b6a6a1`, not released by upstream yet) runs unchanged on .NET 10. That covers its models, meshing, analysis set-up, result handling, forms and 3D view.
Only the Windows-specific layer is replaced: Windows Forms becomes a cross-platform control model drawn with Avalonia,
and the 3D view runs on upstream's VTK 9.7 native port.

> **Status: preview for testing.** It is not a release of PrePoMax and not endorsed by the PrePoMax authors. It is
> signed ad hoc and not notarized by Apple. It has been used on one Mac for real projects; expect rough edges.

A Linux preview of the same app (x86-64 and ARM64, built from source with one command) is on the branch
[`release/linux-preview`](https://github.com/aleksa9275/PrePoMax-X/tree/release/linux-preview).

### Changes in preview 7 (source `f759bf90`, 26 November)

- **Upstream's work after 3.0.2** (upstream `master` `58b6a6a1`, 16 commits):
  - **Element quality:** the standard quality metrics, the mesh coloured by element quality, and an editable colour bar
    title.
  - **Pressure loads:** pressure, hydrostatic pressure and imported pressure are now one Pressure load type.
  - **Structured meshing:** sweeps, mirrored parts and round holes are meshed better.
  - **Change Element Order:** midside nodes are projected or straightened for parts that are already parabolic.
  - **View text** is drawn with a chosen system font: Segoe UI where it is installed, otherwise Arial, which comes with
    macOS.
- **The in-place text editor** (annotations, legend limits, colour bar title) opens at the text's position but is not
  yet laid exactly over the view text as on Windows (B023 in the source repository). Editing works.

### Changes in preview 6 (source `5e612cb5`, 23 November)

- **SPOOLES is multithreaded on Apple Silicon**, as in the Windows build, using the number of processors set in
  Settings → CalculiX. Its multithreaded mode had a thread-safety bug that Intel CPUs hide: some threads handed
  their work to others without locking, so on Apple Silicon a thread could read a result before it was complete.
  Preview 5 therefore ran SPOOLES on one core. A small patch to SPOOLES fixes that bug; SPOOLES's arithmetic is
  unchanged. The patch is
  [`ThirdParty/Build/patches/spooles-2.2-mt-memory-order.patch`](https://github.com/aleksa9275/PrePoMax-X/blob/research/native-feasibility/ThirdParty/Build/patches/spooles-2.2-mt-memory-order.patch),
  and the build recipe that applies it is `ThirdParty/Build/calculix-cpu.py`; the bug and its evidence are
  `.project/bugs/B022-spooles-mt-arm64.md`.

### Changes in preview 5 (source `8aa5e082`, 23 November)

- **PaStiX works.** CalculiX is now built as CalculiX's own 8-byte-integer recipe with PaStiX (step → Solver type),
  multithreaded with the number of processors set in Settings → CalculiX. As in CalculiX on Windows, PaStiX's
  default mixed precision can give wrong results on thin shells (checked: the original Windows solver gives the same
  wrong result). Set the environment variable `PASTIX_MIXED_PRECISION` to `0` in Settings → CalculiX for those; its
  Active check box can now be switched on and off.
- **User materials from shared libraries** (CalculiX external behaviours, for example MFront), as in the Windows build.
- **Dark appearance**: the half-circle button at the right end of the top tool bar switches between light and dark
  while the app runs. The 3D view gets a warm light grey background in dark mode; your Graphics settings are kept.
- **SPOOLES runs on one core on Apple Silicon.** Its multithreaded mode, which the Windows build uses, gave wrong
  eigenvalues in some runs on Apple Silicon (a thread-safety problem in SPOOLES that Intel CPUs hide). For
  multithreaded solving use PaStiX. (Preview 4's notes called SPOOLES multithreaded; it was not.)

### Changes in preview 4 (source `c3a0cb88`, 23 November)

- **PrePoMax 3.0.2** (upstream `master` `6703b1cb`): the new project storage, HiGHS for element counts, structured
  quad meshing of submapped, lens, tube, ring and cap faces, Change Element Order, body force and edge loads, Show
  Nodes in the view, and upstream's fixes.
- **Projects from older versions** are read by upstream's new reader. Every type a file names is checked against a
  reviewed list. Checked with PrePoMax 3.0.1's example models and a 2.5.1 project. Projects saved by this preview
  are in the 3.0.2 format, which older PrePoMax versions cannot open.
- Netgen from the published NetgenMesher source `01e30ce0`. Upstream's own 3.0.2 Netgen carries one more change
  (pyramids at right-angle inside corners) that is not published yet.

### Changes in preview 3 (source `6c776763`, 22 November)

- **Right click on a part** opens the part's menu again. On Retina displays the click was picked at half its
  coordinates, so the view's menu opened instead, or a different part was picked.
- **.NET runtime 10.0.14**, the project's pinned version. Preview 2 had shipped 10.0.15 by mistake.
- The app is checked with four of upstream's Python tests, and with upstream's full suite (see below).

### Changes in preview 2 (source `e076f692`)

The first upload had no icons, no material library, no Python help and no example models. The app read those from
the source tree, which a download does not have. They are now in the bundle, and the checks run with the source
tree blocked. The app also has its own icon now. To update, replace the app; your settings are kept.

## What you get

`PrePoMax-X.app` (670 MB unpacked), with everything it needs inside. No .NET, Python or Homebrew installation is
required.

| Component | In the bundle |
|---|---|
| PrePoMax 3.0.2 (original code), Avalonia front end | yes |
| 3D view (VTK 9.7 through upstream's vtkNative) | yes |
| CalculiX 2.22 (8-byte integers) with **PaStiX** (multithreaded), **SPOOLES** (multithreaded), ARPACK, OpenBLAS; user material libraries | yes |
| Meshers: Netgen (NetGenMesher, OCCT 8.0.1), Gmsh 4.13 (patched), Mmg, QuadWild; HiGHS 1.16 for element counts | yes |
| CAD import (STEP, IGES, BREP) | yes |
| CPython 3.12 for PrePoMax's own Python features | yes (without PyQt) |
| Python API help and agent skill (Help → Python) | yes, generated from this source |
| Original icons, material library (`materials.lib`) and example models (`Models/`) of the PrePoMax 3.0.1 release | yes |
| Tools → Bidirectional Mesh Converter (a Windows-only third-party tool of the 3.0.1 release, no public source) | no |
| Intel MKL **PARDISO** solver | **no** (no macOS ARM64 build) |

### What has been checked

All checks below were run on macOS ARM64 with this exact bundle, unpacked from the zip, on a fresh data folder. The
app ran in a macOS sandbox that blocked the source repository, Homebrew and any installed .NET. Any file the bundle
lacked would have made a check fail.

- **Main window, 16/16 checks:** the original menus, tool strips and model tree with their icons; a model is
  imported and drawn in the 3D view, which can be turned with the mouse; a form opens from the menu with its property
  grid; Esc works; a right click opens the view's menu on empty space and the part's menu on a part, where clicked; a
  modal dialog opens and closes.
- **Forms, 126/126 checks:**
  - all 144 menu icons and the application icon load;
  - the material library opens with the 21 materials of `materials.lib`;
  - every menu matches the original in each view;
  - every create form opens through the original menu entry at the original size, with every control in place, and
    Cancel changes nothing;
  - a step, an amplitude (through the data grid) and the command history editor were created or used;
  - the CalculiX environment variables' Active check box switches on and off.
- **Geometry, 4/4 checks:** CAD import and Netgen meshing.
- **Results, 9/9 checks:**
  - an analysis is created and solved by CalculiX, with the original Monitor window;
  - the results open with their contours, legend and toolbar.
- **Elements, 5/5 checks:** a CalculiX deck with quadratic tetrahedra is imported and drawn.
- **Solvers** (the bundled CalculiX, run with Homebrew blocked): a solid cantilever (static, nonlinear geometry,
  eigenfrequencies) and a thin clamped plate, each solved with SPOOLES, PaStiX and PaStiX with
  `PASTIX_MIXED_PRECISION=0`, on 4 and on 8 threads. SPOOLES and PaStiX each used all the threads allowed and agreed
  (displacements within 3e-10, frequencies equal), except the thin plate with PaStiX's mixed precision, which is
  wrong exactly as with the original Windows solver; with `PASTIX_MIXED_PRECISION=0` it agrees. Multithreaded
  SPOOLES gave the serial SPOOLES's frequencies in 20 of 20 repeated runs on 4 and 8 threads (before the fix: wrong in
  10 of 10 runs on 8 threads).
- **Python API, 4 of upstream's test scripts** (`--script`, no GUI): `Test_Analysis` (builds, solves and reads a
  model through the API), `Test_Model_Materials_Sections`, `Test_Model_Meshing` and
  `Test_Model_Meshing_QuadWild_Transfinite` all passed.
- **Projects from older versions:** PrePoMax 3.0.1's example models (`Profile`, `Bearing_bracket`) and a 2.5.1
  project open with their parts, materials, steps and units.
- **Upstream's full 3.0.2 test suite** (`Run_Tests.py`, 108 runs; on preview 4's bundle just before the reader fixes,
  which no suite script touches; not rerun since): **77 pass** (preview 3: 61 of 81). The others need Windows (environment variables,
  PowerShell, named pipes) or the automation server, which does not run on macOS or Linux yet, or read PrePoMax's
  source code. About 20, mostly new 3.0.2 meshing tests, give meshes or loads that differ from upstream's Windows
  baselines; they are being investigated (B016 in the source repository).
- **Real projects:** a model saved by PrePoMax 2.5.1 opened, and a STEP assembly imported. Linear and nonlinear
  analyses ran with SPOOLES, and the results were reviewed (preview 4). Live window resizing was checked by hand.
- **Layout against the original PrePoMax 3.0.1:** the size and position of every control in every form was compared
  with the original. That original ran under CrossOver/Wine, so this is evidence only, not the Windows reference. All
  108 remaining differences come from Wine's own Windows Forms and fonts.

### Known limitations

- **PARDISO is not available.** New analyses default to SPOOLES. Steps saved by Windows PrePoMax with PARDISO stop
  with `the PARDISO library is not linked`: open the step and choose a different solver, such as PaStiX or Spooles.
- **PaStiX on thin shells:** set `PASTIX_MIXED_PRECISION` to `0` (see above), as on Windows.
- **Windows file paths:** models from Windows keep their Windows result-file paths until they are solved again.
- **Not notarized:** macOS blocks the app until you clear the download flag (see Install).
- **3.0.2 meshing and loads:** some of upstream's new 3.0.2 tests give different meshes or loads than on Windows (see
  above). Check new structured meshes, body forces and edge loads before relying on them.
- **Build paths:** some binaries (VTK, OCCT, QuadWild, CalculiX) contain the source paths of the build machine. They
  have no effect on how the app works.
- **Other platforms:** this is macOS ARM64. Linux has its own preview branch; Windows follows with CI.

## Install

1. Download all three parts and `SHA256SUMS` from this branch. The zip is split because GitHub limits files to
   100 MB.
2. In Terminal, in the download folder, rebuild the zip:

   ```bash
   cat PrePoMax-X-macos-arm64.zip.part-* > PrePoMax-X-macos-arm64.zip
   ```

3. Check it. The first line must print `OK`:

   ```bash
   shasum -a 256 -c SHA256SUMS
   ```

4. Unpack the zip, and move `PrePoMax-X.app` to `/Applications` or anywhere you like.
5. Clear the download flag, which macOS sets on files from the internet. Without this step the unsigned app is
   blocked:

   ```bash
   xattr -dr com.apple.quarantine /Applications/PrePoMax-X.app
   ```

6. Open `PrePoMax-X.app`. The first start takes a few seconds while it sets itself up.

## Where it keeps your data

PrePoMax keeps its settings next to its program files, as on Windows. So on first start, the app copies its
program folder to `~/Library/Application Support/PrePoMax-X` and runs from there.

| Folder or file | Contents |
|---|---|
| `app/` | the program copy, with `settings.bin` |
| `work/` | the default solver work directory (change it in Settings → Solver) |
| `profiles/` | the runtime profiles |

Updating the app keeps your settings. To uninstall, delete `PrePoMax-X.app` and that folder. An installed Windows
PrePoMax, under CrossOver for example, is never touched.

## Licenses and source

PrePoMax is © 2016–2026 Matej Borovinšek, licensed under GPL-3.0 (see [LICENSE](LICENSE)). The bundled components and
their licenses are listed in [NOTICE.md](NOTICE.md); their license texts are inside the app under
`Contents/Resources/Licenses`. The corresponding source is this repository at the commit above, together with
upstream PrePoMax.

Feedback and problems: open an issue in this repository. Include the macOS version, what you did, and the text
from `~/Library/Application Support/PrePoMax-X/app/trace.info` if there is one.

# PrePoMax-X for macOS (Apple Silicon) — preview

This branch holds a **binary preview** of PrePoMax-X for macOS on Apple Silicon (ARM64). It contains no source
code. The source is the [`research/native-feasibility`](https://github.com/aleksa9275/PrePoMax-X/tree/research/native-feasibility)
branch of this repository at commit `e076f692b2f68c49f51504dd88f21a1c3a12ee85`.

PrePoMax-X ports [PrePoMax](https://github.com/PrePoMax/PrePoMax), the open-source pre- and post-processor for the
CalculiX finite element solver, to macOS, Linux and Windows. This is **not** a rewrite: the original PrePoMax 3.0.1
code runs unchanged on .NET 10. That covers its models, meshing, analysis set-up, result handling, forms and 3D view.
Only the Windows-specific layer is replaced: Windows Forms becomes a cross-platform control model drawn with Avalonia,
and the 3D view runs on upstream's VTK 9.7 native port.

> **Status: preview for testing.** It is not a release of PrePoMax and not endorsed by the PrePoMax authors. It is
> signed ad hoc and not notarized by Apple. It has been used on one Mac for real projects; expect rough edges.

### Changes since the first upload (source `73c75b8a`)

The first upload had no icons, no material library, no Python help and no example models. The app read those from
the source tree, which a download does not have. They are now in the bundle, and the checks run with the source
tree blocked. The app also has its own icon now. To update, replace the app; your settings are kept.

## What you get

`PrePoMax-X.app` (664 MB unpacked), with everything it needs inside. No .NET, Python or Homebrew installation is
required.

| Component | In the bundle |
|---|---|
| PrePoMax 3.0.1 (original code), Avalonia front end | yes |
| 3D view (VTK 9.7 through upstream's vtkNative) | yes |
| CalculiX 2.22 with **SPOOLES** (multi-threaded), ARPACK, OpenBLAS | yes |
| Meshers: Netgen (NetGenMesher, OCCT 8.0.1), Gmsh 4.13 (patched), Mmg, QuadWild | yes |
| CAD import (STEP, IGES, BREP) | yes |
| CPython 3.12 for PrePoMax's own Python features | yes (without PyQt) |
| Python API help and agent skill (Help → Python) | yes, generated from this source |
| Original icons, material library (`materials.lib`) and example models (`Models/`) of PrePoMax 3.0.1 | yes |
| Windows-only BidirectionalMeshConverter.exe of the 3.0.1 release | no |
| Intel MKL **PARDISO** solver | **no** (no macOS ARM64 build) |

### What has been checked

All checks below were run on macOS ARM64 with this exact bundle, unpacked from the zip, on a fresh data folder. The
app ran in a macOS sandbox that blocked the source repository, Homebrew and any installed .NET. Any file the bundle
lacked would have made a check fail.

- **Main window, 16/16 checks:** the original icons are drawn in the menus, tool strips and model tree; menus, tool strips and the model tree; a model is imported and drawn in the 3D view,
  which can be turned with the mouse; a form opens from the menu with its property grid; Esc works; the context menu
  opens; a modal dialog opens and closes.
- **Forms, 124/124 checks:**
  - all 144 menu icons and the application icon load;
  - the material library opens with the 21 materials of `materials.lib`;
  - every menu matches the original in each view;
  - every create form opens through the original menu entry at the original size, with every control in place, and
    Cancel changes nothing;
  - a step, an amplitude (through the data grid) and the command history editor were created or used.
- **Geometry, 4/4 checks:** CAD import and Netgen meshing.
- **Results, 9/9 checks:**
  - an analysis is created and solved by CalculiX, with the original Monitor window;
  - the results open with their contours, legend and toolbar.
- **Elements, 5/5 checks:** a CalculiX deck with quadratic tetrahedra is imported and drawn.
- **Python API, 3 of upstream's test scripts** (`--script`, no GUI): `Test_Analysis` (builds, solves and reads a
  model through the API), `Test_Model_Materials_Sections` and `Test_Model_Meshing` all passed.
- **Real projects:** a model saved by PrePoMax 2.5.1 opened, and a STEP assembly imported. Linear and nonlinear
  analyses ran with SPOOLES on 4 cores, and the results were reviewed.
- **Layout against the original PrePoMax 3.0.1:** the size and position of every control in every form was compared
  with the original. That original ran under CrossOver/Wine, so this is evidence only, not the Windows reference. All
  108 remaining differences come from Wine's own Windows Forms and fonts.

### Known limitations

- **PARDISO is not available.** New analyses default to SPOOLES. Steps saved by Windows PrePoMax with PARDISO stop
  with `the PARDISO library is not linked`: open the step and choose a different solver, such as Spooles.
- **Windows file paths:** models from Windows keep their Windows result-file paths until they are solved again.
- **Not notarized:** macOS blocks the app until you clear the download flag (see Install).
- **Resizing:** the 3D view while the window is being resized has not been checked by a person yet.
- **Build paths:** VTK and QuadWild binaries contain the source paths of the build machine. They have no effect on
  how the app works.
- **Other platforms:** this is macOS ARM64 only. Linux comes next; Windows follows with CI.

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

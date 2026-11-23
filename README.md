# PrePoMax-X for Linux — preview

This branch is the **Linux preview** of PrePoMax-X, for both 64-bit PC (x86-64) and 64-bit ARM (aarch64). You build
the package yourself, from source, with one command; a ready-made ARM64 package is here as well. The source is the
[`research/native-feasibility`](https://github.com/aleksa9275/PrePoMax-X/tree/research/native-feasibility) branch
of this repository, tag `preview-3.0.2-1` (commit `a0eebd50`). A macOS (Apple Silicon) preview of the same app is on
[`release/macos-arm64-preview`](https://github.com/aleksa9275/PrePoMax-X/tree/release/macos-arm64-preview).

PrePoMax-X ports [PrePoMax](https://github.com/PrePoMax/PrePoMax), the open-source pre- and post-processor for the
CalculiX finite element solver, to macOS, Linux and Windows. This is **not** a rewrite: the original PrePoMax code
(3.0.2, upstream `master` at `6703b1cb`, not released by upstream yet) runs unchanged on .NET 10. That covers its
models, meshing, analysis set-up, result handling, forms and 3D view. Only the Windows-specific layer is replaced:
Windows Forms becomes a cross-platform control model drawn with Avalonia (X11), and the 3D view runs on upstream's
VTK 9.7 native port.

> **Status: preview for testing.** It is not a release of PrePoMax and not endorsed by the PrePoMax authors. It has
> been tested in an Ubuntu 24.04 desktop in a container (see below), not yet on a physical Linux machine. The
> **x86-64 build has not been tested at all yet**: if you build it, please report how it went.

## Two ways to get it

### A. Build it yourself (x86-64 or ARM64)

You need: Linux on x86-64 or ARM64, **Podman or Docker**, git, about **30 GB** of free disk and **16 GB** of memory.
The build takes a few hours (VTK and OpenCASCADE take most of it) and needs the internet: every component is
downloaded from its official source and checked against a pinned SHA-256 checksum.

```bash
git clone --branch preview-3.0.2-1 --depth 1 https://github.com/aleksa9275/PrePoMax-X.git
```

```bash
PrePoMax-X/X/Build/Linux/build-package.sh ~/prepomax-x-build
```

The script picks the architecture of your machine, builds a build container (Ubuntu 24.04 with the compilers, CMake
and the .NET 10 SDK), then builds everything in it: CalculiX 2.22 with SPOOLES and ARPACK, Gmsh 4.13 (patched), the
PrePoMax Netgen mesher with OpenCASCADE 8.0.1, Mmg, QuadWild, HiGHS, VTK 9.7.1 with upstream's vtkNative, lib3mf,
CPython 3.12 and the application. It also downloads the PrePoMax 3.0.1 release from prepomax.fs.um.si for its material
library and example models. Nothing is installed on your system outside the container and the folder you give.

If the build stops, run the same command again: finished steps are kept and reused. Use `ENGINE=docker` to choose
Docker when both are installed, and `JOBS=4` to use fewer CPU cores.

The result is `~/prepomax-x-build/out/PrePoMax-X` (ready to run) and `PrePoMax-X-linux-<arch>.tar.gz` beside it.
From `~/prepomax-x-build/out`, continue with **Run** below.

### B. The ready-made ARM64 package

`PrePoMax-X-linux-arm64.tar.gz` on this branch is the output of the command above on ARM64, from the same tag. It is
split in parts because GitHub limits files to 100 MB:

```bash
cat PrePoMax-X-linux-arm64.tar.gz.part-* > PrePoMax-X-linux-arm64.tar.gz
```

```bash
sha256sum -c SHA256SUMS
```

```bash
tar xzf PrePoMax-X-linux-arm64.tar.gz
```

## Requirements to run

- **glibc 2.38 and the libstdc++ of GCC 13 or newer**: Ubuntu 24.04, Debian 13, Fedora 39 or newer.
- **An X11 desktop.** On Wayland the app runs through XWayland, which most desktops provide; that has not been
  tested yet.
- **System libraries** that a desktop normally has: X11, OpenGL (Mesa or a GPU driver), fontconfig and ICU. On a
  minimal Ubuntu 24.04:

  ```bash
  sudo apt install libgl1 libglx-mesa0 libgl1-mesa-dri libx11-6 libxt6t64 libxcursor1 libxrandr2 libxi6 libice6 libsm6 libfontconfig1 libicu74 fonts-liberation
  ```

- **Liberation Sans** (`fonts-liberation`) is recommended: the forms are laid out for Windows' Segoe UI, which it
  matches closely. With a wider font, such as DejaVu Sans, some labels are cut off.

## Run

```bash
./PrePoMax-X/PrePoMax-X
```

The first start takes a few seconds while it sets itself up. A model can be given directly:
`./PrePoMax-X/PrePoMax-X model.pmx`. To add PrePoMax-X to your desktop menu (again if you move the folder):

```bash
./PrePoMax-X/share/install-desktop-entry.sh
```

## What you get

| Component | In the package |
|---|---|
| PrePoMax 3.0.2 (original code), Avalonia front end on X11 | yes |
| 3D view (VTK 9.7 through upstream's vtkNative, OpenGL) | yes |
| CalculiX 2.22 with **SPOOLES**, ARPACK, OpenBLAS | yes |
| Meshers: Netgen (NetGenMesher, OCCT 8.0.1), Gmsh 4.13 (patched), Mmg, QuadWild; HiGHS 1.16 for element counts | yes |
| CAD import (STEP, IGES, BREP) | yes |
| CPython 3.12 with numpy for PrePoMax's own Python features | yes |
| Python API help and agent skill (Help → Python) | yes |
| Material library and example models of the PrePoMax 3.0.1 release | yes |
| Intel MKL **PARDISO** solver | **no** (Windows only) |

Projects from older PrePoMax versions open (upstream's reader; every type a file names is checked against a reviewed
list). Projects saved here are in the 3.0.2 format, which older PrePoMax versions cannot open.

## What has been checked

The ARM64 package was built from scratch with the command above (in Podman), unpacked from its tar.gz and run in a
plain Ubuntu 24.04 desktop: a container with no .NET and no development packages, Xvfb, Mesa software OpenGL and
Openbox. The source repository was not mounted, so any file the package lacked would have made a check fail.

- **Main window, 16/16 checks:** the original menus, tool strips and model tree with their icons; a model is
  imported and drawn in the 3D view, which can be turned with the mouse; a form opens from the menu with its property
  grid; Esc works; a right click opens the view's menu on empty space and the part's menu on a part; a modal dialog
  opens and closes.
- **Forms, 124/124 checks:** all 144 menu icons and the application icon load; the material library opens with its 21
  materials; every menu matches the original in each view; every create form opens through the original menu entry
  at the original size with every control in place, and Cancel changes nothing; a step, an amplitude and the command
  history editor were created or used.
- **Geometry, 4/4:** CAD import and Netgen meshing. **Results, 9/9:** an analysis is created and solved by CalculiX
  with the original Monitor window, and its results open with contours, legend and toolbar. **Elements, 5/5:** a
  CalculiX deck with quadratic tetrahedra is imported and drawn.
- **Python API, 4 of upstream's test scripts** (`--script`, no GUI): `Test_Analysis`, `Test_Model_Materials_Sections`,
  `Test_Model_Meshing` and `Test_Model_Meshing_QuadWild_Transfinite` passed.
- **Projects from older versions:** PrePoMax 3.0.1's example models and a 2.5.1 project open with their parts,
  materials, steps and units.

The same source passes these checks as a macOS app as well, and upstream's full 3.0.2 test suite there (77 of 108;
the rest need Windows or the automation server, read PrePoMax's source code, or give meshes and loads that differ
from upstream's Windows baselines and are being investigated).

## Known limitations

- **x86-64 is untested.** The same recipes build both architectures, but only ARM64 has been built and run.
- **PARDISO is not available.** New analyses default to SPOOLES. Steps saved by Windows PrePoMax with PARDISO stop
  with `the PARDISO library is not linked`: open the step and choose another solver, such as Spooles.
- **3.0.2 meshing and loads:** some of upstream's new 3.0.2 tests give different meshes or loads than on Windows.
  Check new structured meshes, body forces and edge loads before relying on them.
- **Windows file paths:** models from Windows keep their Windows result-file paths until they are solved again.
- **Not yet tried on real hardware:** a physical desktop with a GPU driver, Wayland/XWayland and HiDPI scaling.

## Where it keeps your data

On first start, the app copies its program folder to `~/.local/share/PrePoMax-X` (or `$XDG_DATA_HOME/PrePoMax-X`)
and runs from there, because PrePoMax keeps its settings next to its program files, as on Windows.

| Folder | Contents |
|---|---|
| `app/` | the program copy, with `settings.bin` |
| `work/` | the default solver work directory (change it in Settings → Solver) |
| `profiles/` | the runtime profiles |

To update, unpack or build the new version and start it; your settings are kept. To uninstall, delete the
`PrePoMax-X` folder, `~/.local/share/PrePoMax-X` and, if you added it, `~/.local/share/applications/PrePoMax-X.desktop`.

## Licenses and source

PrePoMax is © 2016–2026 Matej Borovinšek, licensed under GPL-3.0 (see [LICENSE](LICENSE)). The bundled components and
their licenses are listed in [NOTICE.md](NOTICE.md); their license texts are inside the package under `Licenses/`.
The corresponding source is this repository at the tag above, with the pinned third-party sources it downloads.

Feedback and problems: open an issue in this repository. Include the distribution and version, the architecture
(`uname -m`), whether you built it yourself, what you did, and the terminal output of `./PrePoMax-X/PrePoMax-X`. For
build problems, attach the end of the build output.

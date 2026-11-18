# Manual testing — PrePoMax-X desktop

State of 11 November 2026 (after C12 and the first desktop packages). This is what you install, what to
look at, and how to report. Automated evidence is in the phase reports; this round is yours.

> 18 November: the target is now 3.0.1 with upstream's native VTK port (D063). These packages are the
> 3.0.0-based P1 builds; findings still carry over. The next packages (after M2) are 3.0.1-based with
> the original viewport; they live in the former GitLab working copy's `X/Build/artifacts/ui-packages/`.

## Packages

Local test builds (not signed for distribution, no installer), retained in
`X/Build/artifacts/ui-packages/` (git-ignored):

| Target | File | Built and checked |
|---|---|---|
| macOS ARM64 | `PrePoMax-X-osx-arm64.dmg` (also extracted as `PrePoMax-X.app`) | Mac; results + geometry self-checks from the mounted DMG, full repository UI verification with its runtime |
| Linux ARM64 | `PrePoMax-X-linux-arm64.tar.gz` | local Podman (Ubuntu 24.04 builder); results + geometry self-checks on a clean Ubuntu 24.04 under Xvfb (software OpenGL) |
| Windows x64 | `PrePoMax-X-win-x64.zip` | cross-packaged on the Mac; **never run** |
| Linux x64 | — | build it yourself (below) |

Each package's `package.json` lists versions, fingerprints and `missing` components:

- all macOS/Linux: **QuadWild** (quad remeshing) — the Windows binaries come from a modified fork whose
  source is not in the repository (ask Matej for it).
- Windows: **Gmsh** (the MSVC build of the pinned patched Gmsh 4.13.0 is pending; Netgen meshing works) and
  **CalculiX** (the Windows native solver build is pending; set a `ccx.exe` in Settings → Solver, e.g. from
  an original PrePoMax installation, to run analyses).

### Install and start

- **macOS**: open the DMG, drag `PrePoMax-X.app` to Applications (or run it from the image). Unsigned:
  the first start needs right-click → Open.
- **Linux**: Ubuntu 24.04 or newer (glibc ≥ 2.39). Install the display libraries once:
  `sudo apt-get install libgl1 libegl1 libgl1-mesa-dri libxrender1 libdbus-1-3 libfontconfig1 fonts-dejavu-core libxkbcommon-x11-0 libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxcb-xinput0 libsm6 libglib2.0-0t64 libicu74 libssl3t64 libgssapi-krb5-2 zlib1g libgomp1`,
  extract the archive and run `./PrePoMax-X/PrePoMax-X`.
- **Windows**: extract the zip (keep the folder together) and run `PrePoMax-X.cmd`.
- User data (runtime profiles, working folder): macOS `~/Library/Application Support/PrePoMax-X`, Linux
  `~/.local/share/PrePoMax-X`, Windows `%LOCALAPPDATA%\PrePoMax-X`. Uninstall = delete the application and
  that folder. Installed original PrePoMax applications and their settings are never touched.
- Start from a terminal to keep the log (the output panel shows the same engineering messages).

### Build Linux x64 (Podman on Windows, D059)

In an Ubuntu 24.04 x64 container with the repository mounted (needs network for the pinned downloads):

    apt-get install -y python3 gcc g++ gfortran cmake make pkg-config libopenblas-dev patchelf binutils file zlib1g-dev patch
    # plus the .NET 10 SDK (mcr.microsoft.com/dotnet/sdk:10.0-noble is a convenient base image)
    python3 X/Build/build_ui.py --target linux-x64 --workspace /work/ws --jobs 8

The result is `/work/ws/package/dist/PrePoMax-X-linux-x64.tar.gz`. The two OCCT builds take the longest.

## Self-checks

Every package carries the GUI probes; each writes a JSON report and exits:

    PrePoMax-X --results-probe <dir>     # import a deck, real CalculiX solve, results/animation/section views
    PrePoMax-X --geometry-probe <dir>    # CAD import, Netgen/Gmsh meshing, Delete Faces, lp_solve shell mesh

(Windows: `PrePoMax-X.cmd --results-probe <dir>`; the results probe needs a configured solver.)

## What to look at

1. **Start and window**: menus, tool strips and the three-tab model tree (the original layout); theme,
   fonts, HiDPI, window resizing; the viewport (rotate/pan/zoom, selection, picking).
2. **Projects**: open your own PMX files from the original 3.0.0 (keep them outside Git), save, reopen in
   the original; history regeneration.
3. **Geometry and meshing**: STEP/BREP/STL import, mesh setup items (Netgen, Gmsh, Mmg; QuadWild missing),
   meshing, mesh tools.
4. **Model**: the original property forms (materials, sections, steps, loads, BCs, contact, amplitudes,
   distributions …), the CalculiX keyword editor, Edit → History.
5. **Analysis and results**: run, monitor, results views (contours, deformation, animation, section,
   transformations), history output, export.
6. **Feel**: mouse/keyboard, shortcuts, copy/paste in grids and editors, focus, dialogs on top, speed.

## Known gaps (not yet the original)

- FrmMain itself is not compiled whole yet (next milestone after this round): the main window is a Qt
  shell with the original menus/tool strips/tree and the original FrmMain members; the Python side panel,
  XY plot and advisor are toolkit panels; Python stop window and the original entity-selection dialog
  (FrmSelectEntity) come with FrmMain.
- Renderer gaps: owner-drawn paint (tab backgrounds, collapsible group +/- glyph), grid row drag-and-drop,
  plot zoom/pan and plot context menu, autocomplete popup look, editor folding/word wrap, light theme/HiDPI.
- B011 analytical stress diagnostic remains failed (D061); recorded bugs are fixed after parity.

## Reporting

For each finding: platform and package (`package.json` → `source`), steps, what you expected (the
original's behaviour), what happened, a screenshot or the terminal log. Original-app comparisons are the
most valuable (CrossOver or Windows side by side).

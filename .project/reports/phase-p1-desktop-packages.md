# Phase P1 — desktop packages and rebuildable runtime profiles

Date: 11 November 2026. REMAINING_WORK §2 (shippable), maintainer decision of 11 November: package first,
then FrmMain whole. Scope: local test builds for manual testing, not release packages.

## What exists

- `X/Build/build_ui.py --target <rid> --workspace <dir>`: every native input from its pinned recipe
  (resumable stages), then the package:
  - `X/Build/LpSolve/` — lp_solve 5.5.2.11 (sourceforge archive, SHA-256 locked), the original Windows
    DLL's 26 sources and defines; `lpsolve55.dll.dylib`/`.so`, the first name .NET probes for the original
    `DllImport("lpsolve55.dll")`, next to GmshCaller and the application assemblies. All 17 entry points
    the original C# calls are exported.
  - `X/Build/Mmg/` — mmgs 5.5.2 and mmg3d 5.7.0 (the shipped Windows releases; banners match), no
    VTK/Elas/Scotch as the Windows build.
  - lib3mf 2.4.1 (official macOS/Windows libraries, Linux source build), `Gmsh/`, `NativeCad/` and the
    CalculiX solver (existing recipes).
- `X/Build/package_ui.py`: self-contained .NET 10.0.14 host and GmshCaller, CPython 3.12.14
  (python-build-standalone 20260929, `python-runtime-lock.json`, same patch release as the verified
  profile) with the hash-pinned UI wheels (`X/UI/requirements/<rid>.txt`: VTK 9.5.2, PyQt6 6.10.0 with Qt
  6.10.2, sip 13.13.0, NumPy 2.3.5, from PyPI digests), native tools, the solver relocated by the existing
  platform adapters, X/UI with the original resources it reads, the GUI probes as self-checks,
  `package.json` (versions, fingerprints, **missing** components) and notices. Formats: macOS app/DMG
  (ad-hoc signed), Linux tar.gz, Windows zip.
- `launch.py` writes the absolute, fingerprinted runtime profiles to the user data folder and starts the
  host; `launch.py --profiles DIR` writes them for `X/UI/verify-ui.py`. Repository verification no longer
  depends on hand-made `/private/tmp` profiles.
- Guide for the maintainer's round: [MANUAL_TESTING.md](../MANUAL_TESTING.md).

## Found

- **lp_solve was missing on macOS/Linux** (C12): fixed by the recipe; the default Meshing Parameters mesh
  of a CAD shell (GmshCaller interval assignment) now meshes (180 parabolic quadrilaterals on the Mac).
- **QuadWild has no macOS/Linux build**: the shipped Windows binaries come from a modified QuadWild-BiMDF
  0.0.2 fork whose source is not in the repository (for the upstream questions).
- **Windows**: the pinned patched Gmsh 4.13.0 has no MSVC build yet (the X Gmsh loader accepts only that
  revision), and the Windows CalculiX build is pending; both are listed as missing in the zip.
- The CPython Linux archive holds terminfo names that differ only by case; Linux packages are staged on a
  case-sensitive file system (inside the container).

## Evidence (11 November 2026)

- macOS ARM64 DMG (413 MB; app 1.1 GB): mounted read-only, the app's geometry probe passes (43 checks: CAD
  import, Netgen and Gmsh meshing, Delete Faces, beam evidence, lp_solve shell mesh); an earlier build of
  the same package passed the results probe (58 checks, real CalculiX 2.22 solve with the relocated solver).
- Linux ARM64 tar.gz, built in the local Podman machine (task0050 builder image, the solver's fingerprinted
  OpenBLAS), extracted on a clean Ubuntu 24.04 with only display libraries: results probe 58 checks,
  geometry probe 43 checks (incl. the lp_solve shell mesh), under Xvfb with software OpenGL.
- Windows x64 zip: cross-packaged on the Mac (vendored Netgen, Mmg, QuadWild, lp_solve; official lib3mf;
  win_amd64 wheels); layout inspected; **not executed**.
- Repository verification with the retained macOS package's runtime (`launch.py --profiles`, now
  `verify-ui.py --package`), `--gui`, unattended: generators current, services, GUI probes C1 18, authoring
  21, geometry 43, results 58, application 39, elements 27, forms 419, menu 122; nothing pending. B011
  "analytic double stress" remains **failed** (D061). `python3 X/Checks/check.py`: 7 areas pass.
- Not run: Linux x64 (Podman on Windows), Windows, physical Linux desktop, original-app comparison.

## Open

- Linux x64 package (maintainer, Podman on Windows); Windows execution; Gmsh MSVC and Windows CalculiX.
- A full from-scratch `build_ui.py` run per target (the packages here reuse the earlier Netgen/Gmsh/solver
  builds made with the same recipes; lp_solve, Mmg and Linux Netgen were built now).
- Distribution: complete third-party notice, signing/notarization, installers (release step).

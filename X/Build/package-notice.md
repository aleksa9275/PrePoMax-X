# PrePoMax-X (local test build)

PrePoMax-X runs the original PrePoMax 3.0.0 engineering code, Controller and forms on .NET 10 with a Qt/VTK
presentation, on macOS, Linux and Windows. This is a **local test build for manual testing**: it is not
signed for distribution or notarized, and it is not a release.

- PrePoMax: Copyright (C) 2016-2026 Matej Borovinšek, GPL-3.0 (`Licenses/PrePoMax-LICENSE`).
- Bundled components: CalculiX 2.22 (GPL-2.0) with SPOOLES 2.2, ARPACK-ng 3.9.1 and OpenBLAS; patched Gmsh 4.13.0
  (GPL-2.0+) with OCCT 7.7.0; Netgen with OCCT 8.0.1 (LGPL-2.1); Mmg 5.5.2/5.7.0 (LGPL-3.0); lp_solve 5.5.2.11
  (LGPL-2.1); lib3mf 2.4.1 (BSD-2); CPython 3.12.14 (PSF-2.0); PyQt6 6.10 (GPL-3.0) with Qt 6.10 (LGPL-3.0);
  VTK 9.5.2 (BSD-3); NumPy 2.3.5 (BSD-3); .NET 10.0.14 (MIT). License texts included: `Licenses/` (PrePoMax,
  Gmsh, lp_solve, Mmg, Netgen, QuadWild), `tools/Netgen/licenses`, and the CPython and wheel license files under
  `python/`. A complete third-party notice file for distribution is still to be prepared (release step).
- Exact component versions, fingerprints and what is **not** included are listed in `package.json`
  (`missing`). Corresponding sources: the PrePoMax-X repository at the recorded `source` commit and the source
  locks it names (`ThirdParty/Sources/source-lock.json`, `X/Build/*/source-lock.json`,
  `X/Build/python-runtime-lock.json`, `X/Build/python-requirements/`).

Start: macOS `PrePoMax-X.app`; Linux `./PrePoMax-X`; Windows `PrePoMax-X.cmd`. User data (runtime profiles,
working folder) goes to the PrePoMax-X data folder (macOS `~/Library/Application Support/PrePoMax-X`, Linux
`~/.local/share/PrePoMax-X`, Windows `%LOCALAPPDATA%\PrePoMax-X`). To uninstall, delete the application and
that folder. Installed original PrePoMax applications and their settings are never touched.

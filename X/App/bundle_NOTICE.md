# PrePoMax-X for macOS ARM64 (preview)

PrePoMax-X runs the original PrePoMax 3.0.2 (upstream `master`, see `bundle.json`) — its engineering code, Controller, forms and 3D view — natively on
macOS (Apple Silicon), with an Avalonia front end in place of Windows Forms. This is a **preview build**: signed
ad hoc, not notarized, not a release. See `bundle.json` for the exact source commit and components.

- PrePoMax: Copyright (C) 2016-2026 Matej Borovinšek, GPL-3.0 (`Licenses/PrePoMax-LICENSE`).
- From the PrePoMax 3.0.1 release (GPL-3.0; 3.0.2 is not released yet), checked by SHA-256 in `bundle.json`: the material library
  (`materials.lib`), the example models (`Models/`) and the Abaqus ODB conversion script. The Python API help
  (`Help/Python`) is generated from this source as upstream builds it (Markdig 1.3.2, build time only).
- Bundled components and licenses:
  - CalculiX 2.22 (GPL-2.0), built with 8-byte integers, with SPOOLES 2.2 (public domain), ARPACK-ng 3.9.1 (BSD-3)
    and, linked statically, PaStiX4CalculiX (CeCILL-C), Scotch 6.0.8 (CeCILL-C), PaRSEC (BSD-3), hwloc 2.1.0 (BSD-3)
    and OpenBLAS 0.3.34 (BSD-3) (license texts in `Licenses/solver`); the GCC runtime libraries libstdc++,
    libgfortran, libgomp, libquadmath, libgcc_s and libatomic (GPL-3.0 with the GCC Runtime Library Exception) beside
    it or linked in (`solver/relocation.json`).
  - Gmsh 4.13.0, patched (GPL-2.0-or-later with exceptions) with OpenCASCADE (LGPL-2.1 with the Open CASCADE
    exception); NetGenMesher (GPL-3.0) with Netgen 5.3.1 (LGPL-2.1) and OpenCASCADE 8.0.1, from the published NetgenMesher
    source (`bundle.json` names the revision); Mmg 5.5.2/5.7.0
    (LGPL-3.0); QuadWild-BiMDF 0.0.2, modified (GPL-3.0); HiGHS 1.16.0 (MIT, `Licenses/highs`); lib3mf 2.4.1 (BSD-2).
  - VTK 9.7 (BSD-3, `Licenses/VTK-Copyright.txt`) through upstream PrePoMax's vtkNative (GPL-3.0).
  - .NET @DOTNET@ runtime (MIT, `Licenses/dotnet`), Avalonia 11.3.23 (MIT, `Licenses/avalonia`), SkiaSharp 2.88.9
    and HarfBuzzSharp 8.3.1.1 (MIT, `Licenses/skiasharp`, `Licenses/harfbuzzsharp`).
  - CPython 3.12.14 (PSF-2.0) and NumPy 2.3.5 (BSD-3), license files under `python/`.
- Corresponding source: the PrePoMax-X repository (github.com/aleksa9275/PrePoMax-X, branch
  `research/native-feasibility`) at the commit in `bundle.json`, its source locks (`ThirdParty/Sources`,
  `X/Build/*/source-lock.json`), and upstream PrePoMax (github.com/PrePoMax/PrePoMax).
- Not included: the Intel MKL PARDISO solver (no macOS ARM64 build; use PaStiX or SPOOLES) and the release's
  Windows-only BidirectionalMeshConverter.exe (a third-party tool without public source).

User data (the application copy with its settings, runtime profiles, the solver work folder) goes to
`~/Library/Application Support/PrePoMax-X`. To uninstall, delete the application and that folder. An installed
original PrePoMax and its settings are never touched.

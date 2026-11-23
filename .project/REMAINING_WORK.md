# Remaining work to full completion (D060)

Updated 23 November 2026 after M3-2 (PaStiX, the solver audit, the dark appearance). Replace, don't append. Evidence for each item is in the
phase reports, `.project/bugs/` and the [backlog](reports/deferred-correctness-improvements.md). History of this plan
(the Qt-era items C1–C12, P1) is in git and `.project/history/`.

## Plan to release (maintainer, 17 November 2026; M3-0 added 23 November, D068)

| | Milestone | Done when | State |
|---|---|---|---|
| M0 | GitHub home, upstream 3.0.1 + vtkNative ([M0](reports/phase-m0-upstream-3.0.1.md)) | checks and UI verification pass on the new base | done |
| M1 | VTK 9.7 recipe, vtkNative on macOS/Linux, the original vtkControl ([M1](reports/phase-m1-original-vtkcontrol.md)) | GUI probes on the original renderer | done |
| M2 | 3.0.1 composites, every form compiled whole, FrmMain and Program ([M2](reports/phase-m2-composites-painting.md)) | composite scripts through the original command line | done (macOS); Linux QuadWild done in M3-1b |
| M3-1 | One runtime: Avalonia front end, macOS (a) then Linux ARM64 (b), PyQt retired ([M3-1](reports/phase-m3-1-front-end.md)) | probes on both, the maintainer's real project and VNC check | done 22 November; previews published |
| M3-0 | Upstream 3.0.2 (`6703b1cb`): storage, HiGHS, Netgen re-pin, vtkNative; housekeeping and release basics ([M3-0](reports/phase-m3-0-upstream-3.0.2.md)) | checks, the macOS package probes and upstream's suite on 3.0.2 | done 23 November: macOS and Linux ARM64 verified and published; Linux x86-64 untested |
| M3-2 | The solver as the Windows release builds it (PaStiX, external behaviours; D070), the dark appearance (D069), macOS ([M3-2](reports/phase-m3-2-solver-appearance.md)) | solver comparison and package checks on macOS | done on macOS ARM64; Linux after macOS is complete and local Forgejo CI exists |
| M3 | GitHub Actions for win-x64, linux-x64, linux-arm64, osx-arm64: `build_ui.py` (every native component from source on a clean host, build paths mapped), `check.py`, the packages and their probes; Windows MSVC Gmsh and CalculiX; the Avalonia front end's first Windows run (Win32 native host); the bounds comparison on Windows | four packages built and tested in CI | planned |
| M4 | Original-app comparison through upstream's Python API test scripts on the original (Windows runner) and on X; analysis/meshing matrices | V evidence | planned |
| M5 | D061 fixes and warnings, clean organization (discussed first), installers, signing, notices, maintainer sign-off, upstream PR(s) | release | planned |

## Open items

Solver and tools (D070):
- **B022**: SPOOLES's multithreaded mode races on ARM64 (ThreadSanitizer: 127 races); ARM64 builds use the serial
  SPOOLES and PaStiX for multithreading. A real fix (synchronize SPOOLES's MT layer) is to discuss.
- **B021**: Tools - Bidirectional Mesh Converter (third-party Windows PyInstaller tool, no public source): ask
  upstream for the source and licence.
- Linux: the `pastix` stage of `build_ui.py` and the i8 solver have not run on Linux (the kit's image may need flex,
  bison and zlib headers); the appearance toggle on Linux.

Platform and packaging:
- **Linux x86-64**: the build kit (`X/Build/Linux/build-package.sh`) has run only on ARM64; its first x86-64 run
  (testers, or Podman on Windows per D059).
- **Windows**: never run yet (front end, Win32 native host, MSVC Gmsh/CalculiX, bounds comparison) — M3.
- **Netgen**: 3.0.2's `nglib.dll` carries a change not yet in the published NetgenMesher (pyramids at right-angle
  inside corners, upstream `42974ee7`); the published `01e30ce0` is pinned. Ask upstream for the revision.
- **Release basics**: every native component rebuilt through `build_ui.py` (compiler prefix maps) so
  `bundle.json` `buildPaths` is empty; notarization and Windows signing (credentials: maintainer); a complete
  third-party notice file; version numbering of the packages (upstream 3.0.2 + PrePoMax-X revision).
- The automation server on Unix; B014 (CAD/meshing results differ between runs and from Windows).

Parity and correctness (after parity, D061, unless noted):
- B013's round trip with the original Windows application; the 15 forms that need a live controller for the bounds
  comparison.
- Recorded bugs: B006–B012, B014, B016 (3.0.2 suite failures, triage first); D029 quadratic tetrahedron quadrature (the quadratic pyramid classification was
  fixed upstream in 3.0.2). Port defects reachable on macOS/Linux: `GmshAPI.cs` `Thread.Abort()` in the Gmsh error
  path, registry/WMI queries in `Tools.cs`/`AnalysisJob.cs`, the GDI calls of `XYPlotCurveSettings.cs`,
  `DynamicTypeDescriptor` `ReflectionOnlyLoad`.
- Warnings (unique, current build): see the latest `check.py` logs.
- V: zero items verified against the original in every inventory section ([inventory](PARITY_INVENTORY.md)).

Organization (M5, discussed first): the Phase A–C test hosts (`X/Core`, `X/Analysis`, `X/Execution`, `X/Results`,
`X/Feasibility`) once their numerical checks move onto X/App; the X deck writers and FRD/DAT snapshot hooks in
original folders that only they use; the per-folder `gitlab-ci.yml` files once GitHub Actions replace them (M3).

## What you need to do manually

1. **Windows x64**: a Windows machine or runner for the native app and the original's behaviour (M3/M4).
2. **Hands-on acceptance** on real hardware: macOS, a physical Linux desktop, Windows.
3. **Original PMX corpus**: real projects (outside Git) for compatibility testing; the release's example models and
   your 2.5.1 bridge model are the current set.
4. **Upstream**: whether a collaboration is welcome (portable vtkNative changes, the legacy-reader allowlist hook,
   the GmshCommon additions); the NetgenMesher revision behind 3.0.2's `nglib.dll`.
5. **Signing and publishing**: Apple Developer ID and notarization, a Windows code-signing certificate, GitHub
   releases.
6. **Decisions**: Gmsh 4.15.2 or 4.13.0; when the Phase A–C test hosts retire.

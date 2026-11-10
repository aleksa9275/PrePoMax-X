# Remaining work to full completion (D060)

Review of 9 November 2026 at `303b43c8`, updated 10 November after C6. Replace, don't append. Evidence for
each item is in the phase reports, `.project/bugs/` and the
[backlog](reports/deferred-correctness-improvements.md).

## Review verdict

| Phase | Verdict |
|---|---|
| A — domain libraries | **Done.** All checks pass (`python3 X/Checks/check.py`, 7 areas, 95 s, re-run 9 Nov). |
| B — Controller/Commands/PMX headless | **Done as a code path.** 236/237 commands structurally reachable; restricted NRBF PMX reader with allowlist, size/depth limits; bidirectional PMX with original 3.0.0 (CrossOver) on representative files only. |
| C — UI | **Implemented, not complete.** C6 (10 Nov) adds the full original main menu and fixes the visible defects. Still 0/72 original forms accepted, icon toolbars/tree tabs not original, 20 model/mesh entries without executed UI evidence, no installable app. |
| V — verified vs original | 0 items in every inventory section. |

## What I (Claude) can do

### 1. Finish Phase C
Done on 10 November ([C6 report](reports/phase-c6-main-window.md)):
- ~~Main menu~~: all 16 original menus and 313 release-visible items, generated
  from `FrmMain`, with original selection/confirmation/enabling; every reachable
  item runs in the GUI probe. Standard views repaired to the original Y-up.
- ~~Commands~~: parameter commands verified through the script panel (C); six
  others have no UI path in the original (compatibility/controller-inserted).
- ~~Visible defects~~: original scale bar and unit-system label, invariant decimal
  separator, original result-selector sizing.
- ~~PMX size caps~~: limits now scale with the file; AVI 2 GiB matches the
  original's AVI 1.0 writer.

Still open:
1. **Main window remainder**: original icon toolbars (File, Views, Model, Results,
   deformation/animation strips, Color by, Symbols) with the original icons, and the
   original model tree's three tabs (Geometry / FE Model / Results) with its context
   menus compared item-by-item.
2. **Model entries**: `MassSection`, `Damping` and the element classes still need
   executed UI evidence before C.
3. **72 forms**: close the C5 audit per form (993 designer fields, 796 event
   handlers): selection filters, property menus, keyboard/focus, row editing,
   clipboard, sizing. Mark C only when the whole form matches.
4. **Matrices**: all analysis types, Mmg/QuadWild/sweep/transfinite/shell/compound
   meshing, section/cap/picking, glyph variants, animation extrema,
   plots/annotations, exports, large projects.
5. **HiDPI**: original overlays (scale bar, status block) use physical pixels;
   compare against the original's DPI behaviour on Windows.

### 2. Make it shippable
7. **Packaging still builds the old app.** `X/Build/build.py` packages the
   reimplemented `X/Desktop` preview, not `X/UI`. Build Mac DMG / Linux
   archives (and Windows layout) for the X/UI app bundling .NET 10, CPython
   3.12, PyQt6/Qt, VTK 9.5.2, Python.NET, Gmsh 4.13 (patched), Netgen,
   CalculiX 2.22, lib3mf 2.4.1, with notices and corresponding sources.
8. **Reproducible profiles.** UI/native checks only run with Python/tool/
   solver profiles that live in `/private/tmp` (they disappear). Add a script
   that builds them from the repo so `check.py` can run the UI and native
   workflows by default instead of reporting them pending.
9. **Retire duplicates**: `X/Desktop` (old Qt app), the older `X/Core`,
   `X/Analysis`, `X/Results`, `X/Execution` hosts and `X/Feasibility` once
   their checks are covered by Controller/UI checks; update READMEs.

### 3. Fixes after parity (D061) — the error list
Port defects (original Windows-only code reachable on Mac/Linux):
- `CaeMesh/Meshing/Gmsh/GmshAPI.cs:173` `Thread.Abort()` throws
  `PlatformNotSupportedException` in the Gmsh error path.
- `CaeGlobals/Tools.cs` registry + WMI queries; `CaeJob/AnalysisJob.cs`
  `IsAdministrator`; `UserControls/.../XYPlotCurveSettings.cs` (9 GDI calls);
  `vtkMaxLookupTable` bitmap export; `DynamicTypeDescriptor` `ReflectionOnlyLoad`.

Recorded bugs:
- **B010** concurrent CAD stages not stopped by Cancel.
- **B011** doubled-stress diagnostic 199.992 vs 200 (original agrees; cause open).
- **B012** cancel before the solver process starts is lost.
- **D029** quadratic tetra measurement quadrature (4.3 % low); quadratic
  pyramid missing from `IsParabolic`.
- **B006** quadratic pyramid → wedge under pressure; **B007** buckling shift
  misses lower factor; **B008/B009** structural/modal diagnostics; thermal
  one-increment accuracy; Mac vs Linux CAD mesh differences; 1e-12…1e-6 MPa
  solver differences.
- Original `CalCLoad` writes global directions when the local CS is unresolved.
- GmshCommon quirks: `OCC.Remove` (0,0) pairs, `GetMaxNodeTag` int truncation.

Warnings (unique, current build): Domain 78, Controller 128, UI 152 (overlapping;
mostly CS0168, NU1701, CA1416, CA2022, CS0649/CS0414/CS0612), including
`CS1717` self-assignment in `Tools.cs:293`.

## What you need to do manually

1. **Windows x64**: run the full original net48 build in Visual Studio
   (C++/CLI GmshCommon, ActiViz) and the native .NET 10 app on a real Windows
   machine; I can prepare scripts but can't execute Windows.
2. **Linux x64** via Podman on Windows (D059).
3. **Hands-on UI acceptance** on real hardware: Mac, a physical Linux desktop
   (GPU, Wayland/X11), Windows — mouse/keyboard feel, HiDPI, side-by-side with
   the original app. I can automate comparisons; the sign-off is yours.
4. **Original PMX corpus**: provide real projects (kept outside Git) for
   compatibility testing.
5. **Upstream**: ask Matej Borovinšek for the Q-Morph `QuadMesher` source and
   license, and the exact source revision of the stable 3.0.0 binary.
6. **Signing and publishing**: Apple Developer ID + notarization credentials,
   Windows code-signing certificate, Homebrew tap repository, GitLab release,
   creating/protecting `x/release`.
7. **Decisions**:
   - must the main window match the original layout exactly (menus, icon
     toolbars, tree tabs), or is the Qt shell with the same commands enough?
   - adopt Gmsh 4.15.2 or stay on 4.13.0;
   - retire `X/Desktop` now;
   - resume hosted CI (D058 quota hold).

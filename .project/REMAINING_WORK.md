# Remaining work to full completion (D060)

Updated 22 November 2026 after M3-1b (Linux ARM64, PyQt retired). Replace,
don't append. Evidence for each item is in the phase reports, `.project/bugs/` and the
[backlog](reports/deferred-correctness-improvements.md).

## Plan to release (maintainer, 17 November 2026)

| | Milestone | Done when |
|---|---|---|
| M0 | ~~GitHub replay, merge upstream `1e2f83f2`, sources/allowlist/generators~~ ([M0](reports/phase-m0-upstream-3.0.1.md)) | checks and UI verification pass on the new base |
| M1 | ~~VTK 9.7 recipe; `vtkNative` for macOS/Linux; original `vtkControl` compiled whole and embedded in Qt~~ ([M1](reports/phase-m1-original-vtkcontrol.md)) | all GUI probes pass with the original renderer (Mac, Linux ARM64) |
| M2 | 3.0.1 features (composites: FrmSection Layers/layup, FrmMaterialOrientation, result outputs, property-grid missing values; a Graphics/Paint layer drawn by Qt), Netgen re-pin to the published NetgenMesher, QuadWild for macOS/Linux from the published fork; FrmMain whole on the native `vtkControl` | every form compiled whole; upstream composite test scripts pass (one VTK per package: done in M1). Done on macOS ARM64 ([M2](reports/phase-m2-composites-painting.md)): all 73 forms compiled whole with FrmMain and Program (`X/App`), 4 of 4 composite scripts pass through the original command line, FrmMain shown in Qt; closeout: off-screen view for `-g No`, upstream suite 63 of 81 (B013, B014 open); open: Linux QuadWild build |
| M3-1a | **macOS first (D067): the original application (`X/App`) on Avalonia, M2's Qt front end matched and bettered.** The spike ([report](reports/phase-m3-1-front-end.md)) proved one runtime, the native 3D view with real input and picking, modal loops, Retina and the overlays (D066). Steps: (1) the renderer moves from `X/Spike/FrontEnd` into X/App: the FormsCompat mirror driven by its notifications, every control kind (check/radio/combo/numeric boxes, list and tree views with images, group boxes), tool strip states (checked, drop-down buttons, combo boxes), context menus, keys (the original key hook, Esc, shortcuts) and focus; (2) the original paint handlers replayed on Avalonia's DrawingContext; (3) property grid (custom, as in Qt), data grids (Avalonia DataGrid), code editor (AvaloniaEdit), ZedGraph plots, message boxes, file and colour dialogs; (4) layout: the dotnet/winforms layout engines (dock/anchor, flow, table, ToolStrip, AutoSize/PreferredSize; MIT, notice kept) ported into FormsCompat, and a per-form bounds comparison with the original 3.0.1 (a 3.0.1 CrossOver bottle: the maintainer's download decision; Windows later); (5) "better than M2": the intermittent start-up stall found and fixed, a compact WinForms-like light theme, no tool strip overflow, view resize without flicker, context-menu coordinates in control units, the triad's arrow length; (6) the GUI probes (app probe and the eight probe areas) on X/App and Avalonia; (7) a macOS .app from `X/App/local_app.py` without PyQt. **21 November:** steps 1–3 done in `X/App/FrontEnd` (data grids and the code editor drawn from the model as in Qt, not Avalonia's DataGrid/AvaloniaEdit), from step 5 the theme and context-menu units, step 6's app probe (16/16); open: step 4, the workbench probe areas, the stall, flicker, triad, step 7's bundle. **Maintainer's real project, 21 November:** a 2.5.1 model and a STEP import open, CalculiX (SPOOLES, 4 cores, linear and nonlinear) runs and its results open in the Mac app; four issues found on the way were fixed ([report](reports/phase-m3-1-front-end.md)) **Closed 21 November:** layout gaps fixed from the bounds comparison (Wine Mono evidence; Windows run in M3), the probe areas pass on Avalonia (120+4+9+5), triad scaled, stall not reproduced in 13 runs, `PrePoMax-X.app` without PyQt (`X/App/package_mac.py`) | on macOS ARM64: the app probe and the eight probe areas pass on Avalonia; the maintainer runs a real project (open, mesh, CalculiX, results) in it; the bounds comparison runs for every original form with its differences recorded; the macOS app has no PyQt |
| M3-1b | **Linux after macOS:** the same app on the local Podman machine (Linux ARM64): automated probes under Xvfb, a VNC view for the maintainer's manual checks; Avalonia's X11 native host with VTK's X11 window and input (`ProcessEvents`); QuadWild on Linux (a VM larger than 4 GiB). The UI does not depend on the CPU architecture; Linux x64 follows with the per-architecture native builds (D059). Then the workbench, headless host, `OriginalFormHost`/`OriginalViewHost` and PyQt are retired; CPython stays only for the original's Python features **Done 22 November**, the maintainer's VNC check passed: app probe 16/16 and probe areas 124+4+9+5 on the Linux package in a Podman session without the repository, upstream suite 60/81 (macOS 61/81, same layout), Linux QuadWild and vtkNative, PyQt workbench, Qt front end and Headless host retired, B015 fixed ([report](reports/phase-m3-1-front-end.md)) | the probes pass on Linux ARM64 with Avalonia; the maintainer's manual check over VNC; no PyQt in the packages |
| M3 | GitHub Actions for win-x64, linux-x64, linux-arm64, osx-arm64: `build_ui.py`, checks, GUI probes; Windows MSVC Gmsh and CalculiX; the Avalonia front end's first Windows run (Win32 native host) | four packages built and tested in CI |
| M4 | Original-app comparison through upstream's Python API test scripts (79) on the original (Windows runner) and on X; analysis/meshing matrices | V evidence |
| M5 | D061 fixes and warnings, clean organization (discussed first), installers, signing, notices, maintainer sign-off, upstream PR(s) | release |

Answered by 3.0.1: the modified QuadWild source (github.com/PrePoMax/QuadWild), NetgenMesher with its
Netgen 5.3.1/OCCT 8.0.1 port (github.com/PrePoMax/NetgenMesher, LGPL-2.1) and the Gmsh fork
(github.com/PrePoMax/Gmsh) are published; Q-Morph was removed upstream.

## Review verdict

| Phase | Verdict |
|---|---|
| A — domain libraries | **Done.** All checks pass (`python3 X/Checks/check.py`, 7 areas, 95 s, re-run 9 Nov). |
| B — Controller/Commands/PMX headless | **Done as a code path.** 236/237 commands structurally reachable; restricted NRBF PMX reader with allowlist, size/depth limits; bidirectional PMX with original 3.0.0 (CrossOver) on representative files only. |
| C — UI | **Implemented, not complete.** C6–C8 (10 Nov) add the original main menu, tool strips and complete model tree; C9 runs 39 original form classes whole (38 forms C). 33 forms still use toolkit dialogs, 2 model/mesh entries (beam elements) lack executed UI evidence, no installable app. |
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

- ~~Tool strips and tree~~ ([C7](reports/phase-c7-toolbars-tree.md)): the five
  original tool strips with original icons, the three-tab ModelTree with original
  layout, images, search and context-menu rules. The two pointer probes now pass.

- ~~Tree remainder and model entries~~ ([C8](reports/phase-c8-tree-elements.md)):
  rename, drag and drop, groups, Group Cells / Fuse Bodies, keys, mouse over,
  keyword counts, `BasePart.ico`, output links; UI evidence for 18 model/mesh
  entries.

Still open:
2. ~~Beam element classes~~ ([C12](reports/phase-c12-editor-forms.md)): CAD shell free edges and a
   second-order Netgen shell mesh through the original UI.
3. **72 forms** — 70 compiled whole in [C9](reports/phase-c9-original-forms.md)–
   [C12](reports/phase-c12-editor-forms.md) (69 C). Remaining (maintainer, 11 Nov: after packaging):
   FrmMain whole — the original ModelTree, side panels (Advisor, Python with
   PythonConsoleTextBox, XY plot), a vtkControl adapter (165 members), menus/tool strips from
   the designer; with it FrmPythonStop (second UI thread) and FrmSelectEntity (the original
   handlers that call it and their ~210 FrmMain targets). Renderer gaps: autocomplete popup
   look, owner-drawn paint (TabPage.Paint, CollapsableGroupBox +/- glyph, CodersLabTreeView
   drop line), grid row drag-and-drop (DoDragDrop), ZedGraph zoom/pan and context menu,
   FCTB folding/column selection/word wrap, light theme/HiDPI. The C1–C5 toolkit dialogs and
   legacy menus the originals replaced are unreachable; retire them in the clean-organization pass.
4. **Matrices**: all analysis types, Mmg/QuadWild/sweep/transfinite/shell/compound
   meshing, section/cap/picking, glyph variants, animation extrema,
   plots/annotations, exports, large projects.
5. **HiDPI**: original overlays (scale bar, status block) use physical pixels;
   compare against the original's DPI behaviour on Windows.

### 2. Make it shippable
6. ~~lp_solve for macOS/Linux~~, 7. ~~packaging the X/UI app~~, 8. ~~reproducible
   profiles~~ ([P1](reports/phase-p1-desktop-packages.md)): `X/Build/build_ui.py` builds every native
   input from its recipe and packages macOS (DMG), Linux (tar.gz) and Windows (zip); `verify-ui.py
   --package` uses a package's runtime. Still open: Linux x64 build (maintainer, Podman on Windows),
   Windows execution, the MSVC Gmsh build and the Windows CalculiX build, QuadWild for macOS/Linux
   (fork source), a full from-scratch `build_ui.py` run per target, distribution notices/signing.
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
- **B013** `System.IO.FileInfo` in PMX objects refused (distributions/imported loads from files). Fixed
  20 November 2026; round trip with the original 3.0.1 pending.
- **B014** 9 upstream CAD/meshing scripts differ from the Windows original (results vary between runs).
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
5. **Upstream**: the QuadWild, NetgenMesher and Gmsh sources are now published and Q-Morph is gone
   (3.0.1). Still worth asking: the exact source revisions behind the shipped 3.0.1 binaries
   (`nglib.dll`, QuadWild, Gmsh), and whether a portable `vtkNative` contribution is welcome.
6. **Signing and publishing**: Apple Developer ID + notarization credentials,
   Windows code-signing certificate, Homebrew tap repository, GitHub release,
   creating/protecting `x/release`.
7. **Decisions**:
   - must the main window match the original layout exactly (menus, icon
     toolbars, tree tabs), or is the Qt shell with the same commands enough?
   - adopt Gmsh 4.15.2 or stay on 4.13.0;
   - retire `X/Desktop` now;
   - ~~resume hosted CI~~: GitHub Actions in M3 (D064).

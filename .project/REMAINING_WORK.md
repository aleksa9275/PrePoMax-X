# Remaining work to full completion (D060)

Updated 18 November 2026 after M0 (upstream 3.0.1 + vtkNative merged, GitHub home; D063, D064). Replace,
don't append. Evidence for each item is in the phase reports, `.project/bugs/` and the
[backlog](reports/deferred-correctness-improvements.md).

## Plan to release (maintainer, 17 November 2026)

| | Milestone | Done when |
|---|---|---|
| M0 | ~~GitHub replay, merge upstream `1e2f83f2`, sources/allowlist/generators~~ ([M0](reports/phase-m0-upstream-3.0.1.md)) | checks and UI verification pass on the new base |
| M1 | VTK 9.7 recipe; `vtkNative` for macOS/Linux (its three Win32 files); original `vtkControl` compiled whole and embedded in Qt | geometry/results GUI probes pass with the original renderer |
| M2 | 3.0.1 features (composites: FrmSection Layers/layup, FrmMaterialOrientation, result outputs, property-grid missing values; a Graphics/Paint layer drawn by Qt), Netgen re-pin to the published NetgenMesher, QuadWild for macOS/Linux from the published fork; FrmMain whole on the native `vtkControl`; Python VTK retired | every form compiled whole; one VTK per package; upstream composite test scripts pass |
| M3 | GitHub Actions for win-x64, linux-x64, linux-arm64, osx-arm64: `build_ui.py`, checks, GUI probes; Windows MSVC Gmsh and CalculiX | four packages built and tested in CI |
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

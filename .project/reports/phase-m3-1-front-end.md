# M3-1 — one runtime for the front end (D065)

Started 20 November 2026 on macOS ARM64; M3-1a closed 21 November, M3-1b (Linux ARM64) closed 22 November.

## Toolkit spike

The spike (`X/Spike/FrontEnd`, removed when its renderer moved into X/App; see git history) ran the original `Program.Main` of X/App with an
Avalonia 11.3.23 front end in one .NET runtime. It was measured with `-f` on the one-element solid fixture
(`editable-solid-workflow/runs/bridge/baseline/mesh.inp`) on macOS ARM64, unattended (`PREPOMAXX_SPIKE_PROBE`).

| Question | Result |
|---|---|
| One thread, one runtime | Control model, Controller callbacks and Avalonia on the main thread (managed thread 1); the WinForms queue is drained by an Avalonia timer; no CPython in the process |
| Start-up | `FrmMain.Show` (Load) 0.17 s; the `-f` import, the tree and FrmMain's model state (menus enabled, view visible) as with the Qt front end |
| Original controls mirrored | 469 menu items (16 menus, submenus filled on `DropDownOpening`), 70 tool strip items with the original icons, status strip, model tree with the imported model; 35 controls at their FormsCompat bounds |
| 3D view in a native host | `NativeControlHost` gives an `NSView`; the original vtkControl attaches to it, draws the model, follows its bounds and `Visible` |
| View input | A middle-button drag through the host's pointer path turns the model (images before/after differ as expected) |
| Modal forms | `FrmNewModel` (no `-u`) opens as an Avalonia window; the nested `Dispatcher.UIThread.MainLoop` ends when the form closes |
| Real OS mouse events over the native view | **Verified by hand (21 November, mouse):** rotate, zoom and clicks act on the cube where it is drawn. It needed three macOS fixes, found in two manual rounds: (1) Avalonia's host `NSView` kept the mouse (no event reached the control) — it is now transparent to hit testing (`CocoaPassThrough.ApplyToView`) and the host answers Avalonia's hit test; (2) VTK sized its view in points from the pixel size it was given, so the view was half size — it now gets device pixels (`VtkNativeHost.DeviceScale`, Retina resolution); (3) VTK placed its view for a flipped parent and macOS no longer clips subviews, so the drawing sat below the area that took the input — VTK's view is now pinned to the host's bounds and clipped (`VtkNativeHost.FitViewToHost`). Both settings default to the Qt behaviour |
| Linux (X11 child window) | **Not run** (Linux ARM64 via Podman/Xvfb next) |
| Seen in the manual runs, not toolkit questions | Fixed on 21 November: FrmMain's output window had half the right side instead of its designer height — the FormsCompat SplitContainer kept a fixed panel's size only outside the form's initialization, so the output panel took all the growth from the designer size to the window size; it now follows every size change, as WinForms does (Qt front end too). The spike draws the splitter bars (draggable), the tab headers in their 24-unit row above the pages (the model tree no longer overlaps them) and the output window's messages. Open: the view's overlays (scale bar, axes) are placed and sized by the original in control units while VTK draws in device pixels, so they are misplaced (see DPI below). Fluent's controls are larger than the WinForms designer sizes |
| DPI | The original is not DPI aware (`SetProcessDPIAware` is commented out in `Program.cs`): on a high-DPI Windows display Windows magnifies its window. On macOS, VTK drawing in points, magnified, crashed in Apple's OpenGL pixel readback (SIGBUS in `glReadPixels`), so that change was taken out. Instead (D066) the view draws in device pixels and the overlay geometry is scaled in vtkControl's C# widget wrappers by `VtkNativeView.DisplayScale` (1 on Windows); VTK's view is pinned to the control's size, never the host's bounds (which lag a layout pass and made vtkNative re-anchor the overlays against a stale size). Result on Retina: scale bar centred at the bottom, axes in the bottom-right corner, full-size text, sharp view. Open: the axes' arrows have a fixed length in vtkNative (slightly short next to their labels); mouse coordinates in the original's context-menu events are device pixels |
| Manual check, 21 November (all seven overlay checks right) | Resizing flickers (the view scales from both sides, then settles centred): VTK's view follows the control's size one layout pass after Avalonia's host. Spike gaps, not toolkit questions: tool buttons do not show their checked state (Query stays highlighted in the original), Esc does not end the query (keys reach only the focused view), annotation removal does nothing visible. Picking works at Retina coordinates (two nodes queried correctly) |
| Start-up stall | The intermittent stall (menus grey, `-f` import not started, no exception) also occurs with Avalonia: 2 of 7 unattended runs on 21 November. It is not specific to Qt; open |

The spike found one bug of its own (a size handler running before its window had a form); it hid the start-up in a
way that looked like the intermittent Qt stall: an exception in a renderer callback escaped through `FrmMain.New` and
left FrmMain in its no-model state with the model loaded. The intermittent Qt stall stays open and is not explained
by this.

### Avalonia or a Qt 6 shim

The Qt 6 route would need a C ABI shim built and shipped for four targets, Qt itself (about 100 MB per package) and a
hand-written binding layer, before any control is drawn. Avalonia is NuGet only (`Avalonia`, `Avalonia.Desktop`,
`Avalonia.Themes.Fluent`; MIT), has native hosts for Win32, Cocoa and X11, nested dispatcher loops for modal forms, and
is already sufficient for everything the spike checked. **Recommendation: Avalonia**, provided the X11 run on Linux passes
(real input on macOS passed). The Qt 6 shim is only needed if they fail without a workaround. The production pin
(Avalonia 11.3.x or 12.1.x) is chosen when the renderer moves into X/App.

## A working app for real projects (21 November)

`X/App/local_app.py` assembles a local macOS folder of X/App with the Qt front end (M2) from the P1 package (Python,
PyQt, meshers, lp_solve), GmshCaller from the current sources, QuadWild and the M2 CalculiX build, with a launcher.
Checked: upstream's analysis, result and composite scripts through it pass 10 of 11 (the failure is the known
Windows-only `Api_View_Results`), and the Qt main-window probe passes 9 of 9. Until the Avalonia renderer covers the
forms, property grid and data grids, this is the front end for real work.

## M3-1a: the front end in X/App (21 November)

The renderer moved from the spike into X/App as `PrePoMaxX.FrontEnd` ([README](../../X/App/FrontEnd/README.md)),
the C# successor of the Qt renderer: PrePoMax.dll hands `Application.Run`'s main form to it; the Qt renderer stays
selectable (`"frontEnd": "qt"`, `PREPOMAXX_FRONT_END=qt`). Ported from the Qt renderer, reusing the model's own
layout and behaviour: every control kind of the Qt renderer (check/radio/combo/numeric boxes, track/scroll/progress
bars, pictures, link labels, group boxes, tabs, splitters, list views), menus with DropDownOpening, tool strips with
the checked state, drop-down buttons, combo and text boxes, the status strip, context menus shown by the original
(`ContextMenuStrip.Show`), menu shortcuts, the original key hook for every key, Enter/Escape as dialog keys, focus
(`Enter`/`Leave`), activation (`Form.ActiveForm`), the tree view and FastColoredTextBox (code editors, the output
window, autocomplete) drawn from the model's rows and lines, data grids on the model's geometry (selection, editing,
keys, clipboard), the property grid with the original converters and UITypeEditors, the paint replay on Avalonia's
DrawingContext, ZedGraph plots, message boxes, file/folder/colour dialogs, timers, text measurement and the
clipboard; a compact WinForms-like light theme with the Windows 10 system colours (.NET's table on macOS has the
Windows XP ones). Design change against the D067 plan: data grids and the code editor are drawn from the model (as in
Qt) rather than Avalonia's DataGrid and AvaloniaEdit, which would duplicate behaviour the model already has.

Found and fixed on the way: a sync storm (the output window reported its scroll position each sync, which the model
notifies); the output window not following its newest message (FormsCompat's `DoRangeVisible` now names its target;
a read-only view at its end stays there); model tree icons (a designer image list's images are in a serialized `.resx`
stream that is never read; its keys are the original icon file names, which the front end resolves).

The spike's gaps from the manual check: Escape now ends the query and closes the forms (the window that is activated
makes its form `Form.ActiveForm`, which FrmMain's key hook requires); tool buttons show their checked and hovered
state; the view's context menus (annotation, legend, viewport) open, so "remove annotation" is reachable; their
position is in control units: vtkControl now gives the original its view mouse events (right click, widget double
clicks) in control units and converts back to device pixels only for the scalar bar's hit test (D066's rule: device
pixels stay inside the widget wrappers).

**Probe** (`PREPOMAXX_UI_PROBE=avalonia`, macOS ARM64, `-f` one-element solid): 16 of 16 — the 9 checks of the Qt app
probe (menus, strips, view, import, tree, view image, FrmMaterial from the menu) and a drag turning the view,
FrmMaterial's property grid after adding Elastic, Escape through the key hook, the view's context menu at the click
point in control units (562, 295 for 561.5, 296), a modal form through the nested loop, tool button states.
Five consecutive unattended runs from the app folder: 16/16 each; the intermittent start-up stall (2 of 7 spike
runs) did not occur in them, which does not show it is gone (open). `python3 X/Checks/check.py`: all 7 areas pass. A local app folder: `X/App/local_app.py --front-end avalonia`
(default) builds `X/Build/artifacts/app-mac`; the Qt folder `app-mac` is left as it is.

Not done in M3-1a yet: the dotnet/winforms layout engines and the per-form bounds comparison with 3.0.1; the eight
workbench GUI probe areas (they drive the Qt workbench, not X/App: their FrmMain parts are covered by this probe, the
form-level checks need porting); the macOS `.app` bundle without PyQt (the app folder still uses the P1 package's
Python, which carries PyQt, though the Avalonia front end does not load it); the triad's arrow length; view resize
flicker; the maintainer's manual check and a real project.

### The maintainer's first check (21 November)

"Very promising"; two failures, neither in the front end (the Qt front end fails the same way):

- **STEP import**: "The work directory does not exist." The original has no work directory until the user sets one
  (Settings → Solver), and CAD import and analyses need it. `Configure --work-directory` now sets it and
  `local_app.py` uses `<output>/work` (outside `app/`, which a rebuild replaces). The maintainer's STEP file imports
  (`Shell_part-1`, NetgenMesher split and visualization).
- **A 2.5.1 `.pmx`**: "corrupt or incompatible". The restricted PMX reader required every field of the current type,
  and 3.0.1's `CommandsCollection` has `_postprocessingDeclined`, which 2.5.1 did not write. The original's
  BinaryFormatter (default simple assembly format) leaves such a field at its default; the reader now does the same
  (types, limits and identity checks unchanged). The maintainer's 2.5.1 bridge model opens, with 3.0.1's own
  compatibility step (a Netgen mesh setup item keeps the 2.5.1 mesh).

After both: Avalonia app probe 16/16, `check.py` 7/7.

The maintainer then moved the Mac app to Avalonia: `X/Build/artifacts/app-mac` is rebuilt with the Avalonia front end
(`local_app.py` now keeps an app folder's settings across rebuilds and sets a work directory only when none exists);
there it passes the probe 16/16 and opens the maintainer's 2.5.1 model and STEP file without an error box.

### The maintainer's second check: an analysis of the 2.5.1 model (21 November)

UI fine; three findings:

- **The analysis fails with "the PARDISO library is not linked"** (CalculiX exit 201). The 2.5.1 model's step keeps
  its PARDISO solver; the local CalculiX build has SPOOLES only (D060's sole exception, D041: no silent rewrite of
  solver choices). Expected behaviour; the user picks a solver of the build in the step. A pre-run notice is a
  maintainer decision, not made.
- **Opening the failed result: "Unclosed, truncated or trailing FRD data is not a complete result."** An X error:
  the bounded FRD inspection (`ReadStaticSnapshot`) adds its limits to the original reader through partial methods,
  and they applied to the original read path too (and its 100000-record limits to real models). They now apply only
  inside `ReadStaticSnapshot`; the original path gives the original's own message ("The result file does not exist
  or is empty.") for the solver's header-only file. Result tests unchanged and passing.
- **The view starts small until the window is resized.** VTK's view was fitted to the control's size while
  Avalonia's native host view still had its first frame (1×1); Avalonia places the host after that layout pass. The
  view is fitted again once the host has its frame (`VtkNativeHost.FitView`, traced with
  `PREPOMAXX_TRACE_VIEW_SIZE=1`: host and view 1123×592). The maintainer: still small, **after opening a model**.
  A capture of the app's own window (`PREPOMAXX_WINDOW_CAPTURE`, the terminal has no screen recording permission)
  showed VTK drawing a quarter of the view: upstream's `vtkControl.SyncNativeMirror` (on SetBackground, which
  opening a model calls) set the view's size from `ClientSize` in control units, which are pixels on Windows and
  half the device pixels on a Retina Mac. The host now sets that size in its own units (`VtkNativeHost.SyncViewSize`,
  both hosts; the Windows one unchanged in effect).
- Re-check: the analysis with SPOOLES runs and its results open. **The output window scrolled to the right**: the
  original output box wraps its lines at the control width (`WordWrap`, rows after the first indented past the date,
  `WordWrapIndent` 20); the Avalonia code view drew every line unwrapped and scrolled to the end of the long 2.5.1
  compatibility line. The code view now lays out wrapped rows as FastColoredTextBox does (breaks between words) and
  maps clicks back to the text box's line coordinates, so links still work. Confirmed in a window capture after
  opening the maintainer's model: view full size, output wrapped.

After these: probe 16/16, `check.py` 7/7.

## M3-1a close-out (21 November)

All four open points closed; M3-1a is done on macOS ARM64.

- **Layout and the bounds comparison.** `X/App/Bounds` dumps every original form's control bounds on WinForms
  (net48, the original 3.0.1) and on FormsCompat (X/App); [evidence](m3-1a-bounds/README.md). The reference ran in
  CrossOver on **Wine Mono** (no Microsoft .NET Framework in the bottle): 66 forms, 566 controls, 108 differences,
  all from Mono's fonts, frame and tab handling; 15 forms need a live controller on both sides. It found four
  FormsCompat gaps, fixed: Minimum/MaximumSize (the splash stayed expanded), the 300 × 300 form default, relayout
  on `Padding`, docking in `DisplayRectangle` (group box caption, scrollable padding); the table layout gained cell
  borders and WinForms' percent rounding. The Windows-authoritative run is the same tool on the M3 Windows runner.
- **The workbench probe areas** on the real app ([evidence](m3-1a-probe-areas/summary.json)):
  `PREPOMAXX_UI_PROBE_AREA` with `run_probe_areas.py` — forms 120 (menu parity in every view; every create form
  through its original entry point at its designer size, every visible control mirrored at its bounds, Cancel
  changing nothing; FrmStep, FrmAmplitude data grid, FrmEditCommands), geometry 4 (CAD import, Netgen), results 9
  (CalculiX through FrmMonitor, results controls, contour view), elements 5. Found and fixed: windows of forms that
  change nothing after `Show` opened at Avalonia's default size (NaN width never compared unequal).
- **Polish.** The triad's shaft is scaled to the display as its labels are (`vtkn_triad_set_shaft_length`, native
  default unchanged on Windows). The start-up stall did not occur in 13 consecutive runs since the renderer's
  callbacks are guarded (not reproduced; not shown gone). Resize: programmatic resize captures show no offset or
  stretch; a live drag is the maintainer's check. `PREPOMAXX_WINDOW_CAPTURE` saves the app's own windows (the VTK
  view included) for visual checks without the screen recording permission.
- **`PrePoMax-X.app` without PyQt** (`X/App/package_mac.py`, source `73c75b8a`): X/App self-contained (no .NET install),
  CPython without PyQt6/VTK-Python, P1's meshers and Gmsh, GmshCaller, QuadWild, the local app's CalculiX relocated
  with its libraries; ad-hoc signed; 615 MB, zip 195 MiB. In a clean environment (no `dotnet` on PATH) the bundle and
  the unpacked zip pass the base probe 16/16 and the four areas (120 + 4 + 9 + 5). Published as a preview on the
  branch `release/macos-arm64-preview` (binary only, README with the status).
- **Preview 2 (source `e076f692`): what the first upload lacked.** The maintainer's download had no icons: the front
  end found the original images by walking up to the repository, which every earlier check ran inside. An audit
  against the 3.0.1 release found more of what the original keeps beside the program. Now in the bundle:
  - `app/resources`: the icons and the designer `.resx` images (235 files);
  - `Help/Python`: built by X/App itself with upstream's `PythonApiHelp.targets` (Markdig 1.3.2) and the SKILL.md
    post-build copy;
  - `materials.lib`, `Models/` and `Tools/abqodb_to_ccxfrd.py` from the 3.0.1 release (`--original`; SHA-256 in
    `bundle.json`);
  - an `.icns` and window/Dock icon from `PrePoMax/main.ico`.
  Not shipped: the release's Windows-only BidirectionalMeshConverter.exe.
  **Verification now blocks the repository:**
  - the unpacked zip ran under `sandbox-exec`, with no reads of the repository, the P1 checkout, Homebrew or .NET,
    on a fresh data folder;
  - base probe 16/16; areas 124 + 4 + 9 + 5 (new checks: 144/144 menu icons, the app icon, and the material
    library with 21 materials read through the allowlist);
  - upstream's Python tests `Test_Analysis`, `Test_Model_Materials_Sections` and `Test_Model_Meshing` passed
    through `--script -g No`.
  Netgen prints `Get neighbourpoints failed` during `Test_Model_Meshing`. The test passes; whether Windows 3.0.1
  prints it too is not checked yet.

## M3-1b: Linux ARM64 and PyQt retired (22 November)

On the maintainer's Podman machine `prepomax-podman` (Fedora 44, libkrun, 8 CPUs, 15 GiB, 93 GB), with downloads
approved for M3-1b: Ubuntu packages, the .NET runtime pack, and the locked sources.

- **Images** (`X/Build/Linux`):
  - `Containerfile.build`: Ubuntu 24.04 with the recipes' build packages and patchelf.
  - `Containerfile.run`: a plain Ubuntu 24.04 desktop with Xvfb, Mesa llvmpipe, Openbox, x11vnc and ImageMagick
    for screenshots; no .NET and no development packages.
  - `session.py` runs a package in the desktop image for the probes, or for a person over VNC (localhost only,
    password). Only the package and a work folder are mounted, so the app under test cannot read the repository.
- **Native builds:**
  - vtkNative rebuilt for Linux ARM64 against M1's VTK 9.7.1. It adds M3-1a's `vtkn_triad_set_shaft_length`.
  - QuadWild built from the locked fork revision (`df747a1`) with its recipe. The Linux QuadWild that M2 left
    open is done.
- **Package** (`X/App/package_linux.py`), the same content as the macOS bundle:
  - X/App self-contained for `linux-arm64`, Avalonia X11, the original resources, help, material library, examples
    and `PrePoMax.com`;
  - Python, meshers, Gmsh, lib3mf and CalculiX from the P1 Linux package, checked against its manifest; Python's
    `share/terminfo` is left out (case-only duplicate names; interactive terminals only);
  - a desktop entry with an install script;
  - data kept in `~/.local/share/PrePoMax-X`.
  - Build-machine run paths are stripped only from this repository's builds, and every fingerprint is checked
    again after packaging. That check caught an early version of the stripper that had touched `libgmsh`.
  - 799 MB unpacked; the tar.gz is 259 MiB.
- **Front end on X11.** It worked on the first start: 13 of 14 app checks, with the 3D view in Avalonia's native
  control host and the host pumping VTK's X11 events. On Linux the default font is now one with Segoe UI's widths
  when installed (Liberation Sans, Arimo); with DejaVu Sans, "Displacements" was cut off.
- **B015, found by Linux.** A right click on a part picked in control units, so on Retina it picked at half the
  coordinates and opened the wrong menu. Fixed in `vtkControl.cs` with a no-op on Windows. The app probe now checks
  both context menus, and macOS fails it with the old dll.
- **.NET runtime.** The macOS preview had shipped .NET 10.0.15: the packager did not pass the project's pin, so the
  SDK took its newest patch. Both packagers now take `runtimeFrameworkVersion` from `X/Build/targets.json`
  (10.0.14) and check the published output against it.
- **Verified on the unpacked Linux tar.gz** in the session, with the repository not mounted:
  - app probe 16/16 and probe areas 124 + 4 + 9 + 5;
  - upstream's Test_Analysis, Materials_Sections, Meshing and Meshing_QuadWild_Transfinite (`verify-app.py
    --scripts`);
  - QuadWild itself ran: remeshing, field and patches.
  The macOS bundle from the same commit passes the same set under `sandbox-exec`, with .NET 10.0.14.
- **Upstream's full suite** (`Run_Tests.py --exe .../PrePoMax.com`, the scripts copied out of the repository):
  - Linux ARM64 passes 60 of 81, macOS ARM64 61 of 81 on the same layout. The one difference is
    Geometry_Transform, which B014 records as not reproducible from run to run.
  - The 64 of 20 November included three scripts that read the repository's C# sources (the two audits,
    Three_Block_Mapping); this layout keeps the repository out of reach.
  - The rest are as in M2: Windows-only test content (`TEMP`/`LOCALAPPDATA`, PowerShell, named mutexes), the
    automation server on Unix, and B014's meshing differences.
- **Retired (D065):**
  - the PyQt workbench (X/UI's Qt files, `OriginalFormHost`/`OriginalViewHost`, the workbench probes and
    generators);
  - the Qt front end of X/App (`frontEnd: qt`, Configure `--ui`, `local_app.py --front-end`);
  - the Headless host and `run-upstream-scripts.py` (upstream's own runner drives X/App);
  - the P1 workbench launcher.
  `package_ui.py` now assembles only the native components, with numpy as the only Python wheel
  (`X/Build/python-requirements`). `X/App/verify-app.py` replaces `X/UI/verify-ui.py` as check area `app`. X/UI
  keeps the control model, the original-form generator and its outputs. `check.py`: 7 of 7 areas pass.
- **The maintainer's check over VNC** (22 November): everything looks good and works.
- **Not done here:**
  - Linux x64 (per-architecture native builds, D059);
  - rebuilding every native component from source on a clean host (M3 CI);
  - the older `X/Desktop` preview with its own PyQt requirements (not packaged; a cleanup candidate for M5).

## Next

M3: GitHub Actions for the four targets: component builds (`build_ui.py`), `check.py`, the packages and their probes
(macOS natively, Linux in `X/Build/Linux` images), the bounds comparison on Windows, and the front end's first Windows
run (Win32 native host).

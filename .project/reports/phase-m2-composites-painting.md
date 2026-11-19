# M2 — 3.0.1 composites, painting, Netgen and QuadWild pins, the original application compiled whole

Date: 19 November 2026. Plan: [REMAINING_WORK](../REMAINING_WORK.md) M2. Part 1 (composites, painting, pins) and part 2
(the whole original application: FrmMain, Program and the command line, `X/App`) are below.

## What changed

- **Upstream composite test scripts on the headless original Controller.** `X/Controller/Headless` gained the
  options of the original batch start that the scripts' headers use (`PrePoMax.com -f FILE -u UNITS --scriptArgs`):
  `--unit-system` starts a new 3D model in the unit system before the import (FrmMain.New, then ImportFileAsync),
  `--script-args` is the script's `sys.argv`, `--solver REGISTRY ID DIR` selects the verified CalculiX build, and
  `--default-solver-type` sets Settings - Solver - Default solver type explicitly (the original default PARDISO is
  the Intel library the non-Windows builds lack, D060; nothing is substituted silently). `X/Controller/run-upstream-scripts.py`
  runs upstream's `APIs/Python/Test_Scripts` through upstream's own header parser (`Run_Tests.py`); runs that need
  the original command line (a batch run report, the automation server, scripts that start `PrePoMax.com`
  themselves) are reported pending, never passed.
- **A recording GDI+ painting surface** (`X/Domain/WinFormsCompat/Painting.cs`). System.Drawing.Common is
  Windows-only on .NET 10 and is no longer referenced by the X domain/UI builds; `System.Drawing.Graphics`, `Pen`,
  `SolidBrush`, `Font`, `Image`, `Icon`, `Region`, `StringFormat`, `Drawing2D` (smoothing, dash styles, arrow caps,
  paths, saved states) keep the original names and signatures and record every call. A control with a Paint handler
  is painted on request (`Control.RenderPaint`, OnPaintBackground then OnPaint) and the Qt renderer replays the
  commands with QPainter (`original_controls.PaintedControl`); mouse input reaches the control as WinForms raises it.
  `TextRenderer.DrawText` records text on the surface. No original file changed.
- **FrmSection Layers tab (3.0.1 composite shell section)**: the original `pnlLayup_Paint`/`DrawLayup` draws the
  layup (hatched layers to scale, mirrored layers of a symmetric layup, the dash-dot reference surface, axis 3 as an
  arrow, layer names, the selected layer's marker) and `pnlLayup_MouseClick` selects a layer's row from a Qt click.
- **Property-grid missing values (3.0.1)**: a property whose `IMissingPropertyValues.IsPropertyValueMissing` is true
  (an empty selection region) shows its value in red with the red dot and tooltip of the original `MySite`; the
  original painter (`PropertyGridMissingValuePainter`) recolours a GDI bitmap through Win32 internals and stays
  Windows-only, the Qt grid draws the same contract.
- **Headless WinForms model fixes found by the Layers tab**: the layout deferred while a control's layout is
  suspended (`ResumeLayout(false)`) is performed when the control is created or shown, as WinForms does (the layers
  grid kept its designer bounds under the docked check box); a column added to a bound grid is bound to the property
  its `DataPropertyName` names (FrmSection's material combo box column showed no material); `Control.Focused` is
  virtual, `OnPaintBackground`, `OnMouseCaptureChanged`, `RichTextBox.OnVScroll` exist.
- **CalculiX 2.22 rebuilt for macOS ARM64** (`build.py --component solver`, gcc 16, Homebrew OpenBLAS/libgomp):
  the retained M1 build was refused after Homebrew's libomp changed.
- **Netgen**: no re-pin needed. The 3.0.1 `nglib.dll` (upstream `fcee7eaa`, 16 October 11:48) is the published
  NetgenMesher `f0ba926` (same minute); the pinned `ThirdParty/Sources/NetgenMesher/c5ecb0ba` that
  `X/Build/NativeCad` builds is `f0ba926` plus a folder rename, the LGPL licence and build-project paths (506 source
  files identical by content). `01e30ce` (16 November) is newer than 3.0.1 and waits for the next upstream sync.
- **QuadWild for macOS/Linux** (`X/Build/QuadWild`): the published fork's commit behind the 3.0.1 Windows binaries
  (upstream `aba367c6` = fork `df747a1`, 10 October) pinned by archive SHA-256, built with the fork's CMake files as
  its CI does (Release, Blossom-V off, no Gurobi), GMM from the archive cache by the SHA-224 the CMake files name.
  The executables keep the original names `quadwild.exe`/`quad_from_patches.exe`: the original sweep mesher
  (`CaeMesh/.../SweepQuadWildMesher`, run inside GmshCaller) finds them beside each other by those names, not
  through the tool manifest. `package_ui.py --quadwild` ships the runtime under the original tool identities, and
  `build_ui.py` gained the `quadwild` stage and the `vtk` stage M1 had left out.
- **One original file edited for portability** (`CaeMesh/Meshing/QuadWild/QuadWildRuntime.cs`, C# 7.3, Windows
  behaviour unchanged): `GetExtendedLengthPath` returns the plain full path off Windows; the `\\?\` prefix lifts
  MAX_PATH on Windows but is read as part of the file name elsewhere (QuadWild could not open its configuration).
## Part 2 — the original application compiled whole (`X/App`)

- **Whole assemblies.** `X/App/UserControls` and `X/App/PrePoMax` build the whole original `UserControls` and
  `PrePoMax` assemblies — Controller, Commands, all 73 forms, FrmMain, the original `Program` — on the headless
  WinForms model. The remaining original files are copied by `generate-original-forms.py` (`APP` list, source hashes,
  reviewed rewrites) into `X/App/Original`. Not compiled, with counterparts: the Visual Studio settings class (empty,
  unused), `MesherMemory.Windows`, `PythonEngineManager.Windows`, the Rpc server files (their portable copies),
  `ViewNodeSet.Windows`, and the UserControls parts that reach WinForms internals (AutoScrollTextBox,
  TabEnabledPropertyGrid, ChildMouseWheelManagedForm, MySite, PropertyGridMissingValuePainter, ColorEditorEx).
- **Reviewed Win32 rewrites** (all in the generator, each with its reason): the console/process entry points of
  `Program` (standard handles, `TerminateProcess` -> `Environment.Exit`, Ctrl+C -> SIGINT, the named cancel event is
  Windows-only because `PrePoMax.com` is the same program here), FrmMain's window-redraw suspension and its search
  for open native dialogs (the toolkit's open message boxes and file dialogs), the low-level mouse hook of the
  autocomplete list, the rich-text paragraph spacing and scroll reset of the viewport text editor. Domain:
  `MessageBoxManager` (user32 hook renaming message box buttons) has a portable counterpart.
- **Control model** (shared with the workbench): `System.Drawing.Font`/`Image`/`Bitmap` replace the model's own
  FontSpec/ImageResource (the font and image rewrites of the generator are gone); `Application` moved into the model
  with `Run`, `OpenForms`, `ThreadException`, a headless message loop (posted calls, timers, Idle) and the run handler
  of a renderer; WinForms order of control creation (user controls get `Load` when their form is shown or when they
  are added to a shown form), posted `Shown`, `Deselecting`; tool strip items notify their strip; tool strip
  combo/text boxes host real controls; MenuStrip/StatusStrip dock Top/Bottom by default; ToolStripPanel rows; tool
  tips shown on request, link behaviour, scroll properties, low-level mouse hook, clipboard images, encoded images.
  CaeMesh and CaeJob reference the model (their original projects reference System.Windows.Forms for
  `Application.DoEvents`).
- **One thread enters the renderer.** `ToolkitSynchronizationContext` is the WinForms message queue of the Qt
  thread: posted and sent calls, control notifications, timers, modal dialogs, measuring and clipboard calls made on
  other threads are queued in .NET and run on the Qt thread. Without it a background thread calling into Python
  waited for the interpreter lock held by the UI thread (a deadlock WinForms does not have). A form shown modally
  from another thread (the original splash screen) is displayed by the UI thread while the calling thread waits.
- **Start-up** (`X/App/PrePoMax/XRuntime.cs`, before `Program.Main`): PMX allowlist, executable check, runtime profile
  `PrePoMaxX.runtime.json` (Python, UI folder, tools, Gmsh). `X/App/Configure` writes it and the original settings
  file of the application folder (verified CalculiX, explicit default solver type). `PrePoMax.com` is a copy of the
  `PrePoMax` executable.
- **FrmMain in Qt** (`X/UI/main_form.py`): FrmMain is a top-level window of the generic form renderer: the model lays
  out its controls and every control is mirrored; the menu strip, tool strips and status strip are Qt menus/tool
  bars whose items are the original ToolStripItems (drop-downs filled after `DropDownOpening`, shortcuts from
  `ShortcutKeys`), the application's keys go to the original keyboard hook, and FrmMain's own vtkControl is embedded
  (`original_viewport.py` adopts it; its native view is connected once the Qt window exists).

## Evidence (macOS ARM64, 19 November 2026)

- Upstream composite scripts (`run-upstream-scripts.py --filter Composite`, P1 Python/tool profiles, the rebuilt
  CalculiX, `--default-solver-type Spooles`): `Test_Model_Composite_Sections`, `Test_Result_Composite` (ply stresses
  against the Phase 0 values, in-plane principal stresses, failure criteria) and `Test_Result_Composite_Lamination`
  (classical lamination theory on an unsymmetric 5-ply laminate) **pass**; `Test_Model_Composite_Parameters` is
  **pending** (it starts `PrePoMax.com -r/-p` regenerations: the original command line, FrmMain).
- **Part 2, the original command line** (`X/App`, P1 Python/tool profiles, the rebuilt CalculiX, settings by
  `X/App/Configure` with Spooles): upstream's own runner, `Run_Tests.py --exe <app>/PrePoMax.com --filter Composite`,
  **4 of 4 pass**, including `Test_Model_Composite_Parameters` (child `PrePoMax.com` runs: `--script`, `--save`, two
  `-r` regenerations with `-p` parameters and a `.pmp` file).
- **Part 2, all upstream scripts through the original command line** (`Run_Tests.py`, 81 runs): 36 pass, 45 fail.
  Not acceptance evidence (M4 reruns it with meshers built from the 3.0.1 sources); the failures group as: CAD
  import/meshing with the 3.0.0-era P1 NetgenMesher (the 6-faced box of `box_and_cylinder.brep` is not found; also
  failed on the headless host in part 1), PARDISO models (exit 201, D060), selection/view scripts that need a drawn
  view (a `-g No` run has no VTK window here; on Windows the original draws off screen), the automation server
  without an access token in the run's settings, and Windows-only test content (`LOCALAPPDATA`, `powershell.exe`).
- **Part 2, FrmMain in Qt** (`app_gui_probe.py`, `PrePoMax -f cube.inp -u MM_TON_S_C`, macOS ARM64): 9 checks pass —
  the 16 original menus, the menu/5 tool strips/status strip, the original vtkControl in its native widget, the `-f`
  model imported by FrmMain's own start-up, the original ModelTree showing it (37 nodes), the view drawn by vtkNative
  (scale bar, axes), Property - Material - Create opening the original FrmMain-created FrmMaterial; the run ends with
  the original "Process finished successfully".
- **Part 2, no workbench regression** from the shared control-model changes: `verify-ui.py --gui` again passes with the
  part 1 counts (C1 18, authoring 21, geometry 43, results 58, application 39, elements 27, forms 437, menu 122),
  nothing pending; `python3 X/Checks/check.py` all 7 areas pass (110 s). Linux ARM64 not rerun for part 2.
- Part 1: `verify-ui.py --gui` unattended (P1 package runtime, vtkNative runtime, macOS ARM64): generators current, services,
  GUI probes C1 18, authoring 21, geometry 43, results 58, application 39, elements 27, **forms 437** (419 + 18: the
  composite stage and the missing-value checks), menu 122; nothing pending.
- Linux ARM64, the same command in Ubuntu 24.04 (Podman, Xvfb, software OpenGL, the P1 Linux package's runtime):
  the same counts (forms 437); nothing pending.
- `python3 X/Checks/check.py`: all 7 areas pass (118 s).
- QuadWild, macOS ARM64 (Apple clang, links only Accelerate/libc++/libSystem, `config/` equal to upstream's): upstream's
  `Test_Model_Meshing_QuadWild_Transfinite`, `Test_Model_Meshing_Sweep_Transfinite`, `..._Three_Block_Mapping`,
  `..._Validity` and `..._Coverage` **pass** on the headless host with the native build, a GmshCaller built from the
  current sources (with lp_solve beside it, as packaged) and the P1 package's Netgen and Gmsh 4.13.0.
- QuadWild, Linux ARM64 (Ubuntu 24.04, g++ 13 in Podman): **not built** — compiling `quadwild/quadwild.cpp` is killed
  for memory even with one job in the 4 GiB Podman VM (the fork's README asks for more memory than the default). The
  recipe is unchanged; it needs a larger VM or the M3 CI runner.

## Open

- The packages (`package_ui.py`, P1) and the GUI probes C1–menu still run the workbench (`X/UI/workbench.py` on the
  headless FrmMain); moving them to the original application (`X/App`), and with it retiring the headless host,
  `OriginalFormHost` and `OriginalViewHost`, is the next step. The FrmMain probe covers the main window, not yet the
  workflows the eight workbench probes cover.
- FrmMain in Qt: the view renders at logical (not Retina device) pixels; tool strips wider than their designer
  widths show an overflow arrow; the window is not yet styled like the original (dark-mode palette, pre-existing).
- A `-g No` run has no VTK window, so view-dependent scripts (selection by visibility, view parameters, captures)
  fail there; the original draws its view off screen. Needs an off-screen vtkNative view.
- Linux ARM64: the FrmMain GUI and the command line were not run in Podman yet.
- QuadWild for Linux ARM64 is not built: the compiler needs more than the 4 GiB of the local Podman VM (or the M3
  CI runner).
- Upstream's `ThirdParty/quadwild-bimdf/README.md` lists an outdated SHA-256 for `quad_from_patches.exe` (NOTICE.md
  has the shipped one).
- The Qt UI follows the system dark mode in grids and lists while the original forms are light (pre-existing).

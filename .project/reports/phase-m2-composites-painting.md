# M2 (part 1) — 3.0.1 composites, painting, CalculiX rebuild, Netgen and QuadWild pins

Date: 19 November 2026. Plan: [REMAINING_WORK](../REMAINING_WORK.md) M2. This report covers the first part of M2;
FrmMain compiled whole is the remaining part (see "FrmMain whole" below).

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
- **FrmMain whole — sized, not done.** A trial compile of FrmMain.cs/.Designer/.Plotting against the headless model
  needs about 30 more original controls (ModelTree, the side panels, XYPlot, the focus strips, OutputTextBox,
  KeyboardHook through a recording low-level hook, ...) and then ~360 member gaps. The structural finding: the
  Controller, `Rpc`, `FrmAnimation` and the Advisor name `FrmMain` directly, so the whole FrmMain must be compiled
  into the same `PrePoMax` assembly as the Controller — a UI build of the whole PrePoMax and UserControls
  assemblies that replaces the headless host (`X/Controller/Host/FrmMain.cs`) and the extracted
  `OriginalFormHost`/`OriginalViewHost`. The parked generator rewrites and the `MainWindow.cs` controls are the start.

## Evidence (macOS ARM64, 19 November 2026)

- Upstream composite scripts (`run-upstream-scripts.py --filter Composite`, P1 Python/tool profiles, the rebuilt
  CalculiX, `--default-solver-type Spooles`): `Test_Model_Composite_Sections`, `Test_Result_Composite` (ply stresses
  against the Phase 0 values, in-plane principal stresses, failure criteria) and `Test_Result_Composite_Lamination`
  (classical lamination theory on an unsymmetric 5-ply laminate) **pass**; `Test_Model_Composite_Parameters` is
  **pending** (it starts `PrePoMax.com -r/-p` regenerations: the original command line, FrmMain).
- `verify-ui.py --gui` unattended (P1 package runtime, vtkNative runtime, macOS ARM64): generators current, services,
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

- FrmMain whole (the UI build of the PrePoMax/UserControls assemblies) and with it the original command line
  (`Test_Model_Composite_Parameters`, the batch report and RPC scripts).
- An early full run of upstream's 78 API scripts on the headless host (36 passed, 31 failed, 11 pending) is not
  evidence: the meshers came from the 3.0.0-era P1 package, `cube.inp` selects PARDISO, the selection scripts need
  viewport visibility, and a concurrent rebuild touched the binaries during the run. M4 reruns it cleanly.
- Upstream's `ThirdParty/quadwild-bimdf/README.md` lists an outdated SHA-256 for `quad_from_patches.exe` (NOTICE.md
  has the shipped one).
- The Qt UI follows the system dark mode in grids and lists while the original forms are light (pre-existing).

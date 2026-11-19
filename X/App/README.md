# The original application compiled whole (M2)

`X/App` builds the original PrePoMax application for macOS and Linux: the whole `PrePoMax` assembly (Controller,
Commands, every form, FrmMain and the original `Program` with its command line) and the whole `UserControls`
assembly, on the headless WinForms control model (`X/UI/FormsCompat`) and the domain libraries (`X/Domain`).

- `UserControls/` and `PrePoMax/` import the domain source lists and the copies that
  `X/UI/generate-original-forms.py` makes of the remaining original files (`X/App/Original`, shared forms in
  `X/UI/Workbench/OriginalForms`). Each copy records its source hash and every reviewed rewrite (Win32 entry points
  replaced by portable ones); `--check` fails on drift.
- `PrePoMax/XRuntime.cs` runs before `Program.Main`: the PMX type allowlist, executables checked by their execute
  permission, and the runtime profile `PrePoMaxX.runtime.json` beside `PrePoMax.dll` (or `PREPOMAXX_RUNTIME`):
  `python` (CPython 3.12 profile), `ui` (the `X/UI` folder), `nativeTools` (tool manifest), `gmshLibrary`.
  `Application.Run(FrmMain)` shows FrmMain through Qt (`X/UI/main_form.py`); with `-g No` it runs the headless
  message loop instead.
- `Configure/` writes the runtime profile and, with `--solver`, the original settings file of the application folder
  with the verified CalculiX build (and `--default-solver-type`, D060).

```sh
dotnet build X/App/PrePoMax/PrePoMax.csproj -c Release -p:VtkNativeRuntime=$PWD/X/Build/artifacts/vtk-mac-arm64/vtkNative/runtime
dotnet X/App/Configure/bin/Release/net10.0/PrePoMaxX.Configure.dll --app <app folder> --python <python.json> --ui $PWD/X/UI \
  --native-tools <tools.json> --gmsh-library <libgmsh> --solver <build-registry.json> <build id> <bin> --default-solver-type Spooles
```

On macOS and Linux `PrePoMax.com` is a copy of the `PrePoMax` executable (the Windows console launcher has no
counterpart there; Ctrl+C reaches the process as SIGINT). Upstream's runner then works unchanged:

```sh
python3 APIs/Python/Test_Scripts/Run_Tests.py --exe <app folder>/PrePoMax.com --work <dir> --filter Composite
```

The GUI probe of the original main window: `PREPOMAXX_UI_PROBE=X/UI/app_gui_probe.py PREPOMAXX_UI_PROBE_OUTPUT=<file>
<app folder>/PrePoMax -f <model> -u <units>`. `PREPOMAXX_TRACE_EXCEPTIONS=1` prints every exception with its stack (the
original prints only the message of the one that ends a run).

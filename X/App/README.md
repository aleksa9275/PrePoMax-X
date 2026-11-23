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
  `python` (CPython 3.12 profile), `nativeTools` (tool manifest), `gmshLibrary`.
  `Application.Run(FrmMain)` shows FrmMain through the Avalonia front end (`FrontEnd/`, M3-1a; the M2 Qt renderer was
  retired in M3-1b, D065); with `-g No` it runs the headless
  message loop instead, and FrmMain's vtkControl draws off screen (as the hidden original window does on Windows), so
  the vtkNative runtime is needed in both cases. HiGHS (`highs.dll.dylib` / `.so`, 3.0.2; lp_solve before) goes beside the assemblies
  and beside GmshCaller, as in the packages.
- `Configure/` writes the runtime profile and, with `--solver`, the original settings file of the application folder
  with the verified CalculiX build (and `--default-solver-type`, D060).

```sh
dotnet build X/App/PrePoMax/PrePoMax.csproj -c Release -p:VtkNativeRuntime=$PWD/X/Build/artifacts/vtk-mac-arm64/vtkNative/runtime
dotnet X/App/Configure/bin/Release/net10.0/PrePoMaxX.Configure.dll --app <app folder> --python <python.json> \
  --native-tools <tools.json> --gmsh-library <libgmsh> --solver <build-registry.json> <build id> <bin> --default-solver-type Spooles
```

A local macOS folder to work with (meshers and CalculiX; not a release package):

```sh
python3 X/App/local_app.py --package <P1 PrePoMax-X.app> --solver <solver folder> --solver-id <build id> --output X/Build/artifacts/app-mac
X/Build/artifacts/app-mac/PrePoMax-X.command [-f <model>]
```

On macOS and Linux `PrePoMax.com` is a copy of the `PrePoMax` executable (the Windows console launcher has no
counterpart there; Ctrl+C reaches the process as SIGINT). Upstream's runner then works unchanged:

```sh
python3 APIs/Python/Test_Scripts/Run_Tests.py --exe <app folder>/PrePoMax.com --work <dir> --filter Composite
```

The GUI probe of the original main window on Avalonia: `PREPOMAXX_UI_PROBE=avalonia PREPOMAXX_UI_PROBE_OUTPUT=<file>
<app folder>/PrePoMax -f <model> -u <units>` ([FrontEnd](FrontEnd/README.md)). `PREPOMAXX_TRACE_EXCEPTIONS=1` prints every exception with its stack (the
original prints only the message of the one that ends a run).

The probe areas (the retired workbench's form-level checks, on the real app: forms, geometry, results, elements):
`python3 X/App/FrontEnd/run_probe_areas.py --app <app folder> --output DIR` (or `--launcher
PrePoMax-X.app/Contents/MacOS/PrePoMax-X`). The per-form bounds comparison with the original: `X/App/Bounds`
(`Windows/BoundsWindows.csproj` on WinForms with the original `PrePoMax.exe`, `Bounds.csproj` on FormsCompat,
`compare.py`).

Packages (no PyQt, no installed .NET; the native components come from `X/Build/package_ui.py` or a P1 package):

- macOS ARM64: `python3 X/App/package_mac.py --p1 <components> --original <PrePoMax 3.0.1 release> --output DIR --zip`
  makes `PrePoMax-X.app`; its launcher (`bundle_launch.py`) clones the app into `~/Library/Application Support/PrePoMax-X`
  and runs the original Configure step there.
- Linux (ARM64; x64 with the per-architecture native builds): `python3 X/App/package_linux.py --p1 <components
  tar.gz> --original <release> --output DIR --archive` makes `PrePoMax-X/` and `PrePoMax-X-linux-arm64.tar.gz`
  (data in `~/.local/share/PrePoMax-X`; `share/install-desktop-entry.sh` adds the menu entry). Build the vtkNative
  and QuadWild runtimes for Linux in the build container (`X/Build/Linux/Containerfile.build`).

Both pin the .NET runtime of `X/Build/targets.json`, ship the original icons, help, material library and example
models, and check every native fingerprint after packaging.

Checks (`X/Checks/check.py` area `app`): `python3 X/App/verify-app.py --output OUT.json [--launcher L --scripts]` —
sources and build, and with a launcher the app probe, the four probe areas and four of upstream's Python tests. On
Linux a Podman session gives the display (`X/Build/Linux/session.py start --package DIR --work W`, then
`--launcher W/launch.sh`; `--vnc` for a person's check over `vnc://localhost:5901`). The session mounts only the
package and the work folder, so the repository is out of reach of the app under test.

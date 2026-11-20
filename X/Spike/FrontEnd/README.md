# M3-1 toolkit spike: Avalonia front end (D065)

`PrePoMaxX.FrontEndSpike` runs the original `Program.Main` of X/App with Avalonia 11.3.23 as the front end, in one
.NET runtime: no CPython, no pythonnet, no GIL. XRuntime (PrePoMax.dll's module initializer) reads the runtime profile
as for the Qt front end; the spike then replaces `Application.RunHandler`.

What it does, deliberately generic and incomplete:

- the WinForms message queue (`ToolkitSynchronizationContext`) is drained by an Avalonia timer on the main thread;
- every original form gets a window whose client area mirrors the FormsCompat control tree: a canvas per control at
  the bounds the control model lays out, with menu strip, tool strips (original resource icons), status strip,
  buttons, labels, text boxes, tree views and tab headers; everything else is an empty frame;
- `Form.ShowDialog` opens the form's window and runs a nested `Dispatcher.UIThread.MainLoop` until the form closes;
- the original `vtkControl` is an Avalonia `NativeControlHost`: VTK creates its OpenGL view in the host's native
  window (`VtkNativeHost.AttachNativeWindow`), and Avalonia's pointer, wheel and key events go to the interaction
  style (`VtkNativeView.HandleInput`), as in `X/UI/original_viewport.py`.

Not in the spike: the property grid, data grids, the code editor, context menus, paint replay, and the layout engines
of dotnet/winforms; all of these follow the toolkit decision.

## Run

```sh
DOTNET_ROLL_FORWARD=Major dotnet build X/Spike/FrontEnd/FrontEnd.csproj -c Release \
  -p:VtkNativeRuntime=$PWD/X/Build/artifacts/vtk-mac-arm64/vtkNative/runtime
PREPOMAXX_RUNTIME=<profile without "ui"> DOTNET_ROLL_FORWARD=Major \
  dotnet X/Spike/FrontEnd/bin/Release/net10.0/PrePoMaxX.FrontEndSpike.dll -f <model> -u MM_TON_S_C
```

`PREPOMAXX_SPIKE_PROBE=<file.json>` makes the run unattended: after `PREPOMAXX_SPIKE_PROBE_DELAY` seconds (default 4)
it records the measurements, captures the view before and after a middle-button drag and the Avalonia part of the
window, and closes; a modal dialog is closed by its accept button (or Close) after 1.5 s. Delete `history.pmh` from
the output folder after a run.

Results: [the M3-1 report](../../../.project/reports/phase-m3-1-front-end.md).

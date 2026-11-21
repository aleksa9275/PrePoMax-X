# The Avalonia front end of the original application (M3-1a, D065/D067)

`PrePoMaxX.FrontEnd` draws the original application of X/App with Avalonia 11.3.23 in the application's own .NET
runtime: no CPython, no pythonnet, no GIL in the drawing path. `XRuntime` (PrePoMax.dll) hands `Application.Run`'s
main form to `AvaloniaFrontEnd.Run`; the M2 Qt renderer (`X/UI/main_form.py`) stays selectable with `"frontEnd": "qt"`
in the runtime profile or `PREPOMAXX_FRONT_END=qt` (a `PREPOMAXX_UI_PROBE` that names a `.py` probe also selects it).

The original forms run unchanged on the headless WinForms control model (`X/UI/FormsCompat`), which lays the controls
out and owns all behaviour. The front end mirrors it (the C# successor of `original_forms.py`, `original_controls.py`
and `main_form.py`):

| File | What |
|---|---|
| `FrontEnd.cs` | Run, the WinForms queue on the Avalonia loop, notifications to windows, input in the WinForms context, modal forms (nested loop), original images (files, `.resx` base64, encoded, drawn) |
| `FormWindow.cs` | A window per form: nested canvases at the model's bounds; activation (`Form.Activate`), focus (`RaiseEnter`/`RaiseLeave`), every key to the original key hook, Enter/Escape as dialog keys, size and location |
| `Controls.cs` | Buttons, check/radio boxes, labels, link labels, text/combo/numeric boxes, track and scroll bars, progress bars, pictures, group boxes, tab headers, splitters, list views |
| `Strips.cs` | Menu strip, tool strips (checked state, drop-downs, combo and text boxes), status strip, context menus (`ContextMenuStrip.Show`), menu shortcuts |
| `TreeAndCode.cs` | The tree view and FastColoredTextBox (code editors, FrmMain's output window, autocomplete) drawn from the model's rows, lines and style runs |
| `DataGrid.cs`, `PropertyGrid.cs` | Data grids on the model's geometry (selection, editing, keys, clipboard); the property grid with the original converters and UITypeEditors |
| `Painting.cs` | Paint handlers (recorded GDI+ calls) replayed on Avalonia's DrawingContext; ZedGraph plots |
| `ViewHost.cs` | The original vtkControl in a `NativeControlHost`: device pixels, overlays scaled (D066), input to the interaction style |
| `Services.cs`, `Look.cs` | Message boxes, file/folder/colour dialogs, timers, text measurement, clipboard, screens; the compact WinForms-like light theme |
| `Probe.cs` | Unattended checks of FrmMain (below) |

## Probe

```sh
PREPOMAXX_UI_PROBE=avalonia PREPOMAXX_UI_PROBE_OUTPUT=<dir>/probe <app folder>/PrePoMax -f <model> -u MM_TON_S_C
```

The report (`probe.json`, view and window images) covers the checks of `X/UI/app_gui_probe.py` and those of M3-1a: a
drag turns the view, FrmMaterial's property grid, Escape through the key hook, the view's context menu at the click
point in control units, a modal form, tool button states. `PREPOMAXX_TRACE_FRONT_END=1` traces start-up and every sync. `PREPOMAXX_TRACE_VIEW_SIZE=1` traces the
view's sizes and native frames. `PREPOMAXX_WINDOW_CAPTURE=<prefix> PREPOMAXX_WINDOW_CAPTURE_AT=<seconds,...>` saves
images of the app's own windows as the screen shows them, the VTK view included (macOS lets an app capture its own
windows without the screen recording permission).
Builds set `AVALONIA_TELEMETRY_OPTOUT=1` (Avalonia's build telemetry).

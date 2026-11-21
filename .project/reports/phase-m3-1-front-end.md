# M3-1 — one runtime for the front end (D065)

Started 20 November 2026, macOS ARM64. In progress.

## Toolkit spike

The spike ([X/Spike/FrontEnd](../../X/Spike/FrontEnd/README.md)) runs the original `Program.Main` of X/App with an
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
| Seen in the manual runs, not toolkit questions | The view's overlays (scale bar, axes) are placed in control units while VTK draws in device pixels: the front end must choose its DPI model (units = device pixels, as a DPI-aware WinForms app on Windows, or VTK at logical size). The model tree overlaps its tab buttons (layout: the dotnet/winforms engines). FrmMain's output window is a text box without its messages yet. Fluent's controls are larger than the WinForms designer sizes (compact density helps; real styling is renderer work) |
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

## Next

The X11 run on Linux ARM64; the start-up stall; then the decision is recorded and the renderer moves into
X/App: the generic control mirror with the dotnet/winforms layout engines, paint replay, the property grid, data grids
and the code editor; the bounds comparison; probes and packages on X/App.

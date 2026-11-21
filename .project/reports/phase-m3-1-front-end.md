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

## Next

The maintainer chose Avalonia and macOS first (D067). M3-1a: the renderer moves into X/App on macOS and must match
and better M2's Qt front end (steps in [REMAINING_WORK.md](../REMAINING_WORK.md)); M3-1b: Linux on the local Podman
machine. This report continues with M3-1a.

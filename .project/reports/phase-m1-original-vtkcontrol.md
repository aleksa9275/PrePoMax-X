# M1 — the original vtkControl on vtkNative, macOS and Linux

Date: 18 November 2026. Plan: [REMAINING_WORK](../REMAINING_WORK.md) M1 (D063). The 3D view of X/UI is now
the original `vtkControl`, compiled whole, drawing through upstream's `vtkNative` on VTK 9.7.1; the interim
Python VTK renderer is gone.

## What changed

- **VTK recipe** (`X/Build/Vtk/`): VTK 9.7.1 pinned by SHA256 (`source-lock.json`) with upstream's
  `vtk-9.7.1-ssao-background.patch`, shared/Release with only the modules `vtkNative/CMakeLists.txt` needs;
  vtkNative built on it; `runtime/` holds `libvtkNative` and the VTK libraries it loads (rpath
  `@loader_path`/`$ORIGIN`) plus the receipt `vtk-build.json`. Built on macOS ARM64 and in Podman for Linux
  ARM64 (Ubuntu 24.04, 61 VTK libraries).
- **vtkNative made portable** (original C++, minimal): the three Win32 window files are `#if defined(_WIN32)`;
  elsewhere `vtkNativeRenderWindow` is the platform's `vtkRenderWindow` (Cocoa, X11). `CopyRuntime.cmake`
  follows symlink chains. New `src/vtkNativeX11.cpp`: on X11 an embedded view leaves the mouse and keys to the
  parent window (as VTK's Cocoa view does) and the new C API `vtkn_view_process_events` lets the host pump the
  view's own display connection (exposure, size, and the interaction style's selection and smooth-zoom
  timers); a no-op on Win32 and Cocoa. Links libX11 on Linux only.
- **vtkControl compiled whole** (`X/Domain/vtkControl`): the whole assembly except four Windows-only originals
  (`Native/VtkNativeHost.cs`, `Native/VtkNativeLibrary.Windows.cs`, `vtkMaxLookupTable.Windows.cs`,
  `Tools/AviWriter.cs`), each replaced by a portable X file of the same API: `VtkNativeHost.Portable.cs` (the
  native window of a Qt widget as parent; macOS click-through for VTK's NSView), `VtkNativeLibrary.Portable.cs`
  (`NativeLibrary.Load` + import resolver), `AviWriter.Portable.cs` (uncompressed RIFF AVI; the Video 1
  compressor and its dialog are Windows only), `TexturePng.cs`. Original files touched: `VtkNativeLibrary`
  became a partial class with its Win32 loader split out; `PrecisionTouchpad` returns early off Windows. The
  ActiViz-era extracts moved to `Legacy/` (`LegacyPolyTopology`, `PolyDataSink`) for the headless host.
- **Headless WinForms model**: real native-window attach/detach (`OnHandleCreated`, `HandleDestroyed`),
  `UserControl.Load`, `AxHost`, VisualStyle elements, `Application.Idle` and message filters.
- **The view half of FrmMain** (`X/UI/Workbench/OriginalViewHost`): `generate-view-host.py` copies the 137
  `IControllerHost` members of the original FrmMain that drive `_vtk` unchanged (with `--check` and source
  hashes); five mixed members keep only their view statements; `SelectBaseParts` stays with the toolkit.
  The headless FrmMain routes the controller's view calls there (`ViewHost`). Marshalled calls are queued for
  the UI thread; `OriginalViewHost.WaitFor` runs them while a UI-thread caller waits on a controller task (the
  original forms `await` those tasks; the generated geometry rules' synchronous `OnApply`/`Preview` use it).
- **Qt embedding** (`X/UI/original_viewport.py`): a native Qt widget whose window parents VTK's OpenGL view;
  size in device pixels; mouse, wheel (per 120 notch) and keys forwarded to the original interaction style
  (`vtkn_view_handle_input`); a 10 ms pump on X11.
- **Interim renderer removed** (15 files, about 1,100 lines; the whole change is +731/−2,089 plus new files): `scene.py`, `presentation.py`, `qt_viewport.py`,
  `view_features.py`, `glyphs.py`, `contours.py`, `scale_widget.py`, `area_selection.py`, `avi_writer.py`,
  the color-map and presentation-rule generators and the follower-camera copy. Views, box zoom, capture
  (`RenderToPNG`), animation frames/export, edge modes, section/follower views and annotations call
  vtkControl. Ogg Theora export (an X addition) left with it; the original exports PNG and AVI.
- **One VTK per package**: the `vtk` 9.5.2 wheel left `X/UI/requirements/*.txt` (nothing imports it; Python VTK and
  VTK 9.7 cannot share a macOS process anyway, both define `vtkCocoaGLView`). The macOS app shrinks from 1.2 GB to 831 MB.
- **Port defects found and fixed on the way** (ours, not original bugs): a UI-thread deadlock when a geometry
  form committed synchronously while the controller task called the view; the area pick passed `list(None)`
  for its missing direction, so box selection was silently dropped (vtkControl swallows exceptions from its
  event handlers — the workbench now keeps them and the probes raise them after a gesture); the original
  FrmAnimation's frame no longer reached the toolkit; the scale bar had no length unit
  (`FrmMain.SetScaleWidgetUnit`).
- **Probe expectations moved to the original renderer** (not loosened): vector/tensor plots replace the part's
  own actor (vtkControl names them after the part), so the probe requires the render command, the part actor
  and a changed picture; BC/load symbols live in the overlay layer that the name lists omit, so the picture
  with the step's symbols must differ from `SymbolNone`; element edges are thin lines, measured as pixels
  darkened against the model-edge picture; tree mouse-over must change the picture and leaving must restore it.
  Probes drive the view through real pointer events (Cocoa events on macOS, Qt events on X11) and read
  vtkControl/vtkNative state (`view_probe.py`).
- `verify-ui.py --gui` requires `--vtk-native DIR`; `package_ui.py --vtk-native DIR` ships the runtime in
  `app/` with a manifest component.

## Evidence (18 November 2026)

- macOS ARM64, `verify-ui.py --gui --package <P1 app> --vtk-native <mac runtime>`, unattended: generators
  current (incl. `original-view-host`), services, GUI probes C1 18, authoring 21, geometry 43, results 58,
  application 39, elements 27, forms 419, menu 122; nothing pending. Same counts as M0 on the interim renderer.
- Linux ARM64, Ubuntu 24.04 in Podman, the P1 Linux package's Python and tools, Xvfb with software OpenGL,
  same command with the Linux runtime: the same eight GUI probes pass with the same counts; nothing pending.
- `python3 X/Checks/check.py`: all 7 areas pass (domain, controller, ui, core, analysis, execution, results;
  117 s).
- Package: `package_ui.py --target osx-arm64 --vtk-native <mac runtime> --format app` from the retained P1
  inputs, without the `vtk` wheel; `package.json` lists the vtkNative 9.7.1 component (125 files, receipt
  hash). The app's own `--geometry-probe` passes (43 checks). CalculiX is **missing** from that test package: the guard refused the
  retained solver build because Homebrew's `libomp.dylib` changed since it was fingerprinted (environment
  drift; the solver needs a rebuild, `build.py --component solver`). No Linux package was built (the
  task0050 builder image is gone; the verification above used the P1 Linux package's runtime).
- Not run: Windows (upstream's own build; the portable files are not compiled there), Linux x64, a physical
  Linux desktop (Wayland/XWayland, GPU drivers), original-app comparison.

## Open

- A minimal embed script (not the workbench) exited with signal 11 at interpreter teardown; the workbench and
  every probe exit cleanly through `detach()`. Kept as a known teardown-order issue.
- The vtkNative changes (Win32 guards, X11 input/pump) are candidates for an upstream contribution (M5).

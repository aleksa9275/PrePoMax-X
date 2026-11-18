# VTK 9.7.1 and vtkNative for macOS and Linux

Upstream's 3D view is `vtkNative` (folder `vtkNative/`), a C++ library on VTK 9.7.1 behind a flat C API that
the original `vtkControl` calls. Windows builds it with Visual Studio as the repository README describes. This
recipe builds the same sources on macOS and Linux:

    python3 X/Build/Vtk/build.py --archive-cache /abs/cache --output /abs/new-output --jobs 12

- VTK 9.7.1 is downloaded into the cache when missing and checked against `source-lock.json`; upstream's
  `vtkNative/patches/vtk-9.7.1-ssao-background.patch` is applied. VTK is configured shared and Release with the
  modules `vtkNative/CMakeLists.txt` asks for (upstream enables whole module groups; the same modules are
  linked). Linux needs `build-essential cmake libx11-dev libxt-dev libxcursor-dev libgl-dev`.
- vtkNative is built with its own CMakeLists.txt. Its post-build step copies `libvtkNative` and the VTK
  libraries it loads into `<output>/vtkNative/runtime` (rpath `@loader_path` / `$ORIGIN`), with
  `VTK-Copyright.txt` and the receipt `vtk-build.json` (source, patch, options, host, hashes).
- `--vtk-prefix <output>/vtk` reuses an installed VTK of this recipe.

Portability changes to vtkNative (M1): the three Win32 window files are `#if defined(_WIN32)`, elsewhere
`vtkNativeRenderWindow` is the platform's `vtkRenderWindow` (Cocoa, X11). On X11 an embedded view leaves the
mouse and the keys to its parent window and the host pumps the view's own events with the new
`vtkn_view_process_events` (`src/vtkNativeX11.cpp`; links libX11; nothing to do on Win32 and Cocoa).

The runtime folder goes beside `vtkControl.dll` (the original practice: the `lib` folder of PrePoMax), where
`VtkNativeLibrary` loads it. On Windows `vtkNativeRenderWindow` keeps its
own window class against ActiViz.

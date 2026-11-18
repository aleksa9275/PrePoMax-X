# VTK 9.7.1 and vtkNative for macOS and Linux

Upstream's 3D view is `vtkNative` (folder `vtkNative/`), a C++ library on VTK 9.7.1 behind a flat C API that
the original `vtkControl` calls. Windows builds it with Visual Studio as the repository README describes. This
recipe builds the same sources on macOS and Linux:

    python3 X/Build/Vtk/build.py --archive-cache /abs/cache --output /abs/new-output --jobs 12

- VTK 9.7.1 is downloaded into the cache when missing and checked against `source-lock.json`; upstream's
  `vtkNative/patches/vtk-9.7.1-ssao-background.patch` is applied. VTK is configured shared and Release with the
  modules `vtkNative/CMakeLists.txt` asks for (upstream enables whole module groups; the same modules are
  linked). Linux needs `build-essential cmake libx11-dev libxt-dev libxcursor-dev libgl-dev`.
- vtkNative is built unchanged with its own CMakeLists.txt. Its post-build step copies `libvtkNative` and the VTK
  libraries it loads into `<output>/vtkNative/runtime` (rpath `@loader_path` / `$ORIGIN`), with
  `VTK-Copyright.txt` and the receipt `vtk-build.json` (source, patch, options, host, hashes).
- `--vtk-prefix <output>/vtk` reuses an installed VTK of this recipe.

The runtime folder goes beside `vtkControl.dll` (the original practice: the `lib` folder of PrePoMax), where
`VtkNativeLibrary` loads it. Platform notes: the view uses the render window VTK makes for the platform (Cocoa,
X11); on Windows `vtkNativeRenderWindow` keeps its own window class against ActiViz.

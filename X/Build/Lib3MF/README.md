# lib3mf 2.4.1 native verification profile

The original `3MF/Lib3MF.cs` declares interface version **2.4.1** and imports
`lib3mf.dll`. Phase B resolves that exact identity to an explicit native path,
checks its SHA-256, and calls `GetLibraryVersion` before export. No newer library
or PATH search is selected. This is a verification profile, not a packaged runtime.

Official inputs from [release v2.4.1](https://github.com/3MFConsortium/lib3mf/releases/tag/v2.4.1):

| Input | SHA-256 |
|---|---|
| `lib3mf-2.4.1-source-with-submodules.zip` | `4e9e1776f4dd1b3dfce684ce9bb4ad1157dadf29908a1f3aabb6cd4358bf3248` |
| `lib3mf-2.4.1-Darwin.zip` | `d3db960146af09cbde98eaafe87ecdaf7d5d22ac6a22bed286d9eb952ccc9d89` |

Mac ARM64 verification uses the official universal dylib. Linux ARM64 builds the
source-with-submodules archive, with included dependencies and no network during
compilation. Verify the input hash before extracting it into a dedicated directory.
Executed CMake recipe (replace the absolute directories):

```sh
cmake -S /absolute/source -B /absolute/build \
  -DCMAKE_BUILD_TYPE=Release -DLIB3MF_TESTS=OFF \
  -DCMAKE_INSTALL_PREFIX=/absolute/runtime
cmake --build /absolute/build -j4
cmake --install /absolute/build
```

Pass the resulting library to `X/Controller/verify-controller.py
--three-mf-library /absolute/library`. The controlled original Controller export
checks twelve cube triangles, independently decodes texture pixels and exercises
native VTK crop/smooth output. Additional source/native/notice/redistribution and
all-target package acceptance belong to the release gate. Preserve upstream's
BSD notice and all included dependency notices when packaging the runtime.

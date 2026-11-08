# Pinned PrePoMax Gmsh native build

The application baseline is **patched Gmsh 4.13.0**, revision
`4156db5d5647087b1575c3f4b8a65a891b81102b`, with static **OCCT 7.7.0**.
It is separate from Netgen's OCCT 8.0.1. Source URLs, archive names and SHA-256
digests are in `source-lock.json`. Download those two archives into a cache,
then build on the native host:

```sh
python3 X/Build/Gmsh/build.py --archives /absolute/archive-cache \
  --output /absolute/build-workspace --jobs 4
python3 X/Domain/verify-gmsh.py \
  --library /absolute/build-workspace/runtime/libgmsh.4.13.0.dylib \
  --output /absolute/new-verification-directory
```

Linux uses `libgmsh.so.4.13.0`. The build needs CMake, C/C++ compilers, Make,
Python 3.11+ and the supplied archives; it performs no downloads. Sources are
extracted unchanged and retained in the workspace. CMake 4's compatibility
minimum is supplied as a configure option, without changing upstream files.
The workspace is reusable for incremental builds; do not mix source pins there.

The receipt retains source/recipe/configuration/runtime fingerprints and exact
commands. The configuration disables GUI, OCCT CAF, OpenMP (matching the
original MSVC threading limitation), and optional external integrations; it
retains the bundled meshing implementations and uses the pinned static CAD
kernel. This is a source/adapter baseline, not proof of every original Windows
build option or mesher result. Windows/MSVC and full native mesher parity remain
pending. No new runtime has been copied into the retained preview application.

Set `PREPOMAXX_GMSH_LIBRARY` to the absolute library path. The portable adapter
requires the adjacent `gmsh-build.json`, checks revision/version/OCCT/hash, and
checks Gmsh's reported version after initialization. It never searches arbitrary
system libraries. A missing or incompatible runtime fails explicitly.

## Upgrade candidate

Gmsh 4.15.2 is pinned separately as an **unadopted candidate**. The three
PrePoMax changes from [the baseline comparison](https://github.com/PrePoMax/Gmsh/compare/gmsh_4_13_0...4156db5d5647087b1575c3f4b8a65a891b81102b)
are retained in `prepomax-4.15.2.patch`:

- preserve user transfinite curve counts;
- avoid folded triangles when splitting non-convex quads;
- use face curvature in the direction of a curve.

All three changes apply cleanly to the pinned 4.15.2 archive (the patch is
generated against those exact bytes, with zero context). Its C header keeps
the declarations of all 118 C functions used by the adapter, including the old
`gmshModelGetType` compatibility alias. This establishes source compatibility
feasibility; it does not establish identical meshing/defaults or an improvement
on PrePoMax models. The application loader continues to require the baseline.

Gmsh's GPL license and OCCT's LGPL license/exception are in the verified source
archives. Preserve those sources, notices, build inputs and any downstream
patches with a future distributed runtime. The temporary build workspace and
archives are local caches, not a completed corresponding-source distribution.

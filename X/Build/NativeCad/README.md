# Original native CAD and Netgen build

Build the recovered original command wrapper and all 141 compilation inputs
listed by its original `nglib.vcxproj`, using native C++17, CMake, make,
pthreads and zlib. macOS requires the Apple command-line developer tools.
Ubuntu build prerequisites are `g++ cmake make zlib1g-dev binutils patch`.

    python3 X/Build/NativeCad/build.py --output /tmp/native-cad --jobs 8

The first build downloads the exact OCCT 8.0.1 archive in `occt-lock.json`,
checks its SHA-256, restores the source and builds it without optional graphics,
image/video/parallel runtimes. Application-framework/data-exchange dependencies
still compile some OCCT visualization toolkits; the runtime closure copies only
toolkits actually referenced by the native executable/library graph. This
does not use those toolkits for the desktop's VTK rendering.

`--occt-archive /path/to/archive.tar.gz` works without a source download.
`--occt-prefix /path/to/occt-install` reuses an installation with this recipe's
source receipt. Generated sources, logs, OCCT installation and native binaries
stay under the chosen output. Use a separate disposable directory.

`runtime/bin/NetGenMesher` and its copied library closure can move together.
`runtime/build-receipt.json` records the source and patch identities, host,
compiler, adapter and runtime hashes. The receipt describes a local build;
it is not a signature or a full release acceptance. OCCT's verified original
archive remains in the build cache; final distribution source/relinking and
clean-machine/runtime-floor acceptance remain pending.

    python3 X/Feasibility/Cad/verify-native.py \
      --mesher /tmp/native-cad/runtime/bin/NetGenMesher \
      --inspector /path/to/PrePoMaxX.InspectVis.dll --output /tmp/native-cad-check

This checks the original L-bracket STEP and two-part BREP twice, with original
CAD identities and independently measured linear volume meshes. Native metadata
has explicitly reported bounds. Any changed display triangles must be on planes
with the same boundary, area, orientation and first moment. Source nodes, edges
and entity IDs must match exactly. The separate original `replay-import.py`
continues to require an exact decoded Windows scene and currently reports a
failure for the native visualization differences. Neither check closes the
original tetrahedron engineering gate.

The runtime folder (`bin/NetGenMesher`, `lib/`, `licenses/`, `build-receipt.json`) is what the X/App packagers
take with `--netgen` (3.0.2: NetgenMesher `01e30ce0`). The earlier Qt desktop research profile that loaded it
(`X/Desktop`) was retired with the 3.0.2 sync.

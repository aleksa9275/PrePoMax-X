# QuadWild-BiMDF (PrePoMax fork) for macOS and Linux

Upstream 3.0.1 ships Windows binaries of its modified QuadWild-BiMDF (`ThirdParty/quadwild-bimdf`, GPL-3.0) and
publishes the source at github.com/PrePoMax/QuadWild. `build.py` builds the fork's revision behind those binaries
(`source-lock.json`: commit `df747a1`, the build of upstream `aba367c6`) with the fork's own CMake files, as its CI
does: Release, Blossom-V (non-free) off, no Gurobi (commercial). GMM, the one library the CMake files download, is
read from the archive cache and checked against the SHA-224 they name.

    python3 X/Build/QuadWild/build.py --archive-cache X/Build/artifacts/archive-cache --output /abs/new-dir --jobs 8

`runtime/` is what the original `QuadWildMesherRunner` expects beside its executable: `quadwild.exe` and
`quad_from_patches.exe` (native executables under the original names, which the sweep mesher looks up), `config/` (checked against upstream's vendored `config/`), `LICENSE` and the receipt
`quadwild-build.json`. `X/Build/package_ui.py --quadwild runtime/` ships it as `tools/QuadWild` with the original
tool identities. Linux: run the same command in the Ubuntu 24.04 build container (`cmake`, `g++`, `make`).

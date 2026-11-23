# PrePoMax-X native components and packages

The application is `X/App` (the original PrePoMax compiled whole on .NET 10 with the Avalonia front end). Its
packages are made by `X/App/package_mac.py` (`PrePoMax-X.app`) and `X/App/package_linux.py` (folder and tar.gz)
from two inputs: X/App itself and a set of **native components** built here. One command builds every native
component for a target from its pinned recipe and assembles them:

    python3 X/Build/build_ui.py --target osx-arm64 --workspace /abs/ws-mac --jobs 8
    python3 X/Build/build_ui.py --target linux-arm64 --workspace /abs/ws-linux --jobs 8
    python3 X/Build/build_ui.py --target win-x64 --workspace /abs/ws-win

Stages: `Highs/` (HiGHS 1.16.0, upstream 3.0.2; lp_solve before), `Mmg/` (mmgs 5.5.2, mmg3d 5.7.0), lib3mf 2.4.1 (official
library or source build), `Gmsh/` (patched 4.13.0 + OCCT 7.7.0), `NativeCad/` (Netgen + OCCT 8.0.1), the
CalculiX solver (`build.py ... --component solver`), then `package_ui.py`. Stages are resumable per
workspace. Run each target on a matching native host (Linux x64: Podman on Windows, D059; Linux ARM64: the
local Podman machine with `Linux/Containerfile.build`). The Linux host needs the solver build tools of `ThirdParty/Build` plus
`patchelf`, .NET 10 SDK and CPython 3.12 to run the scripts. Windows takes the vendored ThirdParty binaries (Netgen,
Mmg, QuadWild, HiGHS) and may be assembled from any host; its Gmsh (MSVC build of the patched 4.13.0) and
CalculiX are pending and listed as missing. The 3D view (`Vtk/`, vtkNative) and QuadWild (`QuadWild/`) are built
with their own recipes and handed to the X/App packagers.

`package_ui.py` can also be given prebuilt inputs (`--netgen`, `--gmsh-library`, `--lib3mf`, `--highs`,
`--mmg`, `--solver-build`). Its output holds CPython 3.12.14 (python-build-standalone, `python-runtime-lock.json`)
with the hash-pinned wheels of `python-requirements/<target>.txt` (numpy), the native tools, the relocated solver,
HiGHS, `package.json` (versions, fingerprints, **missing** components) and notices. Until M3-1b it also packaged
the Qt workbench (X/UI with PyQt6, its .NET host and `package_launch.py`); that went with the Qt front end (D065).
The P1 packages (`PrePoMax-X.app`, `PrePoMax-X-linux-arm64.tar.gz` of that time) still serve as component inputs:
the X/App packagers take their Python, tools and solver, checked against their manifests, and leave PyQt and VTK's
Python modules out.

Linux (`Linux/`): `Containerfile.build` (the build environment of the recipes and `strip_rpaths.py`),
`Containerfile.run` (a plain Ubuntu 24.04 desktop: Xvfb, Mesa, Openbox, x11vnc, no development packages) and
`session.py`, which runs a package in it for the probes or for a person over VNC.

# Solver build and retention

`build.py` plans a target (`targets.json`: OS/architecture, native adapters, planned package formats) and builds its
native CalculiX solver on a matching host; `build_ui.py` runs it as its `solver` stage:

    python3 X/Build/build.py plan --target win-x64
    python3 X/Build/build.py build --target linux-x64 --component solver --jobs 2 --output X/Build/artifacts/linux-native

Cross-publication never executes the target; a build records `nativeExecution=false` and is not solver acceptance.

Generated payloads are disposable after verification/user confirmation. Retain source, small manifests/logs and
useful shared build inputs (an installed VTK or OCCT prefix a recipe can reuse); prune superseded app copies and
build intermediates promptly, keep at most one local preview candidate. Never remove user installed apps, models
or jobs as part of a build cleanup. [Retention policy](../../.project/reports/storage-cleanup.md).

Retired with the 3.0.2 sync (23 November 2026): the earlier Qt desktop preview (`X/Desktop`), its host publication
and DMG/tar.gz/deb packaging in `build.py`, `linux_deb.py` and the `verify-*.py` scripts, and the lp_solve recipe
(upstream 3.0.2 replaced lp_solve by HiGHS, `Highs/`). Their history is in git and `.project/history/`.

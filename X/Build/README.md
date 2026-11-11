# PrePoMax-X desktop packages (X/UI)

The current desktop is X/UI (original Controller, forms and engineering code on .NET 10, Qt/VTK
presentation). One command builds every native input for a target from its pinned recipe and packages it:

    python3 X/Build/build_ui.py --target osx-arm64 --workspace /abs/ws-mac --jobs 8      # -> dmg
    python3 X/Build/build_ui.py --target linux-x64 --workspace /abs/ws-linux --jobs 8   # -> tar.gz
    python3 X/Build/build_ui.py --target win-x64 --workspace /abs/ws-win                # -> zip

Stages: `LpSolve/` (lp_solve 5.5.2.11), `Mmg/` (mmgs 5.5.2, mmg3d 5.7.0), lib3mf 2.4.1 (official
library or source build), `Gmsh/` (patched 4.13.0 + OCCT 7.7.0), `NativeCad/` (Netgen + OCCT 8.0.1), the
CalculiX solver (`build.py ... --component solver`), then `package_ui.py`. Stages are resumable per
workspace. Run each target on a matching native host (Linux x64: Podman on Windows, D059; Linux ARM64: the
local Podman machine). The Linux host needs the solver tools listed below plus `patchelf`, .NET 10 SDK and
CPython 3.12 to run the scripts. Windows takes the vendored ThirdParty binaries (Netgen, Mmg, QuadWild,
lp_solve) and may be packaged from any host; its Gmsh (MSVC build of the patched 4.13.0) and CalculiX are
pending and listed as missing.

`package_ui.py` can also be given prebuilt inputs (`--netgen`, `--gmsh-library`, `--lib3mf`, `--lpsolve`,
`--mmg`, `--solver-build`). The payload holds a self-contained .NET 10.0.14 host, CPython 3.12.14
(python-build-standalone, `python-runtime-lock.json`) with the hash-pinned wheels of
`X/UI/requirements/<target>.txt`, the native tools, the relocated solver, X/UI with the original resources
it reads, `launch.py`, `package.json` (versions, fingerprints, **missing** components) and notices.
`launch.py` writes the absolute runtime profiles to the user data folder and starts the host;
`launch.py --profiles DIR` writes them for `X/UI/verify-ui.py` (repository verification with a package's
runtime; see `DIR/verify-arguments.json`). The GUI probes ship as self-checks, e.g.
`PrePoMax-X --results-probe DIR` (real solve) or `--geometry-probe DIR` (CAD, meshers).
QuadWild has no macOS/Linux build (modified fork, source not in the repository).

# Earlier shared target builds

Generated payloads are disposable after verification/user confirmation. Retain
source, small manifests/logs/reproduction evidence and useful shared build inputs;
prune duplicate app/standalone/DMG staging copies, per-build packaging caches and
test-installed app copies promptly. Keep at most the current DMG while needed
for user testing. Never remove user installed apps, models or jobs as part of a
build cleanup. [Retention policy, actual cleanup and rebuild steps](../../.project/reports/storage-cleanup.md).
Historical manifests are evidence, not a guarantee their binary payloads exist.

One source tree, four RIDs: `osx-arm64`, `win-x64`, `linux-x64`, `linux-arm64`.
`targets.json` holds OS/architecture, native adapter, executable/rendering names
and planned package formats. Null OS/libc floors and empty distro version lists
mean pending validation, not universal compatibility. Debian/Fedora/Arch share
Linux application sources; distro packages are later wrappers. Arch ARM means
the separate Arch Linux ARM environment.

    python3 X/Build/build.py plan --target win-x64
    python3 X/Build/build.py build --target osx-arm64 --output X/Build/artifacts/mac-hosts
    python3 X/Build/build.py build --target win-x64 --output X/Build/artifacts/windows-hosts
    python3 X/Build/build.py build --target linux-arm64 --output X/Build/artifacts/arm-hosts

All three managed hosts use the same projects/source and pinned self-contained
.NET 10.0.14 runtime: original INP mesh decoding, original FRD/DAT inspection and
original deck/job/monitor transport. Hosts remain in separate folders/processes
because their partial assembly closures differ. Cross-publication never executes
the target and records `nativeExecution=false`; a matching native host runs a
small common fixture smoke. Build success is not GUI, solver or installer acceptance.
Run managed publications sequentially in one checkout; they share MSBuild state.

Native solver build and common workflow (on the matching native worker):

    python3 X/Build/build.py build --target linux-x64 --component solver --jobs 2 --output X/Build/artifacts/linux-native
    python3 X/Build/build.py build --target linux-x64 --output X/Build/artifacts/linux-hosts
    python3 ThirdParty/Build/verify-workflow.py --build X/Build/artifacts/linux-native/solver --hosts-dir X/Build/artifacts/linux-hosts --output X/Build/artifacts/linux-workflow

Linux needs GCC/gfortran, CMake, make/perl, pkg-config, native OpenBLAS development
libraries, binutils/file and Python. Mac uses the retained Homebrew GCC/OpenBLAS
setup. Same pristine CalculiX 2.22/SPOOLES 2.2/ARPACK-ng 3.9.1 source and explicit
overlay/compiler flags feed both adapters. OpenBLAS reports an int32/LP64 config;
ARPACK is static/sequential/int32. Compiler/ABI/runtime/load-path hashes are
recorded; Mac Mach-O and Linux ELF inspection live in native platform helpers.
Windows native solver recovery stays pending; the existing Windows reference
registry/default is unchanged. A nonmatching worker fails before creating output.

The existing Mac package command remains usable:

    /private/tmp/prepomaxx-desktop-runtime/bin/python X/Desktop/package-mac.py --output X/Build/artifacts/mac-preview

Equivalent shared entry: `build.py package --target osx-arm64 --format app` with
the same new output argument. Use the isolated Python environment with the pinned
X/Desktop packaging requirements. Common publication builds the two reader hosts;
the Mac helper bundles Qt/Python/VTK and verifies its ad-hoc signature. Target data
is included in the app for renderer expectations. Direct embedding B002 remains;
the frame-copy viewport is still a candidate. Windows desktop packaging,
MSI/DEB/RPM/Arch package creation and clean-machine/Developer-ID tests are pending.

Local workflow preview DMG (ad-hoc app signature, no notarization):

    /private/tmp/prepomaxx-desktop-runtime/bin/python X/Build/build.py package --target osx-arm64 --format dmg --solver-build <verified-native-build> --output <new-output>
    python3 X/Build/verify-macos-dmg.py --package <package-output> --output <new-verification-output>

The explicit solver build is validated, copied with its non-system libraries,
relocated to loader-relative paths and fingerprinted under a distinct local
preview profile. The app includes all three shared hosts and the synthetic cube.
The desktop starts/cancels the original C# run-static service through QProcess;
stdin `cancel` asks the original runner to stop its solver tree. EOF is harmless.
The DMG contains installation and full uninstall/reset instructions. Image creation,
mounting and GUI tests need native macOS privileges unavailable in a filesystem
sandbox; this does not require changing Gatekeeper settings.

Add `--pmx-preview` to the shared macOS package command to bundle the checked
PMX 3.0.0 editor. **Open static PMX…** opens the result-free C3D8 subset for
modulus and axial-force edits and Save As to a new project file. The package
uses the public Microsoft NRBF decoder pinned at 10.0.14. The legacy offline
research build keeps its existing SDK decoder reference. Reopen the edited PMX
to run it through the same native job and results viewport.

[Install](../Desktop/INSTALL-macos.md) · [Uninstall and reset](../Desktop/UNINSTALL-macos.md).

## Linux desktop archive

Use native Ubuntu 24.04 with the .NET 10 SDK, CPython 3.12 and the native
solver build tools listed above. Install the preview build extras
(`python3-venv libpython3.12 patchelf`) and graphics/runtime packages:

    sudo apt-get install libgl1 libegl1 libgl1-mesa-dri libxrender1 libdbus-1-3 \
      libfontconfig1 fonts-dejavu-core libxkbcommon-x11-0 libxcb-cursor0 libxcb-icccm4 \
      libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxcb-xinput0 \
      libsm6 libglib2.0-0t64 libicu74 libssl3t64 libgssapi-krb5-2 zlib1g

Run with the matching RID (`linux-arm64` or `linux-x64`):

    rid=linux-arm64
    python3 -m venv /tmp/prepomaxx-desktop
    /tmp/prepomaxx-desktop/bin/python -m pip install --require-hashes --only-binary=:all: -r "X/Desktop/requirements-$rid.txt"
    python3 X/Build/build.py build --target "$rid" --component solver --output X/Build/artifacts/linux-solver
    /tmp/prepomaxx-desktop/bin/python X/Build/build.py package --target "$rid" --format tar.gz \
      --solver-build X/Build/artifacts/linux-solver/solver --pmx-preview --output X/Build/artifacts/linux-preview

The archive in `dist/` contains the launchable folder. Extract it intact; see
[Linux install and uninstall](../Desktop/INSTALL-linux.md). The adapter
checks the source solver and its ELF libraries against the native build
report, then relocates the compiler/BLAS libraries next to the solver. The
system supplies its loader, glibc and display stack. The archived app uses
the shared frame bridge. PMX remains opt-in.

For verification under Xvfb (`xvfb xauth`):

    LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a -s "-screen 0 1400x1000x24" \
      python3 X/Build/verify-linux-preview.py --package X/Build/artifacts/linux-preview \
        --output X/Build/artifacts/linux-preview-check

Pass `--pmx-fixture` and `--pmx-reference-frd` to additionally exercise the
retained task 0045 fixture against the task 0049 official-export solve.
The Linux x64 CI workflow exercises the archive when desktop/package inputs
change and retains reports, logs and the screenshot. It does not publish
the archive. Xvfb proves rendering and workflow behavior through a virtual
display; physical desktop, GPU/Wayland and distro support are separate.

### Ubuntu 24.04 installer preview

Wrap an existing archive build and its `package.json` on a matching Linux
worker with Python 3.12 and `dpkg-deb`. This reuses the checked application
bytes and records both archive and installer hashes.

    python3 X/Build/linux_deb.py --package X/Build/artifacts/linux-preview \
      --output X/Build/artifacts/linux-preview-deb

Use `sudo apt install ./<installer-filename>.deb` with the actual local
filename. APT resolves the declared Ubuntu runtime dependencies. Launch
**PrePoMax-X Preview** from the applications menu or run
`prepomaxx-preview`. Remove the preview with
`sudo apt remove prepomaxx-preview`. Removal and purge preserve jobs and
projects in user directories. The package version is an internal preview
version derived from the archive build time and source commit.

Run the lifecycle check as root only in a disposable Ubuntu 24.04 container
or VM with current APT indexes, `python3 xvfb xauth desktop-file-utils`, and
the source archive build available. The verifier installs with APT, checks
the menu entry, launches as an ordinary user and checks file hashes through
removal, reinstall and purge.

    python3 X/Build/verify-linux-deb.py --deb X/Build/artifacts/linux-preview-deb/*.deb \
      --package X/Build/artifacts/linux-preview --output X/Build/artifacts/linux-deb-check

Supply the same optional PMX fixture and reference FRD arguments to check the
installed PMX workflow. CI keeps reports and logs. The Ubuntu preview is one
installer proof, with Debian, Fedora, Arch and public release packaging still
pending.

Every output directory must be new. `build.json` retains source/dirty patch/input
identity, exact commands/logs, target, file hashes and native-smoke scope. The
workflow validates the staged hosts' complete regular-file hashes/target and
rejects additional symlinks before running. Known source inputs are snapshotted
through the existing safe check tooling; private models are not collected.
Binary/runtime/build caches remain ignored. Source/license redistribution closure
and native runtime relocation remain separate release work.

    python3 -m unittest discover -s X/Build -p test_build.py

Focused controls cover wrong-host/unsupported native operations, false
cross-run claims and changed/wrong-target/symlinked host evidence or missing ELF
runtime dependencies. A dedicated Linux CI job builds/solves the tiny cube when
native sources/consumers/build inputs change; GUI-only edits keep shorter checks.
Actual hosted outcomes are in the task 0041 report, not inferred from
the existence of a recipe. Full platform/historical matrices remain milestone work.

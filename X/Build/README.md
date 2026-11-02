# Shared target builds

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
the frame-copy viewport is still a candidate. Other OS desktop/package adapters,
DMG/MSI/DEB/RPM/Arch package creation and clean-machine/signing tests are pending.

Every output directory must be new. `build.json` retains source/dirty patch/input
identity, exact commands/logs, target, file hashes and native-smoke scope. The
workflow validates the staged hosts' complete regular-file hashes/target and
rejects additional symlinks before running. Known source inputs are snapshotted
through the existing safe check tooling; private models are not collected.
Binary/runtime/build caches remain ignored. Source/license redistribution closure
and native runtime relocation remain separate release work.

    python3 -m unittest discover -s X/Build -p test_build.py

Seven focused controls cover wrong-host/unsupported native operations, false
cross-run claims and changed/wrong-target/symlinked host evidence or missing ELF
runtime dependencies. A dedicated Linux CI job builds/solves the tiny cube when
native sources/consumers/build inputs change; GUI-only edits keep shorter checks.
Actual hosted outcomes are in the task 0041 report, not inferred from
the existence of a recipe. Full platform/historical matrices remain milestone work.

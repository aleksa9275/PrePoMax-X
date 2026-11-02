# macOS-first delivery from shared source

Revised 2 November 2026 under [task 0039](../tasks/0039-shared-source-delivery-plan.md).
This replaces the sequence in task 0035 using the actual 0037/0038 results.
Maintainer direction: fastest useful native Mac product, with Windows and Linux
(Debian, Fedora, Arch) designed in now and tested progressively. One source tree,
one engineering behavior, target-specific builds and packages. This is the
implementation plan; proposed commands/targets below are not implemented claims.

## Starting point and first priority

Published implementation: 384edea2; closing records: d7498f8e. The Mac ARM64 cube
runs through original definitions/deck, native CalculiX 2.22 and original FRD/DAT
readers. A packaged candidate displays its results. Current-source engineering
checks exist on Mac and GitLab Linux x64; the latest hosted result is unresolved.
The maintainer reports a failed pipeline. Its URL/job/log is requested; root cause
is not established. Earlier “hosted unverified” is not a passing result.

The first engineering action is to obtain that exact job/commit, classify the
failure (configuration, runner/setup, build, engineering assertion or packaging),
repair it and rerun the affected hosted job. Retain the failing log and one useful
regression if it exposes behavior. Do not disable Linux jobs, hide assertions or
weaken tolerances to regain green. Planning can proceed before the log arrives;
a new cross-platform checkpoint cannot be called verified until it is resolved.
Unavailable runners or CI access do not freeze independent Mac work; a shared
engineering failure takes priority over adding behavior on top of that defect.

## Shared source is the development rule

Keep original Cae*/vtkControl paths, types, assembly ownership, equations, units,
numbering and writer/reader semantics. The modern desktop uses the same shared
engineering services on every target. Preserve the legacy Windows/net48 reference
separately while its migration remains incomplete; it is not proof that the new
native desktop already runs on Windows.

- One modern desktop source/UI workflow. Platform adapters handle window/render
  embedding, menus/dialog integration, process launch, paths, runtime loading and
  installation. OS checks belong at those boundaries, not in FEM calculations.
- C# projects publish for osx-arm64, win-x64, linux-x64 and linux-arm64. The same
  source commit supplies all targets. No copied Mac/Windows/Linux application
  trees, separate feature branches per OS, or independently maintained parsers.
- Native C/C++/Fortran dependencies use pinned source plus explicit portability
  overlays and host recipes. Build matching binaries per OS/architecture; record
  toolchain, integer ABI, CPU baseline, runtime closure and actual solver dispatch.
- Dependency versions/patches are shared where available. A target-specific asset
  or justified version difference is explicit in the manifest and checked at its
  boundary. Never substitute a solver, precision or renderer silently.
- Keep the existing bounded C# process boundary while choosing the production
  viewport binding. The Qt/Python candidate packages common scripts and native
  libraries; it is not literally an all-C# compilation. A C# host would reduce
  language/runtime complexity only if its real native VTK binding is practical.

“Same source, different target” is achievable as a build contract. It does not
mean one executable for all OSes, or that all native packages can be produced on
a Mac. .NET uses portable RIDs; the current Python packager requires the target
OS. Separate native workers are expected, not separate implementations.

## Build and package contract — add next, keep small

Generalize the working Mac recipes into one target entry point with target data
and small platform helpers. Preserve current commands as wrappers during migration.
Proposed interface: `build --target <rid>` followed by `package --format <format>`;
choose actual CLI syntax during implementation, not a new build framework now.

One target manifest records RID, source/dependency pins, minimum supported OS or
Linux libc baseline, compiler/ABI settings, native asset locations and package
formats. Shared orchestration validates assets, builds, stages one payload,
records hashes and runs the common smoke command. Target helpers configure the
compiler, inspect Mach-O/PE/ELF, relocate runtimes and sign/package that payload.
Keep Homebrew paths and otool in the Mac helper; do not turn them into core APIs.

The desktop test selects expected native rendering capabilities from target data;
its current hardcoded vtkCocoaRenderWindow check is Mac proof only. Keep the
nonsequential-ID and field-value expectations identical on every host.

| Target | Native build/launch environment | Packaging layer, introduced progressively |
|---|---|---|
| macOS ARM64 | Existing Apple Silicon Mac | Self-contained .app, then signed/notarized DMG and Homebrew cask |
| Windows x64 | Native Windows worker when available | Staged portable EXE folder first, then EXE/MSI installer |
| Linux x64 | Existing native GitLab x64 worker; controlled Linux build image | Common payload/archive, then Debian .deb, Fedora .rpm, Arch PKGBUILD/package |
| Linux ARM64 | ARM64 Linux VM/container on the Mac or an ARM worker | Same source/recipe structure and required Linux ARM64 packages |

For each Linux architecture, aim to reuse one payload across the supported
Debian/Fedora/Arch baselines. Each distro has package metadata/dependency names,
not its own application implementation. Pin the oldest supported glibc/runtime
baseline before shipping; newer-host builds cannot establish older-host support.
Check Qt/VTK plugins, libstdc++/Fortran/BLAS/OpenMP dependencies and graphics/session
requirements. Do not bundle the host libc or graphics driver as a shortcut.
If a distro needs a rebuild, rebuild the same sources with an explicit toolchain
profile and explain the difference; keep the common contract and fixture corpus.

Arch is rolling and officially x86-64. Any Arch ARM package/test refers explicitly
to Arch Linux ARM; do not silently equate it to official Arch Linux. Linux ARM64
remains required independently. Select exact Debian/Fedora versions and pinned
Arch test images during target/dependency implementation; this plan asserts no
untested distro/version support or newly provisioned runners.

## Delivery sequence

| Increment | Main deliverable | Minimum evidence to advance |
|---|---|---|
| 1. Restore feedback and remove Mac assumptions | Diagnose failed CI; target manifest/shared build entry; Mac helper and Linux x64 compute build from the same commit | Affected hosted job passes; Mac artifact still launches; unsupported targets report pending, not success |
| 2. Useful native Mac preview | Resolve one bounded native-VTK host/binding attempt; model tree, open/select, job controls, contours/history and a supported save/reopen slice | Install/launch without SDK/Homebrew build paths on a clean Mac; common solid workflow; IDs/units/results preserved |
| 3. Mac engineering alpha plus portability checkpoint | Solid and shell workflows; self-contained solver/runtime layout; signed preview package | Analytical outcomes and failure/cancel behavior; Linux x64 same-source cube; Windows cross-target managed compile/package preparation when possible |
| 4. Other-target alpha | Same UI/engineering/build entry on native Windows and Linux ARM64; actual Linux desktop/package checks | Native launch/picking/solve/save/reopen on available targets; Debian/Fedora/Arch install/uninstall checks, with missing environments explicit |
| 5. Full product | Expand CAD/meshing, full original analysis/results/PMX history, performance and packaging | Full declared parity/release corpus and signed install/upgrade/uninstall on every required target |

Mac UI work is the critical path. Linux x64 compute remains a small continuous
signal while Mac work proceeds. Bring the other managed target compilations
forward as soon as the shared entry point can do them; do not wait for a completed
Mac application to discover missing platform APIs. Native Windows/ARM64 GUI and
full distro matrices are scheduled at checkpoints, not run after every edit.

Keep the existing viewer as a temporary integration harness if direct embedding
B002 remains unresolved. It must not force duplicated UI/engineering services or
be labelled the final performant renderer. Timebox the next binding attempt to
one implementation increment with a concrete build/pick/package result. If it
fails, record the exact prerequisite and present the concrete tradeoff before
expanding production dialogs; do not launch another open-ended framework survey.

Use native CalculiX 2.22/SPOOLES for the initial open CPU workflow where built and
validated. Keep the existing Windows reference identity distinct. PaStiX remains
the subsequent performance route; Code_Aster, GPU, remote workers, broad benchmarks
and new engineering features stay deferred. No backend/default/precision or
production persistence/frontend decision is silently made by this plan.

## Checks that protect portability without dominating development

| Trigger | Run | Defer |
|---|---|---|
| Ordinary Mac edit | Affected current-source checks; relevant Mac render/workflow smoke | Historical pins, all installers, all desktop targets |
| Shared engineering/build/native boundary change | Affected current checks on Mac and native Linux x64; relevant other-RID compile/source guards | Unrelated suites; full distro GUI matrix |
| Integration checkpoint | Build available target payloads from one commit; small common corpus; schedule native Windows/ARM64 checks on available workers | Full release corpus unless candidate scope requires it |
| Linux payload/dependency/package change | Debian/Fedora/Arch package/load smoke on declared pinned images | Unrelated engineering replays per distro |
| Scoped alpha/release candidate | Actual target artifact, native UI, install/upgrade/uninstall and its required workflow corpus | Nothing required for the claimed candidate scope |

Build once per source/tool/dependency/target key and test that payload; package
wrappers reuse it. Keep current suites and package caching, not a new test system.
Start with the four existing Linux engineering verifiers until the failed pipeline
is diagnosed; then split cheap compute feedback from slower packaging. No new
matrix or runner provisioning is implemented by this planning task.

Cross-publishing managed code checks dependency/target compatibility, not native
execution. Containers can check Linux loading, solver behavior and package
metadata/lifecycle; desktop graphics/input/session behavior requires real native
sessions or appropriate VMs. VM passes are labelled by actual CPU architecture;
emulation and a Mac host alone do not prove native Linux x64 behavior.

Common corpus: analytical solid, thin shell, nonsequential FEM IDs/results,
malformed input, failure/cancellation and supported save/reopen. Add one owning-
layer regression for a real defect. Retain both existing correctness failures,
the tetra measurement gate and unchanged tolerances; do not make every unrelated
change wait for their resolution. Full historical/Windows/net48/RC2/CAD/full-graph/
source/license/four-target/release requirements remain for their stated scope.

## Debugging and next actions

Every artifact/run identifies commit plus dirty-source snapshot if applicable,
RID, distro/image or OS version, runtime/ABI/dependency hashes, fixture ID/units,
solver/backend/thread settings, commands, status and retained logs/output hashes.
Use a single stable bug ID with expected/actual behavior and affected hosts.
Private models are included only with explicit user export authorization.

Next engineering order: **obtain/fix the failed hosted job → generalize target/
build staging without regressing the Mac proof → finish the bounded viewport
choice and Mac workflow → exercise the same payload/source on other targets.**
A Windows/Linux-only failure is repaired in its adapter/recipe or shared owner,
not worked around by forking the feature. Record coverage as passed/failed/not-run
per target and distinguish build, compute, GUI and installer results.

## Primary references for build constraints

- [.NET RID catalog](https://learn.microsoft.com/en-us/dotnet/core/rid-catalog): use portable OS/architecture RIDs rather than distro-specific application targets.
- [.NET publishing](https://learn.microsoft.com/en-us/dotnet/core/deploying/): self-contained publication includes the target runtime; it is distinct from target execution.
- [PyInstaller operation](https://pyinstaller.org/en/stable/operating-mode.html): bundles are built for the active target OS/interpreter. Existing project pins remain 6.16.0, not the moving documentation version.
- [Qt Linux deployment](https://doc.qt.io/qt-6/linux-deployment.html): runtime/plugin deployment and native-library loading need explicit packaging. This is not a Qt version upgrade.
- [Arch Linux](https://archlinux.org/about/) and [Arch Linux ARM](https://archlinuxarm.org/about): distinguish x86-64 Arch from the AArch64 port.

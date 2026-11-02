# Shared target builds — task 0041

Maintainer resumes the accepted shared-source/macOS-first sequence after the
verified CI repair. `X/Build/build.py` now publishes the same original C# mesh,
results and execution hosts for four RIDs, with one target catalog. Common staging,
source/dirty-patch retention, logs, file fingerprints and native smoke are shared.
Target helpers own the native/compiler/runtime/package differences. No engineering
source algorithm, dependency version, frontend/default/backend/precision policy
or application persistence format is changed.

The old Mac package command delegates to the common publisher and a small Mac
bundle helper. Renderer expectations use target data; Qt runtime version is now
reported accurately. Mac shader/input/large-model B002 work is not closed by this
build refactor; the VTK frame-copy viewer stays experimental.

The recovered CalculiX 2.22/SPOOLES/ARPACK source/patch recipe now has Mac Mach-O
and GNU/Linux ELF helpers. OpenBLAS config explicitly rejects int64 interfaces;
build reports record adapter/catalog/compiler/source/runtime identity. No stock
replacement solver or new version is chosen. Linux and Mac runtime libraries
remain external pinned dependencies until the later relocation/source-closure work.

## Local evidence

- Native Mac shared hosts publish and run the common smoke; the new solver recipe
  rebuilds the same executable SHA `c8eb0df883edff6bca85d0de05e9db188d6e08df5ed801044f31c1db7ee9b18b`.
  Its complete original deck/solve/FRD/DAT workflow passes twelve checks plus the
  existing altered-displacement control with external dotnet absent from PATH.
- The repackaged Mac app passes its ten real-frame/ID/value/resize checks and
  ad-hoc signature verification without external Python/dotnet on PATH.
- Windows x64 cross-publishing succeeds and emits PE32+ x86-64 app hosts; Linux
  ARM64 cross-publishing succeeds and emits ELF AArch64 app hosts. Neither runs
  on the Mac and neither is labelled native execution or desktop acceptance.
- Seven meaningful build-boundary controls pass. No unchanged historical matrix
  is repeated. Pristine source manifests and both known failures/tetra gate remain.

[Retained local evidence](shared-target-builds/evidence-index.json) fingerprints
the target publications, final Mac solver/workflow and Mac app/frame. The final
native recipe and Mac adapter source hashes match the solver build report.
Local build outputs and binary app/solver payloads are ignored.

## Linux and remaining coverage

The existing native Linux x64 execution job is extended with the same entry:
managed hosts → pinned native source build → common analytical cube workflow.
It retains commands/logs, runtime/build identity and synthetic result evidence;
large self-contained host directories/object files are not uploaded. No runner
or other distro/GUI job is provisioned. Actual hosted acceptance is pending until
an exact-commit run is inspected and recorded.

Debian/Fedora/Arch package formats are target metadata, not delivered installers.
Minimum OS/glibc baselines and verified distro versions are explicitly unset.
Windows native solver/package, Linux ARM64 native execution, all non-Mac desktop
sessions and direct VTK binding comparison remain. Signing/clean-machine install,
runtime relocation, corresponding-source closure, full graph/persistence/CAD/
Windows/net48/RC2 and four-target/final correctness requirements remain open.

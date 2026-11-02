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

Native Linux x64 CI uses the same entry:
managed hosts → pinned native source build → common analytical cube workflow.
It retains commands/logs, runtime/build identity and synthetic result evidence;
large self-contained host directories/object files are not uploaded. No runner
or other distro/GUI job is provisioned. The source-build step is split
into an affected-input job so GUI-only edits do not rebuild native dependencies
on every push; the original quick execution checks stay independent.

Verified observation: implementation **a893005c** is remote-verified. Exact-commit
[pipeline 3019959774](https://gitlab.com/aleksa9275/pre-po-max-x/-/pipelines/3019959774)
passes all five automatic Linux x64 jobs; compatibility is manual. The downloaded
65-entry execution artifact ZIP identifies a clean source commit and contains the
actual native build and cube results. The shared native build takes 142 seconds
on that worker; this is a build duration, not a solver performance benchmark.

The Linux executable is ELF x86-64, built with GCC/gfortran 13.3, OpenBLAS 0.3.26
LP64 on Ubuntu 24.04.5/glibc 2.39. Mac/Linux source manifests, recipe and target
catalog match. The self-contained Linux hosts run all three smokes; original
deck → native SPOOLES solve → original FRD/DAT/monitor reading passes twelve
checks and altered-displacement rejection. Four field identities, node/element
IDs and all 96 DAT history identities match Mac. Displacements match exactly;
maximum cross-host field differences are 4.06e-7 stress, 2.43e-15 force and
1.05e-19 strain, within the explicitly recorded comparison bounds. This bounded
comparison does not change the original analytical tolerances or certify other
analysis categories. [Downloaded evidence and comparison](shared-target-builds/linux-macos-comparison.json).

The CI-only split **0411ae23** is also remote-verified; its exact-commit
[pipeline 3019992604](https://gitlab.com/aleksa9275/pre-po-max-x/-/pipelines/3019992604)
passes all six automatic jobs; compatibility remains manual. Its downloaded
native artifact identifies clean 0411ae23, verifies all report links, and contains
the same native executable hash and decoded FRD/DAT values as the first run
(source-file hashes are excluded from this semantic comparison). Final hosted
outcomes are retained in [publication record](shared-target-builds/publication.json).

Debian/Fedora/Arch package formats are target metadata, not delivered installers.
Minimum OS/glibc baselines and verified distro versions are explicitly unset.
Windows native solver/package, Linux ARM64 native execution, all non-Mac desktop
sessions and direct VTK binding comparison remain. Signing/clean-machine install,
runtime relocation, corresponding-source closure, full graph/persistence/CAD/
Windows/net48/RC2 and four-target/final correctness requirements remain open.

## Next bounded increments

1. Finish one native viewport binding/host attempt (B002), including whether the
   current C# host can use a practical native VTK binding. Require a visible
   packaged frame, original FEM-ID picking, resize/lifecycle and a recorded
   larger-mesh interaction measurement. Keep the existing viewer as the workflow
   harness; if a concrete dependency blocks the attempt, record that dependency
   and the available tradeoff before expanding production dialogs.
2. Connect a small common desktop workflow: model tree/open/select, native job
   start/cancel/status and contour/history inspection, through the original
   shared C# services. Add a supported save/reopen slice explicitly rather than
   inventing or silently selecting a replacement persistence format.
3. Make the Mac preview relocatable: include the required solver/runtime closure,
   exercise a clean machine without SDK/Homebrew paths, then Developer-ID sign,
   notarize and build DMG/Homebrew delivery. Carry the same build contract to
   native Windows/Linux ARM64 and declared Debian/Fedora/Arch package checkpoints.

Routine edits run affected checks and the relevant native smoke. Full historical,
other-desktop and distro installation matrices remain integration/release work.
These are next increments, not claimed implementation or a production frontend
selection. The installable Mac workflow is the critical path.

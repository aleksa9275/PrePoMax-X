# Local macOS solver preview DMG — task 0042

3 November 2026. Maintainer requests a local-installable DMG while Developer ID
signing/notarization are unavailable, explicitly choosing desktop solver controls
before the first image. This reorders the bounded workflow/package increment
ahead of the remaining native viewport binding attempt; B002 remains open.

## Implemented boundary

The common desktop has Run static, Solve example, Cancel, status, output and Job
files controls. QProcess invokes the original C# run-static service with an INP
mesh and the existing bounded analysis JSON. It does not reimplement engineering
parsers, equations or persistence. Each run gets a new reserved workspace; the
original runner owns native execution, output/error and run.json. Successful jobs
load FRD through the original reader and display selectable contours/IDs. Closing
an active job requests cancellation and waits for cleanup. This preview does not
provide full PMX editing, CAD/meshing or arbitrary deck/analysis execution.

The C# CLI accepts an explicit `cancel` line on redirected stdin. EOF does not
cancel. The existing cancellation token/ExecutableJob process-tree handling owns
cleanup. Real Qt process tests exercise cancellation/reaping, malformed-analysis
diagnostics and tampered solver rejection. Unix CLI pipe controls also run with
the existing execution verifier on Mac/Linux; native Windows remains pending.
The original 49 transport/planning checks and 13 rejection controls are retained.

The shared package entry accepts --format dmg with an explicit verified native
Mac solver build. The unchanged 2.22/SPOOLES/ARPACK/OpenBLAS profile is copied with
its runtime closure, rewritten to loader-relative dependencies, ad-hoc signed and
rehash-pinned under a distinct local-preview build ID. Build and registry identity
must match. No original engineering source/backends/default precision change.
The copied app includes three separate self-contained .NET hosts and Python/Qt/
VTK; PyInstaller caches remain in the build output, not user Library directories.
Solver metadata lives in Resources, avoiding the Frameworks code-signing rule.

The DMG contains the app, Applications shortcut, synthetic examples, project
license, install instructions and the full uninstall/reset guide. No privileged
installer/background service is installed. User models remain external; app jobs
use Qt's per-user data location unless an explicit test root is supplied.

## Verification and publication

Preliminary packaged native cube passes eleven desktop/visible-frame/ID/field
checks without external Python/dotnet on PATH. Three Qt job-boundary checks and
eight build-boundary controls pass. Current Mac execution checks and the new
stdin EOF/cancellation controls pass; twelve original cube checks/control also
pass with the new host. Final exact-commit DMG mounted/copied-app evidence and
publication are pending and will be recorded here before task closeout.

No clean OS, downloaded Gatekeeper, older macOS, Windows/Linux desktop, final
native binding/performance or public redistribution/source-closure claim follows.
Both correctness failures/tetra gate and full four-target/release gates remain.

## Local installation and reset

[Install](../../X/Desktop/INSTALL-macos.md) and
[uninstall/reset](../../X/Desktop/UNINSTALL-macos.md) are included in the image.
Deleting a DMG is separate from deleting the copied app and its per-user jobs.
The uninstall guide identifies precise preview paths, generated test/staging
folders, optional preview crash reports and preservation of user models/results.
It does not run deletion, remove unrelated applications or change security settings.

Apple documents a per-app opening decision for unidentified/unnotarized software:
[Apple app-opening guidance](https://support.apple.com/en-gb/102445). This decision
belongs to the maintainer; no Gatekeeper/quarantine bypass is automated.
[Apple container](https://github.com/apple/container) runs Linux workloads using
lightweight VMs, not a macOS desktop guest. It can serve later Linux compute
checks, not Mac GUI/DMG/clean-macOS acceptance. This Mac reports 26.7.1; container
is not installed, and existing Podman availability does not establish this DMG.

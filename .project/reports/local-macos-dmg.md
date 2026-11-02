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

Implementation **b6ec65d722c8e0d64b8a489cdc4df8afa57973da** is committed and
remote-verified on origin/research/native-feasibility; master remains f6273e39.
The final package identifies that exact clean source commit. Native Mac verification
passes: DMG checksum/integrity; read-only mount; mounted signature; copied app in
a path with spaces; image eject; copied signature; **1,606 regular-file hashes and
1,464 symlink targets** match the manifest without escaping the app bundle.

The copied app runs the real bundled static cube with PATH=/usr/bin:/bin and an
invalid external DOTNET_ROOT. **Eleven desktop/visible-frame/ID/field checks and
seven original analytical checks pass**, as does altered-displacement rejection.
The screenshot was visually reviewed. Real Qt cancellation/reaping, preflight
failure and tampered-solver checks also pass using the host inside the copied app.
Eight build-boundary controls and the existing 49 execution checks/13 rejection
controls pass; new EOF/cancel pipe controls pass. A diagnostic real solve records
the loaded native libraries inside the copied app/system, with no Homebrew path.
The actual packaged storage paths match the uninstall guide.

Exact-commit [pipeline 3020068825](https://gitlab.com/aleksa9275/pre-po-max-x/-/pipelines/3020068825)
passes all **six automatic native Linux x64 jobs**, including the new CLI pipe
controls and native build/cube workflow. Historical compatibility remains manual.
This checkpoint's hosted artifact archive was not downloaded; do not claim an
independent hosted archive comparison. The local final DMG/copy evidence is
retained under [evidence index](local-macos-dmg/evidence-index.json).

Local deliverable: `X/Build/artifacts/task0042-macos-dmg/dist/PrePoMax-X-Preview-arm64.dmg`,
**260,297,246 bytes (248.2 MiB)**. SHA256:
`9ae8e97c283c97db7aae8c0044385a9fa0d08c15f7c5207910eafe5c1a50c606`.
An adjacent `.dmg.sha256` file provides the same checksum. The binary image stays
local/ignored; source, recipes, evidence and instructions publish normally.
It is ad-hoc signed at app level, not Developer-ID signed or notarized. A local
copied-app test is not a downloaded Gatekeeper or clean-macOS installation test.


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

## Maintainer test follow-up — 3 November 2026

Maintainer reports that the local preview test went well and as expected. Record
this as a user-reported pass on the existing Mac, without inferring a separate
uninstall, clean-OS, downloaded Gatekeeper or broader engineering corpus pass.
The next bounded engineering increment is the [native viewport boundary](../tasks/0043-native-viewport-boundary.md),
followed by an editable solid workflow, explicit supported save/reopen, then shell/
history and a portability checkpoint. No new implementation or frontend/format
choice occurs in this follow-up.

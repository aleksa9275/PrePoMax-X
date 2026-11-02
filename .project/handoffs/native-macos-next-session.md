# Native macOS continuation — 3 November 2026

Prepared for another agent at the maintainer's request. No feature implementation
is in progress. Read AGENTS.md, PROJECT.md, STATUS.md, DECISIONS.md and task 0043
before changing code. Current records supersede historical stop/uncommitted-only
instructions; D051/D053 govern the accepted continuation/publication scope.

## Checkout and publication

- Repository: `/Users/aleksa/Documents/GitLab/pre-po-max-x`.
- Reuse branch `research/native-feasibility`. Origin is the maintainer fork;
  master remains upstream mirror f6273e39983e06042ae8b06e9a3dd0f729ea4b91.
- Working implementation: b6ec65d722c8e0d64b8a489cdc4df8afa57973da.
  Evidence closeout ca4b4917; user test/next plan 31f7c755 are published.
  This handoff is a subsequent documentation-only publication; inspect actual HEAD.
- Exact implementation pipeline 3020068825 passes all six automatic native Linux
  x64 jobs. Compatibility is manual. Do not equate a later docs-only pipeline
  with a new engineering matrix. This checkpoint's hosted archive was not downloaded.
- At handoff there are no uncommitted tracked edits. Four untracked Finder files
  exist: `.DS_Store`, `PrePoMax/.DS_Store`, `X/.DS_Store`, `X/Build/.DS_Store`.
  They are not implementation or evidence; do not stage or overwrite user files.
- Commit/push useful reviewed checkpoints normally to origin research, document
  progress and verify remote/relevant CI. No upstream/master/x/main/release writes,
  force pushes or silent frontend/format/backend/precision decisions.

## What works

Task 0041 provides one four-RID catalog/build entry, common self-contained C#
hosts and native Mac/Linux CPU build adapters. Same engineering source; separate
partial assembly closures remain in separate processes. Mac ARM64 and native
Linux x64 analytical cube pass. Windows x64/Linux ARM64 managed cross-publication
passes, but their native execution/desktop acceptance is still pending.

Task 0042 supplies an internal Mac DMG with INP/FRD display, contour/ID picking,
Run static / Solve example / Cancel / status / Job files. The original C# service
builds the static deck, runs CalculiX and opens FRD through the original reader.
The supported analysis definition is the existing bounded JSON, not a new PMX
format or full model editor. Native CalculiX 2.22/SPOOLES research CPU profile and
non-system libraries are relocated into the bundle; the run uses one thread.

Copied-app verification (after image eject, path with spaces, no external Python/
dotnet on PATH) passes eleven GUI checks, seven original analytical checks plus
altered-displacement rejection. Real packaged-host cancel/reaping, malformed
analysis and binary tamper checks pass; 49 execution checks/13 controls plus new
EOF/cancel pipe checks pass. Ad-hoc signature, DMG integrity, 1,606 regular file
hashes and 1,464 symlink targets verify. This is not a clean OS/Gatekeeper pass.

Maintainer reports the local preview test went well/as expected. Separate cleanup,
clean OS and wider test details were not supplied; do not infer them. Install and
complete uninstall/reset instructions are in X/Desktop and inside the DMG.

## Local artifact and retained records

DMG (ignored/local, not uploaded/committed):
`X/Build/artifacts/task0042-macos-dmg/dist/PrePoMax-X-Preview-arm64.dmg`
260,297,246 bytes; SHA256:
`9ae8e97c283c97db7aae8c0044385a9fa0d08c15f7c5207910eafe5c1a50c606`.
Adjacent `.dmg.sha256` is available. Handoff rechecked actual image/hash and all
retained evidence-index entries. App bundle ID: org.prepomaxx.preview.

Read `.project/reports/local-macos-dmg.md`, its `local-macos-dmg/` evidence folder,
`.project/reports/shared-target-builds.md`, and `.project/bugs/B002-qt-vtk-cocoa-host.md`.
Tracked evidence travels via Git; ignored binaries/caches and the temporary Python
environment do not. On another host, rebuild instead of assuming these paths exist.

Useful current local inputs:
- Python environment: `/private/tmp/prepomaxx-desktop-runtime/bin/python`;
  pinned packaging requirements: `X/Desktop/requirements-packaging-macos-arm64.txt`.
- Verified original Mac native solver build:
  `X/Build/artifacts/task0041-final-mac-solver/solver`.
- Final copied test app/output: `X/Build/artifacts/task0042-dmg-verification/`.
- Full installation/removal instructions: `X/Desktop/INSTALL-macos.md` and
  `X/Desktop/UNINSTALL-macos.md`. Do not execute cleanup without user direction.

## Next bounded task: 0043

Task `.project/tasks/0043-native-viewport-boundary.md` records the proposed next
increment under the existing accepted sequence: one native VTK widget/host attempt,
including the practical C# binding route. Require a visible packaged frame,
original FEM IDs/scalars, real pointer interaction, resize/lifecycle and a measured
larger-mesh comparison. Do not begin another framework survey. If blocked, record
the exact prerequisite and present the concrete tradeoff before expanding
production dialogs; do not silently select the current bridge as final.

B002 remains: direct QWidget QVTK stalled in Cocoa expose/paint; QOpenGLWidget
returned valid API/picker data but a black visible frame. The current working
FrameBridge renders native VTK offscreen and copies pixels into Qt. API-only
success is insufficient. Keep this tested DMG as the integration harness.
No task 0043 implementation or production frontend decision has been made.

Later: editable solid analysis (tree/material/supports/loads without hand-editing
JSON), explicitly agreed supported save/reopen, shell/history, then native other-
target/distro integration checkpoints. Keep the Mac installable workflow critical.

## Code/build map and routine checks

- `X/Desktop/viewport.py`: current VTK frame bridge and bounded GUI workflow.
- `X/Desktop/jobs.py`: QProcess adapter; writes stdin `cancel\n` to the C# host.
- `X/Execution/Solve/Program.cs`: original-services CLI and cooperative cancellation.
  EOF must not cancel shell/CI calls. ExecutableJob owns solver-tree cleanup.
- `X/Build/build.py`, `targets.json`, `platforms/macos.py`: common publisher and
  Mac packaging/relocation/DMG. Solver binaries/metadata live in Resources; putting
  metadata in Frameworks caused a code-signing failure. Preserve registry hashes.
- `X/Build/verify-macos-dmg.py`: read-only mount → copy → eject → actual app test.
- `ThirdParty/Build/calculix-cpu.py`: pinned source native solver build; no substitute.

Run only affected checks and native smoke for the actual change. Existing commands:

    python3 -m unittest discover -s X/Build -p test_build.py
    python3 X/Checks/check.py --profile fast --area execution --output <new-check-dir>
    /private/tmp/prepomaxx-desktop-runtime/bin/python X/Build/build.py package --target osx-arm64 --format dmg --solver-build X/Build/artifacts/task0041-final-mac-solver/solver --output <new-package-dir>
    python3 X/Build/verify-macos-dmg.py --package <package-dir> --output <new-test-dir>

Use new output directories, retain source/commands/results. Native hdiutil and GUI
checks require macOS disk/window access beyond the filesystem sandbox; use the
normal approval mechanism when necessary. Never disable Gatekeeper or strip
quarantine. Apple container runs Linux, so it cannot validate this Mac GUI/DMG.
Do not repeat historical/full-platform matrices for documentation or unrelated UI
changes. Broaden at the relevant interoperability/engineering/release checkpoint.

## Still open

Both recorded element correctness failures/tetra measurement gate; B002; full
PMX persistence/model history, CAD/meshing/full graph; Windows/net48/RC2 and other
native desktop targets; Debian/Fedora/Arch install tests/platform floors; native
backend breadth/performance; corresponding-source/license redistribution closure;
Developer ID/notarization and clean-OS installation. Ad-hoc signing permits this
internal test milestone, not a claim of public/final release acceptance.

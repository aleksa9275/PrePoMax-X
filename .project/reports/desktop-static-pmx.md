# Checked desktop PMX on macOS ARM64

[Task 0048](../tasks/0048-desktop-static-pmx.md) adds **Open static PMX…**
to the opt-in macOS preview. The dialog shows the mesh size, unit system,
material and load region. It edits Young's modulus in MPa and axial force
per node in N and saves a new original PMX 3.0.0 file. Reopening reconstructs
and validates the original engineering deck. The original PMX remains intact.

The adapter snapshots up to 32 MiB of source bytes and reuses the existing
record, mesh and deck checks. Save As verifies the resulting file and both
decks before publishing the new file and refuses an existing destination.
The accepted shape is result-free full-integration C3D8 with an empty command
history and the checked material, support, load and step definitions. The
dialog is separate from the INP model tree, viewport and job path. General PMX
and the release corpus remain open under D057.

## Package and decoder

`X/Build/build.py package --target osx-arm64 --format dmg --pmx-preview`
bundles three self-contained helpers with the pinned .NET 10.0.14 runtime.
The NRBF helper uses the public Microsoft `System.Formats.Nrbf` 10.0.14
package. Its nupkg SHA-256 is
`e7d151b9e2d2d86eecaae279f0c484f4b5b8f12923118396b7ad06d6c375e86d`.
The package declares MIT and identifies source revision
`0427b9abbead3fa64c6655eb4290c537397131fa`.
The historical offline research builds use their existing SDK reference.
The package uses record decoding without BinaryFormatter or payload type
loading. Full release source and notices closure remains pending.
[NuGet package](https://www.nuget.org/packages/System.Formats.Nrbf/10.0.14).

## Verification

- The ad-hoc-signed ARM64 DMG was verified, mounted read-only, copied to a
  path containing spaces and ejected. The copied app passed 11 solve and
  render checks, seven analytical checks and the altered-displacement refusal.
  Both the frame bridge and opt-in Cocoa viewport passed 10 PMX dialog checks
  each. The PMX probes ran from outside the checkout without external build
  tools on PATH. The source identity names implementation commit `1a386d26`
  with no changed code or tracked patch. The manifest's dirty flag records
  untracked Finder metadata.
- Eight shared build tests, 14 existing desktop tests and 24 PMX framing and
  decoder tests passed on macOS ARM64.
- The shape regression passed using the three standalone helper executables.
  Repeated Save As and deck reconstruction passed. Six refusal controls covered
  the default unapproved capture, saved results, reduced integration, the
  unsupported version, nonempty command history and an existing destination.
- The desktop wrote 84,500.5 MPa and 42.25 N per node. Its file SHA-256
  `c5752e03f6a80c2b30fbf6d472cc83f7912def6bfcb1347f5aa4aefc67b36a61`
  matches the exact PMX the official Windows 3.0.0 executable reopened and
  resaved through CrossOver. That reference run matched the edited original
  deck and decoded native Mac solver fields.
  [Original application readback](pmx-3.0.0-reference/shape-workflow-original-readback.json).
- The Qt probe exercises the actual modal and its save method, with the output
  path passed directly. The native file chooser itself is outside this probe.

The historical internal image was
`X/Build/artifacts/task0048-final/dist/PrePoMax-X-Preview-arm64.dmg`,
SHA-256 `a6670a0392e618921dfcea785095c01f126765ddc35edbc8a4a1b17e12f77266`.
Sixteen generated paths were removed, including the superseded task 0047 DMG
and duplicate task 0048 app, cache and staging copies. The measured free-space
gain was 10.33 GiB. Build receipts, synthetic PMX fixtures and job evidence
were retained. [Machine-readable checks and cleanup](desktop-static-pmx-verification.json).
Task 0049 superseded and removed the task 0048 image.
[Current image and solve workflow](static-pmx-native-solve.md).

## Publication

The task 0045 and 0047 checkpoint `2a116e26` was pushed and remote-verified
on `origin/research/native-feasibility`. Exact-commit pipeline
[#3027004685](https://gitlab.com/aleksa9275/pre-po-max-x/-/pipelines/3027004685)
passed all six automatic native Linux x64 jobs. Compatibility stayed manual.

Task 0048 implementation `1a386d26` was pushed and remote-verified on the
same research branch. Exact-commit pipeline
[#3027032018](https://gitlab.com/aleksa9275/pre-po-max-x/-/pipelines/3027032018)
passed all six automatic native Linux x64 jobs, including the native solver
workflow. Compatibility stayed manual. Hosted archives were not downloaded.
The Mac DMG and original-app interoperability evidence are separate local checks.

# Native Cocoa viewport boundary — task 0043

Storage update, task 0046: generated app/DMG/test payloads below were removed at
the maintainer's request after successful testing. Verification records and hashes
remain historical; see [cleanup/rebuild process](storage-cleanup.md).

3 November 2026. **Verified observation:** an opt-in direct-render Cocoa child
view works in the copied Mac app with the existing original C# services and the
pinned VTK 9.5.2/PyQt6 6.10.0/Qt runtime 6.10.2/CPython 3.12.14 combination.
This is a bounded host proof, not a production frontend choice or full parity.
Maintainer's 3.0.0 target/future-release direction is tracked in [PARITY](../PARITY.md).

## Implementation and input boundary

`X/Desktop/native_cocoa.py` passes Qt's native NSView address to VTK's
`SetParentInfo`, rather than making Qt's view itself the OpenGL drawable through
`SetWindowInfo` as the rejected QVTK adapter did. VTK creates a separate child
NSView and renders directly into it. Qt owns the event loop and forwards input
to `vtkGenericRenderWindowInteractor`/trackball-camera style. Device-pixel scale
is applied to framebuffer sizes and pick coordinates. No per-frame pixel copy,
second model/parser, engineering algorithm or dependency upgrade is introduced.
`--viewport native-cocoa` selects this Mac-only experiment; the existing bridge
remains the default and the task 0042 DMG is untouched.

The [pinned Cocoa implementation](https://github.com/Kitware/VTK/blob/v9.5.2/Rendering/OpenGL2/vtkCocoaRenderWindow.mm)
explicitly creates a plain NSView for the parent-view path and leaves input to
the parent. The initial prototype using a native Cocoa interactor rendered but
did not deliver selection through that path. Forwarding Qt input fixes that
specific boundary. The test sends synthetic NSEvents through the app's actual
NSWindow/hit-testing, rather than invoking the picker/interactor directly.
These remain automated native-event checks, not human mouse/keyboard acceptance.

`viewport_probe.py` records click → original element/node/field value, drag →
camera rotation without selection, actual screen pixels, Retina resize and
repeated create/render/finalize/close. Native screenshots use the actual screen
rectangle: QWidget.grab alone does not capture the separate native child.
Both the visible packaged solve window and interaction screenshot were inspected.

## Packaged verification

[Retained verification](native-viewport-boundary/verification.json) passes:

- Read-only mount, signature, copy into a path with spaces, image eject and
  copied signature; **1,610 regular files/1,470 symlink targets** match the manifest.
- Copied-app native solve → FRD → displayed fields/IDs: **11 GUI checks**,
  **seven original analytical checks**, and altered-displacement rejection.
- [Native event/display probe](native-viewport-boundary/native-probe/probe.json):
  **12 checks**, including actual native-window clicks/drag, 2x Retina size,
  27,000-cell input and five native lifecycle cycles.
- [Default bridge probe](native-viewport-boundary/bridge-probe/probe.json):
  **11 checks** on the same packaged app and fixtures.
- Packaged native nonsequential-ID fixture: **eight checks**, selecting element
  7001/node 4 at (0,0,1); [report](native-viewport-boundary/nonsequential.json).
- Eight affected build-boundary and three real Qt/C# job-process checks pass.

Packaged runs use `PATH=/usr/bin:/bin`, invalid external DOTNET_ROOT and bundled
readers/runtimes. The build source identity truthfully records base HEAD
fa5494dc plus a **dirty source snapshot**, retained under
[reproduction](native-viewport-boundary/reproduction/source.patch).
All four recorded desktop source hashes were compared to the reviewed files and
independently to the published implementation's Git blobs at **7514c88c**.
This package is not described as a clean-commit build. The DMG stays local/ignored.

## Measured transport tradeoff

Same copied app, original C# decoder, generated structured C3D8 INP with
29,791 nodes/27,000 cells, same fixture hash, same **800×600 physical framebuffer**,
35 synchronous render submissions per route. Measurements are one local run:

| Measurement | Native child view | Existing bridge |
|---|---:|---:|
| Larger-mesh load including original reader | 0.196 s | 0.202 s |
| Median larger-mesh synchronous render call | 11.31 ms | 1.76 ms |
| 95th-percentile render call | 13.66 ms | 8.14 ms |
| Peak GUI-process resident memory | 348.0 MiB | 369.3 MiB |

**Inference:** direct embedding removes the readback/copy transport and supports
live trackball interaction, but these measurements do not establish a speed win.
Onscreen presentation synchronization differs from the bridge's offscreen
render/copy submission; this is not displayed FPS. Peak RSS includes the GUI
interpreter and prior probe allocations, excludes separate C# readers and is
not isolated VTK memory. No solver/CAD/general large-model benchmark is claimed.
The normal native widget renders at 2x Retina; equal framebuffer sizes above
avoid comparing it to the bridge's lower-resolution default.

## Practical C# route and concrete prerequisite

The original `vtkControl.csproj` references ActiViz **5.8.0.607 AMD64** at a
Windows installation path; no current Mac ARM64 C# binding/build is supplied in
this checkout. [Kitware's current offering](https://www.kitware.eu/activiz/)
lists Mac ARM64 binaries under its purchased-license distribution. Its
[maintainer explains](https://discourse.vtk.org/t/how-to-start-a-c-project-with-vtk/14457)
that the old open-source wrapper is unmaintained and that reproducing its
P/Invoke/lifetime layer requires substantial work.

**Architectural inference:** the all-C# viewport route requires either a
separately reviewed current binding with a suitable redistributable/build/source
closure for all four targets, or an owned native C ABI/wrapper plus host and
lifetime work. No current C# host was executed, no license purchased, no vendor
contact made and no four-target binding acceptance is claimed. This is a concrete
prerequisite, not proof C# rendering is impossible. Expanding this into a wrapper
project or dependency policy change is outside this bounded task.

**Recommendation:** use the proven original-C# service boundary and retain the
direct Mac adapter as an opt-in candidate for the next editable-solid prototype.
Keep framework/production-renderer selection explicit. The rejected QVTK paths
are not repaired; [B002](../bugs/B002-qt-vtk-cocoa-host.md) now has a verified
alternative, with full input/DPI/performance and other-target acceptance open.

## Local artifact and reproduction

New DMG: `X/Build/artifacts/task0043-native-viewport/dist/PrePoMax-X-Preview-arm64.dmg`.
260,490,618 bytes; SHA256
`c6618c3f057a0d6c42ec0d7f6d145f6f92d89560aac16956bb8aa402d2f7ee2f`.
App is ad-hoc signed; clean macOS, Developer ID/notarization and downloaded
Gatekeeper acceptance remain pending. No security settings were changed.
The tested task 0042 DMG still hashes to
`9ae8e97c283c97db7aae8c0044385a9fa0d08c15f7c5207910eafe5c1a50c606`.

Commands from the repository root (new output directories required):

```sh
/private/tmp/prepomaxx-desktop-runtime/bin/python X/Build/build.py package --target osx-arm64 --format dmg --solver-build X/Build/artifacts/task0041-final-mac-solver/solver --output <new-package>
python3 X/Build/verify-macos-dmg.py --package <new-package> --output <new-verification> --viewport native-cocoa
env PATH=/usr/bin:/bin DOTNET_ROOT=/nonexistent-external-dotnet '<copied-app>/Contents/MacOS/PrePoMax-X-Viewport' .project/reports/windows-reference/solver/uniaxial.frd --viewport native-cocoa --viewport-probe <new-probe>
```

## Publication and exact-commit hosted verification

Implementation **7514c88c7e2b4cc65825040c2b06a11df5a2ad49** is published and
independently remote-verified on origin/research/native-feasibility. Origin/master
remains f6273e39983e06042ae8b06e9a3dd0f729ea4b91. Exact-commit
[pipeline 3022061388](https://gitlab.com/aleksa9275/pre-po-max-x/-/pipelines/3022061388)
**passes all six automatic native Linux x64 jobs**; compatibility stays manual.
The signed-in pipeline page and native job log were inspected. Native job
[17695879032](https://gitlab.com/aleksa9275/pre-po-max-x/-/jobs/17695879032)
passes eight build controls, shared host publication, the native CPU build and
actual solver execution with twelve common analytical/FRD/DAT/monitor checks.
[Structured observation](native-viewport-boundary/publication.json) records jobs
and scope. Hosted archives were not downloaded or independently compared here;
Linux compute CI does not exercise the Mac viewport.

The closing follow-up changes evidence/documents only. No native Windows/Linux
GUI, stable-3.0.0 correspondence or full release acceptance follows.
Both known correctness failures/tetra gate, full persistence/history/CAD/meshing,
native backend breadth, four-target installers and source/license gates remain.

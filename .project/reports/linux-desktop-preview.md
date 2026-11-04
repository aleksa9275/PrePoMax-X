# Native Linux desktop preview

Task 0050 adds a relocatable Linux archive to the shared build entry for
`linux-arm64` and `linux-x64`. The app uses the same Qt/VTK frame bridge,
original C# readers and job host, and checked PMX editor as the Mac preview.
It requires an explicit native CalculiX 2.22/SPOOLES build. The adapter verifies
its input files and relocates the compiler and OpenBLAS libraries alongside
the solver, leaving the system glibc and loader together. The app launches
the original hosts without inheriting
[PyInstaller's private library path](https://pyinstaller.org/en/stable/runtime-information.html#ld-library-path-libpath-considerations).

The preview uses Ubuntu 24.04, CPython 3.12, hash-pinned wheels and the
existing self-contained .NET 10.0.14 runtime. Early Linux attempts identified
the Python shared library, GLib and XCB Shape build/runtime requirements.
The final recipe includes them and checks the frozen Qt X11 plugin before
archiving. [Build and verify](../../X/Build/README.md) ·
[Install and uninstall](../../X/Desktop/INSTALL-linux.md).

## ARM64 package and verification

Retained internal archive:
`X/Build/artifacts/task0050-arm64-delivery/dist/PrePoMax-X-Preview-linux-arm64.tar.gz`
(415,668,457 bytes; SHA-256
`a80ab8336b34884369a5c60783ce676b0fba2e6189adee7447eec06b4e793a41`).
It identifies implementation `b55882ec` with no source changes in the build
snapshot. The dirty flag reflects untracked Finder metadata.

Built on native-architecture Ubuntu 24.04.5 ARM64 in the Podman VM. The
archive was independently extracted to a path with spaces in a separate
Ubuntu runtime container without the .NET SDK, CalculiX or GCC installed.
All 2,149 file hashes and 244 link targets matched. Xvfb and Mesa software
OpenGL exercised the actual Qt X11 and VTK render path.

- The shipped INP example passed 11 desktop and seven analytical checks,
  including picking, field values, resize, image capture and the altered
  displacement refusal.
- All 17 static PMX checks passed. The saved file and executed deck matched
  task 0049 byte for byte. Original-reader nodes, topology and all decoded
  DISP, STRESS and FORC fields matched the task 0049 official-export solve.
- Four Qt process tests exercised the packaged solve launcher: cancellation,
  preflight failure, changed-solver rejection and frozen job inputs. Nine
  build boundary tests passed.

Only the ARM64 delivery archive remains from this task. Seventeen generated
staging, extracted and superseded payload paths were removed, with 4.84 GiB
more free space observed. Eight stopped task containers were removed. Build
manifests, logs, job folders, the screenshot, the native solver binary and
reusable images were retained.
The task 0049 Mac DMG is still the current Mac preview.
[Verification and cleanup receipt](linux-desktop-preview-verification.json).

## Publication and remaining scope

Implementation `b55882ec` was pushed and verified on
`origin/research/native-feasibility`. Exact-commit
[pipeline #3028048004](https://gitlab.com/aleksa9275/pre-po-max-x/-/pipelines/3028048004)
passed all six automatic native Linux x64 jobs; historical compatibility
stayed manual. The
[native job](https://gitlab.com/aleksa9275/pre-po-max-x/-/jobs/17742939786)
passed the 15 native solver checks, built the x64 archive with PMX tooling,
and verified the extracted INP solve, analytical result and render under
Xvfb. Its packaging and verification logs agreed on the archive SHA-256.
The retained PMX fixture and reference run were exercised on ARM64. CI
uploaded reports, logs and the screenshot; it did not upload the binary
archive, and the hosted artifact bundle was not downloaded.

Linux physical desktop, hardware OpenGL, native Wayland, distro installers
and release packaging are pending. The next packaging proof is a native
Debian-family install/uninstall using this payload. The maintainer's workflow test
remains reserved for the full candidate. General PMX/results/history,
CAD/meshing, both correctness failures, the tetrahedron gate and all release
requirements remain open. No Developer ID or notarization step is needed
for this Linux preview.

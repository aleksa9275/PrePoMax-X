# Testing PrePoMax-X

PrePoMax-X runs the original [PrePoMax](https://github.com/PrePoMax/PrePoMax) (3.0.2, upstream `master`) natively on
macOS and Linux. Only the Windows-specific layer is replaced: Windows Forms by a cross-platform control model drawn
with Avalonia, and the 3D view by upstream's VTK 9.7 native port. It is a **preview for testing**, not a release of
PrePoMax and not endorsed by the PrePoMax authors.

## Get it

| Platform | Where | How |
|---|---|---|
| macOS, Apple Silicon | [`release/macos-arm64-preview`](https://github.com/aleksa9275/PrePoMax-X/tree/release/macos-arm64-preview) | download the app (unsigned; the README shows how to open it) |
| Linux, x86-64 or ARM64 | [`release/linux-preview`](https://github.com/aleksa9275/PrePoMax-X/tree/release/linux-preview) | build it with one command (Podman or Docker), or take the ready-made ARM64 package |
| Windows | — | use the original PrePoMax |

Both are built from the tag [`preview-3.0.2-1`](https://github.com/aleksa9275/PrePoMax-X/tree/preview-3.0.2-1).

## What to test

Your own models and everyday work: opening projects (also from older PrePoMax versions), CAD import, meshing, setting
up and solving analyses with CalculiX, results, and the Python features. The x86-64 Linux build and real Linux desktops
(GPU drivers, Wayland, HiDPI) have not been tested yet; those reports help most.

New in macOS preview 5:
- **PaStiX** works (Step - Solver type), multithreaded with the CPU count of Tools - Settings - CalculiX. As in
  CalculiX on Windows, its default mixed precision can give wrong results on thin shells: set the environment
  variable `PASTIX_MIXED_PRECISION` to `0` there (its Active check box works now). SPOOLES runs on one thread on
  Apple Silicon (its multithreaded mode gives wrong results there); PARDISO is Windows-only.
- User materials from shared libraries (CalculiX external behaviours, e.g. MFront) are supported by the solver.
- **Dark appearance**: the half-circle button at the right end of the top tool bar switches between light and dark.
- Not on macOS/Linux: Tools - Bidirectional Mesh Converter (a Windows-only tool of the release).

## Report problems

Open an issue in [this repository](https://github.com/aleksa9275/PrePoMax-X/issues), not in upstream PrePoMax. Include:
the platform and version (and `uname -m` on Linux), whether you built it yourself, what you did and what happened, and
the terminal output or `~/Library/Application Support/PrePoMax-X/app/trace.info` (macOS) if there is one. A small model
that shows the problem is the most useful.

Status and plans: [`.project/STATUS.md`](.project/STATUS.md). The code changes against upstream are on this branch,
`research/native-feasibility`; PrePoMax itself is © Matej Borovinšek, GPL-3.0.

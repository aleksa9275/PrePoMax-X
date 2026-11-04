# PrePoMax-X development entry point

Project status and next work: [STATUS](../.project/STATUS.md).
Final repository layout and release branch: [repository map](../.project/REPOSITORY_LAYOUT.md).
Native installer/Homebrew requirements: [release delivery](../.project/RELEASE.md).

| Build | Current purpose |
| --- | --- |
| [Analysis](Analysis/README.md) | Original engineering data, complete bounded C3D8 static deck and regression checks |
| [Execution](Execution/README.md) | Native process lifecycle and pinned solver preflight/run seam |
| [Results](Results/README.md) | Original ASCII/binary FRD C3D8 static mesh/field inspection and invariants; full FeResults/DAT graph remains pending |
| [Core](Core/README.md) | Earlier offline mapping/data/element/mesh checkpoint and development ZIP |
| [Desktop and packages](Build/README.md) | Internal macOS DMG and Linux desktop archive with the native static workflow |
| Feasibility | Historical scoped experiments and reference-capture tools |

These are development tools, not the installable desktop release. Engineering
sources remain in their original owning folders and are source-linked by the
modern build projects. Never mix partial-build DLLs with an original installed
application. [Recovered third-party source](../ThirdParty/Sources/README.md)
is separate from ignored downloaded packages, build outputs and binary artifacts.

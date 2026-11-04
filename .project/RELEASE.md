# Installable PrePoMax-X release delivery

As of 4 November 2026, the local macOS ARM64 DMG has passed copied-app
verification and native static solve. Task 0048 adds opt-in desktop Open and
Save As for a result-free static-solid PMX subset. Task 0047 proved named-set
creation, native solve and result display through the desktop INP workflow.
[PMX desktop](reports/desktop-static-pmx.md) ·
[INP desktop](reports/session-named-set-authoring.md).

Task 0049 adds the reopened static PMX model to the Mac viewport and native job
workflow. [Task 0050](reports/linux-desktop-preview.md) adds an internal Linux
archive for the shared desktop and checks the extracted workflow under X11.
Linux distro installers and physical desktop acceptance remain pending.
The full 3.0.0 release requires broader PMX, model, results, CAD and
meshing coverage, resolution of
both recorded correctness failures and the quadratic-tetrahedron gate, verified
3.0.0 source correspondence, and the native platform and installer checks below.
The maintainer's workflow test is reserved for a fully operational 3.0.0 parity
candidate. Notify the maintainer when Developer ID and notarization need their
involvement.

2026-11-02 scheduling: the [accelerated plan](proposals/accelerated-native-delivery.md)
brings an internal installable desktop preview forward, followed by a scoped
engineering alpha. Verify each artifact's stated capabilities; neither is final
parity. The full product and public release requirements below remain unchanged.

Accepted maintainer requirement, 2026-10-18 (Europe/Belgrade). The end product
is an installable native **desktop application** with the mesh/model/deck/solve/
results, interactive rendering, persistence and CAD/native-tool capabilities
required for parity. A framework-dependent development CLI ZIP is an engineering
checkpoint and does not satisfy this requirement.

| Target | Required user-facing delivery |
|---|---|
| Windows x64 | EXE installer or MSI; native application executable |
| macOS ARM64, Apple M-series | Application bundle in DMG (or an equivalent native package); signed and notarized for ordinary distribution |
| Linux x64 | DEB and RPM, or reviewed equivalent native distribution packages |
| Linux ARM64 | Same native package coverage as Linux x64 |
| Homebrew | Maintained project tap: macOS application cask; Linux formula or equivalent Homebrew route, verified on both required Linux architectures |

Intel Macs and 32-bit x86 remain outside scope. Homebrew upstream inclusion is
not assumed: the project's tap must provide a usable installation route first.
Exact installer technology, Linux distribution/runtime floors and package naming
will be selected after measured frontend/native dependency closure; these are
not new frontend or numerical-engine choices.

## Release acceptance

- A user installs and launches without a development SDK or source checkout.
  Bundle required redistributable runtime/native tools or declare and verify
  suitable package dependencies; preserve exact versions, licenses and sources.
- Include launch/menu integration, icons, file associations where supported,
  writable user settings/cache locations and correctly located solver/mesher/
  rendering/Python resources. Installation paths may include spaces/non-ASCII.
- Validate install, first launch, an end-to-end analysis, save/reopen, upgrade
  with user data preserved and uninstall on clean native machines for all four
  targets. Validate Homebrew install/upgrade/uninstall separately.
- Every artifact identifies source commit, version/RC channel, architecture,
  checksums, runtime/native dependency closure and corresponding source/notices.
  Development/RC packages cannot silently replace a stable installation.
- Windows signing/trust and macOS Developer ID signing/notarization are release
  tasks, with signing credentials kept out of Git. Test downloaded macOS packages
  with ordinary Gatekeeper settings and the native library closure.
- Preserve the existing correctness gates and full native Windows/net48/RC2,
  persistence/history/composite/CAD/VTK/source and four-platform acceptance.

The maintainer is willing to enroll in the Apple Developer Program for Developer
ID. This is a future distribution dependency, not a prerequisite for the current
source-linked engineering build. No enrollment, credential handling or store/
package publication is performed by recording this requirement.

Primary distribution references, checked 2026-10-18:
[Apple Developer ID](https://developer.apple.com/developer-id/),
[Apple packaging](https://developer.apple.com/documentation/xcode/packaging-mac-software-for-distribution),
[Homebrew package routes](https://docs.brew.sh/Adding-Software-to-Homebrew),
[Homebrew cask cookbook](https://docs.brew.sh/Cask-Cookbook).

Implement package layout/provenance checks as soon as a runnable host exists;
create the real native installers once the desktop/native closure is known.
This keeps packaging a tracked acceptance requirement throughout development.

## Source organization and public release branch

Accepted maintainer clarification, 2026-10-18: the final repository must include
all third-party corresponding source in organized component/version directories,
with patches, licenses, build recipes and binary/source fingerprints. The
[repository map](REPOSITORY_LAYOUT.md) defines the incremental source layout and
planned `x/release` public release lane. Package managers and installers consume
versioned immutable artifacts from reviewed release commits, with corresponding
source/checksums/notices available. Research branches and floating development
ZIPs are not public package channels. No branch/publication is performed here.

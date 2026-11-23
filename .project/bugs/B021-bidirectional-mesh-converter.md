# B021 — Tools - Bidirectional Mesh Converter is missing on macOS/Linux (open, needs upstream)

Found in the release audit of 23 November 2026 (D070). The 3.0.1 release ships
`Tools/BidirectionalMeshConverter.exe`, which FrmMain's Tools menu starts (`Globals.BidirectionalMeshConverter`,
upstream `6338c886`). It is a Windows PyInstaller build of a Tk program on meshio 5.3.5 (modules `convert_mesh`,
`intermediate_model`), by a third party; its source is not in the PrePoMax repository or public on GitHub.

Our packages do not ship it, so the menu item reports "The Bidirectional Mesh Converter was not found". It cannot be
built for macOS/Linux without the source. To do: ask upstream (maintainer's step) for the source and its licence, then
package it with the bundled Python (3.12, Tk available) as on Windows.

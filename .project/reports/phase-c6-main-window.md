# Phase C6 — original main window menu, viewport defects, limits

Date: 10 November 2026. Follows the 9 November review
([REMAINING_WORK](../REMAINING_WORK.md)). Strategy: D062 (reuse original code).

## Main menu parity

`X/UI/generate-main-menu.py` extracts the original `FrmMain` main menu into
`X/UI/original_main_menu.json`: 16 top-level menus in original order, every item's
text, shortcut and click handler, release visibility (`#if !DEBUG` hides Test and
both STL Crop items) and, for each handler, the original entity selection
(`SelectOneEntity`/`SelectMultipleEntities`, title, Controller getter, step level,
minimum/maximum) plus what the original helper does (confirmation text, Controller
command, form). `verify-ui.py` checks the file is current (`original-main-menu`).

`X/UI/main_menu.py` rebuilds the menu bar from that file and maps each handler to
the live original Controller command or the existing Qt editor for the original
form. Ported original behaviour:

- `FrmSelectEntity` (one/many, preselection from the tree, min/max messages) and
  the single-entity shortcut; two-stage step → item selection.
- Original confirmations ("OK to delete selected …", conditional propagate
  overwrite, merge checks via `AreModelPartsMergeable`/`AreResultPartsMergeable`).
- `SetMenuAndToolStripVisibility`: top-level menus per Geometry/Model/Results view,
  File/Tools/Results item enabling.
- `vtkControl` standard views (Front/Back/Top/Bottom/Left/Right, Isometric quadrant
  rule, Normal, Vertical). **Repaired:** the previous Camera menu used a Z-up
  convention; the original is Y-up (Front looks along −Z with +Y up).
- Color annotations (exclusive colorings vs combinable symbols, All Symbols) and
  item-ID display (`ShowItemIdsEnum` rules).
- Original export filters/format resolution (`ExportFormatTools`), Bidirectional
  Mesh Converter launcher (same "not found" error when `Tools/` lacks the tool).

PrePoMax-X-only actions (projection, Output panel, tree expand/collapse, select by
IDs, automation submenu, presentation dialogs) remain, placed after a separator in
the closest original menu.

## Visible defects repaired

- **Scale bar:** ported `vtkMaxScaleWidget` (`X/UI/scale_widget.py`): 400 px,
  five alternating fields, G4 labels with the model length unit, 320 px from the
  left, relative centre on resize. It no longer overlaps the status block.
- **Unit system status:** original "Unit system: …" status-bar label.
- **Decimal separator:** Qt default locale now follows the original
  `RuntimeInitialization` (invariant culture, no group separator): `30.00°`.
- **Result selector:** original sizing (fit the selected name, 125–400 px; drop-down
  as wide as the longest name). The text is the original result name.

## Defects found by the new checks and repaired

- File › Export › 3MF from the menu failed (`ViewExport3mfFileProperties` imported
  from the wrong namespace); the C5 probe had called the service directly.
- Switching to Results view without results crashed in `ResultsSession.Tree`
  (original shows an empty results tree).

## Inventory and limits

- Parameter commands (`CAddParameter`, `CReplaceParameter`, `CRemoveParameters`)
  are reached in the original only through the Python API; verified through the
  Qt script panel → **C**. Six commands are never constructed by the original UI
  (old-history compatibility types or controller-inserted); marked as such.
  Commands: 230/237 C. Forms remain 0/72 accepted.
- Restricted PMX reader: fixed caps (512 MiB, 2 M records, 32 M array slots) would
  refuse large original projects. Limits now scale with the input (one record per
  byte, eight array slots per byte, floors kept, 64 GiB bound); allowlist and
  depth limit unchanged. New checks round-trip >2 M records and >32 M elements.
- AVI: the original writes through `vtkAVIWriter` (Video for Windows, AVI 1.0),
  so the portable writer's 2 GiB refusal matches the original's practical limit;
  only the Windows codec dialog remains a native-Windows item.

## Original bugs recorded (D061, not changed)

- Tools › Arrange Annotations and Remove Annotations are disabled by
  `SetMenuAndToolStripVisibility` and never re-enabled in 3.0.0; mirrored.
- View › Color Annotations › Defined Fields is wired to the Loads handler (works
  through the sender; recorded).

## Checks (Mac ARM64, 10 November 2026)

- `python3 X/Checks/check.py`: all 7 areas pass (101 s), including 22 restricted
  persistence checks (new: >2 M records, >32 M array elements).
- `X/UI/verify-ui.py` with the explicit Python, native mesher, Gmsh 4.13.0,
  lib3mf 2.4.1 and CalculiX 2.22 profiles: source generators current (incl.
  `original-main-menu`); services C1 20, C2 33, C5 31, C3 25, C4 41 pass.
- GUI probes: C2 authoring 18, C4 results 35, C5 application 39 and the new
  **C6 menu 48** pass. Menu: 313 items, none unmapped; smoke pass ran 292 distinct
  items (442 runs in Geometry/Model/Results views) with no mapping error; the one
  refusal is the original "It is not possible to preview this load type."
- **Not passing here:** the two synthetic native-pointer checks (C1 "dispatched
  pointer resolves original element", C3 "native pointer picks original CAD part").
  C1 fails identically with all C6 Python changes stashed, so it is not a C6
  regression; posted Cocoa events likely need the test window frontmost, which a
  background run cannot force while the machine is in use. Re-run when the
  desktop is idle; these stay open until they pass.
- B011 "analytic double stress" remains **failed** (unchanged, D061).
- Not run: Linux ARM64/Xvfb, native Windows, CrossOver reference comparison of the
  menu.

# B017 — CalculiX environment variables cannot be switched on or off (fixed 23 November 2026)

Found by the maintainer in the macOS previews 3 and 4 (Tools - Settings - CalculiX - environment variables).

The original FrmGetEnvVars binds a `List<EnvironmentVariable>` to a DataGridView with auto-generated columns. WinForms
generates a check box column for the Boolean `Active`; the portable control model (X/UI/FormsCompat) generated a text
box column for every property, and the Avalonia grid had no check box cell, so `Active` could not be toggled.

Fix: FormsCompat generates `DataGridViewCheckBoxColumn` for `bool`/`bool?` properties, as WinForms does, and
`ToggleCheckByUser` flips and commits a check box cell (CellValueChanged follows); the Avalonia grid draws check box
cells and toggles them on a click. The forms probe area checks the original FrmGetEnvVars (check box column drawn; a
click switches `PASTIX_MIXED_PRECISION` off and on). Other forms with Boolean grid columns get the same behaviour.

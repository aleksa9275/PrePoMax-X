# Per-form bounds comparison, original 3.0.1 and X/App (M3-1a, 21 November 2026)

Tool: `X/App/Bounds` — one `Dump.cs` (C# 7.3) built twice: `Windows/BoundsWindows.csproj` (.NET Framework 4.8,
WinForms, loads the original `PrePoMax.exe` by path) and `Bounds.csproj` (.NET 10, X/App on FormsCompat). Every
`Form` class of PrePoMax and UserControls is constructed as the application constructs it (reference arguments
null), every container's pending layout runs top down, and every control's bounds are written. `compare.py`
compares the two files control by control (path of names).

Reference: `PrePoMax v3.0.1 dev.zip` from prepomax.fs.um.si (SHA-256 `76b3aae4cdef2c91e1a15fba46c0b924b63d59c76bb840937e2dab96e283cce8`),
run in the CrossOver bottle `PrePoMax-X-reference-2.6`. **That bottle has no Microsoft .NET Framework: CrossOver
runs .NET programs on Wine Mono, whose WinForms is a separate implementation, with Wine's fonts (no Segoe UI).**
It is evidence, not the Windows reference; the same tool runs on the Windows CI runner in M3.

## Result

82 original form classes, 81 in X (`ChildMouseWheelManagedForm` is not in X/App's UserControls build); 15 are not
constructed with a null controller, identically on both sides (FrmMain and 14 forms that read the controller in
their constructor). 66 forms, 566 matched controls, 108 differences — all explained by the reference runtime:

| Category | Differences | Cause |
|---|---|---|
| AutoSize text measured with Wine's substitute font | 63 | Labels, check and radio boxes measured by Mono with another font (X keeps the designer's Segoe UI 9 sizes) |
| Font-height controls 21 vs 23 px | 18 | Single-line text, numeric and combo boxes and the menu strip take their height from the font |
| Frame offset | 12 | Mono's window frame gives 25 forms an 8 × 5 px larger client area; anchored controls move with it |
| Unselected tab pages | 11 | Mono sizes only the selected page; WinForms sizes every page to the display rectangle (X does) |
| TableLayoutPanel cell offset | 3 | Mono places cells 1 px off WinForms' rule (cell + margin, no border) |
| GroupBox caption | 1 | Docked child below the caption: Mono's font is 2 px lower |

The comparison found four FormsCompat layout gaps, fixed before this run: Minimum/MaximumSize were not applied
(FrmSplash stayed expanded at 420 px instead of 280), forms started at 0 × 0 instead of WinForms' 300 × 300, a new
`Padding` did not lay the children out again (docked property grids in tab pages ignored the page padding), and
docking ignored `DisplayRectangle` (a group box's caption area; scrollable controls' padding). The table layout
gained WinForms' cell borders and its rounding rule (the last percent strip takes the remainder).

Files: `original-3.0.1.json`, `x-app.json`, `comparison.json` (every difference), `comparison.md` (per form).

# B023 — The in-place text editor is not laid exactly over the view text on macOS and Linux (open)

Found 26 November 2026 while merging upstream `58b6a6a1` (M3-3). Upstream's commits `03952685` and `58b6a6a1`
("Draw the text of the view with a Windows font and lay the in-place text editor exactly over it", "Keep the text of
the in-place editor still while typing makes it grow") place `ViewportEditorRichTextBox` pixel-exactly over the text
it edits (annotations, legend limits, the new colour bar title). They do it with the Windows rich edit and GDI:
`EM_GETRECT` for the formatting rectangle, `GetTextMetrics` for the font descent, `EM_SETPARAFORMAT` with a first-line
spacing and a start indent, `WM_SETREDRAW` and `HideCaret`/`ShowCaret` while formatting, and
`GetPositionFromCharIndex` for the line widths.

## Port today (compiles, no Win32 calls)

Reviewed rewrites in `X/UI/generate-original-forms.py` (recorded in the header of
`X/App/Original/UserControls/TextBoxes/ViewportEditorRichTextBox.g.cs`):
- `EM_GETRECT` gives the whole client area; `WM_SETREDRAW`, `HideCaret`, `ShowCaret` do nothing;
- the GDI descent is 0.212 of the font size (Arial's descent);
- `TextBoxBase.GetPositionFromCharIndex` (FormsCompat) measures the line before the character and puts lines a font
  height apart.

The front end draws the box as an Avalonia `TextBox`: it does not apply the recorded paragraph format (line spacing,
first-line spacing, start indent; `RichTextBox.LineSpacing` is stored, not drawn). So the editor opens at the text's
box but its text is not on the view text's baseline and does not keep the view's line pitch. Editing and committing
work as before. Not yet checked by hand in the running app.

## To fix (after parity, D061, unless it bothers use)

Let the front end draw the rich text box with the recorded paragraph format (first-line height, line pitch, start
indent) and the font family and pixel size `SetTextFont` gives it, and give `EM_GETRECT`, the descent and
`GetPositionFromCharIndex` from the Avalonia text layout instead of the estimates. Compare with the Windows 3.0.2
build once it is released.

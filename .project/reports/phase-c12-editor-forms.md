# Phase C12 — code editor forms, beam elements, Command base

Date: 11 November 2026. REMAINING_WORK §1.2–1.3. Strategy: D062, as
[C9](phase-c9-original-forms.md)–[C11](phase-c11-child-forms.md).

## What runs

- **FrmCalculixKeywordEditor and FrmEditCommands compiled whole** (70 of 72 classes), with the original
  `CalculixInpTextBox`, `PythonEditorTextBox` (+ its syntax highlighter, script analyzer, completion and
  autocomplete helpers) and `FrmViewObjectProperties` (opened by a double click in the history grid).
  Edit → Edit History and Edit → CalculiX Keywords (menu and model tree) now open the originals through
  `FrmMain.tsmiEditHistory_Click` / `EditCalculiXKeywords` (with `CheckValidity`); the C5 toolkit history and
  keyword dialogs are no longer reachable. 69 forms are ABC.
- `X/UI/FormsCompat/FastColoredTextBox.cs`: a model of FastColoredTextBox 2.16.24 (Pavel Torgashov, LGPLv3)
  written from its documented behaviour (not its source): lines with per-character style layers, `Place` /
  `Range` (text, regex `SetStyle`/`ClearStyle`, fragments, caret moves), undo commands with auto-undo groups,
  TextChanging/TextChanged/TextChangedDelayed/SelectionChanged, the default `HotkeysMapping`, typed characters
  (InsertChar clears a selection first, auto indent, auto-completed brackets), bookmarks, `AutocompleteMenu`
  and the Find/Replace forms. Drawing follows FCTB: only the first text style of a character draws.
- `SplitContainer` model (orientation, splitter distance and width, fixed panel, minimum sizes, collapsed
  panels, splitter moves), `Control.ProcessCmdKey` bubbling to the form, WM_CHAR → KeyPress after an
  unsuppressed KeyDown, DataGridView `CellMouseDoubleClick`, and grid row deletion governed by
  AllowUserToDeleteRows and the data source (WinForms: ReadOnly blocks cell edits only; the C10 model
  wrongly blocked deletion on read-only grids).
- Renderer (`original_controls.py`): `CodeEditor` draws the model's lines, style runs, selection, caret,
  current line, line numbers and bookmarks; keys and characters go to the model as WM_KEYDOWN/WM_CHAR (the
  platform keyboard layout supplies characters for the original's user32 `ToUnicode`); the main window's
  shortcuts do not take keys from an original form. Autocomplete popup and splitter dragging.
- Generator rewrites (listed in each output, line counts kept): `System.Range` alias for
  `FastColoredTextBoxNS.Range`, style brushes/fonts as colours/font descriptions, the autocomplete helper's
  user32 keyboard calls, and the keyword editor's user32 `LockWindowUpdate` (painting only).
- **Beam elements (ABC)** through the original UI on the CAD cube: Delete Faces (original FrmSurfaceOperation,
  async `SurfaceOperationCommandAsync`) leaves an open shell whose 4 boundary edges are free 2-node edge cells —
  VisFileReader builds them only as `LinearBeamElement`s, which FeMesh converts to edges and drops. A Netgen
  Mesh + Meshing Parameters (second order, midside nodes off geometry) mesh of the shell is converted by
  PrePoMax ("Converting mesh to second order...", `FeMesh.LinearToParabolic`): 30 parabolic triangles and
  3-node edge cells from `ParabolicBeamElement`s.
- **Commands/Base/Command (ABC)**: the abstract base runs with every command (name, date, time span, history
  text, PMX fields, Python journal fallback); 231 commands C.

## Found during the port

- **lp_solve is missing on macOS/Linux.** The default Meshing Parameters mesh of a CAD shell runs GmshCaller's
  interval assignment, which loads `lpsolve55.dll` (lp_solve 5.5.2.11, vendored for Windows only); on the Mac
  profile it fails with "could not be loaded". Netgen meshing of the same shell works. lp_solve 5.5.2.11 for
  macOS/Linux belongs to the X/UI packaging (REMAINING_WORK §2).
- The Python side panel and `FrmPythonStop` belong to FrmMain: the watchdog shows the stop window on a second
  UI thread while panel Python runs on the main window's thread.

## Evidence (Mac ARM64, 11 November 2026)

- `forms_gui_probe.py` (C12 steps in `forms_gui_probe_editor.py`, 327 checks without the native profile):
  keyword editor — tree and 118-line .inp preview, keyword lines blue and comment lines green, a Qt click on a
  keyword node fills the keyword box, Add keyword, Qt typing (click, Ctrl+A, text, Enter), Ctrl+Z, the 500 ms
  preview update, OK stores the user keyword (`SetCalculixKeywordEditorStateCommand`). History editor — every
  command in the grid, View → Python shows the read-only script (comments green italic, keywords blue), the
  selected command's lines selected, a Qt double click opens FrmViewObjectProperties ("Command Properties"), a
  row-header click + Delete removes the row, Cancel keeps the history.
- `geometry_gui_probe.py`: the beam steps above (native profile).
- Full verification: see STATUS.md.
- Not run: Linux, native Windows, CrossOver side-by-side comparison.

## Open

- FrmMain and FrmPythonStop; FrmSelectEntity reachability (the original menu handlers that call it and their
  ~210 FrmMain targets).
- Not modelled: FCTB folding, column selection, macros, word wrap layout, drag-and-drop of text, hints and
  tooltips; IME.
- The C1–C5 toolkit dialogs and legacy menus the originals replaced are still built and checked directly
  (`application_gui_probe.py`); retire them with the clean-organization pass.

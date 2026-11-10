# Phase C10 — data grid forms compiled whole

Date: 10 November 2026. REMAINING_WORK §1.3 (72 forms), second family. Strategy: D062, same
approach as [C9](phase-c9-original-forms.md).

## What runs

- **Four more original forms compiled whole**: `FrmAmplitude`, `FrmDistribution`,
  `FrmResultFieldOutput`, `FrmResultHistoryOutput`, with their base form
  `FrmPropertyDataListView`, the original grid `DataGridViewCopyPaste` (cut/copy/paste/plot,
  data-only clipboard format, autocomplete hook, error messages) and the plot window
  `FrmDiagramView` (`UserControls/DiagramView`). 43 original form classes are now compiled
  whole; 42 forms are ABC.
- `X/UI/FormsCompat/DataGrid.cs`: headless `DataGridView` / `BindingSource` / `DataObject`
  model with WinForms semantics: columns generated from the bound list's item properties
  (`DisplayName` → header, the property's `TypeConverter` formats and parses cell text), the
  new row while `AllowUserToAddRows`, a commit there adds the item through the binding source
  (`List<T>` or `DataTable` → `DataView`), parse/commit failures go to `OnDataError`, Ctrl+key
  input reaches `KeyDown` before `ProcessDataGridViewKey`, Delete removes rows selected through
  their row header, `GetClipboardContent` follows `ClipboardCopyMode` (header text only with
  header-selected rows), and the clipboard keeps a data object's private formats while it
  still holds its text.
- `X/UI/FormsCompat/ZedGraph.cs`: the ZedGraph members `FrmDiagramView` uses (pane, curves,
  titles, legend, axis minima); the renderer draws them. `AutocompleteMenuNS` stand-in keeps the
  original item list, the attached edit control and the `Enabled` rule.
- Compat fixes found on the way: a `TabPage` added through `TabControl.Controls` (designer
  code) joins `TabPages` as in WinForms; `Form.Show(control)` takes the control's form as
  owner; the renderer builds every page a form ever added and shows the tabs `TabPages` lists
  (the forms remove and re-add pages per item type).
- Generator: `UserControls.Properties.Resources` table; designer images stored in a form's
  `.resx` (`ComponentResourceManager.GetObject`) are read by the renderer from the original
  `.resx` (base64 image bytes, nothing deserialized); form icons are the application's.
  Reviewed rewrites are listed in each generated file.
- Renderer (`original_forms.py`): `DataGridWidget` (cells, new-row marker, column widths and
  fill, alignment, selection with header-selected rows, cell editor through `BeginEdit` /
  editing-control text / `EndEdit`, Ctrl+C/X/V/P and Delete, the original context menu with
  its icons), `GraphWidget` (curves with circle symbols, nice 1-2-5 axis steps, titles,
  legend) and a fragment completer for the original autocomplete items (`=` equations).
  The grid's clipboard is the platform clipboard.
- Host: the menu handlers `tsmiCreateDistribution_Click`, `tsmiCreateAmplitude_Click`,
  `tsmiCreateResultFieldOutput_Click`, `tsmiCreateResultHistoryOutput_Click` and the edit
  entry points are extracted verbatim; menus and the model tree open these forms through them.

## Found and fixed

- File → Export → History Output opened a history viewer in the port; the original opens
  `FrmExportFileWithProperties` with the history sets (`tsmiExportResultHistoryOutput_Click`,
  now the original handler).

## Evidence (Mac ARM64, 10 November 2026)

- `forms_gui_probe.py`: Create Distribution / Create Amplitude open through their FrmMain menu
  handlers at the designer size; Cancel changes nothing. Amplitude workflow through the Qt
  cell editor and the original grid: headers from `AmplitudeDataPoint` with model units, the
  new row, an equation cell (`=2*0.5`), an invalid value (original message; the cell stays in
  edit mode with the text as in WinForms, Escape cancels and keeps the value),
  Ctrl+C (data only, tab separated), Ctrl+V of space/tab separated rows at the new row,
  Ctrl+P → `FrmDiagramView` with the selected curve, header axis titles and
  `StartPlotAtZero`, plot hidden on close, the context menu items and resx icon, OK → original
  `AddAmplitudeCommand` with the edited and pasted points; edit mode, a header-selected row
  copies with header text and Delete removes it, OK replaces the amplitude.
- `results_gui_probe.py`: after a real CalculiX 2.22 solve, `FrmResultFieldOutput` (types
  Limit / Envelope / Equation / Coordinate System Transform) creates the `=2*STRESS.S11`
  equation output; `FrmResultHistoryOutput` From Table with values typed into the original
  grid, kept across property edits (`UpdateTableDataFromGrid`), creates the table history.
- `python3 X/Checks/check.py`: all 7 areas pass (101 s).
- `X/UI/verify-ui.py` with the explicit Python, native mesher, Gmsh 4.13.0, lib3mf 2.4.1 and
  CalculiX 2.22 profiles and `--gui`: generators current (incl. `generate-original-forms.py
  --check`) and the UI audit (43 compiled whole); GUI probes C1 18, authoring 20, geometry 31,
  results 39, application 39, elements 27, forms 312, menu 122. Nothing pending.
  B011 "analytic double stress" remains **failed** (unchanged, D061).
- Not run: Linux, native Windows, CrossOver side-by-side comparison.

## Open

- Owner-drawn `TabPage.Paint` handlers do not run (they need GDI+); the data-grid forms use
  theirs to select cell (0,0) when the Data points page is first painted.
- Autocomplete popup look (a Qt completer shows the original items), light WinForms theme,
  HiDPI; side-by-side comparison with the original application; Linux/Windows runs.
- Remaining 29 forms: `PrePoMaxChildForm` forms, plain dialogs and FrmMain.

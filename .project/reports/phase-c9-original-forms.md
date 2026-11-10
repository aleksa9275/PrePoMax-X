# Phase C9 — original forms compiled whole

Date: 10 November 2026. REMAINING_WORK §1.3 (72 forms), first and largest family.
Strategy: D062. Instead of extending the toolkit dialogs that reused selected members of each
form (C2–C5 "form rules"), the original form classes now run unchanged.

## What runs

- **39 original form classes compiled whole**: the 37 `FrmProperties` / `FrmPropertyListView`
  forms (BC, Load, Constraint, Section, Step, sets, surfaces, reference points, coordinate
  systems, contact pairs, initial conditions, outputs, defined fields, model/part properties,
  translate/rotate/mirror/scale, split solid/shell, offset face, surface operations, repair,
  periodic faces, mesh setup, boundary layer, remeshing, thicken shell, split mesh, merge nodes,
  element quality, capture viewport, export with properties, view object properties),
  `FrmNewModel` and `FrmSelectItemSet`, plus the original base forms (`FrmProperties`,
  `FrmPropertyListView`, `PrePoMaxChildForm`), `ListViewWithSelection`, `UnitAwareTextBox`,
  `MultiIntegerTextBox`, `ItemSetDataEditor`, `SinglePointDataEditor` and `IFormBase`.
- `X/UI/generate-original-forms.py` copies these sources into `X/UI/Workbench/OriginalForms/`
  with their SHA256 and `#line` mapping to the original file; `--check` fails on any upstream
  change. Reviewed rewrites: `new System.Drawing.Font(` → `FontSpec` (GDI+ is Windows-only on
  .NET 10) and the Windows-only `ViewNodeSet(Form, …)` overload → `ViewNodeSet(…)` (it only
  forwards). `PrePoMax.Properties.Resources` becomes a table of original image files.
- **FrmMain form hosting, verbatim**: `OriginalFormHost.g.cs` is extracted by Roslyn from
  `FrmMain.cs`: form construction, `AddFormToAllForms`, `ShowForm`, `SetFormLocation`,
  `CloseAllForms`, `itemForm_VisibleChanged/Move`, `SelectionChanged`, `UpdateHighlight`,
  the transformation pick routing of `_vtk_SelectPointOrArea`, every create/edit entry point
  of these forms (`CreateBoundaryCondition`, `EditNodeSet`, `TranslateModelParts`, …), the
  operation callbacks (`TranslateGeometryPartsAsync`, `PreviewEdgeMeshAsync`,
  `SplitPartMeshUsingSurface`, `ExportUsingFileProperties`, …) and the new-model members.
  Routing lines of forms not compiled yet are omitted and listed in the file header;
  `form is FrmAnimation` is the only host rewrite.
- `X/UI/FormsCompat`: headless WinForms control model (Control/Form/GroupBox/Button/
  CheckBox/RadioButton/TextBox/ListView/PropertyGrid/TabControl/ToolStrip…) with WinForms
  anchoring/docking, layout suspension, modal `DialogResult`, `ListView` collection sharing,
  and a `PropertyGrid` with `CategorizedAlphabetical` ordering of the original invisible
  ordering prefixes. `TabEnabledPropertyGrid` and `ChildMouseWheelManagedForm` are stand-ins
  (the originals use WinForms internals); the stand-in keeps the original Tab rule, first-item
  selection and autocomplete item list.
- `X/UI/original_forms.py`: Qt renderer — draws the control tree at the designer geometry
  (Segoe UI 9 pt metrics), mirrors control notifications, and feeds user input back through
  the WinForms events. `X/UI/original_form_host.py` connects the host hooks (working state,
  menu enabling, highlight, capture, output) and the original picking path: while an item form
  is open, viewport and area picks go through `Controller.SelectPointOrArea` with the original
  `GetSelectionPrecision` rule (7 px), then `PickedIds`/`SelectionChanged`.
  `UiSynchronizationContext` resumes the forms' `async` handlers on the UI thread, current only
  while original form code runs (as during WinForms message dispatch).
- Menus, tree and toolbars now open these families through their `FrmMain` entry points
  (`open_original`); the toolkit dialogs remain for forms not compiled yet (materials, surface
  interactions, step controls, parameters, amplitudes, distributions, analyses/results forms,
  presentation forms, application tools).

## Found and fixed during the port

- Viewport picks inside forms bypassed the original `Controller.SelectPointOrArea` (port's own
  selection nodes); now original.
- New model properties used an X dialog; now the modal original `FrmNewModel` through
  `SelectNewModelProperties`/`SetNewModelProperties`/`IfNeededSelectAndSetNewModelProperties`.
- Export to 3MF and Capture Viewport As used X dialogs; now the original forms.
- Probe expectations that described the port, not the original, were replaced: the original
  mesh-setup OK is synchronous; the original zero-load message is "must not be equal to 0".

## Evidence (Mac ARM64, 10 November 2026)

- `forms_gui_probe.py` (`--forms-probe`, run by `verify-ui.py --gui`): every compiled form
  opened through its original `FrmMain` entry point (28 model-view and 14 geometry-view entry
  points) — original `ShowForm` title, client size equal to the designer size (including
  `FrmLoad`'s constructor height), drawn at that size, Cancel hides the form and
  `FrmSelectItemSet` and adds no history; `FrmStep`/`FrmBC` created through type list and
  grid; edit mode (title with name, preselected type, disabled list, OK - New hidden, edited BC
  `Internal` until Cancel); OK - New creates and prepares again; `FrmSelectItemSet` collapsed
  geometry-only state. 276 checks with the native CAD/Gmsh profile; without it the geometry
  forms and Gmsh-based element quality are reported pending.
- The C2 authoring, C3 geometry, C4 results, element and menu probes now drive the original
  forms (`form_driver.py`): original `FrmLoad` rejection and edit, `FrmNodeSet` with a viewport
  pick ([2,3,6,7]), `FrmSection` region rules, `FrmMeshSetupItem` with a native pointer pick,
  `FrmTranslate`, result `FrmPartProperties`, mass/spring/support/gravity/damping forms.
- Inventory: 38 forms ABC (A: builds; B: runs without WinForms; C: reachable in the UI with
  executed evidence). `FrmViewObjectProperties` compiles but is used only by `FrmEditCommands`
  (not compiled yet), so it stays `-`. V remains 0. Audit: 39 forms marked `compiledWhole`.
- `python3 X/Checks/check.py`: all 7 areas pass (102 s).
- `X/UI/verify-ui.py` with the explicit Python, native mesher, Gmsh 4.13.0, lib3mf 2.4.1 and
  CalculiX 2.22 profiles and `--gui`: generators current (incl. `generate-original-forms.py
  --check`); GUI probes C1 18, authoring 20, geometry 31, results 36, application 39,
  elements 27, forms 276, menu 122 (313 items, none unmapped, no mapping errors). Nothing
  pending. B011 "analytic double stress" remains **failed** (unchanged, D061).
- Not run: Linux, native Windows, CrossOver side-by-side comparison.

## Open

- Remaining 33 forms: `FrmPropertyDataListView` forms (Amplitude, Distribution, Result field/
  history output — need a DataGridView model), `PrePoMaxChildForm` forms (Material, Surface
  interaction, Step controls, Analysis, Monitor, Animation, Query, Find, views, Transformation,
  Section/Exploded/Follower view, Settings, Keyword editor), the plain `Form` dialogs
  (Edit commands, Parameters, Material library, Regenerate, Get value/colour, Select entity,
  Analyze geometry, Search contact pairs, View result history, Python stop, Splash) and FrmMain.
- Renderer gaps: property-grid autocomplete popup (the item list is built, completion uses a
  plain completer), owner-drawn paint handlers (e.g. tab-page backgrounds), HiDPI and the light
  WinForms theme; side-by-side comparison with the original app; Linux/Windows runs.

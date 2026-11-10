# Phase C11 — child-window forms and dialogs compiled whole

Date: 10 November 2026. REMAINING_WORK §1.3 (72 forms), third family. Strategy: D062, as
[C9](phase-c9-original-forms.md) and [C10](phase-c10-data-grid-forms.md).

## What runs

- **25 more original forms compiled whole** (68 of 72): FrmMaterial, FrmSurfaceInteraction,
  FrmStepControls, FrmAnalysis, FrmMonitor, FrmAnimation, FrmQuery, FrmFind, FrmUserVew,
  FrmSectionView, FrmExplodedView, FrmFollowerView, FrmTransformation, FrmSettings, FrmGetEnvVars,
  FrmParametersEditor (FrmEquationParameters.cs), FrmMaterialLibrary, FrmSearchContactPairs,
  FrmAnalyzeGeometry, FrmViewResultHistoryOutput, FrmGetValue, FrmGetColor, FrmRegenerate,
  FrmSelectEntity and FrmSplash, with the original controls they use: `CodersLabTreeView`,
  `CollapsableGroupBox`, `NumericTextBox`, `AnalysisProgressView`, `AutoClosingMessageBox`,
  `DataGridViewExtension` (row drag), `ListViewItemComparer`, `EnvVarsUIEditor`, `ViewColor`,
  `ViewDoubleValue` and the UserControls `OrderedDictionary`. 66 forms are ABC; FrmSelectEntity
  is AB (hosted, not yet reachable: the main menu keeps the C6 entity dialog).
- Not compiled yet: FrmCalculixKeywordEditor and FrmEditCommands (FastColoredTextBox editors),
  FrmPythonStop (its watchdog runs a second UI thread with `Application.Run`) and FrmMain.
- `X/UI/FormsCompat`:
  - `TreeView.cs`: native TreeView model — row layout (18 px rows, 19 px indent, label
    rectangles), `GetNodeAt`/`HitTest`, expand/collapse/select events in native order (mouse down,
    native select or +/- toggle; release, NodeMouseClick or the double click, MouseUp), label editing,
    node colours. `CodersLabTreeView` runs on it unchanged except two reviewed rewrites (its user32
    scroll position and GDI+ focus rectangle).
  - `Components.cs`: UI timers, scroll bars (Scroll before ValueChanged, `Maximum - LargeChange + 1`),
    `TableLayoutPanel`, common file dialogs, drag events, `MessageBox` (closable by caption for
    `AutoClosingMessageBox`), `SystemInformation`.
  - `ZedGraph.cs`: ZedGraph's `AxisChange`/`PickScale` (grace, zero lever, 1-2-5 steps, whole log
    decades), Y2 axis, point lists with missing values, zoom states, `RestoreScale`/`ZoomOut` as
    ZedGraph (push, auto-scale, pop). The monitor's progress plots read these scales back.
  - WinForms dock layout and `OnLayout`/`Layout`, `NumericUpDown`/`TrackBar` init and range rules,
    `Control.Invoke`/`BeginInvoke` marshalled to the UI thread, DataGridView row state (cell/row Tag,
    ErrorText, unbound `CreateCells`/`AddRange`), CellValidating, RowsAdded/Removed, Column events,
    `HitTest`/`GetRowDisplayRectangle`.
- Generator: reviewed rewrites for `OrderedDictionary` (.NET 9 adds a generic one), GDI+ text
  measurement, the auto-closing message box's user32 calls, the tree's scroll position/focus
  rectangle and the collapsible group box's caption bitmap; each is listed in the generated file.
- FrmMain hosting (verbatim): menu and tree entry points of these forms (Settings, Query, Find,
  Parameters, user/section/exploded/follower views, Transformation, Material library, Search contact
  pairs, About, Animate, renumber, part colour/transparency, find edges by angle, analyze geometry,
  monitor/results callbacks, entity selection members, KillAnalysis, ClearSelection, the
  nonpositive-Jacobian element set). Main-window members (viewport selection, results opening,
  settings/automation server, annotations, tree selection) go through `MainWindowHandler`.
  `FrmAnimation` drives the viewport through the FrmMain contract (`SetAnimationFrame`,
  `SaveAnimationAsImages/AVI`), now generated from the compiled forms as well.
- Renderer (`original_controls.py`): tree, spin box, track bar, scroll bars, progress bar, link
  label, multiline/auto-scrolling text, collapsible group box; Qt timers, file dialogs, font
  metrics and message-box closing for the model. Plots draw the model's scales (log, Y2, grids,
  dashed lines). The workbench scene follows section/pattern/exploded presentation calls at once.

## Found and fixed during the port

- The workbench opened toolkit dialogs for these forms (C5 settings/library/user views/query/find,
  Python job monitor, parameters, transformations, section/exploded/follower views, value/colour
  inputs, regenerate choice); menus, tree and toolbars now open the originals.
- Analysis results from the monitor now follow FrmMain.ResultsAnalysis (open, CloseMonitorWindow,
  history postprocessing); the history-output leaves open FrmViewResultHistoryOutput as the original
  tree does.

## Original behaviours recorded (D061)

FrmAnimation's non-.avi file name, CloseMonitorWindow on the modeless monitor and the collapsible
group box's per-text bitmap; see [deferred improvements](deferred-correctness-improvements.md).

## Evidence (Mac ARM64, 10 November 2026)

- `forms_gui_probe.py` (C11 steps in `forms_gui_probe_child.py`): the 11 non-modal forms open
  through their FrmMain entry points at the designer size (FrmMaterial and FrmUserVew size
  themselves on prepare/load, as the original); closing changes no history. FrmMaterial: Qt clicks on
  the CodersLabTreeView at the node rectangles select a model, Add and a double click add models, a
  zero density is refused with the original message, OK creates the material with the typed
  values. FrmUserVew: a Qt click on the CollapsableGroupBox button expands the group and the form
  returns to its designer size. Modal dialogs in their nested loop: FrmGetValue (transparency,
  renumber nodes, Cancel), FrmGetColor (part colour), FrmParametersEditor (a parameter typed into the
  grid evaluates to 6, OK sets it), FrmMaterialLibrary, FrmSettings with FrmGetEnvVars through the
  original `EnvVarsUIEditor` (OK reaches FrmMain.UpdateSettings), FrmRegenerate, FrmSplash. With the
  native profile: FrmAnalyzeGeometry and the find-edges FrmGetValue.
- `results_gui_probe.py`: FrmAnalysis creates the job; a real CalculiX 2.22 solve is followed by
  FrmMonitor (solver output, status, "Finished", status plot scales from ZedGraph's rules), its
  Results button opens the results; FrmAnimation moves the rendered points through its own frame
  controls and turns the menus off/on; FrmSectionView draws the section from its scroll bar;
  FrmTransformation renders a linear pattern chosen in its tree; FrmFollowerView opens; a history leaf
  opens FrmViewResultHistoryOutput with the data rows.
- `authoring_gui_probe.py`: the tree opens FrmMaterial for an existing material; Specific Heat added
  through the tree, the temperature-dependent data page and a typed data point; OK, undo and redo.
- `menu_gui_probe.py`: every main-menu leaf mapped (C11 entries now call the original FrmMain
  members); the smoke pass cancels the modal original forms as a user would.
- `python3 X/Checks/check.py`: all 7 areas pass (106 s).
- `X/UI/verify-ui.py` with the explicit Python, native mesher, Gmsh 4.13.0, lib3mf 2.4.1 and
  CalculiX 2.22 profiles and `--gui`, unattended: generators current (incl.
  `generate-original-forms.py --check`) and the UI audit (68 compiled whole); GUI probes C1 18,
  authoring 21, geometry 31, results 58, application 39, elements 27, forms 397, menu 122. Nothing
  pending. B011 "analytic double stress" remains **failed** (unchanged, D061).
- Not run: Linux, native Windows, CrossOver side-by-side comparison.

## Open

- FrmCalculixKeywordEditor, FrmEditCommands (+FrmViewObjectProperties), FrmPythonStop, FrmMain;
  FrmSelectEntity reachability (main-menu selection and its probe).
- Not modelled: owner-drawn paint (tab pages, group-box glyph, tree drop line), grid row drag and drop,
  ZedGraph zoom/pan/context menu and label-overlap step reduction, autocomplete popup look, light
  theme/HiDPI.
- The C5 toolkit dialogs replaced here are unreachable from the UI and still checked directly by
  `application_gui_probe.py`; retire them together (REMAINING_WORK: retiring duplicates).
- Side-by-side comparison with the original application; Linux/Windows runs.

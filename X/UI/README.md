# Original-code desktop host — Phase C

The .NET 10 application owns the original Controller/model. Embedded
Python.NET exposes those same live C# objects to a thin Qt/PyQt6 widget layer;
native VTK renders original Controller actor data. There is no second model,
engineering implementation, deck writer or PMX format. The retained `X/Desktop`
preview remains unchanged.

## Run

Supply the explicit CPython 3.12 profile described in
[the Controller README](../Controller/README.md), with the existing target-specific
`X/Desktop/requirements-*.txt` wheels. Pins remain VTK 9.5.2, PyQt6 6.10.0,
Qt 6.10.2 and Python.NET 3.1.0. No Python wheel is needed to load a second CLR;
.NET already hosts it.

```sh
python3 X/UI/run.py --python-profile /absolute/python.json \
  --work-directory /absolute/session-directory /absolute/project.pmx
```

`--feed /absolute/offline-feed` selects an offline NuGet source. `--no-build`
uses existing Release output. Omit the project for an empty window. This is a
single-document development host with isolated session settings, not an installed
application/package candidate.


C3 native geometry/meshing also takes an explicit tool manifest and pinned Gmsh
library; neither is discovered through PATH or silently upgraded:

```sh
python3 X/UI/run.py --python-profile /absolute/python.json \
  --work-directory /absolute/session --native-tools /absolute/tools.json \
  --gmsh-library /absolute/libgmsh.4.13.0.dylib
```

The manifest schema and original native identities are described in
`X/Controller/README.md`. Include the retained NetGenMesher and GmshCaller paths
and SHA-256 values; other mesher families require their own explicit native
payloads. Gmsh still validates the adjacent `gmsh-build.json` patched-source
profile. All ten original mesh setup factories are exposed (nine in 2D); that
is UI availability, not execution acceptance of every backend.

Geometry/model trees expose original part properties and transforms, CAD
splitting/repair/offset/surface operations, compound/group/fuse controls, mesh
setup, mesh creation/edge preview, boundary layer, remesh/thicken/split/merge,
renumbering, coordinate import, quality and geometry analysis, and part exports.
CAD/mesh native tasks and CAD history replay run off the Qt thread; document
mutations are locked while running, output is marshalled to Qt, and Cancel calls
the original executable-job stop method. Cancel coverage across all concurrent
CAD/native stages remains unaccepted. Modeless region drafts still allow picks.

`generate-geometry-forms.py` extracts the original C3 factories/apply/validation
members into `OriginalGeometryRules.g.cs`; the original type registries and
property classes compile directly. `GeometrySession` wires the original
main-window command/delegate actions. The portable host allocates separate
`native-logs/<job>-<id>/` folders for repeated native operations/history replay;
job working directories and no-overwrite log creation remain intact.

## Authoring

- **New** chooses original model space/units; **Import mesh** invokes the original
  importer. Open/Save/Save As preserve original PMX through the Phase B allowlist.
- Double-click a collection to create, or an item to edit. Right-click for
  duplicate/remove, activation, ordering, folders, grouping and ungrouping where
  the original collection supports them. Steps have their original move command.
- The tree exposes model properties, parameters, mesh sets/surfaces, reference
  points, coordinate systems, materials, sections, constraints, interactions,
  contacts, distributions, amplitudes, initial conditions, steps and step items.
- The original factories determine available types and regions for each step and
  model space. The original view descriptors control fields, choices, visibility,
  units/equations and validation. The form's original apply code dispatches the
  original commands. Undo/redo and saved-state replay remain original.
- Model editors stay open while picking in the viewport. Other document edits
  are disabled until the draft is accepted/cancelled. Pick nodes, face nodes,
  elements, surfaces or parts, then **Use picked selection**. Shift adds, Ctrl/
  Command subtracts, and Shift+Ctrl/Command intersects using original operations.
  Sets also accept explicit IDs. Point editors use an original mesh node's
  coordinates. Coordinate systems expose their individual selection regions.
- Materials support original property add/remove/order, temperature switching,
  existing/new data rows, clipboard TSV and original equation/unit conversion.
  The same table adapter serves amplitude/contact data and direct modal damping.
- Parameters use the original table evaluator/name rules and one atomic original
  SetParameters command. Solution controls preserve the original confirmation.
  File, color, flag and damping editor metadata dispatch to Qt widgets.

Cancel discards the isolated draft. Only values changed in a widget are written,
so a stale computed magnitude cannot overwrite an edited component. Original
warnings/decisions use the original MessageBoxes policy and a Qt presenter; the
original unattended-thread refusal remains in effect.

## Shared source

Original property/data classes compile under their original assembly names and
paths. `SurfaceInteractionEditor` holds original form
construction/validation shared with the Windows forms. The unused Windows parent
argument of `ViewNodeSet` stays available in its original project's small Windows
partial. Original C# remains net48/C# 7.3 compatible.

`FormSourceGen` uses the SDK's Roslyn assemblies to extract complete reviewed
original members. `generate-forms.py` produces `OriginalFormRules.g.cs`: original
view setters, factories, applicability rules, validations, parameter evaluation,
control confirmation and command dispatch. Rewrites substitute UI-neutral
choice/property data and remove only presentation lifetime/layout operations.
The live model is never temporarily hidden/internalized; drafts retain original
selection graphs instead of the Windows numeric-selector sentinel. Source
fingerprints and `--check` detect upstream changes; this is generated reuse, not
an independently maintained implementation of the rules.

```sh
dotnet build X/UI/FormSourceGen/FormSourceGen.csproj -c Release
python3 X/UI/generate-forms.py --check
python3 X/UI/generate-geometry-forms.py --check
```

Use the generator without `--check` after reviewing an upstream change.

## Viewport and verification

Mac reuses the VTK-owned native Cocoa child view. Windows/Linux use QVTK's native
interactor with widget-level click/drag separation. C1 uses no framebuffer-copy
bridge. Native VTK supplies hit coordinates; original selection resolves IDs.
Original Controller highlight actors, topology and camera callbacks drive the
scene. C4 connects original results and transient rendering commands.

```sh
python3 X/UI/verify-ui.py --output /absolute/check.json \
  --python-profile /absolute/python.json --gui --feed /absolute/offline-feed
```

Add `--native-tools /absolute/tools.json --gmsh-library /absolute/libgmsh` to
execute C3 CAD/mesh workflows; without both, C3 runtime checks stay pending.

This checks generated-source consistency, C1 regressions, C2 authoring and, with
`--gui`, actual display/widget workflows. `python3 X/Checks/check.py --area ui`
runs source/syntax/build checks; runtime checks remain explicitly pending without
an explicit profile. Linux under `xvfb-run`/`QT_QPA_PLATFORM=xcb` is supplemental
virtual-display evidence. Physical Linux/GPU/Wayland, human input and native
Windows execution remain pending.

C3 connects geometry/meshing tools; C4 connects jobs/results and viewport
symbols/annotations/contours/animation; C5 finishes remaining application,
automation and UI parity. Original form conveniences such as curve plotting,
material libraries, complete selection-tool/keyboard/focus parity and application
preferences are not inferred complete from these core authoring adapters.
The full D060 scope and all four-target/installer/signing gates remain required.

[C1 report](../../.project/reports/phase-c1-ui-foundation.md) ·
[C2 report](../../.project/reports/phase-c2-model-authoring.md) ·
[C3 report](../../.project/reports/phase-c3-geometry-meshing.md).

## C4 jobs, results and viewport

Supply all three solver arguments to `run.py` or `verify-ui.py` to select a
fingerprinted CalculiX 2.22 build:

```sh
--solver-registry /absolute/build-registry.json \
--solver-id explicit-build-id --solver-directory /absolute/solver-bin
```

No solver or mesher is discovered/upgraded implicitly. Analysis setup uses the
original `ViewAnalysisJob`, validation and commands. Run/check/monitor/kill and
result opening use the original job lifecycle. Monitor tables/plots use original
status/convergence/energy parsers. Stop coverage is active-child coverage;
[B012](../../.project/bugs/B012-analysis-cancellation-before-start.md) remains open.

Result fields, components, steps/increments, units, representation, complex
selection and deformation operate on the original live results. Unknown units
use the original interactive/unattended policy. Original field/history factories,
validation, filters, calculations, coordinate systems/reference points, part
properties and exports remain C#. Tables/plots display original history data.
`generate-results-forms.py --check` fingerprints the reused original rules;
`generate-colormaps.py --check` checks all fourteen original color maps.

Native VTK renders original scalar/frame data, colors/legends, symbols,
annotations/measurements, vector/tensor plots, section cuts/hatching, result
patterns and undeformed copies. Camera/annotation callbacks stay on the UI thread;
solver/native operations lock document edits and preserve output. Animation uses
original scale/time/harmonic frame generation. PNG capture/frame sequences and
native Ogg Theora export are available; AVI is offered only when the pinned VTK
runtime provides its platform writer. Exact cross-platform AVI parity remains
open. No encoder is installed/selected silently.

C4 adds `--results-service-probe` and `--results-probe` to the workbench script.
The independent stress diagnostic remains false in `engineeringChecks`; UI/service
success is not numerical acceptance. Full form/control, viewport edge-case,
automation, corpus, physical/native platform and distribution acceptance remain
open for C5/release. [C4 report](../../.project/reports/phase-c4-jobs-results.md).

### C5 application tools

File/Edit/Tools/Camera expose original PMH/history/keyword and material-library
workflows, thirteen original settings pages, script execution/Stop and journals,
query/Find/contact search, original advisor pages, saved/follower views, original
plot state/data, part appearance and result-component actions. Tree F2/Delete/
duplicate actions and ID/angle/rectangle selection use original Controller paths.
Original engineering objects remain in C#; no Python model or new file format.

`--settings /absolute/path/to/prepomaxx-settings.bin` explicitly loads/persists a
private strict settings file. Installed original settings are untouched. The
original loopback RPC/MCP server is off until explicitly started, or until the
user's loaded preferences request startup. Generate a token in Tools → Automation
server; its connection dialog allows copying/revealing it. Original authentication,
Origin/read-only/busy rules and command recording apply. Stop removes the private
session-discovery file. Do not put tokens in redistributable preferences.

Capture supports original PNG naming/transparency/magnification/clipboard options.
Animation offers first/last/step/FPS, direction, Once/Loop/Swing and current/all-frame
scalar limits. AVI uses VTK on platforms that provide its writer and portable
uncompressed BGR AVI otherwise; the latter refuses files above 2 GiB. Native Windows
codec-option equivalence/OpenDML remains open. PNG sequence naming/Swing endpoints
follow the original exporter. Ogg remains available through pinned VTK.

Colored 3MF requires adding `lib3mf.dll` to the explicit `--native-tools` manifest,
with the absolute library path and SHA256 for existing lib3mf **2.4.1**. The UI
verifier accepts `--three-mf-library ABS` to construct that test manifest. The
optional independent `verify-video.py` decoder uses pinned Qt multimedia; the local
Linux check image includes `libpulse0` for loading that module.

[C5 report](../../.project/reports/phase-c5-application-tools.md) and
[all-form source audit](../../.project/reports/phase-c5-ui-audit.json) distinguish
available tools from full control/input/form acceptance. All 72 complete forms
remain unaccepted; the audit is not a claim of full original UI parity.

### C6 original main window

The menu bar is the original `FrmMain` main menu: `generate-main-menu.py` writes
`original_main_menu.json` (structure, shortcuts, release visibility and each
handler's original entity selection) and `main_menu.py` maps every handler to the
original Controller command or the Qt editor for the original form. Regenerate after
an upstream change to `FrmMain` (`--check` runs in `verify-ui.py`). The GUI verifier
adds `--menu-probe`: structure, per-view enabling, original camera views,
selection/confirmation flows, parameter commands through the script panel, and a
smoke pass that runs every reachable item in Geometry, Model and Results views.
`scale_widget.py` ports the original `vtkMaxScaleWidget`.
[C6 report](../../.project/reports/phase-c6-main-window.md).

### C7 original tool strips and model tree

`generate-main-menu.py` also writes the five original `FrmMain` tool strips
(layout rows, icons, tool tips, combo items, delegated menu handlers);
`main_toolbars.py` builds them and ports the FrmMain toolbar code (symbols, colour
by, deformation, complex, step/increment, check states, per-view enabling).
`generate-model-tree.py` writes `original_model_tree.json` from
`UserControls/ModelTree` (tabs, static nodes, step nodes, context menu, icons);
`Workbench/OriginalModelTree.cs` ports the ModelTree item rules and node status;
`model_tree.py` builds the Geometry / FE Model / Results tabs, search box and the
original context menu, whose actions reuse the C6 FrmMain helper mapping. Icons are
read from the repository's original `.ico` files (`PrePoMax/Icons`,
`UserControls/Resources`) or an `Icons` folder next to the UI.
[C7 report](../../.project/reports/phase-c7-toolbars-tree.md).

### C8 model tree remainder and element evidence

`model_tree.py` adds the remaining ModelTree behaviour: in-place rename (a click on
the selected node or F2; `CanRename`, `CheckNodeName`, `cltv_AfterLabelEdit`), drag
and drop of items, groups and steps, original group creation/removal, Group Cells and
Fuse Bodies, the Space/Enter/Delete keys, the mouse-over highlight and the Model
node's keyword counts. The group and drop rules are ported in
`Workbench/OriginalTreeLayout.cs`; the compound-cell rules in `OriginalModelTree.cs`.
`generate-model-tree.py` decodes `BasePart.ico`, which exists only inside the
ModelTree.resx image stream, to `ImageList/BasePart.png`. `output_links.py` ports the
output-panel links (geometry names and inverted-element reports). The verifier adds
`--elements-probe` (`elements_gui_probe.py`): original element classes imported and
drawn, the inverted-element link, and mass sections, point springs, compression-only
supports, gravity on a mass section and Rayleigh damping through the original forms
and the CalculiX export.
[C8 report](../../.project/reports/phase-c8-tree-elements.md).

### C9 original forms compiled whole

`generate-original-forms.py` copies 39 original form classes (the `FrmProperties`/
`FrmPropertyListView` family, `FrmNewModel`, `FrmSelectItemSet`) with their base forms and
controls into `Workbench/OriginalForms/` and extracts the FrmMain form hosting members into
`OriginalForms/OriginalFormHost.g.cs`; `--check` fails when an original changed. They build
against `FormsCompat`, a headless WinForms control model, and `original_forms.py` draws them
with Qt at the designer geometry and feeds input back as WinForms events, so the original
handlers run unchanged. `original_form_host.py` routes menus/tree to the original `FrmMain`
entry points and picks to `Controller.SelectPointOrArea` while a form is open.
`forms_gui_probe.py` (`--forms-probe`) opens every compiled form through its entry point and
checks title, designer size, edit/OK - New/Cancel rules; `form_driver.py` lets the other probes
operate original forms. [C9 report](../../.project/reports/phase-c9-original-forms.md).

### C10 data grid forms

`FrmAmplitude`, `FrmDistribution`, `FrmResultFieldOutput` and `FrmResultHistoryOutput` compile
whole with `FrmPropertyDataListView`, `DataGridViewCopyPaste` and `FrmDiagramView`.
`FormsCompat/DataGrid.cs` models DataGridView/BindingSource/DataObject with WinForms semantics,
`FormsCompat/ZedGraph.cs` the plot pane; `original_forms.py` draws them (`DataGridWidget`,
`GraphWidget`). The forms probe drives the amplitude grid (edit, new row, invalid value,
copy/paste, plot, delete); the results probe the result field/history forms.
[C10 report](../../.project/reports/phase-c10-data-grid-forms.md).

### C11 child-window forms and dialogs

25 more original forms compile whole (material, surface interaction, step controls, analysis,
monitor, animation, query, find, user/section/exploded/follower views, transformation, settings,
environment variables, parameters, material library, search contact pairs, analyze geometry,
view result history, get value/colour, regenerate, select entity, splash) with the original
`CodersLabTreeView`, `CollapsableGroupBox`, `NumericTextBox`, `AnalysisProgressView` and
`AutoClosingMessageBox`. `FormsCompat/TreeView.cs` models the native TreeView (row geometry, hit
tests, expand/select rules), `FormsCompat/Components.cs` timers, scroll bars, table layout, file
dialogs, drag events and MessageBox, `FormsCompat/ZedGraph.cs` ZedGraph's axis auto-scaling
(linear/log, Y2, zoom states). `original_controls.py` draws the new controls and installs the
toolkit services; menus, tree and toolbars open these forms through their FrmMain members.
[C11 report](../../.project/reports/phase-c11-child-forms.md).

### C12 code editor forms

FrmCalculixKeywordEditor and FrmEditCommands (with FrmViewObjectProperties) compile whole with the
original `CalculixInpTextBox` and `PythonEditorTextBox`. `FormsCompat/FastColoredTextBox.cs` models
FastColoredTextBox 2.16.24 (lines with style layers, ranges, undo groups, hotkeys, typed characters,
autocomplete menu, find/replace); `original_controls.CodeEditor` draws it and sends keys as
WM_KEYDOWN/WM_CHAR. `SplitContainer` lays out its panels in the model. The probe steps are in
`forms_gui_probe_editor.py`; beam element evidence is in `geometry_gui_probe.py`.
[C12 report](../../.project/reports/phase-c12-editor-forms.md).

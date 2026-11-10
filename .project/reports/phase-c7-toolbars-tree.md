# Phase C7 — original tool strips and model tree

Date: 10 November 2026. Continues "Finish Phase C" (REMAINING_WORK §1.1).
Strategy: D062 (reuse original code and data).

## Tool strips

`X/UI/generate-main-menu.py` now also extracts the five original `FrmMain` tool
strips into `original_main_menu.json`: the two rows set in the FrmMain constructor
(File, Views, Symbols / Result deformation, Results), every item's kind, text,
tool tip, combo items and icon (resolved through `Properties/Resources.resx` to the
original `.ico` file), and the main-menu handler each button delegates to
(including the right-click handlers of Section view, Exploded view and Capture).
The menu items get their 139 original icons from the same data.

`X/UI/main_toolbars.py` builds the strips and ports the FrmMain toolbar code:

- Buttons run the same mapped handler as the original menu item (41 buttons).
  Section/Exploded view call `Controller.TurnSectionViewOnOff` /
  `TurnExplodedViewOnOff(true)` on left click and open the settings on right click;
  Capture captures with the current properties (no form) and opens the form on right
  click (`CaptureViewport`, including its "Select to save…" error and replace prompt).
- `SetMenuAndToolStripVisibility` tool-strip enabling per view, check states of
  Section/Exploded/Follower/Transformation and `UpdateResultsTypeIconStates`.
- `UpdateSymbolsList` (None; Model + steps; Result) with the per-view selection,
  `UpdateColorByComboBox` / `tscbColorBy_SelectedIndexChanged` through the original
  annotation items.
- Result strip: result name, deformation variable/type/factor
  (`UpdateScaleFactorTextBoxState`), complex type/angle (`UpdateComplexControlStates`,
  `GetPhase360`), `SetAllStepAndIncrementIds` with First/Previous/Next/Last, and
  Animate opening the animation controls (FrmAnimation stand-in) only for a
  deformed view with result steps.

The superseded PrePoMax-X toolbars (Project, Results field/component/view boxes)
remain as hidden back-ends for existing code and probes; the PrePoMax-X selection
controls (pick mode, angle, box select) stay visible below the original rows.

## Model tree

`X/UI/generate-model-tree.py` extracts `UserControls/ModelTree` into
`original_model_tree.json`: the three tabs (Geometry, FE Model, Results), each
tree's static nodes with text and image (designer sample parts removed as
`ModelTree.Clear` does), the step sub-nodes of `AddStep`, the node-name fields, the
context menu (`cmsTree` plus `cmsTreeSecondary` as `AssembleTreeContextMenu`
joins them) and the `ilIcons` keys with their icon files.

`X/UI/Workbench/OriginalModelTree.cs` ports the item rules of `ModelTree.cs`:
`AppendMenuFields` with `CanCreate/CanDuplicate/CanPropagate/CanPreview/
CanSearchContactPairs/CanSwapMergeMasterSlave/CanHide/CanDeactivate`,
`SetNodeStatus`/`SetSplitSubPartNodeStatus` (part type, transparency, small
features, free-edge warning, hidden/inactive gray, job status, invalid colour) and
the step-controls text. The sessions now attach the original item objects and tags
(`Field`/`ResultFieldOutput`, `FieldData`, `HistoryResultSet`/`ResultHistoryOutput`,
`HistoryResultData`), list geometry folders and compound cells under the part they
were cut from, and add the result mesh node sets, element sets and surfaces that the
original Results tree shows.

`X/UI/model_tree.py` builds the original layout (Model → Mesh/Features/…/Steps,
Analyses; Results → Model/Results), the original counts `Name (n)` through folders,
node images including Dots/Dots_t on expand, the per-tab search box (`FilterTree`),
tab switching (`ModelTree_ViewEvent`, cancelled while a form is open), double click
(`cltv_MouseDoubleClick`) and `PrepareToolStripItem` visibility/enabling. Each menu
action runs the same FrmMain helper as the original main menu item through the C6
selection specs (`apply_target`), so confirmations and Controller commands are shared.

## Not yet ported

- `TryGetSplitCellsToGroup` / `TryGetBodiesToFuse`: Group Cells and Fuse Bodies stay
  hidden in the tree menu (the main-menu items remain available).
- In-place rename (`CanRename`, F2), drag and drop, mouse-over highlight and the
  Model node's user/modified keyword counts.
- `BasePart.ico` exists only inside the ModelTree.resx image stream; the Parts node
  has no icon.
- The exploded-view button was exercised only on a one-part fixture (the original
  rule then leaves the view unchanged, as checked).

## Checks (Mac ARM64, 10 November 2026)

- `python3 X/Checks/check.py`: all 7 areas pass (101 s).
- `X/UI/verify-ui.py` with the explicit Python, native mesher, Gmsh 4.13.0, lib3mf
  2.4.1 and CalculiX 2.22 profiles and `--gui`: generators current (new:
  `original-model-tree`); services pass; GUI probes C1 18, C2 authoring 18, C3
  geometry 21, C4 results 35, C5 application 39 and menu 99 (was 48) pass. Menu
  smoke pass: 313 items, none unmapped, no mapping errors.
- The two synthetic native-pointer checks that failed on 10 November (C1 element
  pick, C3 CAD part pick) pass in this run, so that open item is closed on Mac ARM64.
- New menu-probe checks cover strip layout and icons, every button mapped, per-view
  enabling, symbols list, colour by in both directions, capture without the form,
  result type check states, step/increment list and navigation, user-defined
  factor, complex controls hidden without complex results, Animate, exploded and
  section toggles; tree tabs and view switching, original node order, counts,
  icons, step sub-nodes, part status icons, context-menu visibility for material,
  materials node, Model node, part and raw result field, tree Duplicate/Delete/
  Hide/Show through the original commands, and the search filter.
- B011 "analytic double stress" remains **failed** (unchanged, D061).
- Not run: Linux, native Windows, CrossOver side-by-side comparison of the strips
  and tree.

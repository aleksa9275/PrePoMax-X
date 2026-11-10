# Phase C8 — model tree remainder and model/mesh UI evidence

Date: 10 November 2026. Continues REMAINING_WORK §1.1–1.2 after C7.
Strategy: D062 (reuse original code and data).

## Model tree remainder

Ported from `UserControls/ModelTree.cs`, `CodersLabTreeView` and the FrmMain handlers:

- **Rename in place** (`CanRename`, `IsNodeRenameable`, `CheckNodeName`,
  `OnAfterLabelEdit`, `cltv_AfterLabelEdit`): a click on the selected node or F2
  opens the editor; empty names are rejected; items go through
  `Controller.CheckItemName` and `RenameCommand`, groups through `CheckPartGroupName`
  or the sibling-name rule and `RenameGroup`, split sub parts and a compound shown as
  its single sub part through `RenameSplitSubPartCommand`.
- **Drag and drop** (`cltv_ItemDrag/DragOver/DragDrop`): items and single groups of
  one ordered-dictionary collection, and steps. `Workbench/OriginalTreeLayout.cs`
  ports `TryGetOrderedDictionaryDropTarget` with `GetDropPosition`,
  `AdjustDropTargetIndex`, `IsOrderedDictionaryMoveUnchanged`, the compound
  restrictions and `TryGetStepDropTarget`; drops run
  `ChangeOrderedDictionaryItemLayoutCommand` / `MoveStepsCommand`. The target row is
  marked while dragging (the original draws an insertion line).
- **Groups**: `tsmiCreateGroup_Click` (index rule, `GetNextGroupName` /
  `GetNextPartGroupName`; the C7 name prompt was not original and is removed),
  `CanCreateOrderedDictionaryGroup` for every organisable collection (geometry parts,
  mesh setup, results and analyses included), and `tsmiDelete_Click`: only groups →
  the groups are removed and their items kept; otherwise only the directly selected
  items (split sub parts as their cells) are deleted. C7 also deleted the items
  inside selected groups; that was a port defect.
- **Group Cells / Fuse Bodies** (`TryGetSplitCellsToGroup`, `TryGetBodiesToFuse`,
  `GroupSplitCellsAndSelect`, `FuseBodiesAndSelect`, `SelectSplitSubPart`).
- **Keys** (`cltv_KeyDown`): Space → `InvertHideShowOrActivateDeactivate`, Enter →
  create/edit, Delete → tree Delete.
- **Mouse over** (`timerMouseMove_Tick`): selected plus hovered items highlighted
  with `Highlight3DObjects(items, true)` after 100 ms; single field-data selection
  selects the field (`FieldDataSelectEvent`).
- **Model node counts** (`UpdateNumberOfKeywords`).
- **`BasePart.ico`**: decoded by `generate-model-tree.py` from the ilIcons
  `ImageListStreamer` in `ModelTree.resx` (MSFt run-length stream, ILHEAD, 32-bit
  BMP) to `X/UI/ImageList/BasePart.png`; `--check` covers it.
- Results, analyses and mesh setup lists now show their tree groups, as the
  original's ordered-dictionary contexts do.

The headless FrmMain host did not handle `HighlightActor`, so selecting or hovering a
part in the tree highlighted nothing. It now adds the copy of the part's model edges
to the selection layer in the primary highlight colour
(`vtkControl.HighlightActor`/`GetCopyOfModelEdgesActor`). Without model edges the
original draws a camera silhouette; the host keeps the part surface (recorded
deviation).

## Output links

`output_links.py` ports `FindOutputLinks`, the link drawing of the output box and
`tbOutput_LinkClicked`: on warning/error lines, geometry names
(`GetGeometryNameRanges`) and inverted-element reports
(`GetInvertedElementReferenceRanges`) are links; a click runs
`HighlightGeometryNamedAt` / `HighlightInvertedElementsNamedAt` unless an operation
or a form is active.

## Model/mesh UI evidence

New `elements_gui_probe.py` (`--elements-probe`, run by `verify-ui.py --gui`):

- Original `.inp` model import through the window and drawing with element edges for
  the 3D classes (`pressure-solids.inp`: linear/parabolic tetra, wedge, hexa,
  pyramid) and the 2D classes (`plane-stress.inp`: linear/parabolic triangle and
  quadrilateral), with the parts in the FE Model tree.
- `InvertedElements`: an imported mesh with one inverted tetrahedron; the original
  report line becomes an output link and the click highlights the element.
- `MassSection` (through the Point Mass section form; the negative mass is rejected
  by `MassSection.CheckPositive`), a gravity load on the mass section, a point spring
  and a compression-only surface support through the constraint forms, and a Dynamic
  step with Rayleigh `Damping` through the step form (Alpha/Beta shown by
  `UpdateVisibility`). The CalculiX export contains `*Mass` on the generated MASS
  elements, gravity on the mass section's element set, SPRING1 and GAPUNI elements
  (`MassElement`, `LinearSpringElement`, `LinearGapElement`) and
  `*Damping, Alpha=0.2, Beta=0.001`.

Inventory: these 18 model/mesh entries move from AB to ABC (model/mesh 108 entries:
106 C). `LinearBeamElement` and `ParabolicBeamElement` stay AB: the original model
import (`FeModel.ImportModelFromInpFile`, also UNV/VOL) keeps solid and shell
elements only, so beams appear only as CAD free/internal edges (`VisFileReader`),
in mesh tools and in beam results; a CAD shell/wire or beam-results fixture is
needed for their UI evidence.

Observation (original behaviour, not changed): importing `line-tension.inp` reports
B31/B31R/B21/B32/B32R/T2D2 as unsupported and imports no elements.

## Checks (Mac ARM64, 10 November 2026)

- `python3 X/Checks/check.py`: all 7 areas pass (99 s).
- `X/UI/verify-ui.py` with the explicit Python, native mesher, Gmsh 4.13.0, lib3mf
  2.4.1 and CalculiX 2.22 profiles and `--gui`: generators current; services pass;
  GUI probes C1 18, C2 authoring 18, C3 geometry 29 (was 21; adds split-cell rename,
  Group Cells, Fuse Bodies), C4 results 35, C5 application 39, menu 122 (was 99; adds
  rename, groups, drag and drop, steps, keys, mouse over, keyword counts, Parts icon)
  and the new element probe 27 pass. Menu smoke: 313 items, none unmapped, no
  mapping errors. Nothing pending.
- B011 "analytic double stress" remains **failed** (unchanged, D061).
- Not run: Linux, native Windows, CrossOver side-by-side comparison. Drag and drop
  was exercised through the drop-target/drop handlers, not with a native pointer drag.

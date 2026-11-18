# M0 — GitHub home and upstream 3.0.1 with vtkNative

Date: 18 November 2026. Maintainer decisions D063 (target 3.0.1 with upstream's native VTK port, switch
now) and D064 (GitHub as the project home).

## What changed

- **Home.** Upstream moved to github.com/PrePoMax/PrePoMax; the GitLab project is archived and its history
  was rewritten. The maintainer forked it (github.com/aleksa9275/PrePoMax-X). Our 146 commits were replayed
  onto upstream's own `eb6aff0c`, whose tree equals our former GitLab base `de8f7303` (3.0.0 RC1 plus a
  documentation fix); the replayed head has the identical tree of the GitLab head `e08df83f`. Remotes:
  `origin` (fork), `upstream` (PrePoMax/PrePoMax), `gitlab` (archive).
- **Upstream delta merged** at `1e2f83f2` = 3.0.1 (`51bca35a`, 67 commits on our base) + the vtkNative port
  (ActiViz removed; flat C API over VTK 9.7) + `Dev/` reorganization. 3.0.1 content: composite shells
  (material orientations, composite shell sections with layers and layup diagram, composite strength,
  material-axes / shell in-plane / composite failure result outputs), sweep/QuadWild meshing fixes, a Netgen
  `.vis` kernel-id fix (new `nglib.dll`), Search Contact Pairs in the Python API and as one command, empty
  selections shown red in the property grid, symbols drawn while editing, Q-Morph removed, form/command
  folders renumbered (55 renames). The QuadWild, NetgenMesher and Gmsh sources are now published.
- **Conflicts (15)** resolved toward upstream:
  - `vtkControl` (7): upstream's data classes no longer use ActiViz, so `vtkControl/` now equals upstream
    except the texture split below; our ActiViz-era extracts (cell topology, closest-edge picking) moved to
    `X/Domain/vtkControl/Legacy/` until M1 replaces the Python renderer.
  - `FrmMaterial`: restored to upstream unchanged; the extracted `MaterialEditor` survives only as X code for
    the legacy C2 dialog (with Composite Strength).
  - `VisFileReader`: upstream's 3.0.1 `ReadEdges` fix equals the port fix we had made independently; its new
    `GroupVisualizationFacesByGeometryFace` replaces the old merge in our split file.
  - `FeModel`/`FeResults`: upstream's new members with our `CaeGlobals.OrderedDictionary` qualification;
    `Extensions`: the new `SetLocationInsideWorkingArea` joins the WinForms-only partial; csproj files merged.
- **Original-file divergence** from upstream: 192 files (69 added, 123 changed), was 202. Edits to original
  files after the merge: `vtkMaxLookupTable` partial (`WriteTexture` split; Bitmap is Windows-only on .NET),
  two `using` lines in `VisFileReader.cs`, header links of our split files now point to GitHub.
- **Build lists and contracts:** source lists regenerated for the renumbered folders; 13 new PrePoMax and one
  UserControls source added to the portable subsets; `IControllerHost` regenerated (+7 FrmMain members:
  tree update batches, ambient occlusion, camera adjustment, material axes symbol, menu visibility).
- **PMX allowlist:** 24 reviewed 3.0.1 types (material orientation, composite section/layer/strength,
  orientation/composite keywords, shell result data and the three result outputs, five commands, three
  equation converters as metadata). Views, data points and UI interfaces stay excluded, as before.
- **UI:** generators rerun; FrmMaterialOrientation compiled whole (71 classes); the headless WinForms model
  gained `Splitter`, `DataGridView.CellFormatting` (raised before the column converter, as WinForms does)
  and the combo-box column's `DisplayStyle`/`FlatStyle`; `DoubleBufferedPanel` compiles from its original
  source. The menu, tree and form host know the Material Orientations family; the legacy contact search
  applies through the new single command. The interim renderer's colormap and follower generators read the
  3.0.0 `vtkControl.cs` from git (output identical apart from the source hash) until M1.
- **Expectations updated to 3.0.1** (not loosened): FrmResultFieldOutput lists 7 types in both results probes (+ Material Axes,
  Shell In-Plane State, Composite Failure; the shell ones without properties on a solid model), and the FE
  Model tree has Material Orientations between Materials and Sections.
- Inventory: model/mesh 111 (3 new composite entries, A), commands 242 (5 new, A), forms 73 (1 new, A).

## Evidence (macOS ARM64, 18 November 2026)

- `python3 X/Checks/check.py` areas domain, controller, core, analysis, execution, results: all pass
  (84 s). Controller native parts pending as before (no profiles passed by check.py). The analysis check
  now runs its tests in the post-RC2 mode they were written for (tightened lamina stability, composite
  strength), since 3.0.1 contains those changes.
- `X/UI/verify-ui.py --gui --package <P1 macOS app>`, unattended: generators current, services, GUI probes
  C1 18, authoring 21, geometry 43, results 58, application 39, elements 27, forms 419, menu 122 (317 leaf
  items, all mapped); nothing pending. Same counts as before the merge.
- B011 "analytic double stress" remains **failed** (199.992 vs 200, D061).
- Environment drift: this Mac now has only the .NET 11 SDK/runtime (10.0 removed) and Homebrew Python 3.15.
  The net10.0 projects build with SDK 11.0.100; tests ran with `DOTNET_ROLL_FORWARD=Major` on the 11.0.0
  runtime. The packages keep their self-contained .NET 10.0.14 runtime. Reinstall a .NET 10 SDK for
  release-grade runs.
- Not run: Linux, Windows, packages from this revision (the P1 packages are 3.0.0-based), the upstream
  composite Python test scripts (M2).

## Open (next)

- M1: VTK 9.7 recipe, vtkNative on macOS/Linux, the original vtkControl compiled whole in Qt.
- M2: composite UI (layup diagram via a Paint layer, missing-value painter), Netgen re-pin to the published
  NetgenMesher revision behind the 3.0.1 `nglib.dll`, QuadWild for macOS/Linux, FrmMain whole.

# C3 — Geometry and meshing UI

9 November 2026. C3 core geometry/mesh authoring is implemented on the C1/C2
host. The original Controller, Commands, engineering classes, descriptors and
native tool adapters remain the implementation; full form/control parity and
four-target acceptance are not inferred from this milestone.

## Delivered

- Geometry/model trees, original part properties and translate/rotate/mirror/scale.
  Original CAD/STL and mesh import routes, part exports, hide/show/remove, compound
  creation/regeneration, geometry swapping, shell/solid conversion, STL normals,
  split-cell grouping/subpart rename and body fusion.
- Original solid/shell split types and property views, face offset, repair,
  periodic-face split, flip/defeature/delete/fuse surface operations. Region,
  splitter and direction picks retain original selection graphs and update calls.
- All ten original mesh setup types: sizing, local size, Shell Mmg, Shell Gmsh,
  Shell QuadWild, thickening, Netgen, tetrahedral Gmsh, transfinite and sweep.
  Original 2D filtering offers nine. Selection-dependent defaults, basic/advanced
  sizing, reset, duplication, activation and replace/remove remain original rules.
- Native mesh creation/edge preview, boundary layer, shell remeshing/thickening,
  mesh splitting, coincident-node merge, mesh-part merge, renumbering, nodal
  coordinate import, original element-quality/statistics/set creation and
  geometry-analysis measurements/display filters. Native element-face edges can
  be shown without exposing surface-picking triangulation diagonals.
- Native operations and CAD history replay run on .NET tasks. Qt presentation
  and prompts return to the main thread; document mutations are locked while
  running. Original executable-job stop is exposed. All concurrent native-stage
  cancellation paths are not yet accepted. Picking remains available for idle
  modeless drafts. Unset model space/units are selected before import, matching
  the original main-window prerequisite.

## Reuse and integration repairs

`X/UI/generate-geometry-forms.py` uses the existing Roslyn extractor to reuse
reviewed original form members in `OriginalGeometryRules.g.cs` (17 rule adapters;
SplitShell shares SplitSolid behavior). Toolkit lifetime/layout is removed and
original main-window delegates are wired to the original Controller methods.
Type registries compile directly from the original sources; 26 additional
original property views are included in the whole PrePoMax assembly. Original
net48 engineering code, algorithms, tolerances and dependency pins are unchanged.

Two integration repairs were necessary. Property widgets flush edited fields
before a dynamic rebuild so pending edits survive type/visibility changes. The
portable process adapter formerly required a fresh directory even though the
original Controller reuses its native working directory during history replay.
The host now allocates separate native log folders per invocation, retaining
`CreateNew`/existing-evidence protection and the original executable working
paths. The adapter's default no-overwrite behavior still passes its existing
regression. No deserialization allowlist or native-tool validation was loosened.

## Verification

Evidence: `/private/tmp/prepomaxx-c3`; hashes/commands/artifacts are summarized in
[the verification receipt](phase-c3-ui-verification.json).

| Environment/check | Outcome |
|---|---|
| Mac ARM64, real Cocoa/Qt/VTK display | 25 C3 service + 20 GUI checks passed |
| Linux ARM64 Podman/Xvfb, current GmshCaller build | 25 C3 service + 20 GUI checks passed |
| C1/C2 regressions, each ARM64 host | C1 20 service + 18 GUI; C2 33 service + 18 GUI passed |
| Original Windows 3.0.0 via isolated CrossOver | meshed and split/grouped CAD PMX opened/resaved; native readback passed |
| Original Windows mesh export comparison | engineering text identical; only CRLF/LF and per-export random heading hash differ |
| Original net48/C# 7.3 compile-only | all eleven assemblies passed |
| Existing execution/process regressions | 49 passed; includes timeout/kill/pipes and existing-log refusal |
| Focused Controller/persistence | nine stages passed; 20 strict persistence checks retained |

The public synthetic 10-unit cube imports through original Netgen, meshes through
pinned patched Gmsh 4.13.0 into 241 nodes/677 linear tetrahedra, transforms,
renumbers, evaluates original element quality, exports and round-trips PMX.
A separate CAD flow translates the solid, splits it through a plane into two
original compound cells, groups a subset, renames its subpart and round-trips.
Original-app readback preserves sizing/order, node/element IDs, quality set and
split/subpart data. Source/stable-binary version warnings remain expected.

Checks retain original semantics: redundant grouping of all cells already in a
subpart is refused without recording a command; a subset can be regrouped. CAD
translation compares the original bounding box plus the translation, retaining
OpenCASCADE's existing 1e-7 box padding. Mesh-only export creates a fresh FeModel
and random hash in the original code, so that single header token is normalized
for comparison; every other character after line-ending normalization matches.
No engineering tolerance was relaxed. Initial checks that incorrectly assumed
zero box padding, permitted redundant grouping, or a stable mesh-export header
were corrected from the original sources. The initial milestone grouping failure
and raw Windows comparison failure remain in retained logs.

## Remaining boundaries

C3 is UI connectivity plus representative workflows, not exhaustive mesher,
geometry/element/selection/backend execution. Mmg/QuadWild, all sweep/transfinite/
shell/compound variants, all edit/export combinations and cancellation stages
still need their acceptance matrices. Runtime profiles must supply the actual
pinned native payloads; unsupported/missing tools are not substituted. Patched
Gmsh 4.13.0 remains selected; 4.15.2 is unadopted and dormant Q-Morph source/license
recovery remains unresolved.

Inventory: 87/108 selected model/mesh entries and 136/237 Commands now C. All 72
full forms remain C0; V remains zero. Full tree/selection conveniences, preview
symbols, libraries, preferences, keyboard/focus and full control parity stay in
C4/C5. Results presentation, jobs and complete viewport glyphs/annotations/
contours/deformation/animation are C4 next. Native Windows, deferred Linux x64,
physical Linux/GPU/Wayland/human input, broader original PMX corpus and installers/
signing remain open. CrossOver is reference evidence, not Windows acceptance.
No numerical correctness findings were fixed or marked passed. C3 generator
warnings join the D061 post-parity warning cleanup. No preview/package candidate,
installer or hosted CI run was created; retained preview `1580fa9c` is unchanged.

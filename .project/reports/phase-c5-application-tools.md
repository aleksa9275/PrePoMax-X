# C5 — original application tools and UI audit

9 November 2026. Application/automation adapters implemented and all 72 original
forms inventoried. **This milestone does not establish complete UI parity.** The
[audit](phase-c5-ui-audit.json) records 993 designer fields, 796 event subscriptions,
original-source fingerprints, adapters and remaining comparison work. All full
forms retain C/V pending. [Verification receipt](phase-c5-ui-verification.json).

## Implementation

- Original thirteen settings views, validation, resets and explicit strict
  settings files (`--settings ABS`). Settings never overwrite the installed
  original; Unix preference files are private. Background, orientation/scale
  widgets, navigation sensitivity and original presentation settings are wired.
- Original material-library graph and `.lib` format: libraries/categories,
  copy/remove/reorder/rename, original collision naming and equation rejection,
  isolated model draft, multiple dirty libraries and original material-property
  previews. Original model commands apply accepted changes.
- Original PMH command editor/read/write, Python journal export, stale-draft
  rejection, ordering recipe and nested original command-property inspector.
  Original keyword tree placement, generated-fragment signatures/overrides,
  suppression, add/remove/move/active/reset and original apply command.
- Python file/editor/output/stop/reset, per-command or recorded-script execution;
  original Python engine, APIs, journal and command history. Document mutations
  lock during tasks. Original RPC/MCP method table, tools, authentication, read-only,
  busy, wait/cancel and screenshot routes are reused, rather than reimplemented.
  The endpoint remains opt-in, loopback and authenticated. Native adaptations are
  UI dispatch, current-user pipes and private session-directory permissions.
- Original query calculations/units/formatting, Find, contact search/merge/
  master-slave highlighting and original nine-page advisor text/actions. Original
  user-view/follower parameters and follower camera vector/matrix rules are reused.
- Tree selection/highlighting/preserved selection, rename/delete/duplicate,
  hide/show, propagation, master/slave actions, element-set conversion, part
  appearance, camera/edge modes, ID/angle/rectangle selection and regeneration
  prompts. Original field/history component and raw-history removal are connected.
- Original plot data extraction (including amplitude shifts), curve/settings and
  side-panel state, editable plot/curve controls, pan/zoom, data/image export and
  strict PMX persistence. Script/advisor state also round-trips through PMX.
- Colored 3MF export uses original writer and explicit lib3mf 2.4.1; viewport
  lookup data and original closest-axis up-view rule are supplied. PNG capture
  supports original transparency/magnification/naming/clipboard properties.
  Animation adds range/FPS/step/direction/Once/Loop/Swing/scalar-limit controls.
  PNG sequence naming and Swing endpoints now follow the original exporter.
  Portable uncompressed BGR AVI supports Mac/Linux without a new encoder package;
  the original VTK AVI writer remains used where available. Ogg remains available.
  The AVI container follows [Microsoft's RIFF reference](https://learn.microsoft.com/windows/win32/directshow/avi-riff-file-reference).

The only original-file edits remove two unused Windows/remoting imports from one
export property view. No engineering algorithm, tolerance, mesher/solver version
or persistence allowlist was changed. Gmsh 4.13.0, CalculiX 2.22 and the existing
Qt/VTK/Python pins remain. New original property/helper/automation sources are
compiled whole; generated rule files fingerprint their source. The Controller
contract generator excludes four directly implemented automation methods rather
than generating duplicate presentation forwarding methods.

## Verification

Evidence: `/private/tmp/prepomaxx-c5`. Mac uses native Cocoa/VTK; Linux ARM64
uses native VTK/X11 under Xvfb. The complete milestone runs pass C1 20 service +
18 GUI, C2 33+18, C3 25+21 and C4 41+35 on each host. Final focused C5 checks
pass **31 service + 40 GUI on each host**, supplementing those runs after the last
application adapters. Counts and commands
are retained in the receipt; no unexecuted platform is counted as a pass.

- C5 services cover strict settings/library/history/PMX formats, isolation,
  keyword movement/overrides/reset, original journal/scripts/queries/contact
  search/advisor/follower math, plot state and stale-history rejection.
- C5 GUI covers actual widgets and task locks, dispatched rectangle selection,
  preference widgets, RGBA/magnification, script execution/Stop, plot/script PMX,
  MCP authorization/Origin/busy/read-only, named-pipe ping, private session files,
  native AVI/colored 3MF and original result-component removals.
- Exported AVI decodes into all six valid frames with the pinned Qt multimedia
  backend on both ARM64 hosts. Linux's first decode failed to load `libpulse.so.0`;
  adding `libpulse0` to the local check image resolves that dependency. Its failed
  receipt is retained. Hardware decoding is unavailable; verification uses CPU.
- Original Windows PrePoMax 3.0.0 in the isolated CrossOver reference opens and
  resaves a C5 PMX and reads the native `.lib`. Strict native readback retains
  the material, user keyword, script state and exact plot values `[2,4,6]`.
  The source/stable version warning remains. CrossOver is reference evidence,
  not native Windows acceptance.
- All eleven original net48/C# 7.3 assemblies compile. Ten focused Controller
  stages pass, including strict persistence and explicit native 3MF export.
  Standalone solve/CAD stages in that runner remain pending without their profiles;
  the C3/C4 milestone supplies representative native CAD/solver evidence separately.
  Generator, source-list, Python syntax and whitespace checks pass.

## What remains

The source audit is complete; **behavioral acceptance of every original form,
control and workflow is not complete**. Complete original-app comparisons of
selection filters/conveniences, property menus, keyboard/focus, layout/DPI,
clipboard/row editing and large/complex projects remain. Full section/cap/picking,
all glyph variants, transformed-field/animation extrema, plot/annotation layout
and all-analysis/backend/export matrices remain unaccepted. Native Windows AVI
codec-dialog equivalence and very large (>2 GiB) portable AVI/OpenDML handling
are open; portable AVI currently refuses that size before writing. No new reduced
final scope or backend exception is selected.

B011's stress diagnostic remains **failed** (199.99200439453125 vs 200, absolute
.001). D029, B006–B012 and other D061 numerical/original findings remain deferred;
active Python Stop is not proof of pre-start/concurrent native-job cancellation.
Broader original PMX corpus, physical Linux/GPU/Wayland/human input, native Windows,
deferred Linux x64, installers/signing and distribution acceptance remain open.
The audit must be closed before claiming Phase C/full parity or starting the
post-parity correctness sweep.

Inventory: 88/108 selected model/mesh entries C; 227/237 Commands C; all 72 full
forms unaccepted and V remains zero. Remaining command entries include base/
compatibility commands with no separate modern UI construction path, so these
counts are not a product percentage. No new preview/installer or hosted CI run
was produced; retained preview `1580fa9c` is unchanged. Podman is stopped after
verification. Superseded generated C5 builds are pruned in the receipt.

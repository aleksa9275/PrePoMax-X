# Phase C2 — original-code model authoring

8 November 2026. The core C2 authoring milestone is implemented in the C1 host.
An imported mesh can now receive model properties/parameters, original materials,
sets/surfaces, reference points/coordinate systems, sections, constraints,
interactions/contact pairs, distributions/amplitudes, initial conditions, steps,
BCs/loads/defined fields, field/history requests and solution controls through
original property views, form rules and commands. Original PMX/history remains
the state/persistence implementation.

## Reuse and behavior

The model tree reads the original collections and their folder layout. Context
operations call original duplicate/remove/activation, step movement and ordered
collection layout commands. Original layouts survive PMX and undo/redo; no
parallel Python model is maintained. New/import/open/save and model/units controls
connect to original Controller methods.

`FormSourceGen` uses SDK Roslyn to extract whole reviewed original form members.
The checked-in generator reuses view construction, type factories, applicability,
name/value validation, parameter evaluation, solution-control confirmation and
apply/command dispatch. UI references become neutral property/choice data;
layout/dialog lifetime operations are excluded. Source fingerprints and `--check`
prevent the generated rules drifting from original form changes. Original view
classes remain compiled at their original paths/names/assembly ownership.
The original Windows code keeps its original form methods.

Material property defaults and interaction construction/validation are small
shared helpers used by the original Windows forms as well as the portable host.
The only unused Windows parent argument in ViewNodeSet remains available in an
original-project Windows partial; its nonvisual constructor is shared. All eleven
original C# assemblies still compile with C# 7.3/net48.

Qt presents original descriptors, choices, dynamic visibility, units/equations,
flags, colors, file values and damping tables. Materials support property and
row creation/removal/reordering, temperature switching and clipboard TSV. Other
original tables use the same adapter. Parameters apply atomically after the
original evaluator; cancellation restores the original NCalc context. Solution
controls retain the original warning/cancel behavior.

Definition dialogs keep the viewport usable for picks while blocking concurrent
document edits. Picked sets retain original recorded mouse selections and world
precision. Shift/add, Ctrl or Command/subtract and combined/intersect use original
selection operations. Node/element sets and surfaces support creation/editing;
point controls use original mesh-node coordinates. Original Controller highlight
actors now drive selection display instead of deriving a separate highlight mesh.
The original Controller remains responsible for geometry/engineering behavior.

Two necessary integration repairs were made: register .NET's code-page provider
for the original ISO-8859-8 job-name sanitizer; write only widget values actually
edited so an unchanged computed magnitude cannot restore a stale component.
The original magnitude/validation algorithms and numerical tolerances are unchanged.

## Verification

Evidence root: `/private/tmp/prepomaxx-c2`. The checked-in
[receipt](phase-c2-ui-verification.json) records exact source/log/artifact hashes.

| Check | Actual outcome |
|---|---|
| Mac ARM64 C1 regression | 20 property + 18 native GUI checks passed |
| Mac ARM64 C2 workflow | 33 authoring + 18 GUI checks passed |
| Linux ARM64 C1 regression | 20 property + 18 X11/Xvfb GUI checks passed |
| Linux ARM64 C2 workflow | 33 authoring + 18 GUI checks passed |
| Original type-factory/property matrix | all 12 step families, including the required slip-wear → boundary-displacement sequence |
| Original Windows 3.0.0 via isolated CrossOver | GUI-authored PMX opened, exported and resaved; deck content identical apart from CRLF/LF |
| Native original-app resave readback | nodes, element, material equation/value, force, picked set, parameter, spring, initial temperature, solution controls and folder preserved |
| Original C# 7.3/net48 compile-only check | all eleven assemblies passed |
| Focused Controller/persistence regression | nine stages passed, including 20 persistence checks and picked saved-state replay |
| `X/Checks/check.py --area ui` | source/syntax/build and generated-rule consistency passed; its no-profile runtime checks explicitly pending |

The authored workflow starts from mesh-only public cube input. It evaluates
parameter dependencies, creates an equation-backed material, changes temperature
rows, creates recorded picked sets and an area-checked surface, validates section
element compatibility, creates reference/coordinate definitions, amplitudes,
distributions, interactions/contacts, steps/default job, BC/load/output definitions,
spring/initial temperature and solution controls. It exercises original refusal,
confirmation/cancellation, duplication, removal, activation, undo/replay, grouping,
PMX save/reopen and original-app deck comparison. A mistaken initial test assumed
same-surface contact should be rejected; original source explicitly permits
single-surface contact, so the actual empty-selection rule is tested and the
original permitted contact behavior is retained.

GUI checks exercise real tree/dialog/table widgets, original zero-load rejection,
material property/row changes, modeless picking, set creation, dynamic region
visibility, command restoration on editor close and PMX round-trip. C1 separately
dispatches native Cocoa/Qt pointer events and checks actual screen pixels/camera/
resize. Linux Xvfb is supplemental virtual-display/software-renderer evidence,
not physical desktop/GPU/Wayland acceptance. CrossOver is an original-app reference,
not native Windows acceptance.

## Remaining scope

C3 connects geometry and meshing editors/tools. C4 connects jobs/results and full
viewport glyphs/annotations, contours/legends, animation and screenshot services.
C5 completes remaining application/automation surfaces and audits all UI parity:
material libraries, curve plotting, full selection-tool and keyboard/focus
behavior, application preferences and other original form conveniences remain
required. The core authoring adapters do not mark all 72 complete forms accepted.

The inventory records UI availability for 82 selected model/mesh entries and 83
command entries, not exhaustive execution or full-family V acceptance. Full
feature/PMX/backend matrices, native Windows x64, deferred Linux x64, physical
Linux/GPU/Wayland and human input, source/stable-binary correspondence and
four-target installers/signing/releases remain open. No engineering algorithm,
mesher/solver version, PMX allowlist or installed original was changed. No new
package candidate or hosted CI run was created. Original D029 failures and the
D061 numerical/warning backlog remain open; backend sweeps were not repeated for
this UI integration milestone.

[Usage and reproduction](../../X/UI/README.md).

# C4 — original-code jobs, results and native viewport

9 November 2026. **Core C4 workflows implemented; representative ARM64 and
original-app interoperability verified.** Full form/control, numerical and
four-target acceptance remain open. [Receipt](phase-c4-ui-verification.json).

## Implementation

- Original analysis view, name validation and Add/Replace/Duplicate/Remove/Run
  commands; explicit fingerprinted CalculiX 2.22 profile. Run/check/open/kill use
  original Controller/AnalysisJob. Output/status/convergence/DAT monitor tabs and
  progress/convergence/energy plots use original job data/parsers. Document edits
  lock during tasks; presentation and prompts marshal to the Qt thread.
- Original result/component/step/increment selection, multiple-result selection,
  units and interactive unknown-unit policy, representation, complex selection
  and deformation. Original four field-output and seven Release history-output
  factories, view descriptors, validations, filters, calculations and commands.
  Result reference points/coordinate systems reuse original rules with result
  providers; part properties, colors, transparency, representation and exports
  call original commands. History tables/curves/export use original result data.
- Native VTK displays original scalars, all fourteen original color maps,
  legends/status, symbols, annotations/measurements, vector/tensor plots,
  undeformed copies, section cuts/caps/hatching and symmetry/linear/circular
  patterns. Component transforms use original C# result-field transformation;
  copies contribute to the scalar range and extrema. Closed CAD surface contours
  are triangulated for caps without inventing volume elements.
- Scale/time/harmonic animation requests original Controller frame generation.
  Frames move native points/scalars and update original annotation/reference-point
  data. PNG captures/sequences, original automation screenshot callback and native
  Ogg Theora export are connected. AVI is offered only where pinned VTK supplies
  its platform writer; exact Mac/Linux AVI support remains unfinished.
- `generate-results-forms.py` fingerprints extracted/reused original rule members;
  `generate-colormaps.py` checks original spectrum points/color spaces. The only
  original-file edits remove three unused Windows/remoting imports from two
  property views. Original engineering algorithms/tolerances, strict PMX policy,
  native versions and installed applications are unchanged.

## Verification

Evidence root: `/private/tmp/prepomaxx-c4`. Mac uses native Cocoa/VTK; Linux
ARM64 uses native VTK/X11 under Xvfb in the retained pinned image. Each host has:

| Workflow | Service | GUI |
|---|---:|---:|
| C1 property/selection/PMX regression | 20 passed | 18 passed |
| C2 original authoring regression | 33 passed | 18 passed |
| C3 CAD/mesh regression, plus closed-CAD section cap | 25 passed | 21 passed |
| C4 original jobs/results/viewport | 41 passed | 35 passed |

The final combined run covers all earlier regressions; focused final rendering
checks add CAD caps and rotated tensor-component range coverage after visual
review. These are UI/service checks, not claims of complete engineering accuracy.
The controlled cancellation helper verifies an actually started child and Killed
status; it is not a solver or a pre-start/concurrent-CAD cancellation proof.

The native static cube completes through the original Controller, gives 8 nodes/
1 element, and preserves results, equation fields, table histories, coordinate
systems/reference points and editable model through strict PMX round-trip.
Original Windows PrePoMax 3.0.0 in isolated CrossOver opens that PMX, reads the
same fields/tools, resaves it, and native strict readback preserves them. U1,
S11 and doubled S11 match exactly in original/native readbacks. CrossOver is
reference evidence, not native Windows acceptance. The original source/stable
binary version warning remains and correspondence is not accepted globally.

All eleven original net48/C# 7.3 assemblies compile. Nine focused Controller
stages pass, including 20 strict-persistence checks. That runner separately lists
standalone native 3MF/solver/CAD stages as pending without their profiles; C3/C4
supply representative CAD/solver evidence separately. Source-generation, Python
syntax and whitespace checks pass. Ogg output is written by pinned native VTK;
no external decoder acceptance is claimed.

## Explicit failures and remaining scope

- **B011 numerical check stays failed:** doubled S11 expected 200, actual
  199.99200439453125, absolute tolerance .001. Original equation output exactly
  doubles loaded S11 = 99.99600219726562; original Windows PMX readback agrees.
  Cause is not isolated. No expectation/tolerance is changed and this diagnostic
  is excluded from the UI/service pass counts. [B011](../bugs/B011-c4-linear-cube-stress-diagnostic.md).
- Cancellation before process initialization remains open under D061
  ([B012](../bugs/B012-analysis-cancellation-before-start.md)); concurrent CAD stop
  tracking remains [B010](../bugs/B010-concurrent-cad-cancellation.md). Initial
  failed cancellation/history-routing checks are retained; the C2 routing
  regression is repaired and its final unchanged authoring checks pass.
- C5 must finish remaining application/automation, libraries/plotting, full tree/
  selection/keyboard/focus/preferences and complete form/control parity. This
  includes remaining per-component/raw-history editing and viewport/export
  details. All 72 full forms remain unaccepted; UI availability is not full-form V.
- Full CAD/shell/line/quadratic section/closed-loop/picking matrices, transformed
  fields/extrema across every animation mode, glyph variants, annotation layout/
  editing, capture transparency/magnification/video/container parity, large
  projects and complex/all-analysis result matrices remain open. Core adapters
  do not establish identical behavior for every original viewport edge case.
- Broader original PMX corpus, physical Linux/GPU/Wayland/human input, native
  Windows, deferred Linux x64 and installers/signing remain open. D029 and all
  other D061 numerical findings stay open. Gmsh 4.13.0 and CalculiX 2.22 remain
  pinned; 4.15.2 is unadopted and the dormant Q-Morph wrapper remains unresolved.

Inventory: 87/108 selected model/mesh entries C; 175/237 Commands C; V remains
zero. Superseded C4 build payloads are pruned in the receipt, small evidence is
retained, and the single old preview `1580fa9c` is unchanged. Podman is stopped.
No installer/preview candidate or hosted CI run was produced. C5 is next.

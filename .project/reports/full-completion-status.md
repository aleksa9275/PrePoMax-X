# Full-completion assessment — 8 November 2026

We have moved beyond feasibility to a usable native engineering preview with
substantial original-source analysis coverage. **The application is not yet
feature-complete, generally PMX-compatible, numerically accepted or ready for
public release.** The remaining work includes major implementation areas, not
only packaging or test cleanup.

This assessment consolidates [the parity contract](../PARITY.md),
[release requirements](../RELEASE.md) and the latest
[workflow report/receipt](element-family-completion.md). It is a documentation
review of retained evidence, not a new platform/solver test run.

## Delivered functionality and remaining requirements

| Work area | Delivered and verified within reported boundaries | Required before full completion |
|---|---|---|
| Elements and calculations | Imported solid, plane/axisymmetric, shell/membrane, beam/truss and discrete workflows; representative linear/nonlinear static, frequency/buckling, thermal/expansion and transient calculations on Mac/Linux ARM64 | Remaining original calculation/family combinations, complex/steady-state dynamics, coupled/uncoupled temperature-displacement, boundary-displacement and slip-wear breadth; full materials/orientations, loads, constraints/contact/interactions, controls and outputs |
| CAD and meshing | Native CAD import, selected CAD edits/history/STEP exchange, linear/quadratic tetrahedral meshing; imported-mesh transforms/renumbering and complete boundary surface/edge extraction | Every remaining original mesher/setup/control/backend and mesh operation, including broader surface/line/structured/extruded/revolved/refinement workflows; general geometry/repair and region/selection behavior |
| Project persistence | Restricted editable original C3D8 and CAD/C3D4 PMX workflows; broader static family PMX read/solve/exact-copy Save As, with original-app readback | Original-compatible PMX saving of newly authored native sessions; broader graph editing, results/history/command persistence and the full accepted older/current project corpus in both directions |
| Application, results and automation | Model controls, frozen jobs/status/cancellation, original bounded FRD/DAT fields/histories, contours, deformation/frame animation, plots/CSV and tested selection/picking boundaries | Full original results orchestration and tools, all selection/clipping/editing workflows, settings, scripting/API/MCP, command history/replay and complete application behavior |
| Platforms and distribution | Current copied Mac ARM64 internal app; native Linux ARM64 workflow checks; earlier bounded Linux archive/Ubuntu installer proofs and historical x64 subset checks | Current full-application native Windows x64 and Linux x64 acceptance, physical Linux desktop coverage, clean-machine install/upgrade/uninstall for all four targets, required Windows/Linux packages and Homebrew routes, Mac signing/notarization, corresponding source/notices and verified stable-release source identity |
| Numerical/correctness acceptance | Original algorithms/tolerances retained, independent/reference checks and explicit diagnostics; completion handling rejects solver *ERROR even with exit zero | Investigate/resolve and verify affected D029/B006/B007/B008/B009 and thermal/axisymmetric findings under D061 sequencing; no unexplained mandatory failures at release |

CrossOver reference checks do not count as native Windows acceptance. A built
four-RID host is not four-platform application acceptance. A copied original PMX
is not new-session serialization. An admitted analysis type is not exhaustive
verification of its supported combinations.

## What the eight element-family milestones mean now

| Milestone | Actual standing |
|---|---|
| 1. Plane stress/strain | Connected imported static workflows, thickness/edge pressure and results; representative frequency added. General mesher, PMX and calculation breadth remains. |
| 2. Axisymmetric | Connected imported static/frequency workflows and original field scaling. Coarse/segment diagnostics and broader combinations remain. |
| 3. Shells/membranes | Connected imported static sections/loads/rotations and bounded layers/results; shell frequency added. Material/orientation, calculation, authoring and persistence breadth remains. |
| 4. Beams/trusses | Connected imported static sections/moments/results and beam frequency/implicit transient. Original refusal/accuracy findings and modal-beam failure remain explicit; wider functionality remains. |
| 5. Masses/springs/gaps | Connected exact imported discrete elements, section controls, native jobs and nodal results/history. Automated surface/reference-point/local-coordinate breadth remains. |
| 6. Mixed-family/calculation compatibility | Partial: representative shared-node static, frequency and implicit workflows pass. The complete original combination matrix is not closed. |
| 7. Mesh authoring | Partial: imported transforms, renumbering, boundary extraction and undo/redo work. These do not replace all original meshers/tools. |
| 8. Full PMX/platform compatibility | Partial: checked original-family exchange and available-host checks work. Native project creation/persistence and full platform/release acceptance remain open. |

Thus the eight-step sequence has produced useful implementation in every work
area; it has **not** established eight fully closed parity milestones.

## Evidence supporting the current preview

- Implementation `1580fa9c2405c4652374eeb664df963a22acd078`; closing evidence
  `c278676af270393d61e6b4c7035b607f374480e3`, both remote-verified on the research
  branch with CI skipped. This status/handoff is a following documentation-only
  checkpoint; application code is unchanged.
- Mac/Linux ARM64: 135 family and 58 original-family PMX workflow checks each;
  copied Mac bridge/Cocoa transports and representative prior regressions pass.
- 95 desktop tests and current Core/Analysis/Execution suites pass; final Results
  has 90 checks. Known numerical failures remain separately false.
- Actual Cocoa screen/ID/scalar/resize proof and candidate source/payload/ad-hoc
  signature checks pass. Internal candidate:
  `/tmp/prepomaxx-task0110-current-delivery/PrePoMax-X Preview.app`.
- B009's modal-beam crash remains unresolved. Both native ARM64 solvers fail and
  the pinned Windows binary fails under CrossOver; zero-load basis initialization
  does not resolve it. The user's crash report is retained and linked by hash.
- One signed maximum principal-stress comparison fails the unchanged bound near
  a pure-shear sign tie. Raw stress tensors and other recorded invariants agree
  within the existing bounds. This is documented, not normalized to a pass.

These test counts measure the declared workflows, not the proportion of all
PrePoMax commands implemented. There is no validated whole-product percentage or
completion date. Providing one from task numbers or these pass counts would
suggest precision the current feature inventory does not support.

## Suggested remaining sequence

The next high-value implementation area is a native-authored project that can be
saved as an editable original-compatible PMX, reopened natively and read back in
the original application. Start with a useful explicitly checked graph, then
broaden to the full persistence contract. This addresses a major workflow gap;
exact-copy Save As cannot replace it.

Continue the missing mesher/model/calculation/result/automation areas in usable
increments, updating feature-level coverage and original/native evidence. As
functional parity is reached, perform the deferred correctness work under D061
and finish the required platform/package/full-corpus gates. These are substantial
workstreams, not a promise that each can be finished in a single task/session.

Hosted CI stays off under D058. Linux x64 testing stays deferred under D059 until
the specified finishing environment is used. The maintainer's full workflow test
and Apple Developer ID/notarization involvement remain at their agreed stages.
All original requirements remain; no new solver exception or scope reduction is
introduced.

[Continuation instructions, source map and reproducible commands](../handoffs/current-next-session.md).

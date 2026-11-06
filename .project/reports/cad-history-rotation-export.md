# CAD geometry checkpoints, rotation and whole-model exchange

Task 0078 adds owned geometry undo/redo without command replay. Successful edits
retain the previous verified CAD document; undo/redo restores its exact BREP/VIS
bytes. Failed or cancelled edits keep redo; a successful branch releases redo.
Restoration clears dependent mesh/analysis after confirmation and retains unsaved
state. Opening another document or closing releases all checkpoint inputs.

The preview retains at most 32 checkpoints and 256 MiB of authoritative checkpoint
inputs, including the current/candidate geometry. Rejected edits preserve the
previous model. This is in-memory geometry history, not original PMX history
replay, mesh/analysis undo or native-session serialization.

Native Mac checkpoint byte restoration passes. Forty-eight desktop tests cover
undo/redo, successful/failed branches, lifetime cleanup, checkpoint corruption,
declined restoration and both count/byte limits, plus existing lifecycle paths.
Initial harness/converted-byte expectation failures remain in the local receipt.
Native Linux ARM64 and combined copied-app evidence follow at task 0080 closeout.

Task 0079 adds original axis-angle rotation: explicit center, nonzero axis and
degrees strictly between -360 and 360, excluding zero. The original native
BREP_TRANSFORM owns the transform; no kernel or coordinate formatter changes.
Thirteen Mac native checks pass for off-origin 90-degree rotation, analytical
volume/center/bounds, original face IDs, untouched part bytes and input refusals.
Rotation uses the existing cancellation, publication, checkpoint and frozen
provenance path. New Windows execution and general CAD parity remain pending.

Task 0080 adds **Export all CAD parts as STEP…** through the recovered original
`STEP_ASSEMBLY` command, which gathers bodies unchanged. It deliberately uses
assembly gathering rather than the imprinting `BREP_COMPOUND` operation. Every
source solid is matched uniquely on native readback by finite volume, area,
centroid and inertia measurements (relative 1e-12/absolute 1e-9); solid count,
source bytes and destination bytes are checked. Uncovered shells/faces/edges/
vertices, changed measurements, missing solids and ambiguous origins are refused.
These are bounded exchange checks, not proof of arbitrary CAD equivalence or
assembly naming/hierarchy preservation. Both selected and whole-model exports
preserve the active mesh/analysis and use a new filename, published atomically
only after readback. Cancellation publishes nothing.

The source desktop completes 62 checks: translation and rotation dialogs,
exact owned undo/redo, split/repair, three-body mesh (206 nodes/517 C3D4), selected
and whole-model STEP export/reopen, native affine-displacement/unit-stress solve,
complete frozen edit provenance and visible contours. Forty-nine desktop checks
and nine build guards pass on Mac; both native Mac/Linux ARM64 pass 50 transactions and
49 desktop checks. Linux also completes all 62 combined GUI/analytical checks.
Final copied-app evidence follows below.

D057 original PMX compatibility, D058 hosted CI hold, D059 x64 deferral, strict
native parity differences, both correctness failures, quadratic tetrahedra and
all installer/signing/four-target/release gates remain. STEP exchange is not a
native CAD-session PMX serializer; original session persistence remains open.

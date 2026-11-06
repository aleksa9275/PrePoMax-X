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

Tasks 0079/0080 add original axis-angle rotation and checked whole-model STEP
geometry exchange next. D057 original PMX compatibility, D058 hosted CI hold,
D059 x64 deferral, strict native parity differences, both correctness failures,
quadratic tetrahedra and all installer/signing/four-target/release gates remain.

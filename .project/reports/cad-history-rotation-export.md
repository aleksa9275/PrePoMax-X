# CAD geometry history, rotation and whole-model STEP exchange

Tasks 0078–0080 complete three bounded native desktop increments: owned geometry
undo/redo, original axis-angle rotation and checked whole-model STEP export.
[Verification receipt](cad-history-rotation-export-verification.json).
New native-session PMX serialization remains open under D057.

## Behavior and boundaries

**Undo CAD geometry / Redo CAD geometry** restores verified, independently owned
BREP/VIS checkpoints without replaying commands. Failed/cancelled edits retain
redo; a successful branch releases it. Restoring geometry clears dependent mesh,
regions and analysis after confirmation and retains unsaved state. Opening another
document or closing releases all checkpoint inputs. The preview allows at most
32 checkpoints and 256 MiB of authoritative checkpoint inputs, including current/
candidate geometry after successful publication; rejected edits preserve the old
model. This is geometry history, not mesh/analysis undo, PMX history replay or
project serialization.

**Rotate part…** uses the original native `BREP_TRANSFORM` with an explicit center,
nonzero axis and degrees strictly between -360 and 360, excluding zero. The
original kernel owns axis normalization and geometry behavior. Off-origin
90-degree rotation passes analytical volume/centroid/bounds and retains original
face identities and untouched part bytes. Rotation uses the background worker,
atomic publication, cancellation, geometry history and frozen job provenance.

**Export all CAD parts as STEP…** uses the recovered original `STEP_ASSEMBLY`,
which gathers bodies unchanged. `BREP_COMPOUND` imprints bodies and is not used.
Each source solid must have a unique native-readback match by finite volume,
surface area, centroid and inertia measurements (relative 1e-12/absolute 1e-9).
Solid count, staged source bytes, document integrity and destination bytes are
checked. Uncovered shells/faces/edges/vertices, changed measurements, lost solids
and ambiguous origins are refused. These are bounded exchange checks, not proof
of arbitrary CAD equivalence or preservation of assembly names/hierarchy.
Selected-part export now shares these readback checks. Both exports preserve the
active mesh/analysis and unsaved state, publish atomically to a new filename and
never overwrite an existing destination. Cancellation publishes nothing.

## Actual verification

- Native Mac ARM64 and Linux ARM64 each pass **50 CAD transaction checks**,
  including exact checkpoint restoration, analytical rotation, original reference
  translation/split/repair hashes, selected/whole-model export and refusal controls.
- Both copied Mac viewports and the Linux ARM64 desktop each pass **62 workflow
  checks** through real dialogs, translation/rotation undo/redo, split/repair,
  remeshing, selected/whole STEP export/reopen, frozen provenance and native solve.
  The edited three-solid mesh has **206 nodes / 517 C3D4 elements** on both hosts.
- The affine displacement and unit axial stress checks pass at every result node.
  Maximum displacement error is ~3.47e-18. Jobs freeze all four active operation
  inputs, parameter files, receipts, outputs, hashes and source-part mappings.
  Actual bridge/Cocoa screenshots show mesh contours and the configured model tree.
- **49 desktop regression checks** pass on each native host; **nine build guards**
  pass on Mac. Body-loss/changed-measurement/ambiguous-origin refusals, late export
  cancellation, history corruption, successful/failed branches, checkpoint
  count/byte limits, deferred close and lifetime cleanup are covered.
- Existing CAD PMX and C3D8 PMX workflows pass **28 / 17 checks** respectively in
  the final copied Mac app and against the current Linux ARM64 source.

The strict final Mac/Linux comparison matches mesh topology, decoded coordinates
and result value order, but differs in G17 deck coordinates and tiny field
components: maximum absolute field difference ~9.61688e-14. The full strict
comparison and deck diff remain in the evidence directory. Analytical checks pass
independently; no coordinate formatter, engineering tolerance or solver precision
changed. Exact native parity remains open. The earlier task 0077 strict difference
also remains historical evidence.

Original Windows translation/split/repair BREP hashes are reused from the retained
task 0066 reference. No new Windows rotation/whole-export or original GUI execution
is claimed. Original numerical/C# owners and native runtimes are unchanged, so
verification targets the affected Python/CAD paths; the full numerical/platform/
release matrix was not rerun. Initial task 0078 test-double and raw-versus-converted
BREP assertion failures are retained alongside their corrected passing receipts.

## Publication and retained candidate

Normal research publication is remote-verified:

- 0078: `e62da0fffb9e89367d583b70341fda9b4cc1b3be`
- 0079: `ec24d84d55d81e8b970adad473627f42b3c78d47`
- 0080 / packaged source: `390cf08b9c45363fadba217b5ace91175eb26b73`

All commits contain `[skip ci]`; pushes use `-o ci.skip`. No hosted jobs were
requested. D058's hold and D059's Windows/Podman Linux x64 deferral remain.

Current candidate: `/tmp/prepomaxx-task0080-delivery/PrePoMax-X Preview.app`.
Launch with sibling `/tmp/prepomaxx-task0080-delivery/Native CAD Preview.command`
to enable `/tmp/prepomaxx-task0063-recipe/runtime`. Older task 0067/0068/0070/0073/
0077 launchers forward to it. The package source patch is empty; the dirty flag
reflects four pre-existing Finder metadata files. All **2,422 payload file hashes**,
symlink targets and the copied app's ad-hoc signature pass after cleanup.
This remains an internal, unnotarized native preview.

Evidence: `/tmp/prepomaxx-task0080-evidence`; package manifest, logs and source
snapshot: `/tmp/prepomaxx-task0080-final`. The tracked receipt pins their hashes.
Seven superseded generated directories, including task 0077's copied app and the
new build's duplicate payloads/caches, were pruned: 5,035,165,629 logical bytes,
with 4,436,168,704 bytes (~4.13 GiB) of measured free-space gain. Generated CAD/
STEP/PMX/mesh projects, all jobs/screenshots/receipts/source snapshots and shared
native/Python/.NET/package/Podman/source caches remain. Installed user app/state
was untouched. Historical candidate paths in earlier reports are superseded.

## Open acceptance work

Original-compatible native CAD-session PMX persistence, broader project graphs,
assembly metadata, arbitrary CAD/defective repair, analysis/mesher breadth, exact
native parity, both existing element correctness failures, quadratic tetrahedra,
Windows/net48 and all four-target/installers/Homebrew/signing/notarization/release
requirements remain open. No frontend/default-format/backend/precision decision
or release acceptance is made. Notify the maintainer when Developer ID or
notarization actually requires their involvement.


Task 0083 retention update: task 0080's copied app is superseded and pruned after
verified mirror/scale/copy integration. Evidence/projects/jobs remain. Read
[the current report](cad-mirror-scale-copies.md) for the retained candidate.

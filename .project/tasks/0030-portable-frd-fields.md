# Task 0030 — Original FRD mesh and static field inspection

2026-10-18. Maintainer explicitly resumes after reset. This lifts task 0029's
feature stop and resumes the accepted mesh/deck/solve/results sequence locally;
no new publication instruction. Preserve the verified 993f9263/6c51ced6 checkpoint.

Read PROJECT/STATUS/DECISIONS/task 0029 and its reset handoff before edits.
Next bounded implementation: mechanically separate original FRD decoding from
FeResults/FeMesh orchestration, retain original Field/FieldData/FieldComponent,
names/algorithms/type ownership, expose a guarded raw 3D static results snapshot
and portable inspection command. Reuse the buffered FRD reader and original
ASCII/binary decoding rather than implementing another format decoder.

Scope includes mechanically extracting required unchanged Tools methods, source-
ownership/replay guards, original analytical Windows cube and independent field/
binary/culture/invalid-input controls on Mac/Linux ARM64 and all three source pins.
Keep full legacy Read/axisymmetric preprocessing in net48; raw snapshot is not
full FeResults, DAT histories, axisymmetric/modal/complex acceptance or new format.
No solver substitution/build admission, new numerical benchmark, GPU/default/
serializer choice or correctness-algorithm/tolerance changes. Existing two strict
correctness failures/tetra gate and all Windows/net48/RC2/release gates remain.

Leave local work uncommitted unless publication is explicitly requested again.

## Completed locally

Original FRD decoding, field types/math and shared Tools methods are mechanically
preserved; full net48 orchestration remains in its legacy partial. Callable raw
C3D8 static snapshot and inspect-frd CLI work with the original Windows analytical
fixture and independently written binary float/double counterparts. Six results
guards plus existing nine analysis/four job/ten replay guards pass. All three
source pins each pass 39 results checks/five CLI controls and rerun 331 accepted
analysis checks on Mac/Linux ARM64 with matching fingerprints/outcomes.
Both original correctness failures/tetra gate remain. No solver runs; full
results/Windows/net48/RC2 and all release gates remain. Native x64 CI is prepared,
not run. [Report/evidence](../reports/portable-frd-fields.md). Leave local work
uncommitted and continue the accepted sequence.

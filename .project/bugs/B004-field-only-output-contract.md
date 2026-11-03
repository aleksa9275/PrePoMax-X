# B004 — Field-only static job misclassified as failed

3 November 2026, task 0044 integration. Verified with the actual bundled native
CalculiX 2.22/SPOOLES cube: uncheck all node/element history requests, keep the
original field outputs. CalculiX exits successfully, JobStatus is OK and FRD/STA
exist, but DAT is empty. The host's unconditional nonempty-DAT requirement turns
this valid field-only run into `success=false, outputsPresent=false`.
The actual failed outcome, zero-byte DAT and generated FRD/STA are retained in
[before-fix evidence](../reports/editable-solid-workflow/b004/before-fix/solve/run.json).

Repair in the host output contract: FRD/STA remain required; nonempty DAT remains
required whenever any history set is requested. Record `requiredOutputs` in the
outcome. Do not change original deck/model/solver algorithms or numerical bounds.

Regression coverage: actual Unix transport fixture rejects empty DAT when history
is requested, permits it only for field-only input, and still rejects missing
FRD/STA. Native Mac/Linux cube workflow additionally solves with histories off and
compares original-reader mesh/IDs and all FRD fields exactly with the history-on
run. This is one valid output configuration, not broad solver/release acceptance.
Actual verification/publication is in the task 0044 report.

Local repair checks pass existing 49 execution checks/13 CLI controls, strict
requested-DAT/field-only/missing-field cases, and 15 native Mac cube checks.
Actual copied-app hosts/bundled solver run the edited model with histories off:
zero-byte DAT is accepted, FRD/STA remain required and all original-reader fields
exactly equal the history-on edited run. Both current editor viewport proofs
also pass. No numerical bound is changed.

Repair **921b24a6** is published/remote-verified; exact-commit pipeline
**3022312183 passes all six automatic Linux x64 jobs**. Native Linux history-on/
off cube/reader workflow passes 15 checks, including exact FRD-field equality.

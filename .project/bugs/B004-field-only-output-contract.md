# B004 — Field-only static job misclassified as failed

3 November 2026, task 0044 integration. Verified with the actual bundled native
CalculiX 2.22/SPOOLES cube: uncheck all node/element history requests, keep the
original field outputs. CalculiX exits successfully, JobStatus is OK and FRD/STA
exist, but DAT is empty. The host's unconditional nonempty-DAT requirement turns
this valid field-only run into `success=false, outputsPresent=false`.

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

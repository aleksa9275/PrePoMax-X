# Task 0038 — Reproducible native CalculiX CPU workflow

2 November 2026. Build the already recovered unchanged CalculiX 2.22 sources with
SPOOLES first, using an explicit native toolchain/dependency recipe, then run the
original static deck through native solve and original FRD/DAT inspection. Keep
compile portability patches separate from pristine sources; no numerical algorithm,
tolerance/default/backend rewriting or silent solver upgrade. Initial single-
thread reference evidence is not PaStiX/capacity/full analysis acceptance.

Recover unchanged dependency source incrementally under ThirdParty/Sources;
record actual compiler/ABI/link/runtime hashes. A research binary need not falsely
claim complete public redistribution closure. Preserve Windows reference profile,
both original correctness failures/tetra gate and four-target release requirements.
Maintainer authorizes normal origin research checkpoint commit/push with evidence.

Outcome: bounded Mac ARM64 CPU cube workflow complete, twelve checks plus the
existing analytical negative control pass. Original C# deck/job/results execute
with recovered 2.22/SPOOLES/ARPACK-ng source and pinned toolchain/runtime identity.
B001 duplicate set emission fixed and covered by a real solve and one regression.
Current analysis 332/execution 49 checks and source guards pass; both original
failures/tetra gate and other-target/performance/source/runtime/release gates stay.
[Evidence/next](../reports/native-cpu-workflow.md),
[publication](../reports/native-delivery-publication.md).

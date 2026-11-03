# Task 0044 — First editable solid workflow (implemented; final verification/publication)

3 November continuation: maintainer says to proceed after the published task 0043
checkpoint. Implement the existing bounded definition editor using original INP
set inventory, C# validation and immutable per-job input snapshots. First scope
assigns imported named sets; arbitrary picked/new-set authoring stays pending.

Implemented model tree, units/material/section/support/load/static-output controls,
original-C# `validate-static`, frozen per-run input workspaces and unsaved-session
discard prompts. Seven real-Qt editor checks, four process checks and eight build
checks pass; affected current Analysis/Execution pass. Actual packaged baseline
and edited native solves pass 18 GUI plus 15 deck/numerical/control checks. Final
artifact/verification/publication is recorded in
[the report](../reports/editable-solid-workflow.md). No project format, production
frontend/default/backend change or full parity acceptance is implied.

Final configuration coverage fixes B004: required outputs now follow history
requests; requested DAT and FRD/STA remain strict. Native Mac workflow passes
15 checks, copied edited field-only outputs match exactly, and both current
editor viewport proofs pass. Earlier capture failure remains retained; strict
native retry passes after maintainer display confirmation. The report records
the current repaired DMG and actual second checkpoint publication/CI.

Prepared 3 November 2026 after task 0043's bounded native viewport proof.
Continue the accepted Mac-first/shared-source sequence toward 3.0.0 parity.
The task 0042 DMG remains the tested fallback; task 0043's native transport stays
opt-in pending explicit production selection.

Deliver a model tree and controls to configure the supported INP/static-solid
slice: explicit units, original material/section assignment, node sets/supports
and loads, then solve/cancel and inspect fields without hand-editing JSON.
Use existing original C# model/deck validation/services and existing process
boundaries; presentation must not duplicate engineering calculations or parsers.
Represent unsupported definitions honestly. Preserve original FEM identities.

Verify one edited analysis against its generated deck and analytical/reference
outcome, prove that a changed load/material changes the executed definition,
and exercise invalid input plus cancel/failure through the existing boundary.
Run affected current-source checks and a packaged workflow smoke; keep Linux
x64 engineering feedback and other-target source portability visible.

This increment does not silently invent a PMX format or production frontend.
Supported save/reopen is the subsequent explicit persistence increment; full
CAD/meshing, analysis breadth, command history and release acceptance remain
tracked in PARITY/STATUS. Both known correctness failures/tetra gate remain.

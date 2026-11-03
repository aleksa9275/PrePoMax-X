# Task 0044 — First editable solid workflow (next; not started)

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

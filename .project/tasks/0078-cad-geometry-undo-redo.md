# Task 0078 — Owned CAD geometry undo and redo

Authorized 6 November 2026 as the first of three further tasks. Retain bounded
owned geometry checkpoints for successful native CAD edits; undo/redo restores
validated BREP/VIS bytes without replaying commands. Preserve history on failed
or cancelled edits, discard redo only after a successful branch, and close all
retained inputs on replacement/closing. Geometry undo invalidates dependent mesh/
analysis after confirmation; it does not restore solver/model state or replay
PMX history. Include resource limits and lifecycle/real native checks.

Preserve D057, D058 hosted hold, D059 x64 deferral, both correctness failures,
quadratic tetrahedra, exact native parity and all release requirements.

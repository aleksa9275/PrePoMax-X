# Task 0009 — CrossOver original Windows application reference attempt

Status: reference read/save/reopen complete, 2026-10-15. Maintainer explicitly asked whether the installed
CrossOver can run PrePoMax. CrossOver 26.2 is installed on this Mac; an existing
unrelated bottle is left unchanged. Test the official portable PrePoMax 2.6.0
release in a separate research bottle and disposable work directory, with
runtime/binary provenance and bounded launch diagnostics.

This is a supplementary original-application compatibility-layer experiment.
It is not native Mac/Linux acceptance, a frontend decision, native source
recovery or a replacement for eventual Windows validation. Preserve the supplied
PMX; use a copy for application readback and any save. Use existing CLI/Python
gateways when supported. No original application/source changes or unsafe
serialization switches in the portable probe. No solver/mesher substitution,
commits, pushes, upstream messages or PR publication.

Acceptance: record official bundle URL/hash, application/runtime identities,
separate bottle setup and actual bounded launch/readback outcome. A measured
runtime/graphics prerequisite failure is a completed capability investigation,
not a claimed application pass. Stop if further installation/UI work requires
unavailable interaction; preserve diagnostics and concrete follow-up instructions.

## Outcome

[Report](../reports/crossover-reference.md): original Windows 2.6.0 runs in the
new bottle. Human confirmed model display, separate save and model/results
display on reopening. Inventories and guarded byte comparisons retain evidence
and graph changes. Persistent installation verified: 217 application files/two
PMX copies. No native platform/numerical parity, regeneration, meshing or solver
claim. Original model preserved outside Git.

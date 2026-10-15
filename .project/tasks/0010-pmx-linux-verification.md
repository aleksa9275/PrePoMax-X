# Task 0010 — PMX inspection on Linux and preparation exit gates

Status: bounded task complete, 2026-10-15. Maintainer requested continuing the testing/
preparation phase after the CrossOver reference cycle. Scope is bounded local
research on research/native-feasibility; no production change, new dependency,
format/frontend choice, commit/push or upstream communication.

Run the existing 24 synthetic PMX tests in the cached Linux ARM64 Podman image,
then inspect the existing original and CrossOver-saved private reference copies.
Mount inputs/checkout read-only, disable container network access and retain
image/runtime/tool provenance. Compare the exact framing and record inventories
with the existing Mac observations, excluding only runtime/decoder identities
and build diagnostics. Guard the observed extra framework support assembly
separately; no unknown loaded assembly difference is accepted. Do not normalize
serialized type names, references or values away.
Verify input hashes against the Mac records and after execution. Preserve all
earlier uncommitted work. No private model contents/paths in tracked reports.

Acceptance: retain actual success/failure evidence, a reproducible local entry
point and a prioritized preparation checklist with remaining exit criteria.
Linux ARM64 record inspection does not close native Linux x64, Windows,
semantic PMX/history compatibility or numerical/GUI/mesher parity.

## Outcome

[Execution report](../reports/pmx-linux-verification.md): all 24 tests pass;
both record inventories exactly match Mac portable observations with input hashes
unchanged and explicit runtime-assembly guards. Startup and initial strict
runtime-difference failures are retained; final VM shutdown succeeded.
[Preparation exit gates](../reports/preparation-exit-gates.md) prioritize semantic
persistence/history, required-platform repeats, matching native sources,
interactive VTK and a pinned analytical solve/CAD shell-junction baseline.

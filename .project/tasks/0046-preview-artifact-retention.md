# Task 0046 — Reclaim completed preview build storage

3 November 2026. Maintainer reports task 0044 seems to work and requests removal
of unnecessary tested apps/DMGs while preserving the documented development
process, before task 0045. This explicitly supersedes older keep-DMG instructions.

Scope: inventory and prune only ignored, generated task 0041–0044 target-build
and earlier desktop-preview package payloads under X/Build/artifacts and
X/Desktop/artifacts. Preserve
tracked source/evidence, small sibling manifests/logs/locks/reproduction/examples,
all job/result folders, installed/user app copies, private models and user state.
Keep the verified Mac solver, shared dependency cache and pinned Python runtime.
Check active processes/mounted images and refuse tracked files or changed trees.

The reviewed plan selects 74 generated directories, approximately 46.32 GiB of
allocated storage. Actual filesystem space reclaimed is measured in the receipt;
APFS sharing/snapshots mean estimates are not a guarantee. Verify all retained
evidence indexes before/after and verify reusable build input hashes without
rebuilding an app or rerunning numerical/platform suites for this cleanup.

Record artifact availability as purged/historical, keep original verification
results/identities intact, and document a bounded retention/rebuild procedure.
No application/numerical/default/format/frontend change or task 0045 work.
Existing correctness/four-target/release gates and D051 research publication stay.

Completed: all 74 selected directories removed, observed free-space gain
41.98 GiB; 230 GiB available afterward. All 292 retained evidence files verify
unchanged, nine reusable solver/runtime hashes match, pinned native sources verify,
Qt/VTK imports and Mac recipe dry plan pass. No new app build/numerical suite.

Actual plan, commands, outcome and reusable-input readiness:
[storage cleanup report](../reports/storage-cleanup.md).

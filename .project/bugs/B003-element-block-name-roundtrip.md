# B003 — element-block name lost during mesh export

First affected commit: 384edea2f24bf51b57cac60d02f87e1b37dd77de, B001 fix.
Observed in [pipeline 3019186769](https://gitlab.com/aleksa9275/pre-po-max-x/-/pipelines/3019186769),
[shared-core-linux-x64 job 17675531644](https://gitlab.com/aleksa9275/pre-po-max-x/-/jobs/17675531644).
Downloaded artifact archive and original failed verifier JSON/log are retained in
`reports/core-pipeline-regression/`; archive SHA is in failure-summary.json.

Fixture: `X/Core/MeshDeck/unit-cube.inp`. Inspect → export-mesh → inspect changed
elementBlocks[0].name from CUBE to null. Bounds/counts, node/element IDs,
connectivity/formulation, node sets and element sets survived. The existing full
CLI equality check correctly failed. The earlier B001 fix removed all inline
ELSET names to prevent duplicate solver rows; that also lost block identity.

Fix: preserve original CalElement inline names and track the union of their
members. Explicit ELSET output contains only remaining members not already
defined inline; omit empty residual definitions. Anonymous and repeated named
blocks retain identity, and other sets retain their full memberships.

The full CLI equality assertion stays unchanged. Existing mesh roundtrip checks
now also compare block names; one focused regression covers repeated named plus
anonymous blocks, overlapping membership and an independent set. B001's cube
regression still requires membership once, now through its preserved inline name.
Actual native solve checks eight stresses/reactions and original DAT import.

The previous local analysis suite ran mesh unit checks but not the downstream
Core CLI description comparison. Shared writer changes must run both affected
Core and Analysis verifiers; this reuses existing checks. No numerical tolerance,
known correctness gate or Linux CI requirement is weakened. Hosted acceptance of
the fix is recorded in the task/report after exact-commit verification.

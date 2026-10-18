# Task 0032 — FRD/DAT publication and hosted evidence

2026-10-18. The maintainer explicitly requests committing/pushing at the end of
task 0031 within the available usage. Review and publish tasks 0030/0031 normally
to origin/research/native-feasibility, verify the actual remote SHA, inspect the
exact-commit GitLab Linux x64 pipeline and download/compare new results artifacts.
Record closing evidence with a documentation-only follow-up under this same
publication instruction. Do not infer hosted success from local ARM64 or a prior
commit. Existing correctness failures and all release gates remain. No force,
upstream/x/main/release writes or additional feature scope. The task ends after
publication verification; no new native solver/frontend/default/policy selection.

[Publication record](../reports/results-publication.md) records actual commits,
CI status/artifact checks and next engineering work; do not assume completion
until those observations are present.

## Publication complete

Tasks 0030/0031 implementation is published at **62c7de1b**; independent remote
verification and exact-commit pipeline **#2960686368** pass all five native Linux
x64 jobs. Three hosted results previews verify clean commit, 78 checks/nine CLI
controls and matching ten source/tool/dependency/engineering groups against both
ARM64 hosts. Archive retrieval remains unverified; preview-based semantic evidence
is explicitly distinguished. Closing task 0032 is documentation/evidence only.
[Actual publication evidence](../reports/results-publication.md). Both correctness
failures/tetra gate and every remaining Windows/net48/RC2/release gate stay.
Earlier local/uncommitted wording records the historical implementation phase.

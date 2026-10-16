# Task 0016 — Publish shared data libraries and verify hosted execution

2026-10-16, Europe/Belgrade. Maintainer explicitly requests committing/pushing
completed task 0015 and continuing implementation toward a working build.
This supersedes task 0015's earlier uncommitted-only publication state.
Publish the reviewed source/evidence/records to origin/research/native-feasibility,
then verify the actual remote SHA and exact-commit native Linux x64 pipeline,
source/tool fingerprints and portable data/mapping outcomes. Closing hosted
evidence is included. No force push, upstream write or x/main integration.

Completed: commit **236b1a2e54fe49a218f040b6aebff33217f8722d** is pushed and
remote-verified. Exact-commit pipeline **#2956740201** passes both native Linux
x64 jobs (#17245079895 research, #17245079896 shared core). Downloaded JSON
independently matches published Git source/tool hashes and all ARM64 portable
mapping/data/type/CLI outcomes. [Publication evidence](../reports/shared-core-data-publication.md).
Expanded native Windows execution remains pending. Closing evidence publication
is included in this task; the next element implementation remains local.

Prior checkpoint: reviewed local increment passes Mac/Linux ARM64 (25 mapping,
30 data, seven type contracts, 11 CLI controls, four rejection controls).
Implementation/publication and hosted verification were in progress. Expanded
native Windows execution remains pending; older Windows probes supply data
observations, not a new-assembly pass. Preserve the remaining release gates.

Continue with a separately scoped shared-core implementation task after
publication. Do not infer frontend/default-format/native-tool policy choices
from the maintainer's encouraging CrossOver/native Windows comparison.

# Shared data-library publication and native Linux x64 evidence

Verified observation, 2026-10-16 Europe/Belgrade. Maintainer explicitly requested
committing/pushing completed task 0015 and continuing toward a working build.
Commit **236b1a2e54fe49a218f040b6aebff33217f8722d** was pushed normally to
origin/research/native-feasibility; `git ls-remote origin
refs/heads/research/native-feasibility` returned that exact full SHA.

[Pipeline #2956740201](https://gitlab.com/aleksa9275/pre-po-max-x/-/pipelines/2956740201)
passed [research #17245079895](https://gitlab.com/aleksa9275/pre-po-max-x/-/jobs/17245079895)
and [shared core #17245079896](https://gitlab.com/aleksa9275/pre-po-max-x/-/jobs/17245079896).
The shared log shows exact checkout, Intel Xeon Platinum 8581C native x64,
successful artifact upload and Job succeeded. Image ID:
`sha256:9cd0d6fa04def99891bf4d5a29eb9a3878b6041f9cc25cb389ea0df2177d23fd`;
registry digest `sha256:0d99ebf1ccad15037b5c98c9fe8979d6b8dbac23812feae2277a0b277b5c5ffa`.
SDK 10.0.402/.NET 10.0.13. No translated x64 execution is used.

The actual artifact was downloaded through GitLab's authenticated Download link.
Direct unauthenticated raw access returned 404; GitLab Pages preview was also
unavailable. [Retained JSON](shared-core/data-slice/linux-x64/report.json),
[sanitized normalized trace](shared-core/data-slice/linux-x64/job-trace.txt),
[independent verification](shared-core/data-slice/linux-x64/verification.json).
Artifact SHA-256: `c6004b005cb1d64a4eafe4e1f16ff6a7c0a9610c932b2ba0047b1d690ad60c86`.

The report identifies a clean checkout at the exact published SHA. Every
engineering-source/tool fingerprint was checked against published Git objects
(normalizing the harness's relative path for Git lookup). All source/tool rows,
25 mapping checks, 13 vector results, 30 data checks/observations, seven type
contracts, nine mapping CLI controls, two data CLI controls and four verifier
rejection controls match the retained Mac/Linux ARM64 outcomes. Four existing
test-only SYSLIB0050 warnings are retained; no unsafe serializer was enabled.

This closes task 0016's publication/native x64 follow-up. Native Windows
execution of the new library assembly slice is still pending. CrossOver/native
Windows legacy model/result payload agreement remains useful bounded evidence,
not full persistence/history/clone equivalence or native platform/UI acceptance.
The next local element-kernel implementation is separate from this published
data slice. Existing CAD/interactive VTK/native-source/compiler-policy gates
remain. No force push, upstream write, x/main merge or frontend/default-format
selection occurred.

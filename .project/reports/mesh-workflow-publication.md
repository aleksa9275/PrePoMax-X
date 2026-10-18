# RC2 replay and portable mesh workflow publication

2026-10-18, Europe/Belgrade. [Task 0021](../tasks/0021-mesh-workflow-publication.md).
The maintainer explicitly authorizes publication of completed task 0019/0020
work, then requires a proposed next-step explanation and approval before any
new feature implementation. Publication and closing evidence are in scope.

Verified pre-publication: branch research/native-feasibility, parent
2f2eca945c8acad0c3b902537f95055e67be6a42; configured origin is the maintainer's
fork. Task 0019/0020 retained report hashes independently match their manifests.
The ten replay/source guards pass; the engineering implementation and package
are the already-tested local slice. No new feature is added for publication.

The existing six native Mac/Linux ARM64 reports each retain 218 accepted checks,
39 CLI/four data controls, both original correctness failures and the quadratic
tetrahedron measurement gate. The same 125-entry development ZIP is verified
on both hosts, including source rebuild/export/reopen/tamper checks. Native
Windows and full original net48/RC2 application validation remain pending.
See [implementation evidence](portable-mesh-deck-workflow.md).

## Verified publication and native Linux x64 evidence

Implementation commit: **47f17be6657b470cff814d50b97c79fada52040a**,
`Add portable INP mesh workflow and pinned RC2 source replay` (parent above).
Normal `git push origin HEAD:refs/heads/research/native-feasibility` succeeded;
independent `git ls-remote origin refs/heads/research/native-feasibility` returned
that exact SHA. Origin/master remains the upstream mirror f6273e39. No x/main
integration, upstream write or forced history.

[Pipeline #2960334103](https://gitlab.com/aleksa9275/pre-po-max-x/-/pipelines/2960334103)
**passed**, with both
[research-linux-x64 #17265478067](https://gitlab.com/aleksa9275/pre-po-max-x/-/jobs/17265478067)
and [shared-core-linux-x64 #17265478068](https://gitlab.com/aleksa9275/pre-po-max-x/-/jobs/17265478068)
passed. Authenticated GitLab UI independently displayed the commit and all
statuses. Shared-core runner reports native Intel Xeon Platinum 8581C x64,
Linux container SDK 10 image digest
`mcr.microsoft.com/dotnet/sdk@sha256:0d99ebf1ccad15037b5c98c9fe8979d6b8dbac23812feae2277a0b277b5c5ffa`.
Ten source/replay guards pass. Current/RC2/post-RC2 each pass 25 mapping,
30 data, 95 accepted element and 68 mesh checks (218 total), 39 CLI/four data
controls, while retaining both original correctness failures and the tetra gate.
This is bounded shared-slice acceptance, not full native application acceptance.

Downloaded [job artifacts](https://gitlab.com/aleksa9275/pre-po-max-x/-/jobs/17265478068/artifacts/download)
were inspected locally, not inferred from green badges. All three reports have
clean source HEAD 47f17be6. Each report's 48 source hashes and 36 tool hashes
match the published checkout; nine portable outcome groups exactly equal the
corresponding retained Mac ARM64 report after removing runtime metadata.
[Independent download verification](mesh-workflow-publication/download-verification.json)
retains hashes/counts and comparisons. Downloaded reports are retained alongside
it as linux-x64.json, rc2-linux-x64.json and post-rc2-linux-x64.json.

Inner `X/Core/artifacts/development-build/PrePoMaxX-Core-development.zip`:
586403 bytes; SHA-256
`c89895e562a196b63b4e6d83cf332708dab0f801605c32dd4230df971e7ca242`.
All 125 manifest entries verify; all 90 `source/` entries byte-match `git show
47f17be6:<path>`. Manifest records clean source 47f17be6. Downloaded package/
verification reports match the actual ZIP hash. Hosted source rebuild, three
published tools, unit-cube export/reopen, overwrite rejection, tetra gate and
three tamper controls pass. Running the actual downloaded CI ZIP through
`python3 X/Core/check-package.py --archive <CI ZIP> --report <report>
--expect-os Darwin --expect-architecture Arm64` also passes native Mac ARM64,
including extracted-source rebuild and the same tool/gate/tamper checks.
[Mac verification](mesh-workflow-publication/downloaded-package-macos-arm64.json).
The ZIP remains an ignored local artifact; no binary/private model is committed.
The older dirty-source local ZIP has a different documented hash by design.

## Approval boundary and remaining work

Task 0021 closes with documentation/evidence and
[the proposed next sequence](../proposals/next-native-workflow.md). No proposed
model/deck, native-solver, results, frontend or persistence feature has begun.
Wait for the maintainer to read and approve before implementing those steps.
Windows can be deferred during subsequent approved coding; native Windows x64,
full original net48/RC2 comparison, four-target coverage and full workflow/
UI/persistence/CAD/patched-source/release gates remain mandatory. The two
correctness failures and host gate remain unchanged. Closing documentation does
not change the exact code proven by pipeline #2960334103.

# Task 0018 — Publish element kernel and provide a verified CI development ZIP

2026-10-16, Europe/Belgrade. Maintainer explicitly requests committing/pushing
task 0017 and choosing a bounded task within approximately 20 percentage points
of the five-hour usage allowance. Initial account read: 72% used, 28% remaining.
Usage is an account allowance, not an exact wall-clock estimate. No reset used.

Chosen task: make the existing runnable development ZIP available as a native
Linux x64 CI artifact, including hash verification, extracted source rebuild,
published CLI smoke tests and tamper controls. Reuse package.py and the existing
job/image/toolchain. No engineering algorithm, serializer/frontend/native-tool
policy or integration change. Preserve both open correctness failures and the
quadratic-tetrahedron host gate.

Review/publish task 0017 plus this small build-delivery increment to
origin/research/native-feasibility; verify remote SHA, exact-commit hosted job
and downloaded ZIP/report. Closing publication evidence is included. No force
push, upstream write or x/main merge. The earlier uncommitted-only restriction
is superseded for this requested publication. Native Windows new-slice checks
and all existing release gates remain pending.

Status: complete within bounded scope. Task 0017 and build-delivery increment
are published at b83fa49f96559c1aeb583d7c527647aab0342354, remote SHA verified.
Pipeline #2956835416 passes both native x64 jobs. Actual downloaded ZIP/source/
tool hashes independently verified; that x64-produced bundle also rebuilds/runs
on native Mac ARM64. [Evidence/download](../reports/shared-core-build-delivery.md).
Usage 72% to 87% before closing records; no reset used. Stop at this boundary.

Local verification passed on Mac and native Linux ARM64: prior 25 mapping/30
data checks, 95 accepted element/host checks, 28 CLI controls, four data-evidence
controls; both open correctness failures remain. Archive verification checks
88 manifest entries, rebuilds source, runs published examples and the tetrahedron
gate, and rejects changed binary/unmanifested file/parent traversal controls.
The cached offline Podman image/VM is reused and stopped after testing. Reports
are retained in reports/shared-core/build-delivery/. No development ZIP/private
model/binary is staged in Git; CI will upload the ZIP as a job artifact.

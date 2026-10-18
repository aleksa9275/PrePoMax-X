# FRD/DAT implementation publication

2026-10-18. [Task 0032](../tasks/0032-results-publication.md) publishes the completed
[FRD task 0030](portable-frd-fields.md) and [DAT task 0031](portable-dat-histories.md)
under the maintainer's explicit commit/push instruction. Normal origin research-
branch publication only; no upstream/x/main/release write or force push.

## Prepublication scope

Original FRD/DAT decoders, field math/history entries and required shared helpers
retain original source/type/assembly ownership through mechanically checked
partials. Original net48 orchestration/persistence remain included once. New
bounded inspection commands are modern-only; neither runs a solver nor selects
an application persistence format, frontend, backend/default/precision or GPU.
Existing source policies and both strict correctness failures/tetra gate remain.

Local three-pin Mac/Linux ARM64 evidence and source/dependency/tool comparisons
are linked from the DAT report; earlier FRD-only reports are historical checkpoint
evidence. The existing analysis regression is rerun for the small shared naming-
helper extraction. Review excludes ignored private models, archives, binaries,
cache/build outputs and any machine credentials. Source whitespace/ownership and
exact package archive fingerprints must pass before publishing.

Implementation and independently verified hosted evidence are recorded below.
Archive retrieval failed; artifact contents were verified through authenticated
preview JSON instead. This distinction is retained rather than claiming a download.

## Next engineering work

Recover reproducible native CPU CalculiX/compiler/open-backend dependency builds,
validate actual backend dispatch and connect the first real deck → solve → FRD/
DAT workflow against analytical/Windows expectations. Complete full results graph
and interactive VTK host proof next, followed by frontend/persistence/CAD parity.
No native solver acceptance follows from reading retained Windows output. Latest
Windows/net48/RC2 and full four-target/installers/Homebrew gates remain. Normal
maintainer commit/push policy resumes after this scoped publication.

## Verified publication and hosted artifacts

Implementation **62c7de1bea234acc7aea16ee7c11283822f86501** is on
origin/research/native-feasibility, independently verified with git ls-remote.
Origin/master remains f6273e39983e06042ae8b06e9a3dd0f729ea4b91.
[Exact-commit pipeline #2960686368](https://gitlab.com/aleksa9275/pre-po-max-x/-/pipelines/2960686368)
**passes all five native Linux x64 jobs**: research #17267558861, shared-core
#17267558862, analysis #17267558863, execution #17267558864 and new results
#17267558865. This status was read from authenticated GitLab for this exact SHA.

All three results artifact JSON previews identify clean HEAD 62c7de1b, Linux X64,
78 accepted checks, nine CLI rejection controls, and 163 current/RC2 or 164 post-
RC2 source snapshot rows. Ten groups (sources, tools, shared analysis guards,
FRD/DAT fixture fingerprints, package archives, tests, FRD output, DAT output,
CLI controls) match both retained ARM64 hosts exactly after runtime metadata is
removed. Full compiled engineering source/modern tool bytes were independently
checked against the published commit. [Hosted observations/comparisons](results-publication/hosted-preview-verification.json)
and [independent reproduction](results-publication/verify-hosted-preview.py)
retain semantic SHA256 results; numbers use IEEE754 binary64 big-endian encoding
for a consistent JSON fingerprint across JavaScript and Python.

**Evidence transport limitation:** IAB archive downloads timed out, and an
unauthenticated direct GitLab request returned 404. No credentials were extracted
or access policy changed. Instead, the generated GitLab Pages preview links
exposed the actual JSON in the authenticated browser; its DOM text was parsed and
group fingerprints computed with WebCrypto, then independently recomputed in
Python against local evidence. No archive/raw-file byte download verification is
claimed, and no hosted raw JSON copy is retained locally. This does not change
the independently observed pipeline pass or the inspected artifact content.

Local source guards pass 9 results, 9 analysis, 4 execution and 10 core replay
checks. Six local analysis reruns retain 331 accepted checks and both known strict
correctness failures/tetra gate. Authored content/link/staged-blob review passes;
whitespace findings are confined to mechanically preserved original source in
new legacy partials (no cleanup that would invalidate byte/body preservation).
Private models, binaries, archives and caches are excluded from publication.

Task 0032 closes with documentation/evidence only. No new feature scope or solver/
Windows/net48/RC2/full-graph/four-platform/release acceptance is implied. Normal
maintainer publication policy resumes after this scoped commit/push.

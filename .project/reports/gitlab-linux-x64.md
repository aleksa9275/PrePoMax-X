# Task 0002 — Native Linux x64 acceptance

Date: 2026-10-14, Europe/Belgrade. **Verified observation: both pinned source
revisions pass on GitLab's native Linux x64 hosted runner and match the saved
macOS ARM64 observations. Task 0002's bounded acceptance criteria are complete.**

## Publication and execution

The maintainer committed/pushed the prepared Podman/CI tooling and evidence as
`822bae2528be6e38df6d472fc979c36b9f3e4d27`, title `Phase 0 verification`, on
`feature/core-feasibility`. This commit extends task 0002; its title does not
change the milestone scope. The checkout was clean and tracked origin's feature
branch when this verification began.

The authenticated pipeline list showed only the earlier failed pipeline after
the push; no cause for the absence of a new push-triggered pipeline was
established. The agent submitted the configured manual **New pipeline** for
`feature/core-feasibility`, without variables, under the existing verification
authorization. [Pipeline #2947482796](https://gitlab.com/aleksa9275/pre-po-max-x/-/pipelines/2947482796)
and [job #17176590675](https://gitlab.com/aleksa9275/pre-po-max-x/-/jobs/17176590675)
both passed at that exact commit. Source is Web. Pipeline created 19:10:46;
job started 19:12:37 and its log reports success at 19:13:37; the pipeline
finished at 19:13:46, Europe/Belgrade. Queue wait was
1 minute 49 seconds. No commits, pushes, merges, settings changes, account
verification submissions or historical-pipeline retries were performed by the
agent. This successful run establishes that the previous identity restriction
no longer prevents this account from executing the job.

## Native architecture and runtime provenance

Verified observations from the retained artifacts and execution log:

- Runner #54907241, `k8s.saas-linux-small-amd64.runners-manager.gitlab.com/default`,
  tag `saas-linux-small-amd64`, executable architecture `linux/amd64`;
  GitLab Runner `19.5.0~pre.2316.g3c07c5b0`.
- `docker+machine` executor, x86-64 helper image; log identifies native host CPU
  `INTEL(R) XEON(R) PLATINUM 8581C CPU @ 2.10GHz`.
- Artifact host OS/architecture Linux/x86_64; .NET process and OS architecture
  Linux/X64. No translated container route was selected.
- SDK 10.0.402, runtime .NET 10.0.13. SDK image reference
  `mcr.microsoft.com/dotnet/sdk:10.0`, resolved digest
  `sha256:0d99ebf1ccad15037b5c98c9fe8979d6b8dbac23812feae2277a0b277b5c5ffa`;
  execution image ID
  `sha256:9cd0d6fa04def99891bf4d5a29eb9a3878b6041f9cc25cb389ea0df2177d23fd`.

The tag follows patch updates; this records the actual execution rather than
claiming a locked release build. Native x64 acceptance is supported by the
hosted runner/CPU log and artifact runtime together, not just a runtime enum.

## Tests and artifact verification

Actual hosted commands after ephemeral Python/Git installation and public
release-branch fetch:

```sh
python3 X/Feasibility/Core/test_probe_evidence.py
python3 X/Feasibility/Core/run-ci.py
```

Six comparison/orchestration regression tests passed. The two `success: false`
lines within those tests are deliberately mocked failure-contract cases;
the real probe invocations subsequently both succeeded.

| Revision | Pin | Analytical/STL checks | CLI contracts | Mac comparison |
|---|---|---|---|---|
| Baseline | de8f73032a72746e3d6d9afd53d9fbd289eb310a | 23 passed, 0 failed | 2 passed | Exact portable-observation match |
| v2.6.0 replay | 9e91252563739ee5304cea16c34863dfb17a74d5 | 23 passed, 0 failed | 2 passed | Exact portable-observation match |

The browser's job **Download** control saved the artifact archive. Python's
`zipfile` read only the two expected JSON members; no arbitrary archive paths
were extracted. Original JSON bytes are retained as
[baseline](core-feasibility/gitlab/linux-x64-baseline.json) and
[release replay](core-feasibility/gitlab/linux-x64-v2.6.0.json).

Independent local checks asserted both source pins, success/count/contracts,
Linux/X64 process and OS, Linux/x86_64 host, exact feature commit/pipeline/job
identifiers, and tooling hashes against the published checkout. Each reference
file SHA-256 was checked and `probe_evidence.comparable` recomputed against the
saved Mac JSON, rather than trusting only CI's `matches` flag. Both matched.
Cube geometry remains 12 triangles and bounds [0,0,0]–[1,1,1].

Runner/image identifiers, artifact/archive SHA-256 and retained-evidence hashes
are also in [machine-readable provenance](core-feasibility/gitlab/pipeline-2947482796-provenance.json).

Artifact SHA-256:

- Baseline: `9effaf7cc752d6441ca84e3440c2456efac7f7ebf826501e5e47ac6df2954ca5`.
- Replay: `bd8d549de7cbd4120cd7be05d3c0d92b1e9d0ecedd214a8dd18c4094cf38d73c`.

The [rendered execution log](core-feasibility/gitlab/job-17176590675-rendered-log.txt)
retains line numbers/timestamps and the resolved image/CPU evidence. The
artifact uploader's token fragment is redacted and trailing whitespace removed
from the rendered text before final retention. The
[pipeline screenshot](core-feasibility/gitlab/pipeline-2947482796.png) supports
the visible outcome; JSON and source/runtime evidence are decisive.

## Scope and handoff

Acceptance 4 and the native x64 portion of 5 are now satisfied. Together with
the earlier Mac fixture/math/source-closure and isolated upstream replay
evidence, task 0002 is complete. The seven selected upstream files are identical
across the replay pins: replay mechanics, not adaptation to changed source,
were demonstrated. The retained three upstream-source warnings and parser
limitations remain unchanged.

This is a seven-file compute feasibility result. Windows oracle, Mac x64,
whole-core, PMX/history, controller, rendering/selection, CAD/meshing and solver
parity remain unproved. No production source/project changes were made.
No x/main integration or further implementation phase is authorized by this
pass. Next review is feature integration and the next bounded source/PMX
investigation; GUI/serializer/native dependency decisions remain gated.

The maintainer subsequently authorized the agent to commit/push this closing
evidence during the 2026-10-14 continuation. The pass itself does not authorize
feature integration; see current STATUS/AGENTS for the scoped continuation. Changed-document links, JSON/provenance checks and `git diff --check`
pass. No unrelated historical or live FEM suites were rerun.

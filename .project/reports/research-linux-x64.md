# Task 0012 — Native Linux x64 research acceptance

Verified 2026-10-15, Europe/Belgrade. Research implementation/evidence commit
`24c790ac5f40f976ad8d606a509d5ec9ce3509d8` was committed and pushed to
origin/research/native-feasibility with explicit maintainer authorization.
No x/main integration, upstream write, force push or production change.

Push [pipeline #2951491552](https://gitlab.com/aleksa9275/pre-po-max-x/-/pipelines/2951491552)
and [research-linux-x64 job #17205619186](https://gitlab.com/aleksa9275/pre-po-max-x/-/jobs/17205619186)
**passed**. The authenticated UI showed Job succeeded, successful artifact upload,
runner #54907241 and tag saas-linux-small-amd64. Duration 1 minute 11 seconds,
queued 10 seconds. Six JSON artifacts were downloaded through the browser and
independently checked against source/tool hashes and expected checks.
The direct unauthenticated API request returned 403; no credentials were extracted.

## Actual execution and checks

Linux x86_64 on **AMD EPYC 9B45**, runner executable linux/amd64, Python 3.12.3,
GCC 13.3 with x86_64-linux-gnu target, SDK 10.0.402/.NET 10.0.13. Rendered job log
identifies SDK image `sha256:9cd0d6fa04def99891bf4d5a29eb9a3878b6041f9cc25cb389ea0df2177d23fd`,
digest `mcr.microsoft.com/dotnet/sdk@sha256:0d99ebf1ccad15037b5c98c9fe8979d6b8dbac23812feae2277a0b277b5c5ffa`.
Retained observations:

- [Research runtime/CI/compiler and Mac comparisons](local-completion/linux-x64/research.json)
- [24 PMX synthetic tests](local-completion/linux-x64/pmx-synthetic.json)
- [Three scalar binding/mutation controls](local-completion/linux-x64/pmx-values-synthetic.json)
- [Four shell contracts/two negative controls](local-completion/linux-x64/shell-fixtures.json)
- [Structured kernel](local-completion/linux-x64/meshing.json): 13 original
  vectors, 17 independent native and seven managed checks, 1,728 count comparisons,
  existing mutation/missing-input/CLI controls. Full C# mapping still reaches its
  measured MessageBoxes compile boundary. **Compiler defaults**, no contraction
  override; all vectors pass on this native x64 runner.
- [Engineering data](local-completion/linux-x64/core-data.json): 30 checks/two
  CLI contracts, portable observations matching Mac exactly.
- [Independent artifact verification and hashes](local-completion/linux-x64/verification.json)

The exact source baseline remains `de8f73032a72746e3d6d9afd53d9fbd289eb310a`.
Structured sources/check outcomes/count signatures match the Mac reference;
native area uses 1e-12 tolerance for rounding. Test/tool/source hashes and CI
commit/job identities were independently verified after download. Only explicit
non-secret CI fields were captured. No private model was used in hosted CI;
the legacy private inventory comparison remains Mac/Linux ARM64 evidence.

## Limits and next session

This closes native Linux x64 execution of the **public synthetic research suite**,
not application/PMX reconstruction, history, interactive GPU, native mesher/solver
or release parity. It does not resolve Linux ARM64's default GCC -O2 vector
failure: its contraction-off pass remains an explicit diagnostic control, with
production numerical build policy open. Job-setting drift in private PMX resave
also remains a Windows reference question.

All feasible bounded local preparation and initial hosted verification are now
recorded. Resume [task 0011](../tasks/0011-windows-reference-validation.md) via the
[Windows handoff](../handoffs/windows-next-session.md), using the published research
branch. Matching modified native sources and real UI/required-platform workflows
remain open. The closing evidence commit changes documentation/artifacts only;
research implementation stays at the tested source above.

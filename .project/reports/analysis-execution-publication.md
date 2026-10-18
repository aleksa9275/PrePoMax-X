# Analysis/execution/research publication and reset handoff

2026-10-18, [task 0029](../tasks/0029-analysis-execution-publication.md).
Maintainer explicitly requests a bounded task followed by committing/pushing
all current work and stopping until continuation after reset.

## Reviewed scope

- Tasks 0022/0023: original-owned equation/material/static-deck partial assemblies,
  unchanged engineering writers and bounded C3D8 analysis CLI, regression/evidence.
- Task 0024: native process/preflight/original STA-CVG boundary and unchanged
  organized official CalculiX 2.22 source/license/per-file manifest.
- Tasks 0025–0027: exact RC2 Windows solver identity, PARDISO-free functionality,
  solver/thread/GPU primary research and the maintainer's current policy.
- Task 0028: tested non-mutating CPU thread planner/CLI; no GUI/default/thread
  execution policy or active scheduler change. GitLab execution uses a subreaper.

Pre-publication parent is ed2dcb4d6f579ec6a8c11a1ef0437457a2d22fab on
research/native-feasibility. Origin default remains master at upstream-mirror
f6273e39983e06042ae8b06e9a3dd0f729ea4b91; independent ls-remote confirms research
is still the parent before publication. Only normal origin research-branch
publication is authorized. No x/main, upstream or public release branch write.

Mechanical extraction/source-closure/type-ownership checks pass. Fourteen new
thread checks plus 33 earlier execution/monitor checks pass all three pins on
Mac/Linux ARM64; current Mac analysis rerun passes its 331 accepted checks.
Prior six analysis runs remain verified separately. Both strict correctness
failures are retained, not repaired or reclassified. Original net48 projects
include extracted legacy members; full net48 build still requires Windows.

Content audit excludes ignored private PMX, binaries, archives, caches and build
outputs. Recovered third-party source retains original license/bytes and is
explicitly not release-ready. New research evidence is public synthetic data or
metadata, not the private model. No unpublished numerical result is claimed.

Published SHA, exact-commit hosted status and downloaded artifacts are recorded
in the closing update after the normal push; do not infer them from this initial
publication record.

## After reset

Stop feature work at this handoff. Continue when the maintainer resumes:

1. Read current STATUS/DECISIONS and this publication record; preserve any closing
   evidence and check actual remote/CI before starting a new increment.
2. Recover/build a reproducible native CPU CalculiX with existing open backends,
   or continue original FRD/DAT field import while build dependencies are recovered.
3. Later run representative engineering comparisons, verifying actual backend
   dispatch, shell/modal/buckling correctness, memory and thread scaling.
4. Integrate solver advice/75% automatic/manual execution only against validated
   capability profiles; the new planner alone does not enforce a running budget.

Panua machine-bound licensing remains excluded; new backends only if existing
open choices cannot meet required functionality/capacity/performance. Native
Windows/net48/RC2, both correctness failures/tetra gate, frontend/persistence/CAD,
all corresponding source, four required targets and installers/Homebrew remain.
No frontend/default serializer, numerical/precision/backend substitution or GPU
commitment follows from this publication.

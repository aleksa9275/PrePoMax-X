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

## Verified publication and downloaded evidence

Implementation **993f9263f8770bee5b75d2cca3b07baaf2c1097e** was pushed normally
and independently verified with git ls-remote. Origin/master remains f6273e39.
[Pipeline #2960594131](https://gitlab.com/aleksa9275/pre-po-max-x/-/pipelines/2960594131)
passes all four jobs: research #17266997747, shared-core #17266997748,
analysis #17266997749 and execution #17266997750. Status was read in authenticated
GitLab UI for that exact commit, not inferred from a different branch pipeline.

Actual downloaded analysis and execution artifact ZIPs were read locally.
All six reports identify clean HEAD 993f9263. Analysis source/tool/dependency
fingerprints and engineering outcomes match retained Mac reports after removing
runtime metadata. Each pin retains 331 accepted checks and the two explicit
open correctness checks. Execution's 47 checks/13 CLI rejection controls and
source/tool/monitor outcomes also match Mac; host CPU counts are validated
individually. [Download fingerprints and comparisons](analysis-execution-publication/download-verification.json)
retain archive/report hashes and the six downloaded reports alongside them.
The current Mac analysis rerun and [review record](analysis-execution-publication/prepublication-review.json)
are retained. Archives/binaries remain outside Git.

Authored/extracted-code whitespace checks pass excluding unchanged vendored
CalculiX source, raw solver outputs and downloaded original README notices;
their original whitespace/line endings are preserved rather than edited.
All 1188 staged CalculiX file blobs independently matched verified working bytes.

These closing changes only add documentation and verification evidence. They
do not extend the code acceptance of implementation 993f9263 or close any
remaining gate. Stop features at this reset handoff until the maintainer resumes.

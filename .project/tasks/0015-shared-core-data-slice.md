# Task 0015 — Mac acceptance and shared engineering data increment

Publication update: maintainer now explicitly requests commit/push in task
0016. Earlier uncommitted-only statements below describe the completed local
checkpoint; they no longer prohibit publishing this reviewed increment.

2026-10-16, Europe/Belgrade. Maintainer explicitly requests importing/publishing
the reviewed Windows commit ac51fc77449da26d9c25ddedd924feda2a55e7db, running
the exact first slice on Mac ARM64 and native Linux ARM64, inspecting its native
Linux x64 CI, then continuing the handoff's bounded metadata/IntegrationScale/
FRD-stream-reader increment. Existing checkout was clean at f1e757f1; verified
bundle imported by auxiliary ref and fast-forward only. Exact commit published
and remote SHA verified. No further implementation commit/push is authorized.

Status: bounded local implementation/verification complete; native Windows and
new-commit hosted x64 follow-up pending. Original first slice passed all four
required targets; pipeline #2956616374 passes both exact-ac51fc77 jobs.

Acceptance completed locally: preserve original source bytes and assembly/type owners;
source-link metadata and IntegrationScale in partial CaeMesh and the internal
FRD stream reader in partial CaeResults. Execute the unchanged 30 DataProbe
checks through project references, compare portable observations with the
retained Windows reference, check assembly ownership/visibility and retain
the original 25 mapping checks/nine CLI controls. Verify native Mac/Linux ARM64
using the cached image and prepare the same verifier for later native Windows/
Linux x64 execution. No private PMX needed.

Retain CAD/interactive VTK/full persistence/history/native-source release gates
and the native Linux ARM64 GCC default -O2 sensitivity. No engineering algorithm,
production net48 project, serializer/frontend, F001 or x/main integration change.
Mac/Linux ARM64 each pass 25 mapping + 30 data checks, seven type contracts,
nine mapping + two data CLI controls and four evidence-rejection controls.
Portable observations/source/tool hashes agree; the old isolated DataProbe
also still passes Mac checks. Evidence and next commands:
[shared-core data report](../reports/shared-core-data-slice.md).

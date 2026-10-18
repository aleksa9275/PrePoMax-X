# Decision register

D044 — Accepted bounded thread-planning implementation and publication,
2026-10-18: maintainer requests one small task within remaining usage then commit/
push current work and continue after reset. Task 0028 implements callable modern-
only CPU advice and read-only CLI; 47 checks/13 rejection controls pass each pin
on Mac/Linux ARM64, with tools/source/outcome comparison. No active scheduling,
settings migration or pinned reference-thread change. Task 0029 authorizes normal
origin research-branch publication of tasks 0022–0028 and closing hosted evidence.
Earlier leave-uncommitted restrictions are superseded for this publication only.
No x/main/upstream/release write, force push or solver/numerical-policy change.
Stop after publication/reset handoff until maintainer resumes. Both correctness
failures/tetra gate and all release requirements remain.
[Implementation](reports/portable-thread-planning.md), [publication](reports/analysis-execution-publication.md).

D043 — Requested solver advice/thread product direction; GPU research,
2026-10-18: maintainer asks for recommendations by analysis and 75% available
CPU threads, with research into NVIDIA/AMD/Apple GPU support and candidate native
libraries. Task 0027 is research/design only. Propose capability/evidence-aware
advice, manual override and max(1,floor(0.75*available logical CPUs)) shared across
jobs; it is not a utilization cap or speed guarantee. Existing SPOOLES/modified
PaStiX first, MUMPS only if required under D042. NVIDIA CUDA paths documented;
AMD HIP via SuperLU_DIST requires integration; no reviewed Apple Metal direct-
solver path identified. No new library/default/precision/affinity/GPU policy is
implemented or benchmarked; detailed rule table/rounding/order are proposals.
No publication. Preserve both correctness failures/tetra gate and all release
requirements. [Research and proposal](reports/solver-guidance-threads-gpu.md).

D042 — Accepted licensing/functionality criterion; research recommendation,
2026-10-18: maintainer rejects Panua machine-fingerprint licensing and requires
a new alternative only if omission of PARDISO cripples useful functionality.
This narrows D041's prior all-backend identity requirement; preserve original
CalculiX engineering semantics and transparent capability reporting. Research
recommends existing SPOOLES/PaStiX evaluation before another backend integration.
No PARDISO-exclusive analysis class was identified in reviewed paths, but native
correctness/capacity/performance are not accepted. In original 2.22 source,
PaStiX modal/buckling selections can use PARDISO when both macros are defined.
Own comparisons are deferred; no solver/default/precision/architecture changes
or publication are performed/selected. Both correctness failures/tetra gate and
all release requirements remain. [Assessment](reports/without-pardiso-assessment.md).

D041 — Verified exact RC2 solver identity, native full-stack decision pending,
2026-10-18: task 0025 proves RC2 uses the unchanged official CalculiX 2.22 Windows
executable and the same five runtime DLLs as the recorded reference. Six backend
choices pass the bounded cube through existing Mac CrossOver; no native ARM/full
solver acceptance. Canonical core source/provider and GUI PARDISO default are
identified. Exact static-library revisions/build/ABI recipe remain incomplete;
Intel MKL/PARDISO has no identified native ARM64 distribution. Maintainer requires
complete identical software: do not hide this through dropped/rewritten solver
choices or a substituted backend. Exact-binary compatibility/worker execution
and native alternative dependencies need an explicit architecture/policy choice,
not inferred approval. No production change/contact/publication occurs.
[Research report](reports/exact-solver-provenance.md).

D040 — Verified bounded native job/source recovery, 2026-10-18: task 0024 keeps
original job/enum/monitor ownership and net48 methods, adds a modern platform
partial/CLI and organized unchanged CalculiX 2.22 source. Current/RC2/post-RC2
pass 33 new process/preflight/monitor checks and four CLI controls on Mac/Linux
ARM64; four mechanical guards pass. Matching native solver/PaStiX/BLAS/patch/ABI/
runtime source chain remains open; no native solve or alternate solver/backend
is accepted. Linux checks require an init reaper; earlier analysis fingerprints
and both correctness failures remain. Work stays uncommitted. Continue original
FRD/DAT field import and source/build recovery, retaining all release gates.
[Evidence](reports/native-job-boundary.md).

D039 — Accepted final repository/source and release organization, 2026-10-18:
maintainer requires all third-party sources in appropriate folders and a public
release branch serving Homebrew/other package managers and native installers.
REPOSITORY_LAYOUT.md records the readable map, additive ThirdParty/Sources
recovery, separate patches/build/cache/artifact areas and planned x/release lane
with immutable versioned artifacts. No public branch/push is performed; original
upstream paths and exact-source/native build/release gates remain. Continue local
implementation under the accepted solver/results sequence.

D038 — Verified bounded complete static deck, 2026-10-18: task 0023 reuses
original section/BC/load/static-step/output types/writers behind mechanically
checked core/legacy partials. The explicit-unit no-overwrite CLI preserves the
analytical cube's IDs/material/12 constrained DOFs/100 N force/output semantics.
Current/RC2/post-RC2 pass 331 accepted checks per build on native Mac/Linux ARM64;
source/dependency/tool/outcome fingerprints match. Nine analysis/ten replay guards
and independent offline-core checks pass. Managed Color retains only Primitives;
full net48/Windows remains unverified. Both original correctness failures/gate
remain. All task 0022/0023 changes are uncommitted. No solver is executed here;
continue matching native execution/results under accepted D036 and all release
gates. [Evidence](reports/static-analysis-deck.md).

D037 — Verified bounded equation/material component, 2026-10-18: task 0022
source-links original types/algorithms and exact upstream NCalc/UnitsNet versions
in an isolated expanded build. Native Mac/Linux ARM64 current/RC2/post-RC2 pass
262 accepted checks/eight material CLI controls with both known failures/gate
retained. Original post-RC2 lamina/composite changes are separately pinned and
exercised; no numerical fix is imported into the baseline. Formatting extraction
and four unused-import removals preserve original net48/type ownership. This
local component writes a material fragment, not a full analysis deck or installer.
CI is prepared, new Windows/hosted execution pending; no publication authorized.
Continue the accepted sequence and retain all release delivery/compatibility gates.

D036 — Accepted next implementation and installable desktop objective,
2026-10-18: maintainer accepts proposals/next-native-workflow.md. Proceed through
original model/deck, matching native solver and original result readers in tested
increments; Windows can follow local portable coding. Task 0022 begins equations/
materials. End-user delivery requires Windows EXE/MSI, macOS DMG, Linux DEB/RPM
or equivalent and Homebrew across the required architectures. Apple Developer ID
will be available if needed. RELEASE.md records installation/upgrade/signing/
clean-machine acceptance. No new publication, frontend/default serializer,
algorithm/tolerance or silent tool-version decision. D034/D035's stop is lifted
for this accepted sequence; all correctness/native Windows/release gates remain.

D035 — Verified publication, proposed implementation remains unapproved,
2026-10-18: task 0019/0020 published at 47f17be6; pipeline #2960334103 passes
both native Linux x64 jobs. Downloaded evidence and source/tool/125-entry ZIP
checks match the published source and retained Mac outcomes. Task 0021 closing
changes are documentation/evidence only. Proposed model/deck → native solver →
results sequence is recorded in proposals/next-native-workflow.md; wait for
maintainer approval. Native Windows and all correctness/release gates remain.

Use accepted/proposed/deferred labels; a proposal in a spec is not an architectural commitment.

D034 — Accepted publication, new implementation awaits approval, 2026-10-18:
maintainer requests committing/pushing task 0019/0020 work and receiving a next-
step explanation afterward. Task 0021 authorizes normal origin research-branch
publication plus exact-commit CI/artifact verification and closing evidence.
Do not start proposed model/deck/solver/results or host/persistence features
until the maintainer reads and approves them. Keep both correctness failures/
measurement gate, source ownership and remaining release gates unchanged.

D033 — Accepted local implementation continuation, 2026-10-18: maintainer asks
to proceed while preparing Windows for GitLab. Task 0020 delivers original INP
mesh parsing through a mechanically checked partial reader and a CaeModel
library slice, original element deck formatting, explicit input/output adapters
and a usable mesh CLI. Preserve original assembly/net48 ownership and algorithms;
separate framework-only StandardValueAttribute unchanged from its UI editor.
Mac/Linux ARM64 current/RC2/post-RC2 pass 218 accepted checks/39 CLI controls
with two original correctness failures retained. New source/binary package and
Windows follow-up are prepared. All implementation stays uncommitted; no frontend/
default serializer, x/main, publication, native-tool or numerical-policy change.
Mesh-only completion does not establish full model/deck/solve/results parity.

D032 — Accepted RC2 sync/implementation continuation, 2026-10-18: maintainer
requests syncing the fork, comparing Matej's 3.0.0 RC2 and accelerating coding
toward a cross-platform release near upstream stable. Task 0019 supersedes the
0018 stop for this continuation. Sync origin/master by normal ff-only update
to f6273e39; preserve RC2 marker 912fb3d0 separately from later composites work.
Add reviewed snapshot replay while retaining baseline/source/behavior gates.
Further implementation/evidence remains uncommitted under normal workflow;
no x/main merge, upstream write, force push, frontend/default serializer or
numerical/tolerance/native-tool substitution is selected. Whole-application
release parity remains open. Use a real mesh/deck/solve/results workflow as the
recommended next implementation milestone; host/persistence choices need proof.

D031 — Verified element/build publication, 2026-10-16: b83fa49f is pushed and
remote-verified; pipeline #2956835416 passes both native x64 jobs. Downloaded
framework-dependent ZIP has verified source/tool fingerprints and rebuilds/runs
on Mac ARM64. Both open original-source correctness failures remain, with the
tetrahedron host gate. Task 0018 closes within its budgeted scope; no broader
feature, numerical-policy, frontend/serializer or integration decision follows.

D030 — Accepted bounded publication/build-delivery task, 2026-10-16: maintainer
requests committing/pushing task 0017 and a small task within 20% of the
five-hour allowance. Task 0018 delivers the existing framework-dependent core
ZIP through native x64 CI with checksum/source-rebuild/CLI/gate verification.
Retain the two numerical/classifier failures; no algorithm, frontend/default
format, native-tool or integration policy is selected. Stop at this boundary.

D029 — Local element-kernel increment, 2026-10-16: under the maintainer's
continued-build instruction, task 0017 source-links original element families
and GeometryTools with one exact unused WinForms import removal, preserving
algorithms/type ownership. Mac/Linux ARM64 accepted-scope checks pass, but two
strict original-source correctness failures remain: quadratic tetra integration
bias and missing pyramid classification. Retain failures/source-moment evidence;
gate quadratic tetrahedra in the development host instead of changing numerical
code/tolerances. This is not full element acceptance. The runnable CLI/source
bundle is local; new Windows/x64 and existing release gates remain pending.

D028 — Verified data-slice publication/native x64 acceptance, 2026-10-16:
236b1a2e is pushed and remote-verified. Pipeline #2956740201 passes both jobs;
the downloaded shared-core artifact independently matches published source/tool
hashes and ARM64 mapping/data/type/CLI outcomes. Native Windows execution of
this new assembly slice is still pending; earlier probe data agreement is not
a substitute. Task 0016 includes this closing evidence publication.

D027 — Accepted publication/implementation continuation, 2026-10-16: maintainer
requests committing/pushing completed task 0015 and continuing toward a working
build. Task 0016 publishes the reviewed increment and its hosted evidence to
origin/research/native-feasibility. Continue shared engineering implementation
incrementally; no frontend/default serializer, x/main, upstream write, forced
history or silent native-tool substitution is selected. The encouraging earlier
CrossOver/native Windows payload agreement remains scoped evidence.

D026 — Accepted Mac continuation, 2026-10-16: maintainer authorizes exact-range
Windows bundle import/publication and the handoff's bounded shared data increment.
Reviewed ac51fc77 is remotely verified; both hosted native x64 jobs pass.
First shared mapping libraries now pass all four targets within scope. Task
0015 retains metadata/scaling in CaeMesh and the internal FRD utility in CaeResults;
existing 30 data checks match Windows observations on native Mac/Linux ARM64.
New increment stays uncommitted and needs native Windows/new-commit x64 follow-up.
This does not choose serialization/UI or close full persistence/history/CAD/VTK/
native-source/compiler-policy gates. No further implementation push is authorized.

D025 — Accepted Windows closeout/publication instruction, 2026-10-16:
maintainer explicitly authorizes committing/pushing reviewed Windows/reference/
shared-core work to origin/research/native-feasibility and preparing immediate
MacBook continuation. Task 0014 includes closing evidence and transfer fallback.
No force push, upstream write, x/main integration or frontend/serializer choice.
Windows-only checks needed for this increment are complete; Mac/Linux execution
of the new libraries is next. Remote publication and hosted CI must be verified,
not inferred from local commits or configuration.

D024 — Bounded implementation authorized, 2026-10-16: maintainer requested
finishing supplied-model testing and proceeding to build. Task 0013 starts
partial source-linked shared libraries and a callable mapping host on the
planned branch. Mechanical CaeException separation removes the proven Windows
presentation dependency while retaining existing code/type/assembly identity.
The tested PMX comparison supports proceeding with this limited slice; it does
not establish a portable serializer or complete platform acceptance. Frontend,
full Controller extraction, native integration, x/main and publication stay
outside the current implementation. Preserve remaining release gates.

| ID | Status | Decision / rationale / revisit condition |
|---|---|---|
| D001 | Phase 0 completed; scoped authorization advanced | Phase 0 stayed documentation/repository maintenance only. Maintainer authorized task 0002 on 2026-10-13; broader implementation still requires review |
| D002 | Accepted by task scope; locally established | Keep `master` as clean ff-only upstream mirror, `x/main` separate, Phase 0 on feature/project-initialization; no push/merge without approval |
| D003 | Provisional observation | Analyze master at de8f73032a72746e3d6d9afd53d9fbd289eb310a; stable 3.0 is not yet available. Switch baseline using the audit's release-correspondence and regression gate |
| D004 | Proposed, maintainer approval required | Strategy C transition with Strategy A discipline: retained Windows frontend, shared source/behavior, narrow platform services; avoid independent FEM/controller fork |
| D005 | Proposed, proof required | Preserve VTK filters/ID mapping/selection; select an open-source binding/host after native interactive experiment and license review |
| D006 | Deferred | GUI framework: compare a C# frontend/VTK route with PyQt6 + Python VTK + shared C# backend as full production candidates; decide only after VTK/DPI/input/data-exchange/required-platform proofs |
| D007 | Experiment target accepted; production target deferred | Task 0002 uses net10.0 for a bounded seven-file probe. Production core/build boundaries require broader dependency and file-format evidence |
| D008 | Deferred, critical | Legacy compatible PMX/PMH/settings/material reader/writer and clone strategy; preserve serialized identities initially. No unsupported BinaryFormatter dependency silently introduced |
| D009 | Required before parity implementation/release | Recover matching custom native sources/patches and exact solver/CPython/runtime pins; don't substitute stock binaries and claim equivalence |
| D010 | Proposed | Per-field fixture-based tolerances, exact semantic comparisons, native target runners and Windows oracle; acceptance thresholds need measured repeatability and review |
| D011 | Maintainer Git workflow accepted; other actions deferred | Maintainer normally handles commits/pushes. The 2026-10-14 continuation explicitly authorizes agent commits/origin pushes for task 0002 closing evidence and the next bounded probe/investigation; default maintainer workflow resumes afterward. x/main integration, protected-branch policy, scheduled Hermes work and publishing remain separate approval actions |
| D012 | Accepted, explicit maintainer instruction | Use PrePoMax-X and X/x project naming throughout; the local integration branch is named x/main. Apply this convention to future project documentation, tooling and branches |
| D013 | Bounded task complete, verified 2026-10-14 | Task 0002 on feature/core-feasibility: source-linked STL/vector/node probe, source hash/closure manifest and replay. Mac ARM64, Podman Linux ARM64 and GitLab native Linux x64 pass both source pins, with matching portable observations. Pipeline #2947482796 at 822bae25; see native x64 report. No GUI choice, whole-core portability claim or feature integration authorization |
| D014 | Authorized and performed locally | Reviewed Phase 0 records fast-forwarded into x/main at c840aceb; implementation branch created from it. Maintainer later pushed feature commit 92a491cd; feature implementation is not integrated into x/main |
| D015 | Updated authorization 2026-10-14, explicit maintainer instruction | Retain local Podman testing and prepare complementary GitLab native Linux x64 CI (supersedes the earlier local-only instruction). Retain image/runtime/source provenance and compare structured results. Translated amd64 on an ARM VM is supplemental evidence, not native Linux x64 acceptance. CI configuration/local rehearsal is not a hosted pass |

| D016 | Bounded proof complete 2026-10-14 | Task 0003 on feature/core-data-feasibility: dependency/compiler boundaries, unchanged six-file Matrix/metadata/scaling/FRD-stream probe and PMX source-identity/Windows capture preparation. Mac ARM64 and native Linux x64 pass 30 checks plus two CLI contracts with matching observations; actual Windows capture/PMX compatibility remain pending. No full reader, production serializer or x/main integration commitment |

Review requested at handoff: approve/adjust D004 and the bounded feasibility tasks 1.1/1.2/2.1 plus source recovery 5.1. D005–D008 remain gates rather than immediate commitments. The maintainer handles commits and pushes; agents must not ask to push as a prerequisite for local verification.

D017 — Bounded pre-Windows investigation authorized and audit completed,
2026-10-14: maintainer authorized progressing through the proposed steps,
starting with native source/build feasibility and stopping at completed task
boundaries before usage runs out. Task 0004 records native header/interop checks
and matching-source gaps; native-source recovery/full builds remain open.
No production dependencies, frontend/interop decision, F001 implementation,
x/main integration or commit/push permission follows from this continuation.

D018 — Bounded proofs complete 2026-10-14: task 0005's native structured kernel
and unchanged managed count/grid slice pass on Mac ARM64; task 0006's isolated
Python VTK 9.5.2 synthetic rendering/picking passes 14 checks and exposes clipping
ID loss; task 0007 defines four checked shell-junction fixtures. These establish
specific contracts, not whole-core/native-tool/UI parity. Full C# mapping reaches
the ExceptionTools/MessageBoxes boundary. GUI/binding and F001 implementation
choices remain deferred; Windows/native source/platform gates stay open.

D019 — Research authorization and legacy evidence, 2026-10-15: maintainer
supplied a PMX and accepts investigating an adjusted cross-platform schema with
eventual upstream contribution in mind. Task 0008 decodes actual 2.5.1-dev
records without application reconstruction; production schema remains undecided.
Task 0009's isolated CrossOver Windows 2.6.0 read/save/reopen is human-confirmed,
with guarded byte comparisons and explicit NRBF changes. Native platform/full
semantics remain open. No commits/pushes, messages or PR publication authorized.

D020 — Bounded Linux PMX repetition complete, 2026-10-15: task 0010 passes
24 synthetic tests and both private record inventories on native-architecture
Linux ARM64 in Podman. Portable observations match Mac exactly; one additional
runtime support assembly is guarded separately. No semantic persistence, history,
Windows/Linux x64 or production-format conclusion follows. Preparation exit
gates define next research, with semantic snapshots/history as the next priority.

D021 — Accepted maintainer target correction and next-session handoff,
2026-10-15: required targets are Windows x64, Linux x64, Linux ARM64 and Apple
M-series macOS ARM64. Maintainer explicitly clarified “x86” as 64-bit Intel/AMD.
Intel Macs and 32-bit x86 are excluded; Linux ARM64 is required. This supersedes
the initial target matrix and lower-priority ARM Linux statements in historical
reports. Windows is expected next session; task 0011/handoff are prepared with
capture pending. Uncommitted research must be carried to that checkout; no new
commit/push/integration or architectural-choice authorization.

D022 — Accepted local completion/publication instruction, 2026-10-15: maintainer
explicitly authorizes completing feasible local preparation then committing and
pushing reviewed research to origin. Task 0012 includes hosted evidence follow-up
and ends this exception; later commits/pushes need a new instruction. No upstream
write, force push, x/main integration, frontend/default-format choice or broad
production change. Selected PMX scalar comparisons expose job settings drift;
Linux ARM64 mapping is contraction-sensitive; VTK provenance/lifecycle and the
bundled 2.22 analytical solver reference pass within bounded scopes. None closes
native Windows, full semantics/history, native-source or production-policy gates.

D023 — Verified research publication/native x64 evidence, 2026-10-15:
24c790ac published to origin/research/native-feasibility; push pipeline
#2951491552/job #17205619186 passes on AMD EPYC 9B45 with compiler defaults.
Six downloaded artifacts independently checked. Task 0012 is complete within
its bounded investigation/publication scope; closing evidence publication ends
the scoped agent commit/push exception. Task 0011 remains the next native Windows
checkpoint; no production/integration/format/GUI decision follows.

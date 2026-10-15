# Decision register

Use accepted/proposed/deferred labels; a proposal in a spec is not an architectural commitment.

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

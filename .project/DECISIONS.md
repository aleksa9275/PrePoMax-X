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
| D011 | Deferred | Public fork pushes, x/main integration, protected-branch policy, scheduled Hermes work and publishing remain explicit approval actions |
| D012 | Accepted, explicit maintainer instruction | Use PrePoMax-X and X/x project naming throughout; the local integration branch is named x/main. Apply this convention to future project documentation, tooling and branches |
| D013 | Authorized 2026-10-13; Linux gate pending | Task 0002 implemented on feature/core-feasibility: source-linked STL/vector/node command-line probe, source hash/closure manifest and replay. Mac ARM64 verified; Linux job prepared, not run. No GUI choice or whole-core portability claim |
| D014 | Authorized and performed locally | Reviewed Phase 0 records fast-forwarded into x/main at c840aceb; implementation branch created from it. Feature implementation is not yet integrated or published |

Review requested at handoff: approve/adjust D004 and the bounded feasibility tasks 1.1/1.2/2.1 plus source recovery 5.1. D005–D008 remain gates rather than immediate commitments. Public push approval must specify feature commit and destination; local commits do not authorize it.

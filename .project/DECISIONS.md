# Decision register

Use accepted/proposed/deferred labels; a proposal in a spec is not an architectural commitment.

| ID | Status | Decision / rationale / revisit condition |
|---|---|---|
| D001 | Accepted by task scope | Phase 0 is documentation/repository maintenance only; stop before application implementation |
| D002 | Accepted by task scope; locally established | Keep `master` as clean ff-only upstream mirror, `cp/main` separate, Phase 0 on feature/project-initialization; no push/merge without approval |
| D003 | Provisional observation | Analyze master at de8f73032a72746e3d6d9afd53d9fbd289eb310a; stable 3.0 is not yet available. Switch baseline using the audit's release-correspondence and regression gate |
| D004 | Proposed, maintainer approval required | Strategy C transition with Strategy A discipline: retained Windows frontend, shared source/behavior, narrow platform services; avoid independent FEM/controller fork |
| D005 | Proposed, proof required | Preserve VTK filters/ID mapping/selection; select an open-source binding/host after native interactive experiment and license review |
| D006 | Deferred | GUI framework: compare Avalonia/native host with viable alternatives; decide only after VTK/DPI/input/required-platform proofs |
| D007 | Deferred | Modern .NET target/shared build boundaries: .NET 10 is installed and a candidate; decide using managed/file-format feasibility and supported dependency closure |
| D008 | Deferred, critical | Legacy compatible PMX/PMH/settings/material reader/writer and clone strategy; preserve serialized identities initially. No unsupported BinaryFormatter dependency silently introduced |
| D009 | Required before parity implementation/release | Recover matching custom native sources/patches and exact solver/CPython/runtime pins; don't substitute stock binaries and claim equivalence |
| D010 | Proposed | Per-field fixture-based tolerances, exact semantic comparisons, native target runners and Windows oracle; acceptance thresholds need measured repeatability and review |
| D011 | Deferred | Public fork pushes, cp/main integration, protected-branch policy, scheduled Hermes work and publishing remain explicit approval actions |

Review requested at handoff: approve/adjust D004 and the bounded feasibility tasks 1.1/1.2/2.1 plus source recovery 5.1. D005–D008 remain gates rather than immediate commitments. Public push approval must specify feature commit and destination; local commits do not authorize it.

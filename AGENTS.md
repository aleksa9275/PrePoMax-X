# PrePoMax-X — contributor and agent instructions

PrePoMax-X ports PrePoMax 3.0.2 to native Windows x64, macOS ARM64 (Apple
Silicon), Linux x64 and Linux ARM64. Start every session with
[`.project/STATUS.md`](.project/STATUS.md) (current phase, next step) and
[`.project/DECISIONS.md`](.project/DECISIONS.md) D057–D070. History before
8 November 2026 lives in `.project/history/`; it is reference, not instructions.

## Goal and strategy

- **Target (D063, D068):** upstream `master` pinned per sync (now `6703b1cb`:
  version 3.0.2, not yet released); the 3.0.1 release stays the Windows
  behavioural reference until 3.0.2 is released. The viewport is the original
  `vtkControl` on `vtkNative`. Files of older versions are read by upstream's
  legacy reader with every type bound by our allowlist.
- **Final scope (D060):** identical PrePoMax functionality — every mesh
  type, mesher, calculation, model feature, result tool, PMX round-trip and
  automation surface — on all four targets with installers. The unavailable
  Intel/PARDISO solver is the only exception.
- **Strategy (D062):** maximum reuse of the original code and practices. Build
  the *whole* original assemblies cross-platform instead of porting slices or
  reimplementing features. Phase A: domain libraries (CaeGlobals, CaeMesh,
  CaeModel, CaeResults, CaeJob) for .NET 10. Phase B: original Controller and
  Commands headless, original PMX serialization. Phase C: cross-platform UI
  reusing the original forms/property classes. Progress is tracked in
  [`.project/PARITY_INVENTORY.md`](.project/PARITY_INVENTORY.md).
- **Sequencing (D061):** parity first. Record numerical/original bugs and
  compiler warnings in `.project/reports/deferred-correctness-improvements.md`
  and `.project/bugs/`; fix them together after parity. Keep original
  algorithms and tolerances; never turn a failed check into a pass.

## Code rules

- Original folders keep their paths, namespaces, type and assembly names. Edits
  to original files must stay compilable by the original net48 projects
  (C# 7.3, no new package references there) and be minimal; put platform code
  behind small interfaces or in `X/`.
- Never enable unrestricted deserialization; original PMX reading uses an
  explicit type allowlist (X/Persistence AllowlistBinder over PrePoMax.LegacyImport). Never change mesher/solver versions silently.
- Never copy partial builds over an installed original application.

## Git and publication

- GitHub (D064): `origin` = github.com/aleksa9275/PrePoMax-X (fork of
  github.com/PrePoMax/PrePoMax), `upstream` = github.com/PrePoMax/PrePoMax,
  `gitlab` = the archived GitLab fork (read-only; old history). `master` mirrors
  upstream (fast-forward only). Work goes on `research/native-feasibility`;
  `x/main`, `feature/*`, `integration/*` per `.project/UPSTREAM_SYNC.md`.
- Committing and normal pushes to `origin/research/native-feasibility` are
  authorized; verify the remote SHA. Until CI exists (M3) use `[skip ci]`.
  No force push, no writes to master/x/main/upstream/release branches, no
  pull requests or issues upstream without explicit instruction.
- Do not touch the untracked Finder `.DS_Store` files.

## Verification

- Development: focused checks for the changed area (`python3 X/Checks/check.py`).
  Milestones: representative end-to-end workflows and comparison with the
  original Windows app (CrossOver reference = evidence, not Windows acceptance).
  Full platform/package sweeps only at release candidates. See
  `.project/TEST_STRATEGY.md`.
- Linux x64 is verified later via Podman on Windows (D059). Linux ARM64 via the
  local Podman machine.
- Report outcomes as they are: failed, skipped and pending are not passes.

## Documentation

- One short report per phase/milestone in `.project/reports/`; update
  STATUS.md (replace, don't append) and the parity inventory. Add a decision to
  DECISIONS.md only for real maintainer decisions. Keep this file short.
- Keep at most one local preview candidate; prune superseded generated payloads.

# Task 0041 — Shared target builds and native Linux CPU workflow

Maintainer resumes the accepted next sequence after task 0040. Implement the
small shared target/build entry with all four RIDs, common managed hosts and
target metadata; preserve the Mac package command as a wrapper. Move native Mac
compiler/runtime inspection behind its adapter and add a Linux adapter using the
same pinned CalculiX/SPOOLES/ARPACK source/recipe. Execute the common native cube
workflow on the Mac and native Linux x64 CI. Target availability must distinguish
planning, cross-publishing, native execution and desktop/package acceptance.

No production frontend/format/default backend/precision choice, new solver
version, Windows native solver acceptance or full distro installer claim. Keep
both correctness failures/tetra gate and source/release requirements. Publish
useful verified checkpoints normally to origin/research/native-feasibility under
existing D051 authorization; document actual hosted outcomes and pending targets.

Local outcome: all four target definitions and shared managed/native/package
entry implemented. Mac self-contained hosts/native cube pass, final Mac package
passes ten native frame/field/ID checks and its ad-hoc signature. Windows x64 and
Linux ARM64 cross-publication succeeds with native execution pending. Seven
boundary regressions pass; pristine native source verification passes. Linux x64
CI now includes the native CPU build/workflow; actual publication/hosted state
is recorded in [report](../reports/shared-target-builds.md).

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

Hosted outcome: implementation a893005c is remote-verified; exact-commit pipeline
3019959774 passes five automatic jobs (compatibility manual). Actual downloaded
65-entry execution archive verifies clean source, native ELF build, twelve cube
checks/rejection control, shared source/recipe/catalog identity and Mac comparison
of four FRD fields/96 histories. CI split 0411ae23 moves the slower native build
behind affected inputs; pipeline 3019992604 passes all six automatic Linux x64
jobs. Final coverage is recorded
in the report/publication JSON. No full historical matrix is rerun for this build
boundary change; no other native desktop/distro or release acceptance follows.

Task 0041 is complete within its bounded build/compute scope. Final CI split
artifacts verify clean 0411ae23 and the same native executable/decoded FRD/DAT
values as the initial run; compatibility remains manual. Next increments are
recorded in the report. Both correctness failures/tetra and release gates remain.

# Task 0006 — Native VTK synthetic rendering/selection smoke test

Status: initial bounded smoke experiment complete on 2026-10-14. Authorized by the maintainer's 2026-10-14 instruction to
complete bounded pre-Windows steps while usage permits. Tasks 0004/0005 are
complete within their scopes. Branch: research/native-feasibility.

## Scope and acceptance

Use an isolated Python VTK candidate runtime with a pinned Mac ARM64 wheel to
test synthetic mesh rendering and exact FEM global-ID selection. Preserve
runtime/wheel/binary identities, commands, checked images and bounded failure
diagnostics. Inspect existing vtkControl ID/picker/filter contracts first.
Test direct renderer picks, ID-preserving extraction and deformation/clipping
on independently specified geometry, where the host supports it.

This is a preliminary native binding/rendering experiment, not completion of
roadmap 2.1: no frontend or production dependency is selected. Do not port or
rewrite vtkControl, replace ActiViz, install GUI frameworks, invoke arbitrary
PMX deserialization, or claim genuine pointer/DPI interaction, Windows visual
parity, full rendering equivalence or other-platform acceptance. If Cocoa or
sandbox constraints prevent rendering, retain a completed capability report
with the exact measured failure and whatever nonrendering checks passed.
No commits, pushes or x/main integration.

## Outcome

Fourteen checks pass on native Mac ARM64/Apple M5 Pro through
vtkCocoaRenderWindow. Synthetic render/deformation/removal images inspected;
exact FEM IDs returned by programmatic cell/point/rectangle picks and extraction.
vtkClipDataSet drops global-ID arrays: explicit provenance handling remains
required. [Report](../reports/vtk-native-smoke.md) records pinned wheel, native
module, runtime/source context and limitations. Genuine pointer/DPI/UI and
Windows/platform parity remain pending; roadmap 2.1 and frontend decision stay open.

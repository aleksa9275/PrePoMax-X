# Task 0017 — Callable finite-element geometry and integration kernel

Publication update: maintainer explicitly requests commit/push in task 0018.
Earlier uncommitted-only statements below describe the previous local checkpoint.

2026-10-16, Europe/Belgrade. Maintainer requests continuing shared-core work
toward a working build after task 0015 publication. Implement a bounded next
slice: original FeElement hierarchy (0D/1D/2D/3D, linear/parabolic families),
GeometryTools and required comparer in their original shared assemblies.
Remove only a measured unused Windows import if it blocks compilation;
prove all remaining source bytes unchanged. Keep algorithms, type/field/assembly
identities and original net48 project ownership. No full FeMesh/Controller,
INP/FRD decoder, frontend, serializer or native-tool substitution in this task.

Deliver a callable command-line mesh-measurement host using original element
centroid/measure/integration methods, with finite-input/ID/connectivity checks
at the host boundary. Independently test canonical linear/parabolic cells,
constant/linear field integrals, thickness/axisymmetric scaling, connectivity,
type identity and failures. Preserve unsupported upstream operations explicitly.
Retain the 55 prior engineering checks and controls. Run native Mac ARM64 and
cached Podman Linux ARM64; prepare native Windows/hosted x64 follow-up.
Publish a runnable local development build and reproducible command/evidence.

Status: bounded local implementation and development package complete, with
two open correctness failures explicitly retained. Mac/Linux ARM64 each pass
95 accepted element/host checks plus the prior 55 checks, 28 CLI controls and
four data-verifier controls. Two strict checks fail identically: quadratic
tetrahedron affine integration and quadratic-pyramid classification. The host
rejects quadratic tetrahedra; no numerical tolerance/algorithm was changed.
Source quadrature moments independently expose the tetrahedron bias. Native
Windows/new-commit hosted x64 and those correctness issues remain pending.

The local framework-dependent ZIP includes examples, source and license.
Published examples pass Mac/Linux ARM64; extracted sources rebuild independently.
Evidence and commands: [element kernel report](../reports/shared-element-kernel.md).
All task 0017 implementation remains uncommitted. This is an engineering kernel increment,
not a complete interactive PrePoMax-X application. CAD/interactive VTK/full
persistence/history/native-source and compiler-policy release gates remain.
No new implementation commit/push is assumed from the task 0015 publication.

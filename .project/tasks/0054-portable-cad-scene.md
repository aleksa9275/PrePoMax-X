# Task 0054 — Portable CAD scene

Carry CAD edge IDs through the original VIS node and edge merge. Keep one
display segment when multiple source edges share it and retain all their IDs.
Expose the shared triangles, segments and measurements to the desktop through
the existing self-contained C# VIS host. Keep the task 0053 inspection
contract byte-compatible and compare the scene with the original L-bracket
reference.

[Verification](../reports/desktop-vis-geometry.md).

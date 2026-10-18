# Task 0020 — Portable mesh input and deck export workflow

2026-10-18, Europe/Belgrade. Maintainer asks to proceed with the implementation
while preparing a Windows machine for GitLab. This authorizes local work on the
proposed mesh/deck/solve/results direction; keep all task 0019 changes and new
implementation uncommitted. No push, x/main integration, production frontend/
serializer selection, numerical/tolerance change or native-tool substitution.

First runnable increment: expose the original INP mesh parser without requiring
the whole FeMesh/Controller/CAD graph. Mechanically separate the existing node,
element/connectivity, dataset and set-label parsing into a partial InpFileReader
in its original CaeModel assembly. Preserve all legacy entry points, include
the partial in the original net48 project, and guard extraction against pinned
upstream bytes. A narrow raw-mesh exchange object is not a second model or a
document format. Preserve original FeNode/FeElement/InpElementSet ownership.

Reuse the original CalculiX element keyword writer for mesh export. Separate
the framework-only StandardValueAttribute from its UI editor to retain enum
metadata/type identity. Add a usable inspect/export-mesh CLI, bounded input,
finite/ID/connectivity validation, explicit formulation warnings and explicitly
requested pyramid conversion. Retain mesh-only export omissions in output.
Do not claim full material/BC/step/deck/history/PMX or solver/results workflow.

Verify the original 150 accepted engineering checks and two retained correctness
failures/host gate, analytical input geometry, actual mesh roundtrips, multiline
high-order connectivity, named/generated sets, IDs/formulations, malformed input
and output collision controls. Test native Mac/Linux ARM64 and prepare the same
commands/fixtures for native Windows x64. Preserve source/type identities and
the upstream replay path. Build/package a runnable increment with matching source.

Status: completed within the first mesh-input/export increment. Current/RC2/
post-RC2 each pass Mac/Linux ARM64: 150 previous accepted checks plus 68 mesh
workflow checks, 39 CLI/four data controls and ten source/replay tests. Exact
portable outcomes/tooling hashes match across all six reports. Both correctness
failures/host gate remain. Native Windows/hosted x64 and full original net48
build/oracle remain pending. A runnable three-tool/source development ZIP is
verified on Mac/Linux ARM64; six retained Windows synthetic mesh inputs/exports
also yield expected cube geometry on Mac. All changes remain uncommitted.
The full FeMesh/model/FRD/solver/interactive host and persistence/native-source
release gates remain subsequent work, not passing. [Evidence and Windows
continuation](../reports/portable-mesh-deck-workflow.md).

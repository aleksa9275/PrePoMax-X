# Portable VIS probe

Build the source-linked research host with the repository .NET SDK.
The probe reads a VIS version 2 file and emits the original geometry
metadata, merged nodes, triangles and source face and edge IDs as JSON.

    dotnet build X/Feasibility/Cad/Inspect/Inspect.csproj -c Release --artifacts-path /tmp/prepomaxx-vis
    dotnet /tmp/prepomaxx-vis/bin/Inspect/release/PrePoMaxX.InspectVis.dll X/Feasibility/Cad/fixtures/l-bracket.vis
    python3 X/Feasibility/Cad/verify-vis.py --inspector /tmp/prepomaxx-vis/bin/Inspect/release/PrePoMaxX.InspectVis.dll --output /tmp/vis-check.json

The tracked fixture preserves the exact bytes from the original 3.0.0
NetGenMesher capture. The comparison uses the original app's selection
mapping to relate its measurements to source IDs. Desktop part creation
and selection generation still live in the legacy reader.
[Task 0052 reference](../../../.project/reports/l-bracket-cad-reference.md).

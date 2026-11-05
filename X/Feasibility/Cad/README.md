# Portable VIS probe

Build the source-linked research host with the repository .NET SDK.
The probe reads a VIS version 2 file and emits the original geometry
metadata, merged nodes, triangles and source face and edge IDs as JSON.

    dotnet build X/Feasibility/Cad/Inspect/Inspect.csproj -c Release --artifacts-path /tmp/prepomaxx-vis
    dotnet /tmp/prepomaxx-vis/bin/Inspect/release/PrePoMaxX.InspectVis.dll X/Feasibility/Cad/fixtures/l-bracket.vis
    python3 X/Feasibility/Cad/verify-vis.py --inspector /tmp/prepomaxx-vis/bin/Inspect/release/PrePoMaxX.InspectVis.dll --output /tmp/vis-check.json

The tracked fixture preserves the exact bytes from the original 3.0.0
NetGenMesher capture. The comparison uses the original app's selection
mapping to relate its measurements to source IDs. The `scene` subcommand
emits a desktop DTO with triangles, CAD edge segments and the source IDs
and measurements needed for read-only inspection. The 1 MiB VIS input limit
applies to both modes. Windows part creation and selection numbering still
live in the legacy reader.
[Task 0052 reference](../../../.project/reports/l-bracket-cad-reference.md).

## Replay STEP conversion

Supply the original 3.0.0 `Meshers/Netgen` directory and an isolated
CrossOver Windows 10 64-bit bottle on macOS. The replay validates the 38
executable and DLL hashes, runs both conversion commands twice in fresh
directories and compares the BREP, VIS and portable scene against the
recorded original.

    python3 X/Feasibility/Cad/replay-import.py --reference-runtime /path/to/Meshers/Netgen \
      --bottle cad-reference --inspector /tmp/prepomaxx-vis/bin/Inspect/release/PrePoMaxX.InspectVis.dll \
      --output "/tmp/cad replay"

For a direct candidate comparison, replace the reference options with
`--mesher /absolute/path/to/NetGenMesher`. The candidate must produce
repeatable bytes and an identical decoded scene. The report also says
whether its raw BREP and VIS match the original. A fixture match leaves
source correspondence and native platform acceptance as separate checks.

The shared `convert_cad_parts` boundary accepts up to 32 emitted BREP
parts, with at most 32 MiB of combined BREP and 16 MiB of combined VIS.
Each VIS is limited to 1 MiB. The original single-part conversion entry
continues to require one output.

The two-part fixture was captured twice through the pinned original tool
and imported twice in the original Windows application. Verify its
topology, canonical measurements and part-scoped renderer IDs with

    python3 X/Feasibility/Cad/verify-parts.py --inspector /tmp/prepomaxx-vis/bin/Inspect/release/PrePoMaxX.InspectVis.dll --output /tmp/cad-parts.json

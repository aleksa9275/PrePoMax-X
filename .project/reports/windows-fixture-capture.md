# Windows PMX/history reference capture

Task 0003 preparation, 2026-10-14. Maintainer confirms a Windows machine can run
PrePoMax. **Live capture has not run.** Use a disposable working directory and
repository-owned example models. No personal models or settings/token files are
needed. This is fixture preparation, not a production serializer decision.

## Pin the reference

Record application version/build provenance and SHA-256 of PrePoMax.exe and
the CaeGlobals/CaeMesh/CaeModel/CaeResults DLLs. Record exact source commit when
building from source. Target audit baseline:
`de8f73032a72746e3d6d9afd53d9fbd289eb310a`. An assembly version of 3.0.0 does
not establish the source commit or a stable release. If only a released binary
is available, record it as a distinct reference version; do not invent an exact
correspondence. Hash the unchanged cube.inp input and any native/solver binaries
actually used. The initial mesh-only fixture needs no solver or CAD mesher.

Start with a fresh original Windows application session. Its existing command
gateway is the reference; do not replace it with a new capture service. The
script at `X/Feasibility/Data/Capture_Windows_Reference.py` uses source-verified
`pmx.new_model`, `import_file`, `save` and `export_to_calculix` from
`APIs/Python/PrePoMaxAPI.cs`. It refuses to overwrite its two outputs. Copy
`APIs/Python/Test_Scripts/Models/cube.inp` into a new capture directory, then run
the script through the original application's Python script facility. For a
matching source build, the repository's documented launch pattern is:

```powershell
# Substitute verified application/script paths; work directory must already exist.
& 'C:\PrePoMax-reference\PrePoMax.com' --script 'C:\pre-po-max-x\X\Feasibility\Data\Capture_Windows_Reference.py' -g No -x Yes -w 'C:\PrePoMax-X-capture\mesh-only'
```

`-g No` still constructs the Windows WinForms/VTK host; this is a Windows
reference run, not a platform-neutral headless backend. The script is not
verified live yet. If the installed release lacks these APIs, use its normal
GUI to create the same fixture and record that release/route instead.

## Initial corpus

| Case | Capture and verify in the original Windows host |
|---|---|
| Mesh only | cube-mesh.pmx and cube-export.inp. Reopen PMX and confirm 8 node IDs 1–8, one C3D8 element ID 1 with connectivity 1–8, cube bounds [0,0,0]–[1,1,1], MM_TON_S_C units |
| History | Preserve the generated command history after capture, before closing/starting a new session. `CommandsCollection.GetHistoryFileNameBin` names the application's history file; its constructor combines Application.StartupPath with Globals.HistoryFileName. Locate that exact path using the pinned source/application, copy to corpus, record commands and ensure regeneration can resolve the captured cube.inp |
| Model definitions | Add a simple independently specified material, solid section, named node/element sets, static step, BC and load using original UI or existing Test_Analysis.py setup. Record exact values/units and names; save/reopen and export the solver deck without changing native-tool versions |
| Results included/excluded | Once solver identity is pinned, use the existing Test_Analysis.py route to solve the cube; retain FRD/DAT and PMX with SaveResultsInPmx both on/off. Record steps/increments/fields/components and original Windows readback. This is pending; no solver equivalence yet |
| Metadata/history variants | Add named selections and undo/redo/regeneration; later capture multi-results and CAD metadata only with corresponding tool/source pins. These are additional corpus gates, not covered by the first mesh-only capture |

Source framing: Controller.SaveToPmx writes a 32-byte program/version header,
length-prefixed Deflate block containing the serialized root object graph plus
FeModel custom binary data, then separately framed results. Older-version and
uncompressed fallback readers remain part of compatibility. PMH is a dumped
List<Command>. Copying just the metadata block or a flattened mesh cannot prove
PMX/history compatibility.

Complete [the manifest template](core-data/windows-fixture-manifest.template.json)
with real file names/hashes and observed readback. On Windows, compute hashes:

```powershell
Get-FileHash -Algorithm SHA256 'C:\PrePoMax-X-capture\mesh-only\cube-mesh.pmx'
Get-FileHash -Algorithm SHA256 'C:\PrePoMax-reference\PrePoMax.exe'
```

Retain the input deck, capture outputs, console diagnostics and manifest. Do
not include settings.bin, authentication settings or user work directories.
Actual serialized type/assembly graphs and PMX round-trip remain pending until
these fixtures are available and inspected. No BinaryFormatter compatibility
package or unsafe-deserialization switch is enabled by task 0003.

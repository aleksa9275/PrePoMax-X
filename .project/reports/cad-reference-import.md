# Checked STEP and BREP reference import

Task 0057 replays the original PrePoMax 3.0.0 CAD command sequence.
It validates all 38 executable and DLL hashes from the release
receipt. The tool splits a staged STEP or BREP in a fresh workspace,
then runs `BREP_VISUALIZATION` with the original `0.01 1 0.26`
arguments. The boundary requires one nonempty BREP and a new VIS,
checks the staged input after execution, and retains both stage logs
in replay mode. A direct executable can be supplied to the replay for
comparison with the original. That route checks repeatability and exact
decoded geometry and reports raw file equality separately.
[Replay instructions](../../X/Feasibility/Cad/README.md).

Two runs using the official runtime through CrossOver 26.2.0 on Apple
Silicon reproduced the task 0052 BREP and VIS files byte for byte and
decoded to the same scene. A malformed STEP exited with status 1, and
the tracked `sweep_two_apart.brep` was refused after the tool emitted two
parts. Both original inputs remained intact. The portable process
tests also exercised missing, ambiguous and stale output, staged-input
mutation, nonzero exit, size limits and mismatched runtime files.

Task 0058 adds `--cad-reference RUNTIME BOTTLE` to the native macOS
preview. The option enables STEP and BREP in the open dialog and the
positional file argument. The model tree identifies the compatibility
conversion, and the existing shared VIS reader supplies the read-only
geometry and measurements. Opening an invalid file leaves the previous
document in place. The package includes the hash receipt. CrossOver
and the Windows CAD runtime are supplied separately.
[Desktop usage](../../X/Desktop/README.md).

The ad-hoc-signed ARM64 package opened the original STEP through the
frame bridge and its BREP through the opt-in Cocoa viewport with a
system-only PATH. Both produced the original VIS hash, 38 nodes, 72
triangles and 45 edge segments, and selected the same six source faces.
The bundled native INP solve also passed. The source desktop suite
passed 20 tests. Nine build boundary tests passed and the four portable
conversion tests also passed on Linux ARM64.
[Verification receipt](cad-reference-import-verification.json).

This preview accepts one emitted BREP part and an input up to 16 MiB.
The conversion stages run synchronously with a 60-second limit per
stage. Native STEP/BREP execution still requires the corresponding C++
source and build. CAD repair, meshing, both correctness failures, the
tetrahedron gate, general 3.0.0 parity and release acceptance remain open.

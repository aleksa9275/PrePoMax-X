# Original 3.0.0 L-bracket CAD reference

The pinned Windows PrePoMax 3.0.0 release imported the tracked
`L_bracket_r.step` under CrossOver 26.2 on Apple Silicon. The checkout's
upstream geometry metadata script passed in the original application. Two
additional fresh imports produced byte-identical captures of the part,
measurements, topology and metadata.
[Measurements and topology](l-bracket-cad-reference/geometry.json) ·
[Fixture and upstream checks](../../APIs/Python/Test_Scripts/Test_Model_Geometry_Metadata.py).

| Observation | Original result |
| --- | --- |
| CAD shape | One solid, approximately 100 × 100 × 10 mm |
| Volume | 36,214.6018366 mm³ |
| Surface area | 11,200 mm² |
| Faces | Eight planes and one concave cylinder with a 10 mm radius |
| Edges and vertices | 19 lines, two circles and 14 vertices |
| Display tessellation | 38 nodes and 72 elements |

The original application ran the bundled `NetGenMesher.exe` with
`STEP_ASSEMBLY_SPLIT_TO_COMPOUNDS`, then `BREP_VISUALIZATION` with arguments
`0.01 1 0.26`. Two direct runs of those same commands produced byte-identical
BREP and VIS files. The VIS file has format version 2, global coordinates,
and lengths in model units. The application applies part-level ID mapping
when it reads the visualization and metadata.
[Controller import path](../../PrePoMax/Controller.cs) ·
[Original VIS reader](../../CaeModel/FileInOut/Input/VisFileReader/VisFileReader.cs).

The official and checked-in Netgen directories each contain 38 executable
or DLL files. The executable and 36 DLLs match. The official release's
`nglib.dll` is the one differing file. The receipt records both hashes and
the full release runtime inventory. Recovering the matching NetGenMesher
and modified nglib source remains an open requirement for a corresponding
native build. The documented patched Gmsh source remains a separate meshing
requirement. [Verification and hashes](l-bracket-cad-reference/verification.json) ·
[Netgen source boundary](../../ThirdParty/netgen/README.md).

To repeat, extract the archive identified in the receipt to a temporary
directory and create an isolated Windows 10 64-bit CrossOver bottle. Copy
the tracked STEP into the fixture directory. Run the archive's
`PrePoMax.com` with the following arguments using paths visible to the
bottle. First use the upstream geometry test as the script, then use
`capture.py` in a fresh output directory for each capture.

    -f L_bracket_r.step -u MM_TON_S_C --script capture.py -g No -x Yes -w <output>

Replay the two recorded NetGenMesher commands against the same STEP and
compare the generated files to the receipt. The exact BREP, VIS and command
logs are retained locally under `X/Feasibility/Cad/artifacts/task0052`.
[Capture script](l-bracket-cad-reference/capture.py).

Task 0051's generated 415,485,218-byte ARM64 installer was removed after its
hash was checked. The Ubuntu verification and jobs, task 0050 archive used
to recreate the installer, and current Mac preview remain available. Task
0052's temporary CrossOver bottle and extracted release copy were also
removed after the reference outputs and original ZIP verified.

This establishes the original application's STEP import and display
reference. Native Mac CAD execution and volume meshing remain open,
alongside the existing correctness, tetrahedron, compatibility and release
gates. The next bounded implementation can compare the original VIS reader
against these bytes while the corresponding native sources are recovered.

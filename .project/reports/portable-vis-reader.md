# Portable VIS geometry reader

Task 0053 reads the exact L-bracket VIS file produced by the original
PrePoMax 3.0.0 NetGenMesher. The portable `CaeModel` build compiles the same
metadata reader, face and edge parser, and node and edge merge routines used
by the Windows reader. The coordinate parser explicitly uses the VIS decimal
convention. The Windows project still constructs `FeMesh` parts and applies
its original selection numbering and canonical measurements after parsing.
The CAD probe builds its own partial `CaeMesh` using the existing Core
source list and the additional geometry inputs. [Build and run](../../X/Feasibility/Cad/README.md).

The Mac ARM64 and native-architecture Linux ARM64 runs each passed 292
checks and produced identical decoded JSON. The comparison used the original
application capture and its source-to-local ID mapping. It matched 38
merged nodes, 72 triangles, 14 vertex IDs and coordinates, nine faces,
21 edges, CAD measurements and supplemental metadata by exact comparison.
The probe also refused a VIS version 1 file and a file with
metadata but no tessellation. The comparison validates source face
membership and the decoded geometry before Windows part creation.
Local selection ID generation remains in the Windows part creation stage.
[Original 3.0.0 capture](l-bracket-cad-reference.md) ·
[Verification receipt](portable-vis-reader-verification.json).

Ten existing shared Core replay tests passed. The moved parse and merge
helpers were compared with their originals. The coordinate culture and
equivalent dictionary insertion were the only changes within those helpers.
Windows desktop execution,
native STEP/BREP import, corresponding NetGenMesher and nglib source
recovery, full CAD and volume meshing remain open. Both known correctness
failures, the tetrahedron gate and all release requirements remain open.

Implementation `5507ff75` was pushed and verified on
`origin/research/native-feasibility`. All six automatic jobs passed.
Historical compatibility stayed manual.
The [native Linux x64 research job](https://gitlab.com/aleksa9275/pre-po-max-x/-/jobs/17744290285)
passed all 292 checks with the same decoded hash.
[Exact-commit pipeline #3028209392](https://gitlab.com/aleksa9275/pre-po-max-x/-/pipelines/3028209392).

# Portable CAD scene and desktop VIS inspection

The original VIS reader now carries CAD source edge IDs through the node
and segment merge. Shared segments retain every contributing edge ID. The
existing inspect output has the same decoded hash as task 0053. The
self-contained `PrePoMaxX.InspectVis scene` command projects that data
into a desktop scene with the original triangles, source faces, CAD edge
segments and canonical measurements.

The native preview opens VIS version 2 exports up to 1 MiB through
**Open INP / FRD / VIS**. It draws CAD edges over shaded geometry and maps
triangle picks to source face rows in the model tree. CAD measurements come
from the VIS metadata in the file's declared units. The preview displays
rounded values and keeps the stored values in tooltips. VIS inspection is
read-only. The desktop checks that a refused import preserves an edited INP,
and that switching to FRD or INP restores the corresponding view and controls.
[Original fixture and reference](l-bracket-cad-reference.md).

The L-bracket scene contains 38 nodes, 72 triangles and 45 unique
segments for the original 21 CAD edges. The portable checks compare all
scene nodes, triangles, source face IDs, source edge coverage and measurements.
An alias control assigns one segment to two edge IDs and verifies both
survive. Unsupported-version and missing-tessellation files fail in both
reader modes. macOS ARM64 passed all 346 checks. The source desktop
regression suite passed 15 tests. The Mac source preview picked six visible
faces, including the concave cylinder, through both viewport transports.

Windows part construction and local selection numbering remain in the
Windows reader. The next CAD increment requires a corresponding native
source/build for STEP/BREP import. Native CAD repair and volume meshing,
full 3.0.0 parity, both known correctness failures, the tetrahedron gate
and release acceptance remain open.

# NetgenMesher

The meshing and CAD utility that PrePoMax shells out to for Netgen meshing and for every
OpenCASCADE geometry operation - splitting an imported assembly, building the visualisation mesh,
compounding and converting parts. It ships with PrePoMax as `Meshers\Netgen\NetGenMesher.exe` plus
`nglib.dll`; the deployable copy is vendored in the PrePoMax repository under `ThirdParty\netgen`,
which is also where its licence texts and dll inventory are documented.

## Layout

| Folder | What it is |
|---|---|
| `Netgen v5.3.1 port to OCCT 8.0.1/` | Netgen 5.3.1 ported to OpenCASCADE 8.0.1. `Netgen-master/netgen-5.3.1/nglib/nglib.cpp` holds the PrePoMax specific entry points; `windows/nglib.sln` builds `nglib.dll`. |
| `NetGenMesher 8.0.1/` | `NetGenLibTest/NetGenLibTest.cpp` is the command line front end - it parses the command (`STEP_ASSEMBLY_SPLIT_TO_COMPOUNDS`, `BREP_VISUALIZATION`, `BREP_MESH`, ...) and calls into nglib. `NetGenLibTest.sln` builds `NetGenMesher.exe`. |
| `NetgenMesher/` | Build output. `Release` is the configuration PrePoMax ships. |
| `redist/` | Visual C++ runtime dlls copied next to the output by `copy_runtime_dlls.bat`. |

`BREP_SPLIT` splits a part with a tool built from a plane, from a face continued past its boundary, or from
edges swept along a direction. The tool is described by a small `<property>: <values>` text file whose grammar
follows the `.vis` format - unknown properties are ignored, and a missing property keeps its default - so a new
kind of tool can be added without changing the command line. The caller passes the `Extent` the tool has to
cover, because one tool is applied to every part of a region and a tool sized per part would come out different
for each of them. `Split target: Shell` turns the same tools into a shell split: the faces named by
`Target face ids` are divided and the body they belong to is left whole, so a solid comes back a solid with
more faces instead of being cut in two. It is done by crossing the tool with those faces and imprinting the
curves that come out, since a curve cannot separate a body. `Tool type: TwoPointLine` has no tool shape at
all: it draws the line between `Point 1` and `Point 2` in the parameter space of each target face, clipped
to that face's parameter box, so the line lies on the surface however curved it is and reaches the boundary.
It is what `BREP_SPLIT_A_FACE_USING_TWO_POINTS` should have been - that command projects a straight edge with
`BRepAlgo_NormalProjection` and crashes when the chord between the two points passes through the axis of the
surface. Face and edge ids are read from `Source file` when one is given, which is what lets one part's
geometry split another. The command reports a failure when the tool added no faces, since the modelling kernel
returns a shape whether or not it made the cut. Beside the result it writes `<output>.origins`, one line per
solid of the result in explorer order, holding the number of the input solid that piece came from (counted
the same way, 0 if none holds it). A split only divides solids, so each piece lies inside exactly one input
solid; a point found just inside the piece is classified against the input solids to name it. PrePoMax reads
the file to keep what it knew about a solid - its sub part, its color - on the pieces it became. `BREP_SPLIT_PREVIEW` takes the same arguments with an edges file in place of the output brep: it
splits the same way and writes only the edges the split made, each as `Edge: <n>` followed by n lines of
`x y z` sampled on it, and saves no result. An edge of the result is left out when it is an edge of the input,
or when points sampled inside it lie on the input edges - a piece of an edge the tool crossed is the same
curve cut shorter - so what remains is the outline of the cut. A solid split also writes every edge of
a face it made, a face that lies on no face of the input, since a tool running along edges the shape already had
makes faces whose outline lies on those edges. PrePoMax draws it as the preview of a split. Run the
executable with no arguments for the full grammar.

`BREP_MERGE_SOLIDS <in.brep> <out.brep> <id> <id> ...` makes one solid of the named solids, numbered in
explorer order as `BREP_REMOVE_SOLIDS` numbers them, and writes it in place of the first of them; every other
solid is written as it was. There is no boolean operation: the faces two of the named solids share are left
out and every other face is taken as it is, sorted by the edges they share into the outer shell and one shell
for every void, so a solid that is not named keeps the very faces, edges and vertices it shares with the
result and the compound stays conformal. `ShapeUpgrade_UnifySameDomain` then heals the result in two passes.
The first merges faces lying on one surface, across the edges of the removed faces and across seams only, so
faces the model had before a split stay as they were. The second joins edges, only at the vertices of the
removed faces, which takes out the points a cut left on the edges it crossed. Anything another solid holds is
kept by both passes, and a healed solid that is not valid or has lost any of it is not used. A box cut
through three blind holes and merged back has the faces, edges and vertices it had before the cut. Solids
that do not all share faces cannot become one solid and are refused, as is a result that is not a valid
solid; the command fails when the result has as many faces as before. PrePoMax runs it for Fuse Cells.

`BREP_DEFEATURE_COMPOUND <in.brep> <out.brep> <numOfGroups> {<solid> <numOfFaces> <faceId> ...}` defeatures a
compound of solids as a whole, the faces grouped and numbered inside their solid as `BREP_REMOVE_FACES` takes
them. `BREP_DEFEATURE` takes one solid, and defeaturing the solids of a compound one at a time changes a face two
of them share on one side only, so they no longer meet. Every solid is followed into the result through the
history of the defeaturing and written back in the order it was read, which is the order PrePoMax numbers the
sub parts of the compound in; a solid the defeaturing removed or split is refused. PrePoMax runs it for
Defeature on the sub parts and split cells of a compound.

Both defeaturing commands keep the splits of the faces they do not remove. `BRepAlgoAPI_Defeaturing` simplifies
its result by making every two neighbouring faces on one surface one face, anywhere in the shape, so the two halves
of a periodic face and the pieces of a face a shell split divided came back whole after the removal of something
else - on `blind_holes.brep` split into halves, defeaturing one blind hole removed five faces instead of three. The
edges that separated two input faces which came out as one face are found through the history and cut into the
result again with `BRepAlgoAPI_Splitter`, the way a shell split cuts them, so every split comes back where it was,
whoever made it. An edge that ended on a removed feature no longer reaches across its face and is left out with a
warning, and the result is kept as the defeaturing made it when the cut would leave an edge inside a face or an
invalid shape.

`BREP_FUSE_FACES <in.brep> <out.brep> <numOfGroups> {<solid> <numOfFaces> <faceId> ...}` makes the named
faces one, the ids grouped as `BREP_REMOVE_FACES` takes them. It is the heal `BREP_MERGE_SOLIDS` ends with, run
on faces the caller names: an edge is taken out only when both of its faces are named and bound the same solids,
and a seam only when its face is named, so `ShapeUpgrade_UnifySameDomain` merges faces lying on one surface
across those edges alone and every other edge keeps its identity. The edges are then joined at the vertices of
the edges taken out, which removes the points a split left on the edges it crossed. A face of a compound shared
by two solids is fused only with faces those same two solids share, so the solids still meet. The result must
be valid when the input was and hold the solids and shells it held; the command fails when no face was fused,
which is what faces on different surfaces give. PrePoMax runs it for Fuse Faces.

`BREP_REPAIR <in.brep> <out.brep> <options> <tolerance>` repairs the whole shape. `<options>` adds up 8 sew
faces (`BRepBuilderAPI_Sewing`, only for a shape without solids), 1 fix shape (`ShapeFix_Shape`, the
tolerance its maximum), 4 remove small faces (`ShapeFix_FixSmallFace`), 2 remove small edges
(`ShapeFix_Wireframe`, whose wire gaps are closed only when removing the edges left the shape invalid - on a
valid shape closing them reorients faces far from any small edge), 16 fuse faces (the `BREP_FUSE_FACES` heal on every face) and 32 join edges
(`ShapeUpgrade_UnifySameDomain` on edges), and they run in that order. Each step writes the faces, edges and
vertices it left. A result with another number of solids, or one that is not valid when the input was, is
refused. PrePoMax runs it for Repair.

`BREP_REPAIR_PREVIEW <in.brep> <out.preview> <options> <tolerance> [maxSplitFaces]` repairs as `BREP_REPAIR` does and writes
only what the repair takes away, after `Repair preview format: 1`: every edge of the input as `Edge: <n>`
followed by n lines of `x y z` sampled on it, and every vertex as `Point: x y z`. The input and the result are
compared by their geometry, since the repair steps copy what they touch: an edge is taken away when a point
sampled inside it lies on no edge of the result, which holds for the edge between two fused faces, a small edge
and the edges of a small face, while an edge only joined with its neighbour lies on the joined edge and is left
out. A vertex is taken away when no vertex of the result is at its place, which is what joining edges leaves. A
free edge is written when it lies on an edge of the result that is no longer free, which is what sewing closed.
With `maxSplitFaces` the closed faces of the result are divided as `BREP_SPLIT_CLOSED_FACES` divides them before
the comparison, since the caller divides them after a repair; otherwise fusing the halves of a cylinder would
report its seams as taken away. PrePoMax draws it as the preview of a repair and returns it from
`repair_preview`.

`BREP_REMOVE_FACES <in.brep> <out.brep> <numOfGroups> {<solid> <numOfFaces> <faceId> ...}` deletes the named
faces and puts nothing in their place. The ids are grouped as `BREP_OFFSET_FACES` takes them: the ids of a group
are numbered inside that solid, in explorer order, or in the face map of the whole shape when the solid is 0. A
solid that loses a face is no longer closed, so it is written as the shells that are left of it, each face keeping
the orientation it had; a solid, shell or face that loses nothing is written as it was. The command fails when no
face would be left. When the faces left fall into more pieces than the shape had, two faces being in one piece
when they share an edge, `<out.brep>` holds the largest of them by area, every other piece is written as a shell
of its own to `<out>_000k.brep`, and `<out>.pieces` holds their number, because each piece becomes a part of its
own. PrePoMax runs it for Delete Faces of a CAD part. An opened solid is written as one shell, void shells
included, and a solid that loses every face is gone. `BREP_REMOVE_COMPOUND_FACES` takes the same arguments for a
compound of solids and writes the result in pieces: `<out.brep>` holds the solids that lost nothing, in their
order, every opened solid is written as `<out>_000k.brep` - as many files as it fell into pieces, the largest
first - and `<out>.opened` names the input solid of each and its number of files, one solid per line, and
`<out>.removed` names the solids that lost every face. A face two solids share is deleted
from both, so both are opened. PrePoMax keeps the compound
of the kept solids and turns each opened solid into a shell part of its own.

`BREP_MESH` reads two optional entries after `parallel_meshing_threads` in the mesh parameters file.
`transfinite_faces` meshes 4-sided faces as structured triangle grids when the edge meshing put the
same number of segments on their opposite sides: 0 none, 1 size checked - those whose grid passes the
size check below - and 2 all that qualify; `transfinite_angle` (135 by default, as in Gmsh) is the
angle below which the edges meeting at a vertex make a corner, so a face with a flatter corner is not
4-sided. The interior nodes are placed by transfinite interpolation in the parameter space of the
face, each cell is split into two triangles with the diagonals alternating from cell to cell as in
Gmsh's `AlternateLeft`, and those faces skip the surface optimisation so the grid stays structured. A
face that does not qualify, or whose grid would come out folded, is meshed as before. With 1 so is a
face whose grid would have more than twice the triangles the mesh size asks for there: the advancing
front coarsens from a finely divided side towards the mesh size inside the face, while a grid carries
that division across the whole face.
To make faces qualify, the edge meshing splits the wire of every face with four corners into its four
sides - each one edge or several - and raises segment counts until opposite sides add up to the same
number, the segments a side lacks going one at a time to its edge that is least refined for its mesh
size. A shared edge ties the faces around it together, so counts are only raised, and no edge is made
more than about twice as fine as its mesh size asks for. A face that cannot be balanced within that is
dropped and the rest are balanced again from the counts the mesh size asks for, so no edge is refined
for a face that is not going to be structured. The edges are then divided into their counts, spaced
as the local mesh size would space them.
With `transfinite_filename` the structured faces are the ones PrePoMax gives and none are detected.
Opposite sides are balanced to the coarser count where the counts are close: an edge that borders a face
not given keeps at least 0.8 of the count its mesh size asks for, since the free mesh beside it is made
to that size, and the edges it is balanced with are raised to it instead. The numbers of elements the
file pins are never changed; when they leave no room for those lowest counts, the counts give way.

A face may carry edges that do not bound it: an INTERNAL edge is a line lying on the face that does not
cut it through - where a non-manifold shell has another face meeting it along a line that stops inside
it - and an EXTERNAL edge lies outside it. The edge meshing gives an internal edge's segments to the face
once in each direction, so the advancing front closes around the line and the triangles on both sides
of it share its nodes; external edges are left out. Faces with either kind are not meshed as grids.

`VOL_VOLUME_MESH <in.vol> <out.vol> <parameters>` meshes a boundary it is given by tetrahedra. The
input holds the points and the closed boundary of every domain - triangles and quadrilaterals, each face
written for every domain it bounds, that domain inside and nothing outside, wound outward from it. The
points come first in the file, since a surface element marks its points as boundary points only when
they exist already, and a boundary point is one the volume optimisation never moves. So the boundary
points keep their place and are the first points of the output, in their input order, which lets the
caller join the elements to the mesh the boundary came from. A failed run leaves what it meshed in
`<out>_error.vol`. PrePoMax meshes the cells of a compound that its sweep cannot reach with it.

A pyramid stands on every quadrilateral, which took two changes to Netgen 5.3.1. `ruler3.cpp` accepted
a pyramid rule only where two opposite sides of the quadrilateral are identified point pairs, which a
boundary layer makes and nothing else does; without identified pairs in the mesh, a rule that gives the
pyramid an apex of its own is now accepted on any quadrilateral. A rule that takes its apex from a
neighbour is not, because it chains the pyramids of a whole face together and leaves gaps between them
that no tetrahedron closes - a 9 by 9 grid of quadrilaterals failed that way with 6 open faces. The two
rules with an apex of their own, `Pyramid on quad` and `small Pyramid on quad` in `pyramidrls.cpp`,
carried quality 100, and a rule is tried only once the class of its face reaches its quality, which the
quadrilateral passes give up on at 15. They carry 3 and 11 now, just above the badness their apexes
have, 2.5 and 10.1, so that they are tried after the rules that connect to an existing point. Measured on
a unit hexahedral block with tetrahedral boxes on it - one side, the top, both, a box wrapped round
a corner of the block and a box holding the block inside it as a cavity - every quadrilateral carries
a pyramid, the mesh is conformal, and the minimum SICN is 0.41 to 0.53 for the tetrahedra and 0.53 to
0.65 for the pyramids.

The volume optimisation had to learn about the pyramids as well. `CombineImprove` in `improve3.cpp`
collapses an edge by merging its two points, and it looked for them among the first four points of an
element only - a whole tetrahedron, but not a pyramid - so a pyramid holding one point as its apex and the
other in its base was counted as holding one of them and was kept, its apex merged into its base, instead
of being deleted. It now leaves an edge alone when an element on either point is not a tetrahedron, as
`SplitImprove` and `SwapImprove` already did. A mesh of tetrahedra alone is unchanged.

The smoothing, `ImproveMesh` in `smoothing3.cpp`, moves every inner point to where the badness of the
elements on it is least, and it weighed tetrahedra only: the apex of a pyramid was moved to suit the
tetrahedra around it and on `mixed_03` 13 of 211 pyramids came out with their apex through their base.
A pyramid is now weighed as the four tetrahedra its five points span, which turn inside out exactly when
the apex crosses the base. Keeping the points of pyramids fixed instead also stopped the inversion, but
left the tetrahedra around them at a minimum SICN of 0.029; weighed, they reach 0.259 and the pyramids
0.576. A mesh of tetrahedra alone is weighed as before.

A quadrilateral used to be scaled by the larger of its own size and the local mesh size, which suits a
boundary layer, whose prism has to reach as far as the tetrahedra beyond it. A pyramid scaled so stood
more than an edge of its base high wherever a fine swept mesh meets coarser tetrahedra, and in an inside
corner it leaned over the quadrilaterals of the other face and left no room for their pyramids:
PrePoMax's `mixed_03_1` kept 3 of its 233 quadrilaterals open and stopped. Without identified pairs a
quadrilateral is scaled by its own size now (`meshing3.cpp`); every quadrilateral of `mixed_03_1` carries a
pyramid, at a minimum SICN of 0.383, and its tetrahedra reach 0.275.

Two pyramids of the usual height on the two quadrilaterals of a sharp inside corner leave no room for one
another. On PrePoMax's `mixed_04` two faces meet at 60 degrees; the first pyramid's side face rose 49 degrees
from its base and 4 of 33 quadrilaterals stayed open. Over every edge where another quadrilateral of the front
closes an angle sharper than a right one with the base, a pyramid is now lowered until its side face rises no
more than a third of that angle (`meshing3.cpp`), which leaves the middle third to the tetrahedra. `mixed_04`
meshes at a minimum SICN of 0.330 for the tetrahedra and 0.592 for the pyramids. Lowering the pyramid in every
inside corner, and against triangles as well, also meshed it but cost `mixed_03` 0.255 to 0.218 in its
tetrahedra; limited to sharp corners between quadrilaterals the other fills come out as before.

`BREP_VISUALIZATION` writes the version 2 `.vis` format. It defines solids, shells, faces, edges, and vertices with their
CAD properties before a separate tessellation section. The extensible line format is documented in
[VIS_GEOMETRY_METADATA.md](VIS_GEOMETRY_METADATA.md).

BRepMesh triangulates a face only in part when the polylines of its edges cross in the parameter space of the face.
A relative deflection divides an edge for its own length, so the long curved edges of a thin face sag across its
width; on one face 0.3 wide along a 49 long edge, 5 triangles covered 6 % of it.
`BuildVisualizationMesh` finds such a face by triangulation nodes no triangle uses, and confirms it by triangles
covering less than half of its area. It then meshes again with a quarter of the deflection on the edges of that face, up to
three times, through an edge discretizer in the BRepMesh context. Only the faces of the edges divided differently are
meshed again, and the edges are shared in the discrete model, so the triangulations stay conforming and the rest
of the mesh does not change. A face that one refinement did not help gets its edges divided as before again, so its
neighbours are not meshed finer for nothing. A face still covered less than half is named in a warning.

## Building

Both solutions build **x64**, and nglib must be built first because the front end links `nglib.lib`:

    MSBuild "Netgen v5.3.1 port to OCCT 8.0.1\Netgen-master\netgen-5.3.1\windows\nglib.sln" -t:Build "-p:Configuration=Release(OCC)" -p:Platform=x64
    MSBuild "NetGenMesher 8.0.1\NetGenLibTest.sln" -t:Build -p:Configuration=Release -p:Platform=x64

Both write to `NetgenMesher\Release`. The nglib post build event syncs the OpenCASCADE, runtime,
pthreads and zlib dlls next to them, so that folder is the complete runtime set.

To deploy into PrePoMax, copy `NetGenMesher.exe` and `nglib.dll` from there over
`ThirdParty\netgen` in the PrePoMax repository and commit them - they are a matched pair and should
move together. The PrePoMax post build event copies that folder into `Meshers\Netgen`.

## What is not in this repository

Only sources and project files are tracked. These have to be restored by hand into a fresh clone
before it can build, because they are large and change only when the dependency is upgraded:

- `opencascade-8.0.1/` - an OpenCASCADE 8.0.1 build with the image, video, visualisation and
  parallel runtime dependencies disabled. **One copy is needed in each of the two solution
  folders**, since both resolve it relative to their own `$(SolutionDir)`.
- `pthreads-win32_prebuilt-dll-2-9-1-release/` and `zlib_win64/` - next to the netgen port's
  solution folder.
- `redist/` - the Visual C++ runtime dlls, at the repository root.

`_Old/` holds earlier versions of all of the above and is deliberately untracked.

# Version 2 `.vis` geometry and visualization format

`BREP_VISUALIZATION` writes every OpenCASCADE geometry entity once, followed by the tessellation used to display it.
The file begins with a version and two unit declarations:

```text
VIS file format: 2
Coordinate system: global
Length unit: model
```

Version 2 intentionally replaces the earlier visualization grammar. An abbreviated file with its two sections looks
like this:

```text
**********
Geometry
**********

Number of solids: 1

Solid number: 1
Solid orientation: Forward
Solid volume: 785.39816339744891
Solid center_of_mass: 0 0 5
Solid face_ids: 1 2 3

Number of shells: 1

Shell number: 1
Shell orientation: Forward
Shell closed: 1
Shell area: 471.23889803846936
Shell face_ids: 1 2 3

Number of faces: 3

Face number: 1
Face orientation: Forward
Face type: Cylinder
Face area: 314.15926535897933
Face axis: 0 0 0 0 0 1
Face radius: 5
Face convexity: Convex

Number of edges: 3

Edge number: 1
Edge orientation: Reversed
Edge type: Circle
Edge length: 31.415926535897949
Edge closed: 1
Edge sweep_angle_rad: 6.2831853071795898

Number of vertices: 2

Vertex number: 1
Vertex orientation: Forward
Vertex coordinates: 5 0 10
Vertex edge_ids: 1 2

**********
Visualization
**********

Number of visualization vertices: 2 (Id, X, Y, Z)
1 5 0 10
2 5 0 0

**********
Face mesh number: 1
**********
Number of nodes: 4 (Id, X, Y, Z)
1 5 0 0
2 0 5 0
3 -5 0 0
4 0 -5 0
**********
Number of triangles: 2 (Id, N1, N2, N3)
1 1 2 3
2 1 3 4
**********
Number of edge polylines: 1 (Edge Id, N1, N2, N3 ...)
Edge polyline: 1 1 2 3 4 1
```

An entity starts with `<Kind> number: <id>`. Its following lines use `<Kind> <property>: <values...>`. Blank lines end
the visual group but have no semantic meaning. A reader continues the entity until another entity header or section
header appears.

Every coordinate is written with 17 significant digits, the visualization nodes as well as the metadata. A point
picked on the visualization goes back to the modelling kernel, and a vertex rounded to six decimals lies a fraction of
a micron off the edges it is on - enough for a splitting plane through it to miss them and the split to lose pieces.

The entity kinds are `Solid`, `Shell`, `Face`, `Edge`, and `Vertex`. IDs are 1-based OpenCASCADE map IDs. Unknown
properties are ignored. A missing property means unavailable, so a property can be added or removed without changing
the grammar. The format version changes when the grammar or meaning of an existing property changes incompatibly.

The geometry section contains exact OpenCASCADE measurements, bounding boxes, orientations, topology links, and
analytic geometry parameters where they exist. `axis` has six values in this order:
`origin_x origin_y origin_z direction_x direction_y direction_z`. `x_direction` and `y_direction` describe the other
directions of an analytic geometry's OpenCASCADE position. Bounding boxes use
`x_min x_max y_min y_max z_min z_max`. An inertia tensor is one row-major sequence of nine values.

Every edge that is not degenerated provides `midpoint`, the point half way along it by arc length. It is not the `centroid`: the centroid of an arc does not lie on the arc. For a complete circle the midpoint falls opposite the seam and means nothing, so `closed` is what a reader checks before using it.

Circular edges provide `closed` (`1` for a complete circle, otherwise `0`) and `sweep_angle_rad`. The sweep is the
absolute OpenCASCADE curve-parameter span, so a semicircle reports pi and a complete circle reports 2 pi.

An edge whose curve is not analytic - a `BSplineCurve` or a `BezierCurve`, which is what a STEP file and a boolean
operation both leave behind for a line - provides `axis` as well when the curve stays on the line through its ends
within a relative tolerance of 1e-6. The `type` is unchanged: the axis says the edge is straight, not that a line
represents it. A reader that wants the direction an edge runs in reads `axis` and does not have to care which
curve carries it.

A cylindrical face belonging unambiguously to one solid provides `convexity`. `Convex` means the material is toward
the cylinder axis, as on a pin. `Concave` means the material is away from the axis, as in a cylindrical hole. The
property is omitted for shells, shared faces, or cases where the material side cannot be classified reliably.

All coordinates use the global coordinate system. `Length unit: model` means lengths use the geometry's native model
unit; areas and volumes use its square and cube. Directions are unitless and angles ending in `_rad` are radians.

The visualization section contains connectivity only. Face orientation and analytic type come from the matching face
definition; edge type comes from the matching edge definition. This prevents the same value from being written twice.
Face-local tessellation node IDs are offset by the reader as faces are combined. Visualization vertex IDs use the
global OpenCASCADE vertex IDs.

Topology list properties contain all IDs after the colon. `face_use_count` records the number of topological uses of
an edge. This can differ from the number of unique `face_ids`, for example when a seam edge occurs twice on one periodic
face.

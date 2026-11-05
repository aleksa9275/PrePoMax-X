# Original native CAD and Netgen meshing

Tasks [0063](../tasks/0063-native-cad-meshing-build.md) and
[0064](../tasks/0064-native-desktop-cad.md), 5 November 2026.

The original custom CAD and meshing implementation is recovered and runs
natively on macOS ARM64 and Linux ARM64. The Mac desktop imports the original L-bracket
STEP and two-part BREP through it, with background conversion and source
part/face picks. Original Netgen generates measured linear volume meshes.
Linux ARM64 also passes the same experiment in a separate verification container.
The new native Linux x64 CI job is awaiting publication; no hosted pass is
claimed at this checkpoint.

## Source and build

Upstream moved to [GitHub](https://github.com/PrePoMax/PrePoMax) on 4 November
and published [NetgenMesher](https://github.com/PrePoMax/NetgenMesher),
[patched Gmsh](https://github.com/PrePoMax/Gmsh) and
[modified QuadWild](https://github.com/PrePoMax/QuadWild). The exact observed
revisions are in [the source inventory](native-cad-meshing/upstream-sources.json).
The application baseline is unchanged.

All 517 original NetgenMesher repository files are retained unchanged with
individual hashes under `ThirdParty/Sources/NetgenMesher/c5ecb0ba/src`.
They contain the wrapper and modified Netgen 5.3.1 port to OCCT 8.0.1.
The build uses all 141 original nglib project compilation inputs, official
OCCT 8.0.1 at `b8f597c6`, native pthreads and system zlib. Two small patches
conditionalize Windows startup includes and supply its filename helpers on
POSIX. CAD and meshing algorithms are unchanged.
[Build recipe and source/archive identity](../../X/Build/NativeCad/README.md) ·
[Mac build receipt](native-cad-meshing/mac-build.json).

The local OCCT source archive has SHA-256
`dba62b81078dd43cec23feba89432be301582341001edad1b93342ad8bda35ea`.
It is verified and extracted into the isolated build cache. The final release
source/relinking bundle and matching Windows rebuild remain pending; source
labels alone do not establish correspondence to the released Windows binaries.

## Actual CAD comparison

The native STEP import writes the exact original L-bracket BREP hash
`7e768b0f462d2f897190168b5e9ee73c280aff44127cec4567a95568f35329b6`.
Source node IDs/coordinates, CAD edge segments and entity IDs match exactly
for all three parts in the two fixtures. Both native runs repeat exactly.

The exact decoded Windows-scene replay **fails** for the L-bracket and its
[receipt is retained](native-cad-meshing/mac-exact-replay-failure.json).
It remains unchanged. Native display triangles take the other diagonal on
L-bracket planar faces 1 and 6 and on the second box's planar faces 3 and 4.
The first box's decoded scene matches exactly. L-bracket centroid/inertia
metadata also has floating-point differences; its largest absolute difference
is approximately `5.96e-8` in an inertia entry near `6.29e7`.

The separate native experiment requires exact source nodes, edges and IDs,
and metadata within `1e-12` relative / `1e-10` absolute bounds (`1e-8` absolute
for near-zero inertia entries). Changed triangulations are allowed only on
planes with unchanged boundary, triangle count, area, oriented area vector
and first moment. Curved-face changes, altered orientation, wrong boundaries,
IDs and coordinates are rejected. Three mutation regression tests exercise
these rejection controls. These criteria are recorded separately and do not
turn the original exact comparison into a pass.
[Full Mac experiment](native-cad-meshing/mac-arm64.json).

Linux ARM64 builds from the same original source, patches and OCCT archive
with GCC in Ubuntu 24.04. Its relocated runtime passes the same two-repeat
CAD/meshing experiment in a separate container. Source nodes, edges and IDs
remain exact, measured geometry passes the same bounds, and the L-bracket mesh
has the same original Windows connectivity. Raw VIS bytes differ between the
native hosts. The receipts preserve each actual result rather than claiming
cross-host byte identity.
[Linux experiment](native-cad-meshing/linux-arm64.json) ·
[Linux build](native-cad-meshing/linux-build.json).

## Actual volume meshes

| Native input / size | Nodes | Linear tetrahedra | Boundary triangles | Measured volume |
| --- | ---: | ---: | ---: | ---: |
| L-bracket / 10 | 169 | 356 | 330 | 36,249.7761582 |
| First box / 3 | 142 | 403 | 240 | 2,000 |
| Second box / 3 | 69 | 160 | 124 | 768 |

The independent mesh measurement probe follows the original VOL reader's
tetrahedron permutation. Every tetrahedron then has positive signed volume;
every interior face belongs to two tetrahedra, every boundary face to one,
and the boundary is exactly the emitted CAD surface mesh. No volume node is
unused and every expected source face is present. Both boxes reproduce their
analytical/CAD volumes. The curved bracket is a linear approximation, matching
the original mesher's approximation rather than its exact CAD volume.

The actual official Windows 3.0.0 executable through CrossOver was run with
the same BREP and parameter bytes. Its L-bracket mesh has exactly the same
tetrahedron connectivity, surface connectivity, source CAD IDs and counts.
The largest coordinate difference from the first native run is `4.13e-10`
model units. The new experiment explicitly requires the same connectivity
and coordinates within `1e-8` model units.
[Original Windows mesh and capture receipt](native-cad-meshing-reference/receipt.json).

## Desktop and remaining integration

`--cad-native RUNTIME` selects this explicit research adapter and checks its
host/source receipt and all executable/library hashes before and after import.
The scene identifies its native conversion path. The existing reference
adapter remains available. Native L-bracket import/render/picks pass in the
frame bridge, and native two-part import/render/picks pass in the Cocoa adapter.
Six actual viewport workflow tests pass, including failure, cancellation,
late cancellation and previous-document preservation. Eight process/runtime
tests and three scene-identity tests pass.
[STEP desktop receipt](native-cad-meshing/mac-desktop-step.json) ·
[Two-part desktop receipt](native-cad-meshing/mac-desktop-parts.json).

CAD is still read-only; the measured `.vol` outputs are not yet editable
desktop analysis meshes. Next is the original VOL reader/mesh handoff and
desktop meshing controls, followed by CAD editing/repair coverage and the
remaining native Gmsh/QuadWild paths. Both original correctness failures,
the tetrahedron engineering gate, exact visualization parity, broader 3.0.0
parity and four-target/release acceptance remain open.

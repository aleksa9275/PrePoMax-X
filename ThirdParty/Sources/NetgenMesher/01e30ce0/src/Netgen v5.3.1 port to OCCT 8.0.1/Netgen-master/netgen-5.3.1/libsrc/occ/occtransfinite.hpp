#ifndef FILE_OCCTRANSFINITE
#define FILE_OCCTRANSFINITE

#include <map>
#include <string>
#include <vector>

namespace netgen
{
  /**
     Structured triangulation of a four sided face.

     Points follow the convention of the parallel face results: an element
     vertex that is already in the mesh keeps its number, a new point is
     referenced as -(1 based index into points).
  */
  struct OCCTransfiniteFaceMesh
  {
    std::vector<MeshPoint> points;
    std::vector<Element2d> elements;
  };

  /**
     Meshes face facenr as a transfinite region if it is one.

     The face qualifies when it has a single wire with exactly four corners -
     vertices where the edges meet at less than corner_angle degrees, 180 being
     a straight continuation - and the edge meshing already put the same number
     of segments on opposite sides.  The interior nodes are placed by
     transfinite interpolation in the parameter space of the face, and each grid
     cell is split into two triangles, the diagonals alternating from cell to
     cell.  Returns false, leaving result empty, when the face does not qualify
     or the grid comes out folded, so the caller can mesh it the usual way.  With
     check_size also when the grid has much more triangles than the mesh size
     asks for, since a grid cannot coarsen away from a finely divided side.

     Reads mesh and geom only, so faces can be built on worker threads.
  */
  bool BuildTransfiniteFaceMesh(const OCCGeometry & geom, const Mesh & mesh,
    int facenr, double corner_angle, bool check_size, OCCTransfiniteFaceMesh & result);

  /**
     Splits the wire of face facenr at its corners, in the sense of
     BuildTransfiniteFaceMesh, into four sides and gives the edges of each -
     as edge map numbers, in wire order.  Sides 0 and 2 are opposite, as are
     1 and 3.  The edge meshing makes opposite sides add up to the same
     segment count so that the face qualifies as a structured grid.  Returns
     false for a face that does not have exactly four corners.
  */
  bool CollectTransfiniteSides(const OCCGeometry & geom, int facenr,
    double corner_angle, std::vector<int> sides[4]);

  /**
     The structured faces PrePoMax finds by the one definition all its meshers
     follow, read from the transfinite file of the mesh parameters: the sides of
     every face as chains of edge map numbers in loop order, the number of
     segments the user set on an edge, and the names its messages use.  When
     the file is given, Netgen detects no structured faces of its own.  A
     three-sided face is three blocks of quads around one inner node, or, with
     a polar corner, the grid collapsed at that corner: polar_corners holds the
     side that starts at it.
  */
  struct OCCGivenTransfiniteFaces
  {
    bool loaded = false;
    std::map<int, std::vector<std::vector<int> > > sides;
    std::map<int, std::string> face_names;
    std::map<int, std::string> edge_names;
    std::map<int, int> pinned_counts;
    std::map<int, int> polar_corners;
  };

  OCCGivenTransfiniteFaces & GivenTransfiniteFaces();

  void LoadGivenTransfiniteFaces(const std::string & filename);

  /**
     Gives the opposite sides of every given face the same number of segments,
     for the coarser mesh.  Edges that are whole opposite sides carry one count,
     the one the user set on one of them or the lowest the mesh size asks for;
     sides that are chains of edges are balanced over these by lowering the
     larger side at its most refined edge, and a side is raised only where the
     other cannot be lowered.  Lowering evens out counts that are close: an
     edge that borders a free face, one not given, keeps at least 0.8 of its
     own count, and the edges it is balanced with are raised to it instead,
     unless the numbers the user set leave no room for that.  Pinned counts
     are never changed.  counts, own and borders_free_face are indexed by
     edge map number - 1, own holding the counts the mesh size asks for.
     Throws when the sides cannot be balanced, naming the faces and their
     edges.
  */
  void BalanceGivenTransfiniteEdgeCounts(const std::vector<int> & own, const std::vector<char> & borders_free_face,
                                         std::vector<int> & counts);

  /**
     Meshes a given face as a structured grid between the corners its sides
     give - quads when quads is set, else every cell split in two triangles.
     There is no fallback: the face is meshed as defined, and a grid that comes
     out folded throws, naming the face.
  */
  void BuildGivenTransfiniteFaceMesh(const OCCGeometry & geom, const Mesh & mesh, int facenr, bool quads,
    OCCTransfiniteFaceMesh & result);
}

#endif

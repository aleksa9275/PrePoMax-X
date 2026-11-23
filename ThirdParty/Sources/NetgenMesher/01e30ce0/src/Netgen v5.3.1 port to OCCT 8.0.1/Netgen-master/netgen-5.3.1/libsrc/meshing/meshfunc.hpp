#ifndef FILE_MESHFUNC
#define FILE_MESHFUNC

/**************************************************************************/
/* File:   meshfunc.hpp                                                   */
/* Author: Johannes Gerstmayr, Joachim Schoeberl                          */
/* Date:   26. Jan. 98                                                    */
/**************************************************************************/


/*
  Functions for mesh-generations strategies
 */

class Mesh;
// class CSGeometry;

/// Build tet-mesh
MESHING3_RESULT MeshVolume (MeshingParameters & mp, Mesh& mesh3d);

/// What the checks before volume meshing found out about the boundary mesh
struct VolumePrepareInfo
{
  /// a subdomain has open quadrilaterals, which only the serial path can mesh
  bool has_open_quads;
  /// boundary elements of subdomain k at position k-1, empty if not collected.
  /// Predicts the meshing cost of a subdomain closely and is used to mesh the
  /// largest subdomains first.
  Array<int> boundary_elements;

  VolumePrepareInfo () : has_open_quads(false) { ; }
};

/// Consistency checks that precede volume meshing (part of MeshVolume)
void MeshVolumePrepare (MeshingParameters & mp, Mesh& mesh3d,
                        VolumePrepareInfo * info = 0);

/// Volume mesh of one subdomain; mp.maxh is left at the subdomain limit
void MeshVolumeDomain (MeshingParameters & mp, Mesh& mesh3d, int domain,
                       double globmaxh);

/// Serial loop over all subdomains (part of MeshVolume)
MESHING3_RESULT MeshVolumeDomains (MeshingParameters & mp, Mesh& mesh3d);

/// Number of faces of the finished mesh that are shared by more than two
/// volume elements.  Zero for a valid mesh.
int CountNonManifoldVolumeFaces (const Mesh & mesh);

/// Prints the size of the finished volume mesh and, if the advancing front
/// reported face conflicts, whether they were repaired.
void ReportVolumeMeshingResult (const Mesh & mesh);

/// Volume meshing of independent subdomains with mp.parallel_meshing_threads
/// workers, including the per-domain removal of illegal elements and the
/// volume optimization.  Returns false, without touching the mesh, if the
/// parallel path is not applicable; the caller then uses the serial path.
bool MeshVolumeParallel (MeshingParameters & mp, Mesh& mesh3d,
                         const VolumePrepareInfo & info);

/// MeshVolume + RemoveIllegalElements + OptimizeVolume, in parallel over the
/// subdomains when the parameters ask for it
MESHING3_RESULT MeshVolumeAndOptimize (MeshingParameters & mp, Mesh& mesh3d);

/// Build mixed-element mesh
// MESHING3_RESULT MeshMixedVolume (MeshingParameters & mp, Mesh& mesh3d);

/// Optimize tet-mesh
MESHING3_RESULT OptimizeVolume (MeshingParameters & mp, Mesh& mesh3d);
//			       const CSGeometry * geometry = NULL);

void RemoveIllegalElements (Mesh & mesh3d);


enum MESHING_STEP { 
  MESHCONST_ANALYSE = 1,
  MESHCONST_MESHEDGES = 2,
  MESHCONST_MESHSURFACE = 3,
  MESHCONST_OPTSURFACE = 4,
  MESHCONST_MESHVOLUME = 5,
  MESHCONST_OPTVOLUME = 6
};


#endif

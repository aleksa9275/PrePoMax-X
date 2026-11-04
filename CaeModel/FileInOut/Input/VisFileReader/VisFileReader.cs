// PrePoMax - Copyright (C) 2016-2026 Matej Borovinšek
//
// Licensed under the terms defined in the LICENSE file located in the root directory of this source code.
//
// Source code: https://gitlab.com/MatejB/PrePoMax
//
// Author: Matej Borovinšek
// Contributors:

using System.Collections.Generic;
using System.Linq;
using System.IO;
using CaeMesh;

namespace FileInOut.Input
{
    public static partial class VisFileReader
    {
        public static FeMesh Read(string fileName)
        {
            if (File.Exists(fileName))
            {
                string data = File.ReadAllText(fileName);
                GeometryData geometry = ReadGeometryData(data);
                if (geometry == null) return null;
                GeometryMetadata sourceGeometryMetadata = geometry.Metadata;
                ImportOptions importOptions = ImportOptions.DetectEdges;
                // Import solid geometry
                if (sourceGeometryMetadata.GetEntities("solid").Length > 0)
                {
                    importOptions = ImportOptions.ImportOneCADSolidPart;
                }
                // Import shell geometry
                else if (sourceGeometryMetadata.GetEntities("shell").Length > 0 ||
                          sourceGeometryMetadata.GetEntities("face").Length > 0)
                {
                    importOptions = ImportOptions.ImportCADShellParts;
                }
                //
                FeMesh mesh = new FeMesh(geometry.Nodes, geometry.Elements, MeshRepresentation.Geometry, importOptions);
                //
                mesh.ConvertLineFeElementsToEdges(geometry.VertexNodeIds, true);
                MergeVisualizationFacesOfOneGeometryFace(mesh, geometry.ElementIdSurfaceId);
                //
                Dictionary<string, Dictionary<int, int>> partLocalFaceIdSourceFaceId =
                    new Dictionary<string, Dictionary<int, int>>();
                Dictionary<string, Dictionary<int, int>> partLocalEdgeIdSourceEdgeId =
                    new Dictionary<string, Dictionary<int, int>>();
                mesh.RenumberVisualizationSurfaces(geometry.SurfaceIdNodeIds, geometry.FaceTypes,
                                                   partLocalFaceIdSourceFaceId);
                mesh.RenumberVisualizationEdges(geometry.EdgeIdNodeIds, geometry.EdgeTypes,
                                                partLocalEdgeIdSourceEdgeId);
                //
                mesh.RemoveElementsByType<FeElement1D>();
                mesh.RemoveElementsByType<FeElement3D>();
                // The metadata entity IDs are converted from OCC IDs to the same local, 1-based IDs
                // used by PrePoMax selections. Exact CAD measurements become the canonical values of
                // geometry parts; later mesh transfer only fills values that the mesh does not have.
                foreach (var entry in mesh.Parts)
                {
                    Dictionary<int, int> localFaceIdSourceFaceId;
                    Dictionary<int, int> localEdgeIdSourceEdgeId;
                    partLocalFaceIdSourceFaceId.TryGetValue(entry.Key, out localFaceIdSourceFaceId);
                    partLocalEdgeIdSourceEdgeId.TryGetValue(entry.Key, out localEdgeIdSourceEdgeId);
                    entry.Value.GeometryMetadata =
                        GeometryMetadataReader.CreatePartMetadata(sourceGeometryMetadata,
                                                                  localFaceIdSourceFaceId,
                                                                  localEdgeIdSourceEdgeId);
                    GeometryMetadataReader.ApplyCanonicalMeasurements(entry.Value);
                }
                return mesh;
            }
            //
            return null;
        }
        // An internal edge that runs from boundary to boundary cuts its face in the flood fill of the visualization
        // faces, although the geometry face stays one. Merge such pieces again, so the visualization faces are the
        // geometry faces.
        private static void MergeVisualizationFacesOfOneGeometryFace(FeMesh mesh, Dictionary<int, int> elementIdSurfaceId)
        {
            foreach (var part in mesh.Parts.Values)
            {
                VisualizationData vis = part.Visualization;
                if (vis.CellIdsByFace == null || vis.FaceEdgeIds == null ||
                    vis.FaceEdgeIds.Length != vis.CellIdsByFace.Length) continue;
                //
                int surfaceId;
                int newFaceId;
                Dictionary<int, int> surfaceIdNewFaceId = new Dictionary<int, int>();
                List<List<int>> faceCellIds = new List<List<int>>();
                List<List<int>> faceEdgeIds = new List<List<int>>();
                for (int faceId = 0; faceId < vis.CellIdsByFace.Length; faceId++)
                {
                    // A face of unknown origin is kept as it is
                    if (vis.CellIdsByFace[faceId].Length == 0 ||
                        !elementIdSurfaceId.TryGetValue(vis.CellIds[vis.CellIdsByFace[faceId][0]], out surfaceId))
                        surfaceId = -1 - faceId;
                    //
                    if (!surfaceIdNewFaceId.TryGetValue(surfaceId, out newFaceId))
                    {
                        newFaceId = faceCellIds.Count;
                        surfaceIdNewFaceId.Add(surfaceId, newFaceId);
                        faceCellIds.Add(new List<int>());
                        faceEdgeIds.Add(new List<int>());
                    }
                    faceCellIds[newFaceId].AddRange(vis.CellIdsByFace[faceId]);
                    foreach (int edgeId in vis.FaceEdgeIds[faceId])
                    {
                        if (!faceEdgeIds[newFaceId].Contains(edgeId)) faceEdgeIds[newFaceId].Add(edgeId);
                    }
                }
                if (faceCellIds.Count == vis.CellIdsByFace.Length) continue;
                //
                vis.CellIdsByFace = faceCellIds.Select(cellIds => cellIds.ToArray()).ToArray();
                vis.FaceEdgeIds = faceEdgeIds.Select(edgeIds => edgeIds.ToArray()).ToArray();
                vis.FaceAreas = new double[vis.CellIdsByFace.Length];
                for (int i = 0; i < vis.FaceAreas.Length; i++) vis.FaceAreas[i] = mesh.ComputeFaceArea(vis, i, mesh.Nodes);
                vis.FaceTypes = null;
            }
        }
    }
}

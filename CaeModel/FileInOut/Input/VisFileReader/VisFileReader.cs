// PrePoMax - Copyright (C) 2016-2026 Matej Borovinšek
//
// Licensed under the terms defined in the LICENSE file located in the root directory of this source code.
//
// Source code: https://github.com/PrePoMax/PrePoMax
//
// Author: Matej Borovinšek
// Contributors:

using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using CaeMesh;
using CaeGlobals;

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
                GroupVisualizationFacesByGeometryFace(mesh, geometry.ElementIdSurfaceId);
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
        // The visualization faces are flood filled over the cell edges that are not model edges, so they differ from the
        // geometry faces in two ways. An internal edge that runs from boundary to boundary cuts its face, although the
        // geometry face stays one. And two faces that both fill the sliver between a curved edge and its chords with
        // triangles of the same nodes share a chord with four cells, so the flood fill leaks from one face into the
        // other. Regroup the cells by the geometry face they were read from, so the visualization faces are the
        // geometry faces.
        private static void GroupVisualizationFacesByGeometryFace(FeMesh mesh, Dictionary<int, int> elementIdSurfaceId)
        {
            foreach (var part in mesh.Parts.Values)
            {
                VisualizationData vis = part.Visualization;
                if (vis.CellIdsByFace == null || vis.FaceEdgeIds == null ||
                    vis.FaceEdgeIds.Length != vis.CellIdsByFace.Length) continue;
                //
                int surfaceId;
                int newFaceId;
                bool split = false;
                Dictionary<int, int> surfaceIdNewFaceId = new Dictionary<int, int>();
                List<List<int>> faceCellIds = new List<List<int>>();
                List<List<int>> faceEdgeIds = new List<List<int>>();
                List<bool> splitFaces = new List<bool>();
                for (int faceId = 0; faceId < vis.CellIdsByFace.Length; faceId++)
                {
                    HashSet<int> faceNewFaceIds = new HashSet<int>();
                    foreach (int cellId in vis.CellIdsByFace[faceId])
                    {
                        // A cell of unknown origin stays in its face
                        if (!elementIdSurfaceId.TryGetValue(vis.CellIds[cellId], out surfaceId)) surfaceId = -1 - faceId;
                        //
                        if (!surfaceIdNewFaceId.TryGetValue(surfaceId, out newFaceId))
                        {
                            newFaceId = faceCellIds.Count;
                            surfaceIdNewFaceId.Add(surfaceId, newFaceId);
                            faceCellIds.Add(new List<int>());
                            faceEdgeIds.Add(new List<int>());
                            splitFaces.Add(false);
                        }
                        faceCellIds[newFaceId].Add(cellId);
                        faceNewFaceIds.Add(newFaceId);
                    }
                    if (faceNewFaceIds.Count > 1)
                    {
                        split = true;
                        foreach (int faceNewFaceId in faceNewFaceIds) splitFaces[faceNewFaceId] = true;
                    }
                    foreach (int faceNewFaceId in faceNewFaceIds)
                    {
                        foreach (int edgeId in vis.FaceEdgeIds[faceId])
                        {
                            if (!faceEdgeIds[faceNewFaceId].Contains(edgeId)) faceEdgeIds[faceNewFaceId].Add(edgeId);
                        }
                    }
                }
                if (!split && faceCellIds.Count == vis.CellIdsByFace.Length) continue;
                // The edges of a face that was split are those that bound its own cells
                if (split)
                {
                    int edgeId;
                    int[] key;
                    CompareIntArray comparer = new CompareIntArray();
                    Dictionary<int[], int> edgeCellKeyEdgeId = new Dictionary<int[], int>(comparer);
                    for (int i = 0; i < vis.EdgeCellIdsByEdge.Length; i++)
                    {
                        foreach (int edgeCellId in vis.EdgeCellIdsByEdge[i])
                        {
                            key = vis.EdgeCells[edgeCellId].ToArray();
                            Array.Sort(key);
                            if (!edgeCellKeyEdgeId.ContainsKey(key)) edgeCellKeyEdgeId.Add(key, i);
                        }
                    }
                    //
                    for (int i = 0; i < faceCellIds.Count; i++)
                    {
                        if (!splitFaces[i]) continue;
                        //
                        faceEdgeIds[i].Clear();
                        foreach (int cellId in faceCellIds[i])
                        {
                            foreach (int[] cellEdge in FeMesh.GetVisualizationEdgeCells(vis.Cells[cellId],
                                                                                      ElementFaceType.Face))
                            {
                                key = cellEdge.ToArray();
                                Array.Sort(key);
                                if (edgeCellKeyEdgeId.TryGetValue(key, out edgeId) && !faceEdgeIds[i].Contains(edgeId))
                                    faceEdgeIds[i].Add(edgeId);
                            }
                        }
                    }
                }
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

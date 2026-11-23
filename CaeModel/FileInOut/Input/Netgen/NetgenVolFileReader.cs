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
using System.Text;
using System.Threading.Tasks;
using System.IO;
using CaeMesh;
using CaeGlobals;

namespace FileInOut.Input
{
    public static partial class NetgenVolFileReader
    {
        // Methods                                                                                                                  
        static public FeMesh Read(string fileName, ElementsToImport elementsToImport)
        {
            return Read(fileName, elementsToImport, false);
        }
        static public FeMesh Read(string fileName, ElementsToImport elementsToImport, bool convertToSecondOrder)
        {
            if (fileName != null && File.Exists(fileName))
            {
                string[] lines =  CaeGlobals.Tools.ReadAllLines(fileName);
                //
                List<List<string>> dataSets = GetDataSets(lines);
                //
                int elementStartId = 1;
                Dictionary<int, FeNode> nodes = null;
                Dictionary<int, FeElement> elements = new Dictionary<int,FeElement>();
                // Geometry: itemId, allNodeIds
                Dictionary<int, HashSet<int>> surfaceIdNodeIds = new Dictionary<int, HashSet<int>>();
                Dictionary<int, HashSet<int>> edgeIdNodeIds = new Dictionary<int, HashSet<int>>();
                HashSet<int> vertexNodeIds = new HashSet<int>();
                //
                foreach (List<string> dataSet in dataSets)
                {
                    // Nodes
                    if (dataSet[0] == NetgenVolKeywords.points.ToString()) 
                    {
                        nodes = GetNodes(dataSet.ToArray());
                    }
                    // 3D Elements
                    else if (dataSet[0] == NetgenVolKeywords.volumeelements.ToString())           
                    {
                        AddVolumeElements(dataSet.ToArray(), elements, ref elementStartId);
                    }
                    // 2D Elements
                    else if (dataSet[0] == NetgenVolKeywords.surfaceelements.ToString() ||
                             dataSet[0] == NetgenVolKeywords.surfaceelementsuv.ToString())        
                    {
                        AddSurfaceElements(dataSet.ToArray(), elements, ref elementStartId, surfaceIdNodeIds);
                    }
                    // 1D Elements - always import
                    else if (dataSet[0] == NetgenVolKeywords.edgesegmentsgi2.ToString())          
                    {
                        AddLineElements(dataSet.ToArray(), elements, ref elementStartId, edgeIdNodeIds, vertexNodeIds);
                    }
                }
                //
                MergeEdgeElements(elements);
                //
                FeMesh mesh = new FeMesh(nodes, elements, MeshRepresentation.Mesh, null, null, convertToSecondOrder,
                                         ImportOptions.DetectEdges);
                //
                mesh.ConvertLineFeElementsToEdges(vertexNodeIds, true);
                //
                mesh.RenumberVisualizationSurfaces(surfaceIdNodeIds);
                mesh.RenumberVisualizationEdges(edgeIdNodeIds);
                //
                if (elementsToImport != ElementsToImport.All)
                {
                    if (!elementsToImport.HasFlag(ElementsToImport.Beam)) mesh.RemoveElementsByType<FeElement1D>();
                    if (!elementsToImport.HasFlag(ElementsToImport.Shell)) mesh.RemoveElementsByType<FeElement2D>();
                    if (!elementsToImport.HasFlag(ElementsToImport.Solid)) mesh.RemoveElementsByType<FeElement3D>();
                }
                //
                // Recognize the face and the edge types from the mesh
                mesh.DetectFaceTypes();
                mesh.DetectEdgeTypes();
                //
                return mesh;
            }
            //
            return null;
        }
        //
    }
}

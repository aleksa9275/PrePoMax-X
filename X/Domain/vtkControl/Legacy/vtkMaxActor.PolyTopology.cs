// Original topology conversion, shared unchanged with the headless data sink.
using System;
using System.Collections.Generic;
using System.Linq;
using CaeGlobals;
using Kitware.VTK;
namespace vtkControl
{
    public partial class vtkMaxActor
    {
        private static void AddCellDataToPoly(PartExchangeData data, ref vtkPolyData polyActor, ref vtkPolyData polyEdges,
                                              out int[] numOfCellPolys, bool extractEdges)
        {
            double d1;
            double d2;
            //
            int[] nodeIds;
            double[][] nodeCoor;
            int cellType;
            bool isVertex;
            bool isEdge;
            bool isSurface;
            vtkIdList nodeList = vtkIdList.New();
            vtkIdList edgeNodeList = vtkIdList.New();
            //
            numOfCellPolys = null;
            if (data.Cells.Ids != null)
            {
                numOfCellPolys = new int[data.Cells.Ids.Length];
            }
            //
            int vertexType = (int)vtkCellType.VTK_VERTEX;
            int lineType = (int)vtkCellType.VTK_LINE;
            int polyLineType = (int)vtkCellType.VTK_POLY_LINE;
            int quadraticEdgeType = (int)vtkCellType.VTK_QUADRATIC_EDGE;
            int triangleType = (int)vtkCellType.VTK_TRIANGLE;
            int quadType = (int)vtkCellType.VTK_QUAD;
            int quadraticTriangleType = (int)vtkCellType.VTK_QUADRATIC_TRIANGLE;
            int quadraticQuadType = (int)vtkCellType.VTK_QUADRATIC_QUAD;
            //
            polyActor.Allocate(10000, 10000);
            if (extractEdges) polyEdges.Allocate(1000, 1000);
            //
            int id1;
            int id2;
            int id3;
            HashSet<int> uniqueVertexIds = new HashSet<int>();
            CompareIntArray comparer = new CompareIntArray();
            HashSet<int[]> uniqueEdgeCells = new HashSet<int[]>(comparer);
            HashSet<int[]> uniquePolyEdgeCells = new HashSet<int[]>(comparer);
            //
            for (int i = 0; i < data.Cells.CellNodeIds.Length; i++)
            {
                nodeIds = data.Cells.CellNodeIds[i];
                cellType = data.Cells.Types[i];
                isVertex = cellType == vertexType;
                isEdge = cellType == lineType || cellType == quadraticEdgeType;
                isSurface = cellType == triangleType || cellType == quadType || cellType == quadraticTriangleType ||
                            cellType == quadraticQuadType;
                // Cell edges
                if (extractEdges)
                {
                    if (isEdge)
                    {
                        uniqueVertexIds.UnionWith(nodeIds);
                    }
                    else if (isSurface)
                    {
                        if (cellType == triangleType)
                        {
                            for (int j = 0; j < 3; j++)
                            {
                                id1 = nodeIds[j];
                                id2 = nodeIds[(j + 1) % 3];
                                uniqueEdgeCells.Add(new int[] { Math.Min(id1, id2), Math.Max(id1, id2) });
                            }
                        }
                        else if (cellType == quadType)
                        {
                            for (int j = 0; j < 4; j++)
                            {
                                id1 = nodeIds[j];
                                id2 = nodeIds[(j + 1) % 4];
                                uniqueEdgeCells.Add(new int[] { Math.Min(id1, id2), Math.Max(id1, id2) });
                            }
                        }
                        else if (cellType == quadraticTriangleType)
                        {
                            for (int j = 0; j < 3; j++)
                            {
                                id1 = nodeIds[j];
                                id2 = nodeIds[j + 3];
                                id3 = nodeIds[(j + 1) % 3];
                                if (id1 < id3) uniquePolyEdgeCells.Add(new int[] { id1, id2, id3 });
                                else uniquePolyEdgeCells.Add(new int[] { id3, id2, id1 });
                            }
                        }
                        else if (cellType == quadraticQuadType)
                        {
                            for (int j = 0; j < 4; j++)
                            {
                                id1 = nodeIds[j];
                                id2 = nodeIds[j + 4];
                                id3 = nodeIds[(j + 1) % 4];
                                if (id1 < id3) uniquePolyEdgeCells.Add(new int[] { id1, id2, id3 });
                                else uniquePolyEdgeCells.Add(new int[] { id3, id2, id1 });
                            }
                        }
                    }
                }
                // Cells
                if (isVertex)
                {
                    nodeList.SetNumberOfIds(1);
                    //if (cellType == vertexType)
                    {
                        nodeList.SetId(0, nodeIds[0]);
                        polyActor.InsertNextCell(vertexType, nodeList);
                        if (numOfCellPolys != null) numOfCellPolys[i] = 1;
                    }
                }
                else if (isEdge)
                {
                    nodeList.SetNumberOfIds(2);
                    if (cellType == lineType)
                    {
                        nodeList.SetId(0, nodeIds[0]);
                        nodeList.SetId(1, nodeIds[1]);
                        polyActor.InsertNextCell(lineType, nodeList);
                        if (numOfCellPolys != null) numOfCellPolys[i] = 1;
                    }
                    else if (cellType == quadraticEdgeType)
                    {
                        nodeList.SetId(0, nodeIds[0]);
                        nodeList.SetId(1, nodeIds[2]);
                        polyActor.InsertNextCell(lineType, nodeList);
                        nodeList.SetId(0, nodeIds[2]);
                        nodeList.SetId(1, nodeIds[1]);
                        polyActor.InsertNextCell(lineType, nodeList);
                        if (numOfCellPolys != null) numOfCellPolys[i] = 2;
                    }
                }
                else if (isSurface)
                {
                    nodeList.SetNumberOfIds(3);
                    if (cellType == triangleType)
                    {
                        nodeList.SetId(0, nodeIds[0]);
                        nodeList.SetId(1, nodeIds[1]);
                        nodeList.SetId(2, nodeIds[2]);
                        polyActor.InsertNextCell(triangleType, nodeList);
                        if (numOfCellPolys != null) numOfCellPolys[i] = 1;
                    }
                    else if (cellType == quadType)
                    {
                        nodeList.SetId(0, nodeIds[0]);
                        nodeList.SetId(1, nodeIds[1]);
                        nodeList.SetId(2, nodeIds[2]);
                        polyActor.InsertNextCell(triangleType, nodeList);
                        nodeList.SetId(0, nodeIds[0]);
                        nodeList.SetId(1, nodeIds[2]);
                        nodeList.SetId(2, nodeIds[3]);
                        polyActor.InsertNextCell(triangleType, nodeList);
                        if (numOfCellPolys != null) numOfCellPolys[i] = 2;
                    }
                    else if (cellType == quadraticTriangleType)
                    {
                        nodeList.SetId(0, nodeIds[0]);
                        nodeList.SetId(1, nodeIds[3]);
                        nodeList.SetId(2, nodeIds[5]);
                        polyActor.InsertNextCell(triangleType, nodeList);
                        nodeList.SetId(0, nodeIds[3]);
                        nodeList.SetId(1, nodeIds[4]);
                        nodeList.SetId(2, nodeIds[5]);
                        polyActor.InsertNextCell(triangleType, nodeList);
                        nodeList.SetId(0, nodeIds[3]);
                        nodeList.SetId(1, nodeIds[1]);
                        nodeList.SetId(2, nodeIds[4]);
                        polyActor.InsertNextCell(triangleType, nodeList);
                        nodeList.SetId(0, nodeIds[5]);
                        nodeList.SetId(1, nodeIds[4]);
                        nodeList.SetId(2, nodeIds[2]);
                        polyActor.InsertNextCell(triangleType, nodeList);
                        if (numOfCellPolys != null) numOfCellPolys[i] = 4;
                    }
                    else if (cellType == quadraticQuadType)
                    {
                        nodeCoor = data.Nodes.Coor;
                        d1 = Vec3D.GetDirVec(nodeCoor[nodeIds[4]], nodeCoor[nodeIds[6]]).Len2;
                        d2 = Vec3D.GetDirVec(nodeCoor[nodeIds[5]], nodeCoor[nodeIds[7]]).Len2;
                        if (d1 < d2)
                        {
                            nodeList.SetId(0, nodeIds[7]);
                            nodeList.SetId(1, nodeIds[0]);
                            nodeList.SetId(2, nodeIds[4]);
                            polyActor.InsertNextCell(triangleType, nodeList);
                            nodeList.SetId(0, nodeIds[7]);
                            nodeList.SetId(1, nodeIds[4]);
                            nodeList.SetId(2, nodeIds[6]);
                            polyActor.InsertNextCell(triangleType, nodeList);
                            nodeList.SetId(0, nodeIds[7]);
                            nodeList.SetId(1, nodeIds[6]);
                            nodeList.SetId(2, nodeIds[3]);
                            polyActor.InsertNextCell(triangleType, nodeList);
                            nodeList.SetId(0, nodeIds[5]);
                            nodeList.SetId(1, nodeIds[4]);
                            nodeList.SetId(2, nodeIds[1]);
                            polyActor.InsertNextCell(triangleType, nodeList);
                            nodeList.SetId(0, nodeIds[5]);
                            nodeList.SetId(1, nodeIds[6]);
                            nodeList.SetId(2, nodeIds[4]);
                            polyActor.InsertNextCell(triangleType, nodeList);
                            nodeList.SetId(0, nodeIds[5]);
                            nodeList.SetId(1, nodeIds[2]);
                            nodeList.SetId(2, nodeIds[6]);
                            polyActor.InsertNextCell(triangleType, nodeList);
                        }
                        else
                        {
                            nodeList.SetId(0, nodeIds[4]);
                            nodeList.SetId(1, nodeIds[7]);
                            nodeList.SetId(2, nodeIds[0]);
                            polyActor.InsertNextCell(triangleType, nodeList);
                            nodeList.SetId(0, nodeIds[4]);
                            nodeList.SetId(1, nodeIds[5]);
                            nodeList.SetId(2, nodeIds[7]);
                            polyActor.InsertNextCell(triangleType, nodeList);
                            nodeList.SetId(0, nodeIds[4]);
                            nodeList.SetId(1, nodeIds[1]);
                            nodeList.SetId(2, nodeIds[5]);
                            polyActor.InsertNextCell(triangleType, nodeList);
                            nodeList.SetId(0, nodeIds[6]);
                            nodeList.SetId(1, nodeIds[5]);
                            nodeList.SetId(2, nodeIds[2]);
                            polyActor.InsertNextCell(triangleType, nodeList);
                            nodeList.SetId(0, nodeIds[6]);
                            nodeList.SetId(1, nodeIds[7]);
                            nodeList.SetId(2, nodeIds[5]);
                            polyActor.InsertNextCell(triangleType, nodeList);
                            nodeList.SetId(0, nodeIds[6]);
                            nodeList.SetId(1, nodeIds[3]);
                            nodeList.SetId(2, nodeIds[7]);
                            polyActor.InsertNextCell(triangleType, nodeList);
                        }
                        if (numOfCellPolys != null) numOfCellPolys[i] = 6;
                    }
                    else throw new NotSupportedException();
                }
                else throw new NotSupportedException();
            }
            //
            if (extractEdges)
            {
                edgeNodeList.SetNumberOfIds(1);
                foreach (var vertexId in uniqueVertexIds)
                {
                    edgeNodeList.SetId(0, vertexId);
                    polyEdges.InsertNextCell(vertexType, edgeNodeList);
                }
                //
                edgeNodeList.SetNumberOfIds(2);
                foreach (var edgeCell in uniqueEdgeCells)
                {
                    edgeNodeList.SetId(0, edgeCell[0]);
                    edgeNodeList.SetId(1, edgeCell[1]);
                    polyEdges.InsertNextCell(lineType, edgeNodeList);
                }
                //
                edgeNodeList.SetNumberOfIds(3);
                foreach (var polyEdgeCell in uniquePolyEdgeCells)
                {
                    edgeNodeList.SetId(0, polyEdgeCell[0]);
                    edgeNodeList.SetId(1, polyEdgeCell[1]);
                    edgeNodeList.SetId(2, polyEdgeCell[2]);
                    polyEdges.InsertNextCell(polyLineType, edgeNodeList);
                }
            }
            //
            polyActor.Squeeze();
            if (extractEdges) polyEdges.Squeeze();
        }
    }
}

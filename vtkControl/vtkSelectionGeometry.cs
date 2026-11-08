// Original selection geometry, moved without arithmetic/tolerance changes.
using System;
using System.Linq;
using Kitware.VTK;
namespace vtkControl
{
    public static class vtkSelectionGeometry
    {
        public static void GetClosestEdgeCell(double[] pickedPoint, vtkMaxActorData cellFaceData, out int[] nodeIds,
                                        out double[][] nodeCoor, out int[] edgeCell, out int edgeCellType)
        {
            nodeIds = null;
            nodeCoor = null;
            edgeCell = null;
            edgeCellType = -1;
            if (cellFaceData == null) return;
            //
            double[][] allNodeCoor = cellFaceData.Geometry.Nodes.Coor;
            int[] allNodeIds = cellFaceData.Geometry.Nodes.Ids;
            //
            int[][] cellEdges = GetVisualizationCellEdges(cellFaceData.Geometry.Nodes.Ids.Length);
            //
            double[] d = new double[cellEdges.Length];
            for (int i = 0; i < cellEdges.Length; i++)
            {
                if (cellEdges[i].Length == 2)       // linear edge
                {
                    d[i] = PointToLineSegmentDistance(pickedPoint, allNodeCoor[cellEdges[i][0]], allNodeCoor[cellEdges[i][1]]);
                }
                else if (cellEdges[i].Length == 3)  // parabolic edge
                {
                    d[i] = Math.Min(PointToLineSegmentDistance(pickedPoint, allNodeCoor[cellEdges[i][0]], allNodeCoor[cellEdges[i][1]]),
                                    PointToLineSegmentDistance(pickedPoint, allNodeCoor[cellEdges[i][1]], allNodeCoor[cellEdges[i][2]]));
                }
            }
            //
            double min = d[0];
            int minId = 0;
            for (int i = 1; i < d.Length; i++)
            {
                if (d[i] < min)
                {
                    min = d[i];
                    minId = i;
                }
            }
            //
            int numOfNodes = cellEdges[minId].Length;
            nodeIds = new int[numOfNodes];
            nodeCoor = new double[numOfNodes][];
            for (int i = 0; i < nodeIds.Length; i++)
            {
                nodeIds[i] = allNodeIds[cellEdges[minId][i]];
                nodeCoor[i] = allNodeCoor[cellEdges[minId][i]];
            }
            if (numOfNodes == 2)
            {
                edgeCell = new int[] { 0, 1 };
                edgeCellType = (int)vtkCellType.VTK_LINE;
            }
            else if (numOfNodes == 3)
            {
                edgeCell = new int[] { 0, 2, 1 };
                edgeCellType = (int)vtkCellType.VTK_QUADRATIC_EDGE;
            }
            else throw new NotSupportedException();
            // Swap edge node ids and coor so that first node is the closest
            double[] firstCoor = allNodeCoor[cellEdges[minId].First()];
            double[] lastCoor = allNodeCoor[cellEdges[minId].Last()];
            //
            double d1 = Math.Pow(pickedPoint[0] - firstCoor[0], 2) +
                        Math.Pow(pickedPoint[1] - firstCoor[1], 2) +
                        Math.Pow(pickedPoint[2] - firstCoor[2], 2);
            //
            double d2 = Math.Pow(pickedPoint[0] - lastCoor[0], 2) +
                        Math.Pow(pickedPoint[1] - lastCoor[1], 2) +
                        Math.Pow(pickedPoint[2] - lastCoor[2], 2);
            //
            bool swap = d2 < d1;
            int tmpId;
            double[] tmpCoor;
            //
            if (swap)
            {
                tmpId = nodeIds[0];
                nodeIds[0] = nodeIds[numOfNodes - 1];
                nodeIds[numOfNodes - 1] = tmpId;
                //
                tmpCoor = nodeCoor[0];
                nodeCoor[0] = nodeCoor[numOfNodes - 1];
                nodeCoor[numOfNodes - 1] = tmpCoor;
            }
        }
        public static int[][] GetVisualizationCellEdges(int numOfNodes)
        {
            // lookup - leave here for future searches

            int[] nodeIds = Enumerable.Range(0, numOfNodes).ToArray();
            if (nodeIds.Length == 3)
            {
                return new int[][] {    new int[] { nodeIds[0], nodeIds[1] },
                                        new int[] { nodeIds[1], nodeIds[2] },
                                        new int[] { nodeIds[2], nodeIds[0] } };
            }
            else if (nodeIds.Length == 4)
            {
                return new int[][] {    new int[] { nodeIds[0], nodeIds[1] },
                                        new int[] { nodeIds[1], nodeIds[2] },
                                        new int[] { nodeIds[2], nodeIds[3] },
                                        new int[] { nodeIds[3], nodeIds[0] } };
            }
            else if (nodeIds.Length == 6)
            {
                return new int[][] {    new int[] { nodeIds[0], nodeIds[3], nodeIds[1] },
                                        new int[] { nodeIds[1], nodeIds[4], nodeIds[2] },
                                        new int[] { nodeIds[2], nodeIds[5], nodeIds[0] } };
            }
            else if (nodeIds.Length == 8)
            {
                return new int[][] {    new int[] { nodeIds[0], nodeIds[4], nodeIds[1] },
                                        new int[] { nodeIds[1], nodeIds[5], nodeIds[2] },
                                        new int[] { nodeIds[2], nodeIds[6], nodeIds[3] },
                                        new int[] { nodeIds[3], nodeIds[7], nodeIds[0] } };
            }
            else throw new NotSupportedException();
        }
        private static double PointToLineSegmentDistance(double[] p, double[] l1, double[] l2)
        {
            double[] n = new double[] { l2[0] - l1[0], l2[1] - l1[1], l2[2] - l1[2] };
            double d = Math.Sqrt(Math.Pow(n[0], 2) + Math.Pow(n[1], 2) + Math.Pow(n[2], 2));
            if (d <= 0) return 0;
            // normalize
            n[0] /= d;
            n[1] /= d;
            n[2] /= d;

            double[] a = new double[] { p[0] - l1[0], p[1] - l1[1], p[2] - l1[2] };
            double aProj = a[0] * n[0] + a[1] * n[1] + a[2] * n[2];

            if (aProj <= 0)
            {
                d = Math.Sqrt(Math.Pow(a[0], 2) + Math.Pow(a[1], 2) + Math.Pow(a[2], 2));
                return d;
            }
            else if (aProj >= d)
            {
                double[] b = new double[] { l2[0] - p[0], l2[1] - p[1], l2[2] - p[2] };
                d = Math.Sqrt(Math.Pow(b[0], 2) + Math.Pow(b[1], 2) + Math.Pow(b[2], 2));
                return d;
            }
            else
            {
                double[] c = new double[] { a[0] - aProj * n[0], a[1] - aProj * n[1], a[2] - aProj * n[2] };
                d = Math.Sqrt(Math.Pow(c[0], 2) + Math.Pow(c[1], 2) + Math.Pow(c[2], 2));
                return d;
            }
        }
    }
}

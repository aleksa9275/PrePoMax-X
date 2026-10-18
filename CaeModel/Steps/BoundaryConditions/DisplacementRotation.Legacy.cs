// PrePoMax - Copyright (C) 2016-2026 Matej Borovinšek
//
// Licensed under the terms defined in the LICENSE file located in the root directory of this source code.
//
// Source code: https://gitlab.com/MatejB/PrePoMax
//
// Author: Matej Borovinšek
// Contributors:

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using CaeMesh;
using CaeGlobals;
using System.Runtime.Serialization;
using System.Drawing;
using CaeResults;

namespace CaeModel
{
    public partial class DisplacementRotation : IDistribution, IPreviewable
    {
        public bool IsDistributionTypeSupported(DistributionTypeEnum distributionType, out string error)
        {
            error = "";
            if (distributionType == DistributionTypeEnum.Vector)
            {
                for (int dof = 4; dof <= 6; dof++)
                {
                    if (GetDofType(dof) == DOFType.Prescribed)
                    {
                        error = "A vector distribution scales only U1, U2 and U3. Use a scalar distribution for the " +
                                "boundary condition " + Name + " or do not prescribe its rotations.";
                        return false;
                    }
                }
            }
            return true;
        }
        public double[][] GetConstrainValuesForPoints(FeModel model, double[][] points)
        {
            return GetConstrainValuesAndDistancesForPoints(model, points, out _);
        }
        public double[][] GetConstrainValuesAndDistancesForPoints(FeModel model, double[][] points,
                                                                  out double[][] distances)
        {
            double[] constrainValues = GetConstrainValues();
            double[][] values = new double[points.Length][];
            distances = new double[points.Length][];
            //
            if (_distributionName == Distribution.DefaultDistributionName)
            {
                for (int i = 0; i < points.Length; i++) values[i] = constrainValues.ToArray();
            }
            else
            {
                double[][] factors;
                Distribution distribution = model.Distributions[_distributionName];
                distribution.GetMagnitudesAndDistancesForPoints(model, points, out factors, out distances);
                //
                string error;
                if (!IsDistributionTypeSupported(distribution.DistributionType, out error)) throw new CaeException(error);
                //
                int[] directions = GetConstrainedDirections();
                //
                for (int i = 0; i < points.Length; i++)
                {
                    values[i] = new double[directions.Length];
                    for (int j = 0; j < directions.Length; j++)
                    {
                        if (factors[i].Length == 1) values[i][j] = factors[i][0] * constrainValues[j];
                        else if (factors[i].Length == 3)
                        {
                            if (directions[j] <= 3) values[i][j] = factors[i][directions[j] - 1] * constrainValues[j];
                            else values[i][j] = constrainValues[j];
                        }
                        else throw new NotSupportedException();
                    }
                }
            }
            return values;
        }
        // IPreviewable
        public FeResults GetPreview(FeModel model, string resultName, UnitSystem unitSystem)
        {
            FeMesh targetMesh = model.Mesh;
            PartExchangeData allData = new PartExchangeData();
            targetMesh.GetAllNodesAndCells(out allData.Nodes.Ids, out allData.Nodes.Coor, out allData.Cells.Ids,
                                           out allData.Cells.CellNodeIds, out allData.Cells.Types);
            //
            bool addDistances = _distributionName != Distribution.DefaultDistributionName &&
                model.Distributions[_distributionName] is MappedDistribution md &&
                md.InterpolatorType == CloudInterpolatorEnum.ClosestPoint;
            //
            if (RegionType == RegionTypeEnum.ReferencePointName)
                throw new CaeException("A boundary condition applied to a reference point cannot be previewed.");
            int[] regionNodeIds;
            double[][] coor;
            targetMesh.GetRegionNodeIdsAndCoordinates(RegionName, RegionType, out regionNodeIds, out coor);
            Dictionary<int, int> nodeIdArrayId = new Dictionary<int, int>();
            for (int i = 0; i < regionNodeIds.Length; i++) nodeIdArrayId.Add(regionNodeIds[i], i);
            double[][] distances;
            double[][] values = GetConstrainValuesAndDistancesForPoints(model, coor, out distances);
            int[] directions = GetConstrainedDirections();
            bool hasRotations = directions.Any(direction => direction > 3);
            //
            int numOfNodes = allData.Nodes.Coor.Length;
            float[][] dofValues = new float[6][];
            for (int i = 0; i < dofValues.Length; i++) dofValues[i] = new float[numOfNodes];
            float[] displacementsAll = new float[numOfNodes];
            float[] rotationsAll = new float[numOfNodes];
            float[][] distanceValues = new float[3][];
            for (int i = 0; i < distanceValues.Length; i++) distanceValues[i] = new float[numOfNodes];
            float[] distancesAll = new float[numOfNodes];
            //
            Parallel.For(0, numOfNodes, i =>
            {
                int arrayId;
                for (int dof = 0; dof < 6; dof++) dofValues[dof][i] = float.NaN;
                if (nodeIdArrayId.TryGetValue(allData.Nodes.Ids[i], out arrayId))
                {
                    // A fixed degree of freedom does not move
                    for (int j = 0; j < directions.Length; j++)
                    {
                        double value = values[arrayId][j];
                        dofValues[directions[j] - 1][i] = double.IsInfinity(value) ? 0 : (float)value;
                    }
                    displacementsAll[i] = GetMagnitude(dofValues[0][i], dofValues[1][i], dofValues[2][i]);
                    rotationsAll[i] = GetMagnitude(dofValues[3][i], dofValues[4][i], dofValues[5][i]);
                    //
                    if (addDistances)
                    {
                        double[] distance = distances[arrayId];
                        for (int j = 0; j < 3; j++) distanceValues[j][i] = (float)distance[j];
                        distancesAll[i] = (float)Math.Sqrt(distance[0] * distance[0] + distance[1] * distance[1] +
                                                           distance[2] * distance[2]);
                    }
                }
                else
                {
                    displacementsAll[i] = float.NaN;
                    rotationsAll[i] = float.NaN;
                    for (int j = 0; j < 3; j++) distanceValues[j][i] = float.NaN;
                    distancesAll[i] = float.NaN;
                }
            });
            //
            Dictionary<int, int> nodeIdsLookUp = new Dictionary<int, int>();
            for (int i = 0; i < numOfNodes; i++) nodeIdsLookUp.Add(allData.Nodes.Ids[i], i);
            FeResults results = new FeResults(resultName, unitSystem);
            results.SetMesh(targetMesh, nodeIdsLookUp);
            // Prepare field data
            Field field;
            FieldData fieldData = new FieldData(FOFieldNames.Distance);
            fieldData.GlobalIncrementId = 1;
            fieldData.StepType = StepTypeEnum.Static;
            fieldData.Time = 1;
            fieldData.MethodId = 1;
            fieldData.StepId = 1;
            fieldData.StepIncrementId = 1;
            //
            if (addDistances)
            {
                field = new Field(fieldData.Name);
                field.AddComponent(FOComponentNames.All, distancesAll);
                field.AddComponent(FOComponentNames.D1, distanceValues[0]);
                field.AddComponent(FOComponentNames.D2, distanceValues[1]);
                field.AddComponent(FOComponentNames.D3, distanceValues[2]);
                results.AddField(fieldData, field);
            }
            // Displacements
            fieldData = new FieldData(fieldData);
            fieldData.Name = FOFieldNames.PrescribedDisp;
            field = new Field(fieldData.Name);
            field.AddComponent(FOComponentNames.All, displacementsAll);
            field.AddComponent(FOComponentNames.U1, dofValues[0]);
            field.AddComponent(FOComponentNames.U2, dofValues[1]);
            field.AddComponent(FOComponentNames.U3, dofValues[2]);
            results.AddField(fieldData, field);
            // Rotations
            if (hasRotations)
            {
                fieldData = new FieldData(fieldData);
                fieldData.Name = FOFieldNames.PrescribedRot;
                field = new Field(fieldData.Name);
                field.AddComponent(FOComponentNames.All, rotationsAll);
                field.AddComponent(FOComponentNames.UR1, dofValues[3]);
                field.AddComponent(FOComponentNames.UR2, dofValues[4]);
                field.AddComponent(FOComponentNames.UR3, dofValues[5]);
                results.AddField(fieldData, field);
            }
            //
            return results;
        }
        private static float GetMagnitude(float value1, float value2, float value3)
        {
            double sum = 0;
            int count = 0;
            foreach (float value in new float[] { value1, value2, value3 })
            {
                if (float.IsNaN(value)) continue;
                sum += value * value;
                count++;
            }
            if (count == 0) return float.NaN;
            else return (float)Math.Sqrt(sum);
        }
    }
}

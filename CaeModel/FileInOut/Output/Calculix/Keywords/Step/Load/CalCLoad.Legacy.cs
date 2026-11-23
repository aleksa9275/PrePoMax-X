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
using CaeModel;
using CaeMesh;
using CaeGlobals;

namespace FileInOut.Output.Calculix
{
    internal partial class CalCLoad
    {
        public CalCLoad(FeMesh mesh, CLoad load, Dictionary<string, CalReferencePoint> referencePoints,
                        ComplexLoadTypeEnum complexLoadType)
            : this(load, referencePoints, complexLoadType)
        {
            _mesh = mesh;
        }
        partial void ResolveCoordinateSystem(ref string result, ref bool hasContext)
        {
            hasContext = true;
            CoordinateSystem coordinateSystem = null;
            if (_mesh != null) _mesh.CoordinateSystems.TryGetValue(_load.CoordinateSystemName, out coordinateSystem);
            if (coordinateSystem != null) result = GetDataStringInGlobalDirections(coordinateSystem);
            //
        }
        private string GetDataStringInGlobalDirections(CoordinateSystem coordinateSystem)
        {
            int[] nodeIds;
            if (_load.RegionType == RegionTypeEnum.NodeId) nodeIds = new int[] { _load.NodeId };
            else if (_load.RegionType == RegionTypeEnum.NodeSetName) nodeIds = _mesh.NodeSets[_load.RegionName].Labels;
            else if (_load.RegionType == RegionTypeEnum.ReferencePointName)
                nodeIds = new int[] { _referencePoints[_load.RegionName].ReferenceNodeId };
            else throw new NotSupportedException();
            //
            double ratio = GetComplexRatio(_complexLoadType, _load.PhaseDeg.Value);
            double[] localForce = new double[] { _load.F1.Value, _load.F2.Value, _load.F3.Value };
            bool sameAtEveryNode = coordinateSystem.Type == CoordinateSystemTypeEnum.Rectangular &&
                                   _load.RegionType == RegionTypeEnum.NodeSetName;
            int numOfDirections = _load.TwoD ? 2 : 3;
            //
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < nodeIds.Length; i++)
            {
                double[] coor;
                if (_load.RegionType == RegionTypeEnum.ReferencePointName)
                    coor = _mesh.ReferencePoints[_load.RegionName].Coor();
                else coor = _mesh.Nodes[nodeIds[i]].Coor;
                double[] force = coordinateSystem.GetOrientedVectorAtPoint(localForce, coor);
                string nodeName = sameAtEveryNode ? _load.RegionName : nodeIds[i].ToString();
                //
                for (int dir = 1; dir <= numOfDirections; dir++)
                {
                    if (force[dir - 1] == 0) continue;
                    sb.AppendFormat("{0}, {1}, {2}", nodeName, dir, (ratio * force[dir - 1]).ToCalculiX16String());
                    sb.AppendLine();
                }
                if (sameAtEveryNode) break;
            }
            //
            return sb.ToString();
        }
    }
}

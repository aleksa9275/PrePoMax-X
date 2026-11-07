// PrePoMax - Copyright (C) 2016-2026 Matej Borovinšek
//
// Licensed under the terms defined in the LICENSE file located in the root directory of this source code.
//
// Source code: https://gitlab.com/MatejB/PrePoMax
//
// Author: Matej Borovinšek
// Contributors:

using CaeGlobals;
using CaeMesh;
using CaeModel;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading.Tasks;

namespace FileInOut.Output.Calculix
{
    internal partial class CalDefinedTemperature
    {
        public CalDefinedTemperature(FeModel model, DefinedTemperature definedTemperature)
        {
            _definedTemperature = definedTemperature;
            _definedTemperatures = model.GetNodalTemperaturesFromVariableDefinedTemperature(_definedTemperature);
            //
            _regionName = "";
            if (_definedTemperature.RegionType == RegionTypeEnum.NodeSetName)
                _regionName += _definedTemperature.RegionName;
            else if (_definedTemperature.RegionType == RegionTypeEnum.SurfaceName)
                _regionName += model.Mesh.Surfaces[_definedTemperature.RegionName].NodeSetName;
            else if (_definedTemperature.Type == DefinedTemperatureTypeEnum.FromFile &&
                     _definedTemperature.RegionType == RegionTypeEnum.Selection)
            { }
            else throw new NotSupportedException();
            //
            _opType = OpTypeEnum.None;
        }


        partial void ResolveFileData(ref string data)
        {
                string stepData = ", Step=" + _definedTemperature.StepNumber;
                int maxLength = CalculixLineLength - "*Temperature, File=".Length - stepData.Length - OpTypeString().Length;
                data = ", File=" + Tools.GetPathForSolverLine(_definedTemperature.FileName, maxLength, false) + stepData;
        }
    }
}

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
    internal partial class CalTemperatureBC
    {
        public CalTemperatureBC(FeModel model, TemperatureBC temperatureBC, string nodeSetNameOfSurface)
        {
            _temperatureBC = temperatureBC;
            _temperatureBCs = model.GetNodalTemperaturesFromVariableTemperatureBC(temperatureBC);
            _nodeSetNameOfSurface = nodeSetNameOfSurface;
        }


    }
}

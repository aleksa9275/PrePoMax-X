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

namespace FileInOut.Output.Calculix
{
    internal partial class CalNodePrint
    {
        public CalNodePrint(FeModel model, NodalHistoryOutput nodalHistoryOutput, int outputFrequency)
        {
            _nodalHistoryOutput = nodalHistoryOutput;   // set this first
            //
            _regionName = "";
            if (_nodalHistoryOutput.RegionType == CaeGlobals.RegionTypeEnum.NodeSetName)
                _regionName += _nodalHistoryOutput.RegionName;
            else if (_nodalHistoryOutput.RegionType == CaeGlobals.RegionTypeEnum.SurfaceName)
                _regionName += model.Mesh.Surfaces[_nodalHistoryOutput.RegionName].NodeSetName;
            else if (_nodalHistoryOutput.RegionType == CaeGlobals.RegionTypeEnum.Selection)
            { }
            else throw new NotSupportedException();
            //
            _outputFrequency = outputFrequency;
            OutputFrequency = false;
        }
    }
}

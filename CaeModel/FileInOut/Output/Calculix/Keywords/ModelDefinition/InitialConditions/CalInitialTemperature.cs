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
using CaeModel;
using CaeMesh;
using CaeGlobals;

namespace FileInOut.Output.Calculix
{
    [Serializable]
    internal partial class CalInitialTemperature : CalculixKeyword
    {
        // Variables                                                                                                                
        private string _regionName;
        private InitialTemperature _initialTemperature;
        private InitialTemperature[] _initialTemperatures;


        // Properties                                                                                                               
        public bool CanHideData { get { return _initialTemperatures != null; } }


        // Constructor                                                                                                              
        public CalInitialTemperature(InitialTemperature initialTemperature)
        {
            if ((initialTemperature.RegionType != RegionTypeEnum.NodeSetName && initialTemperature.RegionType != RegionTypeEnum.NodeId) ||
                initialTemperature.DistributionName != Distribution.DefaultDistributionName) throw new NotSupportedException();
            _initialTemperature = initialTemperature;
            _regionName = initialTemperature.RegionName;
            _initialTemperatures = initialTemperature.RegionType == RegionTypeEnum.NodeId ? new[] { initialTemperature } : null;
        }

        // Methods                                                                                                                  
        public override string GetKeywordString()
        {
            StringBuilder sb = new StringBuilder();
            sb.AppendLine("** Name: " + _initialTemperature.Name);
            sb.AppendLine("*Initial conditions, Type=Temperature");
            return sb.ToString();
        }
        public override string GetDataString()
        {
            StringBuilder sb = new StringBuilder();
            if (_initialTemperatures == null)
            {
                sb.AppendFormat("{0}, {1}{2}", _regionName, _initialTemperature.Temperature.Value.ToCalculiX16String(),
                                Environment.NewLine);
            }
            else
            {
                InitialTemperature it;
                for (int i = 0; i < _initialTemperatures.Length; i++)
                {
                    it = _initialTemperatures[i];
                    sb.AppendFormat("{0}, {1}{2}", it.NodeId, it.Temperature.Value.ToCalculiX16String(), Environment.NewLine);
                }
            }
            return sb.ToString();
        }
    }
}

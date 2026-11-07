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
    [Serializable]
    internal partial class CalDefinedTemperature : CalculixKeyword
    {
        // Variables                                                                                                                
        private string _regionName;
        private OpTypeEnum _opType;
        private DefinedTemperature _definedTemperature;
        private DefinedTemperature[] _definedTemperatures;



        // Properties                                                                                                               
        public OpTypeEnum OpType { get { return _opType; } set { _opType = value; } }
        public bool CanHideData { get { return _definedTemperatures != null; } }


        // Constructor                                                                                                              
        public CalDefinedTemperature(DefinedTemperature temperature)
        {
            if (temperature.Type != DefinedTemperatureTypeEnum.ByValue || temperature.RegionType != RegionTypeEnum.NodeSetName ||
                temperature.DistributionName != Distribution.DefaultDistributionName) throw new NotSupportedException();
            _definedTemperature = temperature;
            _regionName = temperature.RegionName;
            _opType = OpTypeEnum.None;
        }

        partial void ResolveFileData(ref string data);

        // Methods                                                                                                                  
        public override string GetKeywordString()
        {
            StringBuilder sb = new StringBuilder();
            string fileData = "";
            string amplitude = "";
            if (_definedTemperature.Type == DefinedTemperatureTypeEnum.FromFile)
            {
                string resolved = null;
                ResolveFileData(ref resolved);
                if (resolved == null) throw new NotSupportedException("File temperatures require the full model context.");
                fileData = resolved;
            }
            else
            {
                if (_definedTemperature.AmplitudeName != Amplitude.DefaultAmplitudeName)
                    amplitude = ", Amplitude=" + _definedTemperature.AmplitudeName;
            }
            //
            sb.AppendLine("** Name: " + _definedTemperature.Name);
            sb.AppendFormat("*Temperature{0}{1}{2}{3}", fileData, amplitude, OpTypeString(), Environment.NewLine);
            return sb.ToString();
        }
        public override string GetDataString()
        {
            StringBuilder sb = new StringBuilder();
            if (_definedTemperature.Type == DefinedTemperatureTypeEnum.ByValue)
            {
                if (_definedTemperatures == null)
                {
                    sb.AppendFormat("{0}, {1}{2}", _regionName, _definedTemperature.Temperature.Value.ToCalculiX16String(),
                                    Environment.NewLine);
                }
                else
                {
                    DefinedTemperature dt;
                    for (int i = 0; i < _definedTemperatures.Length; i++)
                    {
                        dt = _definedTemperatures[i];
                        sb.AppendFormat("{0}, {1}{2}", dt.NodeId, dt.Temperature.Value.ToCalculiX16String(), Environment.NewLine);
                    }
                }
            }
            return sb.ToString();
        }
        public string OpTypeString()
        {
            if (_opType == OpTypeEnum.None) return "";
            else if (_opType == OpTypeEnum.New) return ", op=New";
            else if (_opType == OpTypeEnum.Mod) return ", op=Mod";
            else throw new NotSupportedException();
        }
    }
}

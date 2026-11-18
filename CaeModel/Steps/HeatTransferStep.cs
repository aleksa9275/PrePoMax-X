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
using System.Runtime.Serialization;


namespace CaeModel
{
    [Serializable]
    public partial class HeatTransferStep : StaticStep, ISerializable
    {
        // Variables                                                                                                                
        private bool _steadyState;                  //ISerializable
        private double _deltmx;                     //ISerializable


        // Properties                                                                                                               
        public bool SteadyState { get { return _steadyState; } set { _steadyState = value; } }
        public double Deltmx { get { return _deltmx; } set { _deltmx = value; } }


        // Constructors                                                                                                             
        public HeatTransferStep(string name)
            :this(name, true)
        {
           
        }
        public HeatTransferStep(string name, bool addFieldOutputs)
            : base(name, false)
        {
            _steadyState = true;
            _deltmx = double.PositiveInfinity;
            //
            if (addFieldOutputs)
            {
                AddFieldOutput(new NodalFieldOutput("NF-Output-1", NodalFieldVariable.NT | NodalFieldVariable.RFL));
                AddFieldOutput(new ElementFieldOutput("EF-Output-1", ElementFieldVariable.HFL));
            }
        }
        //ISerializable
        public HeatTransferStep(SerializationInfo info, StreamingContext context)
            : base(info, context)
        {
            foreach (SerializationEntry entry in info)
            {
                switch (entry.Name)
                {
                    case "_steadyState":
                        _steadyState = (bool)entry.Value; break;
                    case "_deltmx":
                        _deltmx = (double)entry.Value; break;
                    default:
                        break;
                }
            }
        }


        // Methods                                                                                                                  
        public override bool IsPerturbationSupported()
        {
            return false;
        }
        // ISerialization
        public new void GetObjectData(SerializationInfo info, StreamingContext context)
        {
            // Using typeof() works also for null fields
            base.GetObjectData(info, context);
            //
            info.AddValue("_steadyState", _steadyState, typeof(bool));
            info.AddValue("_deltmx", _deltmx, typeof(double));
        }
    }
}

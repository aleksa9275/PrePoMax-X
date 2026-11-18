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
using CaeMesh;
using System.Runtime.Serialization;
using CaeGlobals;
using DynamicTypeDescriptor;

namespace CaeModel
{
    public abstract partial class Step
    {
        public abstract bool IsBoundaryConditionSupported(BoundaryCondition boundaryCondition);
        public bool AddBoundaryCondition(BoundaryCondition boundaryCondition)
        {
            if (IsBoundaryConditionSupported(boundaryCondition))
            {
                boundaryCondition.Complex = this is SteadyStateDynamicsStep;
                _boundaryConditions.Add(boundaryCondition.Name, boundaryCondition);
                return true;
            }
            return false;
        }
        public bool ReplaceBoundaryCondition(string oldBoundaryConditionName, BoundaryCondition boundaryCondition)
        {
            if (IsBoundaryConditionSupported(boundaryCondition))
            {
                boundaryCondition.Complex = this is SteadyStateDynamicsStep;
                _boundaryConditions.Replace(oldBoundaryConditionName, boundaryCondition.Name, boundaryCondition);
                return true;
            }
            return false;
        }
        public bool IsLoadSupported(Load load)
        {
            return IsLoadTypeSupported(load.GetType());
        }
        public abstract bool IsLoadTypeSupported(Type loadType);
        public bool AddLoad(Load load)
        {
            if (IsLoadSupported(load))
            {
                load.Complex = this is SteadyStateDynamicsStep;
                _loads.Add(load.Name, load);
                return true;
            }
            return false;
        }
        public bool ReplaceLoad(string oldLoadName, Load load)
        {
            if (IsLoadSupported(load))
            {
                load.Complex = this is SteadyStateDynamicsStep;
                _loads.Replace(oldLoadName, load.Name, load);
                return true;
            }
            return false;
        }
        public abstract bool IsDefinedFieldSupported(DefinedField definedField);
        public bool AddDefinedField(DefinedField definedField)
        {
            if (IsDefinedFieldSupported(definedField))
            {
                _definedFields.Add(definedField.Name, definedField);
                return true;
            }
            return false;
        }
    }
}

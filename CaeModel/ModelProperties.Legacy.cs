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
using System.Data;
using System.Linq;
using System.Runtime.Serialization;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using System.Xml.Linq;
using CaeGlobals;
using CaeMesh;
using CaeResults;
using DynamicTypeDescriptor;
using FileInOut.Output.Calculix;
using static System.Collections.Specialized.BitVector32;

namespace CaeModel
{
    public static class ExtensionMethods
    {
        // ModelSpaceEnum
        public static bool IsTwoD(this ModelSpaceEnum modelSpace)
        {
            return (int)modelSpace > 1; // 2, 3 or 4 is 2D
        }
        //
        public static Dictionary<Type, HashSet<Enum>> GetAvailableElementTypes(this ModelSpaceEnum modelSpace,
                                                                               bool allowMixedModel)
        {            
            List<Type> elementTypes = new List<Type>();
            elementTypes.Add(typeof(FeElementTypeLinearTria));
            elementTypes.Add(typeof(FeElementTypeParabolicTria));
            elementTypes.Add(typeof(FeElementTypeLinearQuad));
            elementTypes.Add(typeof(FeElementTypeParabolicQuad));
            elementTypes.Add(typeof(FeElementTypeLinearTetra));
            elementTypes.Add(typeof(FeElementTypeParabolicTetra));
            elementTypes.Add(typeof(FeElementTypeLinearWedge));
            elementTypes.Add(typeof(FeElementTypeParabolicWedge));
            elementTypes.Add(typeof(FeElementTypeLinearHexa));
            elementTypes.Add(typeof(FeElementTypeParabolicHexa));
            //
            int type = 0;
            if (modelSpace == ModelSpaceEnum.ThreeD) type = 1;
            else if (modelSpace == ModelSpaceEnum.PlaneStress) type = 2;
            else if (modelSpace == ModelSpaceEnum.PlaneStrain) type = 3;
            else if (modelSpace == ModelSpaceEnum.Axisymmetric) type = 4;
            HashSet<Enum> elementEnums;
            Dictionary<Type, HashSet<Enum>> elementTypeEnums = new Dictionary<Type, HashSet<Enum>>();
            //
            foreach (Type elementType in elementTypes)
            {
                foreach (var item in Enum.GetValues(elementType))
                {
                    if ((int)item / 10 == type || (allowMixedModel && type == 4 && (int)item / 10 == 2))
                    {
                        if (elementTypeEnums.TryGetValue(elementType, out elementEnums)) elementEnums.Add((Enum)item);
                        else elementTypeEnums.Add(elementType, new HashSet<Enum>() { (Enum)item });
                    }
                }
            }
            //
            return elementTypeEnums;
        }
        //
        public static Dictionary<Type, HashSet<string>> GetUnavailableElementTypeNames(this ModelSpaceEnum modelSpace)
        {
            List<Type> elementTypes = new List<Type>();
            elementTypes.Add(typeof(FeElementTypeLinearTria));
            elementTypes.Add(typeof(FeElementTypeParabolicTria));
            elementTypes.Add(typeof(FeElementTypeLinearQuad));
            elementTypes.Add(typeof(FeElementTypeParabolicQuad));
            elementTypes.Add(typeof(FeElementTypeLinearTetra));
            elementTypes.Add(typeof(FeElementTypeParabolicTetra));
            elementTypes.Add(typeof(FeElementTypeLinearWedge));
            elementTypes.Add(typeof(FeElementTypeParabolicWedge));
            elementTypes.Add(typeof(FeElementTypeLinearHexa));
            elementTypes.Add(typeof(FeElementTypeParabolicHexa));
            //
            int type = 0;
            if (modelSpace == ModelSpaceEnum.ThreeD) type = 1;
            else if (modelSpace == ModelSpaceEnum.PlaneStress) type = 2;
            else if (modelSpace == ModelSpaceEnum.PlaneStrain) type = 3;
            else if (modelSpace == ModelSpaceEnum.Axisymmetric) type = 4;
            HashSet<string> elementEnums;
            Dictionary<Type, HashSet<string>> unavailableElementTypeNames = new Dictionary<Type, HashSet<string>>();
            //
            foreach (Type elementType in elementTypes)
            {
                foreach (var item in Enum.GetValues(elementType))
                {
                    // Remove all elements of the wrong type
                    if ((int)item > 0 && (int)item / 10 != type) 
                    {
                        // For axisymmetric models allow plane stress elements
                        if (type == 4 && (int)item > 0 && (int)item / 10 == 2) continue;
                        //
                        if (unavailableElementTypeNames.TryGetValue(elementType, out elementEnums))
                            elementEnums.Add(item.ToString());
                        else
                            unavailableElementTypeNames.Add(elementType, new HashSet<string>() { item.ToString() });
                    }
                }
            }
            //
            return unavailableElementTypeNames;
        }
    }
}

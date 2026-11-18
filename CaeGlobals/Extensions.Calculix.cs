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
using System.Reflection;

namespace CaeGlobals
{
    public static partial class ExtensionMethods
    {
        public static string ToCalculiX16String(this double value, bool enforceSeparator = false)
        {
            string result = value.ToString().ToUpper();
            if (result.Length > 16) result = value.ToString("E8");
            else if (enforceSeparator && !result.Contains("."))
            {
                int location = result.IndexOf("E");
                // The first letter must not be E so > 0
                if (location > 0) result = result.Insert(location, ".");
                else result += ".";
            }
            return result;
        }
        public static string GetNextNumberedKey(this HashSet<string> hashSet, string key,
                                                string postFix = "", string separator = "-")
        {
            int n = 0;
            string newKey;
            while (true)
            {
                n++;
                newKey = key + separator + n + postFix;
                if (!hashSet.Contains(newKey)) break;
            }
            return newKey;
        }
        public static bool IsGeometryBased(this vtkSelectBy selectBy)
        {
            return selectBy == vtkSelectBy.Geometry ||
                   selectBy == vtkSelectBy.GeometryVertex ||
                   selectBy == vtkSelectBy.GeometryEdge ||
                   selectBy == vtkSelectBy.GeometrySurface ||
                   selectBy == vtkSelectBy.GeometryEdgeAngle ||
                   selectBy == vtkSelectBy.GeometrySurfaceAngle ||
                   selectBy == vtkSelectBy.GeometryPart;
        }
        public static string GetDisplayedName<T>(this T enumerationValue) where T : struct
        {
            Type type = enumerationValue.GetType();
            if (!type.IsEnum)
            {
                throw new ArgumentException("EnumerationValue must be of Enum type", "enumerationValue");
            }

            //Tries to find a DescriptionAttribute for a potential friendly name
            //for the enum
            MemberInfo[] memberInfo = type.GetMember(enumerationValue.ToString());
            if (memberInfo != null && memberInfo.Length > 0)
            {
                object[] attrs = memberInfo[0].GetCustomAttributes(typeof(DynamicTypeDescriptor.StandardValueAttribute), false);

                if (attrs != null && attrs.Length > 0)
                {
                    //Pull out the description value
                    return ((DynamicTypeDescriptor.StandardValueAttribute)attrs[0]).DisplayName;
                }
            }
            //If we have no description attribute, just return the ToString of the enum
            return enumerationValue.ToString();
        }
    }
}

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
using CaeMesh;

namespace FileInOut.Input
{
    [Serializable]
    static public partial class InpFileReader
    {
        private delegate FeElement ElementReader(ref int lineId, string[] lines, string[] splitter);
        // Keep the supported element type names and their readers in one place so that exact and fallback matching
        // cannot get out of sync with element creation.
        private static readonly Dictionary<string, ElementReader> _elementReaders =
            new Dictionary<string, ElementReader>(StringComparer.Ordinal)
            {
                // Linear beam
                { "T3D2", GetLinearBeamElement },
                // Linear triangle
                { "S3", GetLinearTriangleElement },
                { "S3R", GetLinearTriangleElement },
                { "M3D3", GetLinearTriangleElement },
                { "CPS3", GetLinearTriangleElement },
                { "CPE3", GetLinearTriangleElement },
                { "CAX3", GetLinearTriangleElement },
                // Linear quadrilateral
                { "S4", GetLinearQuadrilateralElement },
                { "S4R", GetLinearQuadrilateralElement },
                { "M3D4", GetLinearQuadrilateralElement },
                { "M3D4R", GetLinearQuadrilateralElement },
                { "CPS4", GetLinearQuadrilateralElement },
                { "CPS4R", GetLinearQuadrilateralElement },
                { "CPE4", GetLinearQuadrilateralElement },
                { "CPE4R", GetLinearQuadrilateralElement },
                { "CAX4", GetLinearQuadrilateralElement },
                { "CAX4R", GetLinearQuadrilateralElement },
                // Linear tetrahedron
                { "C3D4", GetLinearTetraElement },
                { "DC3D4", GetLinearTetraElement },
                // Linear pyramid
                { "C3D5", GetLinearPyramidElement },
                { "C3D5I", GetLinearPyramidElement },
                { "C3D5R", GetLinearPyramidElement },
                // Linear wedge
                { "C3D6", GetLinearWedgeElement },
                { "DC3D6", GetLinearWedgeElement },
                // Linear hexahedron
                { "C3D8", GetLinearHexaElement },
                { "C3D8R", GetLinearHexaElement },
                { "C3D8I", GetLinearHexaElement },
                { "DC3D8", GetLinearHexaElement },
                // Parabolic beam
                { "T3D3", GetParabolicBeamElement },
                // Parabolic triangle
                { "S6", GetParabolicTriangleElement },
                { "M3D6", GetParabolicTriangleElement },
                { "CPS6", GetParabolicTriangleElement },
                { "CPE6", GetParabolicTriangleElement },
                { "CAX6", GetParabolicTriangleElement },
                // Parabolic quadrilateral
                { "S8", GetParabolicQuadrilateralElement },
                { "S8R", GetParabolicQuadrilateralElement },
                { "M3D8", GetParabolicQuadrilateralElement },
                { "M3D8R", GetParabolicQuadrilateralElement },
                { "CPS8", GetParabolicQuadrilateralElement },
                { "CPS8R", GetParabolicQuadrilateralElement },
                { "CPE8", GetParabolicQuadrilateralElement },
                { "CPE8R", GetParabolicQuadrilateralElement },
                { "CAX8", GetParabolicQuadrilateralElement },
                { "CAX8R", GetParabolicQuadrilateralElement },
                // Parabolic tetrahedron
                { "C3D10", GetParabolicTetraElement },
                { "C3D10T", GetParabolicTetraElement },
                { "DC3D10", GetParabolicTetraElement },
                // Parabolic wedge
                { "C3D15", GetParabolicWedgeElement },
                { "DC3D15", GetParabolicWedgeElement },
                // Parabolic pyramid
                { "C3D13", GetParabolicPyramidElement },
                { "C3D13I", GetParabolicPyramidElement },
                { "C3D13R", GetParabolicPyramidElement },
                // Parabolic hexahedron
                { "C3D20", GetParabolicHexaElement },
                { "C3D20R", GetParabolicHexaElement },
                { "DC3D20", GetParabolicHexaElement }
            };
        private static List<string> _errors;
        private static List<string> _warnings;
        private static string[] _splitterComma = new string[] { "," };
        private static string[] _splitterEqual = new string[] { "=" };
        private static string[] _splitter = new string[] { " ", ",", "\t" };

        private static Action<string> WriteDataToOutputStatic;

        static public List<string> Errors { get { return _errors; } }
        static public List<string> Warnings { get { return _warnings; } }

        private static string[][] GetDataSets(string[] lines)
        {
            List<string> dataSet = null;
            List<string[]> dataSets = new List<string[]>();
            //
            for (int i = 0; i < lines.Length; i++)
            {
                if (lines[i].Length == 0) continue;                                             // empty line
                if (lines[i].Length > 1 && lines[i][0] == '*' && lines[i][1] == '*') continue;  // comment line
                //
                if (lines[i].Length > 1 && lines[i][0] == '*' && lines[i][1] != '*')            // keyword line
                {
                    // First keyword
                    if (dataSet != null) dataSets.Add(dataSet.ToArray());
                    dataSet = new List<string>();
                }
                if (dataSet != null) dataSet.Add(lines[i]);                                     // other lines
            }
            // Add last data set
            if (dataSet != null) dataSets.Add(dataSet.ToArray());
            //
            return dataSets.ToArray();
        }

        private static void AddNodeCoordinates(string[] lines, Dictionary<int, FeNode> nodes,
                                               out string nodeSetName, out HashSet<int> ids)
        {
            //*NODE, NSET = Nall
            int id;
            ids = new HashSet<int>();
            FeNode node;
            nodeSetName = null;
            string[] record1;
            string[] record2;
            string[] splitter = new string[] { " ", ",", "\t" };
            // Line 0 - keyword
            record1 = lines[0].Split(_splitterComma, StringSplitOptions.RemoveEmptyEntries);
            foreach (var rec in record1)
            {
                record2 = rec.Split(_splitterEqual, StringSplitOptions.RemoveEmptyEntries);
                if (record2.Length == 2)
                {
                    if (record2[0].Trim().ToUpper() == "NSET") nodeSetName = record2[1].Trim();
                }
            }
            // Lines from 1 to end
            for (int i = 1; i < lines.Length; i++)
            {
                if (lines[i].StartsWith("*")) continue;
                //
                record1 = lines[i].Split(splitter, StringSplitOptions.RemoveEmptyEntries);
                //
                id = int.Parse(record1[0]);
                node = new FeNode();
                node.Id = id;
                node.X = double.Parse(record1[1]);
                node.Y = double.Parse(record1[2]);
                if (record1.Length == 4) node.Z = double.Parse(record1[3]);
                //
                ids.Add(id);
                nodes.Add(id, node);
            }
        }

        private static void AddElements(string[] lines, ref Dictionary<int, FeElement> elements,
                                        ref List<InpElementSet> inpElementTypeSets)
        {
            try
            {
                FeElement element;
                //
                string elementType = null;
                string elementSetName = null;
                string[] record1;
                string[] record2;
                // *Element, type=C3D4, ELSET=PART1
                record1 = lines[0].Split(_splitterComma, StringSplitOptions.RemoveEmptyEntries);
                //
                foreach (var rec in record1)
                {
                    record2 = rec.Split(_splitterEqual, StringSplitOptions.RemoveEmptyEntries);
                    if (record2.Length == 2)
                    {
                        if (record2[0].Trim().ToUpper() == "TYPE") elementType = record2[1].Trim().ToUpper();
                        else if (record2[0].Trim().ToUpper() == "ELSET") elementSetName = record2[1].Trim();
                    }
                }
                if (elementType == null) return;
                // Use an exact match whenever possible. For unsupported formulations, use the longest supported
                // prefix so, for example, C3D20RH resolves to C3D20R rather than C3D20.
                string originalElementType = elementType;
                ElementReader elementReader;
                if (!TryGetElementReader(elementType, out elementType, out elementReader))
                    throw new Exception("The element type '" + originalElementType + "' is not supported.");
                // Notify once per *ELEMENT block while allowing the compatible element topology to be imported.
                if (elementType != originalElementType)
                {
                    AddWarning("The element type '" + originalElementType + "' is not directly supported and was imported as '" +
                               elementType + "'. Formulation-specific behavior may be lost.");
                }
                //
                List<int> elementIds = new List<int>();
                // Line 0 is the line with the keyword
                for (int i = 1; i < lines.Length; i++)
                {
                    if (lines[i].StartsWith("*")) continue;
                    //
                    element = elementReader(ref i, lines, _splitter);
                    elementIds.Add(element.Id);
                    elements.Add(element.Id, element);
                }
                // Find element set
                InpElementSet inpSet = null;
                foreach (var entry in inpElementTypeSets)
                {
                    if (entry.Name == elementSetName)   // both names can be null - must be like this for sets without names
                    {
                        inpSet = entry;
                        break;
                    }
                }
                // Create new set
                if (inpSet == null)
                {
                    inpSet = new InpElementSet(elementSetName, new HashSet<string>(), new HashSet<int>());
                    inpElementTypeSets.Add(inpSet);
                }
                // Add type and labels
                inpSet.InpElementTypeNames.Add(elementType);
                inpSet.ElementLabels.UnionWith(elementIds);
            }
            catch (Exception ex)
            {
                AddError(ex.Message);
            }
        }
        private static bool TryGetElementReader(string elementType, out string supportedElementType,
                                                out ElementReader elementReader)
        {
            supportedElementType = elementType;
            if (_elementReaders.TryGetValue(elementType, out elementReader)) return true;
            // Find the most specific supported prefix. Dictionary enumeration order is not relied upon.
            supportedElementType = null;
            elementReader = null;
            foreach (var entry in _elementReaders)
            {
                if (elementType.StartsWith(entry.Key, StringComparison.Ordinal) &&
                    (supportedElementType == null || entry.Key.Length > supportedElementType.Length))
                {
                    supportedElementType = entry.Key;
                    elementReader = entry.Value;
                }
            }
            return supportedElementType != null;
        }

        private static void GetNodeOrElementSetData(string keywordName, string[] lines,
                                                    Func<string, string, int[]> resolveSet, out string name, out int[] ids)
        {
            name = null;
            ids = null;
            //
            try
            {
                bool generate = false;
                string[] record1;
                string[] record2;
                // *NSET,NSET=SET1,GENERATE
                record1 = lines[0].Split(_splitterComma, StringSplitOptions.RemoveEmptyEntries);
                //
                foreach (var rec in record1)
                {
                    record2 = rec.Split(_splitterEqual, StringSplitOptions.RemoveEmptyEntries);
                    if (record2.Length == 1)
                    {
                        if (record2[0].Trim().ToUpper() == "GENERATE") generate = true;
                    }
                    else if (record2.Length == 2)
                    {
                        if (record2[0].Trim().ToUpper() == keywordName.ToUpper()) name = record2[1].Trim();
                    }
                }
                if (name == null) WriteDataToOutputStatic("There is a set name missing in the line: " + lines[0]);
                //
                List<int> setIds = new List<int>();
                if (generate)   // can be written in more than one line
                {
                    // Line 0 is the line with the keyword
                    for (int i = 1; i < lines.Length; i++)
                    {
                        record1 = lines[i].Split(_splitterComma, StringSplitOptions.RemoveEmptyEntries);
                        //
                        if (record1.Length <= 3)
                        {
                            int start = int.Parse(record1[0]);
                            int end = int.Parse(record1[1]);
                            int step = 1;
                            if (record1.Length == 3) step = int.Parse(record1[2]);

                            for (int j = start; j <= end; j += step) setIds.Add(j);
                        }
                        else throw new CaeGlobals.CaeException("When node set is defined using GENERATE parameter at most three node ids are expected.");
                    }
                    ids = setIds.ToArray();
                }
                else
                {
                    int intId;
                    string setName;
                    //
                    for (int i = 1; i < lines.Length; i++)
                    {
                        record1 = lines[i].Split(_splitter, StringSplitOptions.RemoveEmptyEntries);
                        foreach (string id in record1)
                        {
                            if (int.TryParse(id, out intId)) setIds.Add(intId);
                            else
                            {
                                setName = id;
                                int[] resolvedIds = resolveSet(keywordName, setName);
                                if (resolvedIds != null) setIds.AddRange(resolvedIds);
                                else WriteDataToOutputStatic("The set named '" + setName + "' was not found.");
                            }
                        }
                    }
                    ids = setIds.ToArray();
                    Array.Sort(ids);
                }
            }
            catch (Exception ex)
            {
                WriteDataToOutputStatic(ex.Message);
            }
        }

        //  LINEAR ELEMENTS                                                                                                         
        private static LinearBeamElement GetLinearBeamElement(ref int lineId, string[] lines, string[] splitter)
        {
            // 1, 598, 1368
            int id;
            int[] nodeIds;
            GetElementIdAndNodeIds(2, ref lineId, lines, splitter, out id, out nodeIds);
            //
            return new LinearBeamElement(id, nodeIds);
        }
        private static LinearTriangleElement GetLinearTriangleElement(ref int lineId, string[] lines, string[] splitter)
        {
            // 1, 598, 1368, 1306
            int id;
            int[] nodeIds;
            GetElementIdAndNodeIds(3, ref lineId, lines, splitter, out id, out nodeIds);
            //
            return new LinearTriangleElement(id, nodeIds);
        }
        private static LinearQuadrilateralElement GetLinearQuadrilateralElement(ref int lineId, string[] lines, string[] splitter)
        {
            // 1, 598, 1368, 1306, 16
            int id;
            int[] nodeIds;
            GetElementIdAndNodeIds(4, ref lineId, lines, splitter, out id, out nodeIds);
            //
            return new LinearQuadrilateralElement(id, nodeIds);
        }
        private static LinearTetraElement GetLinearTetraElement(ref int lineId, string[] lines, string[] splitter)
        {
            // 1, 598, 1368, 1306, 1291
            int id;
            int[] nodeIds;
            GetElementIdAndNodeIds(4, ref lineId, lines, splitter, out id, out nodeIds);
            //
            return new LinearTetraElement(id, nodeIds);
        }
        private static LinearPyramidElement GetLinearPyramidElement(ref int lineId, string[] lines, string[] splitter)
        {
            // 1, 598, 1368, 1306, 1291, 3
            int id;
            int[] nodeIds;
            GetElementIdAndNodeIds(5, ref lineId, lines, splitter, out id, out nodeIds);
            //
            return new LinearPyramidElement(id, nodeIds);
        }
        private static LinearWedgeElement GetLinearWedgeElement(ref int lineId, string[] lines, string[] splitter)
        {
            // 1,  132,  133,  495,  646,  647, 1009
            int id;
            int[] nodeIds;
            GetElementIdAndNodeIds(6, ref lineId, lines, splitter, out id, out nodeIds);
            //
            return new LinearWedgeElement(id, nodeIds);
        }
        private static LinearHexaElement GetLinearHexaElement(ref int lineId, string[] lines, string[] splitter)
        {
            // 1, 598, 1368, 1306, 1291, 3, 4, 5, 6
            int id;
            int[] nodeIds;
            GetElementIdAndNodeIds(8, ref lineId, lines, splitter, out id, out nodeIds);
            //
            return new LinearHexaElement(id, nodeIds);
        }


        //  PARABOLIC ELEMENTS                                                                                                      
        private static ParabolicBeamElement GetParabolicBeamElement(ref int lineId, string[] lines, string[] splitter)
        {
            // *ELEMENT, TYPE = T3D3
            // 1, 598, 1368, 1306
            int id;
            int[] nodeIds;
            GetElementIdAndNodeIds(3, ref lineId, lines, splitter, out id, out nodeIds);
            //
            return new ParabolicBeamElement(id, nodeIds);
        }
        private static ParabolicTriangleElement GetParabolicTriangleElement(ref int lineId, string[] lines, string[] splitter)
        {
            // *ELEMENT, TYPE = S6
            // 1, 598, 1368, 1306, 1291, 15 ,16
            int id;
            int[] nodeIds;
            GetElementIdAndNodeIds(6, ref lineId, lines, splitter, out id, out nodeIds);
            //
            return new ParabolicTriangleElement(id, nodeIds);
        }
        private static ParabolicQuadrilateralElement GetParabolicQuadrilateralElement(ref int lineId, string[] lines,
                                                                                      string[] splitter)
        {
            // *ELEMENT, TYPE = S8
            // 1, 5518, 5519, 4794, 5898, 19815, 19819, 19817, 19816
            int id;
            int[] nodeIds;
            GetElementIdAndNodeIds(8, ref lineId, lines, splitter, out id, out nodeIds);
            //
            return new ParabolicQuadrilateralElement(id, nodeIds);
        }
        private static ParabolicTetraElement GetParabolicTetraElement(ref int lineId, string[] lines, string[] splitter)
        {
            // *ELEMENT, TYPE = C3D10
            // 1,1,10,47,19,37,57,78,72,9,45
            int id;
            int[] nodeIds;
            GetElementIdAndNodeIds(10, ref lineId, lines, splitter, out id, out nodeIds);
            //
            return new ParabolicTetraElement(id, nodeIds);
        }
        private static ParabolicPyramidElement GetParabolicPyramidElement(ref int lineId, string[] lines, string[] splitter)
        {
            // *ELEMENT, TYPE = C3D13
            // 1,1,10,47,19,37,57,78,72,9,45,
            // 46,20,56
            int id;
            int[] gmshNodeIds;
            GetElementIdAndNodeIds(13, ref lineId, lines, splitter, out id, out gmshNodeIds);
            //
            int[] nodeIds = new int[gmshNodeIds.Length];
            Array.Copy(gmshNodeIds, nodeIds, 6);
            //
            nodeIds[8] = gmshNodeIds[6];
            nodeIds[9] = gmshNodeIds[7];
            nodeIds[6] = gmshNodeIds[8];
            //
            nodeIds[10] = gmshNodeIds[9];
            nodeIds[7] = gmshNodeIds[10];
            nodeIds[11] = gmshNodeIds[11];
            nodeIds[12] = gmshNodeIds[12];
            //
            return new ParabolicPyramidElement(id, nodeIds);
        }
        private static ParabolicWedgeElement GetParabolicWedgeElement(ref int lineId, string[] lines, string[] splitter)
        {
            // *ELEMENT, TYPE = C3D15
            // 1,1,10,47,19,37,57,78,72,9,45,
            // 46,20,56,76,77
            int id;
            int[] nodeIds;
            GetElementIdAndNodeIds(15, ref lineId, lines, splitter, out id, out nodeIds);
            //
            return new ParabolicWedgeElement(id, nodeIds);
        }
        private static ParabolicHexaElement GetParabolicHexaElement(ref int lineId, string[] lines, string[] splitter)
        {
            // *ELEMENT, TYPE = C3D20R
            // 1,1,10,47,19,37,57,78,72,9,45,
            // 46,20,56,76,77,73,38,55,75,70
            int id;
            int[] nodeIds;
            GetElementIdAndNodeIds(20, ref lineId, lines, splitter, out id, out nodeIds);
            //
            return new ParabolicHexaElement(id, nodeIds);
        }
        private static void GetElementIdAndNodeIds(int numOfNodes, ref int lineId, string[] lines,
                                                   string[] splitter, out int elementId, out int[] nodeIds)
        {
            int numOfRecords = numOfNodes + 1;
            string[] splitStrings = new string[numOfRecords];
            //
            int count = 0;
            string[] record;
            while (count < numOfRecords)
            {
                record = lines[lineId].Split(splitter, StringSplitOptions.RemoveEmptyEntries);
                //
                for (int i = 0; i < record.Length; i++)
                {
                    splitStrings[count++] = record[i];
                }
                lineId++;
            }
            lineId--;   // set the lineId to the last line
            // Element id
            elementId = int.Parse(splitStrings[0]);
            // Node ids
            nodeIds = new int[numOfNodes];
            for (int i = 1; i < splitStrings.Length; i++) nodeIds[i - 1] = int.Parse(splitStrings[i]);
        }
        //

        private static void AddError(string error)
        {
            Errors.Add(error);
            if (WriteDataToOutputStatic != null) WriteDataToOutputStatic(error);
        }
        private static void AddWarning(string warning)
        {
            Warnings.Add(warning);
            if (WriteDataToOutputStatic != null) WriteDataToOutputStatic(warning);
        }
    }
}

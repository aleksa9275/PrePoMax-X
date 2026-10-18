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
using System.IO;
using CaeMesh;
using CaeGlobals;
using System.ComponentModel;
using System.Globalization;

namespace CaeResults
{
    public static partial class FrdFileReader
    {
        static public void ScaleAxisymmetricSegmentFields(FeResults results)
        {
            foreach (var fieldName in _axisymmetricSegmentFieldNames)
                results.ScaleFieldValues(fieldName, _axisymmetricSegmentsPerRevolution);
        }
        static public void ScaleAxisymmetricModesToRevolution(FeResults results)
        {
            float factor = (float)(1 / Math.Sqrt(_axisymmetricSegmentsPerRevolution));
            foreach (var fieldName in _axisymmetricModeFieldNames)
                results.ScaleFieldValues(fieldName, factor, IsAxisymmetricMode);
            foreach (var fieldName in _axisymmetricModeEnergyFieldNames)
                results.ScaleFieldValues(fieldName, factor * factor, IsAxisymmetricMode);
        }
        static private bool IsAxisymmetricMode(FieldData fieldData)
        {
            if (fieldData.StepType == StepTypeEnum.Buckling) return fieldData.Time != 0;
            return _massNormalizedModeStepTypes.Contains(fieldData.StepType);
        }
        static public FeResults Read(string fileName)
        {
            if (fileName != null && File.Exists(fileName))
            {
                if (fileName.ToUpper().Contains("RESULTSFORLASTITERATIONS.FRD"))
                {
                    CompareIntArray comparer = new CompareIntArray();
                    _bemaNodeIds = new HashSet<int[]>(comparer);
                }
                //
                List<FrdDataSet> dataSets = GetDataSets(fileName);
                if (dataSets == null) return null;
                //
                string setID;
                Dictionary<int, FeNode> nodes = null;
                Dictionary<int, int> nodeIdsLookUp = null;
                Dictionary<int, FeElement> elements = null;
                HashSet<int> gapMaterialIds = null;
                HashSet<int> springMaterialIds = null;
                HashSet<int> massMaterialIds = null;
                Dictionary<int, string> materialIdMaterialName = null;
                Dictionary<int, List<int>> materialIdElementIds = null;
                //
                FeResults result = new FeResults(fileName, null);
                Field field;
                FieldData fieldData = null;
                FieldData prevFieldData = null;
                //
                bool constantWidth = true;
                //
                foreach (FrdDataSet dataSet in dataSets)
                {
                    setID = dataSet.Lines[0];
                    if (setID.StartsWith("    1C", StringComparison.Ordinal))  // Data
                    {
                        result.HashName = GetHashName(dataSet.Lines);
                        result.ModelSpace = GetModelSpace(dataSet.Lines);
                        result.DateTime = GetDateTime(dataSet.Lines);
                        result.UnitSystem = GetUnitSystem(dataSet.Lines); // calls SetConverterUnits on the UnitSystem
                        GetMaterialIdsAndNames(dataSet.Lines, out materialIdMaterialName, out gapMaterialIds,
                                               out springMaterialIds, out massMaterialIds);
                    }
                    else if (setID.StartsWith("    2C", StringComparison.Ordinal)) // Nodes
                    {
                        if (dataSet.IsBinary) nodes = GetNodesBinary(dataSet, out nodeIdsLookUp);
                        else
                        {
                            constantWidth = IsConstantWidth(dataSet.Lines);
                            nodes = GetNodes(dataSet.Lines, constantWidth, out nodeIdsLookUp);
                        }
                    }
                    else if (setID.StartsWith("    3C", StringComparison.Ordinal)) // Elements
                    {
                        if (dataSet.IsBinary)
                            elements = GetElementsBinary(dataSet, gapMaterialIds, springMaterialIds, massMaterialIds,
                                                         out materialIdElementIds);
                        else
                            elements = GetElements(dataSet.Lines, gapMaterialIds, springMaterialIds, massMaterialIds,
                                                   out materialIdElementIds);
                    }
                    else if (setID.StartsWith("    1PSTEP", StringComparison.Ordinal)) // Fields
                    {
                        GetField(dataSet, constantWidth, prevFieldData, nodeIdsLookUp, out fieldData, out field);
                        result.AddField(fieldData, field);
                        prevFieldData = fieldData.DeepClone();
                    }
                }
                //
                result.Preprocess();
                //
                if (nodes != null && elements != null)
                {
                    RemoveErrorElements(nodes, ref elements);
                    //
                    FeMesh mesh = new FeMesh(nodes, elements, MeshRepresentation.Results);
                    mesh.ResetPartsColor();
                    result.SetMesh(mesh, nodeIdsLookUp);
                    // Material element sets
                    FeElementSet elementSet;
                    if (materialIdMaterialName != null && materialIdElementIds != null)
                    {
                        foreach (var entry in materialIdMaterialName)
                        {
                            if (materialIdElementIds.ContainsKey(entry.Key))
                            {
                                elementSet = new FeElementSet(entry.Value, materialIdElementIds[entry.Key].ToArray());
                                result.Mesh.AddElementSet(elementSet);
                            }
                        }
                    }
                    // Gap element sets
                    BasePart[] modifiedParts;
                    BasePart[] newParts;
                    List<string> partNamesToRemove = new List<string>();
                    string oldPartName;
                    if (gapMaterialIds.Count > 0 && materialIdElementIds.ContainsKey(_gapMaterialId))
                    {
                        elementSet = new FeElementSet(_gapMaterialName, materialIdElementIds[_gapMaterialId].ToArray());
                        result.Mesh.AddElementSet(elementSet);
                        result.Mesh.CreatePartsFromElementSets(new string[] { elementSet.Name }, out modifiedParts, out newParts);
                        // Rename parts
                        if (newParts.Count() == 1)
                        {
                            oldPartName = newParts[0].Name;
                            newParts[0].Name = "Gap_elements";
                            result.Mesh.Parts.Replace(oldPartName, newParts[0].Name, newParts[0]);
                        }
                        // Get part names to remove
                        foreach (var part in modifiedParts)
                        {
                            if (part.Labels.Length == 0) partNamesToRemove.Add(part.Name);
                        }
                        // Remove parts
                        if (partNamesToRemove.Count > 0) result.Mesh.RemoveParts(partNamesToRemove.ToArray(), out _, false);
                    }
                    // Spring element sets - *SPRING elements are not written into the frd file - this is always empty
                    if (springMaterialIds.Count > 0 && materialIdElementIds.ContainsKey(_springMaterialId))
                    {
                        elementSet = new FeElementSet(_springMaterialName, materialIdElementIds[_springMaterialId].ToArray());
                        result.Mesh.AddElementSet(elementSet);
                    }
                    // Mass element sets - *MASS elements are not written into the frd file - this is always empty
                    if (massMaterialIds.Count > 0 && materialIdElementIds.ContainsKey(_massMaterialId))
                    {
                        elementSet = new FeElementSet(_massMaterialName, materialIdElementIds[_massMaterialId].ToArray());
                        result.Mesh.AddElementSet(elementSet);
                    }
                    // Recognize the face and the edge types from the mesh
                    result.Mesh.DetectFaceTypes();
                    result.Mesh.DetectEdgeTypes();
                    //
                    return result;
                }
            }
            //
            return null;
        }
        static private UnitSystem GetUnitSystem(string[] lines)
        {
            string[] tmp;
            UnitSystemType unitSystemType = UnitSystemType.Undefined;
            //
            for (int i = 0; i < lines.Length; i++)
            {
                if (lines[i].ToUpper().Contains("UNIT SYSTEM"))
                {
                    tmp = lines[i].Split(new string[] { "Unit system:" }, StringSplitOptions.RemoveEmptyEntries);
                    if (tmp.Length == 2) Enum.TryParse(tmp[1], out unitSystemType);
                }
            }
            //
            return new UnitSystem(unitSystemType);
        }
    }
}

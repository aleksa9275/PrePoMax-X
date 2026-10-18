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
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using System.Xml.Linq;

namespace CaeResults
{
    [Serializable]
    public static partial class DatFileReader
    {
        private static readonly string[] _spaceSplitter = new string[] { " " };
        private static readonly string[] _commaSplitter = new string[] { "," };
        private static readonly string[] _underscoreSplitter = new string[] { "_" };
        private static readonly string[] _parenthesesSplitter = new string[] { "(", ")" };
        private static readonly string[] _componentsSplitter = new string[] { " ", "," };
        private static readonly string[] _dataSplitter = new string[] { " ", "for set", "and time" };
        private static readonly string[] _signSplitter = new string[] { "-", "+" };
        private static readonly string[] _atSplitter = new string[] { "@@@" };
        private static readonly string _stepKey = "S T E P";
        private static readonly string _incrementKey = "INCREMENT";
        private static readonly string _stepNumberKey = "STEP_";
        private static readonly string _participationFactorsForFrequencyKey =
            "P A R T I C I P A T I O N   F A C T O R S   F O R   F R E Q U E N C Y";
        private const string _eigenvalueOutputKey = "E I G E N V A L U E   O U T P U T";
        private const string _participationFactorsKey = "P A R T I C I P A T I O N   F A C T O R S";
        
        private const string _effectiveModalMassKey = "E F F E C T I V E   M O D A L   M A S S";
        private const string _totalEffectiveMassKey = "T O T A L   E F F E C T I V E   M A S S";
        private const string _eigenvalueNumberKey = "E I G E N V A L U E    N U M B E R";
        private const string _bucklingFactorKey = "B U C K L I N G   F A C T O R   O U T P U T";
        // Complex frequency
        private const string _participationFactorsForModeKey = "P A R T I C I P A T I O N   F A C T O R S   F O R   M O D E";
        private const string _modalAssuranceCriteriumKey = "Modal Assurance Criterium";
        private const string _eigenmodeTurningDirectionKey = "E I G E N M O D E   T U R N I N G   D I R E C T I O N";
        private static readonly Dictionary<string, string> nameKeyMap = new Dictionary<string, string>()
        {
            // Nodal                                                                
            { HOFieldNames.Displacements, HOFieldNames.Displacements.Replace('_', ' ')},
            { HOFieldNames.Velocities, HOFieldNames.Velocities.Replace('_', ' ')},
            { HOFieldNames.Forces, HOFieldNames.Forces.Replace('_', ' ')},
            { HOFieldNames.TotalForce, HOFieldNames.TotalForce.Replace('_', ' ')},
            { HOFieldNames.Stresses, HOFieldNames.Stresses.Replace('_', ' ')},
            { HOFieldNames.Strains, HOFieldNames.Strains.Replace('_', ' ')},
            { HOFieldNames.MechanicalStrains, HOFieldNames.MechanicalStrains.Replace('_', ' ')},
            { HOFieldNames.EquivalentPlasticStrains, HOFieldNames.EquivalentPlasticStrains.Replace('_', ' ')},
            { HOFieldNames.InternalEnergyDensity, HOFieldNames.InternalEnergyDensity.Replace('_', ' ')},
            // Thermal
            { HOFieldNames.Temperatures, HOFieldNames.Temperatures.Replace('_', ' ')},
            { HOFieldNames.HeatGeneration, HOFieldNames.HeatGeneration.Replace('_', ' ')},
            { HOFieldNames.TotalHeatGeneration, HOFieldNames.TotalHeatGeneration.Replace('_', ' ')},
            // Frequency                                                            
            { _stepKey, _stepKey},
            { _incrementKey, _incrementKey},
            { _eigenvalueOutputKey, _eigenvalueOutputKey},
            { _participationFactorsKey, _participationFactorsKey},
            { _effectiveModalMassKey, _effectiveModalMassKey},
            { _totalEffectiveMassKey, _totalEffectiveMassKey},
            { _eigenvalueNumberKey, _eigenvalueNumberKey},
            { _bucklingFactorKey, _bucklingFactorKey},
            // Steady state                                                         
            { _participationFactorsForFrequencyKey, _participationFactorsForFrequencyKey},
            // Complex frequency                                                    
            { _participationFactorsForModeKey, _participationFactorsForModeKey},
            { _modalAssuranceCriteriumKey, _modalAssuranceCriteriumKey},
            { _eigenmodeTurningDirectionKey, _eigenmodeTurningDirectionKey},
            // Contact                                                              
            { HOFieldNames.RelativeContactDisplacement, HOFieldNames.RelativeContactDisplacement.Replace('_', ' ')},
            { HOFieldNames.ContactStress, HOFieldNames.ContactStress.Replace('_', ' ')},
            { HOFieldNames.ContactPrintEnergy, HOFieldNames.ContactPrintEnergy.Replace('_', ' ')},
            { HOFieldNames.ContactSpringEnergy, HOFieldNames.ContactSpringEnergy.Replace('_', ' ')},
            { HOFieldNames.TotalNumberOfContactElements, HOFieldNames.TotalNumberOfContactElements.Replace('_', ' ')},
            // Set                                                                  
            { HOFieldNames.StatisticsForSlaveSet, HOFieldNames.StatisticsForSlaveSet.Replace('_', ' ')},
            { HOFieldNames.StatisticsForSurfaceSet, HOFieldNames.StatisticsForSurfaceSet.Replace('_', ' ')},
            //
            { HOFieldNames.TotalSurfaceForce, HOFieldNames.TotalSurfaceForce.Replace('_', ' ')},
            { HOFieldNames.MomentAboutOrigin, HOFieldNames.MomentAboutOrigin.Replace('_', ' ')},
            { HOFieldNames.CenterOfGravityCG, HOFieldNames.CenterOfGravityCG.Replace('_', ' ')},
            { HOFieldNames.MeanSurfaceNormal, HOFieldNames.MeanSurfaceNormal.Replace('_', ' ')},
            { HOFieldNames.MomentAboutCG, HOFieldNames.MomentAboutCG.Replace('_', ' ')},
            { HOFieldNames.SurfaceArea, HOFieldNames.SurfaceArea.Replace('_', ' ')},
            { HOFieldNames.SurfaceLoads, HOFieldNames.SurfaceLoads.Replace('_', ' ')},
            // Element                                                              
            { HOFieldNames.Volume, HOFieldNames.Volume.Replace('_', ' ')},
            { HOFieldNames.TotalVolume, HOFieldNames.TotalVolume.Replace('_', ' ')},
            { HOFieldNames.InternalEnergy, HOFieldNames.InternalEnergy.Replace('_', ' ')},
            { HOFieldNames.TotalInternalEnergy, HOFieldNames.TotalInternalEnergy.Replace('_', ' ')},
            { HOFieldNames.KineticEnergy, HOFieldNames.KineticEnergy.Replace('_', ' ')},
            { HOFieldNames.TotalKineticEnergy, HOFieldNames.TotalKineticEnergy.Replace('_', ' ')},
            // Thermal                                                              
            { HOFieldNames.HeatFlux, HOFieldNames.HeatFlux.Replace('_', ' ')},
            { HOFieldNames.BodyHeating, HOFieldNames.BodyHeating.Replace('_', ' ')},
            { HOFieldNames.TotalBodyHeating, HOFieldNames.TotalBodyHeating.Replace('_', ' ')},
        };

        static private IEnumerable<string[]> SplitToDataSetLinesList(string[] lines, Dictionary<string, string> repairedSetNames,
                                                                     out bool steadyStateDynamics)
        {
            // displacements (vx, vy, vz) for set DISP and time  0.1000000E+00
            //         5   5.080202E+00  0.000000E+00  0.000000E+00
            // forces (fx, fy, fz) for set FORCE and time  0.1000000E+00
            //         69 -2.678823E-05  6.029691E+01  1.673592E+01
            //         47  7.091853E-05  1.246206E+01  3.973111E+00
            //         48 -1.268813E-04 -5.285929E+01 -1.336375E+01
            // stresses (elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz) for set ELEMENTSET-1 and time  0.1000000E+01
            //         2030   1 -1.824212E-11 -1.000000E-01 -1.062898E-10 -6.614340E-11 -5.298272E-10  3.899325E-10
            //         2030   2 -2.853204E-09 -1.000000E-01 -3.195191E-11  1.074865E-09 -1.638492E-10 -3.539078E-10
            Dictionary<string, HashSet<string>> existingNames = new Dictionary<string, HashSet<string>>();
            List<string> dataSet;
            List<string[]> dataSets = new List<string[]>();
            //
            string theName;
            steadyStateDynamics = false;
            for (int i = 0; i < lines.Length; i++)
            {
                if (lines[i].Length == 0) continue;
                //
                theName = null;
                foreach (var entry in nameKeyMap)
                {
                    if (lines[i].ToUpper().StartsWith(entry.Value.ToUpper()))
                    {
                        theName = entry.Key;
                        break;
                    }
                }
                // Frequency
                if (theName == _eigenvalueOutputKey ||
                    theName == _participationFactorsKey ||
                    theName == _effectiveModalMassKey ||
                    theName == _totalEffectiveMassKey ||
                    // Steady state
                    theName == _participationFactorsForFrequencyKey ||
                    // Complex
                    theName == _participationFactorsForModeKey ||
                    theName == _modalAssuranceCriteriumKey)
                {
                    if (!steadyStateDynamics && lines[i].ToUpper().StartsWith(_participationFactorsForFrequencyKey))
                        steadyStateDynamics = true;
                    //
                    int emptyLinesCounter = 0;
                    dataSet = new List<string> { lines[i] };
                    i++;
                    //
                    while (i < lines.Length)
                    {
                        if (lines[i].Length == 0) emptyLinesCounter++;
                        else dataSet.Add(lines[i]);
                        if (emptyLinesCounter == 3) break;  // must be here to prevent i++
                        i++;
                    }
                    //
                    dataSets.Add(dataSet.ToArray());
                }
                // Complex frequency
                else if (theName == _eigenmodeTurningDirectionKey)
                {
                    int emptyLinesCounter = 0;
                    dataSet = new List<string> { lines[i] };
                    i++;
                    //
                    while (i < lines.Length && emptyLinesCounter <= 4)
                    {
                        bool nextDataSet = nameKeyMap.Values.Any(
                            key => lines[i].StartsWith(key, StringComparison.OrdinalIgnoreCase));
                        if (nextDataSet)
                        {
                            i--;
                            break;
                        }
                        if (lines[i].Length == 0) emptyLinesCounter++;
                        else dataSet.Add(lines[i]);
                        i++;
                    }
                    //
                    dataSets.Add(dataSet.ToArray());
                }
                // Buckling
                else if (theName == _bucklingFactorKey)
                {
                    int emptyLinesCounter = 0;
                    dataSet = new List<string> { lines[i] };
                    i++;
                    //
                    while (i < lines.Length)
                    {
                        if (lines[i].Length == 0) emptyLinesCounter++;
                        else dataSet.Add(lines[i]);
                        if (emptyLinesCounter == 3) break;
                        //
                        i++;
                    }
                    //
                    dataSets.Add(dataSet.ToArray());
                }
                // Contact statistics
                else if (theName == HOFieldNames.StatisticsForSlaveSet)
                {
                    dataSet = new List<string>();
                    for (int j = 0; j <= 8 && i < lines.Length; j++)
                    {
                        if (lines[i].Length != 0) dataSet.Add(lines[i]);
                        i+=2;
                    }
                    // At the end reduce the i for 1 since it will be increased next time in the loop
                    i--;
                    //
                    IEnumerable<string[]> repairedSets = RepairContactStatistics(dataSet.ToArray(), ref existingNames, repairedSetNames);
                    //
                    if (repairedSets != null) dataSets.AddRange(repairedSets);
                }
                // Section statistics
                else if (theName == HOFieldNames.StatisticsForSurfaceSet)
                {
                    dataSet = new List<string>();
                    for (int j = 0; j <= 8 && i < lines.Length; j++)
                    {
                        if (lines[i].Length != 0) dataSet.Add(lines[i]);
                        i += 2;
                    }
                    // At the end reduce the i for 1 since it will be increased next time in the loop
                    i--;
                    IEnumerable<string[]> repairedSets = RepairSectionStatistics(dataSet.ToArray(), ref existingNames, repairedSetNames);
                    //
                    if (repairedSets != null) dataSets.AddRange(repairedSets);
                }
                else if (theName != null)
                {
                    dataSet = new List<string> { lines[i] };
                    i++;
                    //
                    if (theName == _stepKey || theName == _incrementKey || theName == _eigenvalueNumberKey) { }
                    else
                    {
                        while (i < lines.Length && lines[i].Length == 0) i++;    // skip empty lines
                        //
                        while (i < lines.Length)
                        {
                            if (lines[i].Length == 0 || lines[i].Contains("time")) break;    // last line is empty
                            else dataSet.Add(lines[i]);
                            //
                            i++;
                        }
                        //
                    }
                    dataSets.Add(dataSet.ToArray());
                }
            }
            //
            return dataSets;
        }
        static private List<string[]> RepairContactStatistics(string[] lines, ref Dictionary<string, HashSet<string>> existingNames,
                                                              Dictionary<string, string> repairedSetNames)
        {            
            //statistics for slave set INTERNAL_SELECTION - 2_CONTACTPAIR - 1_SLAVE, master set INTERNAL_SELECTION - 1_CONTACTPAIR - 1_MASTER and time  0.5000000E+00
            //total surface force (fx, fy, fz) and moment about the origin (mx, my, mz)
            //3.821561E+02  1.814803E+02 - 5.224860E+03  4.075417E+05  3.873634E+03  2.996193E+04
            //center of gravity and mean normal
            //- 6.862848E+00 - 8.165902E+01  1.040585E+02  0.000000E+00  0.000000E+00  1.000000E+00
            //moment about the center of gravity(mx, my, mz)
            //- 2.306952E+02 - 3.552590E+01  9.056343E-01
            //area, normal force(+ = tension) and shear force(size)
            //7.729843E+03 - 5.224860E+03  4.230584E+02
            //
            string[] dataSet;
            List<string[]> repairedDataSets = new List<string[]>();
            //
            if (lines.Length != 9) return repairedDataSets;
            //
            string[] tmp = lines[0].Split(new string[] { "slave set", "master set", "and time"}, 
                                          StringSplitOptions.RemoveEmptyEntries);
            string slaveName = tmp[1].Trim(new char[] { ' ', ','});
            string masterName = tmp[2].Trim();
            string time = tmp[3].Trim();
            //
            string name = slaveName + _atSplitter[0] + masterName;
            //
            HashSet<string> existingNamesAtTime;
            if (existingNames.TryGetValue(time, out existingNamesAtTime))
            {
                if (existingNamesAtTime.Contains(name)) return null;
            }
            else
            {
                existingNames.Add(time, new HashSet<string>() { name });
            }
            // Total surface force
            tmp = lines[2].Split(_spaceSplitter, StringSplitOptions.RemoveEmptyEntries);
            dataSet = new string[2];
            dataSet[0] = "Total surface force (FX, FY, FZ) for set " + name + " and time " + time;
            dataSet[1] = string.Format("{0} {1} {2}", tmp[0], tmp[1], tmp[2]);
            repairedDataSets.Add(dataSet);
            // Moment about origin
            dataSet = new string[2];
            dataSet[0] = "Moment about origin (MX, MY, MZ) for set " + name + " and time " + time;
            dataSet[1] = string.Format("{0} {1} {2}", tmp[3], tmp[4], tmp[5]);
            repairedDataSets.Add(dataSet);
            // Center of gravity CG
            tmp = lines[4].Split(_spaceSplitter, StringSplitOptions.RemoveEmptyEntries);
            dataSet = new string[2];
            dataSet[0] = "Center of gravity CG (X, Y, Z) for set " + name + " and time " + time;
            dataSet[1] = string.Format("{0} {1} {2}", tmp[0], tmp[1], tmp[2]);
            repairedDataSets.Add(dataSet);
            // Mean normal
            dataSet = new string[2];
            dataSet[0] = "Mean surface normal (NX, NY, NZ) for set " + name + " and time " + time;
            dataSet[1] = string.Format("{0} {1} {2}", tmp[3], tmp[4], tmp[5]);
            repairedDataSets.Add(dataSet);
            // Moment about CG
            tmp = lines[6].Split(_spaceSplitter, StringSplitOptions.RemoveEmptyEntries);
            dataSet = new string[2];
            dataSet[0] = "Moment about CG (MX, MY, MZ) for set " + name + " and time " + time;
            dataSet[1] = string.Format("{0} {1} {2}", tmp[0], tmp[1], tmp[2]);
            repairedDataSets.Add(dataSet);
            // Area
            tmp = lines[8].Split(_spaceSplitter, StringSplitOptions.RemoveEmptyEntries);
            dataSet = new string[2];
            dataSet[0] = "Surface area (A) for set " + name + " and time " + time;
            dataSet[1] = tmp[0];
            repairedDataSets.Add(dataSet);
            // Surface load
            dataSet = new string[2];
            dataSet[0] = string.Format("Surface loads ({0}, {1}) for set {2}  and time {3}",
                                        HOComponentNames.NORMAL_FORCE,
                                        HOComponentNames.SHEAR_FORCE,
                                        name, time);
            dataSet[1] = string.Format("{0} {1}", tmp[1], tmp[2]);
            repairedDataSets.Add(dataSet);
            //
            return repairedDataSets;
        }
        static private List<string[]> RepairSectionStatistics(string[] lines, ref Dictionary<string, HashSet<string>> existingNames,
                                                              Dictionary<string, string> repairedSetNames)
        {
            // statistics for surface set SURFACE-1 and time  0.1000000E+00
            //   total surface force(fx, fy, fz) and moment about the origin(mx, my, mz)
            //   - 2.667946E+02 - 1.644923E-01  5.003642E+00  4.311920E+01  7.424729E+01  2.009665E+02
            //   center of gravity and mean normal
            //   - 4.802744E+00  2.625216E-04  4.805098E-05  4.819484E-01  3.554706E-17 - 6.629240E-19
            //   moment about the center of gravity(mx, my, mz)
            //    4.311787E+01  5.022890E+01  2.001065E+02
            //   area, normal force(+ = tension), shear force(size), torque and bending moment(size)
            //    3.872828E+02 - 1.285813E+02  2.048863E+02  2.078059E+01  2.089530E+02
            //
            string[] dataSet;
            List<string[]> repairedDataSets = new List<string[]>();
            //
            if (lines.Length != 9) return repairedDataSets;
            //
            string[] tmp = lines[0].Split(new string[] { "surface set", "and time" },
                                          StringSplitOptions.RemoveEmptyEntries);
            string name = tmp[1].Trim();
            string time = tmp[2].Trim();
            //
            HashSet<string> existingNamesAtTime;
            if (existingNames.TryGetValue(time, out existingNamesAtTime))
            {
                if (existingNamesAtTime.Contains(name)) return null;
            }
            else
            {
                existingNames.Add(time, new HashSet<string>() { name });
            }
            // Total surface force
            tmp = lines[2].Split(_spaceSplitter, StringSplitOptions.RemoveEmptyEntries);
            dataSet = new string[2];
            dataSet[0] = "Total surface force (FX, FY, FZ) for set " + name + " and time " + time;
            dataSet[1] = string.Format("{0} {1} {2}", tmp[0], tmp[1], tmp[2]);
            repairedDataSets.Add(dataSet);
            // Moment about origin
            dataSet = new string[2];
            dataSet[0] = "Moment about origin (MX, MY, MZ) for set " + name + " and time " + time;
            dataSet[1] = string.Format("{0} {1} {2}", tmp[3], tmp[4], tmp[5]);
            repairedDataSets.Add(dataSet);
            // Center of gravity CG
            tmp = lines[4].Split(_spaceSplitter, StringSplitOptions.RemoveEmptyEntries);
            dataSet = new string[2];
            dataSet[0] = "Center of gravity CG (X, Y, Z) for set " + name + " and time " + time;
            dataSet[1] = string.Format("{0} {1} {2}", tmp[0], tmp[1], tmp[2]);
            repairedDataSets.Add(dataSet);
            // Mean normal
            dataSet = new string[2];
            dataSet[0] = "Mean surface normal (NX, NY, NZ) for set " + name + " and time " + time;
            dataSet[1] = string.Format("{0} {1} {2}", tmp[3], tmp[4], tmp[5]);
            repairedDataSets.Add(dataSet);
            // Moment about CG
            tmp = lines[6].Split(_spaceSplitter, StringSplitOptions.RemoveEmptyEntries);
            dataSet = new string[2];
            dataSet[0] = "Moment about CG (MX, MY, MZ) for set " + name + " and time " + time;
            dataSet[1] = string.Format("{0} {1} {2}", tmp[0], tmp[1], tmp[2]);
            repairedDataSets.Add(dataSet);
            // Area
            tmp = lines[8].Split(_spaceSplitter, StringSplitOptions.RemoveEmptyEntries);
            dataSet = new string[2];
            dataSet[0] = "Surface area (A) for set " + name + " and time " + time;
            dataSet[1] = tmp[0];
            repairedDataSets.Add(dataSet);
            // Surface load
            dataSet = new string[2];
            dataSet[0] = string.Format("Surface loads ({0}, {1}, {2}, {3}) for set {4}  and time {5}",
                                        HOComponentNames.NORMAL_FORCE,
                                        HOComponentNames.SHEAR_FORCE,
                                        HOComponentNames.TORQUE,
                                        HOComponentNames.BENDING_MOMENT,
                                        name, time);
            dataSet[1] = string.Format("{0} {1} {2} {3}", tmp[1], tmp[2], tmp[3], tmp[4]);
            repairedDataSets.Add(dataSet);
            //
            return repairedDataSets;
        }
        static private void Repair(IEnumerable<string[]> dataSetLinesList)
        {
            foreach (var lines in dataSetLinesList)
            {
                if (lines.Length > 0)
                {
                    foreach (var entry in nameKeyMap)
                    {
                        if (lines[0].ToUpper().StartsWith(entry.Value.ToUpper()))
                        {
                            if (entry.Key == HOFieldNames.Displacements)
                            {
                                //displacements (vx,vy,vz) for set NODESET-1 and time  0.1000000E+01
                                //       310 -2.462709E-03 -6.331758E-04 -4.384750E-05
                                lines[0] = lines[0].Replace("(vx,vy,vz)", "(Id,U1,U2,U3)");
                            }
                            else if (entry.Key == HOFieldNames.Velocities)
                            {
                                //velocities (vx,vy,vz) for set INTERNAL_SELECTION-1_NH_OUTPUT-1 and time  0.8102399E-05
                                //       40  1.162032E-17 -7.948453E-02 -8.204195E-18
                                lines[0] = lines[0].Replace("(vx,vy,vz)", "(Id,V1,V2,V3)");
                            }
                            else if (entry.Key == HOFieldNames.Forces)
                            {
                                //forces (fx,fy,fz) for set NODESET-1 and time  0.1000000E+01
                                //       310 -2.582430E-13 -1.013333E-01  6.199805E-14
                                lines[0] = lines[0].Replace("(fx,fy,fz)", "(Id,RF1,RF2,RF3)");
                            }
                            else if (entry.Key == HOFieldNames.TotalForce)
                            {
                                //total force (fx,fy,fz) for set NODESET-1 and time  0.1000000E+01
                                //       -5.868470E-13 -1.000000E+00 -1.028019E-13
                                lines[0] = lines[0].Replace("(fx,fy,fz)", "(RF1,RF2,RF3)");
                            }
                            else if (entry.Key == HOFieldNames.Stresses)
                            {
                                //stresses (elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz) for set SOLID_PART-1 and time  0.1000000E+01
                                //      1655   1  1.186531E-02 -3.997792E-02 -3.119545E-03  1.104426E-02  2.740127E-03 -9.467634E-03
                                lines[0] = lines[0].Replace("(elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz)",
                                                            "(Id,Int.Pnt.,S11,S22,S33,S12,S13,S23)");
                                RepairShellStressLines(lines);
                            }
                            else if (entry.Key == HOFieldNames.Strains)
                            {
                                //strains (elem, integ.pnt.,exx,eyy,ezz,exy,exz,eyz) forset SOLID_PART-1 and time  0.1000000E+01
                                //      1655   1  1.180693E-07 -2.028650E-07  2.530589E-08  6.836925E-08  1.696269E-08 -5.860917E-08
                                lines[0] = lines[0].Replace("(elem, integ.pnt.,exx,eyy,ezz,exy,exz,eyz)",
                                                            "(Id,Int.Pnt.,E11,E22,E33,E12,E13,E23)");
                                lines[0] = lines[0].Replace(" forset ", " for set ");
                            }
                            else if (entry.Key == HOFieldNames.MechanicalStrains)
                            {
                                // mechanical strains (elem, integ.pnt.,exx,eyy,ezz,exy,exz,eyz) forset ELEMENTSET-1 and time  0.1000000E+01
                                //      2030   1  1.428572E-07 -4.761905E-07  1.428571E-07 -1.951987E-14  2.100533E-15  1.625910E-15
                                lines[0] = lines[0].Replace("(elem, integ.pnt.,exx,eyy,ezz,exy,exz,eyz)",
                                                            "(Id,Int.Pnt.,E11,E22,E33,E12,E13,E23)");
                                lines[0] = lines[0].Replace(" forset ", " for set ");
                            }
                            else if (entry.Key == HOFieldNames.EquivalentPlasticStrains)
                            {
                                // equivalent plastic strain (elem, integ.pnt.,pe)for set ELEMENTSET-1 and time  0.6250000E-01
                                //      1682   1  0.000000E+00
                                lines[0] = lines[0].Replace("(elem, integ.pnt.,pe)",
                                                            "(Id,Int.Pnt.,PEEQ)");
                                lines[0] = lines[0].Replace(")for set ", ") for set ");
                            }
                            // Thermal                                                                                              
                            else if (entry.Key == HOFieldNames.Temperatures)
                            {
                                // temperatures for set INTERNAL_SELECTION-1_NH_OUTPUT-1 and time  0.1000000E+01
                                //      3450  1.000000E+02
                                lines[0] = lines[0].Replace("temperatures for set", "temperatures (Id,T) for set");
                            }
                            else if (entry.Key == HOFieldNames.HeatGeneration)
                            {
                                // heat generation for set INTERNAL_SELECTION-4_NH_OUTPUT-1 and time  0.1000000E+01
                                //       793  6.764684E+02
                                lines[0] = lines[0].Replace("heat generation for set", "heat generation (Id,RFL) for set");
                            }
                            else if (entry.Key == HOFieldNames.TotalHeatGeneration)
                            {
                                // total heat generation for set INTERNAL_SELECTION-4_NH_OUTPUT-1 and time  0.5750000E+01
                                //        9.890290E+02
                                lines[0] = lines[0].Replace("total heat generation for set", "total heat generation (RFL) for set");
                            }
                            //                                                                                                      
                            // Contact                                                                                              
                            //                                                                                                      
                            else if (entry.Key == HOFieldNames.RelativeContactDisplacement)
                            {
                                // relative contact displacement (slave element+face,normal,tang1,tang2) for all contact elements and time 0.1000000E+01
                                //     84102          4 -1.111983E-07 -2.300226E-07  1.142343E-07
                                lines[0] = lines[0].Replace("(slave element+face,normal,tang1,tang2)",
                                                            "(Id,Int.Pnt.,NORMAL,TANG1,TANG2)");
                                lines[0] = lines[0].Replace("for all contact elements", "for set ALL_CONTACT_ELEMENTS");
                            }
                            else if (entry.Key == HOFieldNames.ContactStress)
                            {
                                // contact stress (slave element+face,press,tang1,tang2) for all contact elements and time 0.5000000E+00
                                //     97837          4  9.511105E-01 -2.082501E-01 -2.605988E-02
                                lines[0] = lines[0].Replace("(slave element+face,press,tang1,tang2)",
                                                            "(Id,Int.Pnt.,PRESS,TANG1,TANG2)");
                                lines[0] = lines[0].Replace("for all contact elements", "for set ALL_CONTACT_ELEMENTS");
                            }
                            else if (entry.Key == HOFieldNames.ContactPrintEnergy || entry.Key == HOFieldNames.ContactSpringEnergy)
                            {
                                // contact print energy (slave element+face,energy)for all contact elements and time 0.5000000E+00
                                //     98823          4  6.898953E-06

                                // contact spring energy (slave element+face,energy) for all contact elements and time 0.1000000E+01
                                //       345          3  7.965814E-03
                                lines[0] = lines[0].Replace("(slave element+face,energy) for", "(Id,Int.Pnt.,ENERGY) for");
                                lines[0] = lines[0].Replace("(slave element+face,energy)for", "(Id,Int.Pnt.,ENERGY) for");
                                lines[0] = lines[0].Replace("for all contact elements", "for set ALL_CONTACT_ELEMENTS");
                            }
                            else if (entry.Key == HOFieldNames.TotalNumberOfContactElements)
                            {
                                // total number of contact elements for time  0.5000000E+00
                                // 560
                                lines[0] = lines[0].Replace("elements for time", "elements (NUM) for set ALL_CONTACT_ELEMENTS and time");
                            }
                            //                                                                                                      
                            // Element                                                                                              
                            //                                                                                                      
                            else if (entry.Key == HOFieldNames.InternalEnergyDensity)
                            {
                                // internal energy density (elem, integ.pnt.,eneset ELEMENTSET-1 and time  0.6250000E-01
                                //      3068   1  4.313000E-01
                                lines[0] = lines[0].Replace("(elem, integ.pnt.,eneset ",
                                                            "(Id,Int.Pnt.,ENER) for set ");
                                // internal energy density (elem, integ.pnt.,energy) for set INTERNAL_SELECTION-1_EH_OUTPUT-1 and time  0.6000000E+04
                                lines[0] = lines[0].Replace("(elem, integ.pnt.,energy",
                                                            "(Id,Int.Pnt.,ENER");
                            }
                            else if (entry.Key == HOFieldNames.InternalEnergy)
                            {
                                //internal energy (element, energy) for set SOLID_PART-1 and time  0.1000000E+01
                                //      1655  9.342906E-09
                                lines[0] = lines[0].Replace("(element, energy)", "(Id,ELSE)");
                            }
                            else if (entry.Key == HOFieldNames.TotalInternalEnergy)
                            {
                                //total internal energy for set SOLID_PART-1 and time  0.1000000E+01
                                //        3.249095E-04
                                lines[0] = lines[0].Replace("total internal energy for set",
                                                            "total internal energy (SE) for set");
                            }
                            else if (entry.Key == HOFieldNames.KineticEnergy)
                            {
                                //kinetic energy (element, energy) for set SOLID_PART-1 and time  0.1000000E+01
                                //      1655  9.342906E-09
                                lines[0] = lines[0].Replace("(element, energy)", "(Id,ELKE)");
                                lines[0] = lines[0].Replace("(element,energy)", "(Id,ELKE)");
                                lines[0] = lines[0].Replace("(elem, energy)", "(Id,ELKE)");
                                lines[0] = lines[0].Replace("(elem,energy)", "(Id,ELKE)");
                            }
                            else if (entry.Key == HOFieldNames.TotalKineticEnergy)
                            {
                                //total kinetic energy for set SOLID_PART-1 and time  0.1000000E+01
                                //        3.249095E-04
                                lines[0] = lines[0].Replace("total kinetic energy for set",
                                                            "total kinetic energy (KE) for set");
                            }
                            else if (entry.Key == HOFieldNames.Volume)
                            {
                                //volume (element, volume) for set SOLID_PART-1 and time  0.1000000E+01
                                //      1655  1.538557E+00
                                lines[0] = lines[0].Replace("(element, volume)", "(Id,EVOL)");
                            }
                            else if (entry.Key == HOFieldNames.TotalVolume)
                            {
                                //total volume for set SOLID_PART-1 and time  0.1000000E+01
                                //        2.322033E+03
                                lines[0] = lines[0].Replace("total volume for set", "total volume (VOL) for set");
                            }
                            // Thermal                                                                                              
                            else if (entry.Key == HOFieldNames.HeatFlux)
                            {
                                // heat flux (elem, integ.pnt.,qx,qy,qz) for set INTERNAL_SELECTION-3_EH_OUTPUT-1 and time  0.1000000E+01
                                //       477   1 -6.733427E+00  1.076158E+01 -1.030648E+01
                                lines[0] = lines[0].Replace("(elem, integ.pnt.,qx,qy,qz)", "(Id,Int.Pnt.,Q1,Q2,Q3)");
                            }
                            else if (entry.Key == HOFieldNames.BodyHeating)
                            {
                                // body heating (element, volume) for set INTERNAL_SELECTION-3_EH_OUTPUT-1 and time  0.1000000E+01
                                //       477  0.000000E+00
                                lines[0] = lines[0].Replace("(element, volume)", "(Id,EBHE)");
                            }
                            else if (entry.Key == HOFieldNames.TotalBodyHeating)
                            {
                                // total body heating for set INTERNAL_SELECTION-3_EH_OUTPUT-1 and time  0.1000000E+01
                                //        0.126000E+00
                                lines[0] = lines[0].Replace("total body heating for set", "total body heating (BHE) for set");
                            }
                        }
                        //stresses (elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz) for set INTERNAL_SELECTION-1_EH_OUTPUT-1 and time  0.2000000E+01
                        //
                        //19   1 -8.604228E-16  1.101896E-14  5.000000E-01  2.171349E-16  2.768470E-16 -1.250697E-15 _shell_0000000019   

                    }

                }
            }
        }
        static private void RepairShellStressLines(string[] lines)
        {
            int start;
            for (int i = 1; i < lines.Length; i++)
            {
                start = lines[i].IndexOf("_sh");
                if (start > 0) lines[i] = lines[i].Substring(0, start);
            }
        }
        static private string GetFullSetName(string setName, Dictionary<string, string> hashSuffixFullNames)
        {
            if (hashSuffixFullNames.Count == 0) return setName;
            //
            string fullName;
            string[] names = setName.Split(_atSplitter, StringSplitOptions.None);
            for (int i = 0; i < names.Length; i++)
            {
                fullName = CalculixNameShortener.GetFullName(names[i], hashSuffixFullNames);
                if (fullName != names[i]) names[i] = fullName.ToUpper();
            }
            return string.Join(_atSplitter[0], names);
        }
        static private string RepairSetName(string setName, Dictionary<string, string> repairedSetNames)
        {
            string[] tmp;
            string newName = setName;
            if (setName.Contains(_atSplitter[0]))    // must be first
            {
                if (!repairedSetNames.TryGetValue(setName, out newName))
                {
                    tmp = setName.Split(_atSplitter, StringSplitOptions.None);
                    if (tmp.Length == 2)
                    {
                        string slaveName = RepairSetName(tmp[0], repairedSetNames);
                        string masterName = RepairSetName(tmp[1], repairedSetNames);
                        //
                        if (slaveName.EndsWith(Globals.SlaveNameSuffix.ToUpper()))
                            slaveName = slaveName.Replace(Globals.SlaveNameSuffix.ToUpper(), "");
                        if (masterName.EndsWith(Globals.MasterNameSuffix.ToUpper()))
                            masterName = masterName.Replace(Globals.MasterNameSuffix.ToUpper(), "");
                        //
                        newName = slaveName == masterName ? slaveName : slaveName + "_" + masterName;
                        // Check if an existing set was already renamed to an existing new name
                        if (repairedSetNames.Values.Contains(newName))
                        {
                            newName = NamedClass.GetNameWithoutLastValue(newName);
                            newName = new HashSet<string>(repairedSetNames.Values).GetNextNumberedKey(newName);
                        }
                        repairedSetNames.Add(setName, newName);
                    }
                }
            }
            else if (setName.StartsWith(Globals.InternalSelectionName.ToUpper()))
            {
                if (!repairedSetNames.TryGetValue(setName, out newName))
                {
                    int count = Globals.InternalSelectionName.Split(_underscoreSplitter, StringSplitOptions.None).Length;
                    //
                    tmp = setName.Split(_underscoreSplitter, StringSplitOptions.None);
                    newName = "";
                    for (int i = count; i < tmp.Length; i++)
                    {
                        newName += tmp[i];
                        if (i < tmp.Length - 1) newName += "_";
                    }
                    // Check if an existing set was already renamed to an existing new name
                    if (repairedSetNames.Values.Contains(newName))
                    {
                        newName = NamedClass.GetNameWithoutLastValue(newName);
                        newName = new HashSet<string>(repairedSetNames.Values).GetNextNumberedKey(newName);
                    }
                    repairedSetNames.Add(setName, newName);
                }
            }
            else if (setName.StartsWith(Globals.InternalName.ToUpper()))
            {
                if (!repairedSetNames.TryGetValue(setName, out newName))
                {
                    int count = Globals.InternalName.Split(_underscoreSplitter, StringSplitOptions.None).Length;
                    //
                    tmp = setName.Split(_underscoreSplitter, StringSplitOptions.None);
                    newName = "";
                    for (int i = count; i < tmp.Length; i++)
                    {
                        newName += tmp[i];
                        if (i < tmp.Length - 1) newName += "_";
                    }
                    // Check if an existing set was already renamed to an existing new name
                    if (repairedSetNames.Values.Contains(newName))
                    {
                        newName = NamedClass.GetNameWithoutLastValue(newName);
                        newName = new HashSet<string>(repairedSetNames.Values).GetNextNumberedKey(newName);
                    }
                    repairedSetNames.Add(setName, newName);
                }
            }
            return newName;
        }
        static private DatDataSet GetDatDataSet(string[] dataSetLines, Dictionary<string, string> repairedSetNames,
                                                Dictionary<string, string> hashSuffixFullNames)
        {
            try
            {
                // displacements (vx, vy, vz) for set DISP and time  0.1000000E+00
                IEnumerable<string> componentNames = new List<string>();
                DatDataSet dataSet = new DatDataSet();
                //
                string firstLine = dataSetLines[0];
                if (firstLine.ToUpper().StartsWith(_participationFactorsForFrequencyKey))
                {
                    dataSet.SetName = _participationFactorsForFrequencyKey;
                    return dataSet;
                }
                //
                foreach (var entry in nameKeyMap)
                {
                    if (firstLine.ToLower().StartsWith(entry.Value.ToLower()))
                    {
                        dataSet.FieldName = entry.Key;
                        break;
                    }
                }
                //
                string[] tmp = firstLine.Split(_parenthesesSplitter, StringSplitOptions.RemoveEmptyEntries);
                //
                string[] tmp2 = tmp[1].Split(_componentsSplitter, StringSplitOptions.RemoveEmptyEntries);
                componentNames = tmp2.ToList();
                //
                tmp2 = tmp[2].Split(_dataSplitter, StringSplitOptions.RemoveEmptyEntries);
                dataSet.BaseSetName = GetFullSetName(tmp2[0], hashSuffixFullNames);
                dataSet.SetName = RepairSetName(GetFullSetName(tmp2[0].Trim(), hashSuffixFullNames), repairedSetNames);
                dataSet.Time = double.Parse(tmp2[1]);
                //
                int length;
                double[] values;
                List<bool> locals = new List<bool>();
                List<double[]> allValues = new List<double[]>();
                for (int i = 1; i < dataSetLines.Length; i++)
                {
                    tmp = dataSetLines[i].Split(_spaceSplitter, StringSplitOptions.RemoveEmptyEntries);
                    // Local result
                    if (tmp[tmp.Length - 1].ToUpper() == "L")
                    {
                        locals.Add(true);
                        length = tmp.Length - 1;
                    }
                    else
                    {
                        locals.Add(false);
                        length = tmp.Length;
                    }
                    //
                    values = new double[length];
                    //
                    for (int j = 0; j < length; j++) values[j] = ParseStringToDouble(tmp[j]);
                    // Fix for when no history output exists - Find all occurrences!!!
                    if (dataSet.FieldName == HOFieldNames.RelativeContactDisplacement)
                    {
                        if (values.Length != 5 || double.IsNaN(values[0]) || double.IsNaN(values[1]))
                        {
                            locals.Add(false);
                            // Set the element id to -1
                            // Set the faceName to 1 equals to FeFaceName.S1
                            // Set the values to the smallest possible value
                            allValues.Add(new double[] { -1, 1, double.Epsilon, double.Epsilon, double.Epsilon });
                        }
                    }
                    //
                    allValues.Add(values);
                }
                // Fix for when no history output exists - Find all occurrences!!!
                if (dataSet.FieldName == HOFieldNames.RelativeContactDisplacement && allValues.Count == 0)
                {
                    locals.Add(false);
                    // Set the element id to -1
                    // Set the faceName to 1 equals to FeFaceName.S1
                    // Set the values to the smallest possible value
                    allValues.Add(new double[] { -1, 1, double.Epsilon, double.Epsilon, double.Epsilon });
                }
                dataSet.Locals = locals.ToArray();
                dataSet.Values = allValues.ToArray();
                dataSet.ComponentNames = componentNames.ToArray();
                //
                return dataSet;
            }
            catch
            {
                return new DatDataSet() { FieldName = HOFieldNames.Error };
            }
        }
        static private double ParseStringToDouble(string valueAsString)
        {
            double value;
            int count;
            string tmp3;
            string[] tmp2;
            if (!double.TryParse(valueAsString, out value))
            {
                // Try to repair values as:
                // 1.090361-282  8.468565-284 -8.171595-285
                tmp3 = valueAsString;
                tmp2 = tmp3.Split(_signSplitter, StringSplitOptions.RemoveEmptyEntries);
                if (tmp2.Length == 2)
                {
                    count = tmp3.Length - (tmp2[1].Length + 1);
                    valueAsString = tmp3.Substring(0, count) + "E" + tmp3.Substring(count, tmp2[1].Length + 1);
                    //
                    if (!double.TryParse(valueAsString, out value)) value = double.NaN;
                }
                else value = double.NaN;
            }
            return value;
        }
    }
}

// PrePoMax-X bounded static-deck orchestration. Engineering objects, equations,
// element formatting and analysis keywords remain original PrePoMax sources.
// See root LICENSE and Matej Borovinšek attribution in the reused sources.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using CaeGlobals;
using CaeMesh;
using FileInOut.Input;
using FileInOut.Output.Calculix;

namespace CaeModel
{
    public static class StaticAnalysisDeckWriter
    {
        public static string Write(InpMeshData mesh, IEnumerable<Material> materials,
                                   IEnumerable<SolidSection> sections, StaticStep step)
        {
            if (mesh == null || materials == null || sections == null || step == null)
                throw new ArgumentNullException("Static deck components cannot be null.");
            if (mesh.OmittedKeywords == null || mesh.OmittedKeywords.Length != 0)
                throw new CaeException("Static deck input must contain mesh data only; existing model keywords cannot be discarded.");
            string meshText = MeshDeckWriter.WriteMesh(mesh);
            // Revalidate mutable mesh dictionaries through the original guarded reader.
            var checkedMesh = InpFileReader.ReadMeshData(meshText.Replace("\r", "").Split('\n'));
            if (checkedMesh.ElementBlocks.Any(b => b.InpElementTypeNames.Any(t => t != "C3D8" && t != "C3D4")))
                throw new NotSupportedException("The static-deck boundary supports C3D8 and first-order C3D4 solids only; quadratic tetrahedra remain gated.");
            foreach (var element in checkedMesh.Elements.Values)
            {
                double measure=((FeElement3D)element).GetVolume(checkedMesh.Nodes);
                if (!Finite(measure) || measure==0 || (element is LinearTetraElement && measure<0))
                    throw new CaeException("Original element measure is zero, nonfinite or an inverted tetrahedron.");
            }
            foreach (string name in checkedMesh.NodeSets.Keys.Concat(checkedMesh.ElementSets.Keys)) Name(name);
            var materialList = materials.ToArray(); var sectionList = sections.ToArray();
            if (materialList.Length == 0 || sectionList.Length == 0 || materialList.Length > 10000 || sectionList.Length > 10000)
                throw new CaeException("A bounded nonempty material/section definition is required.");
            var materialNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            var materialText = new List<string>();
            foreach (var material in materialList)
            {
                if (material == null || material.GetType()!=typeof(Material) || material.Properties.Any(p=>p==null || p.GetType()!=typeof(Elastic)) || !materialNames.Add(material.Name)) throw new CaeException("Null or duplicate material.");
                materialText.Add(MaterialDeckWriter.WriteIsotropic(material));
            }
            var usedMaterials = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            var sectionNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            var coverage = new HashSet<int>();
            foreach (var section in sectionList)
            {
                if (section == null || section.GetType()!=typeof(SolidSection)) throw new CaeException("Null solid section.");
                Active(section); Name(section.Name); Name(section.MaterialName);
                if (!sectionNames.Add(section.Name) || section.TwoD || section.RegionType != RegionTypeEnum.ElementSetName ||
                    section.CreationData != null || (section.CreationIds != null && section.CreationIds.Length != 0))
                    throw new NotSupportedException("Unique 3D solid sections on named element sets are required.");
                if (!materialNames.Contains(section.MaterialName)) throw new CaeException("Section refers to a missing material.");
                usedMaterials.Add(section.MaterialName);
                foreach (int id in Set(checkedMesh.ElementSets, section.RegionName))
                    if (!coverage.Add(id)) throw new CaeException("Element has overlapping solid sections.");
            }
            if (!coverage.SetEquals(checkedMesh.Elements.Keys) || !usedMaterials.SetEquals(materialNames))
                throw new CaeException("Every element requires exactly one section and every supplied material must be used.");
            if (step.GetType()!=typeof(StaticStep)) throw new NotSupportedException("Exact original StaticStep type required.");
            Active(step); Name(step.Name);
            if (!step.RunAnalysis || step.Nlgeom || step.Perturbation || step.SolverType != SolverTypeEnum.Default ||
                step.DefinedFields.Count != 0 || step.GetNumberOfStepControls() != 0 ||
                !Enum.IsDefined(typeof(IncrementationTypeEnum), step.IncrementationType) ||
                (step.OutputFrequency != int.MinValue && step.OutputFrequency <= 0))
                throw new NotSupportedException("Only a running linear static step with default solver and ordinary output is supported.");
            double[] times = { step.TimePeriod, step.InitialTimeIncrement, step.MinTimeIncrement, step.MaxTimeIncrement };
            if (times.Any(t => !Finite(t) || t <= 0) || step.InitialTimeIncrement > step.TimePeriod ||
                step.InitialTimeIncrement > step.MaxTimeIncrement || step.MinTimeIncrement > step.InitialTimeIncrement ||
                step.MinTimeIncrement > step.MaxTimeIncrement ||
                (step.IncrementationType == IncrementationTypeEnum.Default &&
                 (step.TimePeriod != 1 || step.InitialTimeIncrement != 1 || step.MinTimeIncrement != 1E-5 || step.MaxTimeIncrement != 1E30)))
                throw new CaeException("Invalid static incrementation or custom values hidden by default incrementation.");
            if (step.BoundaryConditions.Count == 0 || step.BoundaryConditions.Count > 10000 || step.Loads.Count > 10000)
                throw new CaeException("A bounded nonempty displacement constraint definition is required.");
            var constraints = new List<Tuple<DisplacementRotation, double[]>>();
            var constrained = new HashSet<Tuple<int,int>>();
            foreach (var entry in step.BoundaryConditions)
            {
                var bc = entry.Value as DisplacementRotation;
                if (bc == null || bc.GetType()!=typeof(DisplacementRotation) || entry.Key != bc.Name) throw new NotSupportedException("Only named displacement constraints are supported.");
                Active(bc); Name(bc.Name);
                if (bc.TwoD || bc.Complex || bc.PhaseDeg.Value != 0 || bc.AmplitudeName != Amplitude.DefaultAmplitudeName ||
                    bc.CoordinateSystemName != CoordinateSystem.DefaultCoordinateSystemName ||
                    bc.DistributionName != Distribution.DefaultDistributionName || bc.CreationData != null ||
                    (bc.CreationIds != null && bc.CreationIds.Length != 0) || bc.RegionType != RegionTypeEnum.NodeSetName)
                    throw new NotSupportedException("Only constant global translational constraints on named node sets are supported.");
                var values = new[] { bc.U1.Value, bc.U2.Value, bc.U3.Value };
                if (values.All(double.IsNaN) || values.Any(double.IsInfinity) ||
                    !double.IsNaN(bc.UR1.Value) || !double.IsNaN(bc.UR2.Value) || !double.IsNaN(bc.UR3.Value))
                    throw new NotSupportedException("Provide finite translational constraints; free components use NaN. Rotations/fixed sentinels are unsupported.");
                foreach (int id in Set(checkedMesh.NodeSets, bc.RegionName))
                    for (int d = 0; d < 3; d++)
                        if (!double.IsNaN(values[d]) && !constrained.Add(Tuple.Create(id,d)))
                            throw new CaeException("Overlapping displacement definitions for one node/DOF are unsupported.");
                constraints.Add(Tuple.Create(bc,values));
            }
            var loads = new List<Tuple<CLoad,double[]>>(); var loaded = new HashSet<Tuple<int,int>>();
            foreach (var entry in step.Loads)
            {
                var load = entry.Value as CLoad;
                if (load == null || load.GetType()!=typeof(CLoad) || entry.Key != load.Name) throw new NotSupportedException("Only named concentrated forces are supported.");
                Active(load); Name(load.Name);
                if (load.TwoD || load.Complex || load.PhaseDeg.Value != 0 || load.AmplitudeName != Amplitude.DefaultAmplitudeName ||
                    load.CoordinateSystemName != CoordinateSystem.DefaultCoordinateSystemName || load.CreationData != null ||
                    (load.CreationIds != null && load.CreationIds.Length != 0) || load.RegionType != RegionTypeEnum.NodeSetName)
                    throw new NotSupportedException("Only global concentrated forces per node on named node sets are supported.");
                var values = new[] { load.F1.Value, load.F2.Value, load.F3.Value };
                if (values.Any(v => !Finite(v)) || values.All(v => v == 0)) throw new CaeException("Forces must be finite and nonzero.");
                foreach (int id in Set(checkedMesh.NodeSets, load.RegionName))
                    for (int d = 0; d < 3; d++)
                        if (values[d] != 0 && !loaded.Add(Tuple.Create(id,d)))
                            throw new CaeException("Overlapping concentrated loads for one node/DOF are unsupported.");
                loads.Add(Tuple.Create(load,values));
            }
            ValidateOutputs(checkedMesh, step);
            var previous = CultureInfo.CurrentCulture;
            try
            {
                CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
                var text = new StringBuilder("** PrePoMax-X bounded 3D linear-static analysis deck\n");
                text.Append(meshText.Substring(meshText.IndexOf('\n') + 1));
                foreach (string value in materialText) text.Append(value);
                foreach (var section in sectionList) Append(text, new CalSolidSection(section));
                Append(text, new CalStepHeader(step)); Append(text, new CalStaticStep(step));
                foreach (var item in constraints)
                {
                    var source = item.Item1; var v = item.Item2;
                    var snapshot = new DisplacementRotation(source.Name, source.RegionName, RegionTypeEnum.NodeSetName, false, false, 0);
                    snapshot.U1.SetEquationFromValue(v[0]); snapshot.U2.SetEquationFromValue(v[1]); snapshot.U3.SetEquationFromValue(v[2]);
                    Append(text, new CalDisplacementRotation(snapshot, null, null, ComplexLoadTypeEnum.None));
                }
                foreach (var item in loads)
                {
                    var source = item.Item1; var v = item.Item2;
                    var snapshot = new CLoad(source.Name, source.RegionName, RegionTypeEnum.NodeSetName, v[0], v[1], v[2], false, false, 0);
                    var keyword = new CalCLoad(snapshot, null, ComplexLoadTypeEnum.None);
                    Append(text,keyword);
                }
                Append(text, new CalOutputFrequency(step.OutputFrequency));
                foreach (var entry in step.HistoryOutputs)
                {
                    if (entry.Value is NodalHistoryOutput) Append(text, new CalNodePrint((NodalHistoryOutput)entry.Value,entry.Value.RegionName,step.OutputFrequency));
                    else Append(text,new CalElPrint((ElementHistoryOutput)entry.Value,step.OutputFrequency));
                }
                foreach (var entry in step.FieldOutputs)
                {
                    if (entry.Value is NodalFieldOutput) Append(text,new CalNodeFile((NodalFieldOutput)entry.Value,step.OutputFrequency));
                    else Append(text,new CalElFile((ElementFieldOutput)entry.Value,step.OutputFrequency));
                }
                Append(text,new CalEndStep()); return text.ToString();
            }
            finally { CultureInfo.CurrentCulture = previous; }
        }

        private static void ValidateOutputs(InpMeshData mesh, StaticStep step)
        {
            if (step.FieldOutputs.Count == 0 || step.FieldOutputs.Count > 100 || step.HistoryOutputs.Count > 100)
                throw new CaeException("Bounded nonempty field outputs are required.");
            foreach (var item in step.FieldOutputs)
            {
                var value=item.Value; Active(value); Name(value.Name);
                if (item.Key != value.Name || value.LastIterations || value.ContactElements || !value.Global)
                    throw new NotSupportedException("Only ordinary global field output is supported.");
                if (value.GetType()==typeof(NodalFieldOutput))
                {
                    var flags=((NodalFieldOutput)value).Variables;
                    if (flags==0 || (flags & ~(NodalFieldVariable.U | NodalFieldVariable.RF))!=0) throw new NotSupportedException("Only U/RF nodal output is supported.");
                }
                else if (value.GetType()==typeof(ElementFieldOutput))
                {
                    var output=(ElementFieldOutput)value;
                    if (output.Output!=ElementFieldOutputOutputEnum.Default || output.Variables==0 ||
                        (output.Variables & ~(ElementFieldVariable.E | ElementFieldVariable.S))!=0) throw new NotSupportedException("Only default E/S solid output is supported.");
                }
                else throw new NotSupportedException("Unsupported field output type.");
            }
            foreach (var item in step.HistoryOutputs)
            {
                var value=item.Value; Active(value); Name(value.Name);
                if (item.Key!=value.Name || !value.Global || value.TotalsType!=TotalsTypeEnum.No || value.CreationData!=null ||
                    (value.CreationIds!=null && value.CreationIds.Length!=0)) throw new NotSupportedException("Only ordinary named-region global history output is supported.");
                if (value.GetType()==typeof(NodalHistoryOutput))
                {
                    var flags=((NodalHistoryOutput)value).Variables;
                    if (value.RegionType!=RegionTypeEnum.NodeSetName || flags==0 || (flags & ~(NodalHistoryVariable.U | NodalHistoryVariable.RF))!=0)
                        throw new NotSupportedException("Unsupported nodal history output.");
                    Set(mesh.NodeSets,value.RegionName);
                }
                else if (value.GetType()==typeof(ElementHistoryOutput))
                {
                    var flags=((ElementHistoryOutput)value).Variables;
                    if (value.RegionType!=RegionTypeEnum.ElementSetName || flags==0 || (flags & ~ElementHistoryVariable.S)!=0)
                        throw new NotSupportedException("Unsupported element history output.");
                    Set(mesh.ElementSets,value.RegionName);
                }
                else throw new NotSupportedException("Unsupported history output type.");
            }
        }
        private static int[] Set(Dictionary<string,int[]> sets,string name)
        {
            Name(name); var keys=sets.Keys.Where(k=>string.Equals(k,name,StringComparison.OrdinalIgnoreCase)).ToArray();
            if (keys.Length!=1 || sets[keys[0]]==null || sets[keys[0]].Length==0) throw new CaeException("Missing or empty named region: "+name);
            return sets[keys[0]];
        }
        private static void Name(string name)
        {
            if (name==null || name.Length>80 || !Regex.IsMatch(name,@"\A[A-Za-z_][A-Za-z0-9_-]*\z")) throw new CaeException("Simple keyword names up to 80 characters are required.");
        }
        private static void Active(NamedClass value)
        { if(value==null || !value.Active || !value.Valid) throw new CaeException("Inactive, invalid or null analysis definition."); }
        private static bool Finite(double value) { return !double.IsNaN(value) && !double.IsInfinity(value); }
        private static void Append(StringBuilder text, CalculixKeyword keyword)
        { text.Append(keyword.GetKeywordString()).Append(keyword.GetDataString()); }
    }
}

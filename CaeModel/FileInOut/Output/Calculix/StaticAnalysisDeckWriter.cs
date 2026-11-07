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
        // Original mechanical solid formulation choices (CaeMesh/Elements/FeElementType.cs).
        // A topology-compatible choice changes solver behavior, never node ordering.
        public static string[] CompatibleSolidFormulations(string formulation)
        {
            switch (formulation)
            {
                case "C3D4": return new[] { "C3D4" };
                case "C3D10": case "C3D10T": return new[] { "C3D10", "C3D10T" };
                case "C3D6": return new[] { "C3D6" };
                case "C3D15": return new[] { "C3D15" };
                case "C3D8": case "C3D8R": case "C3D8I": return new[] { "C3D8", "C3D8R", "C3D8I" };
                case "C3D20": case "C3D20R": return new[] { "C3D20", "C3D20R" };
                case "C3D5": case "C3D5I": case "C3D5R": return new[] { formulation };
                case "C3D13": case "C3D13I": case "C3D13R": return new[] { formulation };
                default: return new string[0];
            }
        }

        public static string Write(InpMeshData mesh, IEnumerable<Material> materials,
                                   IEnumerable<SolidSection> sections, Step step,
                                   ConvertPyramidsToEnum? pyramidConversion = null, IEnumerable<AmplitudeTabular> amplitudeDefinitions = null, string initialTemperature = null)
        {
            if (mesh == null || materials == null || sections == null || step == null)
                throw new ArgumentNullException("Static deck components cannot be null.");
            if (mesh.OmittedKeywords == null || mesh.OmittedKeywords.Length != 0)
                throw new CaeException("Static deck input must contain mesh data only; existing model keywords cannot be discarded.");
            var amplitudes=AnalysisModelExtensions.Amplitudes(amplitudeDefinitions);
            string meshText = MeshDeckWriter.WriteMesh(mesh, pyramidConversion);
            // Revalidate mutable mesh dictionaries through the original guarded reader.
            var checkedMesh = InpFileReader.ReadMeshData(meshText.Replace("\r", "").Split('\n'));
            if (checkedMesh.ElementBlocks.Any(b => b.InpElementTypeNames.Any(t => CompatibleSolidFormulations(t).Length == 0)))
                throw new NotSupportedException("Mechanical 3D solid formulations are required for this static analysis.");
            foreach (var element in checkedMesh.Elements.Values)
            {
                // This is an input orientation check, not quadratic measurement.
                // CalculiX evaluates C3D10 shape functions/Jacobians itself. The
                // unresolved original PrePoMax Integrate/GetVolume path must not
                // authorize, alter or prohibit that independent formulation.
                double measure = element is ParabolicTetraElement
                    ? new LinearTetraElement(element.Id, element.NodeIds.Take(4).ToArray()).GetVolume(checkedMesh.Nodes)
                    : ((FeElement3D)element).GetVolume(checkedMesh.Nodes);
                if (!Finite(measure) || measure==0 || ((element is LinearTetraElement || element is ParabolicTetraElement) && measure<0))
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
                if (material == null || material.GetType()!=typeof(Material) || !materialNames.Add(material.Name)) throw new CaeException("Null or duplicate material.");
                materialText.Add(MaterialDeckWriter.WriteMechanical(material));
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
            bool isStatic=step.GetType()==typeof(StaticStep),isFrequency=step.GetType()==typeof(FrequencyStep),isBuckling=step.GetType()==typeof(BuckleStep);
            if(!isStatic && !isFrequency && !isBuckling)throw new NotSupportedException("An exact original static, frequency or buckle step is required.");
            if(!isStatic && (amplitudes.Count>0 || initialTemperature!=null || step.DefinedFields.Count>0 || step.Nlgeom || materialList.Any(m=>m.Properties.Any(p=>p is Plastic || p is ThermalExpansion))))throw new NotSupportedException("This eigenmode workflow requires linear elastic materials and linear geometry.");
            if(isFrequency && (step.Loads.Count!=0 || sectionList.Any(section=>!materialList.Single(m=>string.Equals(m.Name,section.MaterialName,StringComparison.OrdinalIgnoreCase)).Properties.Any(p=>p is Density))))
                throw new CaeException("Frequency analysis requires density for every section and no applied loads.");
            if(isBuckling && step.Loads.Count==0)throw new CaeException("Buckling analysis requires a nonzero reference load.");
            if(isFrequency) {
                var frequency=(FrequencyStep)step;
                if(frequency.NumOfFrequencies<1 || frequency.NumOfFrequencies>1000 || frequency.Storage ||
                    frequency.CyclicSymmetryModeMin!=int.MinValue || frequency.CyclicSymmetryModeMax!=int.MinValue ||
                    (!double.IsNaN(frequency.LowerFrequency) && (!Finite(frequency.LowerFrequency) || frequency.LowerFrequency<0)) ||
                    (!double.IsNaN(frequency.UpperFrequency) && (!Finite(frequency.UpperFrequency) || frequency.UpperFrequency<=0)) ||
                    (!double.IsNaN(frequency.LowerFrequency) && !double.IsNaN(frequency.UpperFrequency) && frequency.LowerFrequency>=frequency.UpperFrequency))
                    throw new CaeException("Valid ordinary frequency controls are required; cyclic/storage workflows remain pending.");
            }
            if(isBuckling) {
                var buckle=(BuckleStep)step;
                if(buckle.NumOfBucklingFactors<1 || buckle.NumOfBucklingFactors>1000 || !Finite(buckle.Accuracy) || buckle.Accuracy<=0)
                    throw new CaeException("Valid buckling mode count and accuracy are required.");
            }
            var temperatureFields=AnalysisModelExtensions.Temperatures(checkedMesh,step,initialTemperature,amplitudes);
            if(materialList.Any(m=>m.Properties.Any(p=>p is ThermalExpansion)) && (temperatureFields.Count==0 || initialTemperature==null))
                throw new CaeException("Thermal expansion requires an explicit initial temperature and prescribed temperature fields.");
            Active(step); Name(step.Name);
            if (!step.RunAnalysis || step.Perturbation || step.SolverType != SolverTypeEnum.Default ||
                step.GetNumberOfStepControls() != 0 ||
                !Enum.IsDefined(typeof(IncrementationTypeEnum), step.IncrementationType) ||
                (step.OutputFrequency != int.MinValue && step.OutputFrequency <= 0))
                throw new NotSupportedException("A running mechanical step with default solver and ordinary global output is required.");
            if(isStatic) {
                var staticStep=(StaticStep)step;
            double[] times = { staticStep.TimePeriod, staticStep.InitialTimeIncrement, staticStep.MinTimeIncrement, staticStep.MaxTimeIncrement };
            if (times.Any(t => !Finite(t) || t <= 0) || staticStep.InitialTimeIncrement > staticStep.TimePeriod ||
                staticStep.InitialTimeIncrement > staticStep.MaxTimeIncrement || staticStep.MinTimeIncrement > staticStep.InitialTimeIncrement ||
                staticStep.MinTimeIncrement > staticStep.MaxTimeIncrement ||
                (staticStep.IncrementationType == IncrementationTypeEnum.Default &&
                 (staticStep.TimePeriod != 1 || staticStep.InitialTimeIncrement != 1 || staticStep.MinTimeIncrement != 1E-5 || staticStep.MaxTimeIncrement != 1E30)))
                throw new CaeException("Invalid static incrementation or custom values hidden by default incrementation.");
            }
            if (step.BoundaryConditions.Count == 0 || step.BoundaryConditions.Count > 10000 || step.Loads.Count > 10000)
                throw new CaeException("A bounded nonempty displacement constraint definition is required.");
            var constraints = new List<Tuple<DisplacementRotation, double[]>>();
            var constrained = new HashSet<Tuple<int,int>>();
            foreach (var entry in step.BoundaryConditions)
            {
                var bc = entry.Value as DisplacementRotation;
                if (bc == null || bc.GetType()!=typeof(DisplacementRotation) || entry.Key != bc.Name) throw new NotSupportedException("Only named displacement constraints are supported.");
                Active(bc); Name(bc.Name);AnalysisModelExtensions.Reference(bc.AmplitudeName,amplitudes);
                if (bc.TwoD || bc.Complex || bc.PhaseDeg.Value != 0 ||
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
                if(!isStatic && values.Any(v=>!double.IsNaN(v) && v!=0))throw new CaeException("Eigenmode supports must be homogeneous zero displacement constraints.");
                constraints.Add(Tuple.Create(bc,values));
            }
            var loads = new List<CalculixKeyword>(); var loaded = new HashSet<Tuple<int,int>>();
            var densityElements = new HashSet<int>();
            foreach(var section in sectionList)
                if(materialList.Single(m=>string.Equals(m.Name,section.MaterialName,StringComparison.OrdinalIgnoreCase)).Properties.Any(p=>p is Density))
                    densityElements.UnionWith(Set(checkedMesh.ElementSets,section.RegionName));
            Dictionary<string,int> incidence=null;
            if(step.Loads.Values.OfType<DLoad>().Any(l=>l.RegionType==RegionTypeEnum.NodeSetName))
                incidence=mesh.Elements.Values.SelectMany(e=>Faces((FeElement3D)e)).GroupBy(f=>FaceKey(f.Item2)).ToDictionary(g=>g.Key,g=>g.Count());
            int pressureIndex=0;
            foreach (var entry in step.Loads)
            {
                var source=entry.Value;
                if(source==null || entry.Key!=source.Name)throw new CaeException("A named mechanical load is required.");
                Active(source);Name(source.Name);AnalysisModelExtensions.Reference(source.AmplitudeName,amplitudes);
                if(source.TwoD || source.Complex || source.PhaseDeg.Value!=0 ||
                   source.CreationData!=null || (source.CreationIds!=null && source.CreationIds.Length!=0))
                    throw new NotSupportedException("Ordinary constant global mechanical loads on named regions are required.");
                if(source.GetType()==typeof(CLoad)) {
                    var load=(CLoad)source;
                    if(load.CoordinateSystemName!=CoordinateSystem.DefaultCoordinateSystemName || load.RegionType!=RegionTypeEnum.NodeSetName)
                        throw new NotSupportedException("Global concentrated forces require named node sets.");
                    var values=new[]{load.F1.Value,load.F2.Value,load.F3.Value};
                    if(values.Any(v=>!Finite(v)) || values.All(v=>v==0))throw new CaeException("Forces must be finite and nonzero.");
                    foreach(int id in Set(checkedMesh.NodeSets,load.RegionName))for(int d=0;d<3;d++)
                        if(values[d]!=0 && !loaded.Add(Tuple.Create(id,d)))throw new CaeException("Overlapping concentrated loads for one node/DOF are unsupported.");
                    loads.Add(new CalCLoad(new CLoad(load.Name,load.RegionName,RegionTypeEnum.NodeSetName,values[0],values[1],values[2],false,false,0){AmplitudeName=load.AmplitudeName},null,ComplexLoadTypeEnum.None));
                }
                else if(source.GetType()==typeof(GravityLoad)) {
                    var load=(GravityLoad)source;
                    if(load.RegionType!=RegionTypeEnum.ElementSetName)throw new NotSupportedException("Gravity requires a named element set.");
                    var values=new[]{load.F1.Value,load.F2.Value,load.F3.Value};
                    if(values.Any(v=>!Finite(v)) || values.All(v=>v==0))throw new CaeException("Gravity acceleration must be finite and nonzero.");
                    if(Set(checkedMesh.ElementSets,load.RegionName).Any(id=>!densityElements.Contains(id)))throw new CaeException("Every gravity-loaded element requires a material density.");
                    loads.Add(new CalGravityLoad(new GravityLoad(load.Name,load.RegionName,RegionTypeEnum.ElementSetName,values[0],values[1],values[2],false,false,0){AmplitudeName=load.AmplitudeName},ComplexLoadTypeEnum.None));
                }
                else if(source.GetType()==typeof(DLoad)) {
                    var load=(DLoad)source;double magnitude=load.Magnitude.Value;
                    if(!Finite(magnitude) || load.DistributionName!=Distribution.DefaultDistributionName)
                        throw new CaeException("Pressure must be finite and constant over its selected region.");
                    var targets=new List<Tuple<int,FeFaceName,int[]>>();
                    if(load.RegionType==RegionTypeEnum.NodeSetName) {
                        var nodes=new HashSet<int>(Set(mesh.NodeSets,load.RegionName));
                        foreach(var e in mesh.Elements.Values)foreach(var face in Faces((FeElement3D)e))
                            if(incidence[FaceKey(face.Item2)]==1 && face.Item2.All(nodes.Contains))targets.Add(Tuple.Create(e.Id,face.Item1,face.Item2));
                    } else if(load.RegionType==RegionTypeEnum.ElementSetName) {
                        if((int)load.ElementFaceName<1 || (int)load.ElementFaceName>6)throw new CaeException("An original element face S1–S6 is required.");
                        foreach(int id in Set(mesh.ElementSets,load.RegionName)) {
                            var faces=Faces((FeElement3D)mesh.Elements[id]).Where(f=>f.Item1==load.ElementFaceName).ToArray();
                            if(faces.Length!=1)throw new CaeException("Selected face does not exist on every pressure-loaded element.");
                            targets.Add(Tuple.Create(id,load.ElementFaceName,faces[0].Item2));
                        }
                    } else throw new NotSupportedException("Pressure requires a boundary node set or explicit element-set face.");
                    if(targets.Count==0)throw new CaeException("Pressure region contains no complete exterior element faces.");
                    var groups=new Dictionary<FeFaceName,HashSet<int>>();
                    foreach(var target in targets) {
                        // Original face node identities determine correspondence even
                        // when original CalElement collapses a pyramid for the solver.
                        var matches=Faces((FeElement3D)checkedMesh.Elements[target.Item1]).Where(f=>FaceKey(f.Item2)==FaceKey(target.Item3)).ToArray();
                        if(matches.Length!=1)throw new CaeException("Original pressure face correspondence was lost during solver export.");
                        var face=matches[0].Item1;
                        if(!groups.ContainsKey(face))groups.Add(face,new HashSet<int>());
                        groups[face].Add(target.Item1);
                    }
                    var surface=new FeSurface(load.Name){Type=FeSurfaceType.Element,SurfaceFaceTypes=FeSurfaceFaceTypes.SolidFaces};
                    foreach(var group in groups.OrderBy(g=>g.Key)) {
                        string name;
                        do{name="_XPressure_"+(++pressureIndex);}while(checkedMesh.ElementSets.Keys.Any(n=>string.Equals(n,name,StringComparison.OrdinalIgnoreCase)));
                        checkedMesh.ElementSets.Add(name,group.Value.OrderBy(id=>id).ToArray());surface.AddElementFace(group.Key,name);
                    }
                    var snapshot=new DLoad(load.Name,load.RegionName,load.RegionType,magnitude,false,false,0){AmplitudeName=load.AmplitudeName};
                    loads.Add(new CalDLoad(snapshot,surface,ComplexLoadTypeEnum.None));
                } else throw new NotSupportedException("Unsupported mechanical load type.");
            }
            // New derived element sets are job-owned pressure-face references.
            meshText=MeshDeckWriter.WriteMesh(checkedMesh);
            ValidateOutputs(checkedMesh, step);
            var previous = CultureInfo.CurrentCulture;
            try
            {
                CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
                var text = new StringBuilder(step.Nlgeom || materialList.Any(m=>m.Properties.Any(p=>p is Plastic))
                    ? "** PrePoMax-X 3D nonlinear-static analysis deck\n" : isStatic ? "** PrePoMax-X bounded 3D linear-static analysis deck\n" : "** PrePoMax-X 3D eigenmode analysis deck\n");
                // Solver decks use the original CalNode formatter. G17 remains
                // correct for lossless mesh exchange, but can exceed CalculiX's
                // 20-character numeric input field (e.g. 6.8000000000000001E-15).
                int elementsAt = meshText.IndexOf("*Element", StringComparison.Ordinal);
                text.Append(CalNodeFormatting.Write3D(checkedMesh.Nodes));
                text.Append(meshText.Substring(elementsAt));
                foreach (string value in materialText) text.Append(value);
                foreach (var section in sectionList) Append(text, new CalSolidSection(section));
                AnalysisModelExtensions.WriteAmplitudes(text,amplitudes);
                AnalysisModelExtensions.WriteMechanicalInitial(text,checkedMesh,initialTemperature);
                Append(text, new CalStepHeader(step));
                if(isStatic)Append(text,new CalStaticStep((StaticStep)step));
                else if(isFrequency)Append(text,new CalFrequencyStep((FrequencyStep)step));
                else Append(text,new CalBuckleStep((BuckleStep)step));
                foreach (var item in constraints)
                {
                    var source = item.Item1; var v = item.Item2;
                    var snapshot = new DisplacementRotation(source.Name, source.RegionName, RegionTypeEnum.NodeSetName, false, false, 0);
                    snapshot.AmplitudeName=source.AmplitudeName;
                    snapshot.U1.SetEquationFromValue(v[0]); snapshot.U2.SetEquationFromValue(v[1]); snapshot.U3.SetEquationFromValue(v[2]);
                    Append(text, new CalDisplacementRotation(snapshot, null, null, ComplexLoadTypeEnum.None));
                }
                foreach (var keyword in loads.Concat(temperatureFields)) Append(text,keyword);
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

        private static string FaceKey(IEnumerable<int> ids) { return string.Join(",",ids.Distinct().OrderBy(id=>id)); }
        private static IEnumerable<Tuple<FeFaceName,int[]>> Faces(FeElement3D element)
        {
            for(int i=1;i<=6;i++) {
                int[] ids;
                try { ids=element.GetNodeIdsFromFaceName((FeFaceName)i); }
                catch(NotSupportedException) { continue; }
                if(ids.Distinct().Count()>=3)yield return Tuple.Create((FeFaceName)i,ids);
            }
        }

        internal static void ValidateOutputs(InpMeshData mesh, Step step)
        {
            if (step.FieldOutputs.Count == 0 || step.FieldOutputs.Count > 100 || step.HistoryOutputs.Count > 100)
                throw new CaeException("Bounded nonempty field outputs are required.");
            bool thermal=step is HeatTransferStep;
            foreach (var item in step.FieldOutputs)
            {
                var value=item.Value; Active(value); Name(value.Name);
                if (item.Key != value.Name || value.LastIterations || value.ContactElements || !value.Global)
                    throw new NotSupportedException("Only ordinary global field output is supported.");
                if (value.GetType()==typeof(NodalFieldOutput))
                {
                    var flags=((NodalFieldOutput)value).Variables;
                    if (flags==0 || (flags & ~(thermal ? NodalFieldVariable.NT | NodalFieldVariable.RFL : NodalFieldVariable.U | NodalFieldVariable.RF))!=0) throw new NotSupportedException("Only U/RF nodal output is supported.");
                }
                else if (value.GetType()==typeof(ElementFieldOutput))
                {
                    var output=(ElementFieldOutput)value;
                    if (output.Output!=ElementFieldOutputOutputEnum.Default || output.Variables==0 ||
                        (output.Variables & ~(thermal ? ElementFieldVariable.HFL : ElementFieldVariable.E | ElementFieldVariable.S | ElementFieldVariable.PEEQ))!=0) throw new NotSupportedException("Only ordinary E/S/PEEQ solid output is supported.");
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
                    if (value.RegionType!=RegionTypeEnum.NodeSetName || flags==0 || (flags & ~(thermal ? NodalHistoryVariable.NT | NodalHistoryVariable.RFL : NodalHistoryVariable.U | NodalHistoryVariable.RF))!=0)
                        throw new NotSupportedException("Unsupported nodal history output.");
                    Set(mesh.NodeSets,value.RegionName);
                }
                else if (value.GetType()==typeof(ElementHistoryOutput))
                {
                    var flags=((ElementHistoryOutput)value).Variables;
                    if (value.RegionType!=RegionTypeEnum.ElementSetName || flags==0 || (flags & ~(thermal ? ElementHistoryVariable.HFL : ElementHistoryVariable.S))!=0)
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
        internal static void Name(string name)
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

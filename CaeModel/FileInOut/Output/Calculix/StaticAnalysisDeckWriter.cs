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
    // Configuration transport for original user-keyword-only section families.
    // Numerical section/element behavior remains in the unchanged solver.
    public sealed class StructuralSectionData
    {
        public double? Mass {get;set;}
        public double? Stiffness {get;set;}
        public int Dof {get;set;}
        public int SecondDof {get;set;}
        public double? Clearance {get;set;}
        public double? TensileForce {get;set;}
        public string Kind { get; set; }
        public string Shape { get; set; }
        public double[] Dimensions { get; set; }
        public double[] Direction { get; set; }
        public double Offset { get; set; }
        public string[] LayerMaterials { get; set; }
        public double[] LayerThicknesses { get; set; }
    }
    public static class StaticAnalysisDeckWriter
    {
        // Original mechanical solid formulation choices (CaeMesh/Elements/FeElementType.cs).
        // A topology-compatible choice changes solver behavior, never node ordering.
        public static string[] CompatibleSolidFormulations(string formulation)
        {
            foreach (string prefix in new[] { "CPS", "CPE", "CAX" })
            {
                string suffix = formulation.StartsWith(prefix, StringComparison.Ordinal) ? formulation.Substring(3) : null;
                if (suffix == "3" || suffix == "6") return new[] { "CPS" + suffix, "CPE" + suffix, "CAX" + suffix };
                if (suffix == "4" || suffix == "4R") return new[] { "CPS4", "CPS4R", "CPE4", "CPE4R", "CAX4", "CAX4R" };
                if (suffix == "8" || suffix == "8R") return new[] { "CPS8", "CPS8R", "CPE8", "CPE8R", "CAX8", "CAX8R" };
            }
            foreach (var group in new[] {new[]{"S3","S3R"},new[]{"S6"},new[]{"S4","S4R"},new[]{"S8","S8R"},
                new[]{"M3D3"},new[]{"M3D6"},new[]{"M3D4","M3D4R"},new[]{"M3D8","M3D8R"},
                new[]{"B31","B31R","B21"},new[]{"B32","B32R"},new[]{"T3D2","T2D2"},new[]{"T3D3","T2D3"}})
                if(group.Contains(formulation))return group;
            if(new[]{"MASS","SPRING1","SPRING2","SPRINGA","GAPUNI"}.Contains(formulation))return new[]{formulation};
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
                                   IEnumerable<Section> sections, Step step,
                                   ConvertPyramidsToEnum? pyramidConversion = null, IEnumerable<AmplitudeTabular> amplitudeDefinitions = null, string initialTemperature = null, FrequencyStep modalBasis = null, string modelSpace = "ThreeD", IDictionary<string,StructuralSectionData> structuralSections = null)
        {
            if (mesh == null || materials == null || sections == null || step == null)
                throw new ArgumentNullException("Static deck components cannot be null.");
            if (mesh.OmittedKeywords == null || mesh.OmittedKeywords.Length != 0)
                throw new CaeException("Static deck input must contain mesh data only; existing model keywords cannot be discarded.");
            string prefix = modelSpace == "PlaneStress" ? "CPS" : modelSpace == "PlaneStrain" ? "CPE" : modelSpace == "Axisymmetric" ? "CAX" : null;
            bool twoD = prefix != null;
            if (!twoD && modelSpace != "ThreeD") throw new CaeException("Unknown model space.");
            if (twoD && (pyramidConversion.HasValue ||
                mesh.Nodes.Values.Any(n => n.Z != 0 || (modelSpace == "Axisymmetric" && n.X < 0))))
                throw new CaeException("Plane/axisymmetric static models require XY coordinates (X is nonnegative radius), without pyramid conversion.");
            var amplitudes=AnalysisModelExtensions.Amplitudes(amplitudeDefinitions);
            string meshText = MeshDeckWriter.WriteMesh(mesh, pyramidConversion);
            // Revalidate mutable mesh dictionaries through the original guarded reader.
            var checkedMesh = InpFileReader.ReadMeshData(meshText.Replace("\r", "").Split('\n'));
            if (checkedMesh.ElementBlocks.Any(b => b.InpElementTypeNames.Any(t => CompatibleSolidFormulations(t).Length == 0 ||
                (twoD ? !t.StartsWith(prefix, StringComparison.Ordinal) : !t.StartsWith("C3D", StringComparison.Ordinal) && !t.StartsWith("S", StringComparison.Ordinal) && !t.StartsWith("M3D", StringComparison.Ordinal) && !t.StartsWith("B", StringComparison.Ordinal) && !t.StartsWith("T", StringComparison.Ordinal) && !new[]{"MASS","SPRING1","SPRING2","SPRINGA","GAPUNI"}.Contains(t)))))
                throw new NotSupportedException("Every formulation must match the explicitly selected model space.");
            bool structural = checkedMesh.Elements.Values.Any(e=>e is FeElement1D || (!twoD && e is FeElement2D));
            if(!structural && step.FieldOutputs.Values.OfType<ElementFieldOutput>().Any(o=>o.Output!=ElementFieldOutputOutputEnum.Default))throw new NotSupportedException("Explicit expanded/surface output is connected for structural shell/line models only.");

            var formulations=checkedMesh.ElementBlocks.SelectMany(b=>b.ElementLabels.Select(id=>new {id,type=b.InpElementTypeNames.Single()})).ToDictionary(x=>x.id,x=>x.type);
            foreach (var element in checkedMesh.Elements.Values)
            {
                // This is an input orientation check, not quadratic measurement.
                // CalculiX evaluates C3D10 shape functions/Jacobians itself. The
                // unresolved original PrePoMax Integrate/GetVolume path must not
                // authorize, alter or prohibit that independent formulation.
                if(element is MassElement || element is LinearSpringElement || element is LinearGapElement)continue;
                double measure;
                if(element is FeElement1D)element.GetCG(checkedMesh.Nodes,out measure);
                else measure = element is ParabolicTetraElement
                    ? new LinearTetraElement(element.Id, element.NodeIds.Take(4).ToArray()).GetVolume(checkedMesh.Nodes)
                    : element is FeElement2D ? element.GetArea(FeFaceName.S2, checkedMesh.Nodes) : ((FeElement3D)element).GetVolume(checkedMesh.Nodes);
                if (!Finite(measure) || measure==0 || ((element is LinearTetraElement || element is ParabolicTetraElement) && measure<0))
                    throw new CaeException("Original element measure is zero, nonfinite or an inverted tetrahedron.");
            }
            foreach (string name in checkedMesh.NodeSets.Keys.Concat(checkedMesh.ElementSets.Keys)) Name(name);
            var materialList = materials.ToArray(); var sectionList = sections.ToArray();
            if (sectionList.Length == 0 || materialList.Length > 10000 || sectionList.Length > 10000)
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
            var sectionKeywords=new List<CalculixKeyword>();
            var rotationNodes=new HashSet<int>();
            var usedStructuralSections=new HashSet<string>();
            foreach (var section in sectionList)
            {
                if (section == null || (section.GetType()!=typeof(SolidSection) && section.GetType()!=typeof(ShellSection) && section.GetType()!=typeof(MembraneSection) && section.GetType()!=typeof(Section))) throw new CaeException("Unknown or null section.");
                Active(section); Name(section.Name);
                StructuralSectionData data=null;
                if(structuralSections!=null)structuralSections.TryGetValue(section.Name,out data);
                bool discrete=(data?.Kind == "mass" || data?.Kind == "spring" || data?.Kind == "gap");
                if(!discrete)Name(section.MaterialName);
                if (!sectionNames.Add(section.Name) || section.TwoD != twoD || section.RegionType != RegionTypeEnum.ElementSetName ||
                    section.CreationData != null || (section.CreationIds != null && section.CreationIds.Length != 0))
                    throw new NotSupportedException("Unique solid sections matching model dimensionality on named element sets are required.");
                if (twoD && (!Finite(section.Thickness.Value) || section.Thickness.Value <= 0)) throw new CaeException("Finite positive section thickness required.");
                if (!discrete && !materialNames.Contains(section.MaterialName)) throw new CaeException("Section refers to a missing material.");
                if(!discrete)usedMaterials.Add(section.MaterialName);
                var ids=Set(checkedMesh.ElementSets,section.RegionName);
                bool shell=section is ShellSection || data?.Kind=="composite", membrane=section is MembraneSection;
                foreach(int id in ids) {
                    string type=formulations[id];
                    bool matching=data?.Kind=="mass" ? type=="MASS" : data?.Kind=="spring" ? new[]{"SPRING1","SPRING2","SPRINGA"}.Contains(type) : data?.Kind=="gap" ? type=="GAPUNI" : data?.Kind=="beam" ? type.StartsWith("B",StringComparison.Ordinal) : data?.Kind=="truss" ? type.StartsWith("T",StringComparison.Ordinal) :
                        shell ? type.StartsWith("S",StringComparison.Ordinal) : membrane ? type.StartsWith("M3D",StringComparison.Ordinal) :
                        section is SolidSection && (twoD ? type.StartsWith(prefix,StringComparison.Ordinal) : type.StartsWith("C3D",StringComparison.Ordinal));
                    if(!matching)throw new CaeException("Section kind does not match every assigned element formulation.");
                    if(!coverage.Add(id))throw new CaeException("Element has overlapping sections.");
                    if(shell || data?.Kind=="beam")rotationNodes.UnionWith(checkedMesh.Elements[id].NodeIds);
                }
                if(data!=null) {
                    usedStructuralSections.Add(section.Name);
                    sectionKeywords.Add(discrete ? DiscreteKeyword(section,data,ids,checkedMesh,formulations) : StructuralKeyword(section,data,ids,checkedMesh,materialNames));
                    if(data.Kind=="composite")usedMaterials.UnionWith(data.LayerMaterials);
                }
                else if(section is ShellSection sh) { if(!Finite(sh.Thickness.Value)||sh.Thickness.Value<=0||!Finite(sh.Offset.Value))throw new CaeException("Finite shell thickness and offset required.");sectionKeywords.Add(SectionKeyword(sh)); }
                else if(section is MembraneSection mm) { if(!Finite(mm.Thickness.Value)||mm.Thickness.Value<=0||!Finite(mm.Offset.Value))throw new CaeException("Finite membrane thickness and offset required.");sectionKeywords.Add(SectionKeyword(mm)); }
                else if(section is SolidSection so)sectionKeywords.Add(SectionKeyword(so));
                else throw new CaeException("Unknown section kind.");
            }
            if(structuralSections!=null && !usedStructuralSections.SetEquals(structuralSections.Keys))throw new CaeException("Every advanced section control must be assigned exactly once.");
            if (!coverage.SetEquals(checkedMesh.Elements.Keys) || !usedMaterials.SetEquals(materialNames))
                throw new CaeException("Every element requires exactly one section and every supplied material must be used.");
            bool isStatic=step.GetType()==typeof(StaticStep),isFrequency=step.GetType()==typeof(FrequencyStep),isBuckling=step.GetType()==typeof(BuckleStep),isDynamic=step.GetType()==typeof(DynamicStep),isModal=step.GetType()==typeof(ModalDynamicsStep);
            bool timeDomain=isStatic || isDynamic || isModal;
            if(!timeDomain && !isFrequency && !isBuckling)throw new NotSupportedException("An exact original static, frequency or buckle step is required.");
            if(!timeDomain && (amplitudes.Count>0 || initialTemperature!=null || step.DefinedFields.Count>0 || step.Nlgeom || materialList.Any(m=>m.Properties.Any(p=>p is Plastic || p is ThermalExpansion))))throw new NotSupportedException("This eigenmode workflow requires linear elastic materials and linear geometry.");
            if((isDynamic || isModal) && (materialList.Any(m=>m.Properties.Any(p=>p is Plastic || p is ThermalExpansion)) || step.Nlgeom ||
                sectionList.Where(section=>usedMaterials.Contains(section.MaterialName)).Any(section=>!materialList.Single(m=>string.Equals(m.Name,section.MaterialName,StringComparison.OrdinalIgnoreCase)).Properties.Any(p=>p is Density))))
                throw new CaeException("Linear solid dynamics requires density and elasticity for every section; nonlinear/plastic dynamics remain pending.");
            if(isDynamic) {
                var d=(DynamicStep)step;
                if(!Finite(d.Alpha) || d.Alpha>0 || d.Alpha< -1d/3 || d.SolutionProcedure!=SolutionProcedureEnum.ImplicitImplicit || d.RelativeToAbsolute ||
                    d.Damping==null || !Enum.IsDefined(typeof(DampingTypeEnum),d.Damping.DampingType) || !Finite(d.Damping.Alpha) || d.Damping.Alpha<0 || !Finite(d.Damping.Beta) || d.Damping.Beta<0)
                    throw new CaeException("Valid original implicit dynamics and Rayleigh damping controls required.");
            }
            if(isModal) {
                var m=(ModalDynamicsStep)step;var d=m.ModalDamping;
                if(modalBasis==null || !modalBasis.Storage || modalBasis.NumOfFrequencies<1 || modalBasis.NumOfFrequencies>1000 || modalBasis.Loads.Count!=0 ||
                    modalBasis.Nlgeom || !modalBasis.RunAnalysis || modalBasis.Perturbation || modalBasis.GetNumberOfStepControls()!=0 || modalBasis.DefinedFields.Count!=0 || modalBasis.HistoryOutputs.Count!=0 ||
                    !double.IsNaN(modalBasis.LowerFrequency) || !double.IsNaN(modalBasis.UpperFrequency) || (modalBasis.OutputFrequency!=int.MinValue && modalBasis.OutputFrequency<=0) || modalBasis.SolverType!=SolverTypeEnum.Default || modalBasis.CyclicSymmetryModeMin!=int.MinValue || modalBasis.CyclicSymmetryModeMax!=int.MinValue ||
                    m.BoundaryConditions.Count!=0 || m.DefinedFields.Count!=0 || m.SteadyState || m.Perturbation || d==null ||
                    (d.DampingType != ModalDampingTypeEnum.Off && d.DampingType != ModalDampingTypeEnum.Constant && d.DampingType != ModalDampingTypeEnum.Rayleigh) ||
                    !Finite(d.Alpha) || d.Alpha<0 || !Finite(d.Beta) || d.Beta<0 || !Finite(d.ViscousDampingRatio) || d.ViscousDampingRatio<0 || d.ViscousDampingRatio>=1)
                    throw new CaeException("A stored ordinary frequency basis and supported modal transient controls required; modal BC changes are not allowed.");
                Active(modalBasis);Name(modalBasis.Name);
                if(string.Equals(modalBasis.Name,step.Name,StringComparison.OrdinalIgnoreCase))throw new CaeException("Distinct basis and modal step names required.");
                ValidateOutputs(checkedMesh,modalBasis);
            } else if(modalBasis!=null)throw new CaeException("A frequency basis applies only to modal dynamics.");
            if(isFrequency && (step.Loads.Count!=0 || sectionList.Where(section=>usedMaterials.Contains(section.MaterialName)).Any(section=>!materialList.Single(m=>string.Equals(m.Name,section.MaterialName,StringComparison.OrdinalIgnoreCase)).Properties.Any(p=>p is Density))))
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
            if(timeDomain) {
                var staticStep=(StaticStep)step;
            double[] times = { staticStep.TimePeriod, staticStep.InitialTimeIncrement, staticStep.MinTimeIncrement, staticStep.MaxTimeIncrement };
            if (times.Any(t => !Finite(t) || t <= 0) || staticStep.InitialTimeIncrement > staticStep.TimePeriod ||
                staticStep.InitialTimeIncrement > staticStep.MaxTimeIncrement || staticStep.MinTimeIncrement > staticStep.InitialTimeIncrement ||
                staticStep.MinTimeIncrement > staticStep.MaxTimeIncrement ||
                (staticStep.IncrementationType == IncrementationTypeEnum.Default &&
                 (staticStep.TimePeriod != 1 || staticStep.InitialTimeIncrement != 1 || staticStep.MinTimeIncrement != 1E-5 || staticStep.MaxTimeIncrement != 1E30)))
                throw new CaeException("Invalid static incrementation or custom values hidden by default incrementation.");
            }
            var supportStep=isModal?(Step)modalBasis:step;
            if (supportStep.BoundaryConditions.Count == 0 || supportStep.BoundaryConditions.Count > 10000 || step.Loads.Count > 10000)
                throw new CaeException("A bounded nonempty displacement constraint definition is required.");
            var constraints = new List<Tuple<DisplacementRotation, double[]>>();
            var constrained = new HashSet<Tuple<int,int>>();
            foreach (var entry in supportStep.BoundaryConditions)
            {
                var bc = entry.Value as DisplacementRotation;
                if (bc == null || bc.GetType()!=typeof(DisplacementRotation) || entry.Key != bc.Name) throw new NotSupportedException("Only named displacement constraints are supported.");
                Active(bc); Name(bc.Name);AnalysisModelExtensions.Reference(bc.AmplitudeName,amplitudes);
                if (bc.TwoD != twoD || bc.Complex || bc.PhaseDeg.Value != 0 ||
                    bc.CoordinateSystemName != CoordinateSystem.DefaultCoordinateSystemName ||
                    bc.DistributionName != Distribution.DefaultDistributionName || bc.CreationData != null ||
                    (bc.CreationIds != null && bc.CreationIds.Length != 0) || bc.RegionType != RegionTypeEnum.NodeSetName)
                    throw new NotSupportedException("Only constant global translational constraints on named node sets are supported.");
                var values = new[] { bc.U1.Value, bc.U2.Value, bc.U3.Value, bc.UR1.Value, bc.UR2.Value, bc.UR3.Value };
                if (values.All(double.IsNaN) || values.Any(double.IsInfinity) || (twoD && !double.IsNaN(values[2])) ||
                    (values.Skip(3).Any(v=>!double.IsNaN(v)) && Set(checkedMesh.NodeSets,bc.RegionName).Any(id=>!rotationNodes.Contains(id))))
                    throw new NotSupportedException("Provide finite translational constraints; free components use NaN. Rotations/fixed sentinels are unsupported.");
                foreach (int id in Set(checkedMesh.NodeSets, bc.RegionName))
                    for (int d = 0; d < 6; d++)
                        if (!double.IsNaN(values[d]) && !constrained.Add(Tuple.Create(id,d)))
                            throw new CaeException("Overlapping displacement definitions for one node/DOF are unsupported.");
                if(!isStatic && (bc.AmplitudeName!=Amplitude.DefaultAmplitudeName || values.Any(v=>!double.IsNaN(v) && v!=0)))throw new CaeException("Eigenmode and dynamic supports must be homogeneous zero displacement constraints.");
                constraints.Add(Tuple.Create(bc,values));
            }
            var loads = new List<CalculixKeyword>(); var loaded = new HashSet<Tuple<int,int>>();
            var densityElements = new HashSet<int>();
            foreach(var section in sectionList)
                if(usedMaterials.Contains(section.MaterialName) && materialList.Single(m=>string.Equals(m.Name,section.MaterialName,StringComparison.OrdinalIgnoreCase)).Properties.Any(p=>p is Density))
                    densityElements.UnionWith(Set(checkedMesh.ElementSets,section.RegionName));
            Dictionary<string,int> incidence=null;
            if(step.Loads.Values.OfType<DLoad>().Any(l=>l.RegionType==RegionTypeEnum.NodeSetName))
                incidence=mesh.Elements.Values.SelectMany(e=>Faces(e)).GroupBy(f=>FaceKey(f.Item2)).ToDictionary(g=>g.Key,g=>g.Count());
            int pressureIndex=0;
            foreach (var entry in step.Loads)
            {
                var source=entry.Value;
                if(source==null || entry.Key!=source.Name)throw new CaeException("A named mechanical load is required.");
                Active(source);Name(source.Name);AnalysisModelExtensions.Reference(source.AmplitudeName,amplitudes);
                if(source.TwoD != twoD || source.Complex || source.PhaseDeg.Value!=0 ||
                   source.CreationData!=null || (source.CreationIds!=null && source.CreationIds.Length!=0))
                    throw new NotSupportedException("Ordinary constant global mechanical loads on named regions are required.");
                if(source.GetType()==typeof(CLoad)) {
                    var load=(CLoad)source;
                    if(load.CoordinateSystemName!=CoordinateSystem.DefaultCoordinateSystemName || load.RegionType!=RegionTypeEnum.NodeSetName)
                        throw new NotSupportedException("Global concentrated forces require named node sets.");
                    var values=new[]{load.F1.Value,load.F2.Value,load.F3.Value};
                    if(values.Any(v=>!Finite(v)) || values.All(v=>v==0))throw new CaeException("Forces must be finite and nonzero.");
                    if(twoD && values[2]!=0)throw new CaeException("2D forces use F1/F2 only.");
                    foreach(int id in Set(checkedMesh.NodeSets,load.RegionName))for(int d=0;d<3;d++)
                        if(values[d]!=0 && !loaded.Add(Tuple.Create(id,d)))throw new CaeException("Overlapping concentrated loads for one node/DOF are unsupported.");
                    loads.Add(Invariant(()=>new CalCLoad(new CLoad(load.Name,load.RegionName,RegionTypeEnum.NodeSetName,values[0],values[1],values[2],twoD,false,0){AmplitudeName=load.AmplitudeName},null,ComplexLoadTypeEnum.None)));
                }
                else if(source.GetType()==typeof(MomentLoad)) {
                    var load=(MomentLoad)source;var values=new[]{load.M1.Value,load.M2.Value,load.M3.Value};
                    if(twoD || load.RegionType!=RegionTypeEnum.NodeSetName || load.CoordinateSystemName!=CoordinateSystem.DefaultCoordinateSystemName || values.Any(v=>!Finite(v)) || values.All(v=>v==0))throw new CaeException("Finite nonzero global nodal moments require a spatial structural model.");
                    foreach(int id in Set(checkedMesh.NodeSets,load.RegionName)) {
                        if(!rotationNodes.Contains(id))throw new CaeException("Moments require beam/shell nodes with rotational DOFs.");
                        for(int d=0;d<3;d++)if(values[d]!=0 && !loaded.Add(Tuple.Create(id,d+3)))throw new CaeException("Overlapping moment definitions.");
                    }
                    loads.Add(Invariant(()=>new CalMomentLoad(new MomentLoad(load.Name,load.RegionName,load.RegionType,values[0],values[1],values[2],false,false,0){AmplitudeName=load.AmplitudeName},null,ComplexLoadTypeEnum.None)));
                }
                else if(source.GetType()==typeof(GravityLoad)) {
                    var load=(GravityLoad)source;
                    if(load.RegionType!=RegionTypeEnum.ElementSetName)throw new NotSupportedException("Gravity requires a named element set.");
                    var values=new[]{load.F1.Value,load.F2.Value,load.F3.Value};
                    if(values.Any(v=>!Finite(v)) || values.All(v=>v==0))throw new CaeException("Gravity acceleration must be finite and nonzero.");
                    if(twoD && values[2]!=0)throw new CaeException("2D gravity uses in-plane acceleration only.");
                    if(Set(checkedMesh.ElementSets,load.RegionName).Any(id=>!densityElements.Contains(id)))throw new CaeException("Every gravity-loaded element requires a material density.");
                    loads.Add(Invariant(()=>new CalGravityLoad(new GravityLoad(load.Name,load.RegionName,RegionTypeEnum.ElementSetName,values[0],values[1],values[2],twoD,false,0){AmplitudeName=load.AmplitudeName},ComplexLoadTypeEnum.None)));
                }
                else if(source.GetType()==typeof(DLoad)) {
                    var load=(DLoad)source;double magnitude=load.Magnitude.Value;
                    if(!Finite(magnitude) || load.DistributionName!=Distribution.DefaultDistributionName)
                        throw new CaeException("Pressure must be finite and constant over its selected region.");
                    var targets=new List<Tuple<int,FeFaceName,int[]>>();
                    if(load.RegionType==RegionTypeEnum.NodeSetName) {
                        if(!twoD && mesh.Elements.Values.Any(e=>e is FeElement2D))throw new CaeException("Shell/membrane normal pressure requires an explicit element-set side S1 or S2.");
                        var nodes=new HashSet<int>(Set(mesh.NodeSets,load.RegionName));
                        foreach(var e in mesh.Elements.Values)foreach(var face in Faces(e))
                            if(incidence[FaceKey(face.Item2)]==1 && face.Item2.All(nodes.Contains))targets.Add(Tuple.Create(e.Id,face.Item1,face.Item2));
                    } else if(load.RegionType==RegionTypeEnum.ElementSetName) {
                        if((int)load.ElementFaceName<1 || (int)load.ElementFaceName>6)throw new CaeException("An original element face S1–S6 is required.");
                        foreach(int id in Set(mesh.ElementSets,load.RegionName)) {
                            var faces=Faces(mesh.Elements[id],!twoD).Where(f=>f.Item1==load.ElementFaceName).ToArray();
                            if(faces.Length!=1)throw new CaeException("Selected face does not exist on every pressure-loaded element.");
                            targets.Add(Tuple.Create(id,load.ElementFaceName,faces[0].Item2));
                        }
                    } else throw new NotSupportedException("Pressure requires a boundary node set or explicit element-set face.");
                    if(targets.Count==0)throw new CaeException("Pressure region contains no complete exterior element faces.");
                    var groups=new Dictionary<FeFaceName,HashSet<int>>();
                    foreach(var target in targets) {
                        // Original face node identities determine correspondence even
                        // when original CalElement collapses a pyramid for the solver.
                        var matches=Faces(checkedMesh.Elements[target.Item1],!twoD).Where(f=>FaceKey(f.Item2)==FaceKey(target.Item3) && (!(checkedMesh.Elements[target.Item1] is FeElement2D) || twoD || f.Item1==target.Item2)).ToArray();
                        if(matches.Length!=1)throw new CaeException("Original pressure face correspondence was lost during solver export.");
                        var face=matches[0].Item1;
                        if(!groups.ContainsKey(face))groups.Add(face,new HashSet<int>());
                        groups[face].Add(target.Item1);
                    }
                    var surface=new FeSurface(load.Name){Type=FeSurfaceType.Element,SurfaceFaceTypes=targets.All(t=>checkedMesh.Elements[t.Item1] is FeElement2D) && !twoD ? FeSurfaceFaceTypes.ShellFaces : FeSurfaceFaceTypes.SolidFaces};
                    foreach(var group in groups.OrderBy(g=>g.Key)) {
                        string name;
                        do{name="_XPressure_"+(++pressureIndex);}while(checkedMesh.ElementSets.Keys.Any(n=>string.Equals(n,name,StringComparison.OrdinalIgnoreCase)));
                        checkedMesh.ElementSets.Add(name,group.Value.OrderBy(id=>id).ToArray());surface.AddElementFace(group.Key,name);
                    }
                    var snapshot=Invariant(()=>new DLoad(load.Name,load.RegionName,load.RegionType,magnitude,twoD,false,0){AmplitudeName=load.AmplitudeName});
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
                if(structural) {
                    int omittedDiscrete=checkedMesh.Elements.Values.Count(e=>e is MassElement || e is LinearSpringElement && e.NodeIds.Length==1);
                    int expandedCount=sectionList.Sum(section=>Set(checkedMesh.ElementSets,section.RegionName).Count(id=>!(checkedMesh.Elements[id] is MassElement) && !(checkedMesh.Elements[id] is LinearSpringElement && checkedMesh.Elements[id].NodeIds.Length==1)) *
                        (structuralSections!=null && structuralSections.TryGetValue(section.Name,out var layered) && layered.Kind=="composite" ? layered.LayerMaterials.Length : 1));
                    text.Append("*Heading\nModel space: ThreeD\nPrePoMax-X element counts: ").Append(checkedMesh.Elements.Count).Append(",").Append(expandedCount).Append('\n');
                    if(omittedDiscrete>0)text.Append("PrePoMax-X omitted discrete: ").Append(omittedDiscrete).Append('\n');
                }
                if(twoD) { text.Clear(); text.Append("** PrePoMax-X ").Append(modelSpace).Append(" static analysis deck\n*Heading\nModel space: ").Append(modelSpace).Append('\n'); }
                text.Append(twoD ? CalNodeFormatting.Write2D(checkedMesh.Nodes) : CalNodeFormatting.Write3D(checkedMesh.Nodes));
                text.Append(meshText.Substring(elementsAt));
                foreach (string value in materialText) text.Append(value);
                foreach (var keyword in sectionKeywords) Append(text, keyword);
                AnalysisModelExtensions.WriteAmplitudes(text,amplitudes);
                AnalysisModelExtensions.WriteMechanicalInitial(text,checkedMesh,initialTemperature);
                if(isModal) {
                    Append(text,new CalStepHeader(modalBasis));Append(text,new CalFrequencyStep(modalBasis));
                    foreach(var item in constraints)Append(text,new CalDisplacementRotation(item.Item1,null,null,ComplexLoadTypeEnum.None));
                    // Original CalculiX ccx_2.22step.c requires the same point-load
                    // DOFs to be present at zero magnitude in the stored basis
                    // for expanded 1D/2D nodes. CalCLoad intentionally omits zero
                    // components, so retain them through its original user-keyword route.
                    if(checkedMesh.Elements.Values.Any(e=>e is FeElement1D || e is FeElement2D) && loaded.Count>0) {
                        var zero=new StringBuilder("*Cload\n");
                        foreach(var dof in loaded.OrderBy(v=>v.Item1).ThenBy(v=>v.Item2))zero.Append(dof.Item1).Append(", ").Append(dof.Item2+1).Append(", 0\n");
                        Append(text,new CalculixUserKeyword(zero.ToString()));
                    }
                    foreach(var output in modalBasis.FieldOutputs.Values) {
                        if(output is NodalFieldOutput nf)Append(text,new CalNodeFile(nf,modalBasis.OutputFrequency));
                        else Append(text,new CalElFile((ElementFieldOutput)output,modalBasis.OutputFrequency));
                    }
                    Append(text,new CalEndStep());
                }
                Append(text, new CalStepHeader(step));
                if(isStatic)Append(text,new CalStaticStep((StaticStep)step));
                else if(isDynamic)Append(text,new CalDynamicStep((DynamicStep)step));
                else if(isModal)Append(text,new CalModalDynamicsStep((ModalDynamicsStep)step,false));
                else if(isFrequency)Append(text,new CalFrequencyStep((FrequencyStep)step));
                else Append(text,new CalBuckleStep((BuckleStep)step));
                if(isDynamic && ((DynamicStep)step).Damping.DampingType!=DampingTypeEnum.Off)Append(text,new CalDamping(((DynamicStep)step).Damping));
                if(isModal && ((ModalDynamicsStep)step).ModalDamping.DampingType!=ModalDampingTypeEnum.Off)Append(text,new CalModalDamping(((ModalDynamicsStep)step).ModalDamping));
                foreach (var item in isModal?new List<Tuple<DisplacementRotation,double[]>>():constraints)
                {
                    var source = item.Item1; var v = item.Item2;
                    var snapshot = new DisplacementRotation(source.Name, source.RegionName, RegionTypeEnum.NodeSetName, twoD, false, 0);
                    snapshot.AmplitudeName=source.AmplitudeName;
                    snapshot.U1.SetEquationFromValue(v[0]); snapshot.U2.SetEquationFromValue(v[1]); snapshot.U3.SetEquationFromValue(v[2]);
                    snapshot.UR1.SetEquationFromValue(v[3]);snapshot.UR2.SetEquationFromValue(v[4]);snapshot.UR3.SetEquationFromValue(v[5]);
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
        private static IEnumerable<Tuple<FeFaceName,int[]>> Faces(FeElement element, bool normalFaces=false)
        {
            if(element is FeElement1D || element is FeElement0D)yield break;
            for(int i=element is FeElement2D ? (normalFaces ? 1 : 3) : 1;i<=(element is FeElement2D && normalFaces ? 2 : 6);i++) {
                int[] ids;
                try { ids=element.GetNodeIdsFromFaceName((FeFaceName)i); }
                catch(NotSupportedException) { continue; }
                if(ids.Distinct().Count()>=(element is FeElement2D ? 2 : 3))yield return Tuple.Create((FeFaceName)i,ids);
            }
        }

        private static CalculixKeyword DiscreteKeyword(Section section,StructuralSectionData data,int[] ids,InpMeshData mesh,Dictionary<int,string> types)
        {
            if(data.Kind=="mass") {
                if(!data.Mass.HasValue || !Finite(data.Mass.Value) || data.Mass<=0 || data.Stiffness.HasValue || data.Clearance.HasValue || data.TensileForce.HasValue || data.Dof!=0 || data.SecondDof!=0 || data.Direction!=null)throw new CaeException("Positive mass and no spring/gap controls required.");
                return new CalMassSection(new MassSectionData(section.Name,section.RegionName,data.Mass.Value));
            }
            if(data.Mass.HasValue || !data.Stiffness.HasValue || !Finite(data.Stiffness.Value) || data.Stiffness<=0)throw new CaeException("Positive finite spring/gap stiffness required.");
            if(data.Kind=="spring") {
                if(data.Clearance.HasValue || data.TensileForce.HasValue || data.Direction!=null)throw new CaeException("Spring section has no gap controls.");
                foreach(int id in ids) {
                    string type=types[id];
                    if(type=="SPRINGA" ? data.Dof!=0 || data.SecondDof!=0 : data.Dof<1 || data.Dof>3 || (type=="SPRING2" ? data.SecondDof<1 || data.SecondDof>3 : data.SecondDof!=0))throw new CaeException("SPRING1 requires DOF 1–3; SPRING2 requires two DOFs 1–3; SPRINGA uses its nodal axis.");
                    if(type=="SPRINGA" && mesh.Elements[id].NodeIds.Select(n=>mesh.Nodes[n]).Select(n=>new[]{n.X,n.Y,n.Z}).Distinct(new CoordinateComparer()).Count()<2)throw new CaeException("Axial spring nodes must be separated.");
                }
                return new CalLinearSpringSection(new LinearSpringSectionData(section.Name,section.RegionName,data.Dof,data.SecondDof,data.Stiffness.Value));
            }
            if(!data.Clearance.HasValue || !Finite(data.Clearance.Value) || data.Direction==null || data.Direction.Length!=3 || data.Direction.Any(v=>!Finite(v)) || (!Finite(data.Direction.Sum(v=>v*v)) || data.Direction.Sum(v=>v*v)<1e-30) || data.Dof!=0 || data.SecondDof!=0 || data.TensileForce.HasValue && (!Finite(data.TensileForce.Value) || data.TensileForce<0))throw new CaeException("Gap requires finite clearance, nonzero direction and nonnegative optional tensile force.");
            return new CalGapSection(new GapSectionData(section.Name,section.RegionName,data.Clearance.Value,(double[])data.Direction.Clone(),data.Stiffness.Value,data.TensileForce??double.NaN));
        }
        private sealed class CoordinateComparer : IEqualityComparer<double[]> {
            public bool Equals(double[] a,double[] b)=>a.SequenceEqual(b);
            public int GetHashCode(double[] a)=>0;
        }
        private static T Invariant<T>(Func<T> create)
        {
            var previous=CultureInfo.CurrentCulture;
            try { CultureInfo.CurrentCulture=CultureInfo.InvariantCulture;return create(); }
            finally { CultureInfo.CurrentCulture=previous; }
        }
        private static CalculixKeyword SectionKeyword(Section source)
        {
            // Evaluate original objects in their caller's culture, then freeze
            // numeric values in the invariant job-owned keyword objects.
            double thickness=source.Thickness.Value;
            double offset=source is ShellSection sh ? sh.Offset.Value : source is MembraneSection mm ? mm.Offset.Value : 0;
            return Invariant<CalculixKeyword>(()=> {
                if(source is ShellSection) {
                    var section=new ShellSection(source.Name,source.MaterialName,source.RegionName,source.RegionType,thickness,source.TwoD);
                    section.Offset.SetEquationFromValue(offset);return new CalShellSection(section);
                }
                if(source is MembraneSection) {
                    var section=new MembraneSection(source.Name,source.MaterialName,source.RegionName,source.RegionType,thickness,source.TwoD);
                    section.Offset.SetEquationFromValue(offset);return new CalMembraneSection(section);
                }
                return new CalSolidSection(new SolidSection(source.Name,source.MaterialName,source.RegionName,source.RegionType,thickness,source.TwoD));
            });
        }

        private static CalculixKeyword StructuralKeyword(Section section,StructuralSectionData data,int[] ids,InpMeshData mesh,HashSet<string> materials)
        {
            var previous=CultureInfo.CurrentCulture;
            try {
            CultureInfo.CurrentCulture=CultureInfo.InvariantCulture;
            var text=new StringBuilder();
            if(data.Kind=="beam" || data.Kind=="truss") {
                if(data.LayerMaterials!=null || data.LayerThicknesses!=null || data.Dimensions==null || data.Dimensions.Any(v=>!Finite(v)||v<=0))throw new CaeException("Explicit finite positive line section dimensions required.");
                if(data.Kind=="truss") {
                    if(data.Dimensions.Length!=1 || data.Direction!=null || data.Offset!=0)throw new CaeException("Truss sections require only one positive area.");
                    text.AppendFormat(CultureInfo.InvariantCulture,"*Solid section, Elset={0}, Material={1}\n{2}\n",section.RegionName,section.MaterialName,data.Dimensions[0].ToCalculiX16String());
                } else {
                    if((data.Shape != "RECT" && data.Shape != "CIRC") || data.Dimensions.Length!=2 || data.Direction==null || data.Direction.Length!=3 || data.Direction.Any(v=>!Finite(v)) || data.Direction.All(v=>v==0) || data.Offset!=0)throw new CaeException("RECT/CIRC beam section requires two dimensions and a finite nonzero direction.");
                    foreach(int id in ids) {
                        var element=mesh.Elements[id];var a=mesh.Nodes[element.NodeIds[0]];var b=mesh.Nodes[element.NodeIds[element.NodeIds.Length==3?2:1]];
                        var v=new[]{b.X-a.X,b.Y-a.Y,b.Z-a.Z};var n=data.Direction;
                        if(v[1]*n[2]-v[2]*n[1]==0 && v[2]*n[0]-v[0]*n[2]==0 && v[0]*n[1]-v[1]*n[0]==0)throw new CaeException("Beam section direction cannot be parallel to an element axis.");
                    }
                    text.AppendFormat(CultureInfo.InvariantCulture,"*Beam section, Elset={0}, Material={1}, Section={2}\n{3}, {4}\n{5}, {6}, {7}\n",section.RegionName,section.MaterialName,data.Shape,
                        data.Dimensions[0].ToCalculiX16String(),data.Dimensions[1].ToCalculiX16String(),data.Direction[0].ToCalculiX16String(),data.Direction[1].ToCalculiX16String(),data.Direction[2].ToCalculiX16String());
                }
            } else if(data.Kind=="composite") {
                if(data.LayerMaterials==null || data.LayerThicknesses==null || data.LayerMaterials.Length<1 || data.LayerMaterials.Length>100 || !data.LayerMaterials.Contains(section.MaterialName,StringComparer.OrdinalIgnoreCase) || data.LayerMaterials.Length!=data.LayerThicknesses.Length || data.LayerThicknesses.Any(v=>!Finite(v)||v<=0) || !Finite(data.Offset) || data.Dimensions!=null || data.Direction!=null)throw new CaeException("Bounded finite positive composite layers required.");
                if(ids.Any(id=> { string type=mesh.ElementBlocks.Single(b=>b.ElementLabels.Contains(id)).InpElementTypeNames.Single(); return type != "S8R" && type != "S6"; }))throw new CaeException("Original CalculiX composite sections require S8R/S6 elements.");
                text.AppendFormat(CultureInfo.InvariantCulture,"*Shell section, Elset={0}, Composite, Offset={1}\n",section.RegionName,data.Offset.ToCalculiX16String());
                for(int i=0;i<data.LayerMaterials.Length;i++) { Name(data.LayerMaterials[i]);if(!materials.Contains(data.LayerMaterials[i]))throw new CaeException("Missing layer material.");text.Append(data.LayerThicknesses[i].ToCalculiX16String()).Append(", , ").Append(data.LayerMaterials[i]).Append('\n'); }
            } else throw new CaeException("Unknown advanced section kind.");
            return new CalculixUserKeyword(text.ToString().TrimEnd('\n'));
            } finally { CultureInfo.CurrentCulture=previous; }
        }

        internal static void ValidateOutputs(InpMeshData mesh, Step step)
        {
            if (step.FieldOutputs.Count == 0 || step.FieldOutputs.Count > 100 || step.HistoryOutputs.Count > 100)
                throw new CaeException("Bounded nonempty field outputs are required.");
            bool thermal=step is HeatTransferStep;bool dynamics=step is DynamicStep || step is ModalDynamicsStep;
            foreach (var item in step.FieldOutputs)
            {
                var value=item.Value; Active(value); Name(value.Name);
                if (item.Key != value.Name || value.LastIterations || value.ContactElements || !value.Global)
                    throw new NotSupportedException("Only ordinary global field output is supported.");
                if (value.GetType()==typeof(NodalFieldOutput))
                {
                    var flags=((NodalFieldOutput)value).Variables;
                    if (flags==0 || (flags & ~(thermal ? NodalFieldVariable.NT | NodalFieldVariable.RFL : NodalFieldVariable.U | NodalFieldVariable.RF | (dynamics?NodalFieldVariable.V:0)))!=0) throw new NotSupportedException("Only U/RF nodal output is supported.");
                }
                else if (value.GetType()==typeof(ElementFieldOutput))
                {
                    var output=(ElementFieldOutput)value;
                    if (!Enum.IsDefined(typeof(ElementFieldOutputOutputEnum),output.Output) || output.Variables==0 ||
                        (output.Variables & ~(thermal ? ElementFieldVariable.HFL : ElementFieldVariable.E | ElementFieldVariable.S | ElementFieldVariable.PEEQ | (dynamics?ElementFieldVariable.ENER:0)))!=0) throw new NotSupportedException("Only ordinary E/S/PEEQ solid output is supported.");
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
                    if (value.RegionType!=RegionTypeEnum.NodeSetName || flags==0 || (flags & ~(thermal ? NodalHistoryVariable.NT | NodalHistoryVariable.RFL : NodalHistoryVariable.U | NodalHistoryVariable.RF | (dynamics?NodalHistoryVariable.V:0)))!=0)
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

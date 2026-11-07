// PrePoMax-X thermal integration. Original engineering objects and keywords stay
// in CaeModel; no thermal element, integration, or solver algorithm is replaced.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using CaeGlobals;
using CaeMesh;
using FileInOut.Input;
using FileInOut.Output.Calculix;

namespace CaeModel
{
    public static class ThermalAnalysisDeckWriter
    {
        public static string Write(InpMeshData source, Material[] materials, SolidSection[] sections,
                                   HeatTransferStep step, string initialTemperature)
        {
            if(source==null || materials==null || sections==null || step==null)throw new ArgumentNullException();
            if(source.OmittedKeywords.Length!=0 || source.Warnings.Length!=0)
                throw new CaeException("Thermal analysis requires a standalone mesh without omitted model keywords or reader warnings.");
            var mesh=InpFileReader.ReadMeshData(MeshDeckWriter.WriteMesh(source).Replace("\r", "").Split('\n'));
            if(mesh.ElementBlocks.Any(b=>b.InpElementTypeNames.Any(t=>StaticAnalysisDeckWriter.CompatibleSolidFormulations(t).Length==0)) ||
                mesh.Elements.Values.Any(e=>e is LinearPyramidElement || e is ParabolicPyramidElement))
                throw new NotSupportedException("Heat transfer currently requires original tetrahedron, wedge or hexahedron solid meshes.");
            foreach(var e in mesh.Elements.Values) {
                double volume=e is ParabolicTetraElement ? new LinearTetraElement(e.Id,e.NodeIds.Take(4).ToArray()).GetVolume(mesh.Nodes) : ((FeElement3D)e).GetVolume(mesh.Nodes);
                if(!Finite(volume) || volume==0 || ((e is LinearTetraElement || e is ParabolicTetraElement) && volume<0))
                    throw new CaeException("Zero, nonfinite or inverted solid mesh.");
            }
            foreach(string name in mesh.NodeSets.Keys.Concat(mesh.ElementSets.Keys))Name(name);
            if(materials.Length==0 || sections.Length==0 || materials.Length>1000 || sections.Length>1000)
                throw new CaeException("Bounded thermal materials and solid sections required.");
            var names=new HashSet<string>(StringComparer.OrdinalIgnoreCase);var materialKeywords=new List<CalculixKeyword>();
            foreach(var m in materials) {
                Active(m);Name(m.Name);
                if(m.GetType()!=typeof(Material) || !names.Add(m.Name) || m.TemperatureDependent ||
                    m.Properties.Any(p=>p==null || (p.GetType()!=typeof(ThermalConductivity) && p.GetType()!=typeof(SpecificHeat) && p.GetType()!=typeof(Density))) ||
                    m.Properties.OfType<ThermalConductivity>().Count()!=1 || m.Properties.OfType<SpecificHeat>().Count()>1 || m.Properties.OfType<Density>().Count()>1)
                    throw new CaeException("One constant isotropic conductivity, optional density and specific heat required per thermal material.");
                materialKeywords.Add(new CalMaterial(m));
                double k=Property(m.Properties.OfType<ThermalConductivity>().Single().ThermalConductivityTemp);
                materialKeywords.Add(new CalThermalConductivity(new ThermalConductivity(new[]{new[]{k,0d}}),false));
                var density=m.Properties.OfType<Density>().SingleOrDefault();var heat=m.Properties.OfType<SpecificHeat>().SingleOrDefault();
                if(!step.SteadyState && (density==null || heat==null))throw new CaeException("Transient heat transfer requires density and specific heat in every material.");
                if(density!=null)materialKeywords.Add(new CalDensity(new Density(new[]{new[]{Property(density.DensityTemp),0d}}),false));
                if(heat!=null)materialKeywords.Add(new CalSpecificHeat(new SpecificHeat(new[]{new[]{Property(heat.SpecificHeatTemp),0d}}),false));
            }
            var coverage=new HashSet<int>();var used=new HashSet<string>(StringComparer.OrdinalIgnoreCase);var sectionNames=new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach(var s in sections) {
                Active(s);Name(s.Name);Name(s.MaterialName);
                if(s.GetType()!=typeof(SolidSection) || !sectionNames.Add(s.Name) || s.TwoD || s.RegionType!=RegionTypeEnum.ElementSetName ||
                    s.CreationData!=null || s.CreationIds?.Length>0 || !names.Contains(s.MaterialName))throw new CaeException("Unique named solid sections and existing thermal materials required.");
                used.Add(s.MaterialName);
                foreach(int id in Set(mesh.ElementSets,s.RegionName))if(!coverage.Add(id))throw new CaeException("Overlapping solid sections.");
            }
            if(!coverage.SetEquals(mesh.Elements.Keys) || !used.SetEquals(names))throw new CaeException("Every element requires exactly one section; every material must be used.");
            Active(step);Name(step.Name);
            double[] times={step.TimePeriod,step.InitialTimeIncrement,step.MinTimeIncrement,step.MaxTimeIncrement};
            if(step.GetType()!=typeof(HeatTransferStep) || !step.RunAnalysis || step.Nlgeom || step.Perturbation || step.SolverType!=SolverTypeEnum.Default ||
                step.DefinedFields.Count!=0 || step.GetNumberOfStepControls()!=0 || step.MaxIncrements<1 || step.OutputFrequency<1 ||
                step.IncrementationType is not (IncrementationTypeEnum.Automatic or IncrementationTypeEnum.Direct) ||
                times.Any(t=>!Finite(t)||t<=0) || step.InitialTimeIncrement>step.TimePeriod || step.InitialTimeIncrement>step.MaxTimeIncrement ||
                step.MinTimeIncrement>step.InitialTimeIncrement || step.MinTimeIncrement>step.MaxTimeIncrement ||
                (!double.IsPositiveInfinity(step.Deltmx) && (!Finite(step.Deltmx)||step.Deltmx<=0)))
                throw new CaeException("Valid original heat-transfer time controls and linear geometry required.");
            if(step.Loads.Count>1000 || step.BoundaryConditions.Count>1000)throw new CaeException("Thermal load/BC limit exceeded.");
            var boundaries=new List<CalculixKeyword>();var constrained=new HashSet<int>();
            foreach(var entry in step.BoundaryConditions) {
                var bc=entry.Value as TemperatureBC;Active(bc);
                if(bc.GetType()!=typeof(TemperatureBC) || entry.Key!=bc.Name || bc.TwoD || bc.Complex || bc.PhaseDeg.Value!=0 ||
                    bc.AmplitudeName!=Amplitude.DefaultAmplitudeName || bc.RegionType!=RegionTypeEnum.NodeSetName ||
                    bc.DistributionName!=Distribution.DefaultDistributionName || bc.CreationData!=null || bc.CreationIds?.Length>0 || !Finite(bc.Temperature.Value))
                    throw new CaeException("Constant finite temperatures on named node sets required.");
                Name(bc.Name);
                foreach(int id in Set(mesh.NodeSets,bc.RegionName))if(!constrained.Add(id))throw new CaeException("Overlapping temperature boundary conditions.");
                boundaries.Add(new CalTemperatureBC(bc,null));
            }
            var surfaces=new List<CalculixKeyword>();var loads=new List<CalculixKeyword>();int serial=0;bool film=false;
            var nodalLoads=new HashSet<int>();var bodyLoads=new HashSet<int>();var facesLoaded=new HashSet<string>();
            string DerivedName() {string n;do{n="_XThermal_"+(++serial);}while(mesh.NodeSets.Keys.Concat(mesh.ElementSets.Keys).Any(v=>string.Equals(v,n,StringComparison.OrdinalIgnoreCase)));return n;}
            var incidence=mesh.Elements.Values.SelectMany(e=>Faces((FeElement3D)e)).GroupBy(f=>Key(f.Item2)).ToDictionary(g=>g.Key,g=>g.Count());
            foreach(var entry in step.Loads) {
                var load=entry.Value;Active(load);Name(load.Name);
                if(entry.Key!=load.Name || load.TwoD || load.Complex || load.PhaseDeg.Value!=0 || load.AmplitudeName!=Amplitude.DefaultAmplitudeName ||
                    load.CreationData!=null || load.CreationIds?.Length>0)throw new CaeException("Ordinary constant thermal loads required.");
                if(load.GetType()==typeof(CFlux)) {
                    var f=(CFlux)load;
                    if(f.RegionType!=RegionTypeEnum.NodeSetName || f.AddFlux || !Finite(f.Magnitude.Value))throw new CaeException("Finite nodal power on named node sets required.");
                    foreach(int id in Set(mesh.NodeSets,f.RegionName)) {
                        if(constrained.Contains(id))throw new CaeException("Nodal power on a prescribed-temperature node is unsupported; it cannot heat a free thermal DOF.");
                        if(!nodalLoads.Add(id))throw new CaeException("Overlapping nodal heat loads.");
                    }
                    loads.Add(new CalCFlux(f));
                } else if(load.GetType()==typeof(BodyFlux)) {
                    var f=(BodyFlux)load;
                    if(f.RegionType!=RegionTypeEnum.ElementSetName || !Finite(f.Magnitude.Value))throw new CaeException("Finite heat generation on named element sets required.");
                    foreach(int id in Set(mesh.ElementSets,f.RegionName))if(!bodyLoads.Add(id))throw new CaeException("Overlapping body heat loads.");
                    loads.Add(new CalBodyFlux(f));
                } else if(load.GetType()==typeof(DFlux) || load.GetType()==typeof(FilmHeatTransfer)) {
                    if(load.RegionType!=RegionTypeEnum.NodeSetName)throw new CaeException("Choose a boundary node set containing complete exterior faces.");
                    var nodes=new HashSet<int>(Set(mesh.NodeSets,load.RegionName));
                    var targets=mesh.Elements.Values.SelectMany(e=>Faces((FeElement3D)e).Where(f=>incidence[Key(f.Item2)]==1 && f.Item2.All(nodes.Contains)).Select(f=>Tuple.Create(e.Id,f.Item1,f.Item2))).ToArray();
                    if(targets.Length==0)throw new CaeException("No complete exterior faces in the thermal boundary region.");
                    var surface=new FeSurface(DerivedName()){Type=FeSurfaceType.Element,SurfaceFaceTypes=FeSurfaceFaceTypes.SolidFaces};
                    foreach(var target in targets)if(!facesLoaded.Add(load.GetType().Name+":"+target.Item1+":"+target.Item2))throw new CaeException("Overlapping thermal face loads of the same kind.");
                    foreach(var group in targets.GroupBy(t=>t.Item2).OrderBy(g=>g.Key)) {
                        string n=DerivedName();mesh.ElementSets.Add(n,group.Select(t=>t.Item1).OrderBy(i=>i).ToArray());surface.AddElementFace(group.Key,n);
                    }
                    if(load is DFlux flux) {
                        if(!Finite(flux.Magnitude.Value))throw new CaeException("Finite surface heat flux required.");
                        surfaces.Add(new CalSurface(surface,false));
                        loads.Add(new CalDFlux(new DFlux(flux.Name,surface.Name,RegionTypeEnum.SurfaceName,flux.Magnitude.Value,false)));
                    } else {
                        var f=(FilmHeatTransfer)load;
                        if(!Finite(f.SinkTemperature.Value) || !Finite(f.FilmCoefficient.Value) || f.FilmCoefficient.Value<=0 || f.CoefficientAmplitudeName!=Amplitude.DefaultAmplitudeName)
                            throw new CaeException("Finite sink temperature and positive film coefficient required.");
                        film=true;loads.Add(new CalFilmHeatTransfer(f,surface));
                    }
                } else throw new NotSupportedException("Unsupported thermal load type.");
            }
            if(step.SteadyState && constrained.Count==0 && !film)throw new CaeException("Steady conduction requires a prescribed temperature or convection to a sink.");
            InitialTemperature initial=null;
            if(initialTemperature!=null) {
                string n=DerivedName();mesh.NodeSets.Add(n,mesh.Nodes.Keys.OrderBy(i=>i).ToArray());
                initial=new InitialTemperature("Initial-temperature",n,RegionTypeEnum.NodeSetName,0);
                initial.Temperature.SetEquation(initialTemperature);
                if(!Finite(initial.Temperature.Value))throw new CaeException("Finite initial temperature required.");
            } else if(!step.SteadyState)throw new CaeException("Explicit uniform initial temperature required for transient heat transfer.");
            StaticAnalysisDeckWriter.ValidateOutputs(mesh,step);
            var previous=CultureInfo.CurrentCulture;
            try {
                CultureInfo.CurrentCulture=CultureInfo.InvariantCulture;
                string meshText=MeshDeckWriter.WriteMesh(mesh);var text=new StringBuilder("** PrePoMax-X original solid heat-transfer analysis\n");
                text.Append(CalNodeFormatting.Write3D(mesh.Nodes)).Append(meshText.Substring(meshText.IndexOf("*Element",StringComparison.Ordinal)));
                foreach(var k in materialKeywords)Append(text,k);
                foreach(var s in sections)Append(text,new CalSolidSection(s));
                foreach(var k in surfaces)Append(text,k);
                if(initial!=null)Append(text,new CalInitialTemperature(initial));
                Append(text,new CalStepHeader(step));Append(text,new CalHeatTransferStep(step));
                foreach(var k in boundaries.Concat(loads))Append(text,k);
                Append(text,new CalOutputFrequency(step.OutputFrequency));
                foreach(var h in step.HistoryOutputs.Values) {
                    if(h is NodalHistoryOutput n)Append(text,new CalNodePrint(n,n.RegionName,step.OutputFrequency));
                    else Append(text,new CalElPrint((ElementHistoryOutput)h,step.OutputFrequency));
                }
                foreach(var f in step.FieldOutputs.Values) {
                    if(f is NodalFieldOutput n)Append(text,new CalNodeFile(n,step.OutputFrequency));
                    else Append(text,new CalElFile((ElementFieldOutput)f,step.OutputFrequency));
                }
                Append(text,new CalEndStep());return text.ToString();
            } finally {CultureInfo.CurrentCulture=previous;}
        }
        private static double Property(EquationContainer[][] rows) {
            if(rows==null || rows.Length!=1 || rows[0]==null || rows[0].Length!=2 || rows[0].Any(v=>v==null) ||
                rows[0].Any(v=>!Finite(v.Value)) || rows[0][0].Value<=0)throw new CaeException("One finite positive temperature-independent thermal property row required.");
            return rows[0][0].Value;
        }
        private static IEnumerable<Tuple<FeFaceName,int[]>> Faces(FeElement3D e) {
            for(int i=1;i<=6;i++){int[] ids;try{ids=e.GetNodeIdsFromFaceName((FeFaceName)i);}catch(NotSupportedException){continue;}if(ids.Distinct().Count()>=3)yield return Tuple.Create((FeFaceName)i,ids);}
        }
        private static string Key(IEnumerable<int> ids) {return string.Join(",",ids.Distinct().OrderBy(i=>i));}
        private static int[] Set(Dictionary<string,int[]> sets,string name) {
            Name(name);var matches=sets.Keys.Where(n=>string.Equals(n,name,StringComparison.OrdinalIgnoreCase)).ToArray();
            if(matches.Length!=1 || sets[matches[0]]==null || sets[matches[0]].Length==0)throw new CaeException("Missing or empty thermal region: "+name);
            return sets[matches[0]];
        }
        private static void Name(string n) {StaticAnalysisDeckWriter.Name(n);}
        private static void Active(NamedClass n) {if(n==null || !n.Active || !n.Valid)throw new CaeException("Active valid thermal objects required.");}
        private static bool Finite(double v) {return !double.IsNaN(v) && !double.IsInfinity(v);}
        private static void Append(StringBuilder t,CalculixKeyword k) {t.Append(k.GetKeywordString()).Append(k.GetDataString());}
    }
}

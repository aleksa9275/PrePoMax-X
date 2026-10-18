using System.Globalization;
using System.Runtime.InteropServices;
using System.Runtime.Serialization;
using System.Text.Json;
using CaeGlobals;
using CaeMesh;
using CaeModel;
using FileInOut.Input;
using PrePoMaxX.StaticDeck;
using PrePoMaxX.MeshDeck;

CultureInfo.CurrentCulture=CultureInfo.InvariantCulture;
CultureInfo.CurrentUICulture=CultureInfo.InvariantCulture;
var checks=new List<object>();int failed=0;
void Require(bool condition){if(!condition)throw new Exception("Independent static-deck contract failed.");}
void Check(string name,Action test){try{test();checks.Add(new{name,passed=true});}catch(Exception error){failed++;checks.Add(new{name,passed=false,error=error.ToString()});}}
void Reject(Action action){try{action();}catch(Exception e)when(e is CaeException or ArgumentException or NotSupportedException or IOException or InvalidDataException){return;}throw new Exception("Invalid analysis accepted");}
InpMeshData Mesh()=>MeshFiles.Read(Path.Combine(AppContext.BaseDirectory,"cube-mesh.inp"));
AnalysisSpec Spec()=>AnalysisFiles.Read(Path.Combine(AppContext.BaseDirectory,"cube-analysis.json"));
var baseline=AnalysisFiles.Create(Spec());
string deck=StaticAnalysisDeckWriter.Write(Mesh(),baseline.Materials,baseline.Sections,baseline.Step).Replace("\r\n","\n");
void Invalid(string name,Action<Material[],SolidSection[],StaticStep> mutate)=>Check(name,()=>{var data=AnalysisFiles.Create(Spec());mutate(data.Materials,data.Sections,data.Step);Reject(()=>StaticAnalysisDeckWriter.Write(Mesh(),data.Materials,data.Sections,data.Step));});
Check("complete deck has original analysis keywords in order",()=>{
    string[] names={"*Node\n","*Element,","*Material,","*Elastic\n","*Solid section,","*Step,","*Static\n","*Boundary\n","*Cload\n","*Output,","*Node print,","*El print,","*Node file\n","*El file\n","*End step\n"};
    int previous=-1;foreach(string keyword in names){int at=deck.IndexOf(keyword,StringComparison.Ordinal);Require(at>previous);previous=at;}
});
Check("original concentrated-load virtual dispatch writes data and rejects missing local context",()=>{
    var load=(CLoad)AnalysisFiles.Create(Spec()).Step.Loads["Axial"];
    Type type=typeof(Material).Assembly.GetType("FileInOut.Output.Calculix.CalCLoad");
    var keyword=Activator.CreateInstance(type,new object[]{load,null,FileInOut.Output.Calculix.ComplexLoadTypeEnum.None});
    var method=type.GetMethod("GetDataString");Require(((string)method.Invoke(keyword,null)).Replace("\r\n","\n")=="X1, 1, 25\n");
    load.CoordinateSystemName="Local";
    try{method.Invoke(keyword,null);throw new Exception("Missing local context accepted");}
    catch(System.Reflection.TargetInvocationException e){Require(e.InnerException is NotSupportedException);}
});
Check("unported derived step cannot lose its extra behavior",()=>Reject(()=>StaticAnalysisDeckWriter.Write(Mesh(),baseline.Materials,baseline.Sections,new ExtraStaticStep())));
Check("cube material original property values",()=>Require(deck.Contains("210000, 0.3\n")));
Check("cube original section named references",()=>Require(deck.Contains("*Solid section, Elset=SOLID, Material=ELASTIC\n")));
Check("cube original constraints preserve free and constrained DOFs",()=>{
    Require(deck.Contains("X0, 1, 1, 0\n")&&deck.Contains("Y0, 2, 2, 0\n")&&deck.Contains("Z0, 3, 3, 0\n"));
    Require(baseline.Step.BoundaryConditions["Fix-X"] is DisplacementRotation bc&&bc.GetDofType(1)==DOFType.Zero&&bc.GetDofType(2)==DOFType.Free);
});
Check("concentrated force is per node with 100 N resultant",()=>{
    var load=(CLoad)baseline.Step.Loads["Axial"];Require(load.F1.Value==25&&load.Magnitude.Value==25&&Mesh().NodeSets["X1"].Length*load.F1.Value==100&&deck.Contains("X1, 1, 25\n"));
});
Check("original static increment and output policy",()=>Require(deck.Contains("*Static\n1, 1, 1E-05, 1\n")&&deck.Contains("*Output, Frequency=1\n")));
Check("original field and history output bodies",()=>Require(deck.Contains("*Node file\nRF, U\n")&&deck.Contains("*El file\nS, E, NOE\n")&&deck.Contains("*El print, Elset=SOLID, Global=Yes\nS\n")));
Check("original input mesh IDs and topology survive full export",()=>{
    var reopened=InpFileReader.ReadMeshData(deck.Split('\n'));Require(reopened.Nodes.Count==8&&reopened.Elements.Count==1&&reopened.Elements[1].NodeIds.SequenceEqual(new[]{1,2,3,4,5,6,7,8}));
});
Check("original assembly and serialized field identities",()=>{
    Type[] types={typeof(Selection),typeof(CoordinateSystem),typeof(Section),typeof(SolidSection),typeof(Step),typeof(StaticStep),typeof(Load),typeof(CLoad),typeof(BoundaryCondition),typeof(DisplacementRotation)};
    foreach(Type t in types){string owner=t.Namespace=="CaeGlobals"?"CaeGlobals":t.Namespace=="CaeMesh"?"CaeMesh":"CaeModel";Require(t.Assembly.GetName().Name==owner&&t.IsDefined(typeof(SerializableAttribute),false));}
    var info=new SerializationInfo(typeof(StaticStep),new FormatterConverter());baseline.Step.GetObjectData(info,new StreamingContext());
    Require(info.GetValue("_boundaryConditions",typeof(CaeGlobals.OrderedDictionary<string,BoundaryCondition>)) is CaeGlobals.OrderedDictionary<string,BoundaryCondition>);
    Require(info.GetValue("_loads",typeof(CaeGlobals.OrderedDictionary<string,Load>)) is CaeGlobals.OrderedDictionary<string,Load>);
});
Check("read and write do not select unsafe serialization",()=>Require(typeof(Selection).GetConstructor(new[]{typeof(Selection),typeof(bool),typeof(bool)})==null));
Check("original coordinate system data is callable",()=>{
    var cs=new CoordinateSystem("Local",false);var v=cs.GetOrientedVectorAtPoint(new[]{1d,2d,3d},new[]{0d,0d,0d});Require(v.SequenceEqual(new[]{1d,2d,3d}));
});
Check("original Color data works without GDI or a desktop host",()=>Require(baseline.Step.BoundaryConditions["Fix-X"].Color.ToArgb()==System.Drawing.Color.Lime.ToArgb()));
Check("original negative phase normalization",()=>Require(Tools.GetPhase360(-30)==330));
Check("source equations survive material displacement and load export",()=>{
    var data=AnalysisFiles.Create(Spec());var bc=(DisplacementRotation)data.Step.BoundaryConditions["Fix-X"];var load=(CLoad)data.Step.Loads["Axial"];
    bc.U1.SetEquation("=1/1000");load.F1.SetEquation("=5*5",true);
    string b=bc.U1.String,l=load.F1.String,m=((Elastic)data.Materials[0].Properties[0]).YoungsPoissonsTemp[0][0].String;
    string text=StaticAnalysisDeckWriter.Write(Mesh(),data.Materials,data.Sections,data.Step);
    Require(text.Contains("X0, 1, 1, 0.001")&&b==bc.U1.String&&l==load.F1.String&&m==((Elastic)data.Materials[0].Properties[0]).YoungsPoissonsTemp[0][0].String);
});
Check("typed French culture export snapshots original quantities and restores culture",()=>{
    var old=CultureInfo.CurrentCulture;
    try{
        var data=AnalysisFiles.Create(Spec());CultureInfo.CurrentCulture=CultureInfo.GetCultureInfo("fr-FR");
        var material=new Material("ELASTIC");material.AddProperty(new Elastic(new[]{new[]{210000d,.3,0}}));
        var text=StaticAnalysisDeckWriter.Write(Mesh(),new[]{material},data.Sections,data.Step);Require(text.Contains("210000, 0.3")&&CultureInfo.CurrentCulture.Name=="fr-FR");
    }finally{CultureInfo.CurrentCulture=old;}
});
Check("explicit SI pressure and displacement conversion",()=>{
    var spec=Spec();spec=spec with{UnitSystem="m-N-s-C",Step=spec.Step with{Constraints=spec.Step.Constraints.Select((x,i)=>i==0?x with{Displacements=new[]{"1 mm",null,null}}:x).ToArray()}};
    var data=AnalysisFiles.Create(spec);Require(((Elastic)data.Materials[0].Properties[0]).YoungsPoissonsTemp[0][0].Value==210000000000d);
    Require(((DisplacementRotation)data.Step.BoundaryConditions["Fix-X"]).U1.Value==.001);
    Require(StaticAnalysisDeckWriter.Write(Mesh(),data.Materials,data.Sections,data.Step).Contains("X0, 1, 1, 0.001"));
});
Check("static data getters retain original clamping semantics",()=>{var step=new StaticStep("Test");step.TimePeriod=.5;Require(step.InitialTimeIncrement==.5);});
Check("raw tool increments are rejected before original clamping",()=>Reject(()=>AnalysisFiles.Create(Spec() with{Step=Spec().Step with{InitialTimeIncrement=2}})));
Check("unknown units rejected",()=>Reject(()=>AnalysisFiles.Create(Spec() with{UnitSystem="unknown"})));
Check("unknown schema rejected",()=>Reject(()=>AnalysisFiles.Create(Spec() with{SchemaVersion=99})));
Check("missing material array rejected",()=>Reject(()=>AnalysisFiles.Create(Spec() with{Materials=null})));
Check("missing constraint arrays rejected",()=>Reject(()=>AnalysisFiles.Create(Spec() with{Step=Spec().Step with{Constraints=null}})));
Check("malformed force vector rejected",()=>Reject(()=>AnalysisFiles.Create(Spec() with{Step=Spec().Step with{Loads=new[]{new ForceSpec("Bad","X1",new[]{"25"})}}})));
Check("oversized equation rejected",()=>Reject(()=>AnalysisFiles.Create(Spec() with{Materials=new[]{new MaterialSpec("ELASTIC",new string('1',4097),"0.3")}})));
Check("mesh with model definitions is rejected",()=>Reject(()=>StaticAnalysisDeckWriter.Write(InpFileReader.ReadMeshData(deck.Split('\n')),baseline.Materials,baseline.Sections,baseline.Step)));
Check("unsupported element formulation is rejected",()=>{
    string mesh=File.ReadAllText(Path.Combine(AppContext.BaseDirectory,"cube-mesh.inp")).Replace("TYPE=C3D8","TYPE=C3D8R");
    Reject(()=>StaticAnalysisDeckWriter.Write(InpFileReader.ReadMeshData(mesh.Split('\n')),baseline.Materials,baseline.Sections,baseline.Step));
});
Check("zero original element measure is rejected",()=>{
    var mesh=Mesh();foreach(int id in mesh.Nodes.Keys.ToArray()){var node=mesh.Nodes[id];node.Z=0;mesh.Nodes[id]=node;}Reject(()=>StaticAnalysisDeckWriter.Write(mesh,baseline.Materials,baseline.Sections,baseline.Step));
});
Check("missing sections rejected",()=>Reject(()=>StaticAnalysisDeckWriter.Write(Mesh(),baseline.Materials,Array.Empty<SolidSection>(),baseline.Step)));
Check("overlapping section coverage rejected",()=>Reject(()=>StaticAnalysisDeckWriter.Write(Mesh(),baseline.Materials,new[]{baseline.Sections[0],new SolidSection("Duplicate","ELASTIC","SOLID",RegionTypeEnum.ElementSetName,1,false)},baseline.Step)));
Check("missing element coverage rejected",()=>{var mesh=Mesh();mesh.ElementSets["EMPTY"]=Array.Empty<int>();var data=AnalysisFiles.Create(Spec());data.Sections[0].RegionName="EMPTY";Reject(()=>StaticAnalysisDeckWriter.Write(mesh,data.Materials,data.Sections,data.Step));});
Check("duplicate material name rejected",()=>Reject(()=>StaticAnalysisDeckWriter.Write(Mesh(),new[]{baseline.Materials[0],baseline.Materials[0]},baseline.Sections,baseline.Step)));
Check("unused material rejected",()=>{var extra=new Material("Unused");extra.AddProperty(new Elastic(new[]{new[]{1d,.3,0}}));Reject(()=>StaticAnalysisDeckWriter.Write(Mesh(),new[]{baseline.Materials[0],extra},baseline.Sections,baseline.Step));});
Invalid("missing material reference rejected",(m,s,t)=>s[0].MaterialName="Absent");
Invalid("missing element set rejected",(m,s,t)=>s[0].RegionName="Absent");
Invalid("wrong section region kind rejected",(m,s,t)=>s[0].RegionType=RegionTypeEnum.NodeSetName);
Invalid("inactive section rejected",(m,s,t)=>s[0].Active=false);
Invalid("selection state not silently omitted",(m,s,t)=>s[0].CreationData=new Selection());
Invalid("nonlinear geometry rejected",(m,s,t)=>t.Nlgeom=true);
Invalid("perturbation rejected",(m,s,t)=>t.Perturbation=true);
Invalid("no-analysis step rejected",(m,s,t)=>t.RunAnalysis=false);
Invalid("explicit solver substitution rejected",(m,s,t)=>t.SolverType=SolverTypeEnum.Spooles);
Invalid("invalid incrementation enum rejected",(m,s,t)=>t.IncrementationType=(IncrementationTypeEnum)99);
Invalid("nonfinite increment rejected",(m,s,t)=>t.TimePeriod=double.PositiveInfinity);
Invalid("custom increments not hidden by default",(m,s,t)=>t.IncrementationType=IncrementationTypeEnum.Default);
Invalid("zero output frequency rejected",(m,s,t)=>t.OutputFrequency=0);
Invalid("missing BCs rejected",(m,s,t)=>t.BoundaryConditions.Clear());
Invalid("missing node set rejected",(m,s,t)=>t.BoundaryConditions["Fix-X"].RegionName="Absent");
Invalid("complex BC rejected",(m,s,t)=>t.BoundaryConditions["Fix-X"].Complex=true);
Invalid("local BC coordinates rejected",(m,s,t)=>t.BoundaryConditions["Fix-X"].CoordinateSystemName="Local");
Invalid("nonconstant BC distribution rejected",(m,s,t)=>((DisplacementRotation)t.BoundaryConditions["Fix-X"]).DistributionName="Variable");
Invalid("rotational BC rejected",(m,s,t)=>((DisplacementRotation)t.BoundaryConditions["Fix-X"]).UR1.SetEquationFromValue(0));
Invalid("fixed displacement sentinel rejected",(m,s,t)=>((DisplacementRotation)t.BoundaryConditions["Fix-X"]).U1.SetEquationFromValue(double.PositiveInfinity));
Invalid("empty unconstrained BC rejected",(m,s,t)=>((DisplacementRotation)t.BoundaryConditions["Fix-X"]).U1.SetEquationFromValue(double.NaN));
Invalid("overlapping node DOF rejected",(m,s,t)=>{var b=new DisplacementRotation("Other","X0",RegionTypeEnum.NodeSetName,false,false,0);b.U1.SetEquationFromValue(1);t.BoundaryConditions.Add(b.Name,b);});
Invalid("load missing region rejected",(m,s,t)=>t.Loads["Axial"].RegionName="Absent");
Invalid("complex load rejected",(m,s,t)=>t.Loads["Axial"].Complex=true);
Invalid("load amplitude not silently omitted",(m,s,t)=>t.Loads["Axial"].AmplitudeName="Custom");
Invalid("local load coordinates rejected",(m,s,t)=>t.Loads["Axial"].CoordinateSystemName="Local");
Invalid("zero force rejected",(m,s,t)=>((CLoad)t.Loads["Axial"]).F1.SetEquationFromValue(0,true));
Invalid("overlapping concentrated forces rejected",(m,s,t)=>t.Loads.Add("Other",new CLoad("Other","X1",RegionTypeEnum.NodeSetName,1,0,0,false,false,0)));
Invalid("missing field outputs rejected",(m,s,t)=>t.FieldOutputs.Clear());
Invalid("contact output not silently omitted",(m,s,t)=>t.FieldOutputs.Values.First().ContactElements=true);
Invalid("thermal field flags rejected",(m,s,t)=>((NodalFieldOutput)t.FieldOutputs["NF-Output-1"]).Variables=NodalFieldVariable.NT);
Invalid("2D output flags rejected",(m,s,t)=>((ElementFieldOutput)t.FieldOutputs["EF-Output-1"]).Output=ElementFieldOutputOutputEnum.TwoD);
Invalid("history region not silently omitted",(m,s,t)=>t.HistoryOutputs.Values.First().RegionName="Absent");
Invalid("history totals not silently omitted",(m,s,t)=>t.HistoryOutputs.Values.First().TotalsType=TotalsTypeEnum.Only);
Invalid("inactive history not silently omitted",(m,s,t)=>t.HistoryOutputs.Values.First().Active=false);
Console.WriteLine(JsonSerializer.Serialize(new{success=failed==0,passed=checks.Count-failed,failed,checks,deck,
    runtime=new{architecture=RuntimeInformation.ProcessArchitecture.ToString()},solverExecuted=false}));
return failed==0?0:1;

internal sealed class ExtraStaticStep:StaticStep{public ExtraStaticStep():base("Other") {}}

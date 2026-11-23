using System.Globalization;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Runtime.Serialization;
using System.Text.Json;
using CaeGlobals;
using CaeMesh;
using CaeModel;

CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
CultureInfo.CurrentUICulture = CultureInfo.InvariantCulture;
var checks = new List<object>();
int failed = 0;
bool postRc2 = args.SequenceEqual(new[]{"--post-rc2"});
if(args.Length != 0 && !postRc2) return 2;
void Check(string name, Action action)
{
    try { action(); checks.Add(new { name, passed = true }); }
    catch (Exception error) { failed++; checks.Add(new { name, passed = false, error = error.ToString() }); }
}
void Require(bool value) { if (!value) throw new Exception("Independent contract failed"); }
void Near(double actual, double expected, double tolerance = 1e-9) => Require(double.IsFinite(actual) && Math.Abs(actual - expected) <= tolerance);
void Reject(Action action)
{
    try { action(); }
    catch (Exception error) when (error is CaeException or ArgumentException or NotSupportedException) { return; }
    throw new Exception("Invalid input accepted");
}
Material Material(double e = 210000, double nu = 0.3)
{
    var material = new Material("Steel"); material.AddProperty(new Elastic(new[] { new[] { e, nu, 0d } })); return material;
}
Elastic Elastic(Material m) => (Elastic)m.Properties[0];
StringPressureConverter.SetUnit = "MPa";
StringTemperatureConverter.SetUnit = "°C";
Check("original arithmetic equation", () => {
    var q = new EquationContainer(typeof(StringPressureConverter), 1); q.SetEquation("=2*105000"); Near(q.Value, 210000); Require(q.IsEquation());
});
Check("original expression functions and pi", () => Near(MyNCalc.SolveEquation("=Ln(Exp(1))+Cos(pi)"), 0));
Check("original conditional expression", () => Near(MyNCalc.SolveEquation("=if(2>1,7,9)"), 7));
Check("original distance callbacks", () => { MyNCalc.Dist = (a,b) => Math.Abs(a-b); Near(MyNCalc.SolveEquation("=Dist(11,29)"),18); MyNCalc.Dist=null; });
Check("original dotted parameter cache and updates", () => {
    MyNCalc.ExistingParameters=new CaeGlobals.OrderedDictionary<string,object>("Parameters",StringComparer.OrdinalIgnoreCase);
    MyNCalc.SetParameterValue("Part.Area", 7d); Near(MyNCalc.SolveEquation("=Part.Area*3"),21);
    MyNCalc.SetParameterValue("Part.Area", 9d); Near(MyNCalc.SolveEquation("=Part.Area*3"),27);
    MyNCalc.SetParameterValue("Part.Area.Long", 2d); Near(MyNCalc.SolveEquation("=Part.Area.Long+Part.Area"),11);
    MyNCalc.ExistingParameters=null;
});
Check("original array evaluation", () => {
    MyNCalc.ExistingParameters=new CaeGlobals.OrderedDictionary<string,object>("Parameters");
    MyNCalc.SetParameterValue("x",new[]{1d,2d,3d});
    Require(MyNCalc.SolveArrayEquation("=x*2").SequenceEqual(new[]{2d,4d,6d})); MyNCalc.ExistingParameters=null;
});
Check("unknown equation parameter rejected", () => Reject(() => new EquationContainer(typeof(StringDoubleConverter),0).SetEquation("=missing+1")));
Check("nonfinite equation rejected", () => Reject(() => new EquationContainer(typeof(StringDoubleConverter),0).SetEquation("=1/0")));
Check("pressure quantity conversion GPa to MPa", () => {
    var q=new EquationContainer(typeof(StringPressureConverter),1);q.SetEquation("210 GPa"); Near(q.Value,210000);
});
Check("temperature Fahrenheit to Celsius", () => {
    var q=new EquationContainer(typeof(StringTemperatureConverter),1);q.SetEquation("32 °F");Near(q.Value,0);
});
Check("length mm to inches", () => {
    StringLengthConverter.SetUnit="in";var q=new EquationContainer(typeof(StringLengthConverter),1);q.SetEquation("25.4 mm");Near(q.Value,1);StringLengthConverter.SetUnit="m";
});
Check("force kN to N", () => {
    StringForceConverter.SetUnit="N";var q=new EquationContainer(typeof(StringForceConverter),1);q.SetEquation("1 kN");Near(q.Value,1000);
});
Check("original material positive modulus validation", () => Reject(() => new Elastic(new[]{new[]{-1d,0.3,0d}}).CheckEquations()));
Check("original duplicate elastic exclusion", () => {
    var m=Material(); Reject(()=>m.AddProperty(new ElasticWithDensity(1,0.3,1)));
});
Check("original equation presence and property lookup", () => {
    var m=Material();Require(!m.ContainsEquation());Elastic(m).YoungsPoissonsTemp[0][0].SetEquation("=2*105000");
    Require(m.ContainsEquation() && ReferenceEquals(m.GetProperty<Elastic>(),Elastic(m)));
});
Check("original orthotropic material stability", () => {
    var e=new ElasticEngineeringConstants(new[]{new[]{210000d,210000,210000,.3,.3,.3,80769,80769,80769,0}}); e.CheckEquations();
    var m=new Material("Orthotropic");m.AddProperty(e);Require(!m.ContainsEquation());Reject(()=>m.AddProperty(new Elastic(new[]{new[]{1d,.3,0d}})));
});
Check("original orthotropic unstable data rejected", () => Reject(() => new ElasticEngineeringConstants(new[]{new[]{1d,1,1,2,2,2,1,1,1,0}}).CheckEquations()));
Check("original lamina material validation", () => {
    new ElasticLamina(new[]{new[]{210000d,70000,.25,10000,10000,27000,0}}).CheckEquations();
});
Check("original lamina unstable data rejected", () => Reject(() => new ElasticLamina(new[]{new[]{1d,1,2,1,1,1,0}}).CheckEquations()));
Check("pinned lamina stability behavior is preserved", () => {
    var e = new ElasticLamina(new[]{new[]{210000d,70000,.25,10000,10000,10000,0}});
    Require((typeof(ElasticLamina).GetMethod("GetPoissonsRatio23") != null) == postRc2);
    if(postRc2) Reject(()=>e.CheckEquations()); else e.CheckEquations();
});
Check("pinned composite-strength capability is preserved", () => {
    Type t=typeof(Material).Assembly.GetType("CaeModel.CompositeStrength");Require((t!=null)==postRc2);
    if(t!=null) {
        var value=(MaterialProperty)Activator.CreateInstance(t,new object[]{100d,90d,70d,60d,50d,40d,-.5});value.CheckEquations();
        var m=new Material("Composite");m.AddProperty(value);Require(!m.ContainsEquation());
        ((EquationContainer)t.GetProperty("TensileStrength1").GetValue(value)).SetEquation("=50*2");Require(m.ContainsEquation());
        Reject(()=>MaterialDeckWriter.WriteIsotropic(m));
        var bad=(MaterialProperty)Activator.CreateInstance(t,new object[]{100d,90d,70d,60d,50d,40d,1d});Reject(()=>bad.CheckEquations());
    }
});
Check("original nonelastic material types callable", () => {
    MaterialProperty[] p={new Density(new[]{new[]{1d,0}}),new Plastic(new[]{new[]{1d,0d,0d}}),new SpecificHeat(new[]{new[]{1d,0}}),
        new ThermalConductivity(new[]{new[]{1d,0}}),new ThermalExpansion(new[]{new[]{1d,0}}),new ElasticWithDensity(1,.3,1)};
    foreach(var value in p)value.CheckEquations();
});
Check("original elastic serializable field contract without unsafe serializer", () => {
    // 3.0.2: the one stored field is [PmxKey]; files of older versions give it to the original constructor
    var e=Elastic(Material());var field=typeof(Elastic).GetField("_youngsPoissonsTemp",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic);
    Require(field.IsDefined(typeof(CaeGlobals.PmxKeyAttribute),false)&&field.GetValue(e) is EquationContainer[][]);
    var info=new SerializationInfo(typeof(Elastic),new FormatterConverter());info.AddValue("_youngsPoissonsTemp",field.GetValue(e),typeof(EquationContainer[][]));
    var restored=new Elastic(info,new StreamingContext());Near(restored.YoungsPoissonsTemp[0][0].Value,210000);
});
Check("original legacy elastic constructor contract", () => {
    var info=new SerializationInfo(typeof(Elastic),new FormatterConverter());info.AddValue("_youngsModulus",210000d);info.AddValue("_poissonsRatio",.3d);
    var e=new Elastic(info,new StreamingContext());Near(e.YoungsPoissonsTemp[0][0].Value,210000);Near(e.YoungsPoissonsTemp[0][1].Value,.3);
});
Check("original CalculiX numeric formatter", () => {Require(1d.ToCalculiX16String(true)=="1.");Require((1d/3).ToCalculiX16String()=="3.33333333E-001");});
Check("actual isotropic keyword fragment", () => {
    Require(MaterialDeckWriter.WriteIsotropic(Material()).Replace("\r\n","\n")=="*Material, Name=Steel\n*Elastic\n210000, 0.3\n");
});
Check("equation material export preserves equations", () => {
    var m=Material();Elastic(m).YoungsPoissonsTemp[0][0].SetEquation("=2*105000");string before=Elastic(m).YoungsPoissonsTemp[0][0].String;
    Require(MaterialDeckWriter.WriteIsotropic(m).Contains("210000, 0.3"));Require(before==Elastic(m).YoungsPoissonsTemp[0][0].String);
});
Check("culture-aware evaluation and invariant deck without source mutation", () => {
    var old=CultureInfo.CurrentCulture;
    try {CultureInfo.CurrentCulture=CultureInfo.GetCultureInfo("fr-FR");var m=Material();
        string equation=Elastic(m).YoungsPoissonsTemp[0][1].String;string deck=MaterialDeckWriter.WriteIsotropic(m);
        Require(deck.Contains("210000, 0.3") && CultureInfo.CurrentCulture.Name=="fr-FR" && equation==Elastic(m).YoungsPoissonsTemp[0][1].String);
    } finally {CultureInfo.CurrentCulture=old;}
});
Check("null material rejected", () => Reject(()=>MaterialDeckWriter.WriteIsotropic(null)));
Check("empty material rejected", () => Reject(()=>MaterialDeckWriter.WriteIsotropic(new Material("Empty"))));
Check("inactive material rejected", () => {var m=Material();m.Active=false;Reject(()=>MaterialDeckWriter.WriteIsotropic(m));});
Check("invalid material rejected", () => {var m=Material();m.Valid=false;Reject(()=>MaterialDeckWriter.WriteIsotropic(m));});
Check("temperature dependence not silently omitted", () => {var m=Material();m.TemperatureDependent=true;Reject(()=>MaterialDeckWriter.WriteIsotropic(m));});
Check("extra property not silently omitted", () => {var m=Material();m.AddProperty(new Density(new[]{new[]{1d,0}}));Reject(()=>MaterialDeckWriter.WriteIsotropic(m));});
Check("multiple rows not silently omitted", () => {var m=Material();Elastic(m).YoungsPoissonsTemp=new Elastic(new[]{new[]{1d,.3,0},new[]{2d,.3,100}}).YoungsPoissonsTemp;Reject(()=>MaterialDeckWriter.WriteIsotropic(m));});
Check("negative modulus rejected at material boundary", () => Reject(()=>MaterialDeckWriter.WriteIsotropic(Material(-1))));
Check("nonfinite constant rejected at material boundary", () => Reject(()=>MaterialDeckWriter.WriteIsotropic(Material(double.PositiveInfinity))));
foreach(double nu in new[]{-1d,.5,1d}) {double value=nu;Check("unstable isotropic Poisson ratio rejected "+nu,()=>Reject(()=>MaterialDeckWriter.WriteIsotropic(Material(1,value))));}
Check("non-simple keyword name rejected", () => {Reject(()=>{var m=Material();m.Name="Steel Name";MaterialDeckWriter.WriteIsotropic(m);});});
Check("material field array corruption rejected", () => {var m=Material();Elastic(m).YoungsPoissonsTemp[0][0]=null;Reject(()=>MaterialDeckWriter.WriteIsotropic(m));});
var types = new[]{typeof(EquationContainer),typeof(EquationString),typeof(MyNCalc),typeof(CaeGlobals.OrderedDictionary<string,object>),typeof(Material),typeof(Elastic),typeof(MaterialProperty),typeof(ElasticEngineeringConstants),typeof(ElasticLamina),typeof(MaterialDeckWriter)};
Check("original assembly identities and serialized type markers", () => {
    foreach(var t in types){string owner=t.Namespace=="CaeGlobals"?"CaeGlobals":"CaeModel";Require(t.Assembly.GetName().Name==owner && t.Assembly.GetName().Version==new Version(1,0,0,0));}
    // 3.0.2: [PmxType] marks the stored type; the original (SerializationInfo, StreamingContext) constructor stays for older files
    Require(typeof(Elastic).IsDefined(typeof(PmxTypeAttribute)) && typeof(Elastic).GetConstructor(new[]{typeof(SerializationInfo),typeof(StreamingContext)})!=null);
});
var assemblies=new[]{typeof(EquationContainer).Assembly,typeof(FeNode).Assembly,typeof(Material).Assembly};
Check("expanded assemblies have no desktop platform references", () => {
    foreach(var a in assemblies)foreach(var r in a.GetReferencedAssemblies())
        // Whole original assemblies (D062): original packages and portable assemblies are expected;
        // the real WinForms/WPF desktop frameworks and ActiViz stay excluded.
        Require(r.Name != "System.Windows.Forms" && !r.Name.StartsWith("System.Windows.Forms.") && !r.Name.StartsWith("Presentation") && !r.Name.StartsWith("Kitware"));
});
// A unit tetrahedron with deliberately distinct VOL/original node ordering.
string vol = "mesh3d\ndimension\n3\nsurfaceelements\n4\n1 1 1 0 3 1 2 3\n2 2 1 0 3 1 2 4\n3 3 1 0 3 1 3 4\n4 4 1 0 3 2 3 4\nvolumeelements\n1\n7 4 1 3 2 4\nedgesegmentsgi2\n1\n1 0 1 2 -1 -1 0 0 1 0 9 1\npoints\n4\n0 0 0\n1 0 0\n0 1 0\n0 0 1\nendmesh\n";
void RejectVol(string value) {
    try { FileInOut.Input.NetgenVolFileReader.ReadLinearSolidData(value); }
    catch (Exception e) when (e is System.IO.InvalidDataException or NotSupportedException or FormatException or ArgumentException or IndexOutOfRangeException or OverflowException) { return; }
    throw new Exception("Malformed VOL accepted");
}
Check("original VOL tetra permutation, signed volume and source IDs", () => {
    var m=FileInOut.Input.NetgenVolFileReader.ReadLinearSolidData(vol);
    var e=(LinearTetraElement)m.Elements[5];
    Require(e.NodeIds.SequenceEqual(new[]{1,2,3,4}) && e.PartId==7);
    Near(e.GetVolume(m.Nodes),1d/6); Require(m.FaceNodeIds[4].SetEquals(new[]{2,3,4}) && m.EdgeNodeIds[9].SetEquals(new[]{1,2}));
});
Check("VOL decimal convention independent of current culture", () => {
    var previous=CultureInfo.CurrentCulture;
    try { CultureInfo.CurrentCulture=CultureInfo.GetCultureInfo("de-DE");
        var m=FileInOut.Input.NetgenVolFileReader.ReadLinearSolidData(vol.Replace("1 0 0\n", "1.5 0 0\n"));
        Near(m.Nodes[2].X,1.5);
    } finally { CultureInfo.CurrentCulture=previous; }
});
Check("quadratic VOL tetra remains gated",()=>RejectVol(vol.Replace("7 4 1 3 2 4", "7 10 1 3 2 4 1 2 3 4 1 2")));
string qvol = "mesh3d\ndimension\n3\nsurfaceelements\n4\n1 1 1 0 6 1 2 3 6 7 5\n2 2 1 0 6 1 2 4 9 8 5\n3 3 1 0 6 1 3 4 10 8 7\n4 4 1 0 6 2 3 4 10 9 6\nvolumeelements\n1\n7 10 1 3 2 4 7 5 8 6 10 9\nedgesegmentsgi2\n1\n1 0 1 2 -1 -1 0 0 1 0 9 1\npoints\n10\n0 0 0\n1 0 0\n0 1 0\n0 0 1\n0.5 0 0\n0.5 0.5 0\n0 0.5 0\n0 0 0.5\n0.5 0 0.5\n0 0.5 0.5\nendmesh\n";
Check("quadratic preview preserves original ten-node and face permutations",()=> {
    var m=FileInOut.Input.NetgenVolFileReader.ReadQuadraticPreviewData(qvol);
    Require(m.ElementOrder==2 && m.Elements[5] is ParabolicTetraElement && m.Elements[5].NodeIds.SequenceEqual(Enumerable.Range(1,10)));
    Require(m.FaceNodeIds[1].SetEquals(new[]{1,2,3,5,6,7}) && m.EdgeNodeIds[9].SetEquals(new[]{1,2,5}));
    Require(m.Elements[5].GetVtkCellType()==24);
});
void RejectQuadratic(string text) {
    try { FileInOut.Input.NetgenVolFileReader.ReadQuadraticPreviewData(text); }
    catch(Exception e) when(e is System.IO.InvalidDataException or NotSupportedException or FormatException or ArgumentException) { return; }
    throw new Exception("Malformed quadratic preview accepted");
}
Check("quadratic preview refuses missing midside and inverted corners",()=> {
    RejectQuadratic(qvol.Replace("7 10 1 3 2 4 7 5 8 6 10 9","7 10 1 3 2 4 7 5 8 6 10 11"));
    RejectQuadratic(qvol.Replace("7 10 1 3 2 4 7 5 8 6 10 9","7 10 1 2 3 4 7 5 8 6 10 9"));
});
Check("quadratic preview refuses swapped CAD face midsides",()=>RejectQuadratic(qvol.Replace("6 1 2 3 6 7 5","6 1 2 3 7 6 5")));
Check("quadratic preview keeps the linear admission gate",()=>RejectVol(qvol));
Check("inverted VOL tetra rejected",()=>RejectVol(vol.Replace("7 4 1 3 2 4", "7 4 1 2 3 4")));
Check("VOL missing node rejected",()=>RejectVol(vol.Replace("7 4 1 3 2 4", "7 4 1 3 2 99")));
Check("VOL truncated count rejected",()=>RejectVol(vol.Replace("points\n4", "points\n5")));
Check("VOL nonfinite coordinate rejected",()=>RejectVol(vol.Replace("0 0 1\n", "0 0 NaN\n")));
Check("VOL mismatched exterior boundary rejected",()=>RejectVol(vol.Replace("4 4 1 0 3 2 3 4", "4 4 1 0 3 1 2 3")));
Check("VOL duplicate section rejected",()=>RejectVol(vol+"points\n1\n0 0 0\n"));
Check("VOL oversized declared count rejected",()=>RejectVol(vol.Replace("points\n4", "points\n100001")));
Console.WriteLine(JsonSerializer.Serialize(new {postRc2,success=failed==0,passed=checks.Count-failed,failed,checks,
    types=types.Select(t=>t.AssemblyQualifiedName),assemblies=assemblies.Select(a=>new{name=a.GetName().Name,references=a.GetReferencedAssemblies().Select(r=>r.FullName)}),
    runtime=new {os=RuntimeInformation.OSDescription,architecture=RuntimeInformation.ProcessArchitecture.ToString()},
    limitations=new[]{"Material fragment only; no section/step/BC/load/solve", "NCalc 1.3.8 retains NU1701 compatibility warning", "No production serializer selected or unsafe serialization enabled"}}));
return failed==0?0:1;

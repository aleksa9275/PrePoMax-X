using System.Globalization;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;
using CaeResults;
using CaeMesh;
var checks=new List<object>();int failed=0;
void Check(string name,bool passed){checks.Add(new{name,passed});if(!passed)failed++;}
bool Near(double actual,double expected,double tolerance=1e-8)=>Math.Abs(actual-expected)<=tolerance;
string fixture=Path.Combine(AppContext.BaseDirectory,"uniaxial.frd");
string raw=File.ReadAllText(fixture).Replace("\r","");string[] lines=raw.Split('\n');
string directory=Path.Combine(Path.GetTempPath(),"PrePoMax-X results 空 "+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(directory);
FrdStaticSnapshot ReadText(string name,string value){string p=Path.Combine(directory,name+".frd");File.WriteAllText(p,value);return FrdFileReader.ReadStaticSnapshot(p);}
bool Reject(string name,string value){try{ReadText(name,value);return false;}catch(Exception e)when(e is IOException or InvalidDataException or ArgumentException or NotSupportedException or FormatException or OverflowException or IndexOutOfRangeException or AggregateException){return true;}}
void WriteBinary(string file,int format)
{
 using var stream=File.Create(file);using var writer=new BinaryWriter(stream,Encoding.UTF8);
 void Line(string value)=>writer.Write(Encoding.ASCII.GetBytes(value+"\n"));
 void Value(double value){if(format==3)writer.Write(value);else writer.Write((float)value);}
 for(int i=0;i<lines.Length;i++)
 {
  string line=lines[i];if(line=="")continue;
  if(line.StartsWith("    2C"))
  {
   Line(line[..36]+format.ToString().PadLeft(38));
   while(lines[++i]!=" -3"){writer.Write(int.Parse(lines[i].Substring(3,10)));for(int j=0;j<3;j++)Value(double.Parse(lines[i].Substring(13+12*j,12),CultureInfo.InvariantCulture));}
  }
  else if(line.StartsWith("    3C"))
  {
   Line(line[..36]+format.ToString().PadLeft(38));
   // Independent fixture definition: one eight-node hexahedron, material 1.
   writer.Write(1);writer.Write(1);writer.Write(0);writer.Write(1);for(int n=1;n<=8;n++)writer.Write(n);
   while(lines[++i]!=" -3"){}
  }
  else if(line.StartsWith("  100C"))
  {
   char[] header=line.PadRight(75).ToCharArray();header[73]=' ';header[74]=(char)('0'+format);Line(new string(header));
   Line(lines[++i]);var stored=new List<int>();int component=0;
   while(lines[i+1].StartsWith(" -5")){Line(lines[++i]);if(!lines[i].EndsWith("1ALL"))stored.Add(component);component++;}
   while(lines[++i]!=" -3")
   {
    writer.Write(int.Parse(lines[i].Substring(3,10)));
    for(int j=0;j<stored.Count;j++)Value(double.Parse(lines[i].Substring(13+j*12,12),CultureInfo.InvariantCulture));
   }
  }
  else Line(line);
 }
}
try
{
 var snapshot=FrdFileReader.ReadStaticSnapshot(fixture);
 var disp=snapshot.Fields.Single(f=>f.Data.Name=="DISP");var stress=snapshot.Fields.Single(f=>f.Data.Name=="STRESS");var force=snapshot.Fields.Single(f=>f.Data.Name=="FORC");
 Check("original results types retain CaeResults assembly ownership",new[]{typeof(Field),typeof(FieldData),typeof(FieldComponent),typeof(FrdFileReader)}.All(t=>t.Assembly.GetName().Name=="CaeResults"));
 Check("original mesh types retain CaeMesh ownership",snapshot.Nodes[1].GetType().Assembly.GetName().Name=="CaeMesh"&&snapshot.Elements[1].GetType()==typeof(LinearHexaElement));
 Check("Windows reference node and element IDs preserved",snapshot.Nodes.Count==8&&snapshot.Elements.Count==1&&snapshot.NodeIdsInValueOrder.SequenceEqual(Enumerable.Range(1,8)));
 Check("original element connectivity preserved",snapshot.Elements[1].NodeIds.SequenceEqual(Enumerable.Range(1,8)));
 Check("reference coordinates decoded",snapshot.Nodes[7].X==1&&snapshot.Nodes[7].Y==1&&snapshot.Nodes[7].Z==1);
 Check("all recorded static fields retained",snapshot.Fields.Select(f=>f.Data.Name).SequenceEqual(new[]{"DISP","STRESS","FORC","ERROR"}));
 Check("step increment and time retained",snapshot.Fields.All(f=>f.Data.StepType==StepTypeEnum.Static&&f.Data.StepId==1&&f.Data.StepIncrementId==1&&f.Data.Time==1));
 Check("original displacement names mapped",new[]{"U1","U2","U3","ALL"}.All(disp.Field.ContainsComponent));
 Check("axial displacement agrees with independent cube formula",Near(disp.Field.GetComponentValues("U1")[1],100.0/210000,1e-9));
 Check("Poisson transverse displacement agrees with cube formula",Near(disp.Field.GetComponentValues("U2")[2],-0.3*100/210000,1e-9)&&Near(disp.Field.GetComponentValues("U3")[4],-0.3*100/210000,1e-9));
 Check("stored FRD stress preserved rather than rounded to analytical DAT",Near(stress.Field.GetComponentValues("S11")[0],99.996,1e-5));
 Check("stress component ordering and near-zero shear retained",new[]{"S11","S22","S33","S12","S23","S13"}.All(stress.Field.ContainsComponent)&&Math.Abs(stress.Field.GetComponentValues("S13")[1])<1e-9);
 Check("nodal forces balance and preserve loaded-node magnitude",Near(force.Field.GetComponentValues("F1").Sum(),0)&&Near(force.Field.GetComponentValues("F1")[1],25));
 Check("original displacement magnitude computed",Near(disp.Field.GetComponentValues("ALL")[6],Math.Sqrt(Math.Pow(100.0/210000,2)+2*Math.Pow(0.3*100/210000,2)),1e-9));
 Check("original Mises invariant computed",Near(stress.Field.GetComponentValues("MISES")[0],99.996,1e-5));
 Check("unit system is not inferred or converted",snapshot.UnitSystemHeader==null);
 Check("source fingerprint retained",snapshot.SourceSha256==Convert.ToHexStringLower(System.Security.Cryptography.SHA256.HashData(File.ReadAllBytes(fixture))));
 var culture=CultureInfo.CurrentCulture;try{CultureInfo.CurrentCulture=new CultureInfo("fr-FR");var french=FrdFileReader.ReadStaticSnapshot(fixture);Check("invariant decoding with caller culture restored",Near(french.Fields[0].Field.GetComponentValues("U1")[1],100.0/210000,1e-9)&&CultureInfo.CurrentCulture.Name=="fr-FR");}finally{CultureInfo.CurrentCulture=culture;}
 for(int format=2;format<=3;format++)
 {
  string path=Path.Combine(directory,"binary"+format+".frd");WriteBinary(path,format);var binary=FrdFileReader.ReadStaticSnapshot(path);
  Check("binary format "+format+" preserves mesh",binary.Nodes.Count==8&&binary.Elements[1].NodeIds.SequenceEqual(snapshot.Elements[1].NodeIds)&&binary.Nodes[7].Z==1);
  Check("binary format "+format+" matches all original raw and derived components",binary.Fields.Count==snapshot.Fields.Count&&binary.Fields.Zip(snapshot.Fields).All(pair=>pair.First.Data.Name==pair.Second.Data.Name&&pair.First.Field.GetComponentNames().All(n=>pair.First.Field.GetComponentValues(n).Zip(pair.Second.Field.GetComponentValues(n)).All(v=>Near(v.First,v.Second,1e-5)))));
 }
 Check("unicode and space paths",ReadText("space Čaša",raw).Nodes.Count==8);
 Check("missing terminal marker rejected",Reject("incomplete",raw.Replace(" 9999","")));
 int lastEnd=raw.LastIndexOf(" -3",StringComparison.Ordinal);
 Check("unclosed final field cannot be silently dropped",Reject("unclosed",raw.Remove(lastEnd,3)));
 Check("duplicate terminal records rejected",Reject("duplicate-terminal",raw+" 9999\n"));
 Check("nonfinite/malformed stored values rejected",Reject("bad-value",raw.Replace("4.76190E-04","XXXXXXXXXXX")));
 Check("axisymmetric scaling is gated",Reject("axisymmetric",raw.Replace("    1C\n","    1C\n    1UModel space: Axisymmetric\n")));
 Check("original modal header classifies frequency fields",ReadText("modal",raw.Replace("                     0    1","                     2    1MODAL")).Fields.All(f=>f.Data.StepType==StepTypeEnum.Frequency));
 Check("declared excessive mesh size rejected before allocation",Reject("oversize",raw.Replace("    2C                             8","    2C                       9999999")));
 int value=Array.FindIndex(lines,25,l=>l.StartsWith(" -1"));var swapped=(string[])lines.Clone();(swapped[value],swapped[value+1])=(swapped[value+1],swapped[value]);
 Check("ambiguous reordered full field IDs rejected",Reject("reordered",string.Join('\n',swapped)));
 var missing=(string[])lines.Clone();missing[value]="";Check("partial field records rejected",Reject("partial",string.Join('\n',missing.Where(l=>l!=""))));
 Check("wrong component names rejected",Reject("wrong-component",raw.Replace(" -5  D3"," -5  F3")));
 Check("incomplete/changed connectivity rejected",Reject("bad-node",raw.Replace("         7         8\n","         7        99\n")));
 Check("full legacy FeResults graph excluded",typeof(Field).Assembly.GetType("CaeResults.FeResults")==null);
 var shear=new Field("STRESS");foreach(string n in new[]{"S11","S22","S33","S12","S23","S13"})shear.AddComponent(n,new[]{n=="S12"?10f:0f});shear.ComputeInvariants();
 Check("independent pure-shear Mises calculation",Near(shear.GetComponentValues("MISES")[0],Math.Sqrt(3)*10,1e-5));
 Check("independent pure-shear principal stresses",Near(shear.GetComponentValues("PRINCIPAL_MAX")[0],10,1e-5)&&Near(shear.GetComponentValues("PRINCIPAL_MIN")[0],-10,1e-5));
 Check("no UI rendering or WMI dependency",!typeof(Field).Assembly.GetReferencedAssemblies().Any(a=>a.Name.Contains("Windows")||a.Name.Contains("ActiViz")||a.Name.Contains("Management")));
 var parallel=await Task.WhenAll(Enumerable.Range(0,4).Select(_=>Task.Run(()=>FrdFileReader.ReadStaticSnapshot(fixture))));Check("concurrent callers preserve independent snapshots",parallel.All(s=>s.Fields.Count==4)&&!ReferenceEquals(parallel[0].Fields[0].Field,parallel[1].Fields[0].Field));
 DatChecks.Run(Check,directory);
}
catch(Exception e){Check("unexpected exception: "+e,false);}
finally{Directory.Delete(directory,true);}
Console.WriteLine(JsonSerializer.Serialize(new{success=failed==0,passed=checks.Count-failed,failed,checks,runtime=new{os=RuntimeInformation.OSDescription,architecture=RuntimeInformation.ProcessArchitecture.ToString()},solverExecuted=false}));return failed==0?0:1;

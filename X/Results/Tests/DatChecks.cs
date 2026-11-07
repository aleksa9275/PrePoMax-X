using System.Globalization;
using System.Security.Cryptography;
using CaeResults;

internal static class DatChecks
{
 public static void Run(Action<string,bool> check,string directory)
 {
  string fixture=Path.Combine(AppContext.BaseDirectory,"uniaxial.dat");string raw=File.ReadAllText(fixture).Replace("\r","");
  bool Near(double a,double b,double tolerance=1e-9)=>Math.Abs(a-b)<=tolerance;
  DatStaticSnapshot Read(string name,string text){string path=Path.Combine(directory,name+".dat");File.WriteAllText(path,text);return DatFileReader.ReadStaticSnapshot(path);}
  bool Reject(string name,string text){try{Read(name,text);return false;}catch(Exception e)when(e is IOException or InvalidDataException or ArgumentException or NotSupportedException or FormatException or OverflowException){return true;}}
  DatStaticHistory Get(DatStaticSnapshot data,string field,string component,int id,int? point=null,int step=1)=>data.Histories.Single(h=>h.FieldName==field&&h.ComponentName==component&&h.Id==id&&h.IntegrationPoint==point&&h.StepId==step);
  const string meta="S T E P       1\n\nINCREMENT     1\n\n";
  const string header="displacements (vx,vy,vz) for set SET-1 and time  0.5000000E+00\n\n";
  const string row="42 1.25 -2.5 3.75\n";
  string simple=meta+header+row;
  string basis="\n                        S T E P       1\n\n\n     E I G E N V A L U E   O U T P U T\n\n MODE NO    EIGENVALUE                       FREQUENCY   \n                                     REAL PART            IMAGINARY PART\n                           (RAD/TIME)      (CYCLES/TIME     (RAD/TIME)\n\n      1   0.3000000E+07   0.1732051E+04   0.2756644E+03   0.0000000E+00\n\n     P A R T I C I P A T I O N   F A C T O R S\n\nMODE NO.   X-COMPONENT     Y-COMPONENT     Z-COMPONENT     X-ROTATION      Y-ROTATION      Z-ROTATION\n\n      1   0.1825742E-01   0.0000000E+00   0.0000000E+00   0.0000000E+00   0.9128709E-02  -0.9128709E-02\n\n     E F F E C T I V E   M O D A L   M A S S\n\nMODE NO.   X-COMPONENT     Y-COMPONENT     Z-COMPONENT     X-ROTATION      Y-ROTATION      Z-ROTATION\n\n      1   0.3333333E-03   0.0000000E+00   0.0000000E+00   0.0000000E+00   0.8333333E-04   0.8333333E-04\nTOTAL     0.3333333E-03   0.0000000E+00   0.0000000E+00   0.0000000E+00   0.8333333E-04   0.8333333E-04\n\n     T O T A L   E F F E C T I V E   M A S S\n\nMODE NO.   X-COMPONENT     Y-COMPONENT     Z-COMPONENT     X-ROTATION      Y-ROTATION      Z-ROTATION\n\n          0.3333333E-03   0.0000000E+00   0.0000000E+00   0.0000000E+00   0.1111111E-03   0.1111111E-03\n\n\n";
  string modal=basis+simple.Replace("S T E P       1","S T E P       2").Replace("displacements","velocities");
  var modalData=Read("modal-history",modal);
  check("DAT modal velocity preserves physical step and identifies excluded basis tables",modalData.ExcludedBasisTables.Count==4 && Get(modalData,"VELOCITIES","V1",42,step:2).Entries.Values.Single()==1.25);
  check("DAT basis unknown records and incomplete tables cannot disappear",Reject("basis-unknown",modal.Replace("MODE NO    EIGENVALUE","unknown\nMODE NO    EIGENVALUE")) && Reject("basis-incomplete",modal.Replace("TOTAL     0.3333333E-03","BROKEN    0.3333333E-03")));
  check("DAT basis mode order and nonfinite values refused",Reject("basis-mode",modal.Replace("1   0.3000000E+07","2   0.3000000E+07")) && Reject("basis-number",modal.Replace("0.3000000E+07","1E999")));
  check("DAT basis alone cannot masquerade as time histories",Reject("basis-only",basis));
  var data=DatFileReader.ReadStaticSnapshot(fixture);
  check("DAT original reader and history entries retain original assembly",typeof(DatFileReader).Assembly.GetName().Name=="CaeResults"&&typeof(HistoryResultEntries).Assembly.GetName().Name=="CaeResults");
  check("DAT Windows fixture retains three blocks and 96 component histories",data.DataSetCount==3&&data.Histories.Count==96);
  check("DAT original component names preserved",data.Histories.Select(h=>h.FieldName).Distinct().SequenceEqual(new[]{"DISPLACEMENTS","FORCES","STRESSES"})&&data.Histories.Where(h=>h.FieldName=="STRESSES").Select(h=>h.ComponentName).Distinct().SequenceEqual(new[]{"S11","S22","S33","S12","S13","S23"}));
  check("DAT original set identities and metadata preserved",data.Histories.All(h=>h.StepId==1&&h.IncrementIds.SequenceEqual(new[]{1})&&h.Entries.Time.SequenceEqual(new[]{1.0}))&&Get(data,"DISPLACEMENTS","U1",2).SetName=="NALL"&&Get(data,"STRESSES","S11",1,1).BaseSetName=="SOLID");
  check("DAT axial displacement agrees with independent analytical cube",Near(Get(data,"DISPLACEMENTS","U1",2).Entries.Values[0],100.0/210000));
  check("DAT Poisson contractions agree with independent analytical cube",Near(Get(data,"DISPLACEMENTS","U2",3).Entries.Values[0],-0.3*100/210000)&&Near(Get(data,"DISPLACEMENTS","U3",5).Entries.Values[0],-0.3*100/210000));
  check("DAT forces balance with 25 per loaded node",Near(data.Histories.Where(h=>h.FieldName=="FORCES"&&h.ComponentName=="RF1").Sum(h=>h.Entries.Values[0]),0)&&Get(data,"FORCES","RF1",2).Entries.Values[0]==25);
  check("DAT integration point identities and stress retained",data.Histories.Where(h=>h.FieldName=="STRESSES"&&h.ComponentName=="S11").Select(h=>h.IntegrationPoint.Value).SequenceEqual(Enumerable.Range(1,8))&&Enumerable.Range(1,8).All(p=>Get(data,"STRESSES","S11",1,p).Entries.Values[0]==100));
  check("DAT source fingerprint and unspecified units retained",data.SourceSha256==Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(fixture)))&&data.Histories.All(h=>h.Entries.Unit==null&&!h.Entries.Local));
  var culture=CultureInfo.CurrentCulture;try{CultureInfo.CurrentCulture=new CultureInfo("fr-FR");check("DAT invariant decoding restores caller culture",Read("culture",simple).Histories[0].Entries.Values[0]==1.25&&CultureInfo.CurrentCulture.Name=="fr-FR");}finally{CultureInfo.CurrentCulture=culture;}
  check("DAT caller culture restored after failure",Reject("culture-error",simple.Replace("1.25","BAD"))&&CultureInfo.CurrentCulture.Equals(culture));
  var increments=Read("increments",simple+"\nINCREMENT     2\n\n"+header.Replace("0.5000000E+00","0.1000000E+01")+row.Replace("1.25","2.5"));
  check("DAT original entries accumulate time and increment identities",increments.Histories.Count==3&&increments.Histories[0].IncrementIds.SequenceEqual(new[]{1,2})&&increments.Histories[0].Entries.Time.SequenceEqual(new[]{0.5,1.0})&&increments.Histories[0].Entries.Values.SequenceEqual(new[]{1.25,2.5})&&increments.Histories[0].Entries.Count.SequenceEqual(new[]{1,1}));
  var steps=Read("steps",simple+"\n"+simple.Replace("S T E P       1","S T E P       2"));
  check("DAT different steps keep separate histories without time shifts",steps.Histories.Count==6&&steps.Histories.Select(h=>h.StepId).Distinct().SequenceEqual(new[]{1,2})&&steps.Histories.All(h=>h.Entries.Time[0]==0.5));
  check("DAT row order preserves non-contiguous identities",Read("ids",meta+header+"99 1 2 3\n2 4 5 6\n").Histories.Where(h=>h.ComponentName=="U1").Select(h=>h.Id).SequenceEqual(new[]{99,2}));
  check("DAT original missing-E exponent repair reused",Near(Read("exponent",simple.Replace("1.25","1.25-003")).Histories[0].Entries.Values[0],0.00125,1e-14));
  check("DAT local coordinate flag retained",Read("local",simple.Replace(row,row.TrimEnd()+" L\n")).Histories.All(h=>h.Entries.Local));
  check("DAT original internal-set name repair reused",Read("internal",simple.Replace("SET-1","INTERNAL_SELECTION_1_OUTPUT")).Histories[0].SetName=="1_OUTPUT");
  check("DAT strains preserve original shear ordering",Read("strain",meta+"strains (elem, integ.pnt.,exx,eyy,ezz,exy,exz,eyz) for set SOLID and time 1\n\n1 2 0.1 0.2 0.3 0.4 0.5 0.6\n").Histories.Select(h=>h.ComponentName).SequenceEqual(new[]{"E11","E22","E33","E12","E13","E23"}));
  check("DAT UTF8 BOM CRLF and unicode path",Read("history Čaša", "\uFEFF"+simple.Replace("\n","\r\n")).Histories.Count==3);
  check("DAT empty input rejected",Reject("empty-dat",""));
  check("DAT unsupported record cannot silently disappear",Reject("unknown",simple+"\nunknown output\n"));
  check("DAT malformed numeric values rejected",Reject("numeric",simple.Replace("1.25","1.2E")));
  check("DAT nonfinite and overflow values rejected",Reject("overflow",simple.Replace("1.25","1E999"))&&Reject("nan",simple.Replace("1.25","NaN")));
  check("DAT partial final value row rejected",Reject("partial",simple.Replace("1.25 -2.5 3.75","1.25 -2.5")));
  check("DAT empty final block rejected",Reject("empty-block",simple+"\n"+header.Replace("SET-1","OTHER")));
  check("DAT duplicate row identities rejected",Reject("duplicate-row",simple+row));
  check("DAT duplicate blocks rejected",Reject("duplicate-block",simple+"\n"+header+row));
  check("DAT IDs must be positive integer values",Reject("negative-id",simple.Replace("42 ","-1 "))&&Reject("fractional-id",simple.Replace("42 ","1.5 "))&&Reject("huge-id",simple.Replace("42 ","2147483648 ")));
  check("DAT metadata and ordered increments required",Reject("no-step",header+row)&&Reject("no-increment","S T E P 1\n\n"+header+row)&&Reject("decreasing-inc",simple+"\nINCREMENT 1\n\n"+header+row));
  check("DAT original splitter metadata separator required",Reject("adjacent-metadata",simple.Replace("S T E P       1\n\n","S T E P       1\n")));
  check("DAT adjacent unseparated blocks rejected",Reject("adjacent-block",simple+header.Replace("SET-1","OTHER")+row));
  check("DAT negative or non-increasing times rejected",Reject("negative-time",simple.Replace("0.5000000E+00","-1"))&&Reject("same-time",simple+"\nINCREMENT 2\n\n"+header+row));
  check("DAT mixed local/global histories rejected",Reject("mixed-local",simple+"\nINCREMENT 2\n\n"+header.Replace("0.5000000E+00","1")+row.TrimEnd()+" L\n"));
  check("DAT reference point remapping remains gated",Reject("reference-point",simple.Replace("SET-1","RP_Rot_1")));
  check("DAT unsupported contact/modal records gated; original thermal rows supported",Reject("contact",meta+"contact stress (a,b) for all contact elements and time 1\n\n1 2\n")&&Reject("modal",meta+"E I G E N V A L U E   O U T P U T\n")&&Read("thermal",meta+"temperatures for set NALL and time 1\n\n1 2\n").Histories.Single().Entries.Values.Single()==2);
  check("DAT excessive size rejected before decoding",Reject("size",new string(' ',8*1024*1024+1)));
  check("DAT oversized line rejected",Reject("long-line",simple+new string('1',4097)));
  check("DAT no full history graph or persistence selection",typeof(DatFileReader).Assembly.GetType("CaeResults.HistoryResults")==null);
  var parallel=Task.WhenAll(Enumerable.Range(0,4).Select(_=>Task.Run(()=>DatFileReader.ReadStaticSnapshot(fixture)))).GetAwaiter().GetResult();
  check("DAT concurrent calls retain independent original entries",parallel.All(d=>d.Histories.Count==96)&&!ReferenceEquals(parallel[0].Histories[0].Entries,parallel[1].Histories[0].Entries));
 }
}

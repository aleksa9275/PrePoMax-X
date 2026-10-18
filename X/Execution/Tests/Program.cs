using CaeJob;
using System.Diagnostics;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text.Json;
var checks=new List<object>();int failed=0;
void Check(string name,bool passed){checks.Add(new{name,passed});if(!passed)failed++;}
string root=Path.Combine(Path.GetTempPath(),"PrePoMax-X job 空 "+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(root);
string host=Environment.GetEnvironmentVariable("DOTNET_HOST_PATH")??Environment.ProcessPath!;
string probe=typeof(PrePoMaxXProbe.Marker).Assembly.Location;
ExecutableJob Job(string name,string command,params string[] args){string dir=Path.Combine(root,name);Directory.CreateDirectory(dir);return new(name,host,"",dir){ProcessArguments=new[]{probe,command}.Concat(args).ToArray(),TimeLimit=TimeSpan.FromSeconds(10)};}
try{
 Check("75 percent recommendation examples",new[]{(8,6),(12,9),(16,12),(32,24)}.All(p=>SolverThreadPlan.Create(p.Item1).TotalThreadBudget==p.Item2));
 Check("single available CPU remains usable",SolverThreadPlan.Create(1).ThreadsPerJob.SequenceEqual(new[]{1}));
 Check("automatic rounding uses floor",SolverThreadPlan.Create(3).TotalThreadBudget==2&&SolverThreadPlan.Create(7).TotalThreadBudget==5);
 Check("manual total can override automatic budget",SolverThreadPlan.Create(16,1,16).TotalThreadBudget==16&&!SolverThreadPlan.Create(16,1,16).IsAutomatic);
 Check("fair remainder and deterministic job ordering",SolverThreadPlan.Create(16,5).ThreadsPerJob.SequenceEqual(new[]{3,3,2,2,2}));
 Check("manual budget shared rather than multiplied",SolverThreadPlan.Create(16,3,9).ThreadsPerJob.SequenceEqual(new[]{3,3,3}));
 Check("large CPU count does not overflow",SolverThreadPlan.Create(int.MaxValue,2).TotalThreadBudget==1610612735);
 bool RejectPlan(int available,int jobs,int? manual=null){try{SolverThreadPlan.Create(available,jobs,manual);return false;}catch(ArgumentOutOfRangeException){return true;}}
 Check("invalid available CPU counts rejected",RejectPlan(0,1)&&RejectPlan(-1,1));
 Check("invalid manual total rejected",RejectPlan(8,1,0)&&RejectPlan(8,1,-1)&&RejectPlan(8,1,9));
 Check("invalid or excessive planned jobs rejected",RejectPlan(8,0)&&RejectPlan(8,-1)&&RejectPlan(int.MaxValue,1025));
 Check("overcommitted plan rejected instead of zero thread jobs",RejectPlan(8,7)&&RejectPlan(8,4,3));
 Check("available manual budget allows every CPU one job",SolverThreadPlan.Create(8,8,8).ThreadsPerJob.All(n=>n==1));
 bool invariant=true;
 for(int available=1;available<=128;available++)for(int jobs=1;jobs<=Math.Min(32,Math.Max(1,available*3/4));jobs++){
  var p=SolverThreadPlan.Create(available,jobs);var allocations=p.ThreadsPerJob;
  invariant&=p.IsAutomatic&&allocations.Count==jobs&&allocations.All(n=>n>=1)&&allocations.Sum()==p.TotalThreadBudget&&p.TotalThreadBudget<=available&&allocations.Max()-allocations.Min()<=1;
 }
 Check("allocation bounds conservation and fairness across host sizes",invariant);
 var immutable=SolverThreadPlan.Create(8);bool readOnly=false;try{((IList<int>)immutable.ThreadsPerJob)[0]=99;}catch(NotSupportedException){readOnly=true;}
 Check("callers cannot mutate a returned plan",readOnly&&immutable.ThreadsPerJob[0]==6);
 var job=Job("echo","echo","space path","quote\"value","semi;$(touch nope)","Čaša 空");
 File.WriteAllText(Path.Combine(job.WorkDirectory,"working-marker"),"right working directory");
 job.ProcessEnvironment=new Dictionary<string,string>{{"PREPOMAXX_PROBE","unit context"}};var progress=new List<string>();job.AppendOutput+=value=>{lock(progress)progress.Add(value);};await job.SubmitAsync();
 Check("native process successful status and exit",job.JobStatus==JobStatus.OK&&job.ExitCode==0);
 using(var data=JsonDocument.Parse(job.CapturedStandardOutput)){
  Check("argument tokens including metacharacters unchanged",data.RootElement.GetProperty("args").EnumerateArray().Select(x=>x.GetString()).SequenceEqual(new[]{"space path","quote\"value","semi;$(touch nope)","Čaša 空"}));
  Check("working directory with spaces and unicode",data.RootElement.GetProperty("marker").GetString()=="right working directory");
  Check("explicit child environment",data.RootElement.GetProperty("env").GetString()=="unit context");
 }
 Check("stderr retained separately",job.CapturedStandardError.Contains("probe stderr")&&job.ErrorData.Contains("probe stderr"));
 Check("original progress event and output file",progress.Count>0&&File.ReadAllText(Path.Combine(job.WorkDirectory,"_output_echo.txt")).Contains("probe stderr"));
 Check("no shell side effects",!File.Exists(Path.Combine(job.WorkDirectory,"nope")));
 bool twice=false;try{await job.SubmitAsync();}catch(InvalidOperationException){twice=true;}Check("asynchronous jobs are one shot",twice);
 var bad=Job("fail","fail");await bad.SubmitAsync();Check("nonzero real exit maps to Failed",bad.JobStatus==JobStatus.Failed&&bad.ExitCode==7&&bad.ErrorData.Contains("intentional"));
 var stream=Job("stream","stream");await stream.SubmitAsync();Check("both pipes drain beyond normal pipe capacity",stream.JobStatus==JobStatus.OK&&stream.CapturedStandardOutput.Split('\n',StringSplitOptions.RemoveEmptyEntries).Length==20000&&stream.CapturedStandardError.Split('\n',StringSplitOptions.RemoveEmptyEntries).Length==20000);
 var timed=Job("timed","sleep");timed.TimeLimit=TimeSpan.FromMilliseconds(300);var watch=Stopwatch.StartNew();await timed.SubmitAsync();Check("deadline returns TimedOut with real stopped process",timed.JobStatus==JobStatus.TimedOut&&timed.ExitCode!=null&&watch.Elapsed<TimeSpan.FromSeconds(7));
 var cancel=Job("cancel","sleep");using(var cts=new CancellationTokenSource(300))await cancel.SubmitAsync(cts.Token);Check("cancellation maps to Killed",cancel.JobStatus==JobStatus.Killed&&cancel.ExitCode!=null);
 var early=Job("early","echo");using(var cts=new CancellationTokenSource()){cts.Cancel();await early.SubmitAsync(cts.Token);}Check("pre-cancel never launches child",early.JobStatus==JobStatus.Killed&&early.ExitCode==null&&early.CapturedStandardOutput=="");
 var tree=Job("tree","child");tree.TimeLimit=TimeSpan.FromMilliseconds(1500);await tree.SubmitAsync();string pidPath=Path.Combine(tree.WorkDirectory,"child.pid");Check("tree fixture child actually started",File.Exists(pidPath));
 bool alive=true;if(File.Exists(pidPath)){int pid=int.Parse(File.ReadAllText(pidPath));for(int n=0;n<40;n++){try{using var child=Process.GetProcessById(pid);alive=!child.HasExited;}catch(ArgumentException){alive=false;}if(!alive)break;await Task.Delay(50);}}
 Check("deadline stops attached descendant process",tree.JobStatus==JobStatus.TimedOut&&!alive);
 var serialFirst=Job("serial-first","sleep");using(var cts=new CancellationTokenSource()){
  var firstTask=serialFirst.SubmitAsync(cts.Token);for(int n=0;n<100&&!serialFirst.ProcessStarted;n++)await Task.Delay(20);
  var serialSecond=Job("serial-second","echo");var secondTask=serialSecond.SubmitAsync();await Task.Delay(100);bool waited=!serialSecond.ProcessStarted;
  cts.Cancel();await firstTask;await secondTask;Check("default concurrent-run flag serializes jobs in this host",waited&&serialFirst.ProcessStarted&&serialSecond.JobStatus==JobStatus.OK);
 }
 var parallelFirst=Job("parallel-first","sleep");using(var cts=new CancellationTokenSource()){
  var firstTask=parallelFirst.SubmitAsync(cts.Token);for(int n=0;n<100&&!parallelFirst.ProcessStarted;n++)await Task.Delay(20);
  var parallelSecond=Job("parallel-second","echo");parallelSecond.AllowConcurrentRuns=true;await parallelSecond.SubmitAsync();bool overlapped=parallelFirst.JobStatus==JobStatus.Running;
  cts.Cancel();await firstTask;Check("explicit concurrent-run flag permits independent jobs",overlapped&&parallelSecond.JobStatus==JobStatus.OK);
 }
 var missing=Job("missing","echo");missing.Executable=Path.Combine(root,"missing-native-program");await missing.SubmitAsync();Check("missing executable recorded as failure",missing.JobStatus==JobStatus.Failed&&missing.FailureReason!=null&&missing.ExitCode==null);
 var existing=Job("existing","echo");string original=Path.Combine(existing.WorkDirectory,"_output_existing.txt");File.WriteAllText(original,"preserve");await existing.SubmitAsync();Check("existing output evidence never overwritten",existing.JobStatus==JobStatus.Failed&&File.ReadAllText(original)=="preserve");
 var invalid=Job("invalid","echo");invalid.TimeLimit=TimeSpan.Zero;await invalid.SubmitAsync();Check("invalid deadline fails before execution",invalid.JobStatus==JobStatus.Failed&&invalid.ExitCode==null);
 Check("original job type assembly owner",typeof(ExecutableJob).Assembly.GetName().Name=="CaeJob"&&typeof(JobStatus).Assembly==typeof(ExecutableJob).Assembly);
 Check("original JobStatus names and numbers",Enum.GetNames<JobStatus>().SequenceEqual(new[]{"None","InQueue","Running","OK","Killed","TimedOut","Failed","FailedWithResults"})&&(int)JobStatus.FailedWithResults==7);
 Check("original persisted job fields retained without platform state",typeof(ExecutableJob).GetFields(BindingFlags.NonPublic|BindingFlags.Instance|BindingFlags.DeclaredOnly).Where(f=>!f.IsDefined(typeof(NonSerializedAttribute))).Select(f=>f.Name).Order(StringComparer.Ordinal).SequenceEqual(new[]{"AppendOutput","_argument","_executable","_jobStatus","_workDirectory"}));
 bool missingBuild=false;using(var empty=JsonDocument.Parse("{\"schemaVersion\":1,\"builds\":[]}")){try{PrePoMaxX.Solve.SolverBuilds.Select(empty.RootElement,"unknown");}catch(InvalidDataException){missingBuild=true;}}Check("unknown solver profile never falls back",missingBuild);
 using(var fileProfile=JsonDocument.Parse("{\"executable\":\"probe.bin\",\"files\":{\"probe.bin\":\""+PrePoMaxX.Solve.SolverBuilds.Hash(probe)+"\"}}")){
  string dir=Path.Combine(root,"pinned-files");Directory.CreateDirectory(dir);File.Copy(probe,Path.Combine(dir,"probe.bin"));
  Check("pinned build file accepted only with exact bytes",PrePoMaxX.Solve.SolverBuilds.ValidateFiles(fileProfile.RootElement,dir)==Path.Combine(dir,"probe.bin"));
  File.AppendAllText(Path.Combine(dir,"probe.bin"),"tampered");bool rejected=false;try{PrePoMaxX.Solve.SolverBuilds.ValidateFiles(fileProfile.RootElement,dir);}catch(InvalidDataException){rejected=true;}Check("changed native binary rejected",rejected);
 }
 var recordedStatus=CalculixMonitorDataParser.ParseStatus(File.ReadAllText(Path.Combine(AppContext.BaseDirectory,"uniaxial.sta")));
 Check("original parser reads recorded Windows status IDs",recordedStatus.Count==1&&recordedStatus.Steps[0]==1&&recordedStatus.Increments[0]==1&&recordedStatus.Attempts[0]==1);
 Check("recorded status retains original times and iterations",recordedStatus.TotalTimes[0]==1&&recordedStatus.IncrementTimes[0]==1&&recordedStatus.IterationCounts[0]==1);
 Check("empty recorded convergence is not fabricated",CalculixMonitorDataParser.ParseConvergence(File.ReadAllText(Path.Combine(AppContext.BaseDirectory,"uniaxial.cvg"))).Count==0);
 var previousCulture=System.Globalization.CultureInfo.CurrentCulture;try{
  System.Globalization.CultureInfo.CurrentCulture=new System.Globalization.CultureInfo("fr-FR");
  var status=CalculixMonitorDataParser.ParseStatus("header\r\n1 2 3 4 1.5D+00 1 2.5d-1\r\nbad data");
  Check("original monitor parsing invariant with D exponents",status.Count==1&&status.TotalTimes[0]==1.5&&status.IncrementTimes[0]==0.25&&status.Increments[0]==2);
  var conv=CalculixMonitorDataParser.ParseConvergence("1 2 3 4 5 6D-2 7d-3 8e-4 9E-5");
  Check("original convergence components and record numbering",conv.Count==1&&conv.RecordNumbers[0]==1&&conv.Iterations[0]==4&&conv.ResidualForces[0]==0.06&&conv.TemperatureCorrections[0]==0.00009);
 }finally{System.Globalization.CultureInfo.CurrentCulture=previousCulture;}
 Check("monitor types retain CaeJob ownership",typeof(CalculixStatusData).Assembly==typeof(ExecutableJob).Assembly&&typeof(CalculixConvergenceData).Assembly==typeof(ExecutableJob).Assembly);
 Check("portable job has no WMI or Windows desktop dependencies",!typeof(ExecutableJob).Assembly.GetReferencedAssemblies().Any(a=>a.Name!.Contains("Management")||a.Name.Contains("Windows")||a.Name.Contains("Presentation")));
}catch(Exception e){Check("unexpected test exception: "+e,false);}
finally{Directory.Delete(root,true);}
Console.WriteLine(JsonSerializer.Serialize(new{success=failed==0,passed=checks.Count-failed,failed,checks,runtime=new{os=RuntimeInformation.OSDescription,architecture=RuntimeInformation.ProcessArchitecture.ToString()},solverExecuted=false}));return failed==0?0:1;

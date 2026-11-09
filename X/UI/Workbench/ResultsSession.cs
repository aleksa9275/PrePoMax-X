using CaeGlobals;using CaeResults;using CaeJob;using PrePoMax;using PrePoMaxX.UI.OriginalForms;
namespace PrePoMaxX.UI;
// Typed presentation facade. All engineering and history live in the original Controller.
public sealed class ResultsSession(HeadlessSession session)
{
 readonly Controller controller=session.Controller;
 public ResultFormRule Edit(string family,string name=null)=>family switch{
  "Jobs"=>new FrmAnalysisRule(controller,name),"Result fields"=>new FrmResultFieldOutputRule(controller,name),
  "Result histories"=>new FrmResultHistoryOutputRule(controller,name),
  "Result reference points"=>new ResultReferencePointRule(controller,name),"Result coordinate systems"=>new ResultCoordinateSystemRule(controller,name),_=>throw new NotSupportedException(family)};
 public void ConfigureSolver(string registry,string id,string directory)
 {
  string executable=SolverRuntime.Validate(registry,id,directory);
  var settings=controller.Settings;settings.Solver.CalculixExe=executable;controller.Settings=settings;
 }
 public Task RunJob(string name,bool check=false)=>Task.Run(()=>{
  if(!controller.PrepareAndRunJobCommand(name,check,true,0))throw new CaeException("The original Controller refused to run this analysis.");
  var status=controller.GetJob(name).JobStatus;if(status is JobStatus.Failed or JobStatus.FailedWithResults or JobStatus.TimedOut)throw new CaeException("Analysis finished with status "+status+". See the original monitor output.");
 });
 public void Kill(string name)=>controller.KillJob(name);
 public Task OpenJob(string name)=>Task.Run(()=>controller.OpenResultsCommand(name));
 public Task Open(string path,bool append=false)=>Task.Run(()=>{if(append)controller.AppendResult(path);else session.Open(path);});
 public bool HasBackgroundHistory=>controller.GetCommands().Any(c=>c is PrePoMax.Commands.PostprocessCommand || c.GetType().Name=="CPrepareAndRunJob" || c.GetType().GetProperty("FileName")?.GetValue(c) is string file && new[]{".frd",".dat",".odb",".foam"}.Contains(Path.GetExtension(file).ToLowerInvariant()));
 public string[] ResultNames=>controller.AllResults.GetResultNames();
 public string[] Fields=>controller.CurrentResult?.GetAllVisibleFiledNameComponentNames().Keys.ToArray()??[];
 public string[] Components(string field)=>controller.CurrentResult.GetAllVisibleFiledNameComponentNames()[field];
 public int[] Steps=>controller.GetResultStepIDs();
 public int[] Increments(int step)=>controller.GetResultStepIncrementIds(step);
 public void Field(string name,string component,int step,int increment)
 {
  controller.CurrentFieldData=controller.CurrentResult.GetFieldData(name,component,step,increment,true);
  controller.DrawResults(false);
 }
 public void SelectResult(string name)=>controller.SetCurrentResultsCommand(name);
 public void Representation(string type)=>controller.ViewResultsType=Enum.Parse<ViewResultsTypeEnum>(type);
 public void Deformation(string variable,string type,float factor)
 {
  session.Presentation.SetDeformationVariable(variable);session.Presentation.SetDeformationType(Enum.Parse<DeformationScaleFactorTypeEnum>(type));
  session.Presentation.SetDeformationFactor(factor);controller.DrawResults(false);
 }
 public void Complex(string type,float angle){controller.CurrentResult.SetComplexResultTypeAndAngle(Enum.Parse<ComplexResultTypeEnum>(type),angle);controller.DrawResults(false);}
 public int Animate(string type,int frames)
 {
  if(frames<2)throw new ArgumentOutOfRangeException(nameof(frames));
  bool ok=type switch{"Scale factor"=>controller.DrawScaleFactorAnimation(frames),"Harmonic"=>controller.DrawHarmonicAnimation(frames),"Time increments"=>controller.DrawTimeIncrementAnimation(out frames),_=>throw new NotSupportedException(type)};
  if(!ok)throw new CaeException("The original Controller could not prepare animation data.");return frames;
 }
 public void AnimationFrame(int frame){session.Presentation.AnimationFrame=frame;controller.AnimationFrameChanged(frame,false);}
 public void Execute(string operation,string[] names)
 {
  switch(operation){
   case "Duplicate reference points":controller.DuplicateResultReferencePointsCommand(names);break;case "Remove reference points":controller.RemoveResultReferencePointsCommand(names);break;
   case "Hide reference points":controller.HideResultReferencePointsCommand(names);break;case "Show reference points":controller.ShowResultReferencePointsCommand(names);break;
   case "Duplicate coordinate systems":controller.DuplicateResultCoordinateSystemsCommand(names);break;case "Remove coordinate systems":controller.RemoveResultCoordinateSystemsCommand(names);break;
   case "Hide coordinate systems":controller.HideResultCoordinateSystemsCommand(names);break;case "Show coordinate systems":controller.ShowResultCoordinateSystemsCommand(names);break;
   case "Duplicate jobs":controller.DuplicateJobsCommand(names);break;case "Remove jobs":controller.RemoveJobsCommand(names);break;
   case "Duplicate fields":controller.DuplicateResultFieldOutputsCommand(names);break;case "Remove fields":controller.RemoveResultFieldOutputsCommand(names);break;
   case "Duplicate histories":controller.DuplicateResultHistoryOutputsCommand(names);break;case "Remove histories":controller.RemoveResultHistoryOutputsCommand(names);break;
   case "Hide parts":controller.HideResultPartsCommand(names);break;case "Show parts":controller.ShowResultPartsCommand(names);break;
   case "Merge parts":controller.MergeResultPartsCommand(names);break;case "Remove parts":controller.RemoveResultPartsCommand(names);break;
   case "Remove result":controller.RemoveCurrentResultsCommand();break;default:throw new NotSupportedException(operation);
  }
 }
 public object CloneLegend()=>controller.Settings.Legend.DeepClone();
 public sealed record HistoryTable(string[] Columns,object[][] Rows);
 public HistoryTable History(HistoryResultData source){controller.GetHistoryOutputData(source,out var columns,out var rows,true);return new(columns,rows);}
 public void ExportField(string path)=>controller.ExportResultFieldOutputCommand(path,controller.AllResults.GetCurrentResultName(),controller.CurrentFieldData);
 public Task ExportParts(string[] names,string path,string format)=>Task.Run(()=>controller.ExportResultPartsCommand(names,path,Enum.Parse<FileInOut.Output.ResultsExportFormatEnum>(format)));
 public string[] ExportFormats=>Enum.GetNames<FileInOut.Output.ResultsExportFormatEnum>();
 public void Color(string[] names,int red,int green,int blue)=>controller.SetColorForResultPartsCommand(names,System.Drawing.Color.FromArgb(red,green,blue));
 public void Transparency(string[] names,byte alpha)=>controller.SetTransparencyForResultPartsCommand(names,alpha);
 public void Contours(string[] names,bool visible)=>controller.SetResultRepresentationForResultPartsCommand(names,visible);
 public ModelTreeEntry[] Tree=>[
  new(){Family="Result reference points",Name="Reference points",Group=true,Children=controller.GetResultReferencePointNames().Select(n=>new ModelTreeEntry{Family="Result reference points",Name=n,Type="FeReferencePoint"}).ToArray()},
  new(){Family="Result coordinate systems",Name="Coordinate systems",Group=true,Children=controller.GetResultCoordinateSystemNames().Select(n=>new ModelTreeEntry{Family="Result coordinate systems",Name=n,Type="CoordinateSystem"}).ToArray()},
  new(){Family="Result parts",Name="Parts",Group=true,Children=(controller.CurrentResult?.Mesh?.Parts.Values??[]).Select(p=>new ModelTreeEntry{Family="Result parts",Name=p.Name,Type=p.GetType().Name}).ToArray()},
  new(){Family="Result fields",Name="Field outputs",Group=true,Children=controller.CurrentResult==null?[]:controller.GetResultFieldOutputNames().Select(n=>new ModelTreeEntry{Family="Result fields",Name=n,Type=controller.GetResultFieldOutputs().FirstOrDefault(f=>f.Name==n)?.GetType().Name??"Field",Children=Components(n).Select(comp=>new ModelTreeEntry{Family="Result field components",Step=n,Name=comp,Type="Component"}).ToArray()}).ToArray()},
  new(){Family="Result histories",Name="History outputs",Group=true,Children=controller.CurrentResult==null?[]:controller.GetHistoryResultSetNames().Select(n=>new ModelTreeEntry{Family="Result histories",Name=n,Type="HistoryResultSet",Children=controller.CurrentResult.GetHistory().Sets[n].Fields.Values.Select(historyField=>new ModelTreeEntry{Family="Result history fields",Step=n,Name=historyField.Name,Type="HistoryResultField",Children=historyField.Components.Values.Select(comp=>new ModelTreeEntry{Family="Result history components",Step=n+"|"+historyField.Name,Name=comp.Name,Type="HistoryResultComponent"}).ToArray()}).ToArray()}).ToArray()}
 ];
 public ModelTreeEntry Jobs=>new(){Family="Jobs",Name="Analyses",Group=true,Children=controller.GetAllJobs().Select(j=>new ModelTreeEntry{Family="Jobs",Name=j.Name,Type=j.JobStatus.ToString()}).ToArray()};
}

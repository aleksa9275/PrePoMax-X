using CaeGlobals;using CaeMesh;using CaeResults;using CaeJob;using PrePoMax;using PrePoMaxX.UI.OriginalForms;
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
 public ModelTreeEntry[] Tree
 {
  get
  {
   var result=controller.CurrentResult;var mesh=result?.Mesh;const string view=OriginalModelTree.Results;
   ModelTreeEntry Item(string family,NamedClass item,string step=null,ModelTreeEntry[] children=null,string name=null)=>OriginalModelTree.Annotate(new ModelTreeEntry{Family=family,Step=step,Name=name??item.Name,Type=item.GetType().Name,Children=children??[]},item,view,controller);
   ModelTreeEntry[] Layout(string family,IEnumerable<NamedClass> items)=>OriginalTreeLayout.Build(controller,family,null,items,i=>Item(family,i));
   ModelTreeEntry Group(string family,string name,IEnumerable<ModelTreeEntry> children)=>new(){Family=family,Name=name,Group=true,Children=children.ToArray()};
   var fieldOutputs=result==null?[]:controller.GetResultFieldOutputs();
   var historyOutputs=result==null?[]:controller.GetResultHistoryOutputs();
   return [
    Group("Result reference points","Reference points",mesh==null?[]:Layout("Result reference points",mesh.ReferencePoints.Values.Where(i=>!i.Internal))),
    Group("Result coordinate systems","Coordinate systems",mesh==null?[]:Layout("Result coordinate systems",mesh.CoordinateSystems.Values.Where(i=>!i.Internal))),
    Group("Result parts","Parts",mesh==null?[]:Layout("Result parts",mesh.Parts.Values.Where(i=>!i.Internal))),
    Group("Result node sets","Node sets",mesh==null?[]:Layout("Result node sets",mesh.NodeSets.Values.Where(i=>!i.Internal))),
    Group("Result element sets","Element sets",mesh==null?[]:Layout("Result element sets",mesh.ElementSets.Values.Where(i=>!i.Internal))),
    Group("Result surfaces","Surfaces",mesh==null?[]:Layout("Result surfaces",mesh.Surfaces.Values.Where(i=>!i.Internal))),
    // CreateOverwriteFieldOutputNodes: Field (or the ResultFieldOutput) with FieldData components.
    Group("Result fields","Field outputs",result==null?[]:controller.GetResultFieldOutputNames().Select(n=>Item("Result fields",(NamedClass)fieldOutputs.FirstOrDefault(f=>f.Name==n)??new Field(n),null,
      Components(n).Select(comp=>Item("Result field components",new FieldData(comp),n)).ToArray()))),
    // CreateOverwriteHistoryOutputNodes: HistoryResultSet (or ResultHistoryOutput), fields, HistoryResultData.
    Group("Result histories","History outputs",result==null?[]:controller.GetHistoryResultSetNames().Select(n=>Item("Result histories",(NamedClass)historyOutputs.FirstOrDefault(h=>h.Name==n)??result.GetHistory().Sets[n],null,
      result.GetHistory().Sets[n].Fields.Values.Select(historyField=>Item("Result history fields",historyField,n,
        historyField.Components.Values.Select(comp=>Item("Result history components",new HistoryResultData(n,historyField.Name,comp.Name),n+"|"+historyField.Name,null,comp.Name)).ToArray())).ToArray())))
   ];
  }
 }
 public ModelTreeEntry Jobs=>new(){Family="Jobs",Name="Analyses",Group=true,Children=OriginalTreeLayout.Build(controller,"Jobs",null,controller.GetAllJobs(),i=>OriginalModelTree.Annotate(new ModelTreeEntry{Family="Jobs",Name=i.Name,Type=((AnalysisJob)i).JobStatus.ToString()},i,OriginalModelTree.Model,controller))};
}

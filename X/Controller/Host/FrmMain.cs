using System;
using System.Collections.Generic;
using System.IO;
using CaeGlobals;
using CaeJob;
using CaeModel;
using CaeMesh;
using CaeResults;
using UserControls;
using vtkControl;

namespace PrePoMax
{
    /// <summary>Headless presentation host. Model operations remain in the original
    /// Controller. Render output is observable; spatial/native queries require an
    /// explicit host implementation rather than returning invented selection data.</summary>
    public partial class FrmMain : IControllerHost
    {
        public vtkMaxActor[] SelectionActors => System.Linq.Enumerable.ToArray(selectionActors);
        readonly List<vtkMaxActor> selectionActors=new();
        public string UndoText {get;private set;}
        public string RedoText {get;private set;}
        public vtkMaxActor[] SceneActors => System.Linq.Enumerable.ToArray(actors.Values);
        public IntPtr Handle => IntPtr.Zero;
        // Transient presentation commands: never serialized into the engineering model.
        public sealed class RenderCommand(string name,object[] args){public string Name=>name;public object[] Arguments=>args;}
        readonly Dictionary<string,RenderCommand> renderCommands=new(StringComparer.Ordinal);
        public RenderCommand[] RenderCommands=>System.Linq.Enumerable.ToArray(renderCommands.Values);
        public Action<string,bool,int> Screenshot {get;set;}
        public Func<UnitSystemType> ResultUnitsSelector {get;set;}
        public int AnimationFrame {get;set;}
        public void SetDeformationVariable(string name){deformationVariable=name;Controller.ClearSelectionBuffer();}
        void CaptureRenderCommand(string name,object[] args)
        {
            string key=name;
            if(name=="RemoveSectionView"){renderCommands.Remove("section");return;}
            if(name is "CreateSectionView" or "UpdateSectionView"){renderCommands["section"]=new RenderCommand(name,args);return;}
            if(name is "AddSymmetry" or "AddLinearPattern" or "AddCircularPattern"){renderCommands["pattern:"+renderCommands.Count]=new RenderCommand(name,args);return;}
            bool glyph=name.StartsWith("AddOriented",StringComparison.Ordinal) || name is "AddSphereActor" or "AddVectorFieldActor" or "AddTensorFieldActor" or "AddAnimatedVectorFieldActor" or "AddAnimatedTensorFieldActor";
            if(glyph && args[0] is vtkMaxActorData data)key="actor:"+data.Name;
            else if(name is "AddCaptionActor" or "AddLabelActor" or "AddArrowWidget" )key="overlay:"+(string)args[0];
            else if(name=="AddMeasurementAnnotation")key="measurement:"+(string)args[0];
            else if(name is "AddCoordinateSystemSymbol")key="coordinates:"+renderCommands.Count;
            else if(name is "RemoveOverlayActors" or "RemoveArrowWidgets" or "RemoveMeasurementAnnotations") {foreach(string item in (string[])args[0]){renderCommands.Remove("overlay:"+item);renderCommands.Remove("measurement:"+item);}return;}
            else if(!name.StartsWith("SetScalarBar",StringComparison.Ordinal) && !name.StartsWith("SetStatusBlock",StringComparison.Ordinal) && !name.StartsWith("DrawLegend",StringComparison.Ordinal) && !name.StartsWith("DrawStatusBlock",StringComparison.Ordinal) && name!="SetAnimationFrameData" && !glyph)return;
            renderCommands[key]=new RenderCommand(name,args);
        }
        public Action<string, object[]> Presentation { get; set; }
        public Func<string, object[], object> Query { get; set; }
        // Explicit export view data. Contour lookup tables belong to the renderer;
        // a non-contour export uses the original empty-table default.
        public vtkMaxLookupTable ExportLookupTable {get;set;}
        public double[] ExportUpDirection {get;set;}
        NativeSpatialQueries nativeGeometry;
        vtkEdgesVisibility edgeVisibility=vtkEdgesVisibility.ModelEdges;
        readonly Dictionary<string,vtkMaxActor> actors = new(StringComparer.Ordinal);
        bool[][] treeState = { Array.Empty<bool>(),Array.Empty<bool>(),Array.Empty<bool>() };
        Dictionary<string,bool>[] stableTreeState = { new(),new(),new() };
        SidePanelsState panels = new();
        bool querySelection;
        string workingState;
        string deformationVariable=FOFieldNames.Disp;
        DeformationScaleFactorTypeEnum deformationType=DeformationScaleFactorTypeEnum.Automatic;
        float deformationFactor=1;
        public FrmMain() {ScreenUpdating=true;RenderingOn=true;IsWindowHidden=true;}
        public NativeSpatialQueries EnableNativeSpatialQueries()
        {
            var native=new NativeSpatialQueries(Controller,()=>System.Linq.Enumerable.ToArray(actors.Values));nativeGeometry=native;Query=native.Query;return native;
        }
        public void InvokeIfRequired(Action action) => action();
        public T InvokeIfRequired<T>(Func<T> action) => action();
        public void Invalidate() => InvokePresentation("Invalidate", Array.Empty<object>());
        private void InvokePresentation(string name, object[] arguments)
        {
            CaptureRenderCommand(name,arguments);
            switch(name)
            {
                case "EnableDisableUndoRedo":UndoText=(string)arguments[0];RedoText=(string)arguments[1];break;
                case "Open":
                    ((Action<string,string>)arguments[1])((string)arguments[0],(string)arguments[3]);
                    // Original FrmMain.Open -> UpdateResultMenus selects a valid default before DrawResults.
                    if(Controller.ResultsInitialized)Controller.CurrentFieldData=Controller.CurrentResult.GetFirstComponentOfTheFirstFieldAtDefaultIncrement();
                    if(Controller.CurrentView==ViewGeometryModelResults.Geometry)Controller.DrawGeometry((bool)arguments[2]);
                    else if(Controller.CurrentView==ViewGeometryModelResults.Model)Controller.DrawModel((bool)arguments[2]);
                    else Controller.ViewResultsType=ViewResultsTypeEnum.ColorContours;
                    if(Controller.ResultsInitialized)SelectResultsUnitSystem(arguments[3] as string);
                    Controller.Annotations.DrawAnnotations(false,true);
                    break;
                case "SetAnnotateWithColor":Controller.AnnotateWithColor=(AnnotateWithColorEnum)arguments[0];break;
                case "SetCurrentEdgesVisibilities":edgeVisibility=(vtkEdgesVisibility)arguments[0];break;
                case "ShowSplitMeshResults":
                    if(Controller.ResultsInitialized)Controller.CurrentFieldData=Controller.CurrentResult.GetFirstComponentOfTheFirstFieldAtDefaultIncrement();
                    Controller.ViewResultsType=ViewResultsTypeEnum.ColorContours;break;
                case "SetCurrentResults":
                    if((string)arguments[0]!=Controller.AllResults.GetCurrentResultName())
                    {
                        actors.Clear();Controller.AllResults.SetCurrentResults((string)arguments[0]);
                        if(Controller.ResultsInitialized)Controller.CurrentFieldData=Controller.CurrentResult.GetFirstComponentOfTheFirstFieldAtDefaultIncrement();
                        Controller.ViewResultsType=ViewResultsTypeEnum.ColorContours;
                    }
                    break;
                case "SetResultsUndeformedModelType":Controller.SetUndeformedModelType((UndeformedModelTypeEnum)arguments[0]);Controller.DrawResults(false);break;
                case "RunHistoryPostprocessing": Controller.RunHistoryPostprocessing(arguments.Length==0?null:(bool?)arguments[0]);break;
                case "OpenAnalysisResults": OpenJobResults((string)arguments[0],(bool)arguments[1]);break;
                case "SelectResultsUnitSystem":
                    if(Controller.CurrentResult?.UnitSystem.UnitSystemType==UnitSystemType.Undefined)
                    {
                        UnitSystemType units;
                        if(!Enum.TryParse(arguments[0] as string,out units))units=MessageBoxes.Mode==MessageBoxModeEnum.Interactive && ResultUnitsSelector!=null?ResultUnitsSelector():UnitSystemType.UNIT_LESS;
                        Controller.SetResultsUnitSystem(units);
                    }
                    break;
                case "SelectFirstComponentOfFirstFieldOutput":
                    if(Controller.CurrentResult!=null)Controller.CurrentFieldData=Controller.CurrentResult.GetFirstComponentOfTheFirstFieldAtDefaultIncrement();
                    break;
                case "SetFieldData": case "SelectFieldOutputComponent":
                    SetResultField((string)arguments[0],(string)arguments[1],arguments.Length>2?(int?)arguments[2]:null,arguments.Length>3?(int?)arguments[3]:null);break;
                case "SelectStepAndIncrement":
                    if(Controller.CurrentFieldData!=null)SetResultField(Controller.CurrentFieldData.Name,Controller.CurrentFieldData.Component,(int)arguments[0],(int)arguments[1]);break;
                case "SetViewResultsType":
                    var view=(ViewResultsTypeEnum)arguments[0];
                    if(view is ViewResultsTypeEnum.Undeformed or ViewResultsTypeEnum.Deformed)Controller.SetUndeformedModelType(UndeformedModelTypeEnum.None);
                    Controller.ViewResultsType=view;break;
                case "SetDeformationType":deformationType=(DeformationScaleFactorTypeEnum)arguments[0];Controller.ClearSelectionBuffer();break;
                case "SetDeformationFactor":deformationFactor=(float)arguments[0];Controller.ClearSelectionBuffer();break;
                case "SetTreeExpandCollapseState":treeState=(bool[][])arguments[0];break;
                case "SetStableTreeExpandCollapseState":stableTreeState=(Dictionary<string,bool>[])arguments[0];break;
                case "SetPendingSidePanelsState":panels=(SidePanelsState)arguments[0];break;
                case "SetQuerySelection":querySelection=(bool)arguments[0];break;
                case "SetStateReady":workingState=null;break;
                case "Clear3DSelection":selectionActors.Clear();break;
                case "ClearButKeepParts":
                    foreach(var key in System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Where(actors.Keys,key=>!actors[key].Data.IsAPart)))actors.Remove(key);
                    foreach(var key in System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Where(renderCommands.Keys,key=>key.StartsWith("actor:",StringComparison.Ordinal)||key.StartsWith("coordinates:",StringComparison.Ordinal))))renderCommands.Remove(key);
                    selectionActors.Clear();break;
                case "UpdateArrowWidgetAnimationData":
                    if(renderCommands.TryGetValue("overlay:"+(string)arguments[0],out var annotation)) {if(arguments[1]!=null)annotation.Arguments[1]=arguments[1];if(arguments[2]!=null)annotation.Arguments[3]=arguments[2];}break;
                case "Clear3D":case "ClearControls":actors.Clear();selectionActors.Clear();renderCommands.Clear();break;
                case "AddScalarFieldOn3DCells":var scalar=(vtkMaxActorData)arguments[0];actors[scalar.Name]=new vtkMaxActor(scalar);break;
                case "UpdateActorSurfaceScalarField":
                    if(actors.TryGetValue((string)arguments[0],out var scalarActor)){scalarActor.Data.Geometry.Nodes.Values=(float[])arguments[1];scalarActor.Data.Geometry.ExtremeNodes=(NodesExchangeData)arguments[2];scalarActor.Data.Geometry.Nodes.ResultField=(ResultFieldExchangeData)arguments[3];}break;
                case "UpdateActorColorContoursVisibility":foreach(string item in (string[])arguments[0])if(actors.TryGetValue(item,out var contourActor))contourActor.Data.ColorContours=(bool)arguments[1];break;
                case "UpdateActor":if(actors.Remove((string)arguments[0],out var renamed)){renamed.Data.Name=(string)arguments[1];renamed.Color=(System.Drawing.Color)arguments[2];actors[renamed.Data.Name]=renamed;}break;
                case "HideActors":case "ShowActors":foreach(string item in (string[])arguments[0])if(actors.TryGetValue(item,out var hidden))hidden.Visible=name=="ShowActors";break;
                case "AddActor":var actor=(vtkMaxActor)arguments[0];if(actor.Data.Layer==vtkRendererLayer.Selection)selectionActors.Add(actor);else actors[actor.Data.Name]=actor;break;
                case "Add3DCells":foreach(var data in (vtkMaxActorData[])arguments[0])actors[data.Name]=new vtkMaxActor(data);break;
                case "CropPartWithCylinder":case "CropPartWithCube":case "SmoothPart":
                    if(nativeGeometry==null)throw new NotSupportedException("Enable the native geometry host for: "+name);
                    nativeGeometry.ProcessSurface(name,actors[(string)arguments[0]].Data,arguments);break;
                case "SaveAutomationScreenshot":
                    if(Screenshot==null)throw new NotSupportedException("A screenshot requires a rendered viewport host.");
                    Screenshot((string)arguments[0],(bool)arguments[1],(int)arguments[2]);break;
            }
            Presentation?.Invoke(name,arguments);
        }
        private T QueryPresentation<T>(string name, object[] arguments)
        {
            object result;
            switch(name)
            {
                case "TryGetAnimationNodeData":
                    arguments[1]=null;arguments[2]=0f;result=false;
                    foreach(var candidate in actors.Values){
                        if(!candidate.Visible)continue;
                        var frames=candidate.Data.Geometry.NodesAnimation;
                        if(frames==null || AnimationFrame<0 || AnimationFrame>=frames.Length)continue;
                        var nodes=frames[AnimationFrame];int index=Array.IndexOf(nodes.Ids??candidate.Data.Geometry.Nodes.Ids??Array.Empty<int>(),(int)arguments[0]);
                        if(index<0)continue;
                        arguments[1]=nodes.Coor!=null?nodes.Coor[index]:new double[]{nodes.FlatCoor[index*3],nodes.FlatCoor[index*3+1],nodes.FlatCoor[index*3+2]};
                        arguments[2]=nodes.Values?[index]??0f;result=true;break;
                    }break;
                case "AddAnimatedScalarFieldOn3DCells":
                    var animated=(vtkMaxActorData)arguments[0];actors[animated.Name]=new vtkMaxActor(animated);result=true;break;
                case "AddAnimatedVectorFieldActor":case "AddAnimatedTensorFieldActor":CaptureRenderCommand(name,arguments);result=true;break;
                case "GetTreeExpandCollapseState":result=treeState;break;
                case "GetStableTreeExpandCollapseState":result=stableTreeState;break;
                case "GetSidePanelsState":result=panels;break;
                case "GetQuerySelection":result=querySelection;break;
                case "GetDeformationVariable":result=deformationVariable;break;
                case "GetDeformationType":result=deformationType;break;
                case "GetDeformationFactor":result=deformationFactor;break;
                case "GetComplexResultType":result=Controller.CurrentResult.ComplexResultType;break;
                case "GetComplexAngleDeg":result=(double)Controller.CurrentResult.ComplexAngleDeg;break;
                case "IsStateOpening":result=workingState==Globals.OpeningText;break;
                case "SetStateWorking":workingState=(string)arguments[0];result=true;break;
                case "Add3DNodes":case "Add3DCells":
                    var data=(vtkMaxActorData)arguments[0];var actor=new vtkMaxActor(data,name=="Add3DNodes");if(data.Layer==vtkRendererLayer.Base)actors[data.Name??Guid.NewGuid().ToString()]=actor;else if(data.Layer==vtkRendererLayer.Selection)selectionActors.Add(actor);result=actor;break;
                case "ContainsActor":result=actors.ContainsKey((string)arguments[0]);break;
                case "GetVtkMaxActorData":result=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(actors.Values,a=>a.GetExportData(edgeVisibility)));break;
                case "GetLookupTable":
                    if(ExportLookupTable==null && System.Linq.Enumerable.Any(actors.Values,a=>a.Data.ColorContours))
                        throw new InvalidOperationException("Supply the renderer lookup table for a contour 3MF export.");
                    result=ExportLookupTable??new vtkMaxLookupTable();break;
                case "GetClosestUpView":result=ExportUpDirection;break;
                case "GetDefaultJobName":result=GetDefaultAnalysisName();break;
                case "GetDefaultJob":
                    var settings=Controller.Settings;
                    string jobName=GetDefaultAnalysisName()??"Analysis-1";
                    result=new AnalysisJob(jobName,settings.Solver.CalculixExe,jobName,settings.GetWorkDirectory());break;
                default:
                    if(Query==null)throw new NotSupportedException("Headless presentation query requires a host: "+name);
                    result=Query(name,arguments);break;
            }
            return (T)result;
        }
        string GetDefaultAnalysisName() => Controller.OpenedFileName==null?null:NamedClass.GetErrorFreeName(Path.GetFileNameWithoutExtension(Controller.OpenedFileName),"Analysis",null);
        void SetResultField(string name,string component,int? step,int? increment)
        {
            FieldData current=Controller.CurrentFieldData;
            if(current==null || Controller.CurrentResult==null)return;
            Controller.CurrentFieldData=Controller.CurrentResult.GetFieldData(name,component,step??current.StepId,increment??current.StepIncrementId,true);
        }
        void OpenJobResults(string name,bool asynchronous)
        {
            LastOpenResultsAccepted=false;
            AnalysisJob job=Controller.GetJob(name);
            string parameters=Globals.FromMonitorForm;
            if(!Controller.BatchRegenerationMode)
            {
                if(job.JobStatus==JobStatus.Running)
                {
                    if(MessageBoxes.ShowWarningQuestionOKCancel("The analysis "+name+" is still running. Continue?")!=System.Windows.Forms.DialogResult.OK)return;
                    parameters+=Globals.NameSeparator+Globals.OpenRunningJobResults;
                }
                else if(!job.IsUpToDate && MessageBoxes.ShowWarningQuestionOKCancel("The result file was modified after the analysis "+name+" completed. Continue?")!=System.Windows.Forms.DialogResult.OK)return;
            }
            Open(Path.Combine(job.WorkDirectory,job.ResultsFileName),Controller.Open,false,parameters);
            LastOpenResultsAccepted=true;
        }
    }
}

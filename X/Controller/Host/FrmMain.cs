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
        public IntPtr Handle => IntPtr.Zero;
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
            switch(name)
            {
                case "Open":
                    ((Action<string,string>)arguments[1])((string)arguments[0],(string)arguments[3]);
                    if(Controller.CurrentView==ViewGeometryModelResults.Geometry)Controller.DrawGeometry((bool)arguments[2]);
                    else if(Controller.CurrentView==ViewGeometryModelResults.Model)Controller.DrawModel((bool)arguments[2]);
                    else Controller.ViewResultsType=ViewResultsTypeEnum.ColorContours;
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
                        if(!Enum.TryParse(arguments[0] as string,out units))units=UnitSystemType.UNIT_LESS;
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
                case "Clear3D":case "ClearControls":actors.Clear();break;
                case "HideActors":case "ShowActors":foreach(string item in (string[])arguments[0])if(actors.TryGetValue(item,out var hidden))hidden.Visible=name=="ShowActors";break;
                case "AddActor":var actor=(vtkMaxActor)arguments[0];actors[actor.Data.Name]=actor;break;
                case "Add3DCells":foreach(var data in (vtkMaxActorData[])arguments[0])actors[data.Name]=new vtkMaxActor(data);break;
                case "CropPartWithCylinder":case "CropPartWithCube":case "SmoothPart":
                    if(nativeGeometry==null)throw new NotSupportedException("Enable the native geometry host for: "+name);
                    nativeGeometry.ProcessSurface(name,actors[(string)arguments[0]].Data,arguments);break;
                case "SaveAutomationScreenshot":
                    throw new NotSupportedException("A screenshot requires a rendered viewport host.");
            }
            Presentation?.Invoke(name,arguments);
        }
        private T QueryPresentation<T>(string name, object[] arguments)
        {
            object result;
            switch(name)
            {
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
                    var data=(vtkMaxActorData)arguments[0];var actor=new vtkMaxActor(data,name=="Add3DNodes");if(data.Layer==vtkRendererLayer.Base)actors[data.Name??Guid.NewGuid().ToString()]=actor;result=actor;break;
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
            Controller.Open(Path.Combine(job.WorkDirectory,job.ResultsFileName),parameters);
            LastOpenResultsAccepted=true;
        }
    }
}

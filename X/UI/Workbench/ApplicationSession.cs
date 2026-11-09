using CaeGlobals;
using CaeModel;
using CaeMesh;
using PrePoMax;
using PrePoMax.Commands;
using PrePoMax.Forms;
using PrePoMax.Python;
using PrePoMax.Python.Journal;
using PrePoMax.Rpc;

namespace PrePoMaxX.UI;
// Application actions delegate to the same Controller, serializers and automation engine.
public sealed class ApplicationSession : IDisposable
{
    readonly HeadlessSession session;
    readonly Controller controller;
    volatile int scriptThread;
    public RpcServer Automation {get;}
    public ApplicationSession(HeadlessSession value){session=value;controller=value.Controller;Automation=new RpcServer(value.Presentation,controller);}
    public SettingsEditSession Settings()=>new(controller,()=>Automation.EndpointUrl);
    public CommandEditSession History()=>new(controller);
    public MaterialLibrarySession Library()=>new(controller);
    public UserViewsSession UserViews()=>new(controller);
    public FollowerEditSession Follower()=>new(controller);
    public void ImportMaterials(string file)=>controller.ImportFileCommand(Path.GetFullPath(file),true);
    public void Export(string file,bool abaqus){if(abaqus)controller.ExportToAbaqusCommand(file);else controller.ExportToCalculixCommand(file);}
    public void Export3mf(Export3mfFileProperties properties)=>controller.ExportTo3mfCommand(properties);
    public void Parameters(string file,bool import){if(import)controller.ImportParametersCommand(file);else controller.ExportParametersCommand(file);}
    public Task Regenerate(bool files,bool meshes,string type)=>Task.Run(()=>controller.RegenerateHistoryCommands(files,meshes,Enum.Parse<RegenerateTypeEnum>(type)));
    public Task<PythonEngineResult> Execute(string source,bool recordScript,string file=null,string[] arguments=null)=>Task.Run(()=>{
        scriptThread=Environment.CurrentManagedThreadId;
        try { session.Presentation.PrepareAutomationPythonEngine();
        if(recordScript)return controller.RunPythonScriptCommand(source,file,arguments);
        return controller.ExecutePythonWithKeywordStateReport(()=>PythonEngineManager.ExecuteScript(source));}finally{scriptThread=0;}});
    public Task Open(string path)=>Task.Run(()=>session.Open(path));
    public bool InterruptPython()=>PythonEngineManager.RequestInterrupt(PythonEngineManager.GetExecution(scriptThread),0,out _);
    public void LoadPreferences(string file){var data=Tools.LoadDumpFromFile<Dictionary<string,ISettings>>(Path.GetFullPath(file));foreach(var value in data.Values)value.CheckValues();controller.Settings=new SettingsContainer(data);}
    public void SavePreferences(string file){file=Path.GetFullPath(file);Directory.CreateDirectory(Path.GetDirectoryName(file));string temporary=file+"."+Guid.NewGuid().ToString("N")+".tmp";try{if(!OperatingSystem.IsWindows()){using var reserved=new FileStream(temporary,new FileStreamOptions{Mode=FileMode.CreateNew,Access=FileAccess.Write,UnixCreateMode=UnixFileMode.UserRead|UnixFileMode.UserWrite});}controller.Settings.ToDictionary().DumpToFile(temporary);File.Move(temporary,file,true);}finally{if(File.Exists(temporary))File.Delete(temporary);}}
    public void Rename(string family,string step,string oldName,string newName){
        string method=family switch{"Geometry parts"=>"GetGeometryPart","Parts"=>"GetModelPart","Result parts"=>"GetResultPart","Result reference points"=>"GetResultReferencePoint","Result coordinate systems"=>"GetResultCoordinateSystem","Node sets"=>"GetNodeSet","Element sets"=>"GetElementSet","Surfaces"=>"GetSurface","Reference points"=>"GetModelReferencePoint","Coordinate systems"=>"GetModelCoordinateSystem","Surface interactions"=>"GetSurfaceInteraction","Contact pairs"=>"GetContactPair","Initial conditions"=>"GetInitialCondition","Boundary conditions"=>"GetBoundaryCondition","Defined fields"=>"GetDefinedField","History outputs"=>"GetHistoryOutput","Field outputs"=>"GetFieldOutput","Jobs"=>"GetJob",_=>"Get"+(family.EndsWith("ies")?family[..^3]+"y":family.TrimEnd('s'))};
        var args=step==null?new object[]{oldName}:new object[]{step,oldName};var getter=typeof(Controller).GetMethod(method,args.Select(v=>v.GetType()).ToArray())??throw new NotSupportedException("Original rename provider unavailable: "+family);
        var item=(NamedClass)getter.Invoke(controller,args);if(!controller.CheckItemName(item,newName,step))throw new CaeException("The name is invalid or already in use.");controller.RenameCommand(item,newName,step,controller.CurrentView);
    }
    public void ResetPython()=>PythonEngineManager.ResetScope();
    public string Journal(string file)=>PythonJournalExporter.Export(controller.GetActiveCommands(),file,"PrePoMax-X active history",1,controller.GetWorkDirectory()).ToString();
    public void Dispose()=>Automation.Stop();
    public string GenerateAccessToken(){string token=PrePoMax.Mcp.McpAccessToken.Generate();controller.SaveAutomationAccessToken(token);return token;}
    public void ClearAccessToken(){Automation.Stop();controller.SaveAutomationAccessToken("");}
    public string[] CheckModel()=>controller.CheckAndUpdateModelValidity();
    public void Find(string kind,int id,bool annotate)
    {
        controller.ClearSelectionHistoryAndCallSelectionChanged();
        if(kind=="Node"){controller.HighlightNode(id);if(annotate)controller.Annotations.AddNodeAnnotation(id);}
        else if(kind=="Element"){controller.HighlightElement(id);if(annotate)controller.Annotations.AddElementAnnotation(id);}
        else if(kind=="Part"){var part=controller.DisplayedMesh.GetPartFromId(id);if(part!=null){controller.Highlight3DObjects([part]);if(part.Visible && annotate)controller.Annotations.AddPartAnnotation(part.Name);}}
        else foreach(int partId in controller.DisplayedMesh.GetVisiblePartIds())
        {
            int value=(id-1)*100000+(int)(kind=="Edge"?GeometryType.Edge:GeometryType.SolidSurface)*10000+partId;
            try{if(kind=="Edge"){controller.HighlightItemsByGeometryEdgeIds([value],false);if(annotate)controller.Annotations.AddEdgeAnnotation(value);}
            else{controller.HighlightItemsBySurfaceIds([value],false);if(annotate)controller.Annotations.AddSurfaceAnnotation(value);}}catch{}
        }
    }
}

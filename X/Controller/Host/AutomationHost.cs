using System;
using System.Threading.Tasks;
using PrePoMax.Python;
using CaeGlobals;
namespace PrePoMax;
public partial class FrmMain
{
    public Func<string> AutomationBusyReason {get;set;}
    public Action<Action> PostToUi {get;set;}
    public Action AutomationExit {get;set;}
    public bool IsDisposed {get;set;}
    public bool IsHandleCreated=>PostToUi!=null && !IsDisposed;
    public string AutomationModelFileName=>Controller?.OpenedFileName;
    public string GetAutomationBusyReason()=>AutomationBusyReason?.Invoke() ?? (workingState==null?null:"PrePoMax is busy: "+workingState);
    public IAsyncResult BeginInvoke(System.Windows.Forms.MethodInvoker callback)
    {
        if(!IsHandleCreated)throw new InvalidOperationException("The application window is not available.");
        var task=new TaskCompletionSource();
        PostToUi(()=>{try{callback();task.SetResult();}catch(Exception error){task.SetException(error);}});
        return task.Task;
    }
    public void PrepareAutomationPythonEngine()=>PythonEngineManager.SetResults(Controller.AllResults,Controller);
    public void EchoAutomationExecution(string label,string source,string output,string error)
    {
        if(!Controller.AutomationSettings.EchoToPythonPanel)return;
        string note=Rpc.RpcDispatcher.CurrentEchoNote;
        WriteDataToOutput(note??label);
        if(note==null)WriteDataToOutput(source+"\n"+output+error);
    }
    public void RequestAutomationExit()=>PostToUi?.Invoke(()=>AutomationExit?.Invoke());
}

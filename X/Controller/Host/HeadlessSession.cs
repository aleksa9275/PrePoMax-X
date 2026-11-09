using System;
using System.IO;
using System.Reflection;
using CaeGlobals;
using CaeModel;
using PrePoMaxX.Persistence;
namespace PrePoMax
{
    public sealed class HeadlessSession
    {
        static readonly Lazy<NrbfTypePolicy> policy=new(CreatePolicy);
        public FrmMain Presentation {get;}
        public Controller Controller {get;}
        public static void InstallPersistence() {System.Text.Encoding.RegisterProvider(System.Text.CodePagesEncodingProvider.Instance);RuntimeInitialization.SetCultureAndLanguage();BinarySerialization.Factory=()=>new RestrictedNrbfSerializer(policy.Value);}
        public HeadlessSession(string workDirectory,Action<string> output=null)
        {
            if(!Path.IsPathFullyQualified(workDirectory))throw new ArgumentException("Work directory must be absolute.");
            Directory.CreateDirectory(workDirectory);
            InstallPersistence();
            MessageBoxes.Mode=MessageBoxModeEnum.Strict;
            NativeTools.EnablePlatformExecutables();
            CaeJob.ExecutableJob.ProcessLogDirectoryFactory=(directory,name)=>
                Path.Combine(directory,"native-logs",name+"-"+Guid.NewGuid().ToString("N"));
            // Headless runs use session settings, never the installed user's file.
            SettingsContainer.OverrideFileName=Path.Combine(workDirectory,"settings.bin");
            SettingsContainer.IsSaveDisabled=true;
            Presentation=new FrmMain {Presentation=(name,args)=> {if(name is "WriteDataToOutput" or "WriteErrorToOutput")output?.Invoke((string)args[0]);}};
            Controller=new Controller(Presentation);
            Controller.RegenerationWorkDirectory=workDirectory;
        }
        public void Open(string fileName)
        {
            string extension=Path.GetExtension(fileName).ToLowerInvariant();
            if(extension is ".pmx" or ".pmh" or ".frd" or ".dat" or ".odb" or ".foam")
                Presentation.Open(fileName,Controller.OpenFileCommand,false);
            else Controller.ImportFileCommand(fileName,false);
        }
        public Python.PythonEngineResult RunScript(string fileName,string[] arguments=null)
        {
            return Controller.RunPythonScriptCommand(File.ReadAllText(fileName),fileName,arguments);
        }
        static NrbfTypePolicy CreatePolicy()
        {
            Assembly[] assemblies={typeof(Controller).Assembly,typeof(FeModel).Assembly,typeof(CaeMesh.FeMesh).Assembly,typeof(CaeResults.FeResults).Assembly,typeof(CaeJob.AnalysisJob).Assembly,typeof(NamedClass).Assembly,typeof(vtkControl.vtkMaxActorData).Assembly,typeof(UserControls.SidePanelsState).Assembly,typeof(System.Windows.Forms.DialogResult).Assembly};
            using var resource=typeof(HeadlessSession).Assembly.GetManifestResourceStream("PrePoMaxX.AllowedTypes");
            using var reader=new StreamReader(resource);
            return new NrbfTypePolicy(assemblies,reader.ReadToEnd().Split(new[]{'\r','\n'},StringSplitOptions.RemoveEmptyEntries));
        }
    }
}

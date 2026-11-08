using PrePoMax;
using PrePoMax.Python;

// Phase B development host. The original application CLI/GUI remains separate.
// This runs original recorded Python commands on the original Controller.
if(args.Length<4 || args[0]!="run")
{
    Console.Error.WriteLine("Usage: PrePoMaxX.Headless run SCRIPT WORK_DIRECTORY PYTHON_PROFILE [PROJECT] [NATIVE_TOOL_MANIFEST]");
    return 2;
}
try
{
    string work=Path.GetFullPath(args[2]);
    PythonEngineManager.NativeRuntimeProfile=Path.GetFullPath(args[3]);
    var session=new HeadlessSession(work,Console.WriteLine);
    if(args.Length>5)NativeTools.Configure(Path.GetFullPath(args[5]));
    using var spatial=session.Presentation.EnableNativeSpatialQueries();
    if(args.Length>4)session.Open(Path.GetFullPath(args[4]));
    var result=session.RunScript(Path.GetFullPath(args[1]));
    Console.Write(result.Output);
    Console.Error.Write(result.GetErrorText());
    return string.IsNullOrEmpty(result.Error)?0:1;
}
catch(Exception error) {Console.Error.WriteLine(error);return 1;}

using PrePoMax;
using PrePoMax.Python;
using PrePoMaxX.UI;
using Python.Runtime;

// .NET owns the application and original engineering objects. Python/Qt only
// builds presentation widgets on this main thread; it does not load another CLR.
if(args.Length<3)
{
    Console.Error.WriteLine("Usage: PrePoMaxX.Workbench PYTHON_PROFILE WORK_DIRECTORY UI_SCRIPT [UI_ARGUMENTS...]");
    return 2;
}
try
{
    PythonEngineManager.NativeRuntimeProfile=Path.GetFullPath(args[0]);
    var session=new HeadlessSession(Path.GetFullPath(args[1]),Console.WriteLine);
    PythonEngineManager.EnsureNativeHostInitialized();
    using var spatial=session.Presentation.EnableNativeSpatialQueries();
    using(Py.GIL())
    {
        using var scope=Py.CreateScope();
        scope.Set("session",session);
        scope.Set("ui_arguments",args.Skip(3).ToArray());
        scope.Set("ui_directory",Path.GetDirectoryName(Path.GetFullPath(args[2])));
        scope.Exec("import sys\nsys.path.insert(0, ui_directory)\n");
        scope.Exec(File.ReadAllText(Path.GetFullPath(args[2])));
    }
    return 0;
}
catch(Exception error) {Console.Error.WriteLine(error);return 1;}

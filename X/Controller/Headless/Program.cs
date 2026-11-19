using CaeGlobals;
using PrePoMax;
using PrePoMax.Python;

// Phase B development host. The original application CLI/GUI remains separate.
// This runs original recorded Python commands on the original Controller.
// Options after the positional arguments follow the original PrePoMax.com batch start (FrmMain): with
// --unit-system an imported file starts a new 3D model in that unit system (-f FILE -u UNITS), --script-args are
// the script's sys.argv (--scriptArgs), and --solver selects the verified CalculiX build the settings use.
// --default-solver-type sets Settings - Solver - Default solver type explicitly (the original default, PARDISO, is
// the Intel library that the non-Windows builds lack, D060); without it the original default stays.
const string usage="Usage: PrePoMaxX.Headless run SCRIPT WORK_DIRECTORY PYTHON_PROFILE [PROJECT] [NATIVE_TOOL_MANIFEST]\n"+
                   "       [--unit-system UNITS] [--script-args \"ARGS\"] [--solver REGISTRY BUILD_ID DIRECTORY] [--default-solver-type TYPE]";
var positional=new List<string>();
string? unitSystem=null,scriptArguments=null,solverType=null;
string[]? solver=null;
for(int i=0;i<args.Length;i++)
{
    if(args[i]=="--unit-system" && i+1<args.Length)unitSystem=args[++i];
    else if(args[i]=="--script-args" && i+1<args.Length)scriptArguments=args[++i];
    else if(args[i]=="--default-solver-type" && i+1<args.Length)solverType=args[++i];
    else if(args[i]=="--solver" && i+3<args.Length){solver=args[(i+1)..(i+4)];i+=3;}
    else if(args[i].StartsWith("--",StringComparison.Ordinal)){Console.Error.WriteLine(usage);return 2;}
    else positional.Add(args[i]);
}
if(positional.Count<4 || positional[0]!="run")
{
    Console.Error.WriteLine(usage);
    return 2;
}
try
{
    string work=Path.GetFullPath(positional[2]);
    PythonEngineManager.NativeRuntimeProfile=Path.GetFullPath(positional[3]);
    var session=new HeadlessSession(work,Console.WriteLine);
    if(positional.Count>5)NativeTools.Configure(Path.GetFullPath(positional[5]));
    if(solver!=null)session.UseSolver(SolverRuntime.Validate(Path.GetFullPath(solver[0]),solver[1],Path.GetFullPath(solver[2])));
    if(solverType!=null)
    {
        if(!Enum.TryParse(solverType,true,out CaeModel.SolverTypeEnum type) || type==CaeModel.SolverTypeEnum.Default)
            throw new CaeException("The solver type "+solverType+" is not supported.");
        session.SetDefaultSolverType(type);
    }
    using var spatial=session.Presentation.EnableNativeSpatialQueries();
    UnitSystemType units=UnitSystemType.Undefined;
    if(unitSystem!=null && !Enum.TryParse(unitSystem.ToUpperInvariant(),out units))
        throw new CaeException("The unit system type "+unitSystem+" is not supported.");
    if(positional.Count>4 && positional[4]!="")session.Open(Path.GetFullPath(positional[4]),units);
    string[]? arguments=scriptArguments?.Split(new[]{' '},StringSplitOptions.RemoveEmptyEntries);
    var result=session.RunScript(Path.GetFullPath(positional[1]),arguments);
    Console.Write(result.Output);
    Console.Error.Write(result.GetErrorText());
    return string.IsNullOrEmpty(result.Error)?0:1;
}
catch(Exception error) {Console.Error.WriteLine(error);return 1;}

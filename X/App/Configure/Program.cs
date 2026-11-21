// Configures an X/App build of PrePoMax (M2): writes PrePoMaxX.runtime.json beside PrePoMax.dll (the CPython 3.12
// profile, the Qt user interface folder, the native tool manifest, the patched Gmsh library) and, with --solver, the original settings file of the
// application folder (Globals.SettingsFileName, read by SettingsContainer.LoadFromFile) with the verified CalculiX
// build and, if given, the default solver type. Every path is explicit; an existing settings file is replaced only
// with --replace-settings, and only its solver settings change. --work-directory sets the solver's work directory
// (created if missing) when the settings have none that exists: the original has none until the user sets one, and
// CAD import and analyses need it; a directory the user chose is kept.
using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using PrePoMax;

const string usage = "Usage: PrePoMaxX.Configure --app DIRECTORY --python PROFILE [--ui X/UI] [--native-tools MANIFEST] [--gmsh-library LIBRARY]\n" +
                     "       [--solver REGISTRY BUILD_ID DIRECTORY] [--default-solver-type TYPE] [--work-directory DIRECTORY] [--replace-settings]";
string app = null, python = null, ui = null, tools = null, gmsh = null, solverType = null, work = null;
string[] solver = null;
bool replace = false;
for (int i = 0; i < args.Length; i++)
{
    if (args[i] == "--app" && i + 1 < args.Length) app = args[++i];
    else if (args[i] == "--python" && i + 1 < args.Length) python = args[++i];
    else if (args[i] == "--native-tools" && i + 1 < args.Length) tools = args[++i];
    else if (args[i] == "--ui" && i + 1 < args.Length) ui = args[++i];
    else if (args[i] == "--gmsh-library" && i + 1 < args.Length) gmsh = args[++i];
    else if (args[i] == "--default-solver-type" && i + 1 < args.Length) solverType = args[++i];
    else if (args[i] == "--solver" && i + 3 < args.Length) { solver = args[(i + 1)..(i + 4)]; i += 3; }
    else if (args[i] == "--work-directory" && i + 1 < args.Length) work = args[++i];
    else if (args[i] == "--replace-settings") replace = true;
    else { Console.Error.WriteLine(usage); return 2; }
}
if (app == null || python == null) { Console.Error.WriteLine(usage); return 2; }
try
{
    string Full(string path) => path == null ? null : Path.GetFullPath(path);
    app = Full(app);
    if (!File.Exists(Path.Combine(app, "PrePoMax.dll"))) throw new FileNotFoundException("No PrePoMax.dll in " + app);
    var runtime = new Dictionary<string, object> { ["schemaVersion"] = 1, ["python"] = Full(python) };
    if (tools != null) runtime["nativeTools"] = Full(tools);
    if (ui != null)
    {
        if (!File.Exists(Path.Combine(Full(ui), "main_form.py"))) throw new FileNotFoundException("No main_form.py in " + ui);
        runtime["ui"] = Full(ui);
    }
    if (gmsh != null) runtime["gmshLibrary"] = Full(gmsh);
    string runtimeFile = Path.Combine(app, "PrePoMaxX.runtime.json");
    File.WriteAllText(runtimeFile, JsonSerializer.Serialize(runtime, new JsonSerializerOptions { WriteIndented = true }) + "\n");
    Console.WriteLine("wrote " + runtimeFile);
    if (solver != null || solverType != null || work != null)
    {
        string settingsFile = Path.Combine(app, Globals.SettingsFileName);
        if (File.Exists(settingsFile) && !replace) throw new IOException(settingsFile + " exists; use --replace-settings to change its solver settings.");
        SettingsContainer.OverrideFileName = settingsFile;
        var settings = new SettingsContainer();
        settings.LoadFromFile();
        if (solver != null) settings.Solver.CalculixExe = SolverRuntime.Validate(Full(solver[0]), solver[1], Full(solver[2]));
        if (solverType != null)
        {
            if (!Enum.TryParse(solverType, true, out CaeModel.SolverTypeEnum type) || type == CaeModel.SolverTypeEnum.Default)
                throw new ArgumentException("The solver type " + solverType + " is not supported.");
            settings.Solver.CalculixDefaultSolverType = type;
        }
        string current = settings.Solver.WorkDirectoryForSettingsOnly;
        if (work != null && (string.IsNullOrEmpty(current) || !Directory.Exists(current)))
        {
            Directory.CreateDirectory(Full(work));
            settings.Solver.WorkDirectoryForSettingsOnly = Full(work);
        }
        settings.SaveToFile(settingsFile);
        Console.WriteLine("wrote " + settingsFile + " (CalculiX " + settings.Solver.CalculixExe + ", " + settings.Solver.CalculixDefaultSolverType +
                          ", work directory " + settings.Solver.WorkDirectoryForSettingsOnly + ")");
    }
    return 0;
}
catch (Exception error) { Console.Error.WriteLine(error.Message); return 1; }

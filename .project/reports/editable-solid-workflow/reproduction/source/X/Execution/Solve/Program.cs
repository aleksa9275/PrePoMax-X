using System.Globalization;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using CaeJob;
using PrePoMaxX.StaticDeck;
using PrePoMaxX.MeshDeck;
namespace PrePoMaxX.Solve;

public static class SolverBuilds
{
    public static string HostOs => OperatingSystem.IsWindows()?"Windows":OperatingSystem.IsMacOS()?"Darwin":"Linux";
    public static string HostArchitecture => RuntimeInformation.ProcessArchitecture.ToString();
    public static string Hash(string path) => Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(path)));
    public static JsonElement Read(string path)
    {
        using var document=JsonDocument.Parse(File.ReadAllText(path));
        if(document.RootElement.GetProperty("schemaVersion").GetInt32()!=1)throw new InvalidDataException("Unknown solver build registry schema.");
        return document.RootElement.Clone();
    }
    public static JsonElement Select(JsonElement registry,string id)
    {
        var candidates=registry.GetProperty("builds").EnumerateArray().Where(b=>b.GetProperty("id").GetString()==id).ToArray();
        if(candidates.Length!=1)throw new InvalidDataException("No uniquely pinned solver build: "+id);
        var build=candidates[0];
        if(build.GetProperty("os").GetString()!=HostOs||build.GetProperty("architecture").GetString()!=HostArchitecture)
            throw new InvalidDataException("Pinned build does not match native host. Matching native solver source/build provenance remains open; no substitute is selected.");
        return build;
    }
    public static string ValidateFiles(JsonElement build,string directory)
    {
        string executable=build.GetProperty("executable").GetString()!;
        var files=build.GetProperty("files").EnumerateObject().ToArray();
        if(!files.Any(p=>p.Name==executable))throw new InvalidDataException("Executable is not fingerprinted.");
        foreach(var entry in files)
        {
            if(Path.GetFileName(entry.Name)!=entry.Name||entry.Name.Contains('\\')||entry.Name is "." or "..")throw new InvalidDataException("Build file must be a simple basename.");
            string file=Path.Combine(directory,entry.Name);
            if(!File.Exists(file)||Hash(file)!=entry.Value.GetString())throw new InvalidDataException("Pinned solver/runtime file missing or changed: "+entry.Name);
        }
        if(build.TryGetProperty("externalFiles",out var external))
            foreach(var entry in external.EnumerateObject())
            {
                if(!Path.IsPathFullyQualified(entry.Name))throw new InvalidDataException("External runtime path must be absolute.");
                if(!File.Exists(entry.Name)||Hash(entry.Name)!=entry.Value.GetString())throw new InvalidDataException("Pinned external runtime missing or changed: "+entry.Name);
            }
        return Path.GetFullPath(Path.Combine(directory,executable));
    }
}

internal static class Program
{
    private static async Task ReadCancellationAsync(CancellationTokenSource cancel)
    {
        try
        {
            while(await Console.In.ReadLineAsync() is string line)
                if(line=="cancel"){cancel.Cancel();return;}
        }
        catch(ObjectDisposedException) { } // The job may finish before input arrives.
        catch(IOException) { } // A closed parent pipe is not a cancellation request.
    }

    private static async Task<int> Main(string[] args)
    {
        CultureInfo.CurrentCulture=CultureInfo.InvariantCulture;
        string registryPath=Path.Combine(AppContext.BaseDirectory,"solver-builds.json");
        bool solverExecuted=false;
        try
        {
            if(args.Length>=1&&args[0]=="--registry")
            {
                if(args.Length<3)throw new ArgumentException("--registry requires a registry path and command.");
                registryPath=Path.GetFullPath(args[1]);args=args[2..];
            }
            if(args.Length==3&&args[0]=="validate-static")
            {
                var validationMesh=MeshFiles.Read(args[1]);var validationSpec=AnalysisFiles.Read(args[2]);
                string validationDeck=AnalysisFiles.Build(validationMesh,validationSpec);
                Console.WriteLine(JsonSerializer.Serialize(new{success=true,solverExecuted=false,
                    unitSystem=validationSpec.UnitSystem,nodes=validationMesh.Nodes.Count,elements=validationMesh.Elements.Count,
                    materials=validationSpec.Materials.Length,sections=validationSpec.Sections.Length,
                    constraints=validationSpec.Step.Constraints.Length,loads=validationSpec.Step.Loads.Length,
                    deckSha256=Convert.ToHexStringLower(SHA256.HashData(Encoding.UTF8.GetBytes(validationDeck)))}));return 0;
            }
            var registry=SolverBuilds.Read(registryPath);
            if(args.Length>=1&&args[0]=="thread-plan")
            {
                int? manual=null;int jobs=1;var seen=new HashSet<string>(StringComparer.Ordinal);
                for(int i=1;i<args.Length;i+=2)
                {
                    string option=args[i];
                    if(option is not ("--threads" or "--jobs")||!seen.Add(option)||i+1>=args.Length)
                        throw new ArgumentException("thread-plan accepts unique --threads auto|N and --jobs N pairs.");
                    string value=args[i+1];
                    if(option=="--threads"&&value=="auto")continue;
                    if(!int.TryParse(value,NumberStyles.None,CultureInfo.InvariantCulture,out int count)||count<1)
                        throw new ArgumentException("Thread and job counts must be positive decimal integers.");
                    if(option=="--threads")manual=count;else jobs=count;
                }
                var plan=SolverThreadPlan.Create(Environment.ProcessorCount,jobs,manual);
                Console.WriteLine(JsonSerializer.Serialize(new{success=true,plan,solverExecuted=false,settingsChanged=false,reservationEnforced=false,cpuUtilizationLimit=false}));return 0;
            }
            if(args.Length==3&&args[0]=="inspect-monitor")
            {
                if(new FileInfo(args[1]).Length>16*1024*1024||new FileInfo(args[2]).Length>16*1024*1024)throw new InvalidDataException("Monitor input exceeds bounded 16 MiB limit.");
                var status=CalculixMonitorDataParser.ParseStatus(File.ReadAllText(args[1]));
                var convergence=CalculixMonitorDataParser.ParseConvergence(File.ReadAllText(args[2]));
                Console.WriteLine(JsonSerializer.Serialize(new{success=true,solverExecuted=false,status,convergence}));return 0;
            }
            if(args.Length==1&&args[0]=="availability")
            {
                var builds=registry.GetProperty("builds").EnumerateArray().Where(b=>b.GetProperty("os").GetString()==SolverBuilds.HostOs&&b.GetProperty("architecture").GetString()==SolverBuilds.HostArchitecture).Select(b=>b.GetProperty("id").GetString()).ToArray();
                Console.WriteLine(JsonSerializer.Serialize(new{success=true,os=SolverBuilds.HostOs,architecture=SolverBuilds.HostArchitecture,pinnedBuilds=builds,solverAvailable=builds.Length==0?(bool?)false:null,binaryAvailabilityChecked=false,solverExecuted=false}));return 0;
            }
            if(args.Length!=7||args[0]!="run-static") {Console.Error.WriteLine("Usage: PrePoMaxX.Solve [--registry <explicit-build-registry.json>] validate-static <mesh.inp> <analysis.json> | thread-plan [--threads auto|N] [--jobs N] | availability | inspect-monitor <status.sta> <convergence.cvg> | run-static <build-id> <solver-directory> <mesh.inp> <analysis.json> <new-run-directory> <timeout-seconds>");return 2;}
            var build=SolverBuilds.Select(registry,args[1]);string executable=SolverBuilds.ValidateFiles(build,Path.GetFullPath(args[2]));
            double timeout=double.Parse(args[6],CultureInfo.InvariantCulture);
            if(!double.IsFinite(timeout)||timeout<=0||timeout>86400)throw new InvalidDataException("Timeout must be finite and in (0,86400] seconds.");
            var mesh=MeshFiles.Read(args[3]);var spec=AnalysisFiles.Read(args[4]);string deck=AnalysisFiles.Build(mesh,spec);
            string directory=Path.GetFullPath(args[5]);
            if(Directory.Exists(directory)||File.Exists(directory))throw new IOException("Run directory must be new.");
            // Parent exists, and a CreateNew reservation prevents two CLI instances
            // from sharing or overwriting one run directory.
            string reservation=directory+".reservation";
            using var lease=new FileStream(reservation,FileMode.CreateNew,FileAccess.Write,FileShare.None);
            try
            {
                if(Directory.Exists(directory)||File.Exists(directory))throw new IOException("Run directory already exists.");
                Directory.CreateDirectory(directory);AnalysisFiles.WriteNew(Path.Combine(directory,"analysis.inp"),deck);
                var job=new ExecutableJob("analysis",executable,"",directory){ProcessArguments=new[]{"-i","analysis"},TimeLimit=TimeSpan.FromSeconds(timeout),ProcessEnvironment=new Dictionary<string,string>{{"OMP_NUM_THREADS","1"},{"MKL_NUM_THREADS","1"},{"OPENBLAS_NUM_THREADS","1"}}};
                using var cancel=new CancellationTokenSource();ConsoleCancelEventHandler handler=(_,e)=>{e.Cancel=true;cancel.Cancel();};Console.CancelKeyPress+=handler;
                // A GUI uses redirected stdin for cooperative cancellation. EOF is
                // harmless; it must not cancel ordinary shell/CI invocations.
                if(Console.IsInputRedirected) _=Task.Run(()=>ReadCancellationAsync(cancel));
                try{await job.SubmitAsync(cancel.Token);}finally{Console.CancelKeyPress-=handler;solverExecuted=job.ProcessStarted;}
                bool versionMatches=System.Text.RegularExpressions.Regex.IsMatch(job.CapturedStandardOutput,@"CalculiX Version\s+"+System.Text.RegularExpressions.Regex.Escape(build.GetProperty("version").GetString()!)+@"(?:\s|,)");
                bool outputsPresent=new[]{".dat",".frd",".sta"}.All(s=>new FileInfo(Path.Combine(directory,"analysis"+s))is{Exists:true,Length:>0});
                bool success=job.JobStatus==JobStatus.OK&&versionMatches&&outputsPresent;
                var result=new{success,solverExecuted,buildId=args[1],registrySha256=SolverBuilds.Hash(registryPath),build,os=SolverBuilds.HostOs,architecture=SolverBuilds.HostArchitecture,status=job.JobStatus.ToString(),exitCode=job.ExitCode,versionMatches,outputsPresent,stdout=job.CapturedStandardOutput,stderr=job.CapturedStandardError,failureReason=job.FailureReason,numericalAcceptance=false,outputs=Directory.EnumerateFiles(directory).ToDictionary(Path.GetFileName,p=>SolverBuilds.Hash(p))};
                string json=JsonSerializer.Serialize(result,new JsonSerializerOptions{WriteIndented=true});AnalysisFiles.WriteNew(Path.Combine(directory,"run.json"),json+"\n");Console.WriteLine(json);return success?0:1;
            }
            finally{lease.Dispose();File.Delete(reservation);}
        }
        catch(Exception e)when(e is IOException or InvalidDataException or ArgumentException or CaeGlobals.CaeException or JsonException or NotSupportedException or FormatException or OverflowException or UnauthorizedAccessException or KeyNotFoundException or InvalidOperationException)
        {Console.Error.WriteLine(JsonSerializer.Serialize(new{success=false,solverExecuted,error=e.Message}));return 1;}
    }
}

using System.Formats.Nrbf;
using System.Globalization;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

// Independent research comparison. Raw private values/fingerprints never leave this process.
internal static class Program
{
    static readonly byte[] Key=RandomNumberGenerator.GetBytes(32);
    static string Token(object? value)
    {
        string text=value switch {
            null=>"null",
            ArrayRecord array=>"array:"+array.TypeName.AssemblyQualifiedName+":"+string.Join(",",array.Lengths.ToArray()),
            SerializationRecord record=>"reference:"+record.TypeName.AssemblyQualifiedName,
            double number=>"Double:"+BitConverter.DoubleToInt64Bits(number).ToString("X16"),
            float number=>"Single:"+BitConverter.SingleToInt32Bits(number).ToString("X8"),
            string item=>"String:"+item,
            DateTime date=>"DateTime:"+date.ToBinary().ToString(CultureInfo.InvariantCulture),
            IConvertible scalar=>scalar.GetType().FullName+":"+scalar.ToString(CultureInfo.InvariantCulture),
            _=>throw new InvalidDataException("Unsupported scalar kind")};
        return Convert.ToHexString(HMACSHA256.HashData(Key,Encoding.UTF8.GetBytes(text)));
    }
    static Dictionary<string,List<Dictionary<string,string>>> Read(string path,out ClassRecord[] jobs,out string[] environmentKinds)
    {
        using var stream=File.OpenRead(path);
        if(stream.Length<18 || stream.Length>128L*1024*1024)throw new InvalidDataException("Graph length limit");
        NrbfDecoder.Decode(stream,out var records,leaveOpen:true);
        if(stream.Position!=stream.Length || records.Count>1_000_000)throw new InvalidDataException("Graph trailing bytes or record limit");
        var classes=records.Values.OfType<ClassRecord>().ToArray();
        jobs=classes.Where(r=>r.TypeName.FullName=="CaeJob.AnalysisJob").ToArray();
        environmentKinds=classes.Where(r=>r.TypeName.FullName=="CaeJob.EnvironmentVariable").Select(r=>{
            string? name=r.GetRawValue("<Name>k__BackingField") as string;
            return name is "OMP_NUM_THREADS" or "MKL_NUM_THREADS" or "OPENBLAS_NUM_THREADS"?name:"other/redacted";
        }).Order().ToArray();
        return classes.Where(r=>r.TypeName.FullName.StartsWith("CaeModel.",StringComparison.Ordinal)
                || r.TypeName.FullName=="CaeGlobals.EquationContainer" || r.TypeName.FullName=="CaeGlobals.UnitSystem"
                || r.TypeName.FullName=="CaeJob.AnalysisJob")
            .GroupBy(r=>r.TypeName.AssemblyQualifiedName).ToDictionary(g=>g.Key,
                g=>g.Select(r=>r.MemberNames.OrderBy(m=>m,StringComparer.Ordinal).ToDictionary(m=>m,m=>Token(r.GetRawValue(m)))).ToList());
    }
    static string Bundle(Dictionary<string,string> values)=>JsonSerializer.Serialize(values);
    static int? EnvironmentCount(ClassRecord record)
    {
        if(!record.MemberNames.Contains("_environmentVariables"))return null;
        var value=record.GetRawValue("_environmentVariables");
        return value is ClassRecord list && list.MemberNames.Contains("_size")?Convert.ToInt32(list.GetRawValue("_size")):null;
    }
    static int Main(string[] args)
    {
        if(args.Length!=2){Console.WriteLine("{\"success\":false}");return 2;}
        try {
            var before=Read(args[0],out var oldJobs,out var oldEnvironment);var after=Read(args[1],out var newJobs,out var newEnvironment);
            var comparisons=before.Keys.Union(after.Keys).OrderBy(x=>x,StringComparer.Ordinal).Select(type=>{
                var old=before.GetValueOrDefault(type)??new();var current=after.GetValueOrDefault(type)??new();
                var members=old.Concat(current).SelectMany(r=>r.Keys).Distinct().OrderBy(x=>x,StringComparer.Ordinal);
                var changes=members.Where(m=>!old.Select(r=>r.GetValueOrDefault(m,"absent")).Order().SequenceEqual(current.Select(r=>r.GetValueOrDefault(m,"absent")).Order())).ToArray();
                return new {type,beforeRecords=old.Count,afterRecords=current.Count,
                    exactShallowRecordMultisetMatch=old.Select(Bundle).Order().SequenceEqual(current.Select(Bundle).Order()),changedMembers=changes};
            }).ToArray();
            Console.WriteLine(JsonSerializer.Serialize(new {success=true,
                evidenceKind="Exact scalar bindings and reference-type/shape summaries per record; not full semantic equivalence",
                comparedTypes=comparisons.Length,matchingTypes=comparisons.Count(c=>c.exactShallowRecordMultisetMatch),comparisons,
                jobEnvironmentListSizes=new {before=oldJobs.Select(EnvironmentCount),after=newJobs.Select(EnvironmentCount)},
                knownEnvironmentKinds=new {before=oldEnvironment,after=newEnvironment},
                runtime=new {os=RuntimeInformation.OSDescription,architecture=RuntimeInformation.ProcessArchitecture.ToString(),framework=RuntimeInformation.FrameworkDescription},
                decoderSha256=Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(typeof(NrbfDecoder).Assembly.Location))),
                loadedAssemblyNames=AppDomain.CurrentDomain.GetAssemblies().Select(a=>a.GetName().Name).Order().ToArray(),
                unsafeFormatterSwitchEnabled=AppContext.TryGetSwitch("System.Runtime.Serialization.EnableUnsafeBinaryFormatterSerialization",out bool enabled)&&enabled,
                limits=new[]{"Private values and ephemeral keyed fingerprints omitted","No array materialization, payload type loading or application instances",
                    "Reference types/shapes compared, not target identity or array contents; association/order/aliasing and custom blocks not proved",
                    "Exact scalar record multisets do not prove full engineering semantics or history replay"}}));
            return 0;
        }catch(Exception error){Console.WriteLine(JsonSerializer.Serialize(new {success=false,errorType=error.GetType().Name}));return 1;}
    }
}

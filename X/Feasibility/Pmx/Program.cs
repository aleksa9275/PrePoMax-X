using System.Formats.Nrbf;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text.Json;

// Record inspection never loads a type named by the payload.
internal static class Program
{
    static int Main(string[] args)
    {
        if(args.Length!=2 || args[0] is not ("--inventory" or "--static-graph" or "--command-history" or "--edit-strings" or "--static-edit-contract" or "--cad-static-graph" or "--cad-edit-contract"))
        { Console.WriteLine("{\"success\":false,\"error\":\"Expected a supported inspection command and a bounded NRBF file\"}"); return 2; }
        try
        {
            using var stream=File.OpenRead(args[1]);
            bool projection = args[0] != "--inventory";
            long limit = (projection ? 16L : 128L) * 1024 * 1024;
            if(stream.Length>limit || stream.Length<18) throw new InvalidDataException("NRBF byte limit or minimum length exceeded");
            if(!NrbfDecoder.StartsWithPayloadHeader(stream)) throw new InvalidDataException("NRBF header not recognized");
            var root=NrbfDecoder.Decode(stream,out var records,leaveOpen:true);
            if(stream.Position!=stream.Length) throw new InvalidDataException("Trailing bytes after NRBF MessageEnd");
            if(records.Count>(projection ? 100_000 : 1_000_000)) throw new InvalidDataException("Decoded record count exceeds inspection limit");
            if (projection)
            {
                object summary = args[0] switch
                {
                    "--static-graph" => StaticGraph.Read(root),
                    "--cad-static-graph" => new { definition = StaticGraph.Read(root), geometry = StaticGraph.ReadCadGeometry(root) },
                    "--cad-edit-contract" => StaticGraph.ValidateEditContract(root, records.Values, ReadGraphBytes(stream), true),
                    "--command-history" => StaticGraph.ReadCommandHistory(root),
                    "--static-edit-contract" => StaticGraph.ValidateEditContract(root, records.Values, ReadGraphBytes(stream)),
                    _ => StaticGraph.LocateEditStrings(root, records.Values, ReadGraphBytes(stream))
                };
                Console.WriteLine(JsonSerializer.Serialize(summary));
                return 0;
            }
            var groups=records.Values.GroupBy(record=>record.TypeName.AssemblyQualifiedName)
                .OrderBy(group=>group.Key,StringComparer.Ordinal).Select(group=>new {
                    type=group.Key,
                    records=group.Count(),
                    recordKinds=group.Select(record=>record.RecordType.ToString()).Distinct().OrderBy(x=>x,StringComparer.Ordinal).ToArray(),
                    members=group.OfType<ClassRecord>().SelectMany(record=>record.MemberNames).Distinct().OrderBy(x=>x,StringComparer.Ordinal).ToArray(),
                    arrayShapes=group.OfType<ArrayRecord>().Select(record=>string.Join("x",record.Lengths.ToArray())).Distinct().OrderBy(x=>x,StringComparer.Ordinal).ToArray()
                }).ToArray();
            // Report only reference edges for known application roots, never member values.
            string[] known={"PrePoMax.Controller","PrePoMax.Commands.CommandsCollection","CaeModel.FeModel","CaeResults.ResultsCollection"};
            var ordinals=records.Keys.Select((id,index)=>(id,index)).ToDictionary(pair=>pair.id,pair=>pair.index);
            var referenceEdges=new List<object>();
            foreach(var record in records.Values.OfType<ClassRecord>().Where(record=>known.Contains(record.TypeName.FullName)))
                foreach(string member in record.MemberNames)
                    if(record.GetRawValue(member) is SerializationRecord target)
                        referenceEdges.Add(new {source=record.TypeName.FullName,sourceOrdinal=ordinals[record.Id],member,
                            target=target.TypeName.FullName,targetOrdinal=ordinals[target.Id]});
            var decoder=typeof(NrbfDecoder).Assembly;
            Console.WriteLine(JsonSerializer.Serialize(new {
                success=true, rootType=root.TypeName.AssemblyQualifiedName, rootKind=root.RecordType.ToString(),
                decodedBytes=stream.Position, recordCount=records.Count, types=groups, referenceEdges,
                runtime=new {os=RuntimeInformation.IsOSPlatform(OSPlatform.OSX)?"macOS":RuntimeInformation.IsOSPlatform(OSPlatform.Linux)?"Linux":"Windows",
                    architecture=RuntimeInformation.ProcessArchitecture.ToString(),osArchitecture=RuntimeInformation.OSArchitecture.ToString(),framework=RuntimeInformation.FrameworkDescription},
                decoder=new {assembly=decoder.GetName().FullName,informationalVersion=decoder.GetCustomAttribute<AssemblyInformationalVersionAttribute>()?.InformationalVersion,
                    sha256=Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(decoder.Location)))},
                loadedAssemblyNames=AppDomain.CurrentDomain.GetAssemblies().Select(assembly=>assembly.GetName().Name).OrderBy(x=>x,StringComparer.Ordinal).ToArray(),
                unsafeFormatterSwitchEnabled=AppContext.TryGetSwitch("System.Runtime.Serialization.EnableUnsafeBinaryFormatterSerialization",out bool enabled) && enabled,
                limits=new[]{"No application instances, payload type loading or BinaryFormatter invocation","No array materialization or primitive/string values emitted","Input/record checks are not an OS memory quota"}
            }));
            return 0;
        }
        catch(Exception error)
        {
            if (Environment.GetEnvironmentVariable("PREPOMAXX_PMX_TRACE") == "1") Console.Error.WriteLine(error);
            Console.WriteLine(JsonSerializer.Serialize(new {success=false,errorType=error.GetType().Name,error=error.Message}));
            return 1;
        }
    }

    private static byte[] ReadGraphBytes(FileStream stream)
    {
        byte[] graph = new byte[checked((int)stream.Position)];
        stream.Position = 0;
        stream.ReadExactly(graph);
        return graph;
    }
}

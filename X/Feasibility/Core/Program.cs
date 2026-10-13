// PrePoMax-X feasibility tooling. Upstream engineering sources are linked unchanged.
using System.Runtime.InteropServices;
using System.Text.Json;
using QuantumConcepts.Formats.StereoLithography;

namespace PrePoMaxX.CoreProbe;

internal static class Program
{
    internal static readonly JsonSerializerOptions JsonOptions = new() { WriteIndented = true };

    internal static object RuntimeInfo() => new
    {
        os = RuntimeInformation.IsOSPlatform(OSPlatform.OSX) ? "macOS" :
             RuntimeInformation.IsOSPlatform(OSPlatform.Linux) ? "Linux" :
             RuntimeInformation.IsOSPlatform(OSPlatform.Windows) ? "Windows" : "Other",
        architecture = RuntimeInformation.ProcessArchitecture.ToString(),
        osArchitecture = RuntimeInformation.OSArchitecture.ToString(),
        framework = RuntimeInformation.FrameworkDescription,
    };

    private static int Main(string[] args)
    {
        try
        {
            if (args.Length == 1 && args[0] == "--self-test")
            {
                var results = ProbeChecks.Run(Path.Combine(AppContext.BaseDirectory, "Fixtures", "cube.stl"));
                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    schemaVersion = 1, runtime = RuntimeInfo(), results.passed, results.failed,
                    checks = results.checks, observations = results.observations,
                }, JsonOptions));
                return results.failed == 0 ? 0 : 1;
            }
            if (args.Length == 2 && args[0] == "inspect")
            {
                using var stream = File.OpenRead(args[1]);
                var summary = StlInspector.Summarize(StlInspector.Read(stream));
                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    schemaVersion = 1, success = true, runtime = RuntimeInfo(), geometry = summary,
                }, JsonOptions));
                return 0;
            }
            Console.WriteLine(JsonSerializer.Serialize(new
            {
                success = false, error = "Usage: CoreProbe inspect <file.stl> | --self-test",
            }, JsonOptions));
            return 2;
        }
        catch (Exception exception)
        {
            Console.WriteLine(JsonSerializer.Serialize(new
            {
                success = false, error = exception.Message, errorType = exception.GetType().Name,
            }, JsonOptions));
            return 1;
        }
    }
}

internal static class StlInspector
{
    // Validation belongs to this exploratory CLI, not to the untouched upstream parser.
    internal static STLDocument Read(Stream stream)
    {
        if (!stream.CanSeek) throw new ArgumentException("The probe requires a seekable STL stream.");
        bool textHeader = STLDocument.IsText(stream);
        bool binaryFramingMatches = false;
        if (stream.Length >= 84)
        {
            stream.Position = 80;
            using var reader = new BinaryReader(stream, System.Text.Encoding.ASCII, leaveOpen: true);
            uint declared = reader.ReadUInt32();
            binaryFramingMatches = (ulong)stream.Length == 84UL + 50UL * declared;
        }
        if (!textHeader && !binaryFramingMatches)
            throw new InvalidDataException("Binary STL length does not match its declared triangle count.");
        stream.Position = 0;
        STLDocument document;
        try
        {
            // The upstream API explicitly offers fallback for binary headers beginning with 'solid'.
            document = STLDocument.Read(stream, tryBinaryIfTextFailed: true);
        }
        catch (Exception exception) when (exception is FormatException or EndOfStreamException or
                                          NullReferenceException or ArgumentException)
        {
            throw new InvalidDataException("The upstream STL reader could not read this input.", exception);
        }
        if (document.Name == null && !binaryFramingMatches)
            throw new InvalidDataException("Binary STL length does not match its declared triangle count.");
        Validate(document);
        return document;
    }

    internal static void Validate(STLDocument document)
    {
        if (document?.Facets == null || document.Facets.Count == 0)
            throw new InvalidDataException("No triangles were read from the STL input.");
        foreach (var facet in document.Facets)
        {
            if (facet?.Normal == null || facet.Vertices == null || facet.Vertices.Count != 3)
                throw new InvalidDataException("Incomplete STL triangle.");
            foreach (var vertex in facet.Vertices.Append(facet.Normal))
                if (vertex == null || !float.IsFinite(vertex.X) || !float.IsFinite(vertex.Y) || !float.IsFinite(vertex.Z))
                    throw new InvalidDataException("Missing or non-finite STL coordinate/normal.");
        }
    }

    internal static object Summarize(STLDocument document)
    {
        Validate(document);
        var vertices = document.Facets.SelectMany(facet => facet.Vertices).ToArray();
        return new
        {
            triangleCount = document.Facets.Count,
            bounds = new
            {
                min = new[] { vertices.Min(v => v.X), vertices.Min(v => v.Y), vertices.Min(v => v.Z) },
                max = new[] { vertices.Max(v => v.X), vertices.Max(v => v.Y), vertices.Max(v => v.Z) },
            },
        };
    }
}

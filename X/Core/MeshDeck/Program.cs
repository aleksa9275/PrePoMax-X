using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;
using CaeModel;
using CaeMesh;
using FileInOut.Input;
using PrePoMaxX.MeasureMesh;

namespace PrePoMaxX.MeshDeck;

public static class MeshFiles
{
    public static InpMeshData Read(string path)
    {
        using var stream = File.OpenRead(path);
        if (stream.Length > InpFileReader.MeshDataMaximumCharacters)
            throw new InvalidDataException("Standalone mesh input exceeds 16 MiB.");
        using var reader = new StreamReader(stream, Encoding.UTF8, true);
        var lines = new List<string>();
        while (reader.ReadLine() is { } line)
        {
            if (line.Length > 0 && char.IsWhiteSpace(line[0]) && line.TrimStart().StartsWith('*'))
                throw new InvalidDataException("Mesh keywords must start in the first column, as required by the original parser.");
            lines.Add(line);
            if (lines.Count > InpFileReader.MeshDataMaximumItems * 4)
                throw new InvalidDataException("Standalone mesh input exceeds the line limit.");
        }
        return InpFileReader.ReadMeshData(lines.ToArray());
    }

    public static ElementOutput[] Measure(InpMeshData mesh) => Measurement.Run(new(
        mesh.Nodes.Values.Select(node => new NodeInput(node.Id, node.X, node.Y, node.Z)).ToArray(),
        mesh.Elements.Values.Select(element => new ElementInput(element.Id, element.GetType().Name,
            element.NodeIds, element.PartId)).ToArray()));

    public static void ExportNewFile(InpMeshData mesh, string path, ConvertPyramidsToEnum? conversion)
    {
        string text = MeshDeckWriter.WriteMesh(mesh, conversion);
        // CreateNew refuses an existing output, the input itself, symlinks or hardlink aliases to it.
        using var stream = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None);
        using var writer = new StreamWriter(stream, new UTF8Encoding(false));
        writer.Write(text);
    }

    public static object Describe(InpMeshData mesh) => new
    {
        nodes = mesh.Nodes.Count, elements = mesh.Elements.Count,
        bounds = new[] { new[] { mesh.Nodes.Values.Min(n => n.X), mesh.Nodes.Values.Min(n => n.Y), mesh.Nodes.Values.Min(n => n.Z) },
                         new[] { mesh.Nodes.Values.Max(n => n.X), mesh.Nodes.Values.Max(n => n.Y), mesh.Nodes.Values.Max(n => n.Z) } },
        elementBlocks = mesh.ElementBlocks.Select(block => new { name = block.Name,
            formulations = block.InpElementTypeNames.Order().ToArray(), elementIds = block.ElementLabels.Order().ToArray() }),
        nodeSets = mesh.NodeSets, elementSets = mesh.ElementSets,
        warnings = mesh.Warnings, omittedKeywords = mesh.OmittedKeywords,
        sourceOfEngineeringTypes = new[] { typeof(FeNode).Assembly.GetName().Name, typeof(InpMeshData).Assembly.GetName().Name },
        quadraticTetrahedronMeasurementGated = mesh.Elements.Values.Any(element => element is ParabolicTetraElement)
    };
}

internal static class Program
{
    private static int Main(string[] args)
    {
        bool inspect = args.Length == 2 && args[0] == "inspect";
        bool measure = args.Length == 2 && args[0] == "measure";
        bool export = (args.Length == 3 || (args.Length == 5 && args[3] == "--pyramids" &&
                       args[4] is "wedges" or "hexahedrons")) && args[0] == "export-mesh";
        if (!inspect && !measure && !export)
        {
            Console.Error.WriteLine("Usage: PrePoMaxX.MeshDeck inspect|measure <input.inp>\n" +
                "       PrePoMaxX.MeshDeck export-mesh <input.inp> <new-output.inp> [--pyramids wedges|hexahedrons]");
            return 2;
        }
        try
        {
            var mesh = MeshFiles.Read(args[1]);
            ConvertPyramidsToEnum? conversion = args.Length == 5
                ? args[4] == "wedges" ? ConvertPyramidsToEnum.Wedges : ConvertPyramidsToEnum.Hexahedrons : null;
            if (export) MeshFiles.ExportNewFile(mesh, args[2], conversion);
            Console.WriteLine(JsonSerializer.Serialize(new { success = true,
                operation = args[0], meshOnly = true, mesh = MeshFiles.Describe(mesh),
                measurements = measure ? MeshFiles.Measure(mesh) : null,
                outputWritten = export, pyramidConversion = conversion?.ToString(),
                runtime = new { os = RuntimeInformation.OSDescription, architecture = RuntimeInformation.ProcessArchitecture.ToString() } }));
            return 0;
        }
        catch (Exception error) when (error is IOException or InvalidDataException or UnauthorizedAccessException or ArgumentException or
            CaeGlobals.CaeException or FormatException or OverflowException or IndexOutOfRangeException or
            NotSupportedException or NotImplementedException)
        {
            Console.Error.WriteLine(JsonSerializer.Serialize(new { success = false, error = error.Message }));
            return 1;
        }
    }
}

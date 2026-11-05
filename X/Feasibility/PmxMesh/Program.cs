using CaeMesh;
using System.Text.Json;

try
{
    if (args.Length == 2 && args[0] == "--model-kind")
    {
        using var input = File.OpenRead(args[1]);
        using var binary = new BinaryReader(input);
        if (input.Length > 128L*1024*1024) throw new InvalidDataException("Model frame too large.");
        int marker = binary.ReadInt32();
        if (marker is not (0 or 1)) throw new InvalidDataException("Invalid geometry marker.");
        int geometryNodeCount = marker == 1 ? binary.ReadInt32() : 0;
        if (geometryNodeCount < 0 || geometryNodeCount > 250000) throw new InvalidDataException("Invalid geometry count.");
        Console.WriteLine(JsonSerializer.Serialize(new { cadModel = geometryNodeCount > 0 }));
        return 0;
    }
    if (args.Length == 2 && args[0] == "--cad-model")
    {
        Console.WriteLine(JsonSerializer.Serialize(CadModel.Read(args[1])));
        return 0;
    }
    if (args.Length >= 4 && args[0] == "--compare-results")
    {
        Console.WriteLine(JsonSerializer.Serialize(ResultFields.Compare(args[1], args[2], args[3..])));
        return 0;
    }

    if (args.Length != 1)
        throw new ArgumentException("Expected a PMX 3.0.0 custom model block.");

    using var stream = File.OpenRead(args[0]);
    if (stream.Length > 128L * 1024 * 1024)
        throw new InvalidDataException("Model block exceeds the probe limit.");
    using var reader = new BinaryReader(stream);

    // FeModel's geometry marker, followed by an empty FeMesh if present.
    int geometry = reader.ReadInt32();
    if (geometry != 0 &&
        (geometry != 1 || reader.ReadInt32() != 0 || reader.ReadInt32() != 0 ||
         reader.ReadInt32() != 0))
        throw new InvalidDataException("Only absent or empty geometry is supported.");

    if (reader.ReadInt32() != 1)
        throw new InvalidDataException("Expected an analysis mesh.");

    var (nodes, elements) = MeshPrefix.Read(reader);

    // Check the part names and skip the visualization arrays by length.
    long remaining = stream.Length - stream.Position;
    string[] partNames = PmxBinary.ReadPartNames(reader);
    PmxBinary.End(reader);

    Console.WriteLine(JsonSerializer.Serialize(new
    {
        nodes = nodes.Values.OrderBy(node => node.Id).Select(node => new
            { id = node.Id, coordinates = new[] { node.X, node.Y, node.Z } }),
        elements = elements.Values.OrderBy(element => element.Id).Select(element => new
            { id = element.Id, partId = element.PartId, type = "C3D8", connectivity = element.NodeIds }),
        meshAssembly = typeof(FeNode).Assembly.GetName().Name,
        partNames,
        partBlockBytes = remaining
    }));
    return 0;
}
catch (Exception error) when (error is IOException or InvalidDataException or ArgumentException or NotSupportedException)
{
    Console.Error.WriteLine(error.Message);
    return 1;
}

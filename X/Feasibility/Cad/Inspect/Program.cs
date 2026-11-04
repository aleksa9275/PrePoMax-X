using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using CaeMesh;
using FileInOut.Input;

if (args.Length != 1)
{
    Console.Error.WriteLine("Usage: PrePoMaxX.InspectVis <geometry.vis>");
    return 2;
}

try
{
    using var input = File.OpenRead(args[0]);
    if (input.Length > 1024 * 1024)
        throw new InvalidDataException("VIS research input exceeds 1 MiB.");
    var bytes = new byte[(int)input.Length];
    input.ReadExactly(bytes);
    using var text = new StreamReader(new MemoryStream(bytes), new UTF8Encoding(false, true));
    var data = VisFileReader.ReadGeometryData(text.ReadToEnd());
    if (data == null || data.Nodes.Count == 0 || !data.Elements.Values.Any(e => e is LinearTriangleElement))
        throw new InvalidDataException("Expected VIS version 2 with geometry metadata and visualization triangles.");
    if (data.Elements.Values.Any(e => e.NodeIds.Any(id => !data.Nodes.ContainsKey(id))))
        throw new InvalidDataException("VIS element refers to an absent node.");

    var metadata = data.Metadata;
    Console.WriteLine(JsonSerializer.Serialize(new
    {
        success = true,
        sourceSha256 = Convert.ToHexStringLower(SHA256.HashData(bytes)),
        metadata = new
        {
            formatVersion = metadata.FormatVersion,
            coordinateSystem = metadata.CoordinateSystem,
            lengthUnit = metadata.LengthUnit,
            entities = metadata.EntityKinds.ToDictionary(kind => kind, kind => metadata.GetEntities(kind)
                .Select(entity => new
                {
                    id = entity.Id,
                    properties = entity.Properties.OrderBy(entry => entry.Key, StringComparer.Ordinal)
                        .ToDictionary(entry => entry.Key, entry => entry.Value.IsNumeric
                            ? (object)entry.Value.NumericValues : entry.Value.TextValues),
                })),
        },
        nodes = data.Nodes.Values.OrderBy(node => node.Id)
            .Select(node => new { id = node.Id, coordinates = new[] { node.X, node.Y, node.Z } }),
        triangles = data.Elements.Values.OfType<LinearTriangleElement>().OrderBy(element => element.Id)
            .Select(element => new
            {
                id = element.Id, nodeIds = element.NodeIds,
                sourceFaceId = data.ElementIdSurfaceId[element.Id],
            }),
        vertexNodeIds = data.VertexNodeIds.OrderBy(id => id),
        faces = data.FaceTypes.OrderBy(entry => entry.Key).Select(entry => new
        {
            id = entry.Key, type = entry.Value.ToString(), nodeIds = data.SurfaceIdNodeIds[entry.Key].OrderBy(id => id),
        }),
        edges = data.EdgeTypes.OrderBy(entry => entry.Key).Select(entry => new
        {
            id = entry.Key, type = entry.Value.ToString(), nodeIds = data.EdgeIdNodeIds[entry.Key].OrderBy(id => id),
        }),
    }));
    return 0;
}
catch (Exception error) when (error is IOException or InvalidDataException or ArgumentException or
    FormatException or OverflowException or IndexOutOfRangeException or KeyNotFoundException or NotSupportedException)
{
    Console.Error.WriteLine(JsonSerializer.Serialize(new { success = false, error = error.Message }));
    return 1;
}

using System.Security.Cryptography;
using System.Text.Json;
using PrePoMaxX.MeshDeck;

if (args.Length != 1)
{
    Console.Error.WriteLine("Usage: PrePoMaxX.MeshScene <mesh.inp>");
    return 2;
}
try
{
    var mesh = MeshFiles.Read(args[0]);
    Console.WriteLine(JsonSerializer.Serialize(new {
        success = true, schemaVersion = 1, meshOnly = true,
        SourceSha256 = Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(args[0]))),
        engineeringOwner = "Original CaeModel/CaeMesh INP mesh reader; renderer DTO only",
        nodes = mesh.Nodes.Values.Select(n => new { id = n.Id, x = n.X, y = n.Y, z = n.Z }),
        elements = mesh.Elements.Values.Select(e => new { id = e.Id, vtkCellType = e.GetVtkCellType(), nodeIds = e.NodeIds }),
        warnings = mesh.Warnings, omittedKeywords = mesh.OmittedKeywords,
        solverExecuted = false
    }));
    return 0;
}
catch (Exception e) when (e is IOException or ArgumentException or CaeGlobals.CaeException or
    FormatException or OverflowException or NotSupportedException or IndexOutOfRangeException)
{
    Console.Error.WriteLine(JsonSerializer.Serialize(new { success = false, error = e.Message }));
    return 1;
}

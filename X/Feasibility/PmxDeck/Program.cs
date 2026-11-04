using System.Globalization;
using System.Text.Json;
using CaeGlobals;
using PrePoMaxX.MeshDeck;
using PrePoMaxX.StaticDeck;
using PrePoMaxX.Solve;

CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
CultureInfo.CurrentUICulture = CultureInfo.InvariantCulture;
try
{
    if (args.Length != 3)
        throw new ArgumentException("Expected mesh input, controlled PMX definition and new deck path.");
    var mesh = MeshFiles.Read(args[0]);
    var (deck, massDensity, material, step) = PmxStaticDeck.Build(mesh, args[1]);
    AnalysisFiles.WriteNew(args[2], deck);
    Console.WriteLine(JsonSerializer.Serialize(new { nodes = mesh.Nodes.Count, elements = mesh.Elements.Count,
        massDensity, material, step, solverExecuted = false }));
    return 0;
}
catch (Exception error) when (error is IOException or InvalidDataException or ArgumentException or
    NotSupportedException or FormatException or JsonException or CaeException)
{
    Console.Error.WriteLine(error.Message);
    return 1;
}

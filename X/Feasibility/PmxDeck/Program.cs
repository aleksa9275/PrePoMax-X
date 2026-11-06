using System.Globalization;
using System.Text.Json;
using CaeGlobals;
using CaeModel;
using PrePoMaxX.MeshDeck;
using PrePoMaxX.StaticDeck;
using PrePoMaxX.Solve;

CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
CultureInfo.CurrentUICulture = CultureInfo.InvariantCulture;
try
{
    if (args.Length == 4 && args[0] == "--force-vector")
    {
        StringForceConverter.SetUnit = "N";
        var load = new CLoad("Force", "Nodes", RegionTypeEnum.NodeSetName, 0, 0, 0, false, false, 0);
        load.F1.SetEquation(args[1], true);
        load.F2.SetEquation(args[2], true);
        load.F3.SetEquation(args[3], true);
        if (new[] { load.F1.Value, load.F2.Value, load.F3.Value, load.Magnitude.Value }.Any(v => !double.IsFinite(v)))
            throw new InvalidDataException("Expected finite force components and magnitude.");
        Console.WriteLine(JsonSerializer.Serialize(new { magnitude = load.Magnitude.Equation.Equation }));
        return 0;
    }
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

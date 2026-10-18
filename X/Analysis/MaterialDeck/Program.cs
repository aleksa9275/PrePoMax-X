using System.Globalization;
using System.Text;
using System.Text.Json;
using CaeGlobals;
using CaeModel;

CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
CultureInfo.CurrentUICulture = CultureInfo.InvariantCulture;
if (args.Length != 7 || args[0] != "write-isotropic" || args[5] != "--pressure-unit" ||
    args[6] is not ("Pa" or "MPa" or "GPa"))
{
    Console.Error.WriteLine("Usage: PrePoMaxX.MaterialDeck write-isotropic <name> <E or equation> <Poisson ratio or equation> <new-output.inp> --pressure-unit Pa|MPa|GPa");
    return 2;
}
try
{
    if (args[1].Length > 80 || args[2].Length > 4096 || args[3].Length > 4096)
        throw new ArgumentException("Material name or equation exceeds the tool input limit.");
    StringPressureConverter.SetUnit = args[6];
    var elastic = new Elastic(new[] { new[] { 1d, 0.3, 0d } });
    elastic.YoungsPoissonsTemp[0][0].SetEquation(args[2]);
    elastic.YoungsPoissonsTemp[0][1].SetEquation(args[3]);
    var material = new Material(args[1]);
    material.AddProperty(elastic);
    string fragment = MaterialDeckWriter.WriteIsotropic(material);
    using (var stream = new FileStream(args[4], FileMode.CreateNew, FileAccess.Write, FileShare.None))
    using (var writer = new StreamWriter(stream, new UTF8Encoding(false))) writer.Write(fragment);
    Console.WriteLine(JsonSerializer.Serialize(new { success = true, materialOnly = true,
        pressureUnit = args[6], youngsModulus = elastic.YoungsPoissonsTemp[0][0].Value,
        poissonsRatio = elastic.YoungsPoissonsTemp[0][1].Value, outputWritten = true }));
    return 0;
}
catch (Exception error) when (error is IOException or UnauthorizedAccessException or ArgumentException or
    CaeException or FormatException or OverflowException or NotSupportedException)
{
    Console.Error.WriteLine(JsonSerializer.Serialize(new { success = false, error = error.Message }));
    return 1;
}

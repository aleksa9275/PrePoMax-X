using System.Text.Json;
using System.Text.Json.Serialization;
using CaeMesh;

namespace PrePoMaxX.MeasureMesh;

// Tool input only; these records do not replace persistent engineering types or PMX.
public sealed record NodeInput(int Id, double X, double Y, double Z, double Value = 1);
public sealed record ElementInput(int Id, string Type, int[] NodeIds, int PartId = -1);
public sealed record MeshInput(NodeInput[] Nodes, ElementInput[] Elements, string Scale = "none", double Thickness = 1);
public sealed record ElementOutput(int Id, int PartId, string Type, int Dimension, double Measure,
    double[] Centroid, double Integral, int VtkCellType, int[] VtkNodeIds, int[] GmshNodeIds);

public static class Measurement
{
    private static readonly Dictionary<string, (int Count, Func<int, int, int[], FeElement> Create)> Factories = new()
    {
        [nameof(LinearBeamElement)] = (2, (id, part, nodes) => new LinearBeamElement(id, part, nodes)),
        [nameof(ParabolicBeamElement)] = (3, (id, part, nodes) => new ParabolicBeamElement(id, part, nodes)),
        [nameof(LinearTriangleElement)] = (3, (id, part, nodes) => new LinearTriangleElement(id, part, nodes)),
        [nameof(ParabolicTriangleElement)] = (6, (id, part, nodes) => new ParabolicTriangleElement(id, part, nodes)),
        [nameof(LinearQuadrilateralElement)] = (4, (id, part, nodes) => new LinearQuadrilateralElement(id, part, nodes)),
        [nameof(ParabolicQuadrilateralElement)] = (8, (id, part, nodes) => new ParabolicQuadrilateralElement(id, part, nodes)),
        [nameof(LinearTetraElement)] = (4, (id, part, nodes) => new LinearTetraElement(id, part, nodes)),
        [nameof(LinearPyramidElement)] = (5, (id, part, nodes) => new LinearPyramidElement(id, part, nodes)),
        [nameof(ParabolicPyramidElement)] = (13, (id, part, nodes) => new ParabolicPyramidElement(id, part, nodes)),
        [nameof(LinearWedgeElement)] = (6, (id, part, nodes) => new LinearWedgeElement(id, part, nodes)),
        [nameof(ParabolicWedgeElement)] = (15, (id, part, nodes) => new ParabolicWedgeElement(id, part, nodes)),
        [nameof(LinearHexaElement)] = (8, (id, part, nodes) => new LinearHexaElement(id, part, nodes)),
        [nameof(ParabolicHexaElement)] = (20, (id, part, nodes) => new ParabolicHexaElement(id, part, nodes))
    };

    public static ElementOutput[] Run(MeshInput input)
    {
        if (input?.Nodes == null || input.Elements == null || input.Nodes.Length is < 1 or > 10000 ||
            input.Elements.Length is < 1 or > 10000)
            throw new ArgumentException("Provide 1–10000 nodes and 1–10000 elements.");
        IntegrationScale scale = input.Scale switch
        {
            "none" => IntegrationScale.None,
            "thickness" when double.IsFinite(input.Thickness) && input.Thickness > 0 => IntegrationScale.FromThickness(input.Thickness),
            "axisymmetric" => IntegrationScale.FromAxisymmetric(),
            _ => throw new ArgumentException("Scale must be none, thickness (positive), or axisymmetric.")
        };
        var nodes = new Dictionary<int, FeNode>();
        var values = new Dictionary<int, double>();
        foreach (var node in input.Nodes)
        {
            if (node == null || node.Id <= 0 || !double.IsFinite(node.X) || !double.IsFinite(node.Y) ||
                !double.IsFinite(node.Z) || !double.IsFinite(node.Value) ||
                (input.Scale == "axisymmetric" && node.X < 0) || nodes.ContainsKey(node.Id))
                throw new ArgumentException("Node IDs must be unique and positive; coordinates/values finite; axisymmetric radii nonnegative.");
            nodes.Add(node.Id, new FeNode(node.Id, node.X, node.Y, node.Z));
            values.Add(node.Id, node.Value);
        }
        var ids = new HashSet<int>();
        var output = new List<ElementOutput>();
        foreach (var item in input.Elements)
        {
            if (item?.Type == nameof(ParabolicTetraElement))
                throw new NotSupportedException("Quadratic tetrahedron measurement/integration is gated by an unresolved analytical discrepancy in the original kernel.");
            if (item == null || item.Type == null || !Factories.TryGetValue(item.Type, out var factory))
                throw new ArgumentException("Unsupported element type; use an exact supported engineering class name.");
            if (item.Id <= 0 || !ids.Add(item.Id) || item.NodeIds == null || item.NodeIds.Length != factory.Count ||
                item.NodeIds.Distinct().Count() != factory.Count || item.NodeIds.Any(id => !nodes.ContainsKey(id)))
                throw new ArgumentException("Element IDs must be unique and positive, with complete distinct connectivity to existing nodes.");
            FeElement element = factory.Create(item.Id, item.PartId, item.NodeIds.ToArray());
            double[] cg = element.GetCG(nodes, out double measure);
            double integral = element.Integrate(nodes, values, scale);
            if (!double.IsFinite(measure) || measure == 0 || cg == null || cg.Any(x => !double.IsFinite(x)) || !double.IsFinite(integral))
                throw new ArgumentException("The element produced a zero or nonfinite geometric result.");
            // Signed volume and dimension-dependent measures are retained; no incompatible totals are added.
            output.Add(new(item.Id, item.PartId, item.Type, element.Dimension, measure, cg, integral,
                element.GetVtkCellType(), element.GetVtkNodeIds(), element.GetGmshNodeIds()));
        }
        return output.ToArray();
    }
}

internal static class Program
{
    private static int Main(string[] args)
    {
        if (args.Length != 1) { Console.Error.WriteLine("Usage: PrePoMaxX.MeasureMesh <mesh.json>"); return 2; }
        try
        {
            using var stream = File.OpenRead(args[0]);
            if (stream.Length > 4 * 1024 * 1024) throw new InvalidDataException("Input exceeds 4 MiB.");
            var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true, UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow };
            var input = JsonSerializer.Deserialize<MeshInput>(stream, options);
            var output = Measurement.Run(input);
            Console.WriteLine(JsonSerializer.Serialize(new { success = true, elements = output }));
            return 0;
        }
        catch (Exception error) when (error is IOException or InvalidDataException or UnauthorizedAccessException or ArgumentException or JsonException or NotSupportedException or NotImplementedException)
        {
            Console.Error.WriteLine(JsonSerializer.Serialize(new { success = false, error = error.Message }));
            return 1;
        }
    }
}

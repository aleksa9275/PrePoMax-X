using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using CaeMesh;
using CaeModel;
using FileInOut.Input;

internal static class NativeMeshCommands
{
    private static string Hash(byte[] bytes) => Convert.ToHexStringLower(SHA256.HashData(bytes));
    private static void WriteNew(string path, byte[] bytes)
    {
        using var output = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None);
        output.Write(bytes);
    }

    internal static int Run(string[] args)
    {
        try
        {
            CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
            bool quadratic = args[0] is "netgen-quadratic-parameters" or "from-vol-quadratic-preview" or "from-vol-quadratic";
            if (args[0] is "netgen-parameters" or "netgen-quadratic-parameters")
            {
                if (args.Length != 3 || !double.TryParse(args[1], NumberStyles.Float, CultureInfo.InvariantCulture, out double size) ||
                    !double.IsFinite(size) || size <= 0)
                    throw new ArgumentException("netgen-parameters <positive maximum size> <new file>");
                string temporary = Path.Combine(Path.GetTempPath(), "prepomaxx-netgen-" + Guid.NewGuid().ToString("N"));
                Directory.CreateDirectory(temporary);
                byte[] bytes;
                try
                {
                    var parameters = new MeshingParameters(quadratic ? "Native-quadratic-solid" : "Native-linear-solid") {
                        MaxH = size, MinH = 0, SecondOrder = quadratic, MidsideNodesOnGeometry = quadratic,
                        QuadDominated = false, RelativeSize = false
                    };
                    string file = Path.Combine(temporary, "parameters");
                    parameters.WriteToFile(file, 0, 1);
                    bytes = File.ReadAllBytes(file);
                }
                finally { Directory.Delete(temporary, true); }
                WriteNew(args[2], bytes);
                Console.WriteLine(JsonSerializer.Serialize(new { success = true, sha256 = Hash(bytes), maximumSize = size,
                    elementOrder = quadratic ? 2 : 1, analysisEligible = true, parallelMeshingThreads = 1, owner = "Original CaeMesh.MeshingParameters.WriteToFile" }));
                return 0;
            }
            if (args.Length < 3 || args.Length > 34)
                throw new ArgumentException("from-vol <new mesh.inp> <part1.vol> [part2.vol ...] (at most 32 parts)");
            var mesh = (Nodes: new Dictionary<int, FeNode>(), Elements: new Dictionary<int, FeElement>(),
                ElementBlocks: new List<InpElementSet>(), NodeSets: new Dictionary<string, int[]>(),
                ElementSets: new Dictionary<string, int[]>());
            var parts = new List<object>();
            int nodeOffset = 0, elementOffset = 0, nextDomain = 1;
            for (int index = 2; index < args.Length; index++)
            {
                int partId = index - 1;
                var info = new FileInfo(args[index]);
                if (info.Length <= 0 || info.Length > 16 * 1024 * 1024)
                    throw new InvalidDataException("VOL part exceeds its 16 MiB limit.");
                byte[] bytes = File.ReadAllBytes(args[index]);
                string text = new UTF8Encoding(false, true).GetString(bytes);
                var original = quadratic ? NetgenVolFileReader.ReadQuadraticSolidData(text) : NetgenVolFileReader.ReadLinearSolidData(text);
                if (mesh.Nodes.Count + original.Nodes.Count > 100000 || mesh.Elements.Count + original.Elements.Count > 100000)
                    throw new InvalidDataException("Combined solid mesh exceeds 100000 nodes/elements.");
                var domains = original.Elements.Values.Select(e => e.PartId).Distinct().Order()
                    .ToDictionary(id => id, _ => nextDomain++);
                foreach (var node in original.Nodes.Values)
                    mesh.Nodes.Add(node.Id + nodeOffset, new FeNode(node.Id + nodeOffset, node.X, node.Y, node.Z));
                foreach (var element in original.Elements.Values)
                    mesh.Elements.Add(element.Id + elementOffset,
                        (quadratic ? (FeElement)new ParabolicTetraElement(element.Id + elementOffset, domains[element.PartId],
                            element.NodeIds.Select(id => id + nodeOffset).ToArray()) : new LinearTetraElement(element.Id + elementOffset, domains[element.PartId],
                            element.NodeIds.Select(id => id + nodeOffset).ToArray())));
                foreach (var domain in domains)
                {
                    int[] ids = original.Elements.Values.Where(e => e.PartId == domain.Key).Select(e => e.Id + elementOffset).ToArray();
                    string name = $"PART_{partId}_SOLID_{domain.Key}";
                    mesh.ElementBlocks.Add(new InpElementSet(name, new() { quadratic ? "C3D10" : "C3D4" }, new(ids)));
                    mesh.ElementSets.Add(name, ids);
                }
                foreach (var face in original.FaceNodeIds)
                    mesh.NodeSets.Add($"PART_{partId}_FACE_{face.Key}", face.Value.Select(id => id + nodeOffset).Order().ToArray());
                foreach (var edge in original.EdgeNodeIds)
                    mesh.NodeSets.Add($"PART_{partId}_EDGE_{edge.Key}", edge.Value.Select(id => id + nodeOffset).Order().ToArray());
                mesh.NodeSets.Add($"PART_{partId}_NODES", original.Nodes.Keys.Select(id => id + nodeOffset).Order().ToArray());
                parts.Add(new { id = partId, volSha256 = Hash(bytes), nodeOffset, elementOffset,
                    domains, faceIds = original.FaceNodeIds.Keys.Order().ToArray(), edgeIds = original.EdgeNodeIds.Keys.Order().ToArray() });
                nodeOffset = mesh.Nodes.Keys.Max();
                elementOffset = mesh.Elements.Keys.Max();
            }
            mesh.NodeSets.Add("ALL_NODES", mesh.Nodes.Keys.Order().ToArray());
            var transport = quadratic ? NetgenVolFileReader.CreateQuadraticSolidMesh(mesh.Nodes, mesh.Elements, mesh.ElementBlocks, mesh.NodeSets, mesh.ElementSets) :
                NetgenVolFileReader.CreateLinearSolidMesh(mesh.Nodes, mesh.Elements, mesh.ElementBlocks, mesh.NodeSets, mesh.ElementSets);
            byte[] exported = Encoding.UTF8.GetBytes(MeshDeckWriter.WriteMesh(transport));
            if (exported.Length > InpFileReader.MeshDataMaximumCharacters)
                throw new InvalidDataException("Exported mesh exceeds its 16 MiB limit.");
            var checkedMesh = InpFileReader.ReadMeshData(Encoding.UTF8.GetString(exported).Split('\n'));
            if (checkedMesh.Nodes.Count != mesh.Nodes.Count || checkedMesh.Elements.Count != mesh.Elements.Count ||
                checkedMesh.Warnings.Length != 0 || checkedMesh.OmittedKeywords.Length != 0 ||
                mesh.Elements.Any(e => !checkedMesh.Elements.TryGetValue(e.Key, out var other) ||
                    other.GetVtkCellType()!=e.Value.GetVtkCellType() || !other.NodeIds.SequenceEqual(e.Value.NodeIds)))
                throw new InvalidDataException("Original INP reader did not retain the generated solid mesh.");
            WriteNew(args[1], exported);
            Console.WriteLine(JsonSerializer.Serialize(new { success = true, SourceSha256 = Hash(exported), meshOnly = true,
                nodes = mesh.Nodes.Values.Select(n => new { id = n.Id, x = n.X, y = n.Y, z = n.Z }),
                elements = mesh.Elements.Values.Select(e => new { id = e.Id, vtkCellType = e.GetVtkCellType(), nodeIds = e.NodeIds, vtkNodeIds = e.GetVtkNodeIds() }),
                elementBlocks = mesh.ElementBlocks.Select((b,i) => new { index=i, name=b.Name, formulation=b.InpElementTypeNames.Single(),
                    count=b.ElementLabels.Count, compatibleFormulations=StaticAnalysisDeckWriter.CompatibleSolidFormulations(b.InpElementTypeNames.Single()) }),
                nodeSets = mesh.NodeSets.Select(e => new { name = e.Key, count = e.Value.Length }),
                elementSets = mesh.ElementSets.Select(e => new { name = e.Key, count = e.Value.Length }),
                cadMesh = new { schemaVersion = 1, elementType = quadratic ? "C3D10" : "C3D4", elementOrder = quadratic ? 2 : 1, analysisEligible = true,
                    geometryValidation = quadratic ? "Complete midside topology and positive corner orientation; native solver checks curved integration-point Jacobians; general quality unverified" : "Positive original signed volumes", parts, engineeringOwner = "Original VOL parser, element permutation and CalElement writer" }
            }));
            return 0;
        }
        catch (Exception e) when (e is IOException or ArgumentException or InvalidDataException or NotSupportedException or
            FormatException or OverflowException or IndexOutOfRangeException or KeyNotFoundException or CaeGlobals.CaeException)
        {
            Console.Error.WriteLine(JsonSerializer.Serialize(new { success = false, error = e.Message }));
            return 1;
        }
    }
}

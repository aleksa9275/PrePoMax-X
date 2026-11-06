using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using CaeModel;
using FileInOut.Input;
using PrePoMaxX.MeshDeck;

if (args.Length > 0 && args[0] is "netgen-parameters" or "from-vol" or "netgen-quadratic-parameters" or "from-vol-quadratic-preview" or "from-vol-quadratic")
    return NativeMeshCommands.Run(args);

bool addSet = args.Length == 6 && args[0] is "add-set" or "add-region-set";
bool setFormulations = args.Length == 4 && args[0] == "set-solid-formulations";
if (args.Length != 1 && !addSet && !setFormulations)
{
    Console.Error.WriteLine("Usage: PrePoMaxX.MeshScene <mesh.inp> | add-set <mesh.inp> <new.inp> <node|element> <name> <ids> | add-region-set <mesh.inp> <new.inp> <node|element> <name> <source-set-names> | set-solid-formulations <mesh.inp> <new.inp> <choices.json>");
    return 2;
}
try
{
    var (mesh, source) = addSet ? AddSet(args) : setFormulations ? SetFormulations(args) : (MeshFiles.Read(args[0]), File.ReadAllBytes(args[0]));
    Console.WriteLine(JsonSerializer.Serialize(new {
        success = true, schemaVersion = 1, meshOnly = true,
        SourceSha256 = Convert.ToHexStringLower(SHA256.HashData(source)),
        engineeringOwner = "Original CaeModel/CaeMesh INP mesh reader; renderer DTO only",
        nodes = mesh.Nodes.Values.Select(n => new { id = n.Id, x = n.X, y = n.Y, z = n.Z }),
        elements = mesh.Elements.Values.Select(e => new { id = e.Id, vtkCellType = e.GetVtkCellType(), nodeIds = e.NodeIds, vtkNodeIds = e.GetVtkNodeIds() }),
        elementBlocks = mesh.ElementBlocks.Select((b,i) => new { index=i, name=b.Name, formulation=b.InpElementTypeNames.Single(),
            count=b.ElementLabels.Count, compatibleFormulations=StaticAnalysisDeckWriter.CompatibleSolidFormulations(b.InpElementTypeNames.Single()) }),
        nodeSets = mesh.NodeSets.Select(entry => new { name = entry.Key, count = entry.Value.Length }),
        elementSets = mesh.ElementSets.Select(entry => new { name = entry.Key, count = entry.Value.Length }),
        authoredSet = addSet ? new { kind = args[3], name = args[4], ids = (args[3] == "node" ? mesh.NodeSets : mesh.ElementSets)[args[4]] } : null,
        warnings = mesh.Warnings, omittedKeywords = mesh.OmittedKeywords,
        solverExecuted = false
    }));
    return 0;
}
catch (Exception e) when (e is IOException or InvalidDataException or ArgumentException or CaeGlobals.CaeException or
    FormatException or OverflowException or NotSupportedException or IndexOutOfRangeException or JsonException)
{
    Console.Error.WriteLine(JsonSerializer.Serialize(new { success = false, error = e.Message }));
    return 1;
}

static (InpMeshData Mesh, byte[] Bytes) SetFormulations(string[] arguments)
{
    var original = MeshFiles.Read(arguments[1]);
    if (original.Warnings.Length != 0 || original.OmittedKeywords.Length != 0)
        throw new InvalidDataException("Formulation editing requires a standalone mesh without omissions or fallback warnings.");
    if (new FileInfo(arguments[3]).Length > 64*1024)
        throw new InvalidDataException("Formulation choices exceed the bounded input size.");
    var choices = JsonSerializer.Deserialize<string[]>(File.ReadAllText(arguments[3]));
    if (choices == null || choices.Length != original.ElementBlocks.Count)
        throw new InvalidDataException("Provide one formulation choice per original element block.");
    for (int i=0; i<choices.Length; i++)
        if (!StaticAnalysisDeckWriter.CompatibleSolidFormulations(original.ElementBlocks[i].InpElementTypeNames.Single()).Contains(choices[i]))
            throw new InvalidDataException("The requested formulation is not compatible with the original solid topology.");
    // Change only TYPE in original headers: preserve pyramid input and every
    // coordinate/connectivity/set record, using the original reader for readback.
    string text = File.ReadAllText(arguments[1]);
    int block = 0;
    string updated = Regex.Replace(text, @"(?im)^\*ELEMENT\b[^\r\n]*", m => {
        string choice=choices[block++];
        return Regex.Replace(m.Value, @"(?i)(\bTYPE\s*=\s*)[^,\r\n]+", n => n.Groups[1].Value+choice);
    });
    if (block != choices.Length) throw new InvalidDataException("Element block inventory changed during editing.");
    var checkedMesh = InpFileReader.ReadMeshData(updated.Replace("\r", "").Split('\n'));
    bool SameSets(Dictionary<string,int[]> a, Dictionary<string,int[]> b) => a.Count==b.Count &&
        a.All(e=>b.TryGetValue(e.Key,out var ids) && e.Value.Order().SequenceEqual(ids.Order()));
    if (checkedMesh.Nodes.Count!=original.Nodes.Count || checkedMesh.Elements.Count!=original.Elements.Count ||
        checkedMesh.Warnings.Length!=0 || checkedMesh.OmittedKeywords.Length!=0 ||
        original.Nodes.Any(e=>!checkedMesh.Nodes.TryGetValue(e.Key,out var n) || n.X!=e.Value.X || n.Y!=e.Value.Y || n.Z!=e.Value.Z) ||
        original.Elements.Any(e=>!checkedMesh.Elements.TryGetValue(e.Key,out var other) || !e.Value.NodeIds.SequenceEqual(other.NodeIds)) ||
        !SameSets(original.NodeSets,checkedMesh.NodeSets) || !SameSets(original.ElementSets,checkedMesh.ElementSets) ||
        checkedMesh.ElementBlocks.Where((b,i)=>b.InpElementTypeNames.Single()!=choices[i]).Any())
        throw new InvalidDataException("Formulation readback changed original mesh identities, topology or sets.");
    byte[] bytes=Encoding.UTF8.GetBytes(updated);
    using var output=new FileStream(arguments[2],FileMode.CreateNew,FileAccess.Write,FileShare.None);
    output.Write(bytes);
    return (checkedMesh,bytes);
}

static (InpMeshData Mesh, byte[] Bytes) AddSet(string[] arguments)
{
    string kind = arguments[3];
    string name = arguments[4];
    if (kind is not ("node" or "element"))
        throw new InvalidDataException("Choose a node or element set.");
    if (!Regex.IsMatch(name, @"\A[A-Za-z_][A-Za-z0-9_-]{0,79}\z"))
        throw new InvalidDataException("Use a set name of up to 80 ASCII letters, digits, underscores or hyphens, starting with a letter or underscore.");
    using var source = File.OpenRead(arguments[1]);
    if (source.Length > InpFileReader.MeshDataMaximumCharacters)
        throw new InvalidDataException("Standalone mesh input exceeds 16 MiB.");
    using var input = new StreamReader(source);
    string text = input.ReadToEnd().Replace("\r\n", "\n").Replace('\r', '\n');
    string[] lines = text.Split('\n');
    if (lines.Any(line => line.Length > 0 && char.IsWhiteSpace(line[0]) && line.TrimStart().StartsWith('*')))
        throw new InvalidDataException("Mesh keywords must start in the first column.");
    var original = InpFileReader.ReadMeshData(lines);
    if (original.Warnings.Length != 0 || original.OmittedKeywords.Length != 0)
        throw new InvalidDataException("Set authoring requires a standalone mesh without warnings or omitted keywords.");
    var sets = kind == "node" ? original.NodeSets : original.ElementSets;
    if (sets.Keys.Any(existing => string.Equals(existing, name, StringComparison.OrdinalIgnoreCase)))
        throw new InvalidDataException("A set of this kind already has that name.");

    if (arguments[5].Length > 12_000)
        throw new InvalidDataException("The set label list is too long.");
    string[] tokens = arguments[5].Split(',');
    var ids = new HashSet<int>();
    if (arguments[0] == "add-region-set")
    {
        if (tokens.Length > 256 || tokens.Distinct(StringComparer.OrdinalIgnoreCase).Count() != tokens.Length)
            throw new InvalidDataException("Choose at most 256 distinct source mesh sets.");
        foreach (string token in tokens)
        {
            if (!sets.TryGetValue(token, out int[] members) || members.Length == 0)
                throw new InvalidDataException("Each source set must exist for the selected mesh entity kind.");
            ids.UnionWith(members);
        }
        if (ids.Count > 100000)
            throw new InvalidDataException("A CAD region set requires at most 100000 mesh IDs.");
    }
    else
    {
        if (tokens.Length > 1000)
            throw new InvalidDataException("A set requires at most 1000 IDs.");
        foreach (string token in tokens)
        {
            if (!int.TryParse(token, NumberStyles.None, CultureInfo.InvariantCulture, out int id) || id < 1 ||
                !(kind == "node" ? original.Nodes.ContainsKey(id) : original.Elements.ContainsKey(id)))
                throw new InvalidDataException("Each ID must belong to the selected mesh entity kind.");
            if (!ids.Add(id))
                throw new InvalidDataException("Duplicate IDs are not allowed in a new set.");
        }
    }

    // Preserve the source records. Pass the combined deck through the original
    // INP reader before publishing the session copy.
    string keyword = kind == "node" ? "Nset" : "Elset";
    var updatedText = new StringBuilder(text).Append('\n').Append('*').Append(keyword)
        .Append(", ").Append(keyword).Append('=').Append(name).Append('\n');
    foreach (var row in ids.Order().Chunk(8))
        updatedText.AppendJoin(", ", row).Append('\n');
    string updated = updatedText.ToString();
    var checkedMesh = InpFileReader.ReadMeshData(updated.Split('\n'));
    var checkedSets = kind == "node" ? checkedMesh.NodeSets : checkedMesh.ElementSets;
    if (!checkedSets.TryGetValue(name, out int[] labels) || !ids.SetEquals(labels) ||
        checkedMesh.Warnings.Length != 0 || checkedMesh.OmittedKeywords.Length != 0)
        throw new InvalidDataException("The original mesh reader did not retain the new set.");
    byte[] result = Encoding.UTF8.GetBytes(updated);
    if (result.Length > InpFileReader.MeshDataMaximumCharacters)
        throw new InvalidDataException("The edited mesh exceeds the reader byte limit.");
    using var output = new FileStream(arguments[2], FileMode.CreateNew, FileAccess.Write, FileShare.None);
    output.Write(result);
    return (checkedMesh, result);
}

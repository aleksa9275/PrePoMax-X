using System.Globalization;
using System.Runtime.InteropServices;
using System.Text.Json;
using CaeGlobals;
using CaeMesh;
using CaeModel;
using DynamicTypeDescriptor;
using FileInOut.Input;
using PrePoMaxX.MeshDeck;

internal static class Program
{
    private static readonly List<object> Checks = new();
    private static int failed;
    private static void Require(bool value) { if (!value) throw new Exception("Independent mesh contract failed."); }
    private static void Near(double a, double b) => Require(double.IsFinite(a) && Math.Abs(a - b) < 1e-12);
    private static void Check(string name, Action action)
    {
        try { action(); Checks.Add(new { name, passed = true }); }
        catch (Exception error) { failed++; Checks.Add(new { name, passed = false, error = error.GetBaseException().Message }); }
    }
    private static void Rejected(Action action)
    {
        try { action(); } catch (Exception error) when (error is CaeException or ArgumentException or FormatException or
            IndexOutOfRangeException or OverflowException or NotSupportedException or IOException) { return; }
        throw new Exception("Expected rejection.");
    }
    private static InpMeshData Read(string text) => InpFileReader.ReadMeshData(text.Replace("\r", "").Split('\n'));
    private static string Deck(string type, int count, bool multiline = false) =>
        "*NODE, NSET=ALL\n" + string.Join("\n", Enumerable.Range(1, count).Select(id => $"{id}, {id}, {id % 3}, 0")) +
        $"\n*ELEMENT, TYPE={type}, ELSET=PART\n101, " +
        string.Join(multiline ? ",\n" : ", ", Enumerable.Range(1, count)) + "\n";
    private static void SameMesh(InpMeshData a, InpMeshData b)
    {
        Require(a.Nodes.Keys.Order().SequenceEqual(b.Nodes.Keys.Order()) && a.Elements.Keys.Order().SequenceEqual(b.Elements.Keys.Order()));
        foreach (int id in a.Nodes.Keys)
        {
            var x = a.Nodes[id]; var y = b.Nodes[id];
            Require(x.Id == y.Id && x.X == y.X && x.Y == y.Y && x.Z == y.Z);
        }
        foreach (int id in a.Elements.Keys)
            Require(a.Elements[id].GetType() == b.Elements[id].GetType() && a.Elements[id].NodeIds.SequenceEqual(b.Elements[id].NodeIds));
        foreach (var pair in a.NodeSets) Require(b.NodeSets[pair.Key].SequenceEqual(pair.Value));
        foreach (var pair in a.ElementSets) Require(b.ElementSets[pair.Key].SequenceEqual(pair.Value));
        Require(a.ElementBlocks.Select(block => string.Join(",", block.InpElementTypeNames)).SequenceEqual(
            b.ElementBlocks.Select(block => string.Join(",", block.InpElementTypeNames))));
    }
    private static int Main()
    {
        var sample = File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "unit-cube.inp"));
        var cube = Read(sample);
        Check("real INP cube IDs, bounds and sets", () =>
        {
            Require(cube.Nodes.Count == 8 && cube.Elements.Count == 1 && cube.Elements[101] is LinearHexaElement);
            Require(cube.Elements[101].NodeIds.SequenceEqual(new[] { 11,23,37,41,59,61,73,89 }));
            Require(cube.NodeSets["FIXED"].SequenceEqual(new[] { 11,41,59,89 }) && cube.ElementSets["SOLIDS"].SequenceEqual(new[] { 101 }));
        });
        Check("original unit-cube geometry and integral", () =>
        {
            var result = MeshFiles.Measure(cube).Single();
            Near(result.Measure, 1); Near(result.Integral, 1);
            foreach (double value in result.Centroid) Near(value, .5);
        });
        Check("actual cube export/reimport retains mesh and sets", () => SameMesh(cube, Read(MeshDeckWriter.WriteMesh(cube))));
        Check("mesh-only omissions are visible", () =>
        {
            var model = Read(sample + "*MATERIAL, NAME=STEEL\n*ELASTIC\n210000, .3\n*STEP\n*STATIC\n*END STEP\n");
            Require(model.OmittedKeywords.Length == 5 && model.OmittedKeywords.Contains("*ELASTIC"));
            Require(!MeshDeckWriter.WriteMesh(model).Contains("210000"));
        });
        (string Name, int Count, Type Type)[] families = {
            ("T3D2",2,typeof(LinearBeamElement)),("T3D3",3,typeof(ParabolicBeamElement)),
            ("S3",3,typeof(LinearTriangleElement)),("S6",6,typeof(ParabolicTriangleElement)),
            ("S4R",4,typeof(LinearQuadrilateralElement)),("S8R",8,typeof(ParabolicQuadrilateralElement)),
            ("C3D4",4,typeof(LinearTetraElement)),("C3D10",10,typeof(ParabolicTetraElement)),
            ("C3D6",6,typeof(LinearWedgeElement)),("C3D15",15,typeof(ParabolicWedgeElement)),
            ("C3D8R",8,typeof(LinearHexaElement)),("C3D20R",20,typeof(ParabolicHexaElement)) };
        foreach (var family in families)
            Check("original " + family.Name + " multiline topology and export roundtrip", () =>
            {
                var mesh = Read(Deck(family.Name, family.Count, true));
                Require(mesh.Elements[101].GetType() == family.Type && mesh.Elements[101].NodeIds.SequenceEqual(Enumerable.Range(1, family.Count)));
                SameMesh(mesh, Read(MeshDeckWriter.WriteMesh(mesh)));
            });
        Check("quadratic tetrahedron measurement remains gated", () => Rejected(() => MeshFiles.Measure(Read(Deck("C3D10",10)))));
        Check("quadratic pyramid original node ordering", () => Require(Read(Deck("C3D13",13)).Elements[101].NodeIds.SequenceEqual(
            new[] { 1,2,3,4,5,6,9,11,7,8,10,12,13 })));
        foreach (string type in new[] { "C3D5", "C3D5I", "C3D5R", "C3D13", "C3D13I", "C3D13R" })
        {
            int count = type.StartsWith("C3D5") ? 5 : 13;
            Check(type + " export requires explicit conversion", () => Rejected(() => MeshDeckWriter.WriteMesh(Read(Deck(type,count)))));
            foreach (var conversion in new[] { ConvertPyramidsToEnum.Wedges, ConvertPyramidsToEnum.Hexahedrons })
                Check(type + " explicit original conversion " + conversion, () =>
                {
                    var mesh = Read(MeshDeckWriter.WriteMesh(Read(Deck(type,count)), conversion));
                    int expected = count == 5 ? conversion == ConvertPyramidsToEnum.Wedges ? 6 : 8 :
                        conversion == ConvertPyramidsToEnum.Wedges ? 15 : 20;
                    Require(mesh.Elements[101].NodeIds.Length == expected && mesh.Elements[101].NodeIds.All(id => id > 0 && id <= count));
                    var canonical = Read(MeshDeckWriter.WriteMesh(Read(Deck(count == 5 ? "C3D5" : "C3D13",count)), conversion));
                    Require(mesh.Elements[101].NodeIds.SequenceEqual(canonical.Elements[101].NodeIds));
                });
        }
        Check("longest-prefix formulation fallback is explicit", () =>
        {
            var mesh = Read(Deck("C3D20RH",20));
            Require(mesh.ElementBlocks[0].InpElementTypeNames.Single() == "C3D20R" && mesh.Warnings.Length == 1);
            Require(mesh.Warnings[0].Contains("Formulation-specific behavior may be lost"));
            Rejected(() => MeshDeckWriter.WriteMesh(mesh));
        });
        Check("same named block retains distinct integration formulations", () =>
        {
            var mesh = Read(Deck("C3D8",8) + "*ELEMENT, TYPE=C3D8R, ELSET=PART\n102,1,2,3,4,5,6,7,8\n");
            Require(mesh.ElementBlocks.Count == 2 && mesh.ElementSets["PART"].SequenceEqual(new[] {101,102}));
            SameMesh(mesh, Read(MeshDeckWriter.WriteMesh(mesh)));
        });
        Check("generated and referenced sets merge without ID renumbering", () =>
        {
            var mesh = Read(Deck("C3D8",8) + "*NSET, NSET=ODD, GENERATE\n1,7,2\n*NSET, NSET=COMBINED\nODD,2\n");
            Require(mesh.NodeSets["ODD"].SequenceEqual(new[] {1,3,5,7}) && mesh.NodeSets["COMBINED"].SequenceEqual(new[] {1,2,3,5,7}));
            SameMesh(mesh, Read(MeshDeckWriter.WriteMesh(mesh)));
        });
        Check("two-dimensional node records retain zero Z", () => Require(Read("*NODE\n1,0,0\n2,1,0\n3,0,1\n*ELEMENT,TYPE=S3\n10,1,2,3").Nodes[3].Z == 0));
        Check("roundtrip coordinate precision", () =>
        {
            var mesh = Read(Deck("C3D4",4).Replace("1, 1, 1, 0", "1, 1.2345678901234567, 1e-100, -2.5e100"));
            SameMesh(mesh, Read(MeshDeckWriter.WriteMesh(mesh)));
        });
        Check("reader and writer use invariant culture and restore caller culture", () =>
        {
            var prior = CultureInfo.CurrentCulture;
            try
            {
                CultureInfo.CurrentCulture = CultureInfo.GetCultureInfo("de-DE");
                var mesh = Read(Deck("C3D4",4).Replace("1, 1, 1, 0", "1, 1.25, .5, 0"));
                Near(mesh.Nodes[1].X,1.25);
                Require(MeshDeckWriter.WriteMesh(mesh).Contains("1.25") && CultureInfo.CurrentCulture.Name == "de-DE");
            }
            finally { CultureInfo.CurrentCulture = prior; }
        });
        Check("failed read restores caller culture", () =>
        {
            var prior = CultureInfo.CurrentCulture;
            try { CultureInfo.CurrentCulture = CultureInfo.GetCultureInfo("fr-FR"); Rejected(() => Read(Deck("BAD",4))); Require(CultureInfo.CurrentCulture.Name == "fr-FR"); }
            finally { CultureInfo.CurrentCulture = prior; }
        });
        Check("original assembly ownership and enum metadata", () =>
        {
            Require(typeof(InpFileReader).Assembly.GetName().Name == "CaeModel" && typeof(InpElementSet).Assembly.GetName().Name == "CaeMesh");
            Require(typeof(StandardValueAttribute).Assembly.GetName().Name == "CaeGlobals");
            var attr = (StandardValueAttribute)typeof(ConvertPyramidsToEnum).GetField("Wedges")!.GetCustomAttributes(typeof(StandardValueAttribute), false).Single();
            Require(attr.DisplayName == "Collapsed wedges" && attr.Visible && attr.Enabled);
            Require(new[] { typeof(InpFileReader).Assembly,typeof(FeNode).Assembly,typeof(StandardValueAttribute).Assembly }.All(a =>
                a.GetReferencedAssemblies().All(r => r.Name == "CaeGlobals" || r.Name == "CaeMesh" || r.Name == "System" || r.Name.StartsWith("System."))));
        });
        Check("concurrent standalone reads retain their own IDs and sets", () => Parallel.For(0,30,index =>
        {
            int id = index + 1000;
            var mesh = Read(Deck("C3D4",4).Replace("101, ",id + ", "));
            Require(mesh.Elements.ContainsKey(id) && mesh.ElementSets["PART"].Single() == id);
        }));
        var bad = new Dictionary<string,string> {
            ["unknown topology"] = Deck("UNKNOWN",4),
            ["missing element type"] = Deck("C3D4",4).Replace("TYPE=C3D4, ",""),
            ["duplicate node"] = Deck("C3D4",4).Replace("2, 2, 2, 0","1, 2, 2, 0"),
            ["duplicate element"] = Deck("C3D4",4) + "*ELEMENT, TYPE=C3D4\n101,1,2,3,4\n",
            ["empty element block"] = Deck("C3D4",4) + "*ELEMENT, TYPE=C3D4\n",
            ["missing connectivity"] = Deck("C3D4",4).Replace("101, 1, 2, 3, 4","101,1,2,3"),
            ["extra connectivity"] = Deck("C3D4",4).Replace("101, 1, 2, 3, 4","101,1,2,3,4,1"),
            ["missing node reference"] = Deck("C3D4",4).Replace("101, 1, 2, 3, 4","101,1,2,3,9"),
            ["nonfinite coordinate"] = Deck("C3D4",4).Replace("1, 1, 1, 0","1,NaN,0,0"),
            ["negative ID"] = Deck("C3D4",4).Replace("101, ","-101, "),
            ["overspecified node"] = Deck("C3D4",4).Replace("1, 1, 1, 0","1,1,1,1,1"),
            ["include boundary"] = Deck("C3D4",4) + "*INCLUDE,INPUT=secret.inp\n",
            ["coordinate transform"] = Deck("C3D4",4) + "*SYSTEM\n1,0,0\n",
            ["node coordinate system"] = Deck("C3D4",4).Replace("NSET=ALL","NSET=ALL,SYSTEM=C"),
            ["duplicate formulation parameter"] = Deck("C3D4",4).Replace("TYPE=C3D4","TYPE=C3D4,TYPE=C3D8"),
            ["unknown named set"] = Deck("C3D4",4) + "*NSET,NSET=BAD\nMISSING\n",
            ["missing set ID"] = Deck("C3D4",4) + "*ELSET,ELSET=BAD\n999\n",
            ["zero generate step"] = Deck("C3D4",4) + "*NSET,NSET=BAD,GENERATE\n1,4,0\n",
            ["negative generate step"] = Deck("C3D4",4) + "*NSET,NSET=BAD,GENERATE\n1,4,-1\n",
            ["unbounded generate"] = Deck("C3D4",4) + "*NSET,NSET=BAD,GENERATE\n1,2147483647,1\n",
            ["set generation limit"] = Deck("C3D4",4) + "*NSET,NSET=BAD,GENERATE\n1,1000000,1\n",
            ["missing set name"] = Deck("C3D4",4) + "*NSET\n1,2\n",
            ["empty mesh"] = "*HEADING\nNo mesh\n" };
        foreach (var pair in bad) Check("reject " + pair.Key, () => Rejected(() => Read(pair.Value)));
        Console.WriteLine(JsonSerializer.Serialize(new { success = failed == 0, passed = Checks.Count - failed, failed,
            checks = Checks, runtime = new { architecture = RuntimeInformation.ProcessArchitecture.ToString() } }));
        return failed == 0 ? 0 : 1;
    }
}

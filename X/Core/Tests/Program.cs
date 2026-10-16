using System.Globalization;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text.Json;
using CaeGlobals;
using CaeMesh;

internal static class Program
{
    static readonly List<object> Checks = new();
    static readonly List<object> Vectors = new();
    static int Failed;
    static void Require(bool condition) { if (!condition) throw new Exception("Contract failed."); }
    static void Near(double actual, double expected, double tolerance = 1e-10) =>
        Require(double.IsFinite(actual) && Math.Abs(actual - expected) <= tolerance);
    static void Check(string name, Action test)
    {
        try { test(); Checks.Add(new { name, passed = true }); }
        catch (Exception error) { Failed++; Checks.Add(new { name, passed = false, error = error.Message }); }
    }
    static void ThrowsCae(Action test)
    {
        try { test(); } catch (CaeException) { return; }
        throw new Exception("Expected the shared CaeGlobals.CaeException.");
    }
    sealed class Tokens
    {
        readonly string[] items;
        int index;
        public Tokens(string path) => items = string.Join(" ", File.ReadLines(path)
            .Where(line => !line.StartsWith('#'))).Split((char[])null, StringSplitOptions.RemoveEmptyEntries);
        public bool HasNext => index < items.Length;
        public string Next() => items[index++];
        public void Expect(string value) => Require(Next() == value);
        public int Int() => int.Parse(Next(), CultureInfo.InvariantCulture);
        public double Number() => double.Parse(Next(), CultureInfo.InvariantCulture);
    }

    static bool Matches(ThreeBlockGrid grid, double[][] inner, int[][] quads, int folded, double tolerance,
                        out double deviation)
    {
        deviation = 0;
        if (grid.InnerUv.Length != inner.Length || grid.Quads.Length != quads.Length ||
            grid.NumberOfFoldedQuads != folded) return false;
        for (int i = 0; i < quads.Length; i++)
            if (!grid.Quads[i].SequenceEqual(quads[i])) return false;
        for (int i = 0; i < inner.Length; i++) for (int d = 0; d < 2; d++)
        {
            if (!double.IsFinite(grid.InnerUv[i][d])) return false;
            deviation = Math.Max(deviation, Math.Abs(grid.InnerUv[i][d] - inner[i][d]));
        }
        return deviation <= tolerance;
    }

    static void OriginalVectors()
    {
        var tokens = new Tokens(Path.Combine(AppContext.BaseDirectory, "three_block_vectors.txt"));
        int count = 0;
        while (tokens.HasNext)
        {
            tokens.Expect("case"); string name = tokens.Next();
            var uv = new double[3][][]; var xyz = new double[3][][];
            for (int k = 0; k < 3; k++)
            {
                tokens.Expect("side"); Require(tokens.Int() == k); int n = tokens.Int();
                uv[k] = new double[n][]; xyz[k] = new double[n][];
                for (int i = 0; i < n; i++)
                {
                    uv[k][i] = new[] { tokens.Number(), tokens.Number() };
                    xyz[k][i] = new[] { tokens.Number(), tokens.Number(), tokens.Number() };
                }
            }
            tokens.Expect("inner"); var inner = new double[tokens.Int()][];
            for (int i = 0; i < inner.Length; i++) inner[i] = new[] { tokens.Number(), tokens.Number() };
            tokens.Expect("quads"); var quads = new int[tokens.Int()][];
            for (int i = 0; i < quads.Length; i++) quads[i] = new[] { tokens.Int(), tokens.Int(), tokens.Int(), tokens.Int() };
            tokens.Expect("folded"); int folded = tokens.Int(); tokens.Expect("end");
            double size = uv.SelectMany(s => s).SelectMany(p => p).Max(Math.Abs);
            double deviation = 0;
            Check("upstream vector " + name, () => Require(Matches(ThreeBlockMapping.Map(uv, xyz, null),
                inner, quads, folded, 1e-9 * Math.Max(size, 1), out deviation)));
            Vectors.Add(new { name, maxDeviation = deviation, quads = quads.Length });
            count++;
        }
        Check("all 13 upstream vectors executed", () => Require(count == 13));
    }

    static int Main()
    {
        Check("type and assembly identities retained", () => {
            Require(typeof(CaeException).AssemblyQualifiedName == "CaeGlobals.CaeException, CaeGlobals, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null");
            Require(typeof(ThreeBlockMapping).Assembly.GetName().Name == "CaeMesh");
            Require(typeof(ThreeBlockMapping).Assembly.GetName().Version == new Version(1, 0, 0, 0));
            var inner = new Exception("cause"); var error = new CaeException("message", inner);
            Require(error.Message == "message" && ReferenceEquals(error.InnerException, inner));
        });
        OriginalVectors();
        double root3 = Math.Sqrt(3);
        double[][][] uv = {
            new[] { new[] {0.0, 0}, new[] {1.0, 0}, new[] {2.0, 0} },
            new[] { new[] {2.0, 0}, new[] {1.5, root3 / 2}, new[] {1.0, root3} },
            new[] { new[] {1.0, root3}, new[] {0.5, root3 / 2}, new[] {0.0, 0} }
        };
        var xyz = uv.Select(side => side.Select(p => new[] {p[0], p[1], 0.0}).ToArray()).ToArray();
        var grid = ThreeBlockMapping.Map(uv, xyz, null);
        Check("independent equilateral centroid and counts", () => {
            Require(grid.NumberOfBoundaryNodes == 6 && grid.InnerUv.Length == 1 && grid.Quads.Length == 3);
            Near(grid.InnerUv[0][0], 1); Near(grid.InnerUv[0][1], root3 / 3);
            Require(grid.NumberOfFoldedQuads == 0 && grid.InnerXyz == null);
        });
        Check("area, manifold edges and Euler disk topology", () => {
            var points = uv.SelectMany(side => side.Take(2)).Concat(grid.InnerUv).ToArray();
            var edges = new Dictionary<(int, int), int>(); double area = 0;
            foreach (var quad in grid.Quads)
            {
                Require(quad.Distinct().Count() == 4); double twice = 0;
                for (int i = 0; i < 4; i++)
                {
                    int a = quad[i], b = quad[(i + 1) % 4];
                    var key = (Math.Min(a, b), Math.Max(a, b)); edges[key] = edges.GetValueOrDefault(key) + 1;
                    twice += points[a][0] * points[b][1] - points[b][0] * points[a][1];
                }
                Require(twice > 0); area += twice / 2;
            }
            Near(area, root3); Require(edges.Values.Count(v => v == 1) == 6);
            Require(edges.Values.Count(v => v == 2) == 3 && points.Length - edges.Count + grid.Quads.Length == 1);
        });
        Check("boundary node numbering closes and round trips", () => {
            for (int k = 0; k < 3; k++) Require(grid.GetBoundaryNodeId(k, 2) == grid.GetBoundaryNodeId((k + 1) % 3, 0));
            for (int id = 0; id < 6; id++) {
                Require(grid.TryGetBoundaryNode(id, out int k, out int i)); Require(grid.GetBoundaryNodeId(k, i) == id);
            }
            Require(!grid.TryGetBoundaryNode(6, out _, out _));
        });
        Check("host surface evaluator places inner coordinates", () => {
            var lifted = ThreeBlockMapping.Map(uv, xyz,
                flat => Enumerable.Range(0, flat.Length / 2).SelectMany(i => new[] { flat[2*i], flat[2*i+1], 5.0 }).ToArray());
            Near(lifted.InnerXyz[0][0], 1); Near(lifted.InnerXyz[0][1], root3 / 3); Near(lifted.InnerXyz[0][2], 5);
        });
        Check("bad evaluator output raises domain exception", () => {
            ThrowsCae(() => ThreeBlockMapping.Map(uv, xyz, _ => null));
            ThrowsCae(() => ThreeBlockMapping.Map(uv, xyz, _ => new[] { 1.0 }));
        });
        Check("mismatched geometry raises domain exception", () => {
            var bad = (double[][][])xyz.Clone(); bad[0] = xyz[0].Take(2).ToArray();
            ThrowsCae(() => ThreeBlockMapping.Map(uv, bad, null));
        });
        Check("invalid block counts raise domain exception", () => {
            var badUv = uv.Select(side => side.Take(2).ToArray()).ToArray();
            var badXyz = xyz.Select(side => side.Take(2).ToArray()).ToArray();
            ThrowsCae(() => ThreeBlockMapping.Map(badUv, badXyz, null));
        });
        Check("uniform scale and translation preserve topology", () => {
            var moved = uv.Select(side => side.Select(p => new[] {3*p[0]+7, 3*p[1]-4}).ToArray()).ToArray();
            var movedXyz = moved.Select(side => side.Select(p => new[] {p[0], p[1], 0.0}).ToArray()).ToArray();
            var mapped = ThreeBlockMapping.Map(moved, movedXyz, null);
            Near(mapped.InnerUv[0][0], 10); Near(mapped.InnerUv[0][1], root3 - 4);
            Require(mapped.Quads.Zip(grid.Quads).All(pair => pair.First.SequenceEqual(pair.Second)));
        });
        Check("changed coordinates and connectivity fail comparison", () => {
            Require(!Matches(grid, new[] {new[] {1.01, root3 / 3}}, grid.Quads, 0, 1e-9, out _));
            var bad = grid.Quads.Select(q => q.ToArray()).ToArray(); bad[0][0] = bad[0][1];
            Require(!Matches(grid, grid.InnerUv, bad, 0, 1e-9, out _));
        });
        Check("portable libraries have no Windows or presentation references", () => {
            foreach (var assembly in new[] {typeof(CaeException).Assembly, typeof(ThreeBlockMapping).Assembly})
                Require(!assembly.GetReferencedAssemblies().Any(a => a.Name.Contains("Windows") || a.Name.Contains("Drawing") || a.Name.Contains("VTK")));
        });
        Console.WriteLine(JsonSerializer.Serialize(new { success = Failed == 0, passed = Checks.Count - Failed, failed = Failed,
            runtime = new {os = RuntimeInformation.OSDescription, architecture = RuntimeInformation.ProcessArchitecture.ToString()},
            checks = Checks, vectors = Vectors }));
        return Failed == 0 ? 0 : 1;
    }
}

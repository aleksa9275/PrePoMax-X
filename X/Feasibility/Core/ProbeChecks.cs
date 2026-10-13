// Tests use independently specified coordinates and STL wire data, not a second FEM implementation.
using System.Globalization;
using System.Text;
using CaeGlobals;
using CaeMesh;
using QuantumConcepts.Formats.StereoLithography;

namespace PrePoMaxX.CoreProbe;

internal static class ProbeChecks
{
    private const string Triangle = """
        solid analytical
        facet normal 0 0 1
        outer loop
        vertex -1.25e0 2.5 -3
        vertex 0.25 2.5 -3
        vertex -1.25 4 -3
        endloop
        endfacet
        endsolid analytical
        """;

    internal static (int passed, int failed, List<object> checks, List<object> observations) Run(string cubePath)
    {
        int passed = 0, failed = 0;
        var checks = new List<object>();
        void Check(string name, Action action)
        {
            try
            {
                action(); passed++;
                checks.Add(new { name, status = "passed" });
            }
            catch (Exception exception)
            {
                failed++;
                checks.Add(new { name, status = "failed", detail = exception.Message });
            }
        }

        Check("existing_cube_triangle_count_and_bounds", () =>
        {
            using var stream = File.OpenRead(cubePath);
            var document = StlInspector.Read(stream);
            Require(document.Facets.Count == 12, "Expected 12 cube triangles.");
            var points = document.SelectMany(f => f.Vertices).ToArray();
            Coordinates(new Vec3D(points.Min(v => v.X), points.Min(v => v.Y), points.Min(v => v.Z)), 0, 0, 0);
            Coordinates(new Vec3D(points.Max(v => v.X), points.Max(v => v.Y), points.Max(v => v.Z)), 1, 1, 1);
        });
        Check("independent_ascii_coordinates_and_winding", () => AssertTriangle(ReadText(Triangle)));
        Check("independent_binary_coordinates_and_attributes", () =>
        {
            using var stream = BinaryTriangle();
            var document = StlInspector.Read(stream);
            AssertTriangle(document);
            Require(document.Facets[0].AttributeByteCount == 0x1234, "Binary attribute bytes changed.");
        });
        Check("ascii_round_trip_preserves_vertex_order_and_normals", () =>
        {
            var original = ReadText(Triangle);
            using var stream = new MemoryStream();
            original.WriteText(stream);
            stream.Position = 0;
            var actual = StlInspector.Read(stream);
            AssertTriangle(actual);
            Require(original.Equals(actual), "ASCII geometry/normal/order changed.");
        });
        Check("binary_round_trip_and_independent_wire_layout", () =>
        {
            using var input = BinaryTriangle();
            var original = StlInspector.Read(input);
            using var output = new MemoryStream();
            original.WriteBinary(output);
            Require(output.Length == 134, "Expected 84-byte header plus one 50-byte triangle.");
            output.Position = 80;
            using (var wire = new BinaryReader(output, Encoding.ASCII, leaveOpen: true))
            {
                Require(wire.ReadUInt32() == 1, "Writer triangle count changed.");
                foreach (float value in new float[] { 0, 0, 1, -1.25f, 2.5f, -3, .25f, 2.5f, -3, -1.25f, 4, -3 })
                    Require(wire.ReadSingle() == value, "Writer coordinate/normal layout changed.");
                Require(wire.ReadUInt16() == 0x1234, "Writer attribute layout changed.");
            }
            output.Position = 0;
            Require(original.Equals(StlInspector.Read(output)), "Binary geometry/normal/order changed.");
        });
        Check("binary_solid_header_uses_upstream_fallback", () =>
        {
            using var stream = BinaryTriangle(solidHeader: true);
            AssertTriangle(StlInspector.Read(stream));
        });
        Check("ascii_numbers_are_culture_independent", () =>
        {
            var previous = CultureInfo.CurrentCulture;
            try
            {
                CultureInfo.CurrentCulture = CultureInfo.GetCultureInfo("fr-FR");
                var original = ReadText(Triangle);
                using var stream = new MemoryStream();
                original.WriteText(stream);
                stream.Position = 0;
                AssertTriangle(StlInspector.Read(stream));
            }
            finally { CultureInfo.CurrentCulture = previous; }
        });
        Check("inspector_rejects_binary_count_mismatch", () =>
        {
            using var stream = BinaryTriangle(declaredCount: 2);
            Reject(() => StlInspector.Read(stream));
        });
        Check("inspector_rejects_solid_binary_count_mismatch", () =>
        {
            using var stream = BinaryTriangle(declaredCount: 2, solidHeader: true);
            Reject(() => StlInspector.Read(stream));
        });
        Check("inspector_rejects_truncated_binary_triangle", () =>
        {
            using var stream = BinaryTriangle();
            stream.SetLength(stream.Length - 5);
            Reject(() => StlInspector.Read(stream));
        });
        Check("inspector_rejects_empty_stream", () =>
        {
            using var stream = new MemoryStream();
            Reject(() => StlInspector.Read(stream));
        });
        Check("inspector_rejects_incomplete_ascii_triangle", () =>
            Reject(() => ReadText("solid incomplete\nfacet normal 0 0 1\nouter loop\nvertex 0 0 0\n")));
        Check("inspector_rejects_invalid_ascii_numeric_token", () =>
            Reject(() => ReadText(Triangle.Replace("-1.25e0", "invalid"))));
        Check("inspector_rejects_nonfinite_coordinates", () =>
        {
            using var stream = BinaryTriangle();
            stream.Position = 96; // first vertex X: header (84) + normal (12)
            using (var writer = new BinaryWriter(stream, Encoding.ASCII, leaveOpen: true)) writer.Write(float.NaN);
            stream.Position = 0;
            Reject(() => StlInspector.Read(stream));
        });
        Check("node_translation_preserves_identity", () =>
        {
            var node = new FeNode(42, 2, -3, 4);
            node.Translate(new Vec3D(-1, 5, .5));
            Node(node, 42, 1, 2, 4.5);
        });
        Check("node_rotation_around_nonorigin_center", () =>
        {
            var node = new FeNode(7, 2, 2, 3);
            node.Rotate(new Vec3D(1, 2, 3), new double[][] { [0, -1, 0], [1, 0, 0], [0, 0, 1] });
            Node(node, 7, 1, 3, 3);
        });
        Check("node_mirror_about_offset_plane", () =>
        {
            var node = new FeNode(8, 2, 5, 7);
            node.Mirror(new Vec3D(0, 3, 0), new Vec3D(0, 1, 0));
            Node(node, 8, 2, 1, 7);
        });
        Check("node_mirror_about_oblique_plane", () =>
        {
            var node = new FeNode(9, 3, 1, 5);
            double unit = 1 / Math.Sqrt(2);
            node.Mirror(new Vec3D(1, 1, 0), new Vec3D(unit, unit, 0));
            Node(node, 9, 1, -1, 5);
        });
        Check("node_anisotropic_scale_around_nonorigin_center", () =>
        {
            var node = new FeNode(10, 2, 4, 7);
            node.Scale(new Vec3D(1, 2, 3), [2, -1, .5]);
            Node(node, 10, 3, 0, 5);
        });
        Check("vector_normalization_known_length", () =>
        {
            var vector = new Vec3D(3, 4, 0);
            Near(vector.Normalize(), 5);
            Coordinates(vector, .6, .8, 0);
        });
        Check("zero_vector_normalization_is_finite", () =>
        {
            var vector = new Vec3D(0, 0, 0);
            Near(vector.Normalize(), 0);
            Coordinates(vector, 0, 0, 0);
        });
        Check("vector_cross_product_orientation", () =>
            Coordinates(Vec3D.CrossProduct(new Vec3D(1, 0, 0), new Vec3D(0, 1, 0)), 0, 0, 1));
        Check("circle_from_three_analytic_points", () =>
        {
            Vec3D.GetCircle(new Vec3D(1, 0, 0), new Vec3D(0, 1, 0), new Vec3D(-1, 0, 0),
                           out double radius, out Vec3D center, out Vec3D axis);
            Near(radius, 1);
            Coordinates(center, 0, 0, 0);
            Coordinates(axis, 0, 0, 1);
        });

        // Report raw reader behavior separately; it is not evidence of safe production import.
        var observations = new List<object>();
        using (var stream = BinaryTriangle(declaredCount: 2))
            observations.Add(new { name = "raw_binary_declared_count", declared = 2, parsed = STLDocument.Read(stream).Facets.Count });
        using (var stream = BinaryTriangle(solidHeader: true))
            observations.Add(new { name = "raw_solid_header_default", parsed = STLDocument.Read(stream).Facets.Count });
        try { STLDocument.Read(Triangle.Replace("-1.25e0", "invalid")); }
        catch (Exception exception)
        {
            observations.Add(new { name = "raw_invalid_numeric_token", exceptionType = exception.GetType().Name });
        }
        return (passed, failed, checks, observations);
    }

    private static STLDocument ReadText(string text)
    {
        using var stream = new MemoryStream(Encoding.ASCII.GetBytes(text));
        return StlInspector.Read(stream);
    }

    private static MemoryStream BinaryTriangle(uint declaredCount = 1, bool solidHeader = false)
    {
        var stream = new MemoryStream();
        using (var writer = new BinaryWriter(stream, Encoding.ASCII, leaveOpen: true))
        {
            byte[] header = new byte[80];
            Encoding.ASCII.GetBytes(solidHeader ? "solid binary probe" : "independent binary probe").CopyTo(header, 0);
            writer.Write(header);
            writer.Write(declaredCount);
            foreach (float value in new float[] { 0, 0, 1, -1.25f, 2.5f, -3, .25f, 2.5f, -3, -1.25f, 4, -3 }) writer.Write(value);
            writer.Write((ushort)0x1234);
        }
        stream.Position = 0;
        return stream;
    }

    private static void AssertTriangle(STLDocument document)
    {
        Require(document.Facets.Count == 1, "Expected one triangle.");
        var facet = document.Facets[0];
        Coordinates(new Vec3D(facet.Normal.X, facet.Normal.Y, facet.Normal.Z), 0, 0, 1);
        Coordinates(new Vec3D(facet.Vertices[0].X, facet.Vertices[0].Y, facet.Vertices[0].Z), -1.25, 2.5, -3);
        Coordinates(new Vec3D(facet.Vertices[1].X, facet.Vertices[1].Y, facet.Vertices[1].Z), .25, 2.5, -3);
        Coordinates(new Vec3D(facet.Vertices[2].X, facet.Vertices[2].Y, facet.Vertices[2].Z), -1.25, 4, -3);
        // Independent signed XY area: this triangle is counterclockwise with area 1.125.
        var a = facet.Vertices[0]; var b = facet.Vertices[1]; var c = facet.Vertices[2];
        Near(((b.X - a.X) * (c.Y - a.Y) - (b.Y - a.Y) * (c.X - a.X)) / 2, 1.125);
    }

    private static void Node(FeNode node, int id, double x, double y, double z)
    {
        Require(node.Id == id, "Node identity changed.");
        Coordinates(new Vec3D(node.Coor), x, y, z);
    }
    private static void Coordinates(Vec3D actual, double x, double y, double z)
    {
        Near(actual.X, x); Near(actual.Y, y); Near(actual.Z, z);
    }
    private static void Near(double actual, double expected)
    {
        Require(double.IsFinite(actual) && Math.Abs(actual - expected) <= 1e-12 * Math.Max(1, Math.Abs(expected)),
                $"Expected {expected:R}, got {actual:R}.");
    }
    private static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
    private static void Reject(Action action)
    {
        try { action(); }
        catch (InvalidDataException) { return; }
        throw new InvalidOperationException("Malformed input was accepted by the probe inspector.");
    }
}

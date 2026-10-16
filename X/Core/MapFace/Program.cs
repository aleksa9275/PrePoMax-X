using System.Text.Json;
using CaeGlobals;
using CaeMesh;

// Small host for the shared mapping API. Input/output are parameter-space
// geometry, not a PMX format or CAD mesher protocol.
internal static class Program
{
    private sealed record Face(double[][][] SideUv, double[][][] SideXyz);

    static int Main(string[] args)
    {
        if (args.Length != 1)
        {
            Console.Error.WriteLine("Usage: PrePoMaxX.MapFace <face.json>");
            return 2;
        }
        try
        {
            using var input = File.OpenRead(args[0]);
            if (input.Length > 1024 * 1024) throw new InvalidDataException("Input exceeds 1 MiB.");
            var face = JsonSerializer.Deserialize<Face>(input,
                new JsonSerializerOptions { PropertyNameCaseInsensitive = true, MaxDepth = 16 });
            if (face is null) throw new InvalidDataException("A face object is required.");
            Validate(face);
            var grid = ThreeBlockMapping.Map(face.SideUv, face.SideXyz, null);
            if (grid.InnerUv.Any(point => point.Any(value => !double.IsFinite(value))))
                throw new InvalidDataException("Mapping produced non-finite parameters.");
            Console.WriteLine(JsonSerializer.Serialize(new {
                success = true, grid.SideCounts, grid.NumberOfBoundaryNodes,
                grid.InnerUv, grid.Quads, grid.NumberOfFoldedQuads
            }));
            return 0;
        }
        catch (Exception error) when (error is IOException or InvalidDataException or UnauthorizedAccessException
                                    or JsonException or CaeException)
        {
            Console.Error.WriteLine(JsonSerializer.Serialize(new { success = false, error = error.Message }));
            return 1;
        }
    }

    static void Validate(Face face)
    {
        if (face.SideUv?.Length != 3 || face.SideXyz?.Length != 3)
            throw new InvalidDataException("Exactly three UV and XYZ sides are required.");
        int count = 0;
        for (int k = 0; k < 3; k++)
        {
            var uv = face.SideUv[k]; var xyz = face.SideXyz[k];
            if (uv is null || xyz is null || uv.Length < 2 || uv.Length != xyz.Length)
                throw new InvalidDataException("Every side needs matching UV/XYZ points, including both corners.");
            count += uv.Length - 1;
            if (count > 512) throw new InvalidDataException("At most 512 boundary segments are supported by this host.");
            for (int i = 0; i < uv.Length; i++)
                if (uv[i]?.Length != 2 || xyz[i]?.Length != 3 ||
                    !uv[i].All(double.IsFinite) || !xyz[i].All(double.IsFinite))
                    throw new InvalidDataException("UV/XYZ points must contain two/three finite numbers.");
        }
        for (int k = 0; k < 3; k++)
            if (!face.SideUv[k][^1].SequenceEqual(face.SideUv[(k + 1) % 3][0]) ||
                !face.SideXyz[k][^1].SequenceEqual(face.SideXyz[(k + 1) % 3][0]))
                throw new InvalidDataException("Side endpoints must form one closed boundary.");
    }
}

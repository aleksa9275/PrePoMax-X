using System;
using System.Linq;
using CaeGlobals;
using CaeMesh;

// Runs on the installed Windows .NET Framework CLR, using the same source
// closure as the portable libraries. This is not a full Windows solution build.
internal static class Smoke
{
    static int Main()
    {
        try
        {
            double r = Math.Sqrt(3);
            double[][][] uv = {
                new[] {new[] {0.0, 0}, new[] {1.0, 0}, new[] {2.0, 0}},
                new[] {new[] {2.0, 0}, new[] {1.5, r/2}, new[] {1.0, r}},
                new[] {new[] {1.0, r}, new[] {0.5, r/2}, new[] {0.0, 0}}
            };
            var xyz = uv.Select(side => side.Select(p => new[] {p[0], p[1], 0.0}).ToArray()).ToArray();
            var grid = ThreeBlockMapping.Map(uv, xyz, null);
            if (grid.Quads.Length != 3 || grid.NumberOfBoundaryNodes != 6 || grid.NumberOfFoldedQuads != 0 ||
                Math.Abs(grid.InnerUv[0][0] - 1) > 1e-10 || Math.Abs(grid.InnerUv[0][1] - r/3) > 1e-10)
                throw new Exception("Legacy geometry contract failed");
            bool rejected = false;
            try { ThreeBlockMapping.Map(uv, xyz, _ => new double[0]); }
            catch (CaeException) { rejected = true; }
            if (!rejected) throw new Exception("Legacy domain error contract failed");
            if (typeof(CaeException).AssemblyQualifiedName !=
                "CaeGlobals.CaeException, CaeGlobals, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null")
                throw new Exception("Legacy exception identity changed");
            Console.WriteLine("{\"success\":true,\"geometry\":true,\"domainError\":true,\"typeIdentity\":true,\"clr\":\"" +
                              Environment.Version + "\"}");
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine(error.GetType().Name + ": " + error.Message);
            return 1;
        }
    }
}

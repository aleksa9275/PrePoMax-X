using CaeMesh;
using System.Runtime.InteropServices;
using System.Text.Json;

// Test driver only. All count/grid behavior comes from unchanged source links.
internal static class Program
{
    static readonly List<object> Checks = new();
    static int Failed;
    static void Check(string name, Action action)
    {
        try { action(); Checks.Add(new {name, status="passed"}); }
        catch (Exception error) { Failed++; Checks.Add(new {name, status="failed", error=error.Message}); }
    }
    static void Require(bool condition) { if (!condition) throw new Exception("Assertion failed"); }

    // Independent count oracle: enumerate positive inner-line lengths whose
    // adjacent pairs cover the boundary sides, instead of repeating the formula.
    static int[] Solution(int[] sides)
    {
        for (int a=1; a<=12; a++) for (int b=1; b<=12; b++) for (int c=1; c<=12; c++)
            if (b+c==sides[0] && c+a==sides[1] && a+b==sides[2]) return new[]{a,b,c};
        return null;
    }
    static int Main(string[] args)
    {
        if (args.Length!=1 || args[0]!="--self-test")
        { Console.WriteLine("{\"success\":false,\"error\":\"Use --self-test\"}"); return 2; }
        var signatures = new List<string>();
        Check("1728 positive count triples against independent enumeration", () => {
            for (int a=1; a<=12; a++) for (int b=1; b<=12; b++) for (int c=1; c<=12; c++) {
                int[] sides={a,b,c}; var expected=Solution(sides);
                bool valid=TransfiniteSideTriple.AreCountsValid(sides);
                Require(valid==(expected!=null));
                if (valid) Require(Enumerable.Range(0,3).Select(k=>TransfiniteSideTriple.GetInnerLineCount(sides,k)).SequenceEqual(expected));
                signatures.Add($"{a},{b},{c}:"+(valid?string.Join(",",expected):"invalid"));
            }
        });
        Check("odd and degenerate side counts rejected", () => {
            Require(!TransfiniteSideTriple.AreCountsValid(new[]{2,2,3}));
            Require(!TransfiniteSideTriple.AreCountsValid(new[]{2,2,4}));
        });
        var grid=new ThreeBlockGrid(new[]{2,4,4}, new[]{new[]{0.3,0.2}}, null, new[]{new[]{0,1,10,9}}, 0);
        Check("boundary node count", ()=>Require(grid.NumberOfBoundaryNodes==10));
        Check("side endpoints share the next corner ID", ()=> {
            Require(grid.GetBoundaryNodeId(0,2)==2); Require(grid.GetBoundaryNodeId(1,4)==6);
            Require(grid.GetBoundaryNodeId(2,4)==0);
        });
        Check("all boundary IDs round trip", ()=> {
            for (int n=0;n<10;n++) { Require(grid.TryGetBoundaryNode(n,out int side,out int index)); Require(grid.GetBoundaryNodeId(side,index)==n); }
        });
        Check("inner node is not a boundary node", ()=>Require(!grid.TryGetBoundaryNode(10,out _,out _)));
        Check("stored grid topology and parameters", ()=> {
            Require(grid.InnerUv[0].SequenceEqual(new[]{0.3,0.2})); Require(grid.InnerXyz==null);
            Require(grid.Quads[0].SequenceEqual(new[]{0,1,10,9})); Require(grid.NumberOfFoldedQuads==0);
        });
        Console.WriteLine(JsonSerializer.Serialize(new {success=Failed==0, passed=Checks.Count-Failed, failed=Failed,
            runtime=new {os=RuntimeInformation.IsOSPlatform(OSPlatform.OSX)?"macOS":RuntimeInformation.IsOSPlatform(OSPlatform.Linux)?"Linux":"Windows",
                architecture=RuntimeInformation.ProcessArchitecture.ToString(), osArchitecture=RuntimeInformation.OSArchitecture.ToString(), framework=RuntimeInformation.FrameworkDescription},
            checks=Checks, countSignatures=signatures}));
        return Failed==0?0:1;
    }
}

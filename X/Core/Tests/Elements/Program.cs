using System.Runtime.InteropServices;
using System.Text.Json;
using CaeGlobals;
using CaeMesh;
using PrePoMaxX.MeasureMesh;

namespace PrePoMaxX.ElementTests;

internal static class Program
{
    private static readonly List<object> Checks = new();
    private static readonly List<object> Observations = new();
    private static readonly List<object> OpenCorrectnessChecks = new();
    private static int failed;
    private static void Require(bool value) { if (!value) throw new Exception("Independent contract failed."); }
    private static void Near(double actual, double expected)
    {
        if (!double.IsFinite(actual) || Math.Abs(actual - expected) > 1e-10 * Math.Max(1, Math.Abs(expected)))
            throw new Exception($"Expected {expected:R}; measured {actual:R}.");
    }
    private static void Check(string name, Action action)
    {
        try { action(); Checks.Add(new { name, passed = true }); }
        catch (Exception error) { failed++; Checks.Add(new { name, passed = false, error = error.GetBaseException().Message }); }
    }
    private static void Throws<T>(Action action) where T : Exception
    {
        try { action(); } catch (T) { return; }
        throw new Exception("Expected " + typeof(T).Name);
    }
    private sealed record Shape(string Name, double[][] Points, int[][] Edges, double Measure, double[] Centroid);
    private static IEnumerable<Shape> Shapes()
    {
        yield return new("Beam", new[] {new double[]{0,0,0},new double[]{2,0,0}}, new[]{new[]{0,1}}, 2, new double[]{1,0,0});
        yield return new("Triangle", new[] {new double[]{0,0,0},new double[]{2,0,0},new double[]{0,3,0}},
            new[]{new[]{0,1},new[]{1,2},new[]{2,0}}, 3, new double[]{2.0/3,1,0});
        yield return new("Quadrilateral", new[] {new double[]{0,0,0},new double[]{2,0,0},new double[]{2,3,0},new double[]{0,3,0}},
            new[]{new[]{0,1},new[]{1,2},new[]{2,3},new[]{3,0}}, 6, new double[]{1,1.5,0});
        yield return new("Tetra", new[] {new double[]{0,0,0},new double[]{2,0,0},new double[]{0,3,0},new double[]{0,0,4}},
            new[]{new[]{0,1},new[]{1,2},new[]{2,0},new[]{0,3},new[]{1,3},new[]{2,3}}, 4, new double[]{0.5,0.75,1});
        yield return new("Pyramid", new[] {new double[]{0,0,0},new double[]{2,0,0},new double[]{2,2,0},new double[]{0,2,0},new double[]{1,1,3}},
            new[]{new[]{0,1},new[]{1,2},new[]{2,3},new[]{3,0},new[]{0,4},new[]{1,4},new[]{2,4},new[]{3,4}}, 4, new double[]{1,1,0.75});
        yield return new("Wedge", new[] {new double[]{0,0,0},new double[]{2,0,0},new double[]{0,3,0},new double[]{0,0,4},new double[]{2,0,4},new double[]{0,3,4}},
            new[]{new[]{0,1},new[]{1,2},new[]{2,0},new[]{3,4},new[]{4,5},new[]{5,3},new[]{0,3},new[]{1,4},new[]{2,5}}, 12, new double[]{2.0/3,1,2});
        yield return new("Hexa", new[] {new double[]{0,0,0},new double[]{2,0,0},new double[]{2,3,0},new double[]{0,3,0},
                new double[]{0,0,4},new double[]{2,0,4},new double[]{2,3,4},new double[]{0,3,4}},
            new[]{new[]{0,1},new[]{1,2},new[]{2,3},new[]{3,0},new[]{4,5},new[]{5,6},new[]{6,7},new[]{7,4},new[]{0,4},new[]{1,5},new[]{2,6},new[]{3,7}}, 24, new double[]{1,1.5,2});
    }
    private static double Value(double[] point) => 2 + point[0] + 2 * point[1] + 3 * point[2];
    private static void Main()
    {
        foreach (var shape in Shapes())
        foreach (bool quadratic in new[] {false,true})
        {
            var points = shape.Points.Select(p => p.ToArray()).ToList();
            if (quadratic) foreach (var edge in shape.Edges)
                points.Add(Enumerable.Range(0,3).Select(i => (shape.Points[edge[0]][i] + shape.Points[edge[1]][i])/2).ToArray());
            int[] ids = Enumerable.Range(0,points.Count).Select(i => 11 + i * 17).ToArray();
            string name = (quadratic ? "Parabolic" : "Linear") + shape.Name + "Element";
            Type type = typeof(FeElement).Assembly.GetType("CaeMesh." + name, true);
            FeElement element = (FeElement)Activator.CreateInstance(type, 901, 23, ids.ToArray());
            var nodes = ids.Select((id,i) => new FeNode(id,points[i][0],points[i][1],points[i][2])).ToDictionary(n => n.Id);
            var values = ids.Select((id,i) => (id,value:Value(points[i]))).ToDictionary(p => p.id,p => p.value);
            Check(name + " analytical measure and centroid", () => {
                var cg=element.GetCG(nodes,out double measure); Near(measure,shape.Measure);
                for(int i=0;i<3;i++) Near(cg[i],shape.Centroid[i]);
                Observations.Add(new {name,measure,centroid=cg});
            });
            if (type==typeof(ParabolicTetraElement))
            {
                double expected=shape.Measure*Value(shape.Centroid), actual=element.Integrate(nodes,values);
                OpenCorrectnessChecks.Add(new {name="quadratic tetrahedron affine integral",passed=Math.Abs(expected-actual)<=1e-10,
                    expected,actual,disposition="Unresolved original-source discrepancy; excluded from measurement host"});
                Check("quadratic tetrahedron discrepancy remains visible",()=>Require(Math.Abs(expected-actual)>1));
            }
            else Check(name + " affine field integral", () => Near(element.Integrate(nodes,values),shape.Measure*Value(shape.Centroid)));
            Check(name + " constant field integral", () => Near(element.Integrate(nodes,ids.ToDictionary(id=>id,id=>2.0)),2*shape.Measure));
            Check(name + " connectivity and identity", () => {
                Require(element.Id==901 && element.PartId==23 && element.NodeIds.SequenceEqual(ids));
                Require(element.GetVtkNodeIds().Order().SequenceEqual(ids.Order()) && element.GetGmshNodeIds().Order().SequenceEqual(ids.Order()));
                Require(!ReferenceEquals(element.GetVtkNodeIds(),element.NodeIds));
                if (type!=typeof(ParabolicPyramidElement)) Require(FeElement.IsParabolic(element)==quadratic);
                Require(type.AssemblyQualifiedName=="CaeMesh."+name+", CaeMesh, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null");
                Require(type.IsDefined(typeof(SerializableAttribute),false));
            });
            Check(name + " copy independence", () => {
                var copy=element.DeepCopy(); Require(copy.GetType()==type && copy.Id==901 && copy.PartId==23 && copy.NodeIds.SequenceEqual(ids));
                copy.NodeIds[0]=-99; Require(element.NodeIds[0]==ids[0]);
            });
            Check(name + (type==typeof(ParabolicTetraElement) ? " host rejects unresolved integral" : " callable host agrees with original methods"), () => {
                var input=new MeshInput(ids.Select((id,i)=>new NodeInput(id,points[i][0],points[i][1],points[i][2],Value(points[i]))).ToArray(),
                    new[]{new ElementInput(901,name,ids,23)});
                if(type==typeof(ParabolicTetraElement)) { Throws<NotSupportedException>(()=>Measurement.Run(input));return; }
                var output=Measurement.Run(input).Single(); Near(output.Measure,shape.Measure);Near(output.Integral,shape.Measure*Value(shape.Centroid));
                Require(output.Id==901 && output.PartId==23 && output.VtkCellType==element.GetVtkCellType());
            });
        }
        bool pyramidClassified=FeElement.IsParabolic(new ParabolicPyramidElement(1,Enumerable.Range(1,13).ToArray()));
        OpenCorrectnessChecks.Add(new {name="quadratic pyramid classification",passed=pyramidClassified,expected=true,actual=pyramidClassified,
            disposition="Original helper omits quadratic pyramid; host uses explicit type factories"});
        Check("quadratic pyramid classifier discrepancy remains visible",()=>Require(!pyramidClassified));
        var quadNodes=new[] {new NodeInput(11,1,0,0),new NodeInput(29,3,0,0),new NodeInput(43,3,2,0),new NodeInput(71,1,2,0)};
        var quad=new MeshInput(quadNodes,new[]{new ElementInput(101,"LinearQuadrilateralElement",new[]{11,29,43,71})});
        Check("thickness integral preserves geometry", () => {var result=Measurement.Run(quad with {Scale="thickness",Thickness=0.25}).Single();Near(result.Measure,4);Near(result.Integral,1);});
        Check("axisymmetric integral uses full circumference", () => Near(Measurement.Run(quad with {Scale="axisymmetric"}).Single().Integral,16*Math.PI));
        Check("invalid connectivity rejected by host", () => Throws<ArgumentException>(()=>Measurement.Run(quad with {Elements=new[]{new ElementInput(101,"LinearQuadrilateralElement",new[]{11,29,43,999})}})));
        Check("repeated connectivity rejected by host", () => Throws<ArgumentException>(()=>Measurement.Run(quad with {Elements=new[]{new ElementInput(101,"LinearQuadrilateralElement",new[]{11,29,43,43})}})));
        Check("duplicate node IDs rejected by host", () => Throws<ArgumentException>(()=>Measurement.Run(quad with {Nodes=new[]{quadNodes[0],quadNodes[0]}})));
        Check("nonfinite values rejected by host", () => Throws<ArgumentException>(()=>Measurement.Run(quad with {Nodes=new[]{quadNodes[0] with {Value=double.NaN}}})));
        Check("negative radius rejected by host", () => Throws<ArgumentException>(()=>Measurement.Run(quad with {Scale="axisymmetric",Nodes=new[]{quadNodes[0] with {X=-1}}})));
        Check("unsupported scaling rejected by original solid element", () => {
            var nodes=new Dictionary<int,FeNode>{{1,new FeNode(1,0,0,0)},{2,new FeNode(2,1,0,0)},{3,new FeNode(3,0,1,0)},{4,new FeNode(4,0,0,1)}};
            Throws<NotSupportedException>(()=>new LinearTetraElement(1,new[]{1,2,3,4}).Integrate(nodes,nodes.Keys.ToDictionary(id=>id,id=>1.0),IntegrationScale.FromThickness(1)));
        });
        Check("solid face area numbering and surface traction weights", () => {
            var tetra=new LinearTetraElement(1,new[]{11,29,43,71});
            var nodes=new Dictionary<int,FeNode>{{11,new FeNode(11,0,0,0)},{29,new FeNode(29,2,0,0)},{43,new FeNode(43,0,3,0)},{71,new FeNode(71,0,0,4)}};
            Near(tetra.GetArea(FeFaceName.S1,nodes),3);
            Require(tetra.GetNodeIdsFromFaceName(FeFaceName.S1).SequenceEqual(new[]{11,29,43}));
            foreach(var weight in tetra.GetEquivalentForcesFromFaceName(FeFaceName.S1)) Near(weight,1.0/3);
        });
        Check("special elements retain assembly ownership and dimensions", () => {
            FeElement[] special={new MassElement(1,new[]{11}),new LinearSpringElement(2,new[]{11,29}),new LinearGapElement(3,new[]{11,29})};
            Require(special.Select(e=>e.Dimension).SequenceEqual(new[]{0,1,1}));
            Require(special.All(e=>e.GetType().Assembly.GetName().Name=="CaeMesh"));
            Require(typeof(CompareIntArray).Assembly.GetName().Name=="CaeGlobals");
        });
        Console.WriteLine(JsonSerializer.Serialize(new {success=failed==0,fullyAccepted=failed==0 && OpenCorrectnessChecks.Count==0,
            passed=Checks.Count-failed,failed,openCorrectnessChecks=OpenCorrectnessChecks,
            runtime=new {os=RuntimeInformation.OSDescription,architecture=RuntimeInformation.ProcessArchitecture.ToString()},checks=Checks,observations=Observations}));
        Environment.ExitCode=failed==0?0:1;
    }
}

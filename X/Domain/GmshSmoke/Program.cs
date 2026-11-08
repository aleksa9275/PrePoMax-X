using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using GmshCommon;

class Program
{
    static readonly List<string> Passed = new List<string>();
    static void Require(bool value, string name)
    {
        if (!value) throw new Exception(name);
        Passed.Add(name);
    }
    static int Main(string[] args)
    {
        bool initialized = false;
        try
        {
            Gmsh.Initialize(); initialized = true;
            if (args.Length == 0) return 0; // isolated loader rejection controls
            string work = args[0]; Directory.CreateDirectory(work);
            Gmsh.Option.SetNumber("General.Terminal", 0);
            Require(Gmsh.Option.GetString("General.Version") == "4.13.0", "pinned runtime version");
            Gmsh.Model.Add("Phase A — surface");
            int[] points = { Gmsh.Model.OCC.AddPoint(0,0,0), Gmsh.Model.OCC.AddPoint(2,0,0),
                             Gmsh.Model.OCC.AddPoint(2,1,0), Gmsh.Model.OCC.AddPoint(0,1,0) };
            int[] curves = Enumerable.Range(0,4).Select(i => Gmsh.Model.OCC.AddLine(points[i], points[(i+1)%4])).ToArray();
            int surface = Gmsh.Model.OCC.AddPlaneSurface(new[] { Gmsh.Model.OCC.AddCurveLoop(curves) });
            Gmsh.Model.OCC.Synchronize();
            Require(Gmsh.Model.GetCurrent() == "Phase A — surface", "UTF-8 model name");
            Gmsh.Model.GetBoundary(new[] { Tuple.Create(2,surface) }, out var boundary, false, false, false);
            Require(boundary.Length == 4 && boundary.All(x => x.Item1 == 1), "C dim-tag array ownership");
            Gmsh.Model.OCC.GetMass(2, surface, out double area);
            Require(Math.Abs(area - 2) < 1e-12, "OCCT rectangle area");
            foreach (int curve in curves) Gmsh.Model.Mesh.SetTransfiniteCurve(curve, 5);
            Gmsh.Model.Mesh.SetTransfiniteAutomatic(new[] { Tuple.Create(2,surface) }, 2.35, true);
            Gmsh.Model.Mesh.Generate(2);
            foreach (int curve in curves)
            {
                Gmsh.Model.Mesh.GetNodes(out var tags, out var xyz, 1, curve, true, false);
                Require(tags.Length == 5 && xyz.Length == 15, "prescribed curve nodes " + curve);
            }
            Gmsh.Model.Mesh.GetElements(out var types, out var elements, out var connectivity, 2, surface);
            Require(types.SequenceEqual(new[] { 3 }) && elements[0].Length == 16 && connectivity[0].Length == 64,
                    "structured 16-quad surface / nested C arrays");
            int physical = Gmsh.Model.AddPhysicalGroup(2, new[] {surface}, "surface ü");
            Require(Gmsh.Model.GetPhysicalName(2,physical) == "surface ü" &&
                    Gmsh.Model.GetEntitiesForPhysicalGroup(2,physical).SequenceEqual(new[] {surface}), "physical group round trip");
            string step = Path.Combine(work,"plate ü.step"); Gmsh.Write(step); Gmsh.Clear();
            Gmsh.Model.OCC.ImportShapes(step, out var imported, true, "step"); Gmsh.Model.OCC.Synchronize();
            Require(imported.Length == 1 && imported[0].Item1 == 2, "STEP export/import with Unicode path");
            Gmsh.Model.OCC.Extrude(imported, 0,0,1, out var extruded, new int[0], new double[0], false);
            Gmsh.Model.OCC.Synchronize();
            int volume = extruded.Single(t => t.Item1 == 3).Item2;
            Gmsh.Model.OCC.GetMass(3,volume,out double mass);
            Require(Math.Abs(mass - 2) < 1e-12, "OCCT extruded volume");
            int callbackCalls = 0;
            Gmsh.Model.Mesh.SetSizeCallback((dim,tag,x,y,z,lc) => { callbackCalls++; return 0.35; });
            GC.Collect(); GC.WaitForPendingFinalizers();
            Gmsh.Model.Mesh.Generate(3); Gmsh.Model.Mesh.RemoveSizeCallback();
            Require(callbackCalls > 0, "native size callback lifetime");
            Gmsh.Model.Mesh.SetOrder(2);
            Gmsh.Model.Mesh.GetElements(out types, out elements, out connectivity, 3, volume);
            Require(types.SequenceEqual(new[] { 11 }) && elements[0].Length > 0 &&
                    connectivity[0].Length == elements[0].Length * 10, "quadratic tetrahedra connectivity");
            Gmsh.Model.Mesh.GetElementQualities(elements[0], out var quality, "minSJ");
            Require(quality.Length == elements[0].Length && quality.All(q => q > 0 && double.IsFinite(q)),
                    "positive tetrahedron scaled Jacobians");
            Require(Gmsh.Model.Mesh.GetElementProperties(11, out int dim3, out int order, out int count,
                    out var local, out int primary).Length > 0 && dim3 == 3 && order == 2 && count == 10 && primary == 4,
                    "element property C outputs");
            string mesh = Path.Combine(work,"volume.msh"); Gmsh.Write(mesh); Gmsh.Clear(); Gmsh.Open(mesh);
            Gmsh.Model.Mesh.GetElements(out types, out elements, out connectivity, 3, volume);
            Require(types.SequenceEqual(new[] { 11 }) && elements[0].Length == quality.Length, "MSH mesh reopen");
            bool refused = false;
            try { Gmsh.Model.GetType(3,999999); } catch (Exception) { refused = true; }
            Require(refused, "native error becomes managed exception");
            Console.WriteLine(JsonSerializer.Serialize(new { success=true, passed=Passed.Count, checks=Passed,
                tetrahedra=quality.Length, minimumScaledJacobian=quality.Min() }));
            return 0;
        }
        catch (Exception e)
        {
            Console.Error.WriteLine(JsonSerializer.Serialize(new { success=false, passed=Passed.Count, checks=Passed, error=e.ToString() }));
            return 1;
        }
        finally { if (initialized) Gmsh.FinalizeAll(); }
    }
}

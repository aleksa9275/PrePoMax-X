using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using CaeGlobals;
using Python.Runtime;
using vtkControl;
namespace PrePoMax
{
    public sealed class NativeSpatialQueries : IDisposable
    {
        readonly Controller controller;
        readonly Func<vtkMaxActor[]> actorSource;
        PyModule scope;
        // Mouse precision is a viewport property. Replayed selections keep their
        // recorded world precision; new headless picks must specify it explicitly.
        public double? SelectionPrecision {get;set;}
        public NativeSpatialQueries(Controller controller,Func<vtkMaxActor[]> actors) {this.controller=controller;actorSource=actors;}
        object Grid(PartExchangeData data,bool surface)
        {
            if(surface)
            {
                var topology=LegacyPolyTopology.GetSurfaceTopology(data);
                return new {coordinates=data.Nodes.Coor,nodeIds=data.Nodes.Ids,cells=topology.Cells,types=topology.Types,cellIds=topology.GlobalCellIds};
            }
            return new {coordinates=data.Nodes.Coor,nodeIds=data.Nodes.Ids,cells=data.Cells.CellNodeIds,types=data.Cells.Types,cellIds=data.Cells.Ids};
        }
        JsonElement QueryNative(string operation,double[] point,string[] names,double[][] planes=null)
        {
            var actors=actorSource().Where(a=>a.Data.Pickable && a.Data.Geometry.Cells.CellNodeIds!=null).Select(a=>new {name=a.Data.Name,visible=a.VtkMaxActorVisible,surface=Grid(a.Data.Geometry,true),volume=operation=="frustum" && a.Data.VolumeGridAvailable?Grid(controller.GetVolumeGridData(a.Data.Name,-1),false):null}).ToArray();
            string payload=JsonSerializer.Serialize(new {operation,point,names,planes,actors});
            return CallNative(payload);
        }
        public void ProcessSurface(string operation,vtkMaxActorData actor,object[] parameters)
        {
            CallNative(JsonSerializer.Serialize(new {operation,surface=Grid(actor.Geometry,true),parameters}));
        }
        JsonElement CallNative(string payload)
        {
            Python.PythonEngineManager.EnsureNativeHostInitialized();
            using(Py.GIL())
            {
                if(scope==null)
                {
                    scope=Py.CreateScope();
                    using var stream=typeof(NativeSpatialQueries).Assembly.GetManifestResourceStream("PrePoMaxX.SpatialPython");
                    using var reader=new StreamReader(stream);
                    scope.Exec(reader.ReadToEnd());
                }
                using var input=new PyString(payload);
                using var function=scope.Get("query");
                using var result=function.Invoke(input);
                using var json=JsonDocument.Parse(result.As<string>());
                return json.RootElement.Clone();
            }
        }
        static int[] Ints(JsonElement value)=>value.EnumerateArray().Select(x=>x.GetInt32()).ToArray();
        static double[] Doubles(JsonElement value)=>value.EnumerateArray().Select(x=>x.GetDouble()).ToArray();
        public object Query(string name,object[] arguments)
        {
            switch(name)
            {
                case "GetSelectionPrecision":return SelectionPrecision??throw new InvalidOperationException("Set an explicit world selection precision for new headless picks.");
                case "GetGeometryPickProperties":
                {
                    var hit=QueryNative("pick",(double[])arguments[0],(string[])arguments[4]);
                    arguments[1]=-1;arguments[2]=null;arguments[3]=null;
                    if(hit.ValueKind!=JsonValueKind.Null)
                    {
                        int element=hit.GetProperty("element").GetInt32();int[] face=Ints(hit.GetProperty("nodes"));
                        var data=controller.GetCellFaceActorData(element,face);
                        vtkSelectionGeometry.GetClosestEdgeCell(Doubles(hit.GetProperty("point")),data,out int[] edge,out _,out _,out _);
                        arguments[1]=element;arguments[2]=edge;arguments[3]=face;
                    }
                    return null;
                }
                case "GetClosestCellsOnParts":
                {
                    var hits=QueryNative("closest",(double[])arguments[0],(string[])arguments[1]);
                    var distances=new List<double>();var normals=new List<double[]>();
                    foreach(var hit in hits.EnumerateArray())
                    {
                        distances.Add(hit.ValueKind==JsonValueKind.Null?-1:Math.Sqrt(hit.GetProperty("distance2").GetDouble()));
                        normals.Add(hit.ValueKind==JsonValueKind.Null?null:Normal(hit.GetProperty("coordinates").EnumerateArray().Select(Doubles).ToArray()));
                    }
                    arguments[2]=distances.ToArray();arguments[3]=normals.ToArray();return null;
                }
                case "GetPointAndCellIdsInsideFrustum":
                {
                    var hit=QueryNative("frustum",null,(string[])arguments[1],(double[][])arguments[0]);
                    arguments[2]=Ints(hit.GetProperty("points"));arguments[3]=Ints(hit.GetProperty("cells"));return null;
                }
                default:throw new NotSupportedException("Native spatial host does not supply: "+name);
            }
        }
        // Same first-three-point normal as original vtkControl.GetCellNormal.
        static double[] Normal(double[][] points)
        {
            if(points==null || points.Length<3)return null;
            double[] p0=points[0],p1=points[1],p2=points[2];
            double[] a={p1[0]-p0[0],p1[1]-p0[1],p1[2]-p0[2]},b={p2[0]-p0[0],p2[1]-p0[1],p2[2]-p0[2]};
            double[] normal={a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]};
            double length=Math.Sqrt(normal[0]*normal[0]+normal[1]*normal[1]+normal[2]*normal[2]);
            return length==0?null:new[]{normal[0]/length,normal[1]/length,normal[2]/length};
        }
        public void Dispose() {if(scope!=null)using(Py.GIL()) {scope.Dispose();scope=null;}}
    }
}

using System.Drawing;
using System.Linq;
namespace vtkControl
{
    // A headless presentation handle retains Controller-generated geometry. Native
    // renderer objects stay in the host, outside model state and command history.
    public partial class vtkMaxActor
    {
        public vtkMaxActorData Data { get; }
        public bool Visible {get;set;} = true;
        public Color Color { get; set; }
        public bool UseSecondaryHighlightColor {get;set;}
        public uint MemorySize {get;set;}
        readonly bool nodal;
        public SurfaceTopology SurfaceTopology {get;}
        public vtkMaxActor(vtkMaxActorData data,bool createNodalActor=false)
        {
            Data=data;Color=data.Color;nodal=createNodalActor || data.Geometry.Cells?.CellNodeIds==null;
            if(!nodal)SurfaceTopology=GetSurfaceTopology(data.Geometry);
            long nodes=data.Geometry.Nodes.Coor?.LongLength??0;
            long cells=SurfaceTopology?.Cells.Sum(c=>(long)c.Length)??0;
            MemorySize=(uint)System.Math.Min(uint.MaxValue,(nodes*32+cells*4+1023)/1024);
        }
        public int GetNumberOfElements() => nodal?(Data.Geometry.Nodes.Coor?.Length??0):SurfaceTopology.Cells.Length;
        public vtkMaxActorData GetExportData(vtkEdgesVisibility edges)
        {
            var result=new vtkMaxActorData {Name=Data.Name,ColorTable=new[]{Color,Color.Black,Color.Black},ColorContours=Data.ColorContours};
            result.Geometry=null;
            if(Visible && !nodal && edges!=vtkEdgesVisibility.Wireframe && Data.ActorRepresentation!=vtkMaxActorRepresentation.Wire)
            {
                result.Geometry=new CaeGlobals.PartExchangeData();
                result.Geometry.Nodes.Coor=Data.Geometry.Nodes.Coor.Select(p=>p.Select(v=>(double)(float)v).ToArray()).ToArray();
                result.Geometry.Nodes.Values=Data.ColorContours?Data.Geometry.Nodes.Values:null;
                result.Geometry.Cells.CellNodeIds=SurfaceTopology.Cells.Where((c,i)=>SurfaceTopology.Types[i]==5).ToArray();
            }
            result.ElementEdges=Visible && edges==vtkEdgesVisibility.ElementEdges?ExportEdges(Data.ElementEdges):null;
            result.ModelEdges=Visible && edges!=vtkEdgesVisibility.NoEdges?ExportEdges(Data.ModelEdgesToDraw??Data.ModelEdges):null;
            return result;
        }
        static CaeGlobals.PartExchangeData ExportEdges(CaeGlobals.PartExchangeData source)
        {
            if(source?.Nodes.Coor==null || source.Cells.CellNodeIds==null)return null;
            var result=new CaeGlobals.PartExchangeData();
            result.Nodes.Coor=source.Nodes.Coor.Select(p=>p.Select(v=>(double)(float)v).ToArray()).ToArray();
            result.Cells.CellNodeIds=source.Cells.CellNodeIds.SelectMany(c=>c.Length==3?new[]{new[]{c[0],c[1]},new[]{c[1],c[2]}}:new[]{c}).ToArray();
            return result;
        }
    }
}

using System.Drawing;
using System.Linq;
using vtkControl;

namespace PrePoMax
{
    /// <summary>Export geometry of the headless host (no view): what vtkControl.GetVtkMaxActorData gives the 3MF
    /// export of a drawn scene - the visible triangles in the actor colour, the contour values, and the element and
    /// model edges the edge visibility shows. With a view, the original vtkControl answers.</summary>
    public static class HeadlessExport
    {
        public static vtkMaxActorData GetExportData(vtkMaxActor actor, vtkEdgesVisibility edges)
        {
            vtkMaxActorData data = actor.Data;
            var result = new vtkMaxActorData { Name = data.Name, ColorTable = new[] { actor.Color, Color.Black, Color.Black }, ColorContours = data.ColorContours };
            result.Geometry = null;
            if (actor.VtkMaxActorVisible && !actor.Nodal && edges != vtkEdgesVisibility.Wireframe && data.ActorRepresentation != vtkMaxActorRepresentation.Wire)
            {
                SurfaceTopology topology = LegacyPolyTopology.GetSurfaceTopology(data.Geometry);
                result.Geometry = new CaeGlobals.PartExchangeData();
                result.Geometry.Nodes.Coor = data.Geometry.Nodes.Coor.Select(p => p.Select(v => (double)(float)v).ToArray()).ToArray();
                result.Geometry.Nodes.Values = data.ColorContours ? data.Geometry.Nodes.Values : null;
                result.Geometry.Cells.CellNodeIds = topology.Cells.Where((c, i) => topology.Types[i] == 5).ToArray();
            }
            result.ElementEdges = actor.VtkMaxActorVisible && edges == vtkEdgesVisibility.ElementEdges ? ExportEdges(data.ElementEdges) : null;
            result.ModelEdges = actor.VtkMaxActorVisible && edges != vtkEdgesVisibility.NoEdges ? ExportEdges(data.ModelEdgesToDraw ?? data.ModelEdges) : null;
            return result;
        }
        static CaeGlobals.PartExchangeData ExportEdges(CaeGlobals.PartExchangeData source)
        {
            if (source?.Nodes.Coor == null || source.Cells.CellNodeIds == null) return null;
            var result = new CaeGlobals.PartExchangeData();
            result.Nodes.Coor = source.Nodes.Coor.Select(p => p.Select(v => (double)(float)v).ToArray()).ToArray();
            result.Cells.CellNodeIds = source.Cells.CellNodeIds.SelectMany(c => c.Length == 3 ? new[] { new[] { c[0], c[1] }, new[] { c[1], c[2] } } : new[] { c }).ToArray();
            return result;
        }
    }
}

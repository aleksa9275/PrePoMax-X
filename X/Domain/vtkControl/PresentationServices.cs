using System;
using System.Drawing;
using System.Linq;
namespace vtkControl
{
    // Native renderer-dependent exports are explicit host services.
    public static class PresentationServices
    {
        public static Func<vtkMaxActorData,double[][][]> StlTriangles {get;set;}
    }
    public partial class vtkMaxActorData
    {
        public double[][][] GetStlTriangles()
        {
            if(PresentationServices.StlTriangles!=null)return PresentationServices.StlTriangles(this);
            var topology=vtkMaxActor.GetSurfaceTopology(Geometry);
            return topology.Cells.Select(cell=>
            {
                if(cell.Length!=3)throw new NotSupportedException();
                // vtkPoints in the original actor stores float coordinates.
                return cell.Select(index=>Geometry.Nodes.Coor[index].Select(v=>(double)(float)v).ToArray()).ToArray();
            }).ToArray();
        }
    }
    public static class vtkMaxWidgetHighlight
    {
        public const double WidgetFillOpacity=0.05,WidgetBorderOpacity=0.5,SurfaceFillOpacity=0.15;
        public const float WidgetBorderLineWidth=2f;
        public static Color BorderColor => Color.RoyalBlue;
        public static Color FillColor => Color.LightSkyBlue;
    }
    public class vtkControl {public const int MaxImageMagnification=4;}
}

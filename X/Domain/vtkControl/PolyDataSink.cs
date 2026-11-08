using System;
using System.Collections.Generic;
using System.Linq;
using CaeGlobals;

// Data-only targets for the unchanged original AddCellDataToPoly method. These
// collect its cell connectivity; native VTK still builds and queries datasets.
namespace Kitware.VTK
{
    public sealed class vtkIdList
    {
        internal int[] Ids=Array.Empty<int>();
        public static vtkIdList New()=>new();
        public void SetNumberOfIds(int size) {Ids=new int[size];}
        public void SetId(int index,int id) {Ids[index]=id;}
    }
    public sealed class vtkPolyData
    {
        internal readonly List<(int Type,int[] Nodes)> Cells=new();
        public void Allocate(int capacity,int extension) {Cells.EnsureCapacity(capacity);}
        public void InsertNextCell(int type,vtkIdList nodes) {Cells.Add((type,nodes.Ids.ToArray()));}
        public void Squeeze() {Cells.TrimExcess();}
    }
}
namespace vtkControl
{
    public sealed class SurfaceTopology
    {
        public int[] Types {get;set;}
        public int[][] Cells {get;set;}
        public int[] GlobalCellIds {get;set;}
    }
    public partial class vtkMaxActor
    {
        public static SurfaceTopology GetSurfaceTopology(PartExchangeData data)
        {
            var surface=new Kitware.VTK.vtkPolyData();var edges=new Kitware.VTK.vtkPolyData();
            AddCellDataToPoly(data,ref surface,ref edges,out int[] counts,false);
            return new SurfaceTopology {Types=surface.Cells.Select(c=>c.Type).ToArray(),Cells=surface.Cells.Select(c=>c.Nodes).ToArray(),GlobalCellIds=counts==null?null:data.Cells.Ids.SelectMany((id,index)=>Enumerable.Repeat(id,counts[index])).ToArray()};
        }
    }
}

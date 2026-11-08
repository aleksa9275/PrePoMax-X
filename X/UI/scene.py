"""Native VTK scene built solely from original Controller actor data."""
from vtkmodules.vtkCommonCore import vtkPoints, vtkIdList, vtkIntArray
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkPolyData, vtkCellArray
from vtkmodules.vtkRenderingCore import vtkActor, vtkDataSetMapper, vtkCellPicker
import vtkmodules.vtkRenderingOpenGL2


def grid(data, topology=None):
    result = vtkUnstructuredGrid()
    points = vtkPoints()
    for point in data.Nodes.Coor:
        points.InsertNextPoint(*point)
    result.SetPoints(points)
    cells = topology.Cells if topology is not None else data.Cells.CellNodeIds
    types = topology.Types if topology is not None else data.Cells.Types
    ids = topology.GlobalCellIds if topology is not None else data.Cells.Ids
    labels = vtkIntArray()
    labels.SetName('OriginalElementId')
    if cells is None:
        for index in range(points.GetNumberOfPoints()):
            cell = vtkIdList()
            cell.InsertNextId(index)
            result.InsertNextCell(1, cell)
    else:
        for index, nodes in enumerate(cells):
            cell = vtkIdList()
            for node in nodes:
                cell.InsertNextId(int(node))
            result.InsertNextCell(int(types[index]), cell)
            if ids is not None:
                labels.InsertNextValue(int(ids[index]))
    if labels.GetNumberOfTuples():
        result.GetCellData().AddArray(labels)
    return result


class Scene:
    def __init__(self, renderer):
        self.renderer = renderer
        self.actors = []
        self.names = {}
        self.highlight_actor = None
        self.source = []

    def clear(self):
        self.renderer.RemoveAllViewProps()
        self.actors.clear()
        self.names.clear()
        self.highlight_actor = None

    def update(self, source):
        self.clear()
        self.source = list(source)
        for original in self.source:
            data = original.Data
            if not original.Visible or data.Geometry.Nodes.Coor is None:
                continue
            mapper = vtkDataSetMapper()
            mapper.SetInputData(grid(data.Geometry, original.SurfaceTopology))
            actor = vtkActor()
            actor.SetMapper(mapper)
            color = original.Color
            actor.GetProperty().SetColor(color.R / 255, color.G / 255, color.B / 255)
            actor.GetProperty().SetOpacity(color.A / 255)
            actor.GetProperty().SetPointSize(max(4, data.NodeSize))
            actor.GetProperty().SetLineWidth(max(1, data.LineWidth))
            actor.SetPickable(data.Pickable)
            actor.GetProperty().SetEdgeVisibility(False)
            actor.GetProperty().SetEdgeColor(.15, .18, .22)
            self.renderer.AddActor(actor)
            self.actors.append(actor)
            self.names[actor.GetAddressAsString('')] = str(data.Name)
            edges = data.ModelEdgesToDraw or data.ModelEdges
            if edges is not None and edges.Nodes.Coor is not None:
                edge_mapper = vtkDataSetMapper()
                edge_mapper.SetInputData(grid(edges))
                edge_actor = vtkActor()
                edge_actor.SetMapper(edge_mapper)
                edge_actor.GetProperty().SetColor(.15, .18, .22)
                edge_actor.PickableOff()
                self.renderer.AddActor(edge_actor)

    def show_selection(self, source):
        for actor in getattr(self,'selection_actors',[]):
            self.renderer.RemoveActor(actor)
        self.selection_actors=[]
        self.highlight_actor=None
        for original in source:
            mapper=vtkDataSetMapper()
            mapper.SetInputData(grid(original.Data.Geometry,original.SurfaceTopology))
            mapper.SetResolveCoincidentTopologyToPolygonOffset()
            mapper.SetRelativeCoincidentTopologyPolygonOffsetParameters(-1,-1)
            mapper.SetRelativeCoincidentTopologyPointOffsetParameter(-2)
            actor=vtkActor()
            actor.SetMapper(mapper)
            color=original.Color
            actor.GetProperty().SetColor(color.R/255,color.G/255,color.B/255)
            actor.GetProperty().SetPointSize(max(10,original.Data.NodeSize))
            actor.GetProperty().SetRenderPointsAsSpheres(True)
            actor.GetProperty().LightingOff()
            actor.PickableOff()
            self.renderer.AddActor(actor)
            self.selection_actors.append(actor)
            self.highlight_actor=actor

    def pick(self, x, y):
        picker = vtkCellPicker()
        picker.SetTolerance(.005)
        if not picker.Pick(x, y, 0, self.renderer):
            return None
        actor = picker.GetActor()
        name = self.names.get(actor.GetAddressAsString(''))
        dataset = picker.GetDataSet()
        labels = dataset.GetCellData().GetArray('OriginalElementId')
        return name, picker.GetPickPosition(), (labels.GetValue(picker.GetCellId()) if labels else None)

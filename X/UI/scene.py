"""Native VTK scene built solely from original Controller actor data."""
from vtkmodules.vtkCommonCore import vtkPoints, vtkIdList, vtkIntArray, vtkFloatArray
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkPolyData, vtkCellArray
from vtkmodules.vtkRenderingCore import vtkActor, vtkDataSetMapper, vtkCellPicker
import vtkmodules.vtkRenderingOpenGL2


def coordinates(nodes):
    points=vtkPoints()
    if nodes.FlatCoor is not None:
        flat=list(nodes.FlatCoor)
        for i in range(0,len(flat),3):points.InsertNextPoint(*flat[i:i+3])
    elif nodes.Coor is not None:
        for point in nodes.Coor:points.InsertNextPoint(*point)
    return points

def scalars(dataset,values):
    if values is None:return
    array=vtkFloatArray();array.SetName('Scalars')
    for value in values:array.InsertNextValue(value)
    dataset.GetPointData().SetScalars(array)

def grid(data, topology=None):
    result = vtkUnstructuredGrid()
    points = coordinates(data.Nodes)
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
    scalars(result,data.Nodes.Values)
    return result


class Scene:
    def __init__(self, renderer):
        self.renderer = renderer
        self.actors = []
        self.names = {}
        self.highlight_actor = None
        self.source = []
        self.volume_provider=None
        self.element_edges = False
        self.element_edge_actors = []
        self.edges_by_name={}
        self.drawn=[]

    def clear(self):
        self.renderer.RemoveAllViewProps()
        self.actors.clear()
        self.names.clear()
        self.highlight_actor = None
        self.element_edge_actors = []

    def update(self, source,commands=()):
        self.clear()
        self.source = list(source)
        self.drawn=[];self.edges_by_name={}
        from presentation import Presentation
        self.presentation=Presentation(self)
        for original in self.source:
            data = original.Data
            if not original.Visible or (data.Geometry.Nodes.Coor is None and data.Geometry.Nodes.FlatCoor is None):
                continue
            mapper = vtkDataSetMapper()
            mapper.SetInputData(grid(data.Geometry, original.SurfaceTopology))
            mapper.ScalarVisibilityOff()
            actor = vtkActor()
            actor.SetMapper(mapper)
            color = original.Color
            actor.GetProperty().SetColor(color.R / 255, color.G / 255, color.B / 255)
            actor.GetProperty().SetOpacity(color.A / 255)
            actor.GetProperty().SetLighting(data.Lighting)
            actor.GetProperty().SetAmbient(data.Ambient);actor.GetProperty().SetDiffuse(data.Diffuse)
            actor.GetProperty().SetBackfaceCulling(data.BackfaceCulling)
            if str(data.ActorRepresentation)=='Wire':actor.GetProperty().SetRepresentationToWireframe()
            if data.SmoothShaded:actor.GetProperty().SetInterpolationToGouraud()
            else:actor.GetProperty().SetInterpolationToFlat()
            actor.GetProperty().SetPointSize(max(4, data.NodeSize))
            actor.GetProperty().SetLineWidth(max(1, data.LineWidth))
            actor.SetPickable(data.Pickable)
            actor.GetProperty().SetEdgeVisibility(False)
            actor.GetProperty().SetEdgeColor(.15, .18, .22)
            self.renderer.AddActor(actor)
            self.actors.append(actor)
            self.drawn.append(original)
            self.names[actor.GetAddressAsString('')] = str(data.Name)
            # Element faces retain original quads/quadratic cells. Drawing their
            # edges avoids showing the triangulation used only for surface picking.
            edges = data.Geometry if self.element_edges else data.ModelEdgesToDraw or data.ModelEdges
            if edges is not None and edges.Nodes.Coor is not None:
                edge_mapper = vtkDataSetMapper()
                edge_mapper.SetInputData(grid(edges))
                edge_actor = vtkActor()
                edge_actor.SetMapper(edge_mapper)
                edge_actor.GetProperty().SetColor(.15, .18, .22)
                if self.element_edges:
                    edge_actor.GetProperty().SetRepresentationToWireframe()
                    edge_mapper.SetResolveCoincidentTopologyToPolygonOffset()
                    self.element_edge_actors.append(edge_actor)
                edge_actor.PickableOff()
                self.renderer.AddActor(edge_actor)
                self.edges_by_name.setdefault(str(data.Name),[]).append(edge_actor)

        self.presentation.build(commands)

    def set_frame(self,index):self.presentation.set_frame(index)

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

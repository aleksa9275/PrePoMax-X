"""Native VTK host glue for original Controller spatial-query contracts.

Surface cell topology is produced by the unchanged original C# conversion.
Locator/frustum operations mirror vtkControl.cs, without a render window.
"""
import json
import vtk

if vtk.vtkVersion.GetVTKVersion() != '9.5.2':
    raise RuntimeError('The explicit VTK 9.5.2 host profile is required')


def _ids(values):
    array = vtk.vtkUnsignedLongArray()
    for value in values:
        array.InsertNextValue(value & 0xffffffff)
    return array


def _grid(data, poly):
    points = vtk.vtkPoints()  # original vtkPoints default storage/rounding
    for p in data['coordinates']:
        points.InsertNextPoint(p)
    grid = vtk.vtkPolyData() if poly else vtk.vtkUnstructuredGrid()
    grid.SetPoints(points)
    grid.Allocate(len(data['cells']))
    for kind, nodes in zip(data['types'], data['cells']):
        indices = vtk.vtkIdList()
        for node in nodes:
            indices.InsertNextId(node)
        grid.InsertNextCell(kind, indices)
    if data['nodeIds'] is not None:
        grid.GetPointData().SetGlobalIds(_ids(data['nodeIds']))
    if data['cellIds'] is not None:
        grid.GetCellData().SetGlobalIds(_ids(data['cellIds']))
    return grid


def _signed(value):
    value = int(value)
    return value if value < 2147483648 else value - 4294967296


def _closest(grid, point):
    locator = vtk.vtkCellLocator()
    locator.SetDataSet(grid)
    locator.BuildLocator()  # VTK 9 eagerly builds the same locator used by the old lazy binding.
    cell_id = vtk.reference(-1)
    sub_id = vtk.reference(-1)
    distance2 = vtk.reference(-1.0)
    projected = [0., 0., 0.]
    locator.FindClosestPoint(point, projected, cell_id, sub_id, distance2)
    if int(cell_id) < 0 or float(distance2) < 0:
        return None
    cell = grid.GetCell(int(cell_id))
    points = grid.GetPointData().GetGlobalIds()
    cells = grid.GetCellData().GetGlobalIds()
    return {'element': _signed(cells.GetTuple1(int(cell_id))),
            'nodes': [_signed(points.GetTuple1(cell.GetPointId(i))) for i in range(cell.GetNumberOfPoints())],
            'coordinates': [list(cell.GetPoints().GetPoint(i)) for i in range(cell.GetNumberOfPoints())],
            'point': projected, 'distance2': float(distance2)}


def query(payload):
    request = json.loads(payload)
    operation = request['operation']
    if operation in ('CropPartWithCylinder', 'CropPartWithCube', 'SmoothPart'):
        # Original vtkMaxActor filter parameters and output choices are preserved.
        grid = _grid(request['surface'], True)
        parameters = request['parameters']
        if operation == 'SmoothPart':
            smoother = vtk.vtkWindowedSincPolyDataFilter()
            smoother.SetInputData(grid)
            smoother.NormalizeCoordinatesOn()
            smoother.SetNumberOfIterations(20)
            smoother.BoundarySmoothingOn()
            smoother.FeatureEdgeSmoothingOn()
            smoother.SetFeatureAngle(360.0)
            smoother.SetPassBand(0.1)
            smoother.NonManifoldSmoothingOn()
            smoother.Update()
            # Original writes smoother output, not the unused decimator output.
            output = smoother.GetOutput()
        else:
            if operation == 'CropPartWithCylinder':
                transform = vtk.vtkTransform()
                transform.Identity()
                transform.RotateX(90)
                shape = vtk.vtkCylinder()
                shape.SetTransform(transform)
                shape.SetRadius(parameters[1])
            else:
                x, y, z, a = parameters[1:5]
                shape = vtk.vtkBox()
                shape.SetBounds(x-a/2, x+a/2, y-a/2, y+a/2, z-a/2, z+a/2)
            clipper = vtk.vtkClipPolyData()
            clipper.SetInputData(grid)
            clipper.SetClipFunction(shape)
            clipper.GenerateClippedOutputOn()
            clipper.GenerateClipScalarsOn()
            clipper.SetValue(0)
            clipper.Update()
            decimate = vtk.vtkDecimatePro()
            decimate.SetInputData(clipper.GetClippedOutput())
            decimate.SetTargetReduction(0.05)
            decimate.PreserveTopologyOn()
            decimate.Update()
            output = decimate.GetOutput()
        writer = vtk.vtkSTLWriter()
        writer.SetFileName(parameters[-1])
        writer.SetInputData(output)
        if writer.Write() != 1:
            raise OSError('Native surface export failed')
        return json.dumps(True)
    actors = request['actors']
    names = request.get('names')
    if operation == 'pick':
        result = None
        for actor in actors:
            if (names is not None and actor['name'] not in names) or (names is None and not actor['visible']):
                continue
            hit = _closest(_grid(actor['surface'], True), request['point'])
            if hit is not None and (result is None or hit['distance2'] < result['distance2']):
                result = hit
            if result is not None and result['distance2'] == 0:
                break
        return json.dumps(result)
    if operation == 'closest':
        results = [None for _ in names]
        for actor in actors:
            if actor['name'] not in names:
                continue
            index = names.index(actor['name'])
            hit = _closest(_grid(actor['surface'], True), request['point'])
            if hit is not None and (results[index] is None or hit['distance2'] < results[index]['distance2']):
                results[index] = hit
        return json.dumps(results)
    if operation == 'frustum':
        normals = vtk.vtkDoubleArray()
        normals.SetNumberOfComponents(3)
        points = vtk.vtkPoints()
        for plane in request['planes']:
            points.InsertNextPoint(plane[:3])
            normals.InsertNextTuple3(*plane[3:])
        planes = vtk.vtkPlanes()
        planes.SetPoints(points)
        planes.SetNormals(normals)
        point_ids, cell_ids = {}, {}
        for actor in actors:
            if actor.get('volume') is None:
                continue
            if (names is not None and actor['name'] not in names) or (names is None and not actor['visible']):
                continue
            grid = _grid(actor['volume'], False)
            extractor = vtk.vtkExtractSelectedFrustum()
            extractor.SetFieldType(1)  # original vtkSelectionField.POINT
            extractor.SetContainingCells(0)
            extractor.SetInputData(grid)
            extractor.SetFrustum(planes)
            extractor.Update()
            values = extractor.GetOutput().GetPointData().GetGlobalIds()
            if values is not None:
                point_ids.update((_signed(values.GetTuple1(i)), None) for i in range(values.GetNumberOfTuples()))
            extractor.SetFieldType(0)  # original vtkSelectionField.CELL
            extractor.Update()
            values = extractor.GetOutput().GetCellData().GetGlobalIds()
            if values is not None:
                cell_ids.update((_signed(values.GetTuple1(i)), None) for i in range(values.GetNumberOfTuples()))
        return json.dumps({'points': list(point_ids), 'cells': list(cell_ids)})
    raise ValueError('Unknown spatial operation')

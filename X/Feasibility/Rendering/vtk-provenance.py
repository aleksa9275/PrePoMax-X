#!/usr/bin/env python3
"""Mixed-order FEM provenance and bounded native render lifecycle experiment."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import platform
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--module-dir",type=Path,required=True);parser.add_argument("--output-dir",type=Path,required=True);args=parser.parse_args()
    sys.path.insert(0,str(args.module_dir));import vtk
    args.output_dir.mkdir(parents=True,exist_ok=True)
    report={"success":False,"recordedAtUtc":datetime.now(timezone.utc).isoformat(),"vtk":vtk.vtkVersion.GetVTKVersion(),"os":platform.system(),"architecture":platform.machine(),"toolSha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"checks":[]}
    windows=[]
    def check(name,condition):
        report["checks"].append({"name":name,"passed":bool(condition)})
        if not condition:raise AssertionError(name)
    try:
        check("pinned native Mac ARM64 runtime",report["vtk"]=="9.5.2" and report["os"]=="Darwin" and report["architecture"]=="arm64")
        coordinates=[(-2,-.6,0),(-.5,-.6,0),(-.5,.6,0),(-2,.6,0),(.5,-.6,0),(2,-.6,0),(2,.6,0),(.5,.6,0),(1.25,-.6,0),(2,0,0),(1.25,.6,0),(.5,0,0),(-1,1,0),(0,1,0),(-1,2,0),(-1,1,1)]
        node_ids=[61+17*i for i in range(len(coordinates))];element_ids=[7001,9007,11003]
        points=vtk.vtkPoints();points.SetDataTypeToDouble()
        for point in coordinates:points.InsertNextPoint(point)
        grid=vtk.vtkUnstructuredGrid();grid.SetPoints(points)
        for kind,ids in [(vtk.VTK_QUAD,range(4)),(vtk.VTK_QUADRATIC_QUAD,range(4,12)),(vtk.VTK_TETRA,range(12,16))]:
            indices=vtk.vtkIdList()
            for index in ids:indices.InsertNextId(index)
            grid.InsertNextCell(kind,indices)
        provenance=vtk.vtkIdTypeArray();provenance.SetName("SourceFEMElementId")
        for value in element_ids:provenance.InsertNextValue(value)
        grid.GetCellData().AddArray(provenance)
        def parent_ids(data):
            values=data.GetCellData().GetArray("SourceFEMElementId")
            if values is None:raise ValueError("Missing source FEM provenance")
            result=[int(values.GetTuple1(i)) for i in range(data.GetNumberOfCells())]
            if any(value not in element_ids for value in result):raise ValueError("Unknown FEM parent ID")
            return result
        check("mixed linear quad/quadratic quad/tetra types",[grid.GetCellType(i) for i in range(3)]==[vtk.VTK_QUAD,vtk.VTK_QUADRATIC_QUAD,vtk.VTK_TETRA])
        surface=vtk.vtkDataSetSurfaceFilter();surface.SetInputData(grid);surface.SetNonlinearSubdivisionLevel(2);surface.Update()
        surface_ids=parent_ids(surface.GetOutput())
        check("surface subdivision maps all generated faces to original elements",set(surface_ids)==set(element_ids) and surface_ids.count(9007)>1 and surface_ids.count(11003)==4)
        plane=vtk.vtkPlane();plane.SetOrigin(1.4,0,0);plane.SetNormal(1,0,0)
        clipping=vtk.vtkClipDataSet();clipping.SetInputData(grid);clipping.SetClipFunction(plane);clipping.Update();cut=clipping.GetOutput()
        check("clip children retain explicit parent element ID",cut.GetNumberOfCells()>0 and set(parent_ids(cut))=={9007})
        original=[];generated=[]
        # Coordinate lookup is valid only for this fixture's unique, undeformed points.
        # A generated vertex is deliberately not assigned an interpolated FEM node ID.
        for i in range(cut.GetNumberOfPoints()):
            p=cut.GetPoint(i);matches=[j for j,q in enumerate(coordinates) if sum((p[k]-q[k])**2 for k in range(3))<1e-20]
            if len(matches)==1:original.append(node_ids[matches[0]])
            else:generated.append(i)
        check("new clipping vertices remain distinct from original FEM nodes",len(generated)>0 and len(original)>0)
        invalid=vtk.vtkUnstructuredGrid();invalid.DeepCopy(cut);invalid.GetCellData().GetArray("SourceFEMElementId").SetTuple1(0,999999)
        rejected=False
        try:parent_ids(invalid)
        except ValueError:rejected=True
        check("unknown parent ID negative control rejected",rejected)
        displacement=vtk.vtkDoubleArray();displacement.SetName("Displacement");displacement.SetNumberOfComponents(3)
        for x,y,z in coordinates:displacement.InsertNextTuple3(0,0,.1*x)
        grid.GetPointData().SetVectors(displacement);warp=vtk.vtkWarpVector();warp.SetInputData(grid);warp.SetScaleFactor(2);warp.Update()
        check("mixed-order deformation preserves exact element provenance",parent_ids(warp.GetOutput())==element_ids)
        check("deformation applies to all corner and midside nodes",all(abs(warp.GetOutput().GetPoint(i)[2]-(p[2]+.2*p[0]))<1e-12 for i,p in enumerate(coordinates)))
        picks=[]
        for iteration in range(20):
            mapper=vtk.vtkDataSetMapper();mapper.SetInputData(grid);mapper.ScalarVisibilityOff()
            actor=vtk.vtkActor();actor.SetMapper(mapper);actor.GetProperty().EdgeVisibilityOn()
            renderer=vtk.vtkRenderer();renderer.AddActor(actor);renderer.SetBackground(.04,.06,.1)
            camera=renderer.GetActiveCamera();camera.SetPosition(0,0,8);camera.SetFocalPoint(0,0,0);camera.ParallelProjectionOn();camera.SetParallelScale(2.5)
            window=vtk.vtkRenderWindow();windows.append(window);window.SetOffScreenRendering(1);window.SetSize(640,480);window.SetMultiSamples(0);window.AddRenderer(renderer);window.Render()
            renderer.SetWorldPoint(1.6,.1,0,1);renderer.WorldToDisplay();x,y,_=renderer.GetDisplayPoint()
            picker=vtk.vtkCellPicker();picker.SetTolerance(.001);found=picker.Pick(x,y,0,renderer)
            actual=parent_ids(picker.GetDataSet())[picker.GetCellId()] if found else None;picks.append(actual)
            if iteration==0:
                report["renderWindowClass"]=window.GetClassName();report["renderCapabilities"]=window.ReportCapabilities()
                image=vtk.vtkWindowToImageFilter();image.SetInput(window);image.ReadFrontBufferOff();image.Update()
                writer=vtk.vtkPNGWriter();writer.SetFileName(str(args.output_dir/"mixed-elements.png"));writer.SetInputConnection(image.GetOutputPort());writer.Write()
            renderer.RemoveActor(actor);window.Finalize();windows.remove(window)
        check("20 create/render/pick/remove/finalize cycles return the quadratic element ID",picks==[9007]*20)
        report["observations"]={"surfaceFaces":len(surface_ids),"clippedCells":cut.GetNumberOfCells(),"originalNodeIdsOnCut":sorted(set(original)),"generatedCutVertexCount":len(generated),"lifecycleCycles":20,"cellPicks":picks}
        report["limits"]=["Synthetic candidate only; production vtkControl unchanged","Cell array carries parent element identity; generated points are not FEM nodes","Coordinate lookup only justified for this fixture; production needs topology/parametric provenance","Programmatic picks, no genuine pointer/DPI/framework embedding","Bounded lifecycle execution, not proof of no memory/resource leaks","No native Windows/Linux rendering acceptance or frontend decision"]
        report["success"]=True
    except Exception as error:report["error"]=str(error)
    finally:
        for window in windows:window.Finalize()
        (args.output_dir/"provenance.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"success":report["success"],"checks":len(report["checks"]),"error":report.get("error")}))
    return 0 if report["success"] else 1


if __name__=="__main__":raise SystemExit(main())

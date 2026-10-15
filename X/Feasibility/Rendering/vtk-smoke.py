#!/usr/bin/env python3
"""Synthetic native VTK contracts. This does not execute original vtkControl."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys
import traceback


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module-dir",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--install-report",type=Path,required=True)
    args=parser.parse_args()
    sys.path.insert(0,str(args.module_dir))
    args.output_dir.mkdir(parents=True,exist_ok=True)
    report={"schemaVersion":1,"success":False,"recordedAtUtc":datetime.now(timezone.utc).isoformat(),
            "host":{"os":platform.system(),"architecture":platform.machine(),"python":sys.version},
            "checks":[],"observations":{},"scriptSha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    def save(): (args.output_dir/"macos-arm64.json").write_text(json.dumps(report,indent=2)+"\n")
    def check(name, condition):
        report["checks"].append({"name":name,"status":"passed" if condition else "failed"})
        save()
        if not condition: raise AssertionError(name)
    def global_ids(dataset, association):
        attributes=dataset.GetPointData() if association=="point" else dataset.GetCellData()
        ids=attributes.GetGlobalIds()
        return None if ids is None else [int(ids.GetValue(i)) for i in range(ids.GetNumberOfTuples())]
    window=None
    try:
        import vtk
        import numpy
        from PIL import Image
        report["runtime"]={"vtk":vtk.vtkVersion.GetVTKVersion(),"numpy":numpy.__version__}
        install=json.loads(args.install_report.read_text())
        report["wheel"]=[{"url":p["download_info"]["url"],"archive":p["download_info"]["archive_info"],
                          "name":p["metadata"]["name"],"version":p["metadata"]["version"]} for p in install["install"]]
        check("pinned VTK 9.5.2 native ARM64 host",report["runtime"]["vtk"]=="9.5.2" and platform.machine()=="arm64")
        core=Path(vtk.vtkCommonCore.__file__) if hasattr(vtk,"vtkCommonCore") else args.module_dir/"vtkmodules/vtkCommonCore.cpython-312-darwin.so"
        if core.exists(): report["nativeModule"]={"path":core.name,"sha256":hashlib.sha256(core.read_bytes()).hexdigest()}
        points=vtk.vtkPoints()
        coordinates=[(-1,-1,0),(0,-1,0),(1,-1,0),(-1,1,0),(0,1,0),(1,1,0)]
        for p in coordinates: points.InsertNextPoint(*p)
        grid=vtk.vtkUnstructuredGrid(); grid.SetPoints(points)
        for ids in [(0,1,4,3),(1,2,5,4)]:
            quad=vtk.vtkQuad()
            for k,i in enumerate(ids): quad.GetPointIds().SetId(k,i)
            grid.InsertNextCell(quad.GetCellType(),quad.GetPointIds())
        point_ids=[61,17,105,200,4,99]; cell_ids=[7001,9007]
        for attributes,values,name in [(grid.GetPointData(),point_ids,"FEMNodeId"),(grid.GetCellData(),cell_ids,"FEMElementId")]:
            ids=vtk.vtkUnsignedLongArray(); ids.SetName(name)
            for value in values: ids.InsertNextValue(value)
            attributes.SetGlobalIds(ids)
        check("nonsequential FEM global IDs retained",global_ids(grid,"point")==point_ids and global_ids(grid,"cell")==cell_ids)
        selection=vtk.vtkSelection(); node=vtk.vtkSelectionNode(); node.SetFieldType(vtk.vtkSelectionNode.CELL); node.SetContentType(vtk.vtkSelectionNode.GLOBALIDS)
        selected_ids=vtk.vtkUnsignedLongArray(); selected_ids.InsertNextValue(9007); node.SetSelectionList(selected_ids); selection.AddNode(node)
        extraction=vtk.vtkExtractSelection(); extraction.SetInputData(0,grid); extraction.SetInputData(1,selection); extraction.Update()
        subset=extraction.GetOutput()
        check("global-ID cell extraction maps to original FEM element",global_ids(subset,"cell")==[9007])
        check("extracted cell retains its four FEM node IDs",set(global_ids(subset,"point"))=={17,105,4,99})
        displacement=vtk.vtkDoubleArray(); displacement.SetNumberOfComponents(3); displacement.SetName("Displacement")
        for _ in coordinates: displacement.InsertNextTuple3(0,0.25,0)
        grid.GetPointData().SetVectors(displacement)
        warp=vtk.vtkWarpVector(); warp.SetInputData(grid); warp.SetScaleFactor(2); warp.Update()
        deformed=warp.GetOutput()
        check("deformation applies independently specified scale",deformed.GetBounds()==(-1,1,-0.5,1.5,0,0))
        check("deformation preserves FEM global IDs",global_ids(deformed,"point")==point_ids and global_ids(deformed,"cell")==cell_ids)
        plane=vtk.vtkPlane(); plane.SetOrigin(0,0,0); plane.SetNormal(1,0,0)
        clipping=vtk.vtkClipDataSet(); clipping.SetInputData(grid); clipping.SetClipFunction(plane); clipping.Update()
        clipped=clipping.GetOutput(); bounds=clipped.GetBounds()
        check("clipping keeps the specified half-plane",clipped.GetNumberOfCells()>0 and abs(bounds[0])<1e-12 and abs(bounds[1]-1)<1e-12)
        report["observations"]["clippedGlobalIds"]={"points":global_ids(clipped,"point"),"cells":global_ids(clipped,"cell"),
            "note":"Cut vertices need provenance mapping; filter ID presence alone is not a FEM selection guarantee"}
        save() # Retain non-rendering results even if the native graphics process terminates.
        mapper=vtk.vtkDataSetMapper(); mapper.SetInputData(grid); mapper.ScalarVisibilityOff()
        actor=vtk.vtkActor(); actor.SetMapper(mapper); actor.GetProperty().SetColor(0.18,0.68,0.90)
        actor.GetProperty().EdgeVisibilityOn(); actor.GetProperty().SetEdgeColor(0.03,0.10,0.16); actor.GetProperty().LightingOff()
        renderer=vtk.vtkRenderer(); renderer.SetBackground(0.05,0.07,0.10); renderer.AddActor(actor)
        camera=renderer.GetActiveCamera(); camera.SetPosition(0,0,5); camera.SetFocalPoint(0,0,0); camera.SetViewUp(0,1,0); camera.ParallelProjectionOn(); camera.SetParallelScale(1.6)
        window=vtk.vtkRenderWindow(); window.SetOffScreenRendering(1); window.SetSize(640,480); window.SetMultiSamples(0); window.AddRenderer(renderer)
        window.Render()
        report["renderWindowClass"]=window.GetClassName(); report["renderCapabilities"]=window.ReportCapabilities()
        def project(world):
            renderer.SetWorldPoint(*world,1); renderer.WorldToDisplay(); return renderer.GetDisplayPoint()
        picked=[]
        for world,expected in [((-0.5,0,0),7001),((0.5,0,0),9007)]:
            x,y,_=project(world); picker=vtk.vtkCellPicker(); picker.SetTolerance(0.001)
            found=picker.Pick(x,y,0,renderer); local=picker.GetCellId()
            actual=None if not found else global_ids(picker.GetDataSet(),"cell")[local]
            check("renderer cell pick returns FEM ID "+str(expected),actual==expected); picked.append(actual)
        x,y,_=project(coordinates[0]); picker=vtk.vtkPointPicker(); picker.SetTolerance(0.02)
        found=picker.Pick(x,y,0,renderer)
        actual=None if not found else global_ids(picker.GetDataSet(),"point")[picker.GetPointId()]
        check("renderer point pick returns FEM node 61",actual==61)
        # Rectangle encloses just the leftmost two original nodes.
        x0,y0,_=project((-1.1,-1.1,0)); x1,y1,_=project((-0.9,1.1,0))
        area_picker=vtk.vtkAreaPicker(); area_picker.AreaPick(x0,y0,x1,y1,renderer)
        frustum=vtk.vtkExtractSelectedFrustum(); frustum.SetInputData(grid); frustum.SetFrustum(area_picker.GetFrustum()); frustum.SetFieldType(vtk.vtkSelectionNode.POINT); frustum.SetContainingCells(0); frustum.Update()
        rectangle_ids=global_ids(frustum.GetOutput(),"point")
        check("rectangle frustum returns exact FEM node IDs",rectangle_ids is not None and set(rectangle_ids)=={61,200})
        def snapshot(name):
            capture=vtk.vtkWindowToImageFilter(); capture.SetInput(window); capture.ReadFrontBufferOff(); capture.Update()
            writer=vtk.vtkPNGWriter(); writer.SetFileName(str(args.output_dir/name)); writer.SetInputConnection(capture.GetOutputPort()); writer.Write()
            path=args.output_dir/name
            with Image.open(path) as image: pixels=numpy.asarray(image.convert("RGB")).copy()
            report.setdefault("images",[]).append({"file":name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"width":pixels.shape[1],"height":pixels.shape[0]})
            return pixels
        original=snapshot("synthetic-original.png")
        check("native render contains mesh pixels",int(numpy.count_nonzero(original[:,:,2]>100))>50000)
        mapper.SetInputData(deformed); window.Render(); changed=snapshot("synthetic-deformed.png")
        check("deformation changes the rendered image",int(numpy.count_nonzero(numpy.any(changed!=original,axis=2)))>10000)
        mapper.SetInputData(grid)
        renderer.RemoveActor(actor); window.Render(); blank=snapshot("synthetic-released.png")
        check("actor removal clears mesh pixels",int(numpy.count_nonzero(blank[:,:,2]>100))==0)
        report["observations"].update(cellPicks=picked, pointPick=actual, rectangleNodeIds=sorted(rectangle_ids))
        report["limits"]=["Synthetic modern Python VTK candidate, not execution of original vtkControl", "Programmatic renderer picks, not genuine pointer/UI/DPI interaction", "No Windows/rendering parity or frontend decision", "Clipping can create new geometry needing explicit FEM ID provenance"]
        report["passed"]=len(report["checks"]); report["success"]=True
    except Exception as error:
        report["error"]=str(error); report["traceback"]=traceback.format_exc()
    finally:
        if window is not None: window.Finalize()
        save()
    print(json.dumps({"success":report["success"],"passed":report.get("passed"),"runtime":report.get("runtime"),"error":report.get("error")}))
    return 0 if report["success"] else 1


if __name__=="__main__": raise SystemExit(main())

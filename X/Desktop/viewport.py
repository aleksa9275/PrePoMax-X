#!/usr/bin/env python3
"""Native Qt/VTK viewport candidate. Engineering decoding belongs to C# hosts."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from PyQt6 import QtCore, QtGui, QtWidgets
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkDoubleArray, vtkIdTypeArray, vtkPoints, vtkVersion
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from vtkmodules.vtkRenderingAnnotation import vtkScalarBarActor
from vtkmodules.vtkRenderingCore import vtkActor, vtkCellPicker, vtkDataSetMapper, vtkRenderer, vtkRenderWindow, vtkWindowToImageFilter
import vtkmodules.vtkInteractionStyle
import vtkmodules.vtkRenderingOpenGL2

ROOT = Path(__file__).resolve().parents[2]


class FrameBridge(QtWidgets.QWidget):
    """Candidate transport: native VTK GPU frame -> Qt image, with one frame copy.

    Avoids the observed Cocoa QVTKRWI repaint loop/black QOpenGLWidget. This is
    deliberately not a final high-performance VTK widget binding.
    """
    clicked = QtCore.pyqtSignal(float, float)

    def __init__(self, parent):
        super().__init__(parent)
        self.window = vtkRenderWindow()
        self.window.SetOffScreenRendering(1)
        self.window.SetMultiSamples(0)
        self.capture = vtkWindowToImageFilter()
        self.capture.SetInput(self.window)
        self.capture.SetInputBufferTypeToRGB()
        self.capture.ReadFrontBufferOff()
        self.frame = None
        self.pressed = None

    def GetRenderWindow(self):
        return self.window

    def render(self):
        self.window.SetSize(max(1, self.width()), max(1, self.height()))
        self.window.Render()
        self.capture.Modified()
        self.capture.Update()
        output = self.capture.GetOutput()
        width, height, _ = output.GetDimensions()
        pixels = vtk_to_numpy(output.GetPointData().GetScalars()).reshape(height, width, 3)
        pixels = pixels[::-1].copy()
        self.frame = QtGui.QImage(pixels.data, width, height, width * 3, QtGui.QImage.Format.Format_RGB888).copy()
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        if self.frame:
            painter.drawImage(self.rect(), self.frame)
        else:
            painter.fillRect(self.rect(), QtGui.QColor(30, 38, 48))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.frame:
            self.render()

    def mousePressEvent(self, event):
        self.pressed = event.position()

    def mouseReleaseEvent(self, event):
        position = event.position()
        if self.pressed and (position - self.pressed).manhattanLength() > 4:
            camera = self.window.GetRenderers().GetFirstRenderer().GetActiveCamera()
            delta = position - self.pressed
            camera.Azimuth(-delta.x() * 0.4)
            camera.Elevation(delta.y() * 0.4)
            camera.OrthogonalizeViewUp()
            self.render()
        else:
            self.clicked.emit(position.x(), self.height() - 1 - position.y())
        self.pressed = None

    def Finalize(self):
        self.window.Finalize()


def decode(path):
    """Use the original reader assemblies in separate processes; no second parser."""
    packaged = getattr(sys, "frozen", False)
    if path.suffix.lower() == ".inp":
        command = ([str(Path(sys._MEIPASS) / "hosts/mesh/PrePoMaxX.MeshScene")] if packaged else
            ["dotnet", str(ROOT / "X/Desktop/MeshScene/bin/Release/net10.0/PrePoMaxX.MeshScene.dll")]) + [str(path)]
    elif path.suffix.lower() == ".frd":
        command = ([str(Path(sys._MEIPASS) / "hosts/results/PrePoMaxX.InspectResults")] if packaged else
            ["dotnet", str(ROOT / "X/Results/Inspect/bin/Release/net10.0/PrePoMaxX.InspectResults.dll")]) + ["inspect-frd", str(path)]
    else:
        raise ValueError("This bounded viewport opens INP meshes or completed static C3D8 FRD snapshots.")
    result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise ValueError(result.stderr.strip() or result.stdout.strip() or "Original reader failed")
    scene = json.loads(result.stdout)
    if scene.get("success") is not True:
        raise ValueError("Original reader did not accept input")
    return scene


class Viewport(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PrePoMax-X — native viewport candidate")
        self.resize(1000, 720)
        self.scene = None
        self.selection = None
        toolbar = self.addToolBar("View")
        toolbar.addAction("Open INP / FRD", self.open_dialog)
        toolbar.addAction("Fit", self.fit)
        self.fields = QtWidgets.QComboBox()
        self.fields.setMinimumWidth(330)
        self.fields.currentIndexChanged.connect(self.set_field)
        toolbar.addWidget(self.fields)
        self.vtk = FrameBridge(self)
        self.setCentralWidget(self.vtk)
        self.renderer = vtkRenderer()
        self.renderer.SetBackground(0.12, 0.15, 0.19)
        self.vtk.GetRenderWindow().AddRenderer(self.renderer)
        self.mapper = vtkDataSetMapper()
        self.mapper.SetInputData(vtkUnstructuredGrid())
        self.actor = vtkActor()
        self.actor.SetMapper(self.mapper)
        self.actor.GetProperty().SetEdgeVisibility(True)
        self.actor.GetProperty().SetEdgeColor(0.12, 0.12, 0.12)
        self.actor.GetProperty().SetColor(0.75, 0.81, 0.88)
        self.renderer.AddActor(self.actor)
        self.legend = vtkScalarBarActor()
        self.legend.SetLookupTable(self.mapper.GetLookupTable())
        self.legend.SetNumberOfLabels(5)
        self.legend.SetVisibility(False)
        self.renderer.AddViewProp(self.legend)
        self.picker = vtkCellPicker()
        self.picker.SetTolerance(0.005)
        self.picker.PickFromListOn()
        self.picker.AddPickList(self.actor)
        self.vtk.clicked.connect(self.pick)
        self.statusBar().showMessage("Original C# readers · native VTK · research candidate")

    def open_dialog(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open mesh/results", "", "Mesh/results (*.inp *.frd)")
        if path:
            try:
                self.load(Path(path))
            except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
                QtWidgets.QMessageBox.critical(self, "Cannot open file", str(error))

    def load(self, path):
        scene = decode(path)
        points = vtkPoints()
        points.SetDataTypeToDouble()
        nodes = scene["nodes"]
        indices = {n["id"]: i for i, n in enumerate(nodes)}
        if len(indices) != len(nodes) or not nodes:
            raise ValueError("Invalid node identity data")
        grid = vtkUnstructuredGrid()
        node_ids = vtkIdTypeArray()
        node_ids.SetName("OriginalNodeId")
        for node in nodes:
            points.InsertNextPoint(node["x"], node["y"], node["z"])
            node_ids.InsertNextValue(node["id"])
        grid.SetPoints(points)
        grid.GetPointData().SetGlobalIds(node_ids)
        cell_ids = vtkIdTypeArray()
        cell_ids.SetName("OriginalElementId")
        for element in scene["elements"]:
            cell_type = element.get("vtkCellType")
            if cell_type is None:
                if element["type"] != "LinearHexaElement":
                    raise ValueError("FRD snapshot supports C3D8 only")
                cell_type = 12
            mapped = [indices[n] for n in element["nodeIds"]]
            grid.InsertNextCell(cell_type, len(mapped), mapped)
            cell_ids.InsertNextValue(element["id"])
        grid.GetCellData().SetGlobalIds(cell_ids)
        self.fields.blockSignals(True)
        self.fields.clear()
        self.fields.addItem("Mesh (undeformed)", None)
        if "fields" in scene:
            value_order = {n: i for i, n in enumerate(scene["nodeIdsInValueOrder"])}
            for field_index, field in enumerate(scene["fields"]):
                for component, values in field["components"].items():
                    if len(values) != len(value_order):
                        raise ValueError("Field length does not match original node value order")
                    name = f"{field_index}:{component}"
                    array = vtkDoubleArray()
                    array.SetName(name)
                    for node in nodes:
                        array.InsertNextValue(values[value_order[node["id"]]])
                    grid.GetPointData().AddArray(array)
                    label = f'{field["name"]} / {component} · step {field["stepId"]}:{field["incrementId"]}'
                    self.fields.addItem(label, name)
        self.fields.blockSignals(False)
        self.scene, self.grid = scene, grid
        self.selection = None
        self.mapper.SetInputData(grid)
        self.setWindowTitle(f"PrePoMax-X — {path.name} — native viewport candidate")
        self.renderer.GetActiveCamera().SetPosition(3, 2, 4)
        self.renderer.GetActiveCamera().SetFocalPoint(0.5, 0.5, 0.5)
        self.set_field(0)
        self.fit()
        self.statusBar().showMessage(f'{len(nodes)} nodes · {len(scene["elements"])} elements · values as stored · undeformed')

    def set_field(self, index):
        if self.scene is None:
            return
        name = self.fields.itemData(index)
        self.mapper.SetScalarVisibility(name is not None)
        self.legend.SetVisibility(name is not None)
        if name is not None:
            array = self.grid.GetPointData().GetArray(name)
            self.mapper.SetScalarModeToUsePointFieldData()
            self.mapper.SelectColorArray(name)
            self.mapper.SetScalarRange(array.GetRange())
            self.legend.SetTitle(self.fields.itemText(index).split(" · ")[0])
        if self.isVisible():
            self.vtk.render()

    def fit(self):
        self.renderer.ResetCamera()
        if self.isVisible():
            self.vtk.render()

    def pick(self, x, y):
        if self.scene is None or not self.picker.Pick(x, y, 0, self.renderer):
            self.selection = None
            self.statusBar().showMessage("No mesh selection")
            return None
        cell, point = self.picker.GetCellId(), self.picker.GetPointId()
        if cell < 0 or point < 0:
            return None
        self.selection = {
            "elementId": int(self.grid.GetCellData().GetGlobalIds().GetValue(cell)),
            "nearestVertexNodeId": int(self.grid.GetPointData().GetGlobalIds().GetValue(point)),
            "nodeCoordinates": self.grid.GetPoint(point),
        }
        name = self.fields.currentData()
        if name is not None:
            self.selection["nodalValue"] = self.grid.GetPointData().GetArray(name).GetValue(point)
        self.statusBar().showMessage(json.dumps(self.selection))
        return self.selection

    def closeEvent(self, event):
        self.vtk.Finalize()
        super().closeEvent(event)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, nargs="?")
    parser.add_argument("--self-test", type=Path, help="Write bounded native render/ID/field checks and exit")
    parser.add_argument("--screenshot", type=Path)
    args = parser.parse_args()
    app = QtWidgets.QApplication([sys.argv[0]])
    window = Viewport()
    if args.input:
        window.load(args.input.resolve())
    window.show()
    window.vtk.render()
    result = {"success": False}

    def verify():
        try:
            checks = []
            def check(name, value):
                checks.append({"name": name, "passed": bool(value)})
            check("native render window", window.vtk.GetRenderWindow().GetClassName() == "vtkCocoaRenderWindow")
            check("original IDs retained", window.grid.GetNumberOfPoints() == 8 and window.grid.GetNumberOfCells() == 1)
            if window.fields.count() > 1:
                window.fields.setCurrentIndex(1)
                check("field scalar mapping", window.mapper.GetScalarVisibility() == 1 and window.legend.GetVisibility() == 1)
            window.renderer.SetWorldPoint(0.5, 0.5, 1, 1)
            window.renderer.WorldToDisplay()
            x, y, _ = window.renderer.GetDisplayPoint()
            selection = window.pick(x, y)
            check("VTK hit resolves original element ID", selection and selection["elementId"] == window.scene["elements"][0]["id"])
            check("nearest vertex resolves original node ID", selection and selection["nearestVertexNodeId"] in {n["id"] for n in window.scene["nodes"]})
            if selection:
                node = next(n for n in window.scene["nodes"] if n["id"] == selection["nearestVertexNodeId"])
                check("selected coordinates preserved", list(selection["nodeCoordinates"]) == [node["x"], node["y"], node["z"]])
            if selection and "fields" in window.scene:
                field = window.scene["fields"][0]
                component = next(iter(field["components"]))
                index = window.scene["nodeIdsInValueOrder"].index(selection["nearestVertexNodeId"])
                check("selected nodal value uses original value order", selection["nodalValue"] == field["components"][component][index])
            window.resize(1120, 760)
            app.processEvents()
            window.vtk.render()
            check("resize renders", window.vtk.GetRenderWindow().GetSize()[0] > 0)
            frame = window.vtk.frame
            colors = {frame.pixelColor(x, y).rgb() for x in range(0, frame.width(), 20) for y in range(0, frame.height(), 20)}
            check("displayed frame has mesh/legend pixels", len(colors) > (10 if "fields" in window.scene else 3))
            if args.screenshot:
                args.screenshot.parent.mkdir(parents=True, exist_ok=True)
                check("window capture", window.grab().save(str(args.screenshot)))
            tool_sha = (json.loads((Path(sys._MEIPASS) / "source-identity.json").read_text())["viewportSha256"]
                if getattr(sys, "frozen", False) else hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
            result.update(success=all(c["passed"] for c in checks), checks=checks,
                selection=selection, vtkVersion=vtkVersion.GetVTKVersion(), qtVersion=QtCore.QT_VERSION_STR,
                sourceSha256=window.scene["SourceSha256"], renderer=window.vtk.GetRenderWindow().GetClassName(),
                toolSha256=tool_sha,
                transport="Native VTK offscreen GPU frame copied into Qt; not final widget/performance acceptance",
                scope="Native Mac render and programmatic picking; human pointer, DPI, other platforms and release packaging remain")
        except Exception as error:
            result["error"] = str(error)
        args.self_test.parent.mkdir(parents=True, exist_ok=True)
        args.self_test.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result))
        window.close()
        app.exit(0 if result["success"] else 1)

    if args.self_test:
        QtCore.QTimer.singleShot(1200, verify)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

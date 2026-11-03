#!/usr/bin/env python3
"""Native Qt/VTK viewport candidate. Engineering decoding belongs to C# hosts."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import subprocess
import sys

from PyQt6 import QtCore, QtGui, QtWidgets
from jobs import DesktopJob, examples
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
    def __init__(self, transport="frame-bridge"):
        super().__init__()
        self.setWindowTitle("PrePoMax-X — native viewport candidate")
        self.resize(1000, 720)
        self.scene = None
        self.selection = None
        self.current_path = None
        self.closing_after_job = False
        self.job = DesktopJob(self)
        self.job.changed.connect(self.job_state)
        self.job.completed.connect(self.job_completed)
        self.jobs_root = Path(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.StandardLocation.AppLocalDataLocation)) / 'jobs'
        toolbar = self.addToolBar("View")
        toolbar.addAction("Open INP / FRD", self.open_dialog)
        toolbar.addAction("Fit", self.fit)
        self.fields = QtWidgets.QComboBox()
        self.fields.setMinimumWidth(330)
        self.fields.currentIndexChanged.connect(self.set_field)
        toolbar.addWidget(self.fields)
        self.transport = transport
        if transport == "native-cocoa":
            from native_cocoa import NativeCocoaView
            self.vtk = NativeCocoaView(self)
        else:
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
        jobbar = self.addToolBar("Static analysis")
        self.run_action = jobbar.addAction("Run static…", self.run_dialog)
        self.example_action = jobbar.addAction("Solve example", self.run_example)
        self.cancel_action = jobbar.addAction("Cancel", self.job.cancel)
        self.cancel_action.setEnabled(False)
        jobbar.addAction("Job files", self.open_job_directory)
        self.job_label = QtWidgets.QLabel("Ready · static solid preview")
        jobbar.addWidget(self.job_label)
        dock = QtWidgets.QDockWidget("Job output", self)
        self.job_output = QtWidgets.QPlainTextEdit()
        self.job_output.setReadOnly(True)
        self.job_output.setMaximumBlockCount(3000)
        dock.setWidget(self.job_output)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, dock)
        self.job_poll = QtCore.QTimer(self)
        self.job_poll.timeout.connect(self.refresh_job_output)
        self.job_poll.start(500)

    def run_dialog(self):
        mesh = str(self.current_path) if self.current_path and self.current_path.suffix.lower() == '.inp' else ''
        if not mesh:
            mesh, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Static analysis mesh", "", "INP mesh (*.inp)")
        if not mesh:
            return
        analysis, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Static analysis definitions", str(examples()), "Analysis definitions (*.json)")
        if analysis:
            self.start_job(Path(mesh), Path(analysis))

    def run_example(self):
        self.start_job(examples() / 'cube-mesh.inp', examples() / 'cube-analysis.json')

    def start_job(self, mesh, analysis):
        try:
            self.load(mesh)
            self.job.start(mesh, analysis, self.jobs_root)
            self.job_output.setPlainText(f"Job: {self.job.directory}\nMesh: {mesh}\nAnalysis: {analysis}\n")
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
            self.job_label.setText("Cannot start")
            self.job_output.setPlainText(str(error))
            if getattr(self, 'automated_workflow', False):
                raise
            QtWidgets.QMessageBox.critical(self, "Cannot start static analysis", str(error))

    def job_state(self, state):
        active = state in ('Starting', 'Running', 'Cancelling')
        self.run_action.setEnabled(not active)
        self.example_action.setEnabled(not active)
        self.cancel_action.setEnabled(active and state != 'Cancelling')
        self.job_label.setText(state)

    def refresh_job_output(self):
        if not self.job.directory or not self.job.active:
            return
        log = self.job.directory / '_output_analysis.txt'
        if log.is_file():
            with log.open('rb') as stream:
                stream.seek(max(0, log.stat().st_size - 65536))
                text = stream.read().decode('utf-8', errors='replace')
            self.job_output.setPlainText(f"Job: {self.job.directory}\n{self.job.state}\n{text}")

    def job_completed(self, result):
        outcome = result['outcome']
        self.job_output.setPlainText(f"Job: {self.job.directory}\n{result['state']}\n" +
            outcome.get('stdout', '') + '\n' + outcome.get('stderr', '') + '\n' +
            str(outcome.get('error') or outcome.get('failureReason') or ''))
        if result['success']:
            try:
                self.load(self.job.directory / 'analysis.frd')
                if self.fields.count() > 1:
                    self.fields.setCurrentIndex(1)
            except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
                self.job_label.setText('Solved; results could not be opened')
                self.job_output.appendPlainText(str(error))
        if self.closing_after_job:
            QtCore.QTimer.singleShot(0, self.close)

    def open_job_directory(self):
        if self.job.directory and self.job.directory.is_dir():
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(self.job.directory)))

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
        self.current_path = path.resolve()
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
        if self.job.active:
            self.closing_after_job = True
            self.job.cancel()
            event.ignore()
            return
        self.vtk.Finalize()
        super().closeEvent(event)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, nargs="?")
    parser.add_argument("--self-test", type=Path, help="Write bounded native render/ID/field checks and exit")
    parser.add_argument("--screenshot", type=Path)
    parser.add_argument("--run-example", action="store_true", help="Run bundled native static example and load results")
    parser.add_argument("--jobs-root", type=Path, help="New job folders under this directory")
    parser.add_argument("--viewport", choices=("frame-bridge", "native-cocoa"), default="frame-bridge",
                        help="Experimental native Cocoa child view is opt-in; the tested bridge remains default")
    parser.add_argument("--viewport-probe", type=Path, help="Write native event/display/transport evidence into a new directory")
    args = parser.parse_args()
    if args.viewport_probe and (args.self_test or args.run_example):
        parser.error("Use --viewport-probe separately from solve/self-test")
    app = QtWidgets.QApplication([sys.argv[0]])
    app.setOrganizationName("PrePoMax-X")
    app.setApplicationName("PrePoMax-X Preview")
    window = Viewport(args.viewport)
    if args.jobs_root:
        window.jobs_root = args.jobs_root.resolve()
    window.automated_workflow = bool(args.run_example and args.self_test)
    if args.input:
        window.load(args.input.resolve())
    window.show()
    window.vtk.render()
    result = {"success": False}

    def verify():
        try:
            checks = []
            if args.run_example:
                if not window.job.result or not window.job.result['success']:
                    raise ValueError('Native desktop job failed: ' + str(window.job.result))
                if not window.current_path or window.current_path.name != 'analysis.frd':
                    raise ValueError('Successful job results were not loaded')
                checks.append({'name': 'desktop native solve and result loading', 'passed': True})
                result['desktopJob'] = window.job.result
            def check(name, value):
                checks.append({"name": name, "passed": bool(value)})
            target_path = (Path(sys._MEIPASS) / "targets.json" if getattr(sys, "frozen", False)
                else ROOT / "X/Build/targets.json")
            targets = json.loads(target_path.read_text())["targets"]
            candidates = [(rid, data) for rid, data in targets.items() if data["os"] == platform.system()
                and platform.machine().lower() in data["machines"]]
            if len(candidates) != 1:
                raise ValueError("No unique native rendering target")
            target_id, target = candidates[0]
            check("native render window", window.vtk.GetRenderWindow().GetClassName() in target["renderWindows"])
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
            if window.transport == "native-cocoa":
                # QWidget.grab() does not capture a VTK-owned native child view.
                origin = window.vtk.mapToGlobal(QtCore.QPoint(0, 0))
                frame = window.screen().grabWindow(0, origin.x(), origin.y(),
                    window.vtk.width(), window.vtk.height()).toImage()
            else:
                frame = window.vtk.frame
            if frame is None or frame.isNull():
                raise ValueError("Could not capture displayed viewport")
            colors = {frame.pixelColor(x, y).rgb() for x in range(0, frame.width(), 20) for y in range(0, frame.height(), 20)}
            check("displayed frame has mesh/legend pixels", len(colors) > (10 if "fields" in window.scene else 3))
            if args.screenshot:
                args.screenshot.parent.mkdir(parents=True, exist_ok=True)
                if window.transport == "native-cocoa":
                    origin = window.mapToGlobal(QtCore.QPoint(0, 0))
                    capture = window.screen().grabWindow(0, origin.x(), origin.y(), window.width(), window.height())
                else:
                    capture = window.grab()
                check("window capture", capture.save(str(args.screenshot)))
            tool_sha = (json.loads((Path(sys._MEIPASS) / "source-identity.json").read_text())["viewportSha256"]
                if getattr(sys, "frozen", False) else hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
            result.update(success=all(c["passed"] for c in checks), checks=checks,
                storagePaths={name: QtCore.QStandardPaths.writableLocation(getattr(QtCore.QStandardPaths.StandardLocation, name))
                    for name in ('AppLocalDataLocation', 'CacheLocation', 'AppConfigLocation')},
                qtSettingsPath=QtCore.QSettings().fileName(),
                target=target_id, selection=selection, vtkVersion=vtkVersion.GetVTKVersion(), qtVersion=QtCore.qVersion(),
                sourceSha256=window.scene["SourceSha256"], renderer=window.vtk.GetRenderWindow().GetClassName(),
                toolSha256=tool_sha,
                transport=window.transport,
                scope="Bounded render and programmatic picking; human pointer, DPI, other platforms and release packaging remain")
        except Exception as error:
            result["error"] = str(error)
        args.self_test.parent.mkdir(parents=True, exist_ok=True)
        args.self_test.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result))
        window.close()
        app.exit(0 if result["success"] else 1)

    if args.viewport_probe:
        from viewport_probe import run
        QtCore.QTimer.singleShot(1200, lambda: run(app, window, args.viewport_probe))
    elif args.run_example:
        if args.self_test:
            window.job.completed.connect(lambda _: QtCore.QTimer.singleShot(500, verify))
        def begin_example():
            try:
                window.run_example()
            except Exception as error:
                if args.self_test:
                    args.self_test.parent.mkdir(parents=True, exist_ok=True)
                    args.self_test.write_text(json.dumps({'success': False, 'error': str(error)}) + '\n')
                window.close()
                app.exit(1)
        QtCore.QTimer.singleShot(1200, begin_example)
    elif args.self_test:
        QtCore.QTimer.singleShot(1200, verify)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

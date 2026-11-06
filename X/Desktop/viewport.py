#!/usr/bin/env python3
"""Native Qt/VTK viewport candidate. Engineering decoding belongs to C# hosts."""
import argparse
import copy
import hashlib
import json
import platform
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from PyQt6 import QtCore, QtGui, QtWidgets
from jobs import DesktopJob, examples
from analysis_editor import AnalysisDialog, new_definition
from cad_import import IMPORT_COMMANDS, REFERENCE_RECEIPT, NativeCadTool, ReferenceCadTool, run_process
from cad_job import CadImportJob, CadMeshJob
from cad_document import CadDocument
from mesh_export import publish_mesh
from cad_regions import CadRegions
from cad_scene import read_cad_parts
from pmx_project import PmxDialog, PmxSession, available as pmx_available
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


def mesh_command():
    return ([str(Path(sys._MEIPASS) / "hosts/mesh/PrePoMaxX.MeshScene")] if getattr(sys, "frozen", False) else
            ["dotnet", str(ROOT / "X/Desktop/MeshScene/bin/Release/net10.0/PrePoMaxX.MeshScene.dll")])


def decode(path, *, cancel=None):
    """Use the original reader assemblies in separate processes; no second parser."""
    packaged = getattr(sys, "frozen", False)
    if path.suffix.lower() == ".inp":
        command = mesh_command() + [str(path)]
    elif path.suffix.lower() == ".vis":
        command = ([str(Path(sys._MEIPASS) / "hosts/cad/PrePoMaxX.InspectVis")] if packaged else
            ["dotnet", str(ROOT / "X/Feasibility/Cad/Inspect/bin/Release/net10.0/PrePoMaxX.InspectVis.dll")])
        command += ["scene", str(path)]
    elif path.suffix.lower() == ".frd":
        command = ([str(Path(sys._MEIPASS) / "hosts/results/PrePoMaxX.InspectResults")] if packaged else
            ["dotnet", str(ROOT / "X/Results/Inspect/bin/Release/net10.0/PrePoMaxX.InspectResults.dll")]) + ["inspect-frd", str(path)]
    else:
        raise ValueError("Choose an INP mesh, a VIS geometry export, or a completed static C3D8/C3D4 FRD snapshot.")
    return run_reader(command, cancel=cancel)


def run_reader(command, *, cancel=None):
    result = run_process(command, cancel=cancel)
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise ValueError(detail.decode("utf-8", errors="replace") or "Original reader failed")
    scene = json.loads(result.stdout)
    if scene.get("success") is not True:
        raise ValueError("Original reader did not accept input")
    return scene


class Viewport(QtWidgets.QMainWindow):
    cad_completed = QtCore.pyqtSignal(dict)
    mesh_completed = QtCore.pyqtSignal(dict)

    def __init__(self, transport="frame-bridge", *, cad_tool=None):
        super().__init__()
        self.setWindowTitle("PrePoMax-X — native viewport candidate")
        self.resize(1000, 720)
        self.scene = None
        self.cad_tool = cad_tool
        self.cad_job = None
        self.cad_result = None
        self.cad_document = self.cad_mesh = self.mesh_job = None
        self.mesh_result = None
        self.selection = None
        self.current_path = None
        self.model_path = None
        self.model_scene = None
        self.pmx_session = None
        self.mesh_bytes = None
        self.definition = None
        self.analysis_valid = False
        self.editor_dirty = False
        self.closing_after_job = False
        self.job = DesktopJob(self)
        self.job.changed.connect(self.job_state)
        self.job.completed.connect(self.job_completed)
        self.jobs_root = Path(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.StandardLocation.AppLocalDataLocation)) / 'jobs'
        toolbar = self.addToolBar("View")
        open_label = "Open mesh, results or CAD" if cad_tool else "Open INP / FRD / VIS"
        self.open_action = toolbar.addAction(open_label, self.open_dialog)
        self.mesh_action = toolbar.addAction("Mesh CAD…", self.mesh_cad_dialog)
        self.mesh_action.setEnabled(False)
        self.pmx_action = toolbar.addAction("Open static PMX…", self.open_pmx_dialog)
        self.pmx_action.setVisible(pmx_available())
        self.edit_pmx_action = toolbar.addAction("Edit PMX…", self.edit_pmx)
        self.edit_pmx_action.setVisible(False)
        toolbar.addAction("Fit", self.fit)
        self.fields = QtWidgets.QComboBox()
        self.fields.setMinimumWidth(330)
        self.fields.currentIndexChanged.connect(self.set_field)
        self.field_action = toolbar.addWidget(self.fields)
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
        self.cad_edge_mapper = vtkDataSetMapper()
        self.cad_edge_actor = vtkActor()
        self.cad_edge_actor.SetMapper(self.cad_edge_mapper)
        self.cad_edge_actor.GetProperty().SetColor(0.12, 0.12, 0.12)
        self.cad_edge_actor.GetProperty().SetLineWidth(2)
        self.cad_edge_actor.GetProperty().RenderLinesAsTubesOn()
        self.cad_edge_actor.PickableOff()
        self.cad_edge_actor.VisibilityOff()
        self.renderer.AddActor(self.cad_edge_actor)
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
        self.export_mesh_action = jobbar.addAction("Export mesh…", self.export_mesh_dialog)
        self.add_set_action = jobbar.addAction("Add set…", self.add_set_dialog)
        self.add_set_action.setEnabled(False)
        self.configure_action = jobbar.addAction("Configure…", self.configure_model)
        self.run_action = jobbar.addAction("Run analysis", self.run_model)
        self.example_action = jobbar.addAction("Solve example", self.run_example)
        self.cancel_action = jobbar.addAction("Cancel", self.cancel_operation)
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
        model_dock = QtWidgets.QDockWidget("Model", self)
        self.model_tree = QtWidgets.QTreeWidget()
        self.model_tree.setHeaderLabels(['Model', 'Definition'])
        self.model_tree.setMinimumWidth(330)
        self.model_tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.model_tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.model_tree.setToolTip('Double-click a material, section, support, load or step to configure it.')
        self.model_tree.itemDoubleClicked.connect(self.edit_tree_item)
        model_dock.setWidget(self.model_tree)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, model_dock)
        self.regions = CadRegions(self, toolbar, jobbar)
        from cad_operations import CadOperations
        self.operations = CadOperations(self, toolbar)
        self.update_model_tree()

    @property
    def busy(self):
        return self.job.active or self.job.state in ('Starting', 'Running', 'Cancelling') or self.cad_job is not None or self.mesh_job is not None or (getattr(self,'operations',None) is not None and self.operations.job is not None)

    def update_model_tree(self):
        self.regions.begin_tree()
        try:
            self._update_model_tree()
        finally:
            self.regions.end_tree()
            self.regions.refresh()

    def _update_model_tree(self):
        self.model_tree.clear()
        self.cad_faces = {}
        if self.scene and "cad" in self.scene and self.model_scene is None:
            self.populate_cad_tree(self.scene["cad"])
            return
        if self.model_scene is None:
            QtWidgets.QTreeWidgetItem(self.model_tree, ['Open an INP or VIS file', 'or Solve example'])
            return
        units = 'Model units · C3D10 preview' if self.quadratic_preview else self.pmx_session.project['graph']['unitSystem'] if self.pmx_session else self.definition['unitSystem']
        root = QtWidgets.QTreeWidgetItem(self.model_tree, [self.model_path.name, units or 'Choose units'])
        root.setData(0, QtCore.Qt.ItemDataRole.UserRole, 0)
        QtWidgets.QTreeWidgetItem(root, ['Mesh', f"{len(self.model_scene['nodes'])} nodes · {len(self.model_scene['elements'])} elements"])
        for key, label in [('nodeSets', 'Node sets'), ('elementSets', 'Element sets')]:
            group = QtWidgets.QTreeWidgetItem(root, [label])
            for item in self.model_scene.get(key, []):
                QtWidgets.QTreeWidgetItem(group, [item['name'], str(item['count'])])
        if self.quadratic_preview:
            QtWidgets.QTreeWidgetItem(root,['C3D10 preview','Measurement/analysis gated'])
            if self.cad_document is not None:self.populate_cad_tree(self.cad_document.scene['cad'])
            self.model_tree.expandToDepth(1);return
        for tab, label, records, region in [(1, 'Materials', self.definition['materials'], 'youngsModulus'),
                (2, 'Solid sections', self.definition['sections'], 'elementSet'),
                (3, 'Supports', self.definition['step']['constraints'], 'nodeSet'),
                (4, 'Nodal loads', self.definition['step']['loads'], 'nodeSet')]:
            group = QtWidgets.QTreeWidgetItem(root, [label, str(len(records))])
            group.setData(0, QtCore.Qt.ItemDataRole.UserRole, tab)
            for record in records:
                child = QtWidgets.QTreeWidgetItem(group, [record['name'], record[region]])
                child.setData(0, QtCore.Qt.ItemDataRole.UserRole, tab)
        step = QtWidgets.QTreeWidgetItem(root, [self.definition['step']['name'], 'Static step / output'])
        step.setData(0, QtCore.Qt.ItemDataRole.UserRole, 5)
        if self.cad_document is not None:
            self.populate_cad_tree(self.cad_document.scene["cad"])
        self.model_tree.expandToDepth(1)

    def populate_cad_tree(self, cad):
        path = self.cad_document.source if self.cad_document is not None and self.model_scene is not None else self.current_path
        root = QtWidgets.QTreeWidgetItem(self.model_tree, [path.name, "Source CAD" if self.model_scene is not None else "Read-only CAD"])
        if "conversion" in cad:
            QtWidgets.QTreeWidgetItem(root, ["Conversion", cad["conversion"]])
        unit = "Model units" if cad["lengthUnit"] == "model" else cad["lengthUnit"]
        QtWidgets.QTreeWidgetItem(root, ["Length unit", unit])
        if "parts" in cad:
            for part in cad["parts"]:
                item = QtWidgets.QTreeWidgetItem(root, [part["name"], f'{part["triangleCount"]} triangles'])
                self.regions.decorate(item, ("part", part["id"], 0))
                self.populate_cad_entities(item, part["entities"], part["id"])
        else:
            self.populate_cad_entities(root, cad["entities"])
        self.model_tree.expandToDepth(1)

    def populate_cad_entities(self, root, metadata, part_id=None):
        for kind, label in (("solid", "Solids"), ("shell", "Shells"), ("face", "Faces"), ("edge", "Edges")):
            entities = metadata.get(kind, [])
            group = QtWidgets.QTreeWidgetItem(root, [label, str(len(entities))])
            for entity in entities:
                properties = entity["properties"]
                item = QtWidgets.QTreeWidgetItem(group, [f"{kind.title()} {entity['id']}",
                                                         ", ".join(map(str, properties.get("type", [])))])
                if kind == "face":
                    key = (part_id, entity["id"]) if part_id is not None else entity["id"]
                    self.cad_faces[key] = item
                    self.regions.decorate(item, ("face", part_id, entity["id"]))
                for name in ("volume", "surface_area", "center_of_mass", "area", "length", "radius", "convexity"):
                    if name in properties:
                        values = properties[name]
                        display = ", ".join(format(value, ".12g") if isinstance(value, float) else str(value)
                                            for value in values)
                        measurement = QtWidgets.QTreeWidgetItem(item, [name.replace("_", " ").capitalize(), display])
                        measurement.setToolTip(1, ", ".join(map(str, values)))

    def edit_tree_item(self, item, column):
        tab = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if tab is not None:
            self.configure_model(tab)

    def add_set_dialog(self):
        if self.busy or self.model_scene is None:
            return
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle('Add mesh set')
        form = QtWidgets.QFormLayout(dialog)
        kind = QtWidgets.QComboBox()
        kind.addItem('Node set', 'node')
        kind.addItem('Element set', 'element')
        name = QtWidgets.QLineEdit()
        name.setMaxLength(80)
        ids = QtWidgets.QLineEdit()
        ids.setMaxLength(12000)
        ids.setPlaceholderText('Original mesh IDs, separated by commas or spaces')
        pick = QtWidgets.QPushButton('Use picked ID')
        selection = self.selection if self.scene is self.model_scene else None
        pick.setEnabled(bool(selection))
        if selection:
            def use_pick():
                field = 'nearestVertexNodeId' if kind.currentData() == 'node' else 'elementId'
                ids.setText(str(selection[field]))
            pick.clicked.connect(use_pick)
        form.addRow('Kind', kind)
        form.addRow('Name', name)
        form.addRow('IDs', ids)
        form.addRow('', pick)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok |
                                             QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)

        def apply():
            try:
                self.add_named_set(kind.currentData(), name.text().strip(), ids.text())
            except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
                QtWidgets.QMessageBox.critical(dialog, 'Cannot add mesh set', str(error))
            else:
                dialog.accept()

        buttons.accepted.connect(apply)
        dialog.exec()

    def add_named_set(self, kind, name, labels):
        if self.busy or self.model_scene is None or self.pmx_session is not None:
            raise ValueError('Open an INP mesh and finish any active job before editing sets.')
        if len(labels) > 12000:
            raise ValueError('The set label list is too long.')
        ids = ','.join(re.split(r'[,\s]+', labels.strip()))
        self.write_mesh_set(kind, name, ids, 'add-set')

    def add_cad_region_set(self, kind, name):
        if self.busy:
            raise ValueError('Finish the active operation before creating a CAD region set.')
        sources = self.regions.sources(kind)
        self.cad_document.verify()
        refs = sorted(self.regions.refs)
        before = hashlib.sha256(self.mesh_bytes).hexdigest()
        scene = self.write_mesh_set(kind, name, ','.join(sources), 'add-region-set')
        self.cad_mesh.authored_regions.append({'name': name, 'kind': kind, 'sourceSets': sources,
            'regions': [{'kind': r[0], 'partId': r[1], 'entityId': r[2]} for r in refs],
            'inputMeshSha256': before, 'outputMeshSha256': self.model_scene['SourceSha256']})
        return scene['authoredSet']

    def write_mesh_set(self, kind, name, labels, operation):
        with tempfile.TemporaryDirectory(prefix='prepomaxx-set-') as directory:
            original, updated = (Path(directory) / file for file in ('mesh.inp', 'updated.inp'))
            original.write_bytes(self.mesh_bytes)
            scene = run_reader(mesh_command() + [operation, str(original), str(updated), kind, name, labels])
            mesh_bytes = updated.read_bytes()
            if hashlib.sha256(mesh_bytes).hexdigest() != scene['SourceSha256']:
                raise ValueError('Edited mesh changed while loading the new set.')
        if self.cad_mesh is not None:
            scene["cadMesh"] = self.cad_mesh.scene["cadMesh"]
        if self.scene is self.model_scene:
            self.scene = scene
        self.model_scene, self.mesh_bytes = scene, mesh_bytes
        self.analysis_valid = False
        self.editor_dirty = True
        self.update_model_tree()
        return scene

    @property
    def quadratic_preview(self):
        return self.model_scene is not None and any(e.get('vtkCellType')==24 or e.get('type')=='ParabolicTetraElement' for e in self.model_scene['elements'])

    def require_analysis(self):
        if not self.quadratic_preview:return True
        message='C3D10 mesh preview/export is available. Quadratic tetrahedron analysis is gated by the unresolved original integration discrepancy.'
        if getattr(self,'automated_workflow',False):raise ValueError(message)
        QtWidgets.QMessageBox.information(self,'Quadratic analysis unavailable',message)
        return False

    def export_mesh_dialog(self):
        if self.busy or self.model_scene is None:return
        name,_=QtWidgets.QFileDialog.getSaveFileName(self,'Export mesh-only INP',str(self.model_path.with_name(self.model_path.stem+'-mesh.inp')),'Mesh-only INP (*.inp)',options=QtWidgets.QFileDialog.Option.DontConfirmOverwrite)
        if not name:return
        try:
            target=Path(name)
            if not target.suffix:target=target.with_suffix('.inp')
            self.mesh_export_result=publish_mesh(self.mesh_bytes,self.model_scene,target,decode)
            self.job_label.setText('Mesh-only INP export complete')
        except (OSError,ValueError) as error:
            self.mesh_export_result={'success':False,'error':str(error)}
            if getattr(self,'automated_workflow',False):raise
            QtWidgets.QMessageBox.critical(self,'Cannot export mesh',str(error))

    def configure_model(self, tab=0):
        if not self.require_analysis():return
        if self.busy:
            return
        if self.pmx_session is not None:
            self.edit_pmx()
            return
        if self.model_scene is None:
            QtWidgets.QMessageBox.information(self, 'Open a mesh', 'Open an INP mesh or use Solve example before configuring an analysis.')
            return
        dialog = AnalysisDialog(self, self.model_scene, self.mesh_bytes, self.definition, int(tab))
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.editor_dirty = self.editor_dirty or dialog.definition != self.definition
            self.definition = dialog.definition
            self.analysis_valid = True
            self.update_model_tree()

    def run_model(self):
        if not self.require_analysis():return
        if self.busy:
            return
        if not self.analysis_valid:
            self.configure_model()
        if self.model_scene is not None and self.analysis_valid:
            if self.pmx_session is not None:
                pmx = self.pmx_session
                self.start_job(self.model_path, None, definition=pmx.definition, mesh_bytes=pmx.mesh_bytes,
                               pmx_sha256=pmx.project['inputSha256'])
            else:
                self.start_job(self.model_path, None, definition=self.definition, mesh_bytes=self.mesh_bytes)

    def run_example(self):
        if self.busy:
            return
        if not self.confirm_discard():
            return
        definition = json.loads((examples() / 'cube-analysis.json').read_text())
        self.load(examples() / 'cube-mesh.inp', as_model=True, definition=definition)
        self.analysis_valid = True
        self.run_model()

    def start_job(self, mesh, analysis, *, definition=None, mesh_bytes=None, pmx_sha256=None):
        if self.busy:
            raise ValueError("Finish the active operation before starting an analysis.")
        try:
            if not self.require_analysis():return
            if definition is None:
                self.load(mesh)
            else:
                self.show_scene(self.model_scene, self.model_path)
            self.job.start(mesh, analysis, self.jobs_root, definition=definition,
                           mesh_bytes=mesh_bytes, pmx_sha256=pmx_sha256, cad_mesh=self.cad_mesh,
                           pmx_bytes=self.pmx_session.contents if pmx_sha256 is not None else None)
            self.job_output.setPlainText(f"Job: {self.job.directory}\nSource: {mesh}\nInputs: {self.job.input_directory or analysis}\n")
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
            self.job_label.setText("Cannot start")
            self.job_output.setPlainText(str(error))
            if getattr(self, 'automated_workflow', False):
                raise
            QtWidgets.QMessageBox.critical(self, "Cannot start static analysis", str(error))

    def job_state(self, state):
        importing = self.cad_job is not None
        if importing:
            state = "Cancelling CAD" if self.cad_job.cancel_requested.is_set() else "Importing CAD"
        meshing = self.mesh_job is not None
        if meshing:
            state = "Cancelling mesh" if self.mesh_job.cancel_requested.is_set() else "Meshing CAD"
        editing = getattr(self,'operations',None) is not None and self.operations.job is not None
        if editing:state='Cancelling CAD edit' if self.operations.job.cancel_requested.is_set() else 'Editing CAD'
        active = importing or meshing or editing or state in ('Starting', 'Running', 'Cancelling')
        self.mesh_action.setEnabled(not active and self.cad_document is not None and self.pmx_session is None)
        cad = self.scene is not None and "cad" in self.scene and self.model_scene is None
        self.run_action.setEnabled(not active and not cad and not self.quadratic_preview)
        self.configure_action.setEnabled(not active and not cad and not self.quadratic_preview and self.pmx_session is None)
        self.edit_pmx_action.setEnabled(not active and self.pmx_session is not None)
        self.export_mesh_action.setEnabled(not active and self.model_scene is not None)
        self.run_action.setToolTip("Quadratic analysis is gated by the original integration discrepancy" if self.quadratic_preview else "Run the supported static analysis")
        self.add_set_action.setEnabled(not active and self.model_scene is not None and self.pmx_session is None)
        self.open_action.setEnabled(not active)
        self.pmx_action.setEnabled(not active)
        self.example_action.setEnabled(not active)
        self.cancel_action.setEnabled(active and state not in ('Cancelling', 'Cancelling CAD', 'Cancelling mesh','Cancelling CAD edit'))
        self.job_label.setText(state)
        self.regions.refresh()
        if getattr(self,'operations',None) is not None:self.operations.refresh()

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
        if self.job.workspace and self.job.workspace.is_dir():
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(self.job.workspace)))

    def open_dialog(self):
        supported = "*.inp *.frd *.vis"
        if self.cad_tool:
            supported += " " + " ".join("*" + suffix for suffix in IMPORT_COMMANDS)
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open mesh, results or geometry", "",
                                                        f"Supported files ({supported})")
        if path:
            try:
                as_model = Path(path).suffix.lower() == '.inp'
                if as_model and not self.confirm_discard():
                    return
                if Path(path).suffix.lower() in IMPORT_COMMANDS:
                    self.start_cad_import(Path(path))
                else:
                    self.load(Path(path), as_model=as_model)
            except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
                QtWidgets.QMessageBox.critical(self, "Cannot open file", str(error))

    def open_pmx_dialog(self):
        name, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open static PMX project', '',
                                                        'PrePoMax project (*.pmx)')
        if name:
            try:
                self.open_pmx(name)
            except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
                QtWidgets.QMessageBox.critical(self, 'Cannot open static PMX', str(error))

    def open_pmx(self, path):
        if self.busy:
            raise ValueError('Finish the active job before opening a static PMX.')
        if not self.confirm_discard():
            return
        pmx = PmxSession(path)
        with tempfile.TemporaryDirectory(prefix='prepomaxx-pmx-mesh-') as directory:
            mesh = Path(directory) / 'mesh.inp'
            mesh.write_bytes(pmx.mesh_bytes)
            scene = decode(mesh)
        if hashlib.sha256(pmx.mesh_bytes).hexdigest() != scene['SourceSha256']:
            raise ValueError('The displayed PMX mesh differs from the validated model.')
        document = None
        if pmx.cad_model and isinstance(self.cad_tool, NativeCadTool):
            with tempfile.TemporaryDirectory(prefix='prepomaxx-pmx-cad-') as directory:
                brep = Path(directory)/'saved.brep'
                brep.write_bytes(pmx.project['cadGeometry'][0]['Brep'].encode('utf-8'))
                document = CadDocument(brep, self.cad_tool, decode)
            document.source = pmx.path
            document.scene['cad']['parts'][0]['name'] = pmx.project['cadGeometry'][0]['Name']
        try:
            self.set_model(pmx.path, scene, pmx.mesh_bytes, pmx.definition['analysis'], pmx=pmx, cad_document=document)
        except BaseException:
            if document is not None:
                document.close()
            raise

    def edit_pmx(self):
        if not self.busy and self.pmx_session is not None:
            PmxDialog(self, self.pmx_session).exec()

    def load(self, path, *, as_model=False, definition=None):
        if self.busy:
            raise ValueError("Finish the active operation before opening a document.")
        suffix = path.suffix.lower()
        if suffix == ".vis" or suffix in IMPORT_COMMANDS:
            if self.job.active:
                raise ValueError("Finish the active job before opening CAD geometry.")
            if suffix != ".vis" and self.cad_tool is None:
                raise ValueError("STEP/BREP import requires --cad-native RUNTIME or --cad-reference RUNTIME BOTTLE.")
            if not self.confirm_discard():
                return
            if suffix == ".vis":
                scene = decode(path)
            else:
                QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
                try:
                    if isinstance(self.cad_tool, NativeCadTool):
                        document = CadDocument(path, self.cad_tool, decode)
                        self.set_cad_document(document.scene, path, document=document)
                        return
                    else:
                        with tempfile.TemporaryDirectory(prefix="prepomaxx-cad-") as directory:
                            scene = read_cad_parts(path, self.cad_tool, decode, Path(directory) / "import")
                finally:
                    QtWidgets.QApplication.restoreOverrideCursor()
            self.set_cad_document(scene, path)
            return
        mesh_bytes = path.read_bytes() if as_model else None
        scene = decode(path)
        if as_model and hashlib.sha256(mesh_bytes).hexdigest() != scene['SourceSha256']:
            raise ValueError('Mesh changed during import. Reopen it before configuring an analysis.')
        if as_model:
            self.set_model(path, scene, mesh_bytes, definition)
        else:
            leaving_cad = self.scene is not None and "cad" in self.scene
            self.show_scene(scene, path)
            if leaving_cad:
                self.job_state(self.job.state)
                self.update_model_tree()

    def release_cad(self,*,keep_geometry_history=False):
        if not keep_geometry_history and getattr(self,'operations',None) is not None:
            self.operations.history.clear()
        if self.cad_mesh is not None:
            self.cad_mesh.close()
        if self.cad_document is not None and not keep_geometry_history:
            self.cad_document.close()
        self.cad_mesh = self.cad_document = None
        self.regions.reset()
        self.regions.refresh()

    def set_cad_document(self, scene, path, *, document=None,keep_geometry_history=False):
        self.regions.reset()
        self.show_scene(scene, path)
        self.release_cad(keep_geometry_history=keep_geometry_history)
        self.cad_document = document
        self.model_path = self.model_scene = self.mesh_bytes = self.definition = self.pmx_session = None
        self.analysis_valid = self.editor_dirty = False
        self.edit_pmx_action.setVisible(False)
        self.job_state(self.job.state)
        self.update_model_tree()

    def start_cad_import(self, path):
        if self.busy:
            raise ValueError("Finish the active operation before importing CAD.")
        if self.cad_tool is None:
            raise ValueError("STEP/BREP import requires --cad-native RUNTIME or --cad-reference RUNTIME BOTTLE.")
        if not self.confirm_discard():
            return
        self.cad_result = None
        self.cad_job = CadImportJob(path, self.cad_tool, decode, self)
        self.cad_job.finished.connect(self.cad_import_finished)
        self.job_state(self.job.state)
        self.cad_job.start()

    def cancel_operation(self):
        if self.operations.job is not None:
            self.operations.job.cancel();self.job_state(self.job.state)
        elif self.cad_job is not None:
            self.cad_job.cancel()
            self.job_state(self.job.state)
        elif self.mesh_job is not None:
            self.mesh_job.cancel()
            self.job_state(self.job.state)
        else:
            self.job.cancel()

    def cad_import_finished(self):
        job = self.cad_job
        result = job.result or {"success": False, "error": "CAD import ended without a result."}
        if job.cancel_requested.is_set():
            result = {"success": False, "cancelled": True}
        self.cad_job = None
        try:
            if result["success"]:
                self.set_cad_document(result["scene"], job.source, document=result.get("document"))
        except (OSError, ValueError, KeyError) as error:
            result = {"success": False, "error": str(error)}
        self.cad_result = result
        if not result["success"] and job.document is not None:
            job.document.close()
        self.job_state(self.job.state)
        state = "CAD import complete" if result["success"] else (
            "CAD import cancelled" if result.get("cancelled") else "CAD import failed")
        self.job_label.setText(state)
        if result.get("error"):
            self.job_output.setPlainText(result["error"])
            if not self.closing_after_job and not getattr(self, "automated_workflow", False):
                QtWidgets.QMessageBox.critical(self, "Cannot import CAD", result["error"])
        job.deleteLater()
        self.cad_completed.emit(result)
        if self.closing_after_job:
            QtCore.QTimer.singleShot(0, self.close)

    def mesh_cad_dialog(self):
        if self.busy or self.cad_document is None:
            return
        dialog=QtWidgets.QDialog(self);dialog.setWindowTitle('Mesh CAD')
        form=QtWidgets.QFormLayout(dialog)
        size=QtWidgets.QDoubleSpinBox();size.setObjectName('cadMaximumSize');size.setDecimals(6);size.setRange(.000001,1e9)
        size.setValue(max(max(n[axis] for n in self.cad_document.scene['nodes'])-min(n[axis] for n in self.cad_document.scene['nodes']) for axis in ('x','y','z'))/10)
        order=QtWidgets.QComboBox();order.setObjectName('cadMeshOrder');order.addItem('Linear C3D4',1);order.addItem('Quadratic C3D10 — preview/export only',2)
        form.addRow('Maximum element size (model units)',size);form.addRow('Mesh order',order)
        note=QtWidgets.QLabel('Quadratic measurement and analysis remain unavailable while the original integration discrepancy is unresolved.');note.setWordWrap(True);form.addRow(note)
        buttons=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok|QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);form.addRow(buttons)
        if dialog.exec()==QtWidgets.QDialog.DialogCode.Accepted:self.start_cad_mesh(size.value(),element_order=order.currentData())

    def start_cad_mesh(self, maximum_size, *, element_order=1):
        if self.busy or self.cad_document is None:
            raise ValueError("Open native CAD and finish the current operation before meshing.")
        if not self.confirm_discard():
            return
        self.mesh_result = None
        self.mesh_job = CadMeshJob(self.cad_document, mesh_command(), run_reader, maximum_size, self, element_order=element_order)
        self.mesh_job.finished.connect(self.cad_mesh_finished)
        self.job_state(self.job.state)
        self.mesh_job.start()

    def cad_mesh_finished(self):
        job = self.mesh_job
        result = job.result or {"success": False, "error": "Mesher did not return a result."}
        if job.cancel_requested.is_set():
            result = {"success": False, "cancelled": True}
        self.mesh_job = None
        try:
            if result["success"]:
                mesh = result["mesh"]
                if mesh.document is not self.cad_document:
                    raise ValueError("CAD document changed before mesh publication.")
                self.set_model(mesh.mesh, mesh.scene, mesh.mesh_bytes, None, cad_mesh=mesh)
                self.editor_dirty = True
        except (OSError, ValueError, KeyError) as error:
            result = {"success": False, "error": str(error)}
        if not result["success"] and job.mesh is not None:
            job.mesh.close()
        self.mesh_result = result
        self.job_state(self.job.state)
        self.job_label.setText(("Quadratic mesh preview — analysis gated" if self.quadratic_preview else "CAD mesh ready") if result["success"] else
                              "Meshing cancelled" if result.get("cancelled") else "Meshing failed")
        if result.get("error"):
            self.job_output.setPlainText(result["error"])
            if not self.closing_after_job and not getattr(self, "automated_workflow", False):
                QtWidgets.QMessageBox.critical(self, "Cannot mesh CAD", result["error"])
        job.deleteLater()
        self.mesh_completed.emit(result)
        if self.closing_after_job:
            QtCore.QTimer.singleShot(0, self.close)

    def set_model(self, path, scene, mesh_bytes, definition, *, pmx=None, cad_mesh=None, cad_document=None):
        self.regions.reset()
        self.show_scene(scene, path)
        if cad_mesh is None:
            self.release_cad()
            self.cad_document = cad_document
        else:
            if self.cad_mesh is not None:
                self.cad_mesh.close()
            self.cad_mesh = cad_mesh
        self.model_path, self.model_scene, self.mesh_bytes = path.resolve(), scene, mesh_bytes
        self.definition = copy.deepcopy(definition) if definition is not None else new_definition()
        self.pmx_session = pmx
        self.analysis_valid = pmx is not None
        self.editor_dirty = False
        self.edit_pmx_action.setVisible(pmx is not None)
        self.job_state(self.job.state)
        self.update_model_tree()

    def show_scene(self, scene, path):
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
        cad = scene.get("cad")
        if cad:
            face_ids = vtkIdTypeArray()
            face_ids.SetName("SourceFaceId")
            for element in scene["elements"]:
                face_ids.InsertNextValue(element["sourceFaceId"])
            grid.GetCellData().AddArray(face_ids)
            if "parts" in cad:
                for records, target, fields in (
                    (nodes, grid.GetPointData(), ("SourceNodeId", "SourcePartId")),
                    (scene["elements"], grid.GetCellData(), ("SourceElementId", "SourcePartId")),
                ):
                    for name in fields:
                        array = vtkIdTypeArray()
                        array.SetName(name)
                        key = name[0].lower() + name[1:]
                        for record in records:
                            array.InsertNextValue(record[key])
                        target.AddArray(array)
            edge_grid = vtkUnstructuredGrid()
            edge_grid.SetPoints(points)
            for segment in cad["edgeSegments"]:
                edge_grid.InsertNextCell(3, 2, [indices[node] for node in segment["nodeIds"]])
            self.cad_edge_mapper.SetInputData(edge_grid)
        else:
            self.cad_edge_mapper.RemoveAllInputs()
        self.cad_edge_actor.SetVisibility(cad is not None)
        self.actor.GetProperty().SetEdgeVisibility(cad is None)
        self.fields.blockSignals(True)
        self.fields.clear()
        self.fields.addItem("CAD geometry" if cad else "Mesh (undeformed)", None)
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
        self.regions.on_scene()
        self.fit()
        if cad:
            self.statusBar().showMessage(f'{len(scene["elements"])} display triangles · '
                                         f'{len(cad["edgeSegments"])} CAD edge segments · read-only')
        else:
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
            self.statusBar().showMessage("No selection")
            return None
        cell, point = self.picker.GetCellId(), self.picker.GetPointId()
        if cell < 0 or point < 0:
            return None
        if "cad" in self.scene:
            face_id = self.grid.GetCellData().GetArray("SourceFaceId").GetValue(cell)
            self.selection = {"sourceFaceId": face_id}
            part_ids = self.grid.GetCellData().GetArray("SourcePartId")
            key = face_id
            if part_ids is not None:
                part_id = part_ids.GetValue(cell)
                self.selection["sourcePartId"] = part_id
                key = (part_id, face_id)
            item = self.cad_faces[key]
            item.parent().setExpanded(True)
            if part_ids is None or not self.regions.available:
                self.model_tree.setCurrentItem(item)
            else:
                self.regions.picked(part_id, face_id)
            item.setExpanded(True)
            self.model_tree.scrollToItem(item)
            description = f"CAD part {part_id}, face {face_id}" if part_ids is not None else f"CAD face {face_id}"
            self.statusBar().showMessage(description + " · source IDs")
            return self.selection
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
        if not self.closing_after_job and not self.confirm_discard():
            event.ignore()
            return
        if self.job.active:
            self.closing_after_job = True
            self.job.cancel()
            event.ignore()
            return
        if self.cad_job is not None or self.mesh_job is not None or self.operations.job is not None:
            self.closing_after_job = True
            self.cancel_operation()
            event.ignore()
            return
        self.vtk.Finalize()
        self.release_cad()
        super().closeEvent(event)

    def confirm_discard(self):
        if not self.editor_dirty:
            return True
        return QtWidgets.QMessageBox.question(self, 'Discard unsaved model edits?',
            'Geometry and analysis edits are kept in memory. Submitted run inputs remain in Job files. '
            'Discard the current model edits?', QtWidgets.QMessageBox.StandardButton.Yes |
            QtWidgets.QMessageBox.StandardButton.No, QtWidgets.QMessageBox.StandardButton.No) == QtWidgets.QMessageBox.StandardButton.Yes


def verify_cad_view(window, check):
    scene = window.scene
    cad = scene["cad"]
    check("renderer node and triangle IDs retained" if "parts" in cad else "original VIS node and triangle IDs retained",
          [window.grid.GetPointData().GetGlobalIds().GetValue(i) for i in range(window.grid.GetNumberOfPoints())]
          == [node["id"] for node in scene["nodes"]]
          and [window.grid.GetCellData().GetGlobalIds().GetValue(i) for i in range(window.grid.GetNumberOfCells())]
          == [element["id"] for element in scene["elements"]])
    check("CAD edges visible without triangle wireframe",
          window.cad_edge_actor.GetVisibility() and not window.actor.GetProperty().GetEdgeVisibility()
          and window.cad_edge_mapper.GetInput().GetNumberOfCells() == len(cad["edgeSegments"]))
    check("CAD document is read-only", window.model_scene is None and not window.run_action.isEnabled()
          and not window.configure_action.isEnabled() and not window.add_set_action.isEnabled())
    face_ids = window.grid.GetCellData().GetArray("SourceFaceId")
    check("source face IDs carried by VTK cells", [face_ids.GetValue(i) for i in range(face_ids.GetNumberOfTuples())]
          == [element["sourceFaceId"] for element in scene["elements"]])
    hits = set()
    for i, element in enumerate(scene["elements"]):
        source_id = element["sourceFaceId"]
        part_id = element.get("sourcePartId")
        key = (part_id, source_id) if part_id is not None else source_id
        if key in hits:
            continue
        triangle = window.grid.GetCell(i).GetPoints()
        centroid = [sum(triangle.GetPoint(j)[axis] for j in range(3)) / 3 for axis in range(3)]
        window.renderer.SetWorldPoint(*centroid, 1)
        window.renderer.WorldToDisplay()
        x, y, _ = window.renderer.GetDisplayPoint()
        selection = window.pick(x, y)
        if selection and window.picker.GetCellId() == i:
            expected = {"sourceFaceId": source_id}
            if part_id is not None:
                expected["sourcePartId"] = part_id
            check(f"CAD pick resolves source face {key}",
                  selection == expected and window.model_tree.currentItem() is window.cad_faces[key])
            hits.add(key)
    check("visible CAD face picked", bool(hits))
    result = {"nodes": len(scene["nodes"]), "triangles": len(scene["elements"]),
              "edgeSegments": len(cad["edgeSegments"]), "sourceFaces": len(window.cad_faces)}
    if "parts" in cad:
        check("visible face picked in every CAD part", {part for part, _ in hits} == {p["id"] for p in cad["parts"]})
        for records, data, fields in (
            (scene["nodes"], window.grid.GetPointData(), ("sourceNodeId", "sourcePartId")),
            (scene["elements"], window.grid.GetCellData(), ("sourceElementId", "sourcePartId")),
        ):
            for key in fields:
                array = data.GetArray(key[0].upper() + key[1:])
                check(f"VTK preserves {key}", [array.GetValue(i) for i in range(len(records))]
                      == [row[key] for row in records])
        result.update(partCount=len(cad["parts"]), pickedPartFaces=sorted(hits))
    else:
        result["pickedSourceFaceIds"] = sorted(hits)
    return result


def verify_mesh_view(window, check):
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
    return selection


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, nargs="?")
    parser.add_argument("--self-test", type=Path, help="Write bounded native render/ID/field checks and exit")
    parser.add_argument("--screenshot", type=Path)
    parser.add_argument("--run-example", action="store_true", help="Run bundled native static example and load results")
    parser.add_argument("--jobs-root", type=Path, help="New job folders under this directory")
    parser.add_argument("--viewport", choices=("frame-bridge", "native-cocoa"), default="frame-bridge",
                        help="Experimental native Cocoa child view is opt-in; the tested bridge remains default")
    cad_modes = parser.add_mutually_exclusive_group()
    cad_modes.add_argument("--cad-reference", nargs=2, metavar=("RUNTIME", "BOTTLE"),
                        help="Enable STEP/BREP inspection with the pinned 3.0.0 runtime in a CrossOver bottle")
    cad_modes.add_argument("--cad-native", type=Path, metavar="RUNTIME",
                        help="Enable STEP/BREP inspection with a checked native Netgen/OCCT research build")
    parser.add_argument("--viewport-probe", type=Path, help="Write native event/display/transport evidence into a new directory")
    parser.add_argument("--editor-probe", type=Path, help="Exercise edited controls and two native jobs; write evidence to a new directory")
    parser.add_argument("--pmx-probe", type=Path, nargs=2, metavar=("INPUT", "OUTPUT"),
                        help="Exercise static PMX edit, save, reopen and solve in the desktop")
    parser.add_argument("--cad-workflow-probe", type=Path, nargs=3, metavar=("CAD", "ANALYSIS", "OUTPUT"),
                        help="Exercise native CAD to linear tetrahedra, editor and real static results")
    parser.add_argument("--cad-pmx-probe", type=Path, nargs=2, metavar=("PMX", "OUTPUT"),
                        help="Verify CAD PMX native edit/save/reopen/solve")
    parser.add_argument('--cad-edit-probe',type=Path,nargs=2,metavar=('CAD','OUTPUT'),
                        help='Verify native CAD dialogs, STEP export, remeshing and solve')
    parser.add_argument('--cad-quadratic-probe',type=Path,nargs=2,metavar=('CAD','OUTPUT'),help='Verify quadratic preview, gated analysis and mesh-only export')
    args = parser.parse_args()
    if args.cad_quadratic_probe and (not args.cad_native or any([args.input,args.self_test,args.editor_probe,args.pmx_probe,args.viewport_probe,args.run_example,args.cad_workflow_probe,args.cad_pmx_probe,args.cad_edit_probe])):
        parser.error('Use --cad-quadratic-probe with --cad-native separately from other inputs/probes')
    if args.cad_edit_probe and (not args.cad_native or args.input or args.self_test or args.editor_probe or args.pmx_probe or args.viewport_probe or args.run_example or args.cad_workflow_probe or args.cad_pmx_probe):
        parser.error('Use --cad-edit-probe with --cad-native separately from other inputs/probes')
    if args.cad_pmx_probe and (not args.cad_native or args.input or args.self_test or args.editor_probe or args.pmx_probe or args.viewport_probe or args.run_example or args.cad_workflow_probe):
        parser.error("Use --cad-pmx-probe with --cad-native separately from other inputs/probes")
    if args.cad_workflow_probe and (not args.cad_native or args.input or args.self_test or args.editor_probe or args.pmx_probe or args.viewport_probe or args.run_example):
        parser.error("Use --cad-workflow-probe with --cad-native separately from other inputs/probes")
    if args.viewport_probe and (args.self_test or args.run_example):
        parser.error("Use --viewport-probe separately from solve/self-test")
    if args.editor_probe and (args.self_test or args.run_example or args.viewport_probe or args.input):
        parser.error("Use --editor-probe separately from other probes and input")
    if args.pmx_probe and (args.self_test or args.run_example or args.viewport_probe or args.editor_probe or args.input):
        parser.error("Use --pmx-probe separately from other probes and input")
    cad_tool = None
    if args.cad_native:
        try:
            cad_tool = NativeCadTool(args.cad_native)
        except (OSError, ValueError, KeyError) as error:
            parser.error(str(error))
    if args.cad_reference:
        runtime, bottle = args.cad_reference
        receipt = (Path(sys._MEIPASS) / "cad-reference/verification.json"
                   if getattr(sys, "frozen", False) else REFERENCE_RECEIPT)
        try:
            cad_tool = ReferenceCadTool(Path(runtime), bottle, receipt)
        except (OSError, ValueError, KeyError) as error:
            parser.error(str(error))
    app = QtWidgets.QApplication([sys.argv[0]])
    app.setOrganizationName("PrePoMax-X")
    app.setApplicationName("PrePoMax-X Preview")
    window = Viewport(args.viewport, cad_tool=cad_tool)
    if args.jobs_root:
        window.jobs_root = args.jobs_root.resolve()
    window.automated_workflow = bool(args.self_test or args.editor_probe or args.pmx_probe or args.cad_workflow_probe or args.cad_pmx_probe or args.cad_edit_probe or args.cad_quadratic_probe)
    if args.input:
        if args.input.suffix.lower() == '.pmx':
            window.open_pmx(args.input)
        elif args.input.suffix.lower() in IMPORT_COMMANDS:
            window.start_cad_import(args.input.resolve())
        else:
            window.load(args.input.resolve(), as_model=args.input.suffix.lower() == '.inp')
    window.show()
    window.vtk.render()
    result = {"success": False}

    def verify():
        try:
            checks = []
            if window.cad_result is not None and not window.cad_result["success"]:
                raise ValueError(window.cad_result.get("error", "CAD import cancelled."))
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
            if "cad" in window.scene:
                result["cad"] = verify_cad_view(window, check)
                if "conversion" in window.scene["cad"]:
                    result["cad"]["conversion"] = window.scene["cad"]["conversion"]
                selection = window.selection
            else:
                selection = verify_mesh_view(window, check)
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

    if args.cad_quadratic_probe:
        from quadratic_probe import begin
        source,output=(p.resolve() for p in args.cad_quadratic_probe)
        QtCore.QTimer.singleShot(1000,lambda:begin(app,window,source,output))
    elif args.cad_edit_probe:
        from cad_edit_probe import begin
        source,output=(p.resolve() for p in args.cad_edit_probe)
        QtCore.QTimer.singleShot(1200,lambda:begin(app,window,source,output))
    elif args.cad_pmx_probe:
        from cad_pmx_probe import begin
        source, output = (p.resolve() for p in args.cad_pmx_probe)
        QtCore.QTimer.singleShot(500, lambda: begin(app, window, source, output))
    elif args.cad_workflow_probe:
        from cad_workflow_probe import begin
        source, definition, output = (p.resolve() for p in args.cad_workflow_probe)
        QtCore.QTimer.singleShot(500, lambda: begin(app, window, source, definition, output))
    elif args.pmx_probe:
        from pmx_project import run_probe
        source, output = (path.resolve() for path in args.pmx_probe)
        QtCore.QTimer.singleShot(500, lambda: run_probe(app, window, source, output))
    elif args.editor_probe:
        from editor_probe import begin
        QtCore.QTimer.singleShot(1200, lambda: begin(app, window, args.editor_probe))
    elif args.viewport_probe:
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
        if window.cad_job is not None:
            window.cad_completed.connect(lambda _: QtCore.QTimer.singleShot(500, verify))
        else:
            QtCore.QTimer.singleShot(1200, verify)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

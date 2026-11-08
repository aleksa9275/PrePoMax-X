"""Phase C shell. Widgets and rendering only; original C# owns all model state."""
import argparse
import json
import sys
from pathlib import Path

import clr
for assembly in ['CaeGlobals', 'CaeModel', 'CaeMesh', 'PrePoMax', 'PrePoMaxX.Workbench']:
    clr.AddReference(assembly)
from System import Array, Double, String, Int32, Object, Func, Action
from CaeGlobals import vtkSelectItem, vtkSelectBy, vtkSelectOperation, Selection, SelectionNodeMouse
from PrePoMax import ViewGeometryModelResults
from PrePoMax.Commands import RegenerateTypeEnum
from PrePoMaxX.UI import MaterialEditSession

parser = argparse.ArgumentParser()
parser.add_argument('project', nargs='?')
parser.add_argument('--probe', type=Path)
parser.add_argument('--service-probe', type=Path)
args = parser.parse_args(list(ui_arguments))
controller = session.Controller

if args.service_probe:
    from service_probe import run
    run(session, args.service_probe)
else:
    from PyQt6 import QtCore, QtGui, QtWidgets
    from vtkmodules.vtkRenderingCore import vtkRenderer
    from scene import Scene
    from vtkmodules.vtkCommonCore import vtkVersion
    if vtkVersion.GetVTKVersion() != '9.5.2' or QtCore.PYQT_VERSION_STR != '6.10.0' or QtCore.qVersion() != '6.10.2':
        raise RuntimeError('C1 requires the existing VTK 9.5.2 / PyQt 6.10.0 / Qt 6.10.2 pins')

    class MaterialDialog(QtWidgets.QDialog):
        def __init__(self, parent, name):
            super().__init__(parent)
            self.setWindowTitle('Edit material — ' + name)
            self.resize(680, 490)
            self.draft = MaterialEditSession(controller, name)
            layout = QtWidgets.QVBoxLayout(self)
            form = QtWidgets.QFormLayout()
            self.name = QtWidgets.QLineEdit(self.draft.Name)
            self.description = QtWidgets.QLineEdit(self.draft.Description or '')
            form.addRow('Name', self.name)
            form.addRow('Description', self.description)
            layout.addLayout(form)
            self.pages = QtWidgets.QTabWidget()
            layout.addWidget(self.pages)
            self.entries = {}
            for index, title in enumerate(self.draft.PropertyNames):
                page = QtWidgets.QWidget()
                box = QtWidgets.QVBoxLayout(page)
                if self.draft.ShowProperties(index):
                    props = QtWidgets.QFormLayout()
                    sheet = self.draft.Properties(index)
                    for field in sheet.Fields:
                        if len(field.Choices):
                            edit = QtWidgets.QComboBox()
                            edit.addItems(list(field.Choices))
                            edit.setEditable(not field.Exclusive)
                            edit.setCurrentText(field.Text)
                            edit.setEnabled(not field.ReadOnly)
                        else:
                            edit = QtWidgets.QLineEdit(field.Text)
                            edit.setReadOnly(field.ReadOnly)
                        edit.setToolTip(field.Description)
                        props.addRow(field.Label.strip(), edit)
                        self.entries[(index, field.Name)] = (sheet, edit)
                    box.addLayout(props)
                if self.draft.ShowTable(index):
                    table = QtWidgets.QTableWidget(self.draft.RowCount(index), 0)
                    self._table(index, table)
                    box.addWidget(table)
                box.addStretch()
                self.pages.addTab(page, title)
            self.error = QtWidgets.QLabel()
            self.error.setWordWrap(True)
            self.error.setMinimumHeight(self.error.fontMetrics().height() * 3)
            self.error.setStyleSheet('color: #b83b35')
            layout.addWidget(self.error)
            buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(self.apply)
            buttons.rejected.connect(self.reject)
            layout.addWidget(buttons)

        def _table(self, index, table):
            if not table.rowCount():
                return
            fields = self.draft.Row(index, 0).Fields
            table.setColumnCount(len(fields))
            # The units/equations are converted by the original descriptors.
            table.setHorizontalHeaderLabels([f.Label.replace('[?]', '') for f in fields])
            for row in range(table.rowCount()):
                sheet = self.draft.Row(index, row)
                for col, field in enumerate(sheet.Fields):
                    edit = QtWidgets.QLineEdit(field.Text)
                    edit.setReadOnly(field.ReadOnly)
                    table.setCellWidget(row, col, edit)
                    self.entries[(index, row, field.Name)] = (sheet, edit)
            table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

        def apply(self):
            try:
                for key, (sheet, edit) in self.entries.items():
                    text = edit.currentText() if isinstance(edit, QtWidgets.QComboBox) else edit.text()
                    sheet.Set(key[-1], text)
                self.draft.Name = self.name.text()
                self.draft.Description = self.description.text()
                self.draft.Commit()
                self.accept()
            except Exception as error:
                self.error.setText(str(error).split('   at ')[0])

    class Workbench(QtWidgets.QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle('PrePoMax-X')
            self.resize(1180, 760)
            self.path = None
            self.selected = []
            self.toolbar = self.addToolBar('Project')
            self.actions = {}
            for title, callback in [('Open…', self.choose_open), ('Save', self.save), ('Save As…', self.save_as),
                                    ('Undo', self.undo), ('Redo', self.redo), ('Fit', self.fit)]:
                action = self.toolbar.addAction(title)
                self.actions[title] = action
                action.triggered.connect(lambda checked=False, cb=callback: self.guard(cb))
                if title in ('Save', 'Undo', 'Redo'):
                    action.setShortcut({'Save':'Ctrl+S','Undo':'Ctrl+Z','Redo':'Ctrl+Shift+Z'}[title])
            self.pick_mode = QtWidgets.QComboBox()
            self.pick_mode.addItems(['Pick element', 'Pick face nodes', 'Pick node'])
            self.toolbar.addWidget(self.pick_mode)
            self.view = QtWidgets.QComboBox()
            self.view.addItems(['Model', 'Geometry'])
            self.view.currentTextChanged.connect(lambda value: self.guard(lambda: self.change_view(value)))
            self.toolbar.addWidget(self.view)
            splitter = QtWidgets.QSplitter()
            self.tree = QtWidgets.QTreeWidget()
            self.tree.setHeaderLabel('Model')
            self.tree.itemDoubleClicked.connect(self.edit_item)
            splitter.addWidget(self.tree)
            if sys.platform == 'darwin':
                sys.path.insert(0, str(Path(ui_directory).parent / 'Desktop'))
                from native_cocoa import NativeCocoaView
                self.viewport = NativeCocoaView(self)
                self.viewport.clicked.connect(self.pick)
            else:
                from qt_viewport import NativeQtView
                self.viewport = NativeQtView(self)
                self.viewport.clicked.connect(self.pick)
            splitter.addWidget(self.viewport)
            splitter.setSizes([270, 910])
            self.setCentralWidget(splitter)
            self.renderer = vtkRenderer()
            self.renderer.SetBackground(.93, .95, .98)
            self.viewport.GetRenderWindow().AddRenderer(self.renderer)
            self.scene = Scene(self.renderer)
            self.native_query = session.Presentation.Query
            self.previous_presentation = session.Presentation.Presentation
            self.query_delegate = Func[String, Array[Object], Object](self.query)
            self.presentation_delegate = Action[String, Array[Object]](self.present)
            session.Presentation.Query = self.query_delegate
            session.Presentation.Presentation = self.presentation_delegate
            self.statusBar().showMessage('Open an original PMX project. Double-click a material to edit it.')
            self.dirty = False
            self.actions['Undo'].setEnabled(False)
            self.actions['Redo'].setEnabled(False)

        def query(self, name, arguments):
            camera = self.renderer.GetActiveCamera()
            if name == 'GetViewParameters':
                arguments[0] = Array[Double](camera.GetPosition())
                arguments[1] = Array[Double](camera.GetFocalPoint())
                arguments[2] = Array[Double](camera.GetViewUp())
                arguments[3] = Double(camera.GetParallelScale())
                return None
            if name == 'GetViewPlaneNormal':
                return Array[Double](camera.GetViewPlaneNormal())
            return self.native_query(name, arguments)

        def present(self, name, arguments):
            self.previous_presentation(name, arguments)
            camera = self.renderer.GetActiveCamera()
            if name == 'SetViewParameters':
                camera.SetPosition(*arguments[1])
                camera.SetFocalPoint(*arguments[2])
                camera.SetViewUp(*arguments[3])
                camera.SetParallelScale(float(arguments[4]))
                self.renderer.ResetCameraClippingRange()
                self.render()
            elif name == 'Rotate':
                camera.Azimuth(float(arguments[0]))
                camera.Elevation(float(arguments[1]))
                camera.Roll(float(arguments[2]))
                self.renderer.ResetCameraClippingRange()
                self.render()
            elif name == 'SetZoomToFit':
                self.scene.update(session.Presentation.SceneActors)
                self.fit()

        def guard(self, callback):
            try:
                callback()
            except Exception as error:
                if args.probe:
                    raise
                QtWidgets.QMessageBox.critical(self, 'PrePoMax-X', str(error))

        def confirm_discard(self):
            if not self.dirty:
                return True
            result = QtWidgets.QMessageBox.question(self, 'Save project?', 'Save changes before continuing?',
                QtWidgets.QMessageBox.StandardButton.Save | QtWidgets.QMessageBox.StandardButton.Discard | QtWidgets.QMessageBox.StandardButton.Cancel)
            if result == QtWidgets.QMessageBox.StandardButton.Cancel:
                return False
            if result == QtWidgets.QMessageBox.StandardButton.Save:
                return self.save()
            return True

        def choose_open(self):
            if not self.confirm_discard():
                return
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open project', '', 'PrePoMax project (*.pmx)')
            if path:
                self.open(path)

        def open(self, path):
            session.Open(str(Path(path).resolve()))
            self.path = str(Path(path).resolve())
            self.dirty = False
            # C1 opens the model/geometry; result presentation is connected in C4.
            controller.CurrentView = ViewGeometryModelResults.Model if controller.Model.Mesh is not None else ViewGeometryModelResults.Geometry
            if controller.CurrentView == ViewGeometryModelResults.Model:
                controller.DrawModel(False)
            else:
                controller.DrawGeometry(False)
            self.view.blockSignals(True)
            self.view.setCurrentText('Geometry' if controller.CurrentView == ViewGeometryModelResults.Geometry else 'Model')
            self.view.blockSignals(False)
            self.refresh()
            self.fit()

        def refresh(self):
            self.dirty = controller.ModelChanged
            self.tree.clear()
            model = controller.Model
            for title, values, kind in [('Materials', model.Materials.Keys, 'material'),
                                       ('Parts', (controller.DisplayedMesh.Parts.Keys if controller.DisplayedMesh is not None else []), 'part')]:
                group = QtWidgets.QTreeWidgetItem(self.tree, [title])
                for name in values:
                    item = QtWidgets.QTreeWidgetItem(group, [name])
                    item.setData(0, QtCore.Qt.ItemDataRole.UserRole, kind)
                group.setExpanded(True)
            self.selected = []
            self.scene.update(session.Presentation.SceneActors)
            for name in ['Undo', 'Redo']:
                text = getattr(session.Presentation, name + 'Text')
                self.actions[name].setEnabled(bool(text))
                self.actions[name].setToolTip(str(text or name))
            self.render()
            self.setWindowTitle('PrePoMax-X — ' + (Path(self.path).name if self.path else 'New project') + (' *' if self.dirty else ''))

        def render(self):
            if sys.platform == 'darwin':
                self.viewport.render()
            else:
                self.viewport.GetRenderWindow().Render()

        def fit(self):
            self.renderer.ResetCamera()
            self.renderer.ResetCameraClippingRange()
            self.render()

        def change_view(self, value):
            if not self.path:
                return
            controller.CurrentView = ViewGeometryModelResults.Model if value == 'Model' else ViewGeometryModelResults.Geometry
            if value == 'Model':
                controller.DrawModel(False)
            else:
                controller.DrawGeometry(False)
            self.refresh()

        def edit_item(self, item, column):
            if item.data(0, QtCore.Qt.ItemDataRole.UserRole) == 'material':
                dialog = MaterialDialog(self, item.text(0))
                if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                    self.dirty = True
                    self.refresh()

        def save(self):
            if not self.path:
                return self.save_as()
            controller.SaveToPmxCommand(self.path)
            self.dirty = False
            self.refresh()
            return True

        def save_as(self):
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save project', self.path or '', 'PrePoMax project (*.pmx)')
            if not path:
                return False
            path = path if path.lower().endswith('.pmx') else path + '.pmx'
            controller.SaveToPmxCommand(str(Path(path).resolve()))
            self.path = str(Path(path).resolve())
            self.dirty = False
            self.refresh()
            return True

        def undo(self):
            controller.UndoHistory(RegenerateTypeEnum.All)
            self.dirty = True
            self.refresh()

        def redo(self):
            controller.RedoHistory()
            self.dirty = True
            self.refresh()

        def pick(self, x, y):
            self.guard(lambda: self._pick(x, y))

        def _pick(self, x, y):
            hit = self.scene.pick(x, y)
            if hit is None:
                self.selected = []
                controller.ClearSelectionHistoryAndCallSelectionChanged()
                self.scene.highlight([], False)
                self.render()
                self.statusBar().showMessage('No mesh under the pointer')
                return
            name, point, element = hit
            part_id = controller.DisplayedMesh.Parts[name].PartId
            mode = self.pick_mode.currentIndex()
            select_by = [vtkSelectBy.Element, vtkSelectBy.Surface, vtkSelectBy.Node][mode]
            select_item = vtkSelectItem.Element if mode == 0 else vtkSelectItem.Node
            direction = self.renderer.GetActiveCamera().GetDirectionOfProjection()
            node = SelectionNodeMouse(Array[Double](point), Array[Double](direction), None, False,
                getattr(vtkSelectOperation, 'None'), Array[Int32]([part_id]), None, select_by, 0)
            # Six display pixels converted into world distance at the picked depth.
            self.renderer.SetWorldPoint(*point, 1)
            self.renderer.WorldToDisplay()
            display = self.renderer.GetDisplayPoint()
            self.renderer.SetDisplayPoint(display[0] + 6, display[1], display[2])
            self.renderer.DisplayToWorld()
            world = self.renderer.GetWorldPoint()
            node.Precision = sum((world[i] / world[3] - point[i])**2 for i in range(3))**.5
            selection = Selection()
            selection.CurrentView = int(controller.CurrentView)
            selection.SelectItem = select_item
            selection.Add(node)
            self.selected = list(controller.GetIdsFromSelection(selection))
            controller.Selection = selection
            self.scene.highlight(self.selected, mode != 0)
            self.render()
            self.statusBar().showMessage(f'{name}: {str(select_item)} IDs ' + ', '.join(map(str, self.selected)))

        def closeEvent(self, event):
            if not self.confirm_discard():
                event.ignore()
                return
            self.viewport.Finalize()
            super().closeEvent(event)

    application = QtWidgets.QApplication.instance() or QtWidgets.QApplication(['PrePoMax-X'])
    window = Workbench()
    window.show()
    if sys.platform != 'darwin':
        window.viewport.Initialize()
    if args.project:
        QtCore.QTimer.singleShot(0, lambda: window.guard(lambda: window.open(args.project)))
    if args.probe:
        from gui_probe import start
        start(application, window, MaterialDialog, session, args.probe)
    application.exec()

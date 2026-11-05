"""CAD selection presentation; original C# mesh sets own region membership."""
import subprocess
from PyQt6 import QtCore, QtWidgets
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from vtkmodules.vtkRenderingCore import vtkActor, vtkDataSetMapper

ROLE = QtCore.Qt.ItemDataRole.UserRole + 1


class CadRegions(QtCore.QObject):
    def __init__(self, window, toolbar, jobbar):
        super().__init__(window)
        self.window = window
        self.refs = set()
        self.items = {}
        self.building = False
        self.result = None
        self.view = QtWidgets.QComboBox()
        self.view.setObjectName('cadDocumentView')
        self.view.addItem('Mesh', 'mesh')
        self.view.addItem('CAD geometry', 'cad')
        self.view.addItem('Results', 'results')
        self.view.currentIndexChanged.connect(self.change_view)
        self.view_action = toolbar.addWidget(self.view)
        self.toolbar = QtWidgets.QToolBar('CAD selection', window)
        window.addToolBarBreak()
        window.addToolBar(self.toolbar)
        self.mode = QtWidgets.QComboBox()
        self.mode.setObjectName('cadPickMode')
        self.mode.addItem('Pick faces', 'face')
        self.mode.addItem('Pick parts', 'part')
        self.mode.setToolTip('Click replaces the selection. Ctrl/Command-click adds or removes a region. The tree supports multiple selections.')
        self.mode_action = self.toolbar.addWidget(self.mode)
        self.create = self.toolbar.addAction('Set from CAD…', self.dialog)
        self.clear_action = self.toolbar.addAction('Clear CAD selection', lambda: self.select(set()))
        self.label = QtWidgets.QLabel()
        self.label_action = self.toolbar.addWidget(self.label)
        self.mapper = vtkDataSetMapper()
        self.mapper.SetResolveCoincidentTopologyToPolygonOffset()
        self.mapper.SetRelativeCoincidentTopologyPolygonOffsetParameters(-2, -2)
        self.actor = vtkActor()
        self.actor.SetMapper(self.mapper)
        self.actor.GetProperty().SetColor(1, .55, .05)
        self.actor.GetProperty().SetOpacity(.6)
        self.actor.GetProperty().LightingOff()
        self.actor.PickableOff()
        self.actor.VisibilityOff()
        window.renderer.AddActor(self.actor)
        window.model_tree.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        window.model_tree.itemSelectionChanged.connect(self.tree_changed)
        self.refresh()

    @property
    def available(self):
        return self.window.cad_mesh is not None and self.window.model_scene is not None

    def reset(self):
        self.refs.clear()
        self.items.clear()
        self.result = None
        self.actor.VisibilityOff()

    def refresh(self):
        available = self.available
        busy = self.window.busy
        self.toolbar.setVisible(available)
        for action in (self.view_action, self.mode_action, self.create, self.clear_action, self.label_action):
            action.setVisible(available)
        self.view.setEnabled(available and not busy)
        self.mode.setEnabled(available and not busy)
        self.create.setEnabled(available and not busy and bool(self.refs))
        self.clear_action.setEnabled(available and not busy and bool(self.refs))
        self.label.setText(f'{len(self.refs)} CAD region' + ('' if len(self.refs) == 1 else 's') + ' selected')
        self.view.model().item(2).setEnabled(self.result is not None)
        scene = self.window.scene or {}
        key = 'cad' if 'cad' in scene else 'results' if 'fields' in scene else 'mesh'
        self.window.field_action.setVisible(not available or key == 'results')
        with QtCore.QSignalBlocker(self.view):
            self.view.setCurrentIndex(self.view.findData(key))

    def on_scene(self):
        w = self.window
        if self.available and 'fields' in w.scene:
            mesh = w.model_scene
            if ({n['id'] for n in mesh['nodes']} == {n['id'] for n in w.scene['nodes']} and
                {e['id']: e['nodeIds'] for e in mesh['elements']} ==
                    {e['id']: e['nodeIds'] for e in w.scene['elements']}):
                self.result = (w.scene, w.current_path)
        self.highlight()
        self.refresh()

    def change_view(self, index):
        if not self.available or self.window.busy:
            self.refresh()
            return
        w = self.window
        key = self.view.itemData(index)
        if key == 'cad':
            scene, path = w.cad_document.scene, w.cad_document.source
        elif key == 'mesh':
            scene, path = w.model_scene, w.model_path
        elif self.result is not None:
            scene, path = self.result
        else:
            self.refresh()
            return
        w.show_scene(scene, path)
        w.update_model_tree()
        w.job_state(w.job.state)

    def sources(self, kind, refs=None):
        if not self.available or kind not in ('node', 'element'):
            raise ValueError('Open a native CAD mesh before creating a region set.')
        refs = self.refs if refs is None else refs
        if not refs or len(refs) > 256:
            raise ValueError('Choose between 1 and 256 CAD regions.')
        parts = {p['id']: p for p in self.window.cad_mesh.scene['cadMesh']['parts']}
        names = set()
        for entity, part_id, entity_id in refs:
            part = parts.get(part_id)
            if part is None:
                raise ValueError('Selected CAD part is not in the current mesh.')
            if entity == 'face' and kind == 'node' and entity_id in part['faceIds']:
                names.add(f'PART_{part_id}_FACE_{entity_id}')
            elif entity == 'part' and entity_id == 0:
                if kind == 'node':
                    names.add(f'PART_{part_id}_NODES')
                else:
                    names.update(f'PART_{part_id}_SOLID_{d}' for d in part['domains'])
            else:
                raise ValueError('Faces create node sets; element sets require whole parts. Unmapped regions cannot be used.')
        if len(names) > 256:
            raise ValueError('Choose at most 256 source mesh sets.')
        return sorted(names)

    def begin_tree(self):
        self.building = True
        self.items = {}

    def decorate(self, item, ref):
        if not self.available:
            return
        try:
            self.sources('node', {ref})
        except ValueError:
            return
        item.setData(0, ROLE, ref)
        self.items[ref] = item

    def end_tree(self):
        for ref, item in self.items.items():
            item.setSelected(ref in self.refs)
            if ref in self.refs:
                parent = item.parent()
                while parent is not None:
                    parent.setExpanded(True)
                    parent = parent.parent()
        self.building = False

    def tree_changed(self):
        if self.building or not self.available or self.window.busy:
            return
        refs = {tuple(item.data(0, ROLE)) for item in self.window.model_tree.selectedItems()
                if item.data(0, ROLE) is not None}
        if len(refs) > 256:
            self.window.statusBar().showMessage('Choose at most 256 CAD regions.')
            self.select(self.refs)
            return
        self.refs = refs
        self.highlight()
        self.refresh()

    def select(self, refs):
        self.refs = set(refs)
        with QtCore.QSignalBlocker(self.window.model_tree):
            self.window.model_tree.clearSelection()
            for ref in self.refs:
                if ref in self.items:
                    self.items[ref].setSelected(True)
        self.highlight()
        self.refresh()

    def picked(self, part_id, face_id):
        entity = self.mode.currentData()
        ref = (entity, part_id, face_id if entity == 'face' else 0)
        if ref not in self.items or self.window.busy:
            return False
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        multiple = bool(modifiers & (QtCore.Qt.KeyboardModifier.ControlModifier | QtCore.Qt.KeyboardModifier.MetaModifier))
        refs = self.refs ^ {ref} if multiple else {ref}
        if len(refs) > 256:
            return False
        self.select(refs)
        item = self.items[ref]
        self.window.model_tree.setCurrentItem(item, 0, QtCore.QItemSelectionModel.SelectionFlag.NoUpdate)
        item.parent().setExpanded(True)
        self.window.model_tree.scrollToItem(item)
        return True

    def highlight(self):
        w = self.window
        self.actor.VisibilityOff()
        if self.available and w.scene and 'cad' in w.scene and self.refs:
            grid = vtkUnstructuredGrid()
            grid.SetPoints(w.grid.GetPoints())
            for i, element in enumerate(w.scene['elements']):
                part, face = element['sourcePartId'], element['sourceFaceId']
                if ('part', part, 0) in self.refs or ('face', part, face) in self.refs:
                    grid.InsertNextCell(w.grid.GetCellType(i), w.grid.GetCell(i).GetPointIds())
            self.mapper.SetInputData(grid)
            self.actor.SetVisibility(grid.GetNumberOfCells() > 0)
        if w.isVisible():
            w.vtk.render()

    def dialog(self):
        if not self.available or self.window.busy or not self.refs:
            return
        dialog = QtWidgets.QDialog(self.window)
        dialog.setWindowTitle('Create set from CAD selection')
        form = QtWidgets.QFormLayout(dialog)
        kind = QtWidgets.QComboBox()
        kind.addItem('Node set — supports and nodal loads', 'node')
        if all(ref[0] == 'part' for ref in self.refs):
            kind.addItem('Element set — solid sections', 'element')
        name = QtWidgets.QLineEdit()
        name.setMaxLength(80)
        message = QtWidgets.QLabel()
        form.addRow('Selection', QtWidgets.QLabel(', '.join(f'{r[0]} {r[2] or r[1]} (part {r[1]})' for r in sorted(self.refs))))
        form.addRow('Kind', kind)
        form.addRow('Name', name)
        form.addRow(message)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        form.addRow(buttons)
        buttons.rejected.connect(dialog.reject)
        def apply():
            try:
                self.window.add_cad_region_set(kind.currentData(), name.text().strip())
            except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
                message.setText(str(error))
            else:
                dialog.accept()
        buttons.accepted.connect(apply)
        dialog.exec()

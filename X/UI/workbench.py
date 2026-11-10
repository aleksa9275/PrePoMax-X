"""Phase C shell. Widgets and rendering only; original C# owns all model state."""
import argparse
import json
import sys
from pathlib import Path

import clr
for assembly in ['CaeGlobals', 'CaeModel', 'CaeMesh', 'PrePoMax', 'PrePoMaxX.Workbench']:
    clr.AddReference(assembly)
from System import Array, Double, String, Int32, Object, Func, Action, Boolean
from CaeGlobals import vtkSelectItem, vtkSelectBy, vtkSelectOperation, Selection, SelectionNodeMouse
from PrePoMax import ViewGeometryModelResults
from PrePoMax.Commands import RegenerateTypeEnum
from PrePoMaxX.UI import MaterialEditSession

parser = argparse.ArgumentParser()
parser.add_argument('project', nargs='?')
parser.add_argument('--probe', type=Path)
parser.add_argument('--service-probe', type=Path)
parser.add_argument('--authoring-service-probe', type=Path)
parser.add_argument('--authoring-probe', type=Path)
parser.add_argument('--native-tools', type=Path)
parser.add_argument('--geometry-service-probe', type=Path)
parser.add_argument('--geometry-probe', type=Path)
parser.add_argument('--cad-fixture', type=Path)
parser.add_argument('--solver-registry',type=Path)
parser.add_argument('--solver-id')
parser.add_argument('--solver-directory',type=Path)
parser.add_argument('--results-service-probe',type=Path)
parser.add_argument('--results-probe',type=Path)
parser.add_argument('--application-service-probe',type=Path)
parser.add_argument('--application-probe',type=Path)
parser.add_argument('--menu-probe',type=Path)
parser.add_argument('--elements-probe',type=Path)
parser.add_argument('--menu-model',type=Path)
parser.add_argument('--menu-results',type=Path)
parser.add_argument('--settings',type=Path)
parser.add_argument('--check-3mf',action='store_true')
args = parser.parse_args(list(ui_arguments))
controller = session.Controller
if args.native_tools:
    from PrePoMax import NativeTools
    NativeTools.Configure(str(args.native_tools.resolve()))

if any([args.solver_registry,args.solver_id,args.solver_directory]):
    if not all([args.solver_registry,args.solver_id,args.solver_directory]):raise ValueError('Supply the complete explicit solver profile.')
    from PrePoMaxX.UI import ResultsSession
    ResultsSession(session).ConfigureSolver(str(args.solver_registry.resolve()),args.solver_id,str(args.solver_directory.resolve()))

if args.application_service_probe:
    from application_probe import run
    run(session,args.application_service_probe)
elif args.results_service_probe:
    from results_probe import run
    run(session,args.results_service_probe)
elif args.geometry_service_probe:
    from geometry_probe import run
    run(session,args.geometry_service_probe,args.cad_fixture)
elif args.authoring_service_probe:
    from authoring_probe import run
    run(session,args.authoring_service_probe)
elif args.service_probe:
    from service_probe import run
    run(session, args.service_probe)
else:
    from PyQt6 import QtCore, QtGui, QtWidgets
    from vtkmodules.vtkRenderingCore import vtkRenderer
    from scene import Scene
    from vtkmodules.vtkCommonCore import vtkVersion
    if vtkVersion.GetVTKVersion() != '9.5.2' or QtCore.PYQT_VERSION_STR != '6.10.0' or QtCore.qVersion() != '6.10.2':
        raise RuntimeError('C1 requires the existing VTK 9.5.2 / PyQt 6.10.0 / Qt 6.10.2 pins')

    from authoring_widgets import MaterialDialog, PropertyDialog, MultiPropertyDialog, ParametersDialog
    from PrePoMaxX.UI import AuthoringSession, GeometrySession
    from geometry_widgets import GeometryDialog
    from operation_dispatch import Dispatcher
    from CaeGlobals import MessageBoxes, MessageBoxModeEnum
    from System.Windows.Forms import IWin32Window, MessageBoxButtons, MessageBoxIcon, DialogResult

    from geometry_workbench import GeometryWorkbench

    from results_workbench import ResultsWorkbench
    from application_workbench import ApplicationWorkbench
    from main_menu import MainMenuWorkbench
    from main_toolbars import OriginalToolbarsWorkbench
    from model_tree import OriginalModelTreeWorkbench
    from output_links import OutputLinksWorkbench

    class Workbench(MainMenuWorkbench,OriginalToolbarsWorkbench,OriginalModelTreeWorkbench,OutputLinksWorkbench,ApplicationWorkbench,ResultsWorkbench,GeometryWorkbench,QtWidgets.QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle('PrePoMax-X')
            self.resize(1180, 760)
            self.path = None
            self.controller = controller
            self.session=session
            self.authoring = AuthoringSession(controller)
            self.geometry = GeometrySession(controller)
            self.dispatcher = Dispatcher()
            self.operation_task = None
            self.last_pick_point = None
            self.active_editor = None
            self.selected = []
            self.toolbar = self.addToolBar('Project')
            self.actions = {}
            for title, callback in [('New…', self.new_project), ('Import mesh…', self.import_mesh), ('Import CAD…', self.import_cad), ('Open…', self.choose_open), ('Save', self.save), ('Save As…', self.save_as),
                                    ('Undo', self.undo), ('Redo', self.redo), ('Fit', self.fit)]:
                action = self.toolbar.addAction(title)
                self.actions[title] = action
                action.triggered.connect(lambda checked=False, cb=callback: self.guard(cb))
                if title in ('Save', 'Undo', 'Redo'):
                    action.setShortcut({'Save':'Ctrl+S','Undo':'Ctrl+Z','Redo':'Ctrl+Shift+Z'}[title])
            self.pick_mode = QtWidgets.QComboBox()
            self.pick_mode.addItems(['Pick element', 'Pick face nodes', 'Pick node', 'Pick surface', 'Pick part','Pick geometry','Pick geometry vertex','Pick geometry edge','Pick geometry surface','Pick geometry part'])
            self.pick_mode.addItems(['Pick edge nodes','Pick nodes by edge angle','Pick nodes by surface angle','Pick geometry edges by angle','Pick geometry surfaces by angle'])
            self.addToolBarBreak()
            self.viewport_toolbar=self.addToolBar('Viewport')
            self.viewport_toolbar.addWidget(self.pick_mode)
            self.selection_angle=QtWidgets.QDoubleSpinBox();self.selection_angle.setRange(0,180);self.selection_angle.setValue(30);self.selection_angle.setSuffix('°');self.selection_angle.setMaximumWidth(90);self.viewport_toolbar.addWidget(self.selection_angle)
            self.box_select=QtWidgets.QCheckBox('Box select');self.box_select.toggled.connect(lambda value:setattr(self.viewport,'box_selection',value));self.viewport_toolbar.addWidget(self.box_select)
            self.view = QtWidgets.QComboBox()
            self.view.addItems(['Model', 'Geometry'])
            self.view.currentTextChanged.connect(lambda value: self.guard(lambda: self.change_view(value)))
            self.viewport_toolbar.addWidget(self.view)
            self.element_edges=QtWidgets.QCheckBox('Element edges')
            self.element_edges.toggled.connect(lambda checked:self.refresh())
            self.viewport_toolbar.addWidget(self.element_edges)
            splitter = QtWidgets.QSplitter()
            self.tree = QtWidgets.QTreeWidget()
            self.tree.setHeaderLabel('Model')
            self.tree.itemDoubleClicked.connect(self.edit_item)
            self.tree.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
            self.tree.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
            self.tree.customContextMenuRequested.connect(self.tree_menu)
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
            from area_selection import AreaSelectionFilter
            self.area_selection_filter=AreaSelectionFilter(self.viewport)
            self.viewport.area_selected.connect(lambda *rect:self.guard(lambda:self.area_pick(*rect)))
            splitter.addWidget(self.viewport)
            splitter.setSizes([270, 910])
            self.setCentralWidget(splitter)
            self.renderer = vtkRenderer()
            self.renderer.SetBackground(.93, .95, .98)
            self.viewport.GetRenderWindow().AddRenderer(self.renderer)
            self.scene = Scene(self.renderer)
            self.scene.volume_provider=controller.GetVolumeGridData
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
            self.prompt_delegate=Func[IWin32Window,String,String,MessageBoxButtons,MessageBoxIcon,DialogResult](self.prompt)
            MessageBoxes.InteractivePresenter=self.prompt_delegate
            MessageBoxes.Mode=MessageBoxModeEnum.Interactive
            self.build_geometry_menus()
            self.build_results_ui()
            self.preferences_path=args.settings.resolve() if args.settings else None
            self.build_application_ui()
            self.build_original_menus()
            self.build_original_toolbars()
            self.build_original_tree()
            self.build_output_links()
            if self.preferences_path and self.preferences_path.is_file():self.application.LoadPreferences(str(self.preferences_path));self.apply_preferences()
            self.screenshot_delegate=Action[String,Boolean,Int32](lambda path,transparent,scale:self.dispatcher.call(lambda:self.capture(path,transparent,scale)))
            session.Presentation.Screenshot=self.screenshot_delegate
            from CaeGlobals import UnitSystemType
            self.result_units_delegate=Func[UnitSystemType](lambda:self.dispatcher.call(self.select_result_units))
            session.Presentation.ResultUnitsSelector=self.result_units_delegate
            self.refresh()
            if controller.AutomationSettings.StartWithApplication:self.guard(self.start_automation)

        def query(self, name, arguments):
            if name in ['GetViewParameters','GetViewPlaneNormal','GetFileNameToOpen','GetFileNameToSaveAs','EditMeshingParametersFromHistory']:
                return self.dispatcher.call(lambda:self.ui_query(name,arguments))
            return self.native_query(name,arguments)

        def ui_query(self,name,arguments):
            camera = self.renderer.GetActiveCamera()
            if name=='EditMeshingParametersFromHistory':
                from PrePoMaxX.UI import MeshHistoryEditSession
                from application_widgets import SheetDialog
                edit=MeshHistoryEditSession(controller,arguments[0]);dialog=SheetDialog(self,'Edit mesh setup during regeneration',edit.Properties,edit.Apply);return edit.Result if dialog.exec() else None
            if name=='GetFileNameToOpen':
                original=str(arguments[1]) if len(arguments)>1 else 'All files|*.*';parts=original.split('|');filters=';;'.join(parts[i]+' ('+parts[i+1]+')' for i in range(0,len(parts)-1,2))
                path,_=QtWidgets.QFileDialog.getOpenFileName(self,str(arguments[0]),'',filters);return path or None
            if name=='GetFileNameToSaveAs':
                path,_=QtWidgets.QFileDialog.getSaveFileName(self,'Save project',self.path or '', 'PrePoMax (*.pmx)');return path or None
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
            self.previous_presentation(name,arguments)
            self.dispatcher.post(lambda:self.ui_present(name,arguments))

        def ui_present(self,name,arguments):
            if name in ['WriteDataToOutput','WriteErrorToOutput']:
                self.write_output(arguments[0],name=='WriteErrorToOutput')
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
            elif name=='UpdateArrowWidgetAnimationData':
                self.scene.presentation.update_annotation(*arguments)
            elif name=='ApplyFollowerView':
                self.apply_follower(*arguments)
            elif name=='UpdateFollowerView':
                self.update_follower()
            elif name=='RemoveFollowerView':
                self.follower_nodes=None
            elif name=='SetPendingSidePanelsState' and hasattr(self,'plot_panel'):
                self.restore_panel_state(arguments[0])
            elif name=='SetStateWorking' and hasattr(self,'application'):
                self.set_application_busy(True)
            elif name=='SetStateReady' and hasattr(self,'application'):
                self.set_application_busy(False)
            elif name == 'SetZoomToFit':
                if self.operation_task is not None:
                    self.pending_fit=True;return
                self.scene.update(session.Presentation.SceneActors,session.Presentation.RenderCommands)
                self.fit()

        def guard(self, callback):
            try:
                callback()
            except Exception as error:
                if args.probe or args.authoring_probe or args.geometry_probe or args.results_probe or args.application_probe or args.menu_probe or args.elements_probe:
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
            if controller.ResultsInitialized:
                controller.CurrentView=ViewGeometryModelResults.Results
                controller.DrawResults(False)
            elif controller.Model.Mesh is not None:
                controller.CurrentView=ViewGeometryModelResults.Model;controller.DrawModel(False)
            else:
                controller.CurrentView=ViewGeometryModelResults.Geometry;controller.DrawGeometry(False)
            self.refresh()
            self.fit()

        def refresh(self):
            self.update_results_ui()
            self.dirty = controller.ModelChanged
            self.view.blockSignals(True)
            self.view.setCurrentText(str(controller.CurrentView))
            self.view.blockSignals(False)
            expanded={item.data(0,QtCore.Qt.ItemDataRole.UserRole+1):item.isExpanded() for item in self.walk_tree()}
            selected_keys={i.data(0,QtCore.Qt.ItemDataRole.UserRole+1) for i in self.tree.selectedItems()}
            self.tree.blockSignals(True)
            self.tree.clear()
            # Original ModelTree tabs, layout, images (model_tree.py).
            self.populate_original_tree(expanded,selected_keys)
            self.sync_tree_tab()
            self.tree.blockSignals(False)
            self.selected = []
            self.scene.element_edges=self.element_edges.isChecked() and controller.CurrentView!=ViewGeometryModelResults.Geometry
            self.scene.update(session.Presentation.SceneActors,session.Presentation.RenderCommands)
            self.apply_edge_mode()
            self.apply_view_widgets()
            if hasattr(self,'original_top'):self.update_original_menu_state()
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
            controller.CurrentView = getattr(ViewGeometryModelResults,value)
            if value == 'Results':
                controller.DrawResults(False)
            elif value == 'Model':
                controller.DrawModel(False)
            else:
                controller.DrawGeometry(False)
            self.refresh()

        def walk_tree(self):
            def children(parent):
                for index in range(parent.childCount()):
                    item=parent.child(index)
                    yield item
                    yield from children(item)
            return children(self.tree.invisibleRootItem())

        def prompt(self,owner,text,caption,buttons,icon):
            return self.dispatcher.call(lambda:self.ui_prompt(owner,text,caption,buttons,icon))

        def ui_prompt(self,owner,text,caption,buttons,icon):
            # The original unattended-thread policy runs before this UI boundary.
            mapping={str(MessageBoxButtons.OK):[('OK',DialogResult.OK)],
                     str(MessageBoxButtons.OKCancel):[('OK',DialogResult.OK),('Cancel',DialogResult.Cancel)],
                     str(MessageBoxButtons.YesNo):[('Yes',DialogResult.Yes),('No',DialogResult.No)],
                     str(MessageBoxButtons.YesNoCancel):[('Yes',DialogResult.Yes),('No',DialogResult.No),('Cancel',DialogResult.Cancel)]}
            box=QtWidgets.QMessageBox(self)
            box.setWindowTitle(caption or 'PrePoMax-X')
            box.setText(text)
            choices=mapping.get(str(buttons))
            if choices is None:raise ValueError('Unhandled original prompt buttons: '+str(buttons))
            answers={}
            for label,value in choices:
                role=QtWidgets.QMessageBox.ButtonRole.RejectRole if label in ['Cancel','No'] else QtWidgets.QMessageBox.ButtonRole.AcceptRole
                button=box.addButton(label,role);answers[button]=value
            box.exec()
            return answers.get(box.clickedButton(),DialogResult.Cancel)

        def new_project(self):
            if not self.confirm_discard():return
            values=self.select_model_properties()
            if values is None:return
            controller.New()
            controller.SetNewModelPropertiesCommand(*values)
            self.path=None;self.refresh()

        def select_model_properties(self):
            from CaeModel import ModelSpaceEnum
            from CaeGlobals import UnitSystemType
            from System import Enum
            dialog=QtWidgets.QDialog(self);dialog.setWindowTitle('New model')
            layout=QtWidgets.QFormLayout(dialog)
            spaces=QtWidgets.QComboBox();spaces.addItems([str(v) for v in Enum.GetValues(ModelSpaceEnum)])
            spaces.setCurrentText('ThreeD')
            units=QtWidgets.QComboBox();units.addItems([str(v) for v in Enum.GetValues(UnitSystemType) if str(v)!='Undefined'])
            units.setCurrentText('MM_TON_S_C')
            layout.addRow('Model space',spaces);layout.addRow('Units',units)
            buttons=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok|QtWidgets.QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);layout.addRow(buttons)
            if dialog.exec()!=QtWidgets.QDialog.DialogCode.Accepted:return None
            return Enum.Parse(ModelSpaceEnum,spaces.currentText()),Enum.Parse(UnitSystemType,units.currentText())

        def import_mesh(self):
            path,_=QtWidgets.QFileDialog.getOpenFileName(self,'Import mesh','','Mesh (*.inp *.unv *.vol *.mesh *.obj)')
            if path:self.import_path(path,False)

        def import_cad(self):
            path,_=QtWidgets.QFileDialog.getOpenFileName(self,'Import geometry','','Geometry (*.brep *.step *.stp *.iges *.igs *.stl)')
            if path:self.import_path(path,True)

        def import_path(self,path,geometry=True):
            if str(controller.Model.Properties.ModelSpace)=='Undefined' or str(controller.Model.UnitSystem.UnitSystemType)=='Undefined':
                values=self.select_model_properties()
                if values is None:return
                controller.SetNewModelPropertiesCommand(*values)
            def done():
                value=str(controller.CurrentView)
                self.view.setCurrentText(value)
                self.change_view(value);self.fit()
            self.run_operation(self.geometry.Import(str(Path(path).resolve())),done)

        def edit_item(self,item,column=0):
            entry=item.data(0,QtCore.Qt.ItemDataRole.UserRole)
            if entry is None:return
            if entry.Family in ['Result field components','Result history fields','Result history components']:
                self.guard(lambda:self.open_result_leaf(entry));return
            if entry.Family in ['Jobs','Result fields','Result histories','Result reference points','Result coordinate systems']:
                if entry.Family=='Result fields' and not entry.Group and not any(f.Name==entry.Name for f in controller.GetResultFieldOutputs()):
                    self.result_boxes['Field'].setCurrentText(entry.Name);return
                if entry.Family=='Result histories' and not entry.Group and not any(f.Name==entry.Name for f in controller.GetResultHistoryOutputs()):
                    self.guard(lambda:self.history_data(entry.Name));return
                self.guard(lambda:self.edit_results(entry.Family,None if entry.Group else entry.Name));return
            if entry.Family=='Result parts':
                if not entry.Group:self.guard(lambda:self.edit_geometry('Parts',entry.Name))
                return
            if entry.Group and entry.FolderId:
                item.setExpanded(not item.isExpanded());return
            if entry.Group:
                if entry.Family=='Mesh setup':self.guard(lambda:self.edit_geometry('Mesh setup'))
                elif entry.Family not in ['Parts','Geometry parts']:self.guard(lambda:self.edit_definition(entry.Family,entry.Step,None))
            elif entry.Family in ['Parts','Geometry parts','Mesh setup']:
                self.guard(lambda:self.edit_geometry(entry.Family,entry.Name))
            elif entry.Family!='Parts':
                self.guard(lambda:self.edit_definition(entry.Family,entry.Step,entry.Name))

        def edit_definition(self,family,step=None,name=None):
            if self.active_editor is not None:
                self.active_editor.raise_();self.active_editor.activateWindow();return
            if family=='Materials':dialog=MaterialDialog(self,name)
            elif family in ['Surface interactions','Solution controls']:dialog=MultiPropertyDialog(self,name,family,step)
            elif family=='Parameters':dialog=ParametersDialog(self)
            else:dialog=PropertyDialog(self,family,step,name)
            self.show_editor(dialog,family)

        def show_editor(self,dialog,family):
            self.active_editor=dialog
            for menu in self.geometry_menus:menu.setEnabled(False)
            for title,action in self.actions.items():
                if title!='Fit':action.setEnabled(False)
            self.tree.setEnabled(False);self.view.setEnabled(False)
            self.result_toolbar.setEnabled(False);self.animation_toolbar.setEnabled(False);self.symbols.setEnabled(False)
            if family=='Parameters':self.viewport.setEnabled(False);self.pick_mode.setEnabled(False)
            def finish(result):
                self.active_editor=None
                for menu in self.geometry_menus:menu.setEnabled(True)
                for action in self.actions.values():action.setEnabled(True)
                self.tree.setEnabled(True);self.view.setEnabled(True);self.viewport.setEnabled(True);self.pick_mode.setEnabled(True)
                self.result_toolbar.setEnabled(True);self.animation_toolbar.setEnabled(True);self.symbols.setEnabled(True)
                self.refresh()
                dialog.deleteLater()
            dialog.finished.connect(finish)
            dialog.show()

        def tree_menu(self,position):
            item=self.tree.itemAt(position)
            if item is None:return
            entry=item.data(0,QtCore.Qt.ItemDataRole.UserRole)
            if entry is None:return
            if entry.Family in ['Result field components','Result history fields','Result history components']:
                self.results_leaf_menu(entry,position);return
            if entry.Family in ['Geometry parts','Mesh setup','Parts']:
                return self.geometry_tree_menu(entry,position)
            if entry.Family in ['Jobs','Result fields','Result histories','Result parts','Result reference points','Result coordinate systems']:
                self.results_tree_menu(entry);return
            menu=QtWidgets.QMenu(self)
            actions={}
            if entry.Family!='Parts':
                action=menu.addAction('Create…' if entry.Group else 'Edit…')
                actions[action]=lambda:self.edit_definition(entry.Family,entry.Step,None if entry.Group else entry.Name)
            if not entry.Group and entry.Family in list(self.authoring.Families)+list(self.authoring.StepFamilies):
                names=[i.data(0,QtCore.Qt.ItemDataRole.UserRole).Name for i in self.tree.selectedItems() if i.data(0,QtCore.Qt.ItemDataRole.UserRole).Family==entry.Family and i.data(0,QtCore.Qt.ItemDataRole.UserRole).Step==entry.Step]
                if not names:names=[entry.Name]
                for title,method in [('Duplicate',self.authoring.Duplicate),('Remove',self.authoring.Remove)]:
                    action=menu.addAction(title)
                    actions[action]=lambda m=method,n=names:m(entry.Family,entry.Step,Array[String](n))
                if entry.Family in ['Steps','Constraints','Contact pairs','Initial conditions']+list(self.authoring.StepFamilies):
                    for title,active in [('Activate',True),('Deactivate',False)]:
                        action=menu.addAction(title)
                        actions[action]=lambda value=active,n=names:self.authoring.Activate(entry.Family,entry.Step,Array[String](n),value)
            self.add_model_tree_actions(menu,actions,entry)
            if self.authoring.CanOrganize(entry.Family,entry.Step):
                action=menu.addAction('New folder…')
                def new_folder():
                    text,ok=QtWidgets.QInputDialog.getText(self,'New folder','Name')
                    if ok:self.authoring.CreateFolder(entry.Family,entry.Step,text,Array[String]([] if entry.Group else [entry.Name]),entry.FolderId)
                actions[action]=new_folder
                if entry.FolderId:
                    action=menu.addAction('Rename folder…')
                    def rename_folder():
                        text,ok=QtWidgets.QInputDialog.getText(self,'Rename folder','Name',text=entry.Name)
                        if ok:self.authoring.RenameFolder(entry.Family,entry.Step,entry.FolderId,text)
                    actions[action]=rename_folder
                    action=menu.addAction('Ungroup')
                    actions[action]=lambda:self.authoring.RemoveFolder(entry.Family,entry.Step,entry.FolderId)
                elif not entry.Group:
                    targets=[('Collection root',None)]+[(i.text(0),i.data(0,QtCore.Qt.ItemDataRole.UserRole).FolderId) for i in self.walk_tree() if i.data(0,QtCore.Qt.ItemDataRole.UserRole).Family==entry.Family and i.data(0,QtCore.Qt.ItemDataRole.UserRole).Step==entry.Step and i.data(0,QtCore.Qt.ItemDataRole.UserRole).FolderId]
                    action=menu.addAction('Move to folder…')
                    def move_folder():
                        text,ok=QtWidgets.QInputDialog.getItem(self,'Move to folder','Folder',[t[0] for t in targets],editable=False)
                        if ok:self.authoring.MoveToFolder(entry.Family,entry.Step,Array[String]([entry.Name]),next(t[1] for t in targets if t[0]==text))
                    actions[action]=move_folder
            if not entry.Group and (self.authoring.CanOrganize(entry.Family,entry.Step) or entry.Family=='Steps'):
                for title,offset in [('Move up',-1),('Move down',1)]:
                    action=menu.addAction(title)
                    actions[action]=lambda value=offset:self.authoring.Move(entry.Family,entry.Step,entry.Name,value)
            chosen=menu.exec(self.tree.viewport().mapToGlobal(position))
            if chosen in actions:
                self.guard(actions[chosen]);self.refresh()

        def save(self):
            if not self.path:
                return self.save_as()
            self.capture_panel_state()
            controller.SaveToPmxCommand(self.path)
            self.dirty = False
            self.refresh()
            return True

        def save_as(self):
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save project', self.path or '', 'PrePoMax project (*.pmx)')
            if not path:
                return False
            path = path if path.lower().endswith('.pmx') else path + '.pmx'
            self.capture_panel_state()
            controller.SaveToPmxCommand(str(Path(path).resolve()))
            self.path = str(Path(path).resolve())
            self.dirty = False
            self.refresh()
            return True

        def undo(self):
            if self.geometry.HasGeometryHistory or self.results.HasBackgroundHistory:
                return self.run_operation(self.geometry.Undo())
            controller.UndoHistory(RegenerateTypeEnum.All)
            self.dirty = True
            self.refresh()

        def redo(self):
            if self.geometry.HasGeometryHistory or self.results.HasBackgroundHistory:
                return self.run_operation(self.geometry.Redo())
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
                self.scene.show_selection([])
                self.render()
                self.statusBar().showMessage('No mesh under the pointer')
                return
            name, point, element = hit
            part_id = controller.DisplayedMesh.Parts[name].PartId
            mode = self.pick_mode.currentIndex()
            select_by = [vtkSelectBy.Element, vtkSelectBy.Surface, vtkSelectBy.Node, vtkSelectBy.Surface, vtkSelectBy.Part,vtkSelectBy.Geometry,vtkSelectBy.GeometryVertex,vtkSelectBy.GeometryEdge,vtkSelectBy.GeometrySurface,vtkSelectBy.GeometryPart,vtkSelectBy.Edge,vtkSelectBy.EdgeAngle,vtkSelectBy.SurfaceAngle,vtkSelectBy.GeometryEdgeAngle,vtkSelectBy.GeometrySurfaceAngle][mode]
            select_item = [vtkSelectItem.Element,vtkSelectItem.Node,vtkSelectItem.Node,vtkSelectItem.Surface,vtkSelectItem.Part,vtkSelectItem.Geometry,vtkSelectItem.Geometry,vtkSelectItem.GeometryEdge,vtkSelectItem.GeometrySurface,vtkSelectItem.Part,vtkSelectItem.Node,vtkSelectItem.Node,vtkSelectItem.Node,vtkSelectItem.GeometryEdge,vtkSelectItem.GeometrySurface][mode]
            self.last_pick_point=point
            modifiers=QtWidgets.QApplication.keyboardModifiers()
            shift=bool(modifiers & QtCore.Qt.KeyboardModifier.ShiftModifier)
            control=bool(modifiers & (QtCore.Qt.KeyboardModifier.ControlModifier|QtCore.Qt.KeyboardModifier.MetaModifier))
            operation=vtkSelectOperation.Intersect if shift and control else vtkSelectOperation.Add if shift else vtkSelectOperation.Subtract if control else getattr(vtkSelectOperation,'None')
            direction = self.renderer.GetActiveCamera().GetDirectionOfProjection()
            node = SelectionNodeMouse(Array[Double](point), Array[Double](direction), None, False,
                operation, Array[Int32]([part_id]), None, select_by, self.selection_angle.value())
            # Six display pixels converted into world distance at the picked depth.
            self.renderer.SetWorldPoint(*point, 1)
            self.renderer.WorldToDisplay()
            display = self.renderer.GetDisplayPoint()
            self.renderer.SetDisplayPoint(display[0] + 6, display[1], display[2])
            self.renderer.DisplayToWorld()
            world = self.renderer.GetWorldPoint()
            node.Precision = sum((world[i] / world[3] - point[i])**2 for i in range(3))**.5
            selection = controller.Selection.DeepCopy(True,False) if (shift or control) and controller.Selection.SelectItem==select_item else Selection()
            selection.CurrentView = int(controller.CurrentView)
            selection.SelectItem = select_item
            selection.Add(node)
            self.selected = list(controller.GetIdsFromSelection(selection))
            controller.Selection = selection
            controller.HighlightSelection()
            self.scene.show_selection(session.Presentation.SelectionActors)
            self.render()
            self.statusBar().showMessage(f'{name}: {str(select_item)} IDs ' + ', '.join(map(str, self.selected)))

        def closeEvent(self, event):
            if self.operation_task is not None or (hasattr(self,'application') and self.application.Automation.GetDispatcher().GetRunningCall() is not None):
                self.statusBar().showMessage('Wait for the active operation or stop it before closing.');event.ignore();return
            self.stop_animation(False)
            if not self.confirm_discard():
                event.ignore()
                return
            self.persist_preferences()
            self.application.Dispose()
            self.session.Presentation.IsDisposed=True
            self.viewport.Finalize()
            super().closeEvent(event)

    application = QtWidgets.QApplication.instance() or QtWidgets.QApplication(['PrePoMax-X'])
    # RuntimeInitialization.SetCultureAndLanguage: invariant culture without group separator.
    invariant=QtCore.QLocale.c();invariant.setNumberOptions(QtCore.QLocale.NumberOption.OmitGroupSeparator);QtCore.QLocale.setDefault(invariant)
    splash=None
    if not any([args.probe,args.authoring_probe,args.geometry_probe,args.results_probe,args.application_probe,args.menu_probe,args.elements_probe]):
        original_splash=Path(ui_directory).parents[1]/'PrePoMax/Resources/Splash_01.png'
        if original_splash.is_file():
            splash=QtWidgets.QSplashScreen(QtGui.QPixmap(str(original_splash)));splash.showMessage('Loading PrePoMax-X…',QtCore.Qt.AlignmentFlag.AlignBottom|QtCore.Qt.AlignmentFlag.AlignHCenter,QtGui.QColor('black'));splash.show();application.processEvents()
    window = Workbench()
    window.show()
    if splash:splash.finish(window)
    if sys.platform != 'darwin':
        window.viewport.Initialize()
    if args.project:
        QtCore.QTimer.singleShot(0, lambda: window.guard(lambda: window.open(args.project)))
    if args.probe:
        from gui_probe import start
        start(application, window, MaterialDialog, session, args.probe)
    if args.authoring_probe:
        from authoring_gui_probe import start
        start(application,window,args.authoring_probe)
    if args.geometry_probe:
        from geometry_gui_probe import start
        start(application,window,args.geometry_probe,args.cad_fixture)
    if args.results_probe:
        from results_gui_probe import start
        start(application,window,args.results_probe)
    if args.application_probe:
        from application_gui_probe import start
        start(application,window,args.application_probe,args.check_3mf)
    if args.elements_probe:
        from elements_gui_probe import start
        start(application,window,args.elements_probe)
    if args.menu_probe:
        from menu_gui_probe import start
        start(application,window,args.menu_probe,str(args.menu_model.resolve()),str(args.menu_results.resolve()) if args.menu_results else None)
    application.exec()

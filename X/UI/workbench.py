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
parser.add_argument('--forms-probe',type=Path)
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
    from vtkControl.Native import VtkNativeLibrary
    # The view is the original vtkControl on vtkNative (M1); no Python VTK is loaded into this process: its Cocoa
    # view classes would clash with those of VTK 9.7.1
    if VtkNativeLibrary.GetVtkVersion() != '9.7.1' or QtCore.PYQT_VERSION_STR != '6.10.0' or QtCore.qVersion() != '6.10.2':
        raise RuntimeError('The desktop requires vtkNative on VTK 9.7.1 and the PyQt 6.10.0 / Qt 6.10.2 pins')

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
    from original_form_host import OriginalFormHostWorkbench

    class Workbench(OriginalFormHostWorkbench,MainMenuWorkbench,OriginalToolbarsWorkbench,OriginalModelTreeWorkbench,OutputLinksWorkbench,ApplicationWorkbench,ResultsWorkbench,GeometryWorkbench,QtWidgets.QMainWindow):
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
            self.pick_mode.currentIndexChanged.connect(lambda index:self.guard(self.apply_pick_mode))
            self.view = QtWidgets.QComboBox()
            self.view.addItems(['Model', 'Geometry'])
            self.view.currentTextChanged.connect(lambda value: self.guard(lambda: self.change_view(value)))
            self.viewport_toolbar.addWidget(self.view)
            self.element_edges=QtWidgets.QCheckBox('Element edges')
            self.element_edges.toggled.connect(lambda checked:self.guard(lambda:self.set_edge_mode('Element edges' if checked else 'Model edges')))
            self.viewport_toolbar.addWidget(self.element_edges)
            splitter = QtWidgets.QSplitter()
            self.tree = QtWidgets.QTreeWidget()
            self.tree.setHeaderLabel('Model')
            self.tree.itemDoubleClicked.connect(self.edit_item)
            self.tree.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
            self.tree.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
            self.tree.customContextMenuRequested.connect(self.tree_menu)
            splitter.addWidget(self.tree)
            from original_viewport import OriginalViewport
            self.viewport = OriginalViewport(self, self.dispatcher.post)
            self.vtk = self.viewport.control
            # FrmMain constructor: the view asks the controller for its data, the picks go to the selection
            self.viewport.host.Attach(session.Presentation)
            from System.Windows.Forms import MouseEventArgs, Keys
            self.selection_delegate = Action[Array[Double], Array[Double], Array[Array[Double]], Boolean, vtkSelectOperation, Array[String]](
                lambda *a: self.view_callback(lambda: self.vtk_select_point_or_area(*a)))
            self.vtk.OnMouseLeftButtonUpSelection += self.selection_delegate
            self.actors_picked_delegate = Action[MouseEventArgs, Keys, Array[String]](
                lambda e, keys, names: self.view_callback(lambda: self.select_base_parts(e, keys, names)))
            self.vtk.Controller_ActorsPicked = self.actors_picked_delegate
            splitter.addWidget(self.viewport)
            splitter.setSizes([270, 910])
            self.setCentralWidget(splitter)
            # FrmMain adds vtkControl to its controls in the constructor; its window (and Load) exist before the
            # settings are applied, so the native window is created here, not at the first show
            self.viewport.attach()
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
            self.build_original_forms()
            if self.preferences_path and self.preferences_path.is_file():self.application.LoadPreferences(str(self.preferences_path));self.apply_preferences()
            self.screenshot_delegate=Action[String,Boolean,Int32](lambda path,transparent,scale:self.dispatcher.call(lambda:self.capture(path,transparent,scale)))
            session.Presentation.Screenshot=self.screenshot_delegate
            from CaeGlobals import UnitSystemType
            self.result_units_delegate=Func[UnitSystemType](lambda:self.dispatcher.call(self.select_result_units))
            session.Presentation.ResultUnitsSelector=self.result_units_delegate
            self.refresh()
            if controller.AutomationSettings.StartWithApplication:self.guard(self.start_automation)

        def query(self, name, arguments):
            if name in ['GetFileNameToOpen','GetFileNameToSaveAs','EditMeshingParametersFromHistory']:
                return self.dispatcher.call(lambda:self.ui_query(name,arguments))
            return self.native_query(name,arguments)

        def ui_query(self,name,arguments):
            if name=='EditMeshingParametersFromHistory':
                from PrePoMaxX.UI import MeshHistoryEditSession
                from application_widgets import SheetDialog
                edit=MeshHistoryEditSession(controller,arguments[0]);dialog=SheetDialog(self,'Edit mesh setup during regeneration',edit.Properties,edit.Apply);return edit.Result if dialog.exec() else None
            if name=='GetFileNameToOpen':
                original=str(arguments[1]) if len(arguments)>1 else 'All files|*.*';parts=original.split('|');filters=';;'.join(parts[i]+' ('+parts[i+1]+')' for i in range(0,len(parts)-1,2))
                path,_=QtWidgets.QFileDialog.getOpenFileName(self,str(arguments[0]),'',filters);return path or None
            if name=='GetFileNameToSaveAs':
                path,_=QtWidgets.QFileDialog.getSaveFileName(self,'Save project',self.path or '', 'PrePoMax (*.pmx)');return path or None
            return self.native_query(name, arguments)

        def present(self, name, arguments):
            self.previous_presentation(name,arguments)
            self.dispatcher.post(lambda:self.ui_present(name,arguments))

        def ui_present(self,name,arguments):
            if name in ('SelectionChanged','UpdateHighlight','CloseAllForms','UpdateAnalysisProgress'):
                self.form_presentation(name,arguments)
            if name in ['WriteDataToOutput','WriteErrorToOutput']:
                self.write_output(arguments[0],name=='WriteErrorToOutput')
            # The view calls (camera, sections, patterns, animation frames, annotations, follower view, zoom) are
            # the original FrmMain's, in OriginalViewHost; the toolkit mirrors only its own controls
            if name=='SetAnimationFrameData':
                self.animation_scene_stale=True
            elif name=='UpdateUnitSystem' and hasattr(self,'update_unit_system'):
                self.update_unit_system()
            elif name=='SetAnimationFrame' and hasattr(self,'show_original_animation_frame'):
                self.show_original_animation_frame(*arguments)
            elif name in ('SaveAnimationAsImages','SaveAnimationAsAVI'):
                pass
            elif name in ('ApplyFollowerView','UpdateFollowerView','RemoveFollowerView','CreateSectionView','UpdateSectionView','RemoveSectionView'):
                self.update_view_buttons()
            if name=='SetPendingSidePanelsState' and hasattr(self,'plot_panel'):
                self.restore_panel_state(arguments[0])
            elif name=='SetStateWorking' and hasattr(self,'application'):
                self.set_application_busy(True)
            elif name=='SetStateReady' and hasattr(self,'application'):
                self.set_application_busy(False)

        def guard(self, callback):
            try:
                callback()
            except Exception as error:
                if args.probe or args.authoring_probe or args.geometry_probe or args.results_probe or args.application_probe or args.menu_probe or args.elements_probe or args.forms_probe:
                    raise
                QtWidgets.QMessageBox.critical(self, 'PrePoMax-X', str(error))

        def view_callback(self, callback):
            """A vtkControl event handler. The native view's callback swallows an exception raised through it, so a
            probe's error is kept here and raised again by the probe after the gesture (view_probe.py)."""
            try:
                self.guard(callback)
            except Exception as error:
                self.view_callback_errors = getattr(self, 'view_callback_errors', []) + [error]

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
            # The edge buttons follow the edge visibility of the current view (Controller.CurrentEdgesVisibility)
            self.element_edges.blockSignals(True);self.element_edges.setChecked(str(controller.CurrentEdgesVisibility)=='ElementEdges');self.element_edges.blockSignals(False)
            self.apply_view_widgets()
            if hasattr(self,'original_top'):self.update_original_menu_state()
            for name in ['Undo', 'Redo']:
                text = getattr(session.Presentation, name + 'Text')
                self.actions[name].setEnabled(bool(text))
                self.actions[name].setToolTip(str(text or name))
            self.render()
            self.setWindowTitle('PrePoMax-X — ' + (Path(self.path).name if self.path else 'New project') + (' *' if self.dirty else ''))

        def update_view_buttons(self):
            """The section view and follower view buttons the original view members check (tsbSectionView, tsbFollowerView)."""
            host=self.viewport.host
            for attribute,checked in (('section_view_action',host.SectionViewChecked),('follower_view_action',host.FollowerViewChecked)):
                action=getattr(self,attribute,None)
                if action is not None:action.setChecked(bool(checked))

        def render(self):
            """Draws the scene of the original view now (vtkControl paints on Invalidate)."""
            if self.viewport.attached:self.viewport.control.NativeHost.Refresh()

        def fit(self):
            """tsmiZoomToFit_Click: vtkControl.SetZoomToFit."""
            if self.viewport.attached:self.vtk.SetZoomToFit(False)

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
            if getattr(self,'auto_prompts',None) is not None:
                # Probe capture: original message text recorded, the first (affirmative) answer returned.
                self.auto_prompts.append(str(text))
                first={str(MessageBoxButtons.OK):DialogResult.OK,str(MessageBoxButtons.OKCancel):DialogResult.OK,
                       str(MessageBoxButtons.YesNo):DialogResult.Yes,str(MessageBoxButtons.YesNoCancel):DialogResult.Yes}
                return getattr(self,'auto_prompt_answer',None) or first[str(buttons)]
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
            # FrmMain.New with undefined properties: the modal original FrmNewModel, then a new model.
            if not self.in_ui_context(lambda:self.form_host.SelectNewModel(True)):return
            controller.New()
            self.in_ui_context(self.form_host.ApplyNewModelProperties)
            self.path=None;self.refresh()

        def import_mesh(self):
            path,_=QtWidgets.QFileDialog.getOpenFileName(self,'Import mesh','','Mesh (*.inp *.unv *.vol *.mesh *.obj)')
            if path:self.import_path(path,False)

        def import_cad(self):
            path,_=QtWidgets.QFileDialog.getOpenFileName(self,'Import geometry','','Geometry (*.brep *.step *.stp *.iges *.igs *.stl)')
            if path:self.import_path(path,True)

        def import_path(self,path,geometry=True):
            # FrmMain.ImportFile: IfNeededSelectAndSetNewModelProperties (original FrmNewModel, modal).
            self.in_ui_context(lambda:self.form_host.Invoke('IfNeededSelectAndSetNewModelProperties'))
            if str(controller.Model.Properties.ModelSpace)=='Undefined' or str(controller.Model.UnitSystem.UnitSystemType)=='Undefined':return
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
            # Original form compiled whole (C9): FrmMain create/edit entry point.
            if self.open_original(family,step,name):return
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

        # Pick modes of the toolbar as the original selection modes (Controller.SelectBy / SelectItem): a pick in the
        # view then selects through FrmMain._vtk_SelectPointOrArea, as the original forms make it select
        PICK_MODES=[('Element','Element'),('Surface','Node'),('Node','Node'),('Surface','Surface'),('Part','Part'),
                    ('Geometry','Geometry'),('GeometryVertex','Geometry'),('GeometryEdge','GeometryEdge'),
                    ('GeometrySurface','GeometrySurface'),('GeometryPart','Part'),('Edge','Node'),('EdgeAngle','Node'),
                    ('SurfaceAngle','Node'),('GeometryEdgeAngle','GeometryEdge'),('GeometrySurfaceAngle','GeometrySurface')]

        def apply_pick_mode(self):
            if self.original_form_open():return
            by,item=self.PICK_MODES[self.pick_mode.currentIndex()]
            controller.SelectBy=getattr(vtkSelectBy,by);controller.SelectItem=getattr(vtkSelectItem,item)
            controller.SetSelectAngle(self.selection_angle.value())

        def vtk_select_point_or_area(self, point, direction, planes, completely_inside, operation, part_names):
            """vtkControl.OnMouseLeftButtonUpSelection -> FrmMain._vtk_SelectPointOrArea (original_form_host.py)."""
            self.selection_events=getattr(self,'selection_events',0)+1
            if point is not None:self.last_pick_point=list(point)
            # An area pick has planes and no point or direction (vtkControl.OnMouseLeftButtonUpSelection)
            self.original_pick(None if point is None else list(point), None if direction is None else list(direction),
                               None if planes is None else [list(p) for p in planes], bool(completely_inside), operation,
                               None if part_names is None else [str(n) for n in part_names])
            self.statusBar().showMessage('Selected IDs: ' + ', '.join(map(str, self.selected)))

        def select_base_parts(self, e, keys, names):
            """vtkControl.Controller_ActorsPicked -> FrmMain.SelectBaseParts: a click on a part selects it in the tree
            (double click on empty space zooms to fit, a click there clears the selection)."""
            names=[str(n) for n in names] if names is not None else None
            if not names or names[0] in (None,'None'):
                if e.Clicks==2:self.fit()
                elif not (int(keys) & (int(__import__('System.Windows.Forms',fromlist=['Keys']).Keys.Shift)|int(__import__('System.Windows.Forms',fromlist=['Keys']).Keys.Control))):
                    controller.ClearAllSelection();self.tree.clearSelection()
                return
            items=[i for i in self.walk_tree() if not i.data(0,QtCore.Qt.ItemDataRole.UserRole).Group and str(i.text(0)) in names]
            if not items:return
            additive=bool(int(keys) & int(__import__('System.Windows.Forms',fromlist=['Keys']).Keys.Shift))
            if not additive:self.tree.clearSelection()
            for item in items:item.setSelected(True)
            self.tree.setCurrentItem(items[-1])

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
            self.viewport.detach()
            super().closeEvent(event)

    application = QtWidgets.QApplication.instance() or QtWidgets.QApplication(['PrePoMax-X'])
    # RuntimeInitialization.SetCultureAndLanguage: invariant culture without group separator.
    invariant=QtCore.QLocale.c();invariant.setNumberOptions(QtCore.QLocale.NumberOption.OmitGroupSeparator);QtCore.QLocale.setDefault(invariant)
    splash=None
    if not any([args.probe,args.authoring_probe,args.geometry_probe,args.results_probe,args.application_probe,args.menu_probe,args.elements_probe,args.forms_probe]):
        original_splash=Path(ui_directory).parents[1]/'PrePoMax/Resources/Splash_01.png'
        if original_splash.is_file():
            splash=QtWidgets.QSplashScreen(QtGui.QPixmap(str(original_splash)));splash.showMessage('Loading PrePoMax-X…',QtCore.Qt.AlignmentFlag.AlignBottom|QtCore.Qt.AlignmentFlag.AlignHCenter,QtGui.QColor('black'));splash.show();application.processEvents()
    window = Workbench()
    window.show()
    if splash:splash.finish(window)
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
    if args.forms_probe:
        from forms_gui_probe import start
        start(application,window,args.forms_probe)
    if args.menu_probe:
        from menu_gui_probe import start
        start(application,window,args.menu_probe,str(args.menu_model.resolve()),str(args.menu_results.resolve()) if args.menu_results else None)
    application.exec()

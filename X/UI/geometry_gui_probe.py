"""Real Qt/native-VTK CAD picking, authored mesh setup and asynchronous meshing."""
import json
import time
import traceback
from pathlib import Path
from PyQt6 import QtCore, QtWidgets, QtTest
from System import Array, String
from PrePoMax import ViewGeometryModelResults


def start(app,window,output,fixture=None):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    fixture=Path(fixture) if fixture else Path(__file__).parent/'fixtures/cube.brep'
    report={'success':False,'checks':[],'scope':'local native Qt/VTK workflow; synthetic input; not four-target acceptance'}
    state={};started=time.monotonic()
    def check(name,value):
        if not value:raise AssertionError(name)
        report['checks'].append(name)
    def wait():
        if window.operation_task is not None:return False
        if window.operation_error:raise AssertionError(window.operation_error)
        return True
    def field(dialog,name):return next(f for f in dialog.rule.Properties.Fields if f.Name==name)
    def choose(dialog,name,text):
        f=field(dialog,name);widget=dialog.entries[name][1]
        widget.setCurrentText(next(v for v in f.Choices if text in v))
        dialog.panel.commit_field(f,widget);app.processEvents()
    def click_part():
        camera=window.renderer.GetActiveCamera();camera.SetPosition(35,5,5);camera.SetFocalPoint(5,5,5);camera.SetViewUp(0,0,1);window.fit()
        window.raise_();window.activateWindow();QtTest.QTest.qWait(100)
        window.renderer.SetWorldPoint(10,5,5,1);window.renderer.WorldToDisplay();x,y,_=window.renderer.GetDisplayPoint()
        scale=window.viewport.devicePixelRatioF();qx,qy=x/scale,window.viewport.height()-y/scale
        if __import__('sys').platform=='darwin':
            from viewport_probe import CocoaEvents
            events=CocoaEvents(window.viewport);events.height=window.viewport.height();events.send(1,qx,qy);events.send(2,qx,qy)
        else:QtTest.QTest.mouseClick(window.viewport,QtCore.Qt.MouseButton.LeftButton,pos=QtCore.QPoint(round(qx),round(qy)))
        app.processEvents()
    def import_cad():
        from CaeModel import ModelSpaceEnum
        from CaeGlobals import UnitSystemType
        window.controller.SetNewModelPropertiesCommand(ModelSpaceEnum.ThreeD,UnitSystemType.MM_TON_S_C)
        window.import_path(str(fixture.resolve()),True)
        check('CAD import runs with document controls locked',window.operation_task is not None and not window.tree.isEnabled())
    def import_ready():
        if not wait():return False
        window.undo()
    def import_undone():
        if not wait():return False
        check('CAD import undo leaves empty geometry',len(window.controller.Model.Geometry.Parts)==0)
        window.redo()
        check('CAD import redo stays asynchronous with empty geometry',window.operation_task is not None and not window.tree.isEnabled())
    def sizing():
        if not wait():return False
        check('native CAD imported into geometry tree',window.controller.CurrentView==ViewGeometryModelResults.Geometry and len(window.scene.actors)>0 and any(i.data(0,QtCore.Qt.ItemDataRole.UserRole).Family=='Geometry parts' and not i.data(0,QtCore.Qt.ItemDataRole.UserRole).Group for i in window.walk_tree()))
        from System import Array,Double
        from System.Drawing import Color
        window.controller.CreateSectionView(Array[Double]([5,5,5]),Array[Double]([1,0,0]),True,Color.Empty,False,True);window.refresh()
        report['cadCapData']=[{'name':str(a.Data.Name),'representation':str(a.Data.ActorRepresentation),'volumeCells':bool(a.Data.HasVolumeCells),'section':bool(a.Data.SectionViewPossible)} for a in window.session.Presentation.SceneActors]
        report['cadCuts']=[{'cells':a.GetMapper().GetInput().GetNumberOfCells(),'type':a.GetMapper().GetInput().GetClassName()} for a in window.scene.presentation.features.cuts]
        check('closed CAD section cap rendered without volume cells',any(a.GetMapper().GetInput().GetNumberOfCells()>0 and a.GetMapper().GetInput().GetCell(0).GetCellDimension()==2 for a in window.scene.presentation.features.cuts))
        window.controller.RemoveSectionView(False);window.refresh()
        # Original FrmMeshSetupItem compiled whole (C9), opened through FrmMain.CreateMeshSetupItem.
        from form_driver import FormDriver
        forms=FormDriver(window);state['forms']=forms
        window.edit_geometry('Mesh setup')
        check('original FrmMeshSetupItem offers all ten meshing types',type(forms.form).__name__=='FrmMeshSetupItem' and len(forms.types)==10)
        report['meshSetupTypes']=forms.types
        forms.select_type(forms.types[0])
        forms.set_choice('AdvancedView','Advanced');forms.set_choice('Relative','Absolute')
        forms.set_choice('SecondOrder','No')
        forms.set('Name','GUI_Sizing');forms.set('MaxH','4')
        check('FrmSelectItemSet shown for the region selection',forms.host.SelectItemSetForm.Visible)
        click_part()
        check('native pointer picks the original CAD part through Controller.SelectPointOrArea',len(window.selected)==1)
        check('mesh setup form records the pick (FrmMeshSetupItem.SelectionChanged)',forms.form.MeshSetupItem.CreationIds is not None and len(forms.form.MeshSetupItem.CreationIds)==1)
        forms.ok()
        check('original OnApply adds the setup and hides the form',forms.form is None and window.controller.GetMeshSetupItem('GUI_Sizing') is not None)
    def tetra():
        if not wait():return False
        forms=state['forms']
        check('sizing form committed original object',window.controller.GetMeshSetupItem('GUI_Sizing').MaxH==4 and window.active_editor is None)
        window.edit_geometry('Mesh setup')
        forms.select_type('Tetrahedral Gmsh')
        forms.set('Name','GUI_Tetrahedra');click_part();forms.ok()
    def mesh():
        if not wait():return False
        check('second mesher widget records original setup',len(window.controller.GetMeshSetupItemNames())==2)
        window.run_operation(window.geometry.Execute('Create mesh',Array[String](list(window.controller.GetGeometryPartNames()))),lambda:window.view.setCurrentText('Model'))
        check('native meshing leaves event loop responsive',window.operation_task is not None and window.cancel_operation.isVisible())
    def mesh_done():
        if not wait():return False
        c=window.controller
        check('generated solid mesh displayed in model view',len(c.Model.Mesh.Elements)>0 and c.CurrentView==ViewGeometryModelResults.Model and len(window.scene.actors)>0)
        check('native mesher output reaches output panel','elements' in window.output.toPlainText().lower())
        check('operation completion restores controls',window.tree.isEnabled() and window.actions['Open…'].isEnabled())
        window.element_edges.setChecked(True);app.processEvents()
        check('original element face edges rendered',len(window.scene.element_edge_actors)>0 and window.scene.element_edge_actors[0].GetMapper().GetInput().GetNumberOfCells()>12)
        state['elements']=len(c.Model.Mesh.Elements)
        part=next(iter(c.Model.Mesh.Parts.Values));state['part']=part.Name;state['minx']=part.BoundingBox.MinX
        item=next(i for i in window.walk_tree() if i.data(0,QtCore.Qt.ItemDataRole.UserRole).Family=='Parts' and not i.data(0,QtCore.Qt.ItemDataRole.UserRole).Group)
        window.tree.setCurrentItem(item)
        window.edit_geometry('Translate')
        forms=state['forms']
        check('original FrmTranslate opened through FrmMain.TranslateModelParts',type(forms.form).__name__=='FrmTranslate')
        forms.set('X2','2');forms.ok()
    def moved():
        if not wait():return False
        c=window.controller
        check('mesh transform widget uses original command',c.Model.Mesh.Parts[state['part']].BoundingBox.MinX==state['minx']+2)
        # Undo runs through the same background path as the application buttons.
        window.undo()
    def undone():
        if not wait():return False
        c=window.controller
        check('GUI transform undo preserves mesh',c.Model.Mesh.Parts[state['part']].BoundingBox.MinX==state['minx'] and len(c.Model.Mesh.Elements)==state['elements'])
        window.redo()
    def redone():
        if not wait():return False
        c=window.controller
        check('GUI transform redo',c.Model.Mesh.Parts[state['part']].BoundingBox.MinX==state['minx']+2)
        window.path=str(output/'gui-meshed.pmx');window.save()
        window.open(window.path)
        check('GUI PMX preserves CAD setup and mesh',len(c.Model.Geometry.Parts)==1 and len(c.GetMeshSetupItemNames())==2 and len(c.Model.Mesh.Elements)==state['elements'])
        window.raise_();window.activateWindow();QtTest.QTest.qWait(150)
        check('meshed CAD window captured',window.screen().grabWindow(0,window.x(),window.y(),window.width(),window.height()).save(str(output/'meshed.png')))
        report.update(elements=state['elements'],nodes=len(c.Model.Mesh.Nodes),project=window.path)
    def compound_tree():
        """Original ModelTree rules for the cells of a split CAD part: rename, Group Cells, Fuse Bodies."""
        import model_tree
        from System import Int32
        from CaeModel import ModelSpaceEnum
        from CaeGlobals import UnitSystemType,Selection,SelectionNodeIds,vtkSelectItem,vtkSelectOperation
        c=window.controller
        c.New();c.SetNewModelPropertiesCommand(ModelSpaceEnum.ThreeD,UnitSystemType.MM_TON_S_C);c.ImportFileCommand(str(fixture.resolve()),False)
        c.CurrentView=ViewGeometryModelResults.Geometry
        part=next(iter(c.Model.Geometry.Parts.Values));original=str(part.Name)
        split=window.geometry.Edit('Split solid');split.Select(1)
        for key,value in [('X','6'),('Nx','1'),('Ny','0'),('Nz','0')]:split.Properties.Set(key,value)
        selection=Selection();selection.CurrentView=int(c.CurrentView);selection.SelectItem=vtkSelectItem.Part
        selection.Add(SelectionNodeIds(getattr(vtkSelectOperation,'None'),False,Array[Int32]([part.PartId])))
        split.SetSelection(Array[Int32]([part.PartId]),selection,'');split.Commit();window.refresh();app.processEvents()
        def compound_item():
            return next((i for i in window.walk_tree() if type(getattr(i.data(0,QtCore.Qt.ItemDataRole.UserRole),'Item',None)).__name__=='CompoundGeometryPart'),None)
        item=compound_item()
        check('split part shown as the part it was cut from with its cells',item is not None and item.text(0)==original and item.childCount()==2)
        cells=[item.child(i) for i in range(2)]
        visible,_=window.prepare_tree_menu(cells)
        check('two cells: Fuse Bodies offered, Group Cells not (whole sub part)',visible['tsmiFuseBodies'] and not visible['tsmiGroupSplitCells'])
        visible,_=window.prepare_tree_menu([cells[0]])
        check('one cell: Group Cells offered, Fuse Bodies not',visible['tsmiGroupSplitCells'] and not visible['tsmiFuseBodies'])
        visible,_=window.prepare_tree_menu([item])
        check('split compound row stands for all its cells (Fuse Bodies)',visible['tsmiFuseBodies'])
        check('split compound row is renameable as the part',window.can_rename_entry(item.data(0,QtCore.Qt.ItemDataRole.UserRole)))
        window.rename_node(item.data(0,QtCore.Qt.ItemDataRole.UserRole),'Body')
        compound=next(p for p in c.Model.Geometry.Parts.Values if type(p).__name__=='CompoundGeometryPart')
        check('compound row rename renames the split sub part (RenameSplitSubPartCommand)',str(compound.GetSingleSplitSubPartName())=='Body' and compound_item().text(0)=='Body')
        cell=str(compound_item().child(0).data(0,QtCore.Qt.ItemDataRole.UserRole).Name)
        window.tree_action('tsmiGroupSplitCells',[compound_item().child(0)]);app.processEvents()
        compound=next(p for p in c.Model.Geometry.Parts.Values if type(p).__name__=='CompoundGeometryPart')
        selected=[i.data(0,QtCore.Qt.ItemDataRole.UserRole) for i in window.tree.selectedItems()]
        report['groupedSubParts']=[str(n) for n in compound.CellSubPartNames]
        check('tree Group Cells runs GroupSplitCellsCommand and selects the new sub part',len(set(report['groupedSubParts']))==2 and len(selected)==1)
        item=compound_item();cells=[item.child(i) for i in range(item.childCount())]
        window.tree_action('tsmiFuseBodies',cells);app.processEvents()
        parts=[p for p in c.Model.Geometry.Parts.Values if not p.Internal]
        report['fusedParts']=[str(p.Name)+':'+type(p).__name__ for p in parts]
        check('tree Fuse Bodies runs FuseBodiesCommand',not any(type(p).__name__=='CompoundGeometryPart' and len(p.SubPartNames)>1 for p in parts))
        report.update(success=True)
    steps=iter([import_cad,import_ready,import_undone,sizing,tetra,mesh,mesh_done,moved,undone,redone,compound_tree]);current=[None]
    timer=QtCore.QTimer(window)
    def tick():
        try:
            if time.monotonic()-started>120:raise TimeoutError('GUI native operation timed out')
            if current[0] is None:current[0]=next(steps)
            if current[0]() is not False:current[0]=None
        except StopIteration:
            timer.stop();finish()
        except Exception as error:
            report.update(error=str(error),traceback=traceback.format_exc());timer.stop();finish()
    def finish():
        (output/'geometry-gui.json').write_text(json.dumps(report,indent=2)+'\n')
        window.dirty=False
        # Finalize using the normal UI close path; a task timeout is still a failure.
        if window.operation_task is not None:window.geometry.Cancel()
        window.close();app.exit(0 if report['success'] else 1)
    timer.timeout.connect(tick);timer.start(50)

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
    from view_probe import ViewProbe
    view=ViewProbe(app,window)
    def click_part(world=(10,5,5)):
        view.look((35,5,5),(5,5,5),(0,0,1))
        window.raise_();window.activateWindow();QtTest.QTest.qWait(100)
        view.click(*view.to_widget(world))
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
        check('native CAD imported into geometry tree',window.controller.CurrentView==ViewGeometryModelResults.Geometry and len(view.actor_names())>0 and any(i.data(0,QtCore.Qt.ItemDataRole.UserRole).Family=='Geometry parts' and not i.data(0,QtCore.Qt.ItemDataRole.UserRole).Group for i in window.walk_tree()))
        from System import Array,Double
        from System.Drawing import Color
        # Looking at the cut from the removed side: the cap of the closed CAD part fills the section
        view.look((35,5,5),(5,5,5),(0,0,1))
        whole=view.colored_pixels(output/'cad-whole.png')
        window.controller.CreateSectionView(Array[Double]([5,5,5]),Array[Double]([1,0,0]),True,Color.Empty,False,True);window.refresh()
        report['cadSection']={'names':view.actor_names(),'pixels':[whole,view.colored_pixels(output/'cad-section.png')],
                              'pictureChanged':(output/'cad-whole.png').read_bytes()!=(output/'cad-section.png').read_bytes()}
        check('closed CAD section cap rendered without volume cells',window.viewport.host.SectionViewChecked and report['cadSection']['pictureChanged']
              and report['cadSection']['pixels'][1]>0.5*whole)
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
        check('generated solid mesh displayed in model view',len(c.Model.Mesh.Elements)>0 and c.CurrentView==ViewGeometryModelResults.Model and len(view.actor_names())>0)
        check('native mesher output reaches output panel','elements' in window.output.toPlainText().lower())
        check('operation completion restores controls',window.tree.isEnabled() and window.actions['Open…'].isEnabled())
        window.set_edge_mode('Model edges');window.fit();model_edges=view.dark_pixels(output/'mesh-model-edges.png')
        window.element_edges.setChecked(True);app.processEvents()
        report['meshEdges']=[model_edges,view.dark_pixels(output/'mesh-element-edges.png')]
        check('original element face edges rendered',str(window.vtk.EdgesVisibility)=='ElementEdges' and report['meshEdges'][1]>report['meshEdges'][0])
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
    # Beam elements (C12): the free edges of a CAD shell are LinearBeamElements (VisFileReader); a second-order
    # Netgen mesh of the shell converts its edge segments to ParabolicBeamElements (FeMesh.LinearToParabolic);
    # both become the part's edges (FeMesh.ConvertLineFeElementsToEdges), 2- and 3-node edge cells.
    def element_types(mesh,part):
        import collections
        return dict(collections.Counter(type(mesh.Elements[i]).__name__ for i in part.Labels))
    def beam_import():
        from CaeModel import ModelSpaceEnum
        from CaeGlobals import UnitSystemType
        c=window.controller
        c.New();c.SetNewModelPropertiesCommand(ModelSpaceEnum.ThreeD,UnitSystemType.MM_TON_S_C);window.refresh()
        window.import_path(str(fixture.resolve()),True)
    def beam_delete_face():
        if not wait():return False
        from form_driver import FormDriver
        c=window.controller
        part=next(iter(c.Model.Geometry.Parts.Values));state['beamPart']=str(part.Name)
        report['beamSolid']={'partType':str(part.PartType),'elements':element_types(c.Model.Geometry,part)}
        forms=FormDriver(window);state['forms']=forms
        window.geometry_tool('DeleteCadFaces')
        check('Delete Faces opens the original FrmSurfaceOperation',type(forms.form).__name__=='FrmSurfaceOperation' and str(forms.form.Text)=='Delete Faces')
        click_part((10,5,5))
        report['beamFacePick']={'selected':list(window.selected),'item':str(c.Selection.SelectItem)}
        check('the +X face of the cube picked for deletion',len(window.selected)==1)
        state['promptsStart']=len(forms.prompts)
        forms.ok()
        report['beamDeleteForm']={'visible':forms.form is not None,'prompts':list(forms.prompts)[state['promptsStart']:],'task':window.operation_task is not None}
    def beam_deleted():
        if not wait():return False
        # The original OnApplyAsync awaits SurfaceOperationCommandAsync and then hides the form.
        form=state['forms'].form
        if form is not None and form.Visible:return False
        c=window.controller
        part=c.Model.Geometry.Parts[state['beamPart']]
        types=element_types(c.Model.Geometry,part)
        cells=[len(e) for e in part.Visualization.EdgeCells]
        report['beamDeleteOutput']=window.output.toPlainText()[-600:]
        report['beamShell']={'partType':str(part.PartType),'elements':types,'edgeCellNodes':sorted(set(cells)),'edgeCells':len(cells)}
        check('Delete Faces leaves an open CAD shell (DeleteCadFaces)',str(part.PartType)=='Shell')
        # VisFileReader makes a LinearBeamElement of every free triangle side on a CAD edge; FeMesh turns the 1D
        # elements into the part's edge cells and drops them (ConvertLineFeElementsToEdges), so the free edges are
        # the evidence: edge cells bounded by a single triangle exist only through those beam elements.
        sides={}
        for i in part.Labels:
            n=list(c.Model.Geometry.Elements[i].NodeIds)
            for a,b in ((n[0],n[1]),(n[1],n[2]),(n[2],n[0])):sides[frozenset((a,b))]=sides.get(frozenset((a,b)),0)+1
        free=[e for e in part.Visualization.EdgeCells if sides.get(frozenset(list(e)),0)==1]
        report['beamShell'].update(freeEdgeCells=len(free))
        check('the shell boundary is drawn from LinearBeamElements: 2-node free edge cells (VisFileReader, ConvertLineFeElementsToEdges)',
              len(free)>=4 and set(cells)=={2})
        forms=state['forms']
        # The Netgen mesher for the shell (Netgen Mesh) and its second-order parameters (Meshing Parameters)
        window.edit_geometry('Mesh setup')
        forms.select_type('Netgen Mesh')
        forms.set('Name','GUI_NetgenShell')
        click_part((0,5,5))
        check('the shell picked as the Netgen mesh region',forms.form.MeshSetupItem.CreationIds is not None and len(forms.form.MeshSetupItem.CreationIds)==1)
        forms.ok()
        window.edit_geometry('Mesh setup')
        forms.select_type('Meshing Parameters')
        forms.set_choice('AdvancedView','Advanced')
        forms.set_choice('SecondOrder','Yes');forms.set_choice('MidsideNodesOnGeometry','No')
        forms.set('Name','GUI_SecondOrderShell')
        click_part((0,5,5))
        check('the shell picked as the mesh setup region',forms.form.MeshSetupItem.CreationIds is not None and len(forms.form.MeshSetupItem.CreationIds)==1)
        forms.ok()
        item=c.GetMeshSetupItem('GUI_SecondOrderShell')
        check('second order with midside nodes off geometry (Controller converts the Netgen mesh)',item is not None and item.SecondOrder and not item.MidsideNodesOnGeometry)
        state['outputStart']=len(window.output.toPlainText())
        window.run_operation(window.geometry.Execute('Create mesh',Array[String]([state['beamPart']])),lambda:window.view.setCurrentText('Model'))
    def beam_meshed():
        if not wait():return False
        c=window.controller
        part=next(iter(c.Model.Mesh.Parts.Values))
        types=element_types(c.Model.Mesh,part)
        cells=[len(e) for e in part.Visualization.EdgeCells]
        text=window.output.toPlainText()[state['outputStart']:]
        report['beamMesh']={'partType':str(part.PartType),'elements':types,'edgeCellNodes':sorted(set(cells)),'edgeCells':len(cells),
                            'converted':'Converting mesh to second order' in text}
        check('the shell mesh is second order (ParabolicTriangleElement)',types.get('ParabolicTriangleElement',0)>0)
        check('the Netgen mesh was converted to second order by PrePoMax',report['beamMesh']['converted'])
        check('its edges are ParabolicBeamElement edges: 3-node edge cells (LinearToParabolic, ConvertLineFeElementsToEdges)',cells and set(cells)=={3})
        # The default shell mesher (Meshing Parameters only) runs GmshCaller's interval assignment with lp_solve
        c.RemoveMeshSetupItemsCommand(Array[String](['GUI_NetgenShell']))
        state['outputStart']=len(window.output.toPlainText())
        window.run_operation(window.geometry.Execute('Create mesh',Array[String]([state['beamPart']])),lambda:window.view.setCurrentText('Model'))
    def shell_default_mesh():
        if not wait():return False
        c=window.controller
        text=window.output.toPlainText()[state['outputStart']:]
        part=next(iter(c.Model.Mesh.Parts.Values))
        report['shellDefaultMesh']={'elements':element_types(c.Model.Mesh,part),'lpSolveError':'lp_solve' in text and 'could not be loaded' in text}
        check('the default shell mesh runs GmshCaller with lp_solve (interval assignment)',not report['shellDefaultMesh']['lpSolveError'] and 'Mesh generation failed' not in text)
        check('and meshes the shell',sum(report['shellDefaultMesh']['elements'].values())>0)
        report.update(success=True)
    steps=iter([import_cad,import_ready,import_undone,sizing,tetra,mesh,mesh_done,moved,undone,redone,compound_tree,
                beam_import,beam_delete_face,beam_deleted,beam_meshed,shell_default_mesh]);current=[None]
    # A hang can be inspected: kill -USR1 writes the Python stacks to faults.log
    import faulthandler,signal
    state['faults']=open(output/'faults.log','w');faulthandler.register(signal.SIGUSR1,file=state['faults'],all_threads=True)
    timer=QtCore.QTimer(window)
    def tick():
        try:
            if time.monotonic()-started>240:raise TimeoutError('GUI native operation timed out')
            if current[0] is None:
                current[0]=next(steps)
                # Which step runs, written as it starts (a hang leaves the step it is in)
                with open(output/'progress.log','a') as log:log.write(current[0].__name__+'\n')
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

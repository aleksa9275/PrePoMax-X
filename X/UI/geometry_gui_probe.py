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
        window.edit_geometry('Mesh setup');dialog=window.active_editor
        check('all ten original meshing types offered',dialog.types.count()==10)
        choose(dialog,'AdvancedView','Advanced');choose(dialog,'Relative','Absolute')
        choose(dialog,'SecondOrder','No')
        dialog.entries['Name'][1].setText('GUI_Sizing');dialog.entries['MaxH'][1].setText('4')
        dialog.prepare_selection('');click_part()
        check('native pointer picks original CAD part',len(window.selected)==1)
        dialog.use_selection('')
        check('mesh setup retains native mouse selection',dialog.rule.Item.CreationData.Nodes.Count==1)
        dialog.apply()
        check('setup commit locks active editor',window.operation_task is not None and not dialog.isEnabled())
    def tetra():
        if not wait():return False
        check('sizing widget committed original object',window.controller.GetMeshSetupItem('GUI_Sizing').MaxH==4 and window.active_editor is None)
        window.edit_geometry('Mesh setup');dialog=window.active_editor
        dialog.types.setCurrentIndex(next(i for i in range(dialog.types.count()) if dialog.types.itemText(i)=='Tetrahedral Gmsh'));app.processEvents()
        dialog.entries['Name'][1].setText('GUI_Tetrahedra');dialog.prepare_selection('');click_part();dialog.use_selection('');dialog.apply()
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
        window.edit_geometry('Translate');dialog=window.active_editor
        dialog.entries['X2'][1].setText('2');dialog.apply()
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
        report.update(success=True,elements=state['elements'],nodes=len(c.Model.Mesh.Nodes),project=window.path)
    steps=iter([import_cad,import_ready,import_undone,sizing,tetra,mesh,mesh_done,moved,undone,redone]);current=[None]
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

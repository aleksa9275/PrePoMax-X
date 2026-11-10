"""C2 interactive authoring through actual tree, dialogs, table and viewport widgets."""
import json
import traceback
from pathlib import Path
from PyQt6 import QtCore, QtWidgets, QtTest
from System import Array, Int32


def start(app,window,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    report={'success':False,'checks':[]}
    def check(name,condition):
        if not condition:raise AssertionError(name)
        report['checks'].append(name)
    def capture(name):
        origin=window.mapToGlobal(QtCore.QPoint(0,0))
        return window.screen().grabWindow(0,origin.x(),origin.y(),window.width(),window.height()).save(str(output/(name+'.png')))
    def find(family,name=None,step=None):
        for item in window.walk_tree():
            entry=item.data(0,QtCore.Qt.ItemDataRole.UserRole)
            if entry.Family==family and (name is None and entry.Group or name is not None and entry.Name==name) and (step is None or entry.Step==step):return item
        raise AssertionError('Tree entry missing: '+str((family,name,step)))
    def open_editor(item):
        window.tree.scrollToItem(item)
        window.tree.setCurrentItem(item)
        rect=window.tree.visualItemRect(item)
        QtTest.QTest.mouseDClick(window.tree.viewport(),QtCore.Qt.MouseButton.LeftButton,pos=rect.center())
        app.processEvents()
        # Some platform styles emit activated on release, after the double click.
        if window.active_editor is None:window.edit_item(item)
        app.processEvents()
        return window.active_editor
    def run():
        try:
            c=window.controller
            window.open(str(output.parent/'service/authored.pmx'))
            check('authored model tree includes step children',find('Loads','Force','Static') is not None and find('Sections','Solid') is not None)
            # Original FrmMaterial compiled whole (C11), opened by the tree through FrmMain.EditMaterial.
            from form_driver import FormDriver, walk
            from forms_gui_probe_child import ChildFormsProbe
            open_editor(find('Materials','Steel'))
            forms=FormDriver(window);form=forms.form
            check('tree opens the original FrmMaterial',type(form).__name__=='FrmMaterial' and str(form.Text)=='Edit Material: Steel')
            helper=ChildFormsProbe(app,window,check,{'forms':{}},lambda *a:None)
            tree=forms.control('tvProperties');_,tree_widget=helper.widget(form,tree)
            node=helper.find_node(tree.Nodes,'Specific Heat');node.EnsureVisible();window.form_renderer.flush()
            helper.tree_click(tree_widget,node);forms.click('btnAdd')
            added=[str(i.Text) for i in forms.control('lvAddedProperties').Items]
            check('Specific Heat added through the original models tree',added[-1:]==['Specific Heat'])
            helper.grid_set(form,'Specific heat','500')
            temperature=forms.control('cbTemperatureDependent');window.form_renderer.guard(temperature.RaiseClick);forms.flush()
            pages=[str(p.Name) for p in forms.control('tcProperties').TabPages]
            check('temperature dependence shows the original data points page (HideShowTemperature)',pages==['tpDataPoints'])
            grid=forms.control('dgvData');before=grid.RowCount
            from forms_gui_probe_grid import edit_cell
            _,table=helper.widget(form,grid);edit_cell(app,table,grid.NewRowIndex,0,'600');forms.flush()
            check('a typed value on the new row adds a data point',grid.RowCount==before+1)
            window.form_renderer.guard(temperature.RaiseClick);forms.flush()
            check('material editor capture',window.form_renderer.windows[form].grab().save(str(output/'material.png')))
            forms.ok();app.processEvents()
            check('original FrmMaterial OK replaces the material with the new property',len(c.GetMaterial('Steel').Properties)==3 and not form.Visible)
            window.undo();check('material authoring undo',len(c.GetMaterial('Steel').Properties)==2)
            window.redo();check('material authoring redo',len(c.GetMaterial('Steel').Properties)==3)
            # Original FrmLoad compiled whole (C9), opened by the tree through FrmMain.EditLoad.
            from form_driver import FormDriver
            forms=FormDriver(window)
            dialog=open_editor(find('Loads','Force','Static'))
            check('tree opens the original FrmLoad',type(forms.form).__name__=='FrmLoad' and forms.has('F1') and str(forms.form.Text)=='Edit Load: Force')
            before=c.GetLoad('Static','Force').F1.Value
            forms.set('F1','0');forms.ok()
            check('original FrmLoad zero-load rejection in a message box',any('must not be equal to 0' in t for t in forms.prompts) and forms.form is not None and c.GetLoad('Static','Force').F1.Value==before)
            forms.set('F1','250');forms.ok()
            check('original FrmLoad edits the load',forms.form is None and c.GetLoad('Static','Force').F1.Value==250)
            # FrmNodeSet stays open while the viewport picks through FrmMain._vtk_SelectPointOrArea.
            dialog=open_editor(find('Node sets'))
            check('original FrmNodeSet keeps viewport enabled, tree mouse off',type(forms.form).__name__=='FrmNodeSet' and window.viewport.isEnabled() and not window.tree.isEnabled())
            check('FrmSelectItemSet shown with the node set form',forms.host.SelectItemSetForm.Visible)
            camera=window.renderer.GetActiveCamera();camera.SetPosition(4,.5,.5);camera.SetFocalPoint(.5,.5,.5);camera.SetViewUp(0,0,1);window.fit()
            # FrmSelectItemSet: mesh-based selection by surface.
            forms.click('rbSurface',forms.host.SelectItemSetForm)
            window.renderer.SetWorldPoint(1,.5,.5,1);window.renderer.WorldToDisplay()
            x,y,_=window.renderer.GetDisplayPoint()
            window._pick(x,y)
            report['pick']={'selected':list(window.selected),'selectBy':str(c.SelectBy),'item':str(c.Selection.SelectItem),'nodes':c.Selection.Nodes.Count,'hit':str(window.scene.pick(x,y))}
            check('viewport selects while the original set form stays open',sorted(window.selected)==[2,3,6,7])
            forms.set('Name','FromDialog')
            forms.ok()
            check('original FrmNodeSet creates the picked node set with history',sorted(c.GetNodeSet('FromDialog').Labels)==[2,3,6,7] and c.GetNodeSet('FromDialog').CreationData.Nodes.Count>=1)
            dialog=open_editor(find('Sections'))
            check('tree opens the original FrmSection',type(forms.form).__name__=='FrmSection')
            report['sectionTypes']=forms.types
            forms.select_type(next(t for t in forms.types if 'Solid' in t))
            region=next(v for v in forms.choices('Region type') if 'Element' in v)
            forms.set('Region type',region)
            check('original region setter updates the visible grid rows',forms.has('Element set') and not forms.has('Part'))
            forms.cancel()
            check('closing editor restores document commands',window.active_editor is None and window.tree.isEnabled() and window.actions['Open…'].isEnabled())
            window.raise_();window.activateWindow();QtTest.QTest.qWait(150);app.processEvents()
            check('complete authoring tree captured',capture('tree'))
            window.path=str(output/'gui-authored.pmx');window.save();c.ExportToCalculixCommand(str(output/'gui-authored.inp'))
            window.open(window.path)
            check('GUI-authored project save/reopen',c.GetLoad('Static','Force').F1.Value==250 and sorted(c.GetNodeSet('FromDialog').Labels)==[2,3,6,7])
            report['success']=True
        except Exception:report['error']=traceback.format_exc()
        finally:
            if window.active_editor is not None:window.active_editor.reject()
            (output/'authoring-gui.json').write_text(json.dumps(report,indent=2)+'\n')
            window.dirty=False;window.close();app.quit()
    QtCore.QTimer.singleShot(350,run)

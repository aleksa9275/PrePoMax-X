"""Integrated GUI proof using real widgets, native VTK and dispatched pointer events."""
import json
import platform
import traceback
from pathlib import Path
from PyQt6 import QtCore, QtWidgets, QtTest


def start(app, window, material_dialog, session, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    report = {'success':False, 'host':platform.platform(), 'checks':[],
              'scope':'synthetic native/Qt pointer events and local display; not human/four-target acceptance'}
    def check(name, condition):
        report['checks'].append({'name':name, 'passed':bool(condition)})
        if not condition:
            raise AssertionError(name)
    def capture(widget, name):
        origin = widget.mapToGlobal(QtCore.QPoint(0,0))
        return widget.screen().grabWindow(0, origin.x(), origin.y(), widget.width(), widget.height()).toImage()
    def run():
        try:
            c = session.Controller
            baseline = output.parent / 'service/baseline.pmx'
            window.open(str(baseline))
            app.processEvents()
            from view_probe import ViewProbe
            view=ViewProbe(app,window)
            view.look((4,.5,.5),(.5,.5,.5),(0,0,1))
            window.raise_()
            window.activateWindow()
            QtTest.QTest.qWait(250)
            part=str(next(iter(c.Model.Mesh.Parts.Keys)))
            report['drawnActors']=view.actor_names()
            check('original actor topology rendered', part in view.actor_names() and view.triangles(part)==12)
            qx,qy=view.to_widget((1,.5,.5))
            # The toolbar pick modes set the original selection mode (Controller.SelectBy/SelectItem)
            window.pick_mode.setCurrentIndex(0);window.apply_pick_mode()
            view.click(qx,qy)
            report["pointerDebug"] = {"selected":window.selected,"status":window.statusBar().currentMessage(),"position":[qx,qy],"viewport":[window.viewport.width(),window.viewport.height()]}
            check('dispatched pointer resolves original element', window.selected==[1])
            window.pick_mode.setCurrentIndex(1)
            view.click(qx,qy)
            report["pointerDebug"] = {"selected":window.selected,"status":window.statusBar().currentMessage(),"position":[qx,qy],"viewport":[window.viewport.width(),window.viewport.height()],"drawn":view.actor_names()}
            check('dispatched face pick resolves original node IDs', sorted(window.selected)==[2,3,6,7])
            report['highlightPixels']=view.highlighted_pixels(output/'highlight.png')
            check('selection highlight actor displayed', report['highlightPixels']>20)
            # The middle button turns the view (vtkInteractorStyleControl); the left one picks and draws the box
            before=view.camera()
            view.drag(qx,qy,35,17.5,button=QtCore.Qt.MouseButton.MiddleButton)
            check('native drag rotates camera', view.camera()[0]!=before[0])
            original_view=c.GetViewParameters()
            before=view.camera()
            c.Rotate(12,0,0)
            check('original Controller camera command reaches VTK', view.camera()[0]!=before[0])
            c.SetViewParameters(False,*original_view)
            check('original Controller camera query/restore', all(abs(a-b)<1e-9 for a,b in zip(view.camera()[0],original_view[0])))
            frame=capture(window,'window')
            check('actual displayed window captured', not frame.isNull() and frame.save(str(output/'window.png')))
            colors={frame.pixelColor(x,y).rgb() for x in range(0,frame.width(),16) for y in range(0,frame.height(),16)}
            check('actual displayed frame has geometry pixels', len(colors)>20)
            dialog=material_dialog(window,'XSTEEL')
            dialog.show()
            app.processEvents()
            field=dialog.entries[(0,'YoungsModulus')][1]
            field.setFocus()
            field.selectAll()
            QtTest.QTest.keyClicks(field, '-1')
            dialog.apply()
            check('widget accept reports original invalid-value error', bool(dialog.error.text()) and dialog.result()!=QtWidgets.QDialog.DialogCode.Accepted)
            check('invalid widget accept preserves model', c.GetMaterial('XSTEEL').Properties[0].YoungsPoissonsTemp[0][0].Value==210000)
            field.setText('100 GPa')
            check('material editor displayed', dialog.grab().save(str(output/'material.png')))
            dialog.reject()
            check('widget cancel preserves model', c.GetMaterial('XSTEEL').Properties[0].YoungsPoissonsTemp[0][0].Value==210000)
            dialog=material_dialog(window,'XSTEEL')
            dialog.entries[(0,'YoungsModulus')][1].setText('100 GPa')
            dialog.apply()
            check('widget accept commits original unit conversion', dialog.result()==QtWidgets.QDialog.DialogCode.Accepted and c.GetMaterial('XSTEEL').Properties[0].YoungsPoissonsTemp[0][0].Value==100000)
            window.undo()
            check('GUI undo uses original history', c.GetMaterial('XSTEEL').Properties[0].YoungsPoissonsTemp[0][0].Value==210000)
            window.redo()
            check('GUI redo uses original history', c.GetMaterial('XSTEEL').Properties[0].YoungsPoissonsTemp[0][0].Value==100000)
            window.path=str(output/'gui-edited.pmx')
            window.save()
            c.ExportToCalculixCommand(str(output/'gui-edited.inp'))
            window.open(window.path)
            check('GUI PMX save/reopen keeps edit', c.GetMaterial('XSTEEL').Properties[0].YoungsPoissonsTemp[0][0].Value==100000)
            window.resize(1040,680)
            app.processEvents()
            window.render()
            scale=window.viewport.devicePixelRatioF()
            size=view.size()
            check('native resize uses device pixel scale', size==(round(window.viewport.width()*scale),round(window.viewport.height()*scale)))
            report.update(success=True, renderer=view.render_info(), devicePixelRatio=scale, renderSize=list(size))
        except Exception:
            report['error']=traceback.format_exc()
        finally:
            (output/'gui.json').write_text(json.dumps(report,indent=2)+'\n')
            window.dirty=False
            window.close()
            app.quit()
    QtCore.QTimer.singleShot(300, run)

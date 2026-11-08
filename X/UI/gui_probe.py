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
            camera = window.renderer.GetActiveCamera()
            camera.SetPosition(4,.5,.5)
            camera.SetFocalPoint(.5,.5,.5)
            camera.SetViewUp(0,0,1)
            window.fit()
            window.raise_()
            window.activateWindow()
            QtTest.QTest.qWait(250)
            check('original actor topology rendered', len(window.scene.actors)>0 and window.scene.actors[0].GetMapper().GetInput().GetNumberOfCells()==12)
            window.renderer.SetWorldPoint(1,.5,.5,1)
            window.renderer.WorldToDisplay()
            x,y,_ = window.renderer.GetDisplayPoint()
            scale = window.viewport.devicePixelRatioF()
            qx,qy=x/scale,window.viewport.height()-y/scale
            if platform.system()=='Darwin':
                from viewport_probe import CocoaEvents
                events=CocoaEvents(window.viewport)
                events.height=window.viewport.height()
                def click():
                    events.send(1,qx,qy)
                    events.send(2,qx,qy)
            else:
                def click():
                    QtTest.QTest.mouseClick(window.viewport, QtCore.Qt.MouseButton.LeftButton,
                                          pos=QtCore.QPoint(round(qx),round(qy)))
            click()
            app.processEvents()
            report["pointerDebug"] = {"selected":window.selected,"status":window.statusBar().currentMessage(),"hit":str(window.scene.pick(x,y)),"position":[x,y,qx,qy],"viewport":[window.viewport.width(),window.viewport.height()]}
            check('dispatched pointer resolves original element', window.selected==[1])
            window.pick_mode.setCurrentIndex(1)
            QtTest.QTest.qWait(app.doubleClickInterval()+50)
            click()
            app.processEvents()
            report["pointerDebug"] = {"selected":window.selected,"status":window.statusBar().currentMessage(),"hit":str(window.scene.pick(x,y)),"position":[x,y,qx,qy],"viewport":[window.viewport.width(),window.viewport.height()]}
            check('dispatched face pick resolves original node IDs', sorted(window.selected)==[2,3,6,7])
            check('selection highlight actor displayed', window.scene.highlight_actor is not None)
            if platform.system()=='Darwin':
                before=camera.GetPosition()
                QtTest.QTest.qWait(app.doubleClickInterval()+50)
                events.send(1,qx,qy)
                for d in range(5,36,5):
                    events.send(6,qx+d,qy+d/2)
                events.send(2,qx+35,qy+17.5)
                app.processEvents()
                check('native drag rotates camera', camera.GetPosition()!=before)
            else:
                before=camera.GetPosition()
                QtTest.QTest.mousePress(window.viewport, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(round(qx),round(qy)))
                for d in range(5,36,5):
                    QtTest.QTest.mouseMove(window.viewport, QtCore.QPoint(round(qx+d),round(qy+d/2)), 20)
                QtTest.QTest.mouseRelease(window.viewport, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(round(qx+35),round(qy+17.5)))
                app.processEvents()
                check('Qt drag rotates native VTK camera', camera.GetPosition()!=before)
            original_view=c.GetViewParameters()
            before=camera.GetPosition()
            c.Rotate(12,0,0)
            check('original Controller camera command reaches VTK', camera.GetPosition()!=before)
            c.SetViewParameters(False,*original_view)
            check('original Controller camera query/restore', tuple(camera.GetPosition())==tuple(original_view[0]))
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
            size=window.viewport.GetRenderWindow().GetSize()
            check('native resize uses device pixel scale', tuple(size)==(round(window.viewport.width()*scale),round(window.viewport.height()*scale)))
            report.update(success=True, renderer=window.viewport.GetRenderWindow().GetClassName(),
                          devicePixelRatio=scale, renderSize=list(size))
        except Exception:
            report['error']=traceback.format_exc()
        finally:
            (output/'gui.json').write_text(json.dumps(report,indent=2)+'\n')
            window.dirty=False
            window.close()
            app.quit()
    QtCore.QTimer.singleShot(300, run)

"""Unattended checks of the original FrmMain in Qt (M2, main_form.py): the original menus, tool strips, tree and view,
a model opened by the original command line (-f FILE -u UNITS), the view drawn by vtkNative, and an original form
opened from the original menu. Run by main_form.py when PREPOMAXX_UI_PROBE names this file; the report goes to
PREPOMAXX_UI_PROBE_OUTPUT (.json, plus the view and window images).
"""
import json
import os
import time
import traceback

from PyQt6 import QtCore, QtGui, QtWidgets
from System.Windows.Forms import ToolStripDropDownItem, TreeView

PROMPTS = None  # set by main_form.py: the message boxes shown (answered with their first button)
PROMPT_ANSWER = [None]  # set by main_form.py: an answer the message boxes give instead


def start(app, window, form, renderer):
    output = os.environ['PREPOMAXX_UI_PROBE_OUTPUT']
    report = {'success': False, 'checks': []}

    def check(name, value, detail=None):
        report['checks'].append({'name': name, 'passed': bool(value), **({'detail': detail} if detail is not None else {})})
        if not value:
            raise AssertionError(name + ('' if detail is None else ': ' + str(detail)))

    def pump(seconds=0.2):
        end = time.time() + seconds
        if os.environ.get('PREPOMAXX_UI_PROBE_SIZES'):
            import sys
            print('[sizes] ' + '; '.join(f'{type(w).__name__}:{getattr(getattr(w, "form", None), "Name", "")}:{w.width()}x{w.height()}:{w.isVisible()}'
                                         for w in QtWidgets.QApplication.topLevelWidgets() if w.width() > 2000 or w.height() > 2000), file=sys.stderr, flush=True)
        while time.time() < end:
            app.processEvents()
            renderer.flush()

    def wait(condition, seconds, name):
        end = time.time() + seconds
        while time.time() < end:
            pump(0.1)
            if condition():
                return
        from System.Windows.Forms import Form
        shown = [type(f).__name__ + ' ' + str(f.Text) for f in Form.OpenForms if f.Visible and f is not form]
        check(name, False, 'timed out; open forms: ' + ', '.join(shown))

    def walk(items):
        for item in items:
            yield item
            if isinstance(item, ToolStripDropDownItem):
                yield from walk(item.DropDownItems)

    def controls(control):
        for child in control.Controls:
            yield child
            yield from controls(child)

    try:
        pump(1)
        menu = form.MainMenuStrip
        check('the original menu strip', menu is not None)
        top = [str(i.Text).replace('&', '') for i in menu.Items]
        check('16 original menus', len(top) == 16, top)
        strips = [w for w in window.widgets.values() if type(w).__name__ == 'StripWidget']
        check('menu, 5 tool strips and the status strip', len(strips) == 7, len(strips))
        check('the original vtkControl in a native widget', len(window.viewports) == 1 and window.viewports[0].attached)
        # The model of the command line: the original Shown handler imports it in a new model of the unit system
        wait(lambda: form.Controller.Model is not None and form.Controller.Model.Mesh is not None and form.Controller.Model.Mesh.Parts.Count > 0,
             60, 'the -f model is imported')
        parts = form.Controller.Model.Mesh.Parts.Count
        check('mesh parts', parts > 0, parts)
        trees = [c for c in controls(form) if isinstance(c, TreeView)]
        nodes = sum(t.GetNodeCount(True) for t in trees)
        check('the original model tree shows the model', nodes > 10, nodes)
        # The view drawn by vtkNative (the native window of the original vtkControl)
        pump(1)
        view = window.viewports[0].control
        png = output + '-view.png'
        view.NativeMirror.WritePng(png, 1)
        image = QtGui.QImage(png)
        colors = {image.pixel(x, y) for x in range(0, image.width(), max(1, image.width() // 40))
                  for y in range(0, image.height(), max(1, image.height() // 40))}
        check('the view shows the model', image.width() > 100 and len(colors) > 10, len(colors))
        # An original form from the original menu (Property - Material - Create)
        item = next(i for i in walk(menu.Items) if str(i.Name) == 'tsmiCreateMaterial')
        check('Create Material enabled with a mesh', bool(item.Enabled))
        renderer.input(item.PerformClick)
        pump(1)
        shown = [f for f, w in renderer.windows.items() if f is not form and f.Visible and w.isVisible()]
        names = [type(f).__name__ for f in shown]
        check('FrmMaterial shown from the menu', 'FrmMaterial' in names, names)
        for f in shown:
            renderer.input(f.CloseByUser)
        pump(0.5)
        window.grab().save(output + '-window.png')
        report['success'] = True
    except Exception:
        report['error'] = traceback.format_exc()
    report['messageBoxes'] = list(PROMPTS or [])
    with open(output + '.json', 'w') as stream:
        json.dump(report, stream, indent=1)
    # Closing: the original asks to save the changed model; the probe leaves it unsaved
    from System.Windows.Forms import DialogResult
    PROMPT_ANSWER[0] = DialogResult.No
    QtCore.QTimer.singleShot(100, window.close)

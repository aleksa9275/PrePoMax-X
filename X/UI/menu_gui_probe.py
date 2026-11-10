"""Original FrmMain main-menu parity: structure, per-view enabling and representative
item execution through the real Qt window and original Controller."""
import json
import time
import traceback
from pathlib import Path

from PyQt6 import QtCore, QtTest, QtWidgets

import main_menu
from main_menu import MENU, leaves


def start(app, w, output, model, results):
    import shutil
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    # Work on copies: the smoke pass runs Save and other mutating items.
    model = str(shutil.copy2(model, output / 'menu-model.pmx'))
    results = str(shutil.copy2(results, output / 'menu-results.pmx')) if results and Path(results).is_file() else None
    report = {'success': False, 'checks': []}

    def check(name, value):
        report['checks'].append({'name': name, 'passed': bool(value)})
        if not value:
            raise AssertionError(name)

    # Non-interactive stand-ins for the original selection/confirmation dialogs.
    chosen = {}
    original_exec = main_menu.EntityDialog.exec

    def auto_exec(dialog):
        wanted = chosen.get(dialog.title)
        for i in range(dialog.list.count()):
            item = dialog.list.item(i)
            item.setSelected(wanted is None and item.isSelected() or wanted is not None and item.text() in wanted)
        return QtWidgets.QDialog.DialogCode.Accepted
    main_menu.EntityDialog.exec = auto_exec
    original_warning = QtWidgets.QMessageBox.warning
    QtWidgets.QMessageBox.warning = staticmethod(lambda *a, **k: QtWidgets.QMessageBox.StandardButton.Ok)

    def trigger(item_id):
        action = w.original_actions[item_id]
        check('menu item enabled: ' + item_id, action.isEnabled() and action.parent() is not None)
        action.trigger()
        app.processEvents()

    MAPPING_ERRORS = ('AttributeError', 'TypeError', 'NameError', 'KeyError', 'IndexError', 'MissingMethodException',
                      'InvalidCastException', 'NullReferenceException', 'AmbiguousMatchException', 'SyntaxError',
                      'ImportError', 'ModuleNotFoundError', 'UnboundLocalError')
    SKIP = {'tsmiExit', 'tsmiNew', 'tsmiAbout', 'tsmiHomePage', 'tsmiRunAnalysis', 'tsmiCheckModel', 'tsmiKillAnalysis',
            'tsmiAutomationServer', 'tsmiCloseAllResults', 'tsmiCloseCurrentResult', 'tsmiOpen', 'tsmiRunHistoryFile',
            'tsmiRegenerateHistory', 'tsmiRegenerateHistoryUsingOtherFiles', 'tsmiRegenerateHistoryWithRemeshing',
            'tsmiAppendResults', 'tsmiCreateMesh', 'tsmiResultsAnalysis', 'tsmiBidirectionalMeshConverter'}

    def smoke(results):
        """Execute every enabled original leaf once in its view; dialogs are cancelled."""
        c = w.controller
        patches = []

        def patch(owner, name, value):
            patches.append((owner, name, getattr(owner, name)))
            setattr(owner, name, value)
        patch(QtWidgets.QFileDialog, 'getOpenFileName', staticmethod(lambda *a, **k: ('', '')))
        patch(QtWidgets.QFileDialog, 'getSaveFileName', staticmethod(lambda *a, **k: ('', '')))
        patch(QtWidgets.QInputDialog, 'getDouble', staticmethod(lambda *a, **k: (0.0, False)))
        patch(QtWidgets.QInputDialog, 'getInt', staticmethod(lambda *a, **k: (0, False)))
        patch(QtWidgets.QInputDialog, 'getItem', staticmethod(lambda *a, **k: ('', False)))
        patch(QtWidgets.QInputDialog, 'getText', staticmethod(lambda *a, **k: ('', False)))
        patch(QtWidgets.QColorDialog, 'getColor', staticmethod(lambda *a, **k: __import__('PyQt6').QtGui.QColor()))
        patch(QtWidgets.QMessageBox, 'warning', staticmethod(lambda *a, **k: QtWidgets.QMessageBox.StandardButton.Cancel))
        patch(QtWidgets.QDialog, 'exec', lambda self: QtWidgets.QDialog.DialogCode.Rejected)
        chosen.clear()
        outcomes = {}
        views_seen = {}
        try:
            for path, view in [(model, 'Model'), (model, 'Geometry'), (results, 'Results')]:
                if not path or not Path(path).is_file():
                    continue
                w.open(path)
                if str(c.CurrentView) != view:
                    w.view.setCurrentText(view)
                app.processEvents()
                for top in MENU['menus']:
                    menu = w.original_top[top['id']]
                    for node in leaves(top):
                        item = node['id']
                        if item in SKIP or node.get('visible') is False or item == 'tsmiOpenRecent':
                            continue
                        if view == 'Results' and not c.ResultsInitialized:
                            w.open(path)
                        if str(c.CurrentView) != view:
                            w.view.setCurrentText(view)
                            app.processEvents()
                        w.update_original_menu_state()
                        if not menu.isEnabled() or not w.original_actions[item].isEnabled():
                            continue
                        try:
                            w.run_original_item(node)
                            app.processEvents()
                            outcome = 'ok'
                        except BaseException as error:
                            kind = type(error).__name__
                            text = str(error)
                            mapping = kind in MAPPING_ERRORS or any(m in text for m in MAPPING_ERRORS)
                            outcome = ('MAPPING ' if mapping else 'refused ') + kind + ': ' + text.splitlines()[0][:160] if text else kind
                        finally:
                            while w.operation_task is not None:
                                QtTest.QTest.qWait(20)
                            if w.active_editor is not None:
                                w.active_editor.reject()
                                app.processEvents()
                        outcomes.setdefault(item, {})[view] = outcome
                        views_seen.setdefault(view, set()).add(str(c.CurrentView))
        finally:
            for owner, name, value in reversed(patches):
                setattr(owner, name, value)
        report['smoke'] = outcomes
        report['smokeViews'] = {k: sorted(v) for k, v in views_seen.items()}
        bad = {k: v for k, v in outcomes.items() if any(o.startswith('MAPPING') for o in v.values())}
        report['smokeMappingErrors'] = bad
        check('every reachable original item runs without a mapping error (%d items)' % len(outcomes), not bad)

    def run():
        c = w.controller
        try:
            # Structure: every original top-level menu and leaf, in original order.
            bar = [a.text() for a in w.menuBar().actions()]
            check('16 original top-level menus in order', bar == [m['text'] for m in MENU['menus']])
            original_leaves = [n for m in MENU['menus'] for n in leaves(m) if n.get('visible') is not False]
            check('Open Recent is a run-time submenu', hasattr(w, 'original_recent'))
            original_leaves = [n for n in original_leaves if n['id'] != 'tsmiOpenRecent']
            check('all original leaf items present', all(n['id'] in w.original_actions for n in original_leaves))
            report['leafItems'] = len(original_leaves)
            report['unmappedItems'] = list(w.unmapped_handlers)
            check('every original leaf item is mapped', not w.unmapped_handlers)
            check('original shortcuts', w.original_actions['tsmiSave'].shortcut().toString() == 'Ctrl+S'
                  and w.original_actions['tsmiCaptureViewport'].shortcut().toString() == 'Ctrl+P')

            # Empty application: only File/Results/Tools/Help enabled, like SetMenuAndToolStripVisibility.
            w.update_original_menu_state()
            enabled = {k for k, m in w.original_top.items() if m.isEnabled()}
            check('empty state enables original menus', enabled == {'tsmiFile', 'tsmiResults', 'tsmiTools', 'tsmiHelp'})

            w.open(model)
            app.processEvents()
            w.update_original_menu_state()
            enabled = {k for k, m in w.original_top.items() if m.isEnabled()}
            check('model view enables original model menus', {'tsmiModel', 'tsmiProperty', 'tsmiStepMenu', 'tsmiAnalysis'} <= enabled
                  and 'tsmiGeometry' not in enabled)

            # Original vtkMaxScaleWidget: drawn with model length unit, clear of the status block.
            w.render()
            app.processEvents()
            scale = w.scale_actor
            props = w.renderer.GetViewProps()
            present = all(props.IsItemPresent(a) for a in scale.actors())
            report['scaleBar'] = {'present': present, 'visible': scale.visible, 'labels': [l.GetInput() for l in scale.labels],
                                  'position': list(scale.position), 'barWidth': scale.bar_width,
                                  'setting': bool(c.Settings.Graphics.ScaleWidgetVisibility)}
            check('original scale bar drawn with length unit', present and scale.visible and scale.labels[-1].GetInput().endswith(' mm'))
            check('scale bar starts right of the status block', scale.position[0] >= 300)

            # RuntimeInitialization: invariant culture for displayed numbers.
            check('invariant decimal separator in numeric widgets', w.selection_angle.text().startswith('30.00'))

            # Original camera conventions (vtkControl): front looks along -Z with +Y up.
            trigger('tsmiFrontView')
            cam = w.renderer.GetActiveCamera()
            check('original front view', abs(cam.GetViewPlaneNormal()[2] - 1) < 1e-9 and abs(cam.GetViewUp()[1] - 1) < 1e-9)
            trigger('tsmiTopView')
            check('original top view', abs(cam.GetViewPlaneNormal()[1] - 1) < 1e-9 and abs(cam.GetViewUp()[2] + 1) < 1e-9)
            trigger('tsmiIsometricView')
            n = cam.GetViewPlaneNormal()
            check('original isometric view', all(abs(abs(v) - 3 ** -.5) < 1e-6 for v in n))

            # Property > Material: Duplicate then Delete through original selection and commands.
            materials = [m.Name for m in c.GetAllMaterials()]
            chosen['Materials'] = [materials[0]]
            trigger('tsmiDuplicateMaterial')
            after = [m.Name for m in c.GetAllMaterials()]
            check('Property > Material > Duplicate', len(after) == len(materials) + 1)
            chosen['Materials'] = [n for n in after if n not in materials]
            trigger('tsmiDeleteMaterial')
            check('Property > Material > Delete with original confirmation', [m.Name for m in c.GetAllMaterials()] == materials)

            # Model > Part: Hide / Show Only / Show.
            parts = [p.Name for p in c.GetModelParts()]
            chosen['Parts'] = parts[:1]
            trigger('tsmiHideModelParts')
            check('Model > Part > Hide', not c.Model.Mesh.Parts[parts[0]].Visible)
            trigger('tsmiShowOnlyModelParts')
            check('Model > Part > Show Only', c.Model.Mesh.Parts[parts[0]].Visible)
            trigger('tsmiShowAllParts')

            # Step-level two-stage selection (Steps → boundary conditions).
            steps = [s.Name for s in c.GetAllSteps()]
            step = next((s for s in steps if c.GetStepBoundaryConditions(s).Length), None)
            if step is not None:
                bc = c.GetStepBoundaryConditions(step)[0].Name
                chosen['Steps'] = [step]
                chosen['Boundary conditions'] = [bc]
                trigger('tsmiHideBC')
                check('Step > BC > Hide (step then item selection)', not c.GetStep(step).BoundaryConditions[bc].Visible)
                trigger('tsmiShowBC')
                check('Step > BC > Show', c.GetStep(step).BoundaryConditions[bc].Visible)
            else:
                report.setdefault('pending', []).append('fixture has no boundary condition')

            # View > Color Annotations / Items use original controller state.
            trigger('tsmiAnnotateParts')
            check('View > Color Annotations > Parts', str(c.AnnotateWithColor) == 'Parts')
            trigger('tsmiAnnotateAllSymbols')
            check('All Symbols clears exclusive coloring', str(c.AnnotateWithColor) != 'Parts'
                  and not w.original_actions['tsmiAnnotateParts'].isChecked())
            trigger('tsmiAnnotateAllSymbols')
            trigger('tsmiViewNodeIds')
            check('View > Items > Node IDs', 'Nodes' in str(c.ShowItemIds))
            trigger('tsmiViewNodeIds')

            # Parameter commands: the original UI reaches them only through the Python API.
            w.script_dock.show()
            w.script_edit.setPlainText("p = pmx.model.parameters\np.add('menuP', 2.5)\np.replace('menuP', 'menuQ', 3.5)\np.remove('menuQ')")
            w.execute_script()
            deadline = time.monotonic() + 60
            while w.operation_task is not None and time.monotonic() < deadline:
                QtTest.QTest.qWait(20)
            kinds = [type(cmd).__name__ if not hasattr(cmd, 'GetType') else cmd.GetType().Name for cmd in c.GetCommands()]
            report['parameterCommands'] = [k for k in kinds if 'Parameter' in k]
            check('original CAddParameter/CReplaceParameter/CRemoveParameters through the script panel',
                  {'CAddParameter', 'CReplaceParameter', 'CRemoveParameters'} <= set(kinds))

            # Results view items.
            if results and Path(results).is_file():
                w.open(results)
                app.processEvents()
                w.update_original_menu_state()
                check('results view menus', w.original_top['tsmiView'].isEnabled() and not w.original_top['tsmiModel'].isEnabled())
                trigger('tsmiResultsUndeformed')
                check('View > Undeformed', str(c.ViewResultsType) == 'Undeformed')
                trigger('tsmiResultsColorContours')
                check('View > Color Contours', str(c.ViewResultsType) == 'ColorContours')
                trigger('tsmiResultsUndeformedWireframe')
                check('Undeformed wireframe toggles', str(c.GetUndeformedModelType()) == 'WireframeBody')
                trigger('tsmiResultsUndeformedWireframe')
                check('Undeformed wireframe toggles off', str(c.GetUndeformedModelType()) == 'None')
            else:
                report.setdefault('pending', []).append('results fixture not supplied')
            smoke(results)
            report['success'] = True
        except BaseException as error:
            report['error'] = str(error)
            report['traceback'] = traceback.format_exc()
        finally:
            main_menu.EntityDialog.exec = original_exec
            QtWidgets.QMessageBox.warning = original_warning
            if w.active_editor is not None:
                w.active_editor.reject()
            w.dirty = False
            c.ModelChanged = False
            (output / 'menu-gui.json').write_text(json.dumps(report, indent=2) + '\n')
            w.viewport.Finalize()
            app.quit()

    QtCore.QTimer.singleShot(200, run)

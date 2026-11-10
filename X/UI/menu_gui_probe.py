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

            # Original FrmMain tool strips: layout, icons, delegation to the menu handlers.
            strips = MENU['toolstrips']
            check('original tool strip rows', [[b for b in row] for row in strips['rows']] ==
                  [['tsFile', 'tsViews', 'tsSymbols'], ['tsResultDeformation', 'tsResults']]
                  and all(w.toolBarArea(w.original_strips[n]) == QtCore.Qt.ToolBarArea.TopToolBarArea for row in strips['rows'] for n in row))
            buttons = [i for s in strips['strips'].values() for i in s['items'] if i['kind'] == 'Button']
            report['toolButtons'] = len(buttons)
            check('every original tool button has its original icon', all(not w.original_tools[i['id']].icon().isNull() for i in buttons))
            check('every original tool button is mapped', all(i.get('left') in w.original_menu_nodes or i.get('left') in
                  ('TurnSectionViewOnOff', 'TurnExplodedViewOnOff') or i['handler'] in w.STEP_BUTTONS or i['handler'] == 'tsbAnimate_Click'
                  for i in buttons))
            check('original menu icons', not w.original_actions['tsmiSave'].icon().isNull() and not w.original_actions['tsmiFrontView'].icon().isNull())
            check('model view tool strip enabling', w.original_tools['tsbSave'].isEnabled() and w.original_tools['tsbImport'].isEnabled()
                  and w.original_tools['tscbSymbols'].isEnabled() and not w.original_strips['tsResults'].isEnabled()
                  and not w.original_tools['tsbFollowerView'].isEnabled())
            symbols = [w.symbols.itemText(i) for i in range(w.symbols.count())]
            check('model view symbols list (UpdateSymbolsList)', symbols[:2] == ['None', 'Model'] and symbols[2:] == [s.Name for s in c.GetAllSteps()])
            w.original_tools['tsbTopView'].trigger(); app.processEvents()
            cam = w.renderer.GetActiveCamera()
            check('tool strip Top view runs the original menu view', abs(cam.GetViewPlaneNormal()[1] - 1) < 1e-9)
            w.symbols.setCurrentIndex(0); app.processEvents()
            check('symbols combo draws None', str(c.GetDrawSymbolsForStep()) == 'None')
            w.symbols.setCurrentIndex(w.symbols.count() - 1); app.processEvents()
            check('symbols combo draws the step', str(c.GetDrawSymbolsForStep()) == symbols[-1])
            w.tool_tscbColorBy.setCurrentText('Parts'); app.processEvents()
            check('Color by combo uses the original annotation', str(c.AnnotateWithColor) == 'Parts'
                  and w.original_actions['tsmiAnnotateParts'].isChecked())
            w.tool_tscbColorBy.setCurrentText('None'); app.processEvents()
            check('Color by None clears the annotation', str(c.AnnotateWithColor) == 'None')
            w.original_actions['tsmiAnnotateMaterials'].trigger(); app.processEvents()
            check('Color by follows the menu (UpdateColorByComboBox)', w.tool_tscbColorBy.currentText() == 'Materials')
            w.original_actions['tsmiAnnotateMaterials'].trigger(); app.processEvents()
            capture = Path(output) / 'capture'
            capture.mkdir(exist_ok=True)
            properties = w.current_capture_properties()
            properties.SaveToFile = True
            properties.CopyToClipboard = False
            properties.Folder = str(capture)
            properties.AutoIncrement = True
            w.capture_properties = properties
            exec_calls = []
            original_dialog_exec = QtWidgets.QDialog.exec
            QtWidgets.QDialog.exec = lambda self: exec_calls.append(self) or QtWidgets.QDialog.DialogCode.Rejected
            try:
                before = set(Path(str(properties.GetFileName())).parent.glob('*.png'))
                w.original_tools['tsbCapture'].trigger(); app.processEvents()
                after = set(Path(str(properties.GetFileName())).parent.glob('*.png'))
            finally:
                QtWidgets.QDialog.exec = original_dialog_exec
            check('Capture viewport captures without the form', not exec_calls and len(after - before) == 1)
            for f in after - before:
                f.unlink()

            # Original ModelTree: tabs, layout, counts, images, context menu rules and actions.
            import model_tree
            check('original tree tabs', [w.tree_tabs.tabText(i) for i in range(w.tree_tabs.count())] == ['Geometry', 'FE Model', 'Results']
                  and w.tree_tabs.currentIndex() == 1)
            top = [w.tree.topLevelItem(i) for i in range(w.tree.topLevelItemCount())]
            check('FE Model top nodes Model and Analyses', [t.text(0).split(' (')[0] for t in top] == ['Model', 'Analyses'])
            model_node = top[0]
            names = [model_node.child(i).text(0).split(' (')[0] for i in range(model_node.childCount())]
            report['modelTreeNodes'] = names
            check('original Model children order', names == ['Mesh', 'Features', 'Materials', 'Sections', 'Constraints', 'Contacts',
                                                             'Distributions', 'Amplitudes', 'Initial Conditions', 'Steps'])
            def find(text, parent=None):
                stack = [parent] if parent else [w.tree.topLevelItem(i) for i in range(w.tree.topLevelItemCount())]
                while stack:
                    node = stack.pop(0)
                    if node.text(0) == text or node.text(0).split(' (')[0] == text:
                        return node
                    stack += [node.child(i) for i in range(node.childCount())]
            materials_node = find('Materials')
            count = len([m for m in c.GetAllMaterials()])
            check('group text with original count', materials_node.text(0) == f'Materials ({count})')
            check('static node icons', not materials_node.icon(0).isNull() and not find('Steps').icon(0).isNull())
            step_node = find('Steps').child(0)
            check('step sub nodes in AddStep order', [step_node.child(i).text(0).split(' (')[0] for i in range(step_node.childCount())]
                  == ['History Outputs', 'Field Outputs', 'BCs', 'Loads', 'Defined Fields'] and step_node.data(0, model_tree.KEY)[0] == 'Steps')
            part_node = find('Parts', find('Mesh')).child(0)
            part = str(part_node.data(0, model_tree.ROLE).Name)
            check('part status icon (SetNodeStatus)', part_node.data(0, QtCore.Qt.ItemDataRole.UserRole + 2) in
                  ('Solid.ico', 'Shell.ico', 'Wire.ico', 'Compound.ico', 'Solid_transparent.ico'))
            material_item = materials_node.child(0)
            w.tree.clearSelection(); material_item.setSelected(True)
            visible, enabled = w.prepare_tree_menu([material_item])
            shown = [k for k in visible if visible[k]]
            report['materialMenu'] = shown
            check('material context menu (PrepareToolStripItem)', {'tsmiEdit', 'tsmiDuplicate', 'tsmiDeactivate', 'tsmiDelete',
                  'tsmiExpandAll', 'tsmiCollapseAll'} <= set(shown) and 'tsmiHide' not in shown and 'tsmiCreate' not in shown)
            visible, _ = w.prepare_tree_menu([materials_node])
            check('materials node menu: Create and Material Library', visible['tsmiCreate'] and visible['tsmiMaterialLibrary']
                  and not visible['tsmiDelete'])
            visible, _ = w.prepare_tree_menu([model_node])
            check('Model node menu: Edit and Edit CalculiX Keywords', visible['tsmiEdit'] and visible['tsmiEditCalculiXKeywords'])
            visible, _ = w.prepare_tree_menu([part_node])
            check('part menu: Hide/Show, colour, Query', visible['tsmiHide'] and visible['tsmiSetColor'] and visible['tsmiQuery'])
            before = len(list(c.GetAllMaterials()))
            w.tree_action('tsmiDuplicate', [material_item]); app.processEvents()
            check('tree Duplicate runs the original command', len(list(c.GetAllMaterials())) == before + 1)
            duplicate = [m.Name for m in c.GetAllMaterials()][-1]
            node = find(duplicate, find('Materials'))
            w.tree_action('tsmiDelete', [node]); app.processEvents()
            check('tree Delete with original confirmation', len(list(c.GetAllMaterials())) == before)
            w.tree_action('tsmiHide', [find('Parts', find('Mesh')).child(0)]); app.processEvents()
            hidden = find(part, find('Parts', find('Mesh')))
            check('tree Hide and gray hidden icon', not c.Model.Mesh.Parts[part].Visible
                  and hidden.data(0, QtCore.Qt.ItemDataRole.UserRole + 2) == 'Hide.ico')
            w.tree_action('tsmiShow', [hidden]); app.processEvents()
            check('tree Show', c.Model.Mesh.Parts[part].Visible)
            w.tree_search.setText(part); app.processEvents()
            leaves_left = []
            stack = [w.tree.topLevelItem(i) for i in range(w.tree.topLevelItemCount())]
            while stack:
                node = stack.pop()
                if node.childCount() == 0:
                    leaves_left.append(node.text(0))
                stack += [node.child(i) for i in range(node.childCount())]
            check('search box filters leaves (FilterTree)', leaves_left and all(part.upper() in t.upper() for t in leaves_left))
            w.tree_search.setText(''); app.processEvents()
            w.tree_tabs.setCurrentIndex(0); app.processEvents()
            check('Geometry tab switches the view', str(c.CurrentView) == 'Geometry'
                  and [w.tree.topLevelItem(i).text(0).split(' (')[0] for i in range(w.tree.topLevelItemCount())] == ['Parts', 'Mesh Setup'])
            w.tree_tabs.setCurrentIndex(1); app.processEvents()
            check('FE Model tab switches back', str(c.CurrentView) == 'Model' and w.tree_tabs.currentIndex() == 1)

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
                top = [w.tree.topLevelItem(i).text(0).split(' (')[0] for i in range(w.tree.topLevelItemCount())]
                check('Results tab and tree', w.tree_tabs.currentIndex() == 2 and top == ['Model', 'Results'])
                results_node = w.tree.topLevelItem(1)
                check('Results children', [results_node.child(i).text(0).split(' (')[0] for i in range(results_node.childCount())]
                      == ['Field Outputs', 'History Outputs'])
                field = results_node.child(0).child(0)
                visible, _ = w.prepare_tree_menu([field])
                check('raw field node menu: no Edit, Delete allowed', not visible['tsmiEdit'] and visible['tsmiDelete'])
                # Result tool strips.
                tools = w.original_tools
                check('results view tool strip enabling', w.original_strips['tsResults'].isEnabled()
                      and w.original_strips['tsResultDeformation'].isEnabled() and tools['tsbFollowerView'].isEnabled())
                check('results symbols list', [w.symbols.itemText(i) for i in range(w.symbols.count())] == ['None', 'Result'])
                tools['tsbResultsDeformed'].trigger(); app.processEvents()
                check('tool strip Deformed + checked state', str(c.ViewResultsType) == 'Deformed' and tools['tsbResultsDeformed'].isChecked()
                      and not tools['tsbResultsColorContours'].isChecked())
                tools['tsbResultsColorContours'].trigger(); app.processEvents()
                check('tool strip Color contours', str(c.ViewResultsType) == 'ColorContours' and tools['tsbResultsColorContours'].isChecked())
                box = w.tool_tscbStepAndIncrement
                items = [box.itemText(i) for i in range(box.count())]
                ids = c.CurrentResult.GetAllExistingIncrementIds()
                expected = [f'{k}, {i}' for k, v in (ids.items() if isinstance(ids, dict) else ((k, ids[k]) for k in ids.Keys)) for i in v]
                report['stepIncrements'] = items
                check('step, increment list (SetAllStepAndIncrementIds)', items == expected and
                      box.currentText() == f'{c.CurrentFieldData.StepId}, {c.CurrentFieldData.StepIncrementId}')
                tools['tsbFirstStepIncrement'].trigger(); app.processEvents()
                first = (c.CurrentFieldData.StepId, c.CurrentFieldData.StepIncrementId)
                check('First increment', box.currentIndex() == 0 and f'{first[0]}, {first[1]}' == items[0])
                tools['tsbLastStepIncrement'].trigger(); app.processEvents()
                check('Last increment', box.currentIndex() == len(items) - 1
                      and f'{c.CurrentFieldData.StepId}, {c.CurrentFieldData.StepIncrementId}' == items[-1])
                if len(items) > 1:
                    tools['tsbPreviousStepIncrement'].trigger(); app.processEvents()
                    check('Previous increment', box.currentIndex() == len(items) - 2)
                    tools['tsbNextStepIncrement'].trigger(); app.processEvents()
                    check('Next increment', box.currentIndex() == len(items) - 1)
                check('Factor box disabled unless user defined (UpdateScaleFactorTextBoxState)',
                      w.tool_tscbDeformationType.currentText() != 'User defined' and not w.tool_tstbDeformationFactor.isEnabled())
                user = next(t for t, v in w.deformation_types.items() if str(v) == 'UserDefined')
                w.tool_tscbDeformationType.setCurrentText(user); app.processEvents()
                w.tool_tstbDeformationFactor.setText('7'); w.tool_tstbDeformationFactor.returnPressed.emit(); app.processEvents()
                check('user-defined deformation factor applied', w.tool_tstbDeformationFactor.isEnabled()
                      and str(w.session.Presentation.GetDeformationType()) == 'UserDefined'
                      and abs(float(w.session.Presentation.GetDeformationFactor()) - 7) < 1e-6)
                automatic = next(t for t, v in w.deformation_types.items() if str(v) == 'Automatic')
                w.tool_tscbDeformationType.setCurrentText(automatic); app.processEvents()
                check('complex controls hidden without complex results', not tools['tscbComplex'].isVisible()
                      and not c.ContainsComplexResults)
                tools['tsbAnimate'].trigger(); app.processEvents()
                check('Animate opens the animation controls', w.animation_toolbar.isVisible() and not tools['tsbAnimate'].isEnabled())
                w.close_animation(); app.processEvents()
                check('closing the animation restores Animate', not w.animation_toolbar.isVisible() and tools['tsbAnimate'].isEnabled())
                exploded = c.IsExplodedViewActive()
                several = c.DisplayedMesh is not None and c.DisplayedMesh.Parts.Count > 1
                tools['tsbExplodedView'].trigger(); app.processEvents()
                # Controller.TurnExplodedViewOnOff explodes only a mesh with more than one part.
                check('Exploded view button follows the original rule', c.IsExplodedViewActive() == (several != exploded)
                      and tools['tsbExplodedView'].isChecked() == bool(c.IsExplodedViewActive()))
                if several:
                    tools['tsbExplodedView'].trigger(); app.processEvents()
                    check('Exploded view button toggles back', c.IsExplodedViewActive() == exploded)
                tools['tsbSectionView'].trigger(); app.processEvents()
                check('Section view button turns the original section view on', c.IsSectionViewActive() and tools['tsbSectionView'].isChecked())
                tools['tsbSectionView'].trigger(); app.processEvents()
                check('Section view button turns it off', not c.IsSectionViewActive())
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

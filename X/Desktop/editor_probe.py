"""Automated controls -> immutable job inputs -> real native solve probe."""
import hashlib
import json
from pathlib import Path

from PyQt6 import QtCore, QtWidgets
from analysis_editor import AnalysisDialog
from jobs import examples


def begin(app, window, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    report = {'success': False, 'checks': [], 'transport': window.transport,
        'scope': 'Automated Qt editor controls and actual bundled native jobs; no project save/reopen or full-model acceptance'}
    state = {'phase': 'baseline', 'finished': False}
    mesh_path = examples() / 'cube-mesh.inp'
    original_mesh_hash = hashlib.sha256(mesh_path.read_bytes()).hexdigest()

    def check(name, passed):
        report['checks'].append({'name': name, 'passed': bool(passed)})
        if not passed:
            raise ValueError(name)

    def finish(error=None):
        if state['finished']:
            return
        if window.job.active:
            state['finish_error'] = error or 'Probe ended while a native job was active'
            state['finishing'] = True
            window.job.cancel()
            return  # Wait for the original runner's process-tree cleanup.
        state['finished'] = True
        if error is not None:
            report['error'] = str(error)
        report['success'] = error is None
        (output / 'editor.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report), flush=True)
        window.editor_dirty = False  # Only this probe's generated model edits.
        window.close()
        app.exit(0 if report['success'] else 1)

    def capture(widget, path):
        # Includes the native VTK child when capturing the main window.
        origin = widget.mapToGlobal(QtCore.QPoint(0, 0))
        return widget.screen().grabWindow(0, origin.x(), origin.y(), widget.width(), widget.height()).save(str(path))

    def edit_modal():
        try:
            dialog = app.activeModalWidget()
            check('Configure opens the real analysis dialog', isinstance(dialog, AnalysisDialog))
            original_constraints = dialog.collect()['step']['constraints']
            dialog.sections.table.item(0, 1).setText('MissingMaterial')
            dialog.apply()
            check('invalid material cannot apply or start a solver', dialog.definition is None and
                  dialog.isVisible() and not window.job.active)
            report['invalidDefinitionDiagnostic'] = dialog.message.text()
            dialog.sections.table.item(0, 1).setText('ELASTIC')
            dialog.materials.table.item(0, 1).setText('105 GPa')
            dialog.loads.table.item(0, 2).setText('50 N')
            check('support free/constrained components survive editing', dialog.collect()['step']['constraints'] == original_constraints)
            dialog.tabs.setCurrentIndex(4)
            app.processEvents()
            check('edited load dialog capture', dialog.grab().save(str(output / 'loads-dialog.png')))
            dialog.tabs.setCurrentIndex(1)
            app.processEvents()
            check('edited material dialog capture', dialog.grab().save(str(output / 'material-dialog.png')))
            dialog.apply()
            check('original C# validation accepts edited controls', dialog.definition is not None and
                  dialog.validation['success'] and not dialog.validation['solverExecuted'])
            report['validation'] = dialog.validation
        except Exception as error:
            if isinstance(app.activeModalWidget(), QtWidgets.QDialog):
                app.activeModalWidget().reject()
            state['edit_error'] = error

    def completed(result):
        if state['finished']:
            return
        if state.get('finishing'):
            QtCore.QTimer.singleShot(0, lambda: finish(state['finish_error']))
            return
        QtCore.QTimer.singleShot(200, lambda: after_job(result))

    def after_job(result):
        if state['finished'] or state.get('finishing'):
            return
        try:
            check(state['phase'] + ' actual native job completed', result['success'] and result['outcome']['solverExecuted'])
            check(state['phase'] + ' FRD loaded into viewport', window.current_path.name == 'analysis.frd' and
                  window.mapper.GetScalarVisibility() == 1)
            report[state['phase']] = result
            if state['phase'] == 'baseline':
                check('model tree retains source model after result loading', window.model_path == mesh_path.resolve() and
                      window.model_tree.topLevelItem(0).text(0) == mesh_path.name)
                QtCore.QTimer.singleShot(150, edit_modal)
                window.configure_action.trigger()
                if 'edit_error' in state:
                    raise state['edit_error']
                check('applied controls update model definition', window.definition['materials'][0]['youngsModulus'] == '105 GPa' and
                      window.definition['step']['loads'][0]['forcePerNode'][0] == '50 N' and window.editor_dirty)
                report['appliedDefinition'] = window.definition
                state['phase'] = 'edited'
                window.run_model()
                return
            snapshot = json.loads((Path(result['inputDirectory']) / 'analysis.json').read_text())
            check('executed snapshot matches applied controls', snapshot == report['appliedDefinition'])
            check('edited run uses a distinct workspace', result['workspace'] != report['baseline']['workspace'])
            deck = Path(result['directory']) / 'analysis.inp'
            check('executed deck matches original validation hash', hashlib.sha256(deck.read_bytes()).hexdigest() == report['validation']['deckSha256'])
            check('original example mesh remains unchanged', hashlib.sha256(mesh_path.read_bytes()).hexdigest() == original_mesh_hash)
            check('model tree shows changed material', window.model_tree.findItems('Materials',
                QtCore.Qt.MatchFlag.MatchRecursive, 0)[0].child(0).text(1) == '105 GPa')
            window.raise_()
            app.processEvents()
            check('edited native result and model tree capture', capture(window, output / 'edited-result.png'))
            finish()
        except Exception as error:
            finish(error)

    window.job.completed.connect(completed)
    timeout = QtCore.QTimer(window)
    timeout.setSingleShot(True)
    timeout.timeout.connect(lambda: finish('Editor workflow exceeded 120 seconds'))
    timeout.start(120000)
    try:
        window.run_example()
    except Exception as error:
        finish(error)

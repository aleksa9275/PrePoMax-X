"""Bounded two-box native CAD/mesh/editor/solver integration, with analytical fields."""
import hashlib
import json
from pathlib import Path
from PyQt6 import QtCore, QtWidgets
from analysis_editor import AnalysisDialog
from viewport import decode


def begin(app, window, source, definition_path, output):
    output.mkdir(parents=True, exist_ok=False)
    report = {'success': False, 'transport': window.transport, 'checks': []}
    state = {'done': False}

    def check(name, passed):
        report['checks'].append({'name': name, 'passed': bool(passed)})
        if not passed:
            raise ValueError(name)

    def finish(error=None):
        if state['done']:
            return
        # Owned workers/processes must finish before Qt is torn down.
        if window.busy:
            window.cancel_operation()
            QtCore.QTimer.singleShot(100, lambda: finish(error or 'Probe timed out'))
            return
        state['done'] = True
        report['success'] = error is None
        if error:
            report['error'] = str(error)
        (output / 'workflow.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report), flush=True)
        window.editor_dirty = False
        window.close()
        app.exit(0 if error is None else 1)

    def imported(result):
        try:
            check('native retained two-part import', result['success'] and len(window.cad_document.parts) == 2)
            state['document'] = window.cad_document
            state['cadRoot'] = window.cad_document.root
            window.start_cad_mesh(3)
            check('meshing disables replacement and solve', window.busy and not window.open_action.isEnabled()
                  and not window.run_action.isEnabled() and window.cancel_action.isEnabled())
        except Exception as error:
            finish(error)

    def apply_controls():
        dialog = app.activeModalWidget()
        try:
            check('real static editor opens for generated C3D4', isinstance(dialog, AnalysisDialog))
            dialog.materials.table.item(0, 1).setText('0')
            dialog.apply()
            check('invalid material blocks submission', dialog.definition is None and dialog.isVisible() and not window.job.active)
            dialog.materials.table.item(0, 1).setText('1000')
            dialog.apply()
            check('original C# validation accepts C3D4 controls', dialog.definition is not None and dialog.validation['success'])
            report['validation'] = dialog.validation
        except Exception as error:
            if isinstance(dialog, QtWidgets.QDialog):
                dialog.reject()
            state['error'] = error

    def meshed(result):
        try:
            check('all parts publish one linear tetrahedral model', result['success'] and
                  len(window.model_scene['cadMesh']['parts']) == 2 and
                  all(e['vtkCellType'] == 10 for e in window.model_scene['elements']))
            scene = window.model_scene
            report['nodes'], report['elements'] = len(scene['nodes']), len(scene['elements'])
            check('source CAD face and edge sets retained', {'PART_1_FACE_5', 'PART_2_FACE_6', 'PART_1_EDGE_1'} <=
                  {s['name'] for s in scene['nodeSets']})
            state['meshRoot'] = window.cad_mesh.root
            state['meshHash'] = hashlib.sha256(window.mesh_bytes).hexdigest()
            from cad_region_probe import prepare, assign
            prepare(app, window, output, check)
            window.definition = json.loads(definition_path.read_text())  # Explicit analytical test inputs.
            assign(window.definition)
            QtCore.QTimer.singleShot(100, apply_controls)
            window.configure_action.trigger()
            if state.get('error'):
                raise state['error']
            check('applied analysis can run', window.analysis_valid)
            window.run_model()
            check('region edits and view switching are disabled while solving', not window.regions.create.isEnabled() and not window.regions.view.isEnabled())
        except Exception as error:
            finish(error)

    def solved(result):
        try:
            check('actual native CalculiX completes', result['success'] and result['outcome']['solverExecuted'])
            report['job'] = result
            scene = decode(Path(result['directory']) / 'analysis.frd')
            check('original FRD reader and viewport retain C3D4',
                  len(scene['nodes']) == report['nodes'] and len(scene['elements']) == report['elements'] and
                  all(e['vtkCellType'] == 10 for e in scene['elements']) and window.mapper.GetScalarVisibility() == 1)
            fields = {f['name']: f['components'] for f in scene['fields']}
            nodes = {n['id']: n for n in scene['nodes']}
            errors = [abs(fields['DISP']['U3'][i] - .001 * nodes[n]['z'])
                      for i, n in enumerate(scene['nodeIdsInValueOrder'])]
            report['maximumDisplacementError'] = max(errors)
            check('analytical affine displacement at every node', max(errors) <= 2e-8 and
                  max(map(abs, fields['DISP']['U1'])) <= 1e-12 and max(map(abs, fields['DISP']['U2'])) <= 1e-12)
            check('analytical unit axial stress at every node', max(abs(v - 1) for v in fields['STRESS']['S33']) <= 1e-6)
            frozen = Path(result['inputDirectory']) / 'cad'
            identity = json.loads((frozen / 'identity.json').read_text())
            check('frozen job records original mesh and both CAD parts', identity['baseMeshSha256'] == state['meshHash'] and
                  len(identity['mapping']['parts']) == 2 and identity['elementOrder'] == 1)
            check('frozen job retains selected CAD region provenance', len(identity['authoredRegions']) == 8 and
                  identity['authoredRegions'][3]['name'] == 'SelectedSolids')
            before = window.mesh_bytes
            window.regions.view.setCurrentIndex(window.regions.view.findData('cad'))
            window.regions.view.setCurrentIndex(window.regions.view.findData('results'))
            check('CAD and result views retain selected model and decoded results', window.regions.result is not None and window.scene is window.regions.result[0] and
                  window.current_path.name == 'analysis.frd' and window.mesh_bytes == before)
            check('frozen native recipe verified', hashlib.sha256((frozen / 'tool-build-receipt.json').read_bytes()).hexdigest() == identity['toolReceiptSha256'])
            check('all frozen CAD bytes verified', all(hashlib.sha256((frozen / row['file']).read_bytes()).hexdigest() == row['sha256'] for row in identity['files']))
            window.raise_()
            app.processEvents()
            if window.transport == 'frame-bridge':
                captured = window.grab()
            else:
                origin = window.mapToGlobal(QtCore.QPoint(0, 0))
                captured = window.screen().grabWindow(0, origin.x(), origin.y(), window.width(), window.height())
            check('result display captured', captured.save(str(output / 'result.png')))
            # A changed retained mesher output cannot be submitted again.
            target = window.cad_mesh.volumes[0]
            target.write_bytes(target.read_bytes() + b'\n# changed\n')
            try:
                window.cad_mesh.freeze(output / 'rejected-freeze')
            except ValueError:
                check('retained input tampering blocks a later submission', True)
            else:
                raise ValueError('Changed mesher output was accepted')
            window.release_cad()
            check('document cleanup keeps immutable job inputs', not state['cadRoot'].exists() and
                  not state['meshRoot'].exists() and (frozen / 'identity.json').is_file() and
                  not window.regions.refs and window.regions.result is None)
            finish()
        except Exception as error:
            finish(error)

    window.cad_completed.connect(imported)
    window.mesh_completed.connect(meshed)
    window.job.completed.connect(lambda result: QtCore.QTimer.singleShot(250, lambda: solved(result)))
    QtCore.QTimer.singleShot(180000, lambda: finish('Native CAD workflow probe timeout'))
    window.start_cad_import(source)

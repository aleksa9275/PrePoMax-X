"""Original plane/axisymmetric desktop integration with independent elasticity checks."""
import hashlib
import json
import math
from pathlib import Path
from PyQt6 import QtCore, QtWidgets
from unittest.mock import patch
from analysis_editor import AnalysisDialog
from jobs import examples
from results_tools import read_histories, export_histories

CASES = ('plane-stress', 'plane-strain', 'axisymmetric', 'axisymmetric-cylinder')


def verify_fields(case, scene, history, check):
    fields = {f['name']: f['components'] for f in scene['fields']}
    nodes = {n['id']: n for n in scene['nodes']}
    check(case+' model space retained', scene['ModelSpace'] == ('Axisymmetric' if case.startswith('axisymmetric') else 'PlaneStress' if case == 'plane-stress' else 'PlaneStrain'))
    check(case+' original 2D topology decoded', {e['vtkCellType'] for e in scene['elements']} <= {5, 9, 22, 23})
    check(case+' fields and histories available', {'DISP', 'STRESS', 'TOSTRAIN', 'FORC'} <= fields.keys() and bool(history['histories']))
    if case == 'axisymmetric-cylinder':
        errors = {'radialDisplacement': 0., 'radialStress': 0., 'hoopStress': 0., 'axialStress': 0.}
        for j, identity in enumerate(scene['nodeIdsInValueOrder']):
            r = nodes[identity]['x']; a, b, nu, e = 1/3, 4/3, .25, 1000
            expected = {'radialDisplacement': ((1-nu)*a*r+(1+nu)*b/r)/e,
                        'radialStress': a-b/r**2, 'hoopStress': a+b/r**2, 'axialStress': 0.}
            for key, field, component in [('radialDisplacement', 'DISP', 'U1'), ('radialStress', 'STRESS', 'S11'),
                                          ('hoopStress', 'STRESS', 'S33'), ('axialStress', 'STRESS', 'S22')]:
                errors[key] = max(errors[key], abs(fields[field][component][j]-expected[key]))
        # FRD averages the original expanded 2-degree segment. The angular
        # projection alone is up to u*(1-cos(1 degree)), about 3e-7 here.
        check(case+' independent Lame displacement with original segment projection', errors['radialDisplacement'] < 5e-7)
        check(case+' independent radial/hoop/axial stresses', max(errors[k] for k in ('radialStress', 'hoopStress', 'axialStress')) < .002)
        return errors
    diagnostics = {}
    suffixes = ('3', '6', '4', '4R', '8', '8R')
    for part, suffix in enumerate(suffixes):
        origin = 1+2*part if case == 'axisymmetric' else 2*part
        errors = {'displacement': 0., 'axialDisplacement': 0., 'radialDisplacement': 0., 'stress': 0.}
        for j, identity in enumerate(scene['nodeIdsInValueOrder']):
            n = nodes[identity]
            if not origin-1e-7 <= n['x'] <= origin+1+1e-7:
                continue
            ux = -.00025*n['x'] if case == 'axisymmetric' else (-.0003125 if case == 'plane-strain' else -.00025)*(n['x']-origin)
            uy = (.0009375 if case == 'plane-strain' else .001)*n['y']
            errors['displacement'] = max(errors['displacement'], abs(fields['DISP']['U1'][j]-ux), abs(fields['DISP']['U2'][j]-uy))
            errors['axialDisplacement'] = max(errors['axialDisplacement'], abs(fields['DISP']['U2'][j]-uy))
            errors['radialDisplacement'] = max(errors['radialDisplacement'], abs(fields['DISP']['U1'][j]-ux))
            errors['stress'] = max(errors['stress'], *(abs(fields['STRESS'][c][j]-v) for c, v in [('S11', 0), ('S22', 1), ('S33', .25 if case == 'plane-strain' else 0)]))
        # Original coarse CAX3/CAX4R discretization is retained as an explicit
        # diagnostic. Do not bless it by loosening the exact-patch expectation.
        errors['exactPatchPassed'] = errors['displacement'] < 1e-8 and errors['stress'] < 1e-4
        if case != 'axisymmetric' or suffix not in ('3', '4R'):
            if case == 'axisymmetric':
                check(case+' '+suffix+' independent axial response and stress', errors['axialDisplacement'] < 1e-8 and errors['stress'] < 1e-4)
                check(case+' '+suffix+' radial response with original segment projection', errors['radialDisplacement'] < 1e-6)
            else:
                check(case+' '+suffix+' independent free-response patch', errors['exactPatchPassed'])
        diagnostics[suffix] = errors
    reactions = [h for h in history['histories'] if h['FieldName'] == 'FORCES' and h['ComponentName'] == 'RF2']
    lower = sum(h['values'][-1] for h in reactions if h['BaseSetName'] == 'BOTTOM')
    upper = sum(h['values'][-1] for h in reactions if h['BaseSetName'] == 'TOP')
    check(case+' DAT force equilibrium', abs(lower+upper) < 1e-5)
    if case != 'axisymmetric':
        check(case+' pressure resultant includes section thickness', abs(upper-12) < 1e-5)
    diagnostics['fullRevolutionReaction'] = upper
    if case == 'axisymmetric':
        diagnostics['continuumReaction'] = sum(math.pi*((2+2*i)**2-(1+2*i)**2) for i in range(6))
    return diagnostics


def begin(app, w, output):
    output.mkdir(parents=True, exist_ok=False)
    report = {'success': False, 'transport': w.transport, 'checks': [], 'runs': {}}
    state = {'index': 0, 'done': False}
    w.confirm_discard = lambda: True
    def check(name, passed):
        report['checks'].append({'name': name, 'passed': bool(passed)})
        if not passed:
            raise ValueError(name)
    def finish(error=None):
        if state['done']:
            return
        if w.busy:
            w.cancel_operation(); QtCore.QTimer.singleShot(100, lambda: finish(error or 'Timeout')); return
        state['done'] = True; report['success'] = error is None
        if error:
            report['error'] = str(error)
        (output/'workflow.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps({'success': report['success'], 'checks': len(report['checks']), 'error': report.get('error')}), flush=True)
        w.editor_dirty = False; w.close(); app.exit(0 if error is None else 1)
    def guarded(fn):
        def call(*args):
            try: fn(*args)
            except Exception as error: finish(error)
        return call
    def controls():
        dialog = app.activeModalWidget()
        try:
            check(state['case']+' configuration opens', isinstance(dialog, AnalysisDialog))
            check(state['case']+' model space explicit', dialog.model_space.currentData() == w.definition['modelSpace'])
            check(state['case']+' configuration captured', dialog.grab().save(str(output/(state['case']+'-configure.png'))))
            dialog.apply(); check(state['case']+' original validation passes', dialog.definition is not None)
        except Exception as error:
            state['dialogError'] = str(error)
            if dialog: dialog.reject()
    @guarded
    def prepare():
        case = CASES[state['index']]; state['case'] = case
        mesh = examples()/(case+'.inp'); spec = json.loads(mesh.with_suffix('.json').read_text())
        w.editor_dirty = False; w.load(mesh, as_model=True, definition=spec)
        state['meshHash'] = hashlib.sha256(w.mesh_bytes).hexdigest()
        QtCore.QTimer.singleShot(100, controls); w.configure_model()
        if state.get('dialogError'): raise ValueError(state['dialogError'])
        w.run_action.trigger(); check(case+' native job starts', w.busy)
    @guarded
    def solved(result):
        from viewport import decode
        from solid_formulations import SolidFormulationDialog
        case = state['case']; check(case+' native solver completes', result['success'])
        directory = Path(result['directory']); scene = decode(directory/'analysis.frd'); history = read_histories(directory/'analysis.dat')
        check(case+' result displayed', w.scene['SourceSha256'] == scene['SourceSha256'])
        check(case+' immutable input', hashlib.sha256(w.mesh_bytes).hexdigest() == state['meshHash'] and json.loads((Path(result['inputDirectory'])/'analysis.json').read_text()) == w.definition)
        metrics = verify_fields(case, scene, history, check)
        dialog = SolidFormulationDialog(w, w.model_scene)
        check(case+' formulation identity retained', dialog.values() == [b['formulation'] for b in w.model_scene['elementBlocks']])
        export_histories(output/(case+'-histories.csv'), history['histories'])
        # Export the original model mesh, not the solver-expanded result mesh.
        with patch.object(QtWidgets.QFileDialog, 'getSaveFileName', return_value=(str(output/(case+'-export.inp')), 'INP')):
            w.export_mesh_action.trigger()
        check(case+' mesh export succeeds', w.mesh_export_result['originalReadbackPassed'])
        reopened = decode(output/(case+'-export.inp'))
        check(case+' export reopens with topology and formulations', reopened['elements'] == w.model_scene['elements'] and reopened['elementBlocks'] == w.model_scene['elementBlocks'])
        w.result_tools.deformed.setChecked(True); w.result_tools.outline.setChecked(True); w.result_tools.scale.setValue(25)
        w.fit(); app.processEvents()
        if w.transport == 'frame-bridge': picture = w.grab()
        else:
            origin = w.mapToGlobal(QtCore.QPoint(0, 0))
            picture = w.screen().grabWindow(0, origin.x(), origin.y(), w.width(), w.height())
        check(case+' viewport captured', picture.save(str(output/(case+'.png'))))
        report['runs'][case] = {'job': result, 'analytical': metrics}; state['index'] += 1
        if state['index'] == len(CASES): finish()
        else: QtCore.QTimer.singleShot(50, prepare)
    w.job.completed.connect(lambda result: QtCore.QTimer.singleShot(200, lambda: solved(result)))
    QtCore.QTimer.singleShot(300000, lambda: finish('Workflow timeout')); QtCore.QTimer.singleShot(0, prepare)

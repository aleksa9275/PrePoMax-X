#!/usr/bin/env python3
"""Verify a copied app's edited controls, generated deck and native numerical run."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--viewport', choices=('frame-bridge', 'native-cocoa'), default='native-cocoa')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {'success': False, 'checks': [], 'scope': 'Local copied-app edited static cube; no clean OS or full parity acceptance'}

    def check(name, passed):
        report['checks'].append({'name': name, 'passed': bool(passed)})
        if not passed:
            raise ValueError(name)

    try:
        env = dict(os.environ, PATH='/usr/bin:/bin', DOTNET_ROOT='/nonexistent-external-dotnet')
        for name in ('PYTHONHOME', 'PYTHONPATH', 'DYLD_LIBRARY_PATH', 'DYLD_FRAMEWORK_PATH'):
            env.pop(name, None)
        executable = args.app.resolve() / 'Contents/MacOS/PrePoMax-X-Viewport'
        command = [str(executable), '--editor-probe', str(out / 'gui'), '--jobs-root', str(out / 'jobs'), '--viewport', args.viewport]
        report['command'] = command
        done = subprocess.run(command, capture_output=True, env=env, timeout=180)
        (out / 'app.stdout').write_bytes(done.stdout)
        (out / 'app.stderr').write_bytes(done.stderr)
        report['exitCode'] = done.returncode
        gui = json.loads((out / 'gui/editor.json').read_text())
        check('packaged editor workflow passes', done.returncode == 0 and gui['success'])
        baseline = Path(gui['baseline']['directory'])
        edited = Path(gui['edited']['directory'])
        definitions = json.loads((Path(gui['edited']['inputDirectory']) / 'analysis.json').read_text())
        check('submitted material is 105 GPa', definitions['materials'][0]['youngsModulus'] == '105 GPa')
        check('submitted nodal force is 50 N per node', definitions['step']['loads'][0]['forcePerNode'] == ['50 N', '0', '0'])
        decks = module('deck_checks', ROOT / 'X/Analysis/static_deck_checks.py')
        original = decks.snapshot((baseline / 'analysis.inp').read_text())
        changed = decks.snapshot((edited / 'analysis.inp').read_text())

        def edited_deck_ok(snapshot):
            return (snapshot['materials'] == {'ELASTIC': (105000.0, 0.3)} and
                snapshot['loads'] == {(node, 1): 50.0 for node in (2, 3, 6, 7)} and
                all(snapshot[key] == original[key] for key in ('nodes', 'elements', 'sections',
                    'constraints', 'outputs', 'stepCount', 'staticCount', 'endCount')))

        check('original deck reflects edits and preserves mesh supports sections outputs', edited_deck_ok(changed))
        tampered = decks.snapshot((edited / 'analysis.inp').read_text().replace('X1, 1, 50', 'X1, 1, 51'))
        check('altered edited-deck force rejected', not edited_deck_ok(tampered))
        reference = module('solver_reference', ROOT / 'X/Feasibility/Solver/run-reference.py')
        baseline_data = reference.parse_dat((baseline / 'analysis.dat').read_text())
        baseline_checks = reference.analytical_checks(baseline_data)
        check('all seven original baseline analytical checks pass', all(item['passed'] for item in baseline_checks))
        data = reference.parse_dat((edited / 'analysis.dat').read_text())
        coordinates = original['nodes']
        displacements, forces, stresses = [data.get(name, []) for name in ('displacements', 'forces', 'stresses')]
        check('edited displacement IDs unchanged', sorted(int(row[0]) for row in displacements) == list(range(1, 9)))
        check('edited force IDs unchanged', sorted(int(row[0]) for row in forces) == list(range(1, 9)))
        # Independent uniform-strain cube expectation, unchanged absolute bounds.
        def displacement_ok(rows):
            return len(rows) == 8 and all(abs(row[k+1] - (200/105000 * coordinates[int(row[0])][0],
                -0.3*200/105000 * coordinates[int(row[0])][1],
                -0.3*200/105000 * coordinates[int(row[0])][2])[k]) <= 1e-9
                for row in rows for k in range(3))
        check('edited displacements match 200 N and 105 GPa', displacement_ok(displacements))
        check('edited stresses retain eight integration points', len(stresses) == 8 and all(int(row[0]) == 1 for row in stresses))
        check('edited axial stress is 200 MPa with transverse/shear zero', len(stresses) == 8 and
              all(abs(row[2]-200) <= 1e-4 and all(abs(v) <= 1e-5 for v in row[3:]) for row in stresses))
        reaction = sum(row[1] for row in forces if int(row[0]) in (1, 4, 5, 8))
        check('edited support reaction balances 200 N', len(forces) == 8 and abs(reaction+200) <= 1e-5)
        check('edited global nodal-force sum zero', len(forces) == 8 and all(abs(sum(row[k+1] for row in forces)) <= 1e-5 for k in range(3)))
        altered = [row[:] for row in displacements]
        altered[0][1] += 0.01
        check('altered edited displacement rejected', not displacement_ok(altered))
        check('edited displacement is four times baseline', abs(next(row[1] for row in displacements if int(row[0]) == 2) -
              4*next(row[1] for row in baseline_data['displacements'] if int(row[0]) == 2)) <= 1e-9)
        report.update(success=True, guiChecks=gui['checks'], baselineAnalyticalChecks=baseline_checks,
            baselineDirectory=str(baseline), editedDirectory=str(edited), expected={'modulusMPa': 105000,
            'forcePerNodeN': 50, 'totalAxialForceN': 200, 'stressMPa': 200, 'loadedFaceDisplacementMm': 200/105000},
            originalTolerances={'displacement': 1e-9, 'axialStress': 1e-4, 'transverseStress': 1e-5, 'force': 1e-5},
            baselineDeckSha256=hashlib.sha256((baseline / 'analysis.inp').read_bytes()).hexdigest(),
            editedDeckSha256=hashlib.sha256((edited / 'analysis.inp').read_bytes()).hexdigest(),
            externalBuildToolsOnPath=False, developerIdSigned=False, notarized=False)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        report['error'] = str(error)
    (out / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: report.get(key) for key in ('success', 'editedDirectory', 'error')}))
    return 0 if report['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

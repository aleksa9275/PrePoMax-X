#!/usr/bin/env python3
"""Runs the Avalonia probe areas (ProbeAreas.cs) on an app folder and writes one report.

  python3 X/App/FrontEnd/run_probe_areas.py --app X/Build/artifacts/app-mac/app --output DIR [--area forms ...]

forms:    the bridge mesh deck (.project/reports/editable-solid-workflow/runs/bridge/baseline/mesh.inp)
geometry: X/UI/fixtures/cube.brep
results:  the solid project of the latest check run (X/Checks/artifacts/*/controller-current/solid/project.pmx;
          --project overrides), solved with the app's CalculiX
elements: X/Analysis/StaticDeck/c3d10-force.inp
Each run is a separate application start (hard timeout); history.pmh is removed after each.
"""
import argparse
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def latest_project():
    found = sorted(ROOT.glob('X/Checks/artifacts/*/controller-current/solid/project.pmx'))
    return found[-1] if found else None


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--app', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--area', action='append', choices=('forms', 'geometry', 'results', 'elements'))
    p.add_argument('--project', type=Path)
    a = p.parse_args()
    fixtures = {
        'forms': ROOT / '.project/reports/editable-solid-workflow/runs/bridge/baseline/mesh.inp',
        'geometry': ROOT / 'X/UI/fixtures/cube.brep',
        'results': a.project or latest_project(),
        'elements': ROOT / 'X/Analysis/StaticDeck/c3d10-force.inp',
    }
    a.output.mkdir(parents=True, exist_ok=True)
    summary = {}
    for area in a.area or ['forms', 'geometry', 'results', 'elements']:
        fixture = fixtures[area]
        prefix = a.output / area
        env = dict(os.environ, PREPOMAXX_UI_PROBE='avalonia', PREPOMAXX_UI_PROBE_AREA=area,
                   PREPOMAXX_UI_PROBE_OUTPUT=str(prefix), PREPOMAXX_UI_PROBE_TIMEOUT='420',
                   DOTNET_ROLL_FORWARD=os.environ.get('DOTNET_ROLL_FORWARD', 'Major'))
        (a.output / (area + '.json')).unlink(missing_ok=True)
        with open(a.output / (area + '.log'), 'w') as log:
            code = subprocess.run(['timeout', '-s', 'KILL', '480', 'dotnet', str(a.app.resolve() / 'PrePoMax.dll'),
                                   '-f', str(Path(fixture).resolve()), '-u', 'MM_TON_S_C'],
                                  env=env, stdout=log, stderr=subprocess.STDOUT).returncode
        (a.app / 'history.pmh').unlink(missing_ok=True)
        report = json.loads((a.output / (area + '.json')).read_text()) if (a.output / (area + '.json')).exists() else {}
        checks = report.get('checks', [])
        summary[area] = {'fixture': str(fixture), 'exit': code, 'success': report.get('success', False),
                         'passed': sum(1 for c in checks if c['passed']), 'checks': len(checks),
                         'failed': [c['name'] + ': ' + str(c.get('detail', '')) for c in checks if not c['passed']],
                         'error': report.get('error')}
        print(area, summary[area]['passed'], '/', summary[area]['checks'], 'success' if summary[area]['success'] else 'FAILED',
              summary[area]['failed'] or '', (summary[area]['error'] or '')[:300])
    (a.output / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n')
    raise SystemExit(0 if all(s['success'] for s in summary.values()) else 1)


if __name__ == '__main__':
    main()

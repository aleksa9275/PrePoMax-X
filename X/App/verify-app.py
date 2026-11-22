#!/usr/bin/env python3
"""Focused checks of the original application on the Avalonia front end (X/App; check.py area "app"). Replaced the
Qt workbench's X/UI/verify-ui.py in M3-1b (D065).

  python3 X/App/verify-app.py --output OUT.json                      # sources and build
  python3 X/App/verify-app.py --output OUT.json --launcher L [--scripts]

Always: the generated original form classes and domain source lists are current (X/UI/generate-original-forms.py
--check, X/Domain/domain_sources.py --check) and X/App builds. With --launcher (a package's launcher, e.g.
PrePoMax-X.app/Contents/MacOS/PrePoMax-X, or a Linux session's launch.sh from X/Build/Linux/session.py) and a display:
the app probe and the four probe areas (FrontEnd/run_probe_areas.py), the fixtures copied out of the repository.
--scripts adds upstream's Python API tests Test_Analysis, Test_Model_Materials_Sections, Test_Model_Meshing and
Test_Model_Meshing_QuadWild_Transfinite through the original command line (-g No). Without a launcher the GUI and
script checks are reported as pending, never as passed.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCRIPTS = ('Test_Analysis:cube.inp', 'Test_Model_Materials_Sections:cube.inp', 'Test_Model_Meshing:cube.stl',
           'Test_Model_Meshing_QuadWild_Transfinite:box_and_cylinder.brep')


def sha(path):
    with open(path, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--expect-os')
    p.add_argument('--expect-architecture')
    p.add_argument('--launcher', type=Path)
    p.add_argument('--scripts', action='store_true')
    a = p.parse_args()
    output = a.output.resolve()
    folder = output.with_suffix('')
    folder.mkdir(parents=True, exist_ok=True)
    arch = {'arm64': 'Arm64', 'aarch64': 'Arm64', 'x86_64': 'X64', 'amd64': 'X64'}.get(platform.machine().lower())
    report = {'success': False, 'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
              'host': {'os': platform.system(), 'architecture': arch}, 'steps': [], 'pending': []}
    env = {**os.environ, 'DOTNET_ROLL_FORWARD': os.environ.get('DOTNET_ROLL_FORWARD', 'Major'), 'AVALONIA_TELEMETRY_OPTOUT': '1'}

    def run(name, command, timeout=3600):
        started = time.monotonic()
        done = subprocess.run([str(x) for x in command], cwd=ROOT, env=env, capture_output=True, text=True, timeout=timeout)
        log = folder / (name + '.log')
        log.write_text(done.stdout + done.stderr)
        report['steps'].append({'name': name, 'arguments': [str(x) for x in command], 'passed': done.returncode == 0,
                                'exitCode': done.returncode, 'seconds': round(time.monotonic() - started, 3),
                                'log': str(log), 'logSha256': sha(log)})
        if done.returncode:
            raise RuntimeError(name + ' failed; see ' + str(log))
        return done.stdout

    try:
        if (a.expect_os and a.expect_os != platform.system()) or (a.expect_architecture and a.expect_architecture != arch):
            raise ValueError('Unexpected native host')
        run('source-lists', [sys.executable, ROOT / 'X/Domain/domain_sources.py', '--check'])
        build = ['dotnet', 'build', '-c', 'Release', '--disable-build-servers', '-m:1', '-p:UseSharedCompilation=false', '-v:minimal']
        run('form-extractor-build', [*build, ROOT / 'X/UI/FormSourceGen/FormSourceGen.csproj', '-o', folder / 'extractor'])
        run('original-form-classes', [sys.executable, ROOT / 'X/UI/generate-original-forms.py', '--check',
                                      '--extractor', folder / 'extractor/FormSourceGen.dll'])
        run('build', [*build, ROOT / 'X/App/PrePoMax/PrePoMax.csproj'])
        if a.launcher:
            launcher = a.launcher.resolve()
            fixtures = folder / 'fixtures'
            fixtures.mkdir(exist_ok=True)
            mesh = fixtures / 'app-mesh.inp'
            shutil.copy2(ROOT / '.project/reports/editable-solid-workflow/runs/bridge/baseline/mesh.inp', mesh)
            probe_env = {'PREPOMAXX_UI_PROBE': 'avalonia', 'PREPOMAXX_UI_PROBE_OUTPUT': str(folder / 'app-probe'),
                         'PREPOMAXX_SESSION_TIMEOUT': '240'}
            env.update(probe_env)
            run('app-probe', ['timeout', '-s', 'KILL', '260', launcher, '-f', mesh, '-u', 'MM_TON_S_C'], timeout=300)
            for key in probe_env:
                env.pop(key)
            probe = json.loads((folder / 'app-probe.json').read_text())
            report['appProbe'] = {'success': probe.get('success'), 'passed': sum(c['passed'] for c in probe['checks']),
                                  'checks': len(probe['checks'])}
            if probe.get('success') is not True:
                raise RuntimeError('app probe failed: ' + str([c['name'] for c in probe['checks'] if not c['passed']]))
            run('probe-areas', [sys.executable, HERE / 'FrontEnd/run_probe_areas.py', '--launcher', launcher,
                                '--output', folder / 'areas', '--fixtures', fixtures])
            report['probeAreas'] = json.loads((folder / 'areas/summary.json').read_text())
            if a.scripts:
                scripts = folder / 'scripts'
                if scripts.exists():
                    shutil.rmtree(scripts)
                shutil.copytree(ROOT / 'APIs/Python/Test_Scripts/Models', scripts / 'Models')
                env['PREPOMAXX_SESSION_TIMEOUT'] = '900'
                for entry in SCRIPTS:
                    name, model = entry.split(':')
                    shutil.copy2(ROOT / 'APIs/Python/Test_Scripts' / (name + '.py'), scripts / (name + '.py'))
                    work = scripts / ('work-' + name)
                    work.mkdir()
                    run('script-' + name, ['timeout', '-s', 'KILL', '950', launcher, '-f', scripts / 'Models' / model, '-u', 'MM_TON_S_C',
                                           '--script', scripts / (name + '.py'), '-g', 'No', '-x', 'Yes', '-w', work], timeout=1000)
            else:
                report['pending'].append("upstream's Python API tests: --scripts not given")
        else:
            report['pending'].append('app probe, probe areas and scripts: no --launcher (a package and a display)')
        report['success'] = True
    except Exception as error:
        report['error'] = str(error)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'success': report['success'], 'steps': len(report['steps']), 'pending': report['pending'],
                      'error': report.get('error')}))
    return 0 if report['success'] else 1


if __name__ == '__main__':
    sys.exit(main())

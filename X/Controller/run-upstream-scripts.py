#!/usr/bin/env python3
"""Run upstream's Python API test scripts (APIs/Python/Test_Scripts) on the headless original Controller.

Each script's own header gives its PrePoMax.com command line; this reads it with upstream's Run_Tests.py
(read_tests/collect) instead of keeping a second list, and maps -f, -u and --scriptArgs to
X/Controller/Headless (the original batch start: a new 3D model in the unit system, then the import).

What the headless host does not have is reported as pending, never as passed: runs whose header expects
a batch run report (--report checks), a non-zero exit status of the batch contract, the automation server
(--rpc), or scripts that start PrePoMax.com processes themselves (-r/-p regenerations). Those need the
original command line, which runs in FrmMain (M2: FrmMain whole).

  python3 X/Controller/run-upstream-scripts.py --output DIR --python-profile P --native-tools T \
      [--solver REGISTRY ID DIRECTORY --default-solver-type Spooles] [--filter Composite ...]
"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'APIs/Python/Test_Scripts'
HEADLESS = ROOT / 'X/Controller/Headless/bin/Release/net10.0/PrePoMaxX.Headless.dll'


def upstream_runner():
    spec = importlib.util.spec_from_file_location('Run_Tests', SCRIPTS / 'Run_Tests.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pending_reason(test):
    if test.report_checks or test.expected_code != 0:
        return 'expects a batch run report or exit status (original PrePoMax.com command line)'
    if '--rpc' in test.switches:
        return 'uses the automation server (original PrePoMax.com command line)'
    source = Path(test.path).read_text(encoding='utf-8')
    if 'subprocess' in source and 'PrePoMax' in source:
        return 'starts PrePoMax.com runs itself (original command line)'
    return None


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--python-profile', type=Path, required=True)
    p.add_argument('--native-tools', type=Path, required=True)
    p.add_argument('--solver', nargs=3, metavar=('REGISTRY', 'ID', 'DIRECTORY'))
    p.add_argument('--default-solver-type')
    p.add_argument('--filter', nargs='+')
    p.add_argument('--build', action='store_true', help='build the headless host first')
    args = p.parse_args()
    if args.output.exists():
        raise SystemExit(f'{args.output} exists; choose a new output directory')
    args.output.mkdir(parents=True)
    env = dict(os.environ, DOTNET_ROLL_FORWARD='Major')
    if args.build or not HEADLESS.exists():
        subprocess.run(['dotnet', 'build', '-c', 'Release', str(ROOT / 'X/Controller/Headless')], check=True, env=env,
                       stdout=subprocess.DEVNULL)
    runner = upstream_runner()
    report = {'host': 'X/Controller/Headless', 'passed': [], 'failed': [], 'pending': []}
    for test in runner.collect(args.filter):
        reason = pending_reason(test)
        if reason:
            report['pending'].append({'test': test.label, 'reason': reason})
            print(f'PENDING {test.label}: {reason}')
            continue
        work = args.output / test.file_stem.replace('.py', '')
        work.mkdir()
        command = ['dotnet', str(HEADLESS), 'run', test.path, str(work), str(args.python_profile.resolve())]
        if test.model is not None:
            model = (work.parent / runner.RESULT_WRITER.replace('.py', '') / runner.RESULT_FILE) if test.needs_result \
                else Path(runner.MODELS) / test.model
            command.append(str(model))
        else:
            command.append('')
        command.append(str(args.native_tools.resolve()))
        units = test.switches.get('-u', runner.DEFAULT_UNIT_SYSTEM if test.model is not None else None)
        if units:
            command += ['--unit-system', units]
        if '--scriptArgs' in test.switches:
            command += ['--script-args', test.switches['--scriptArgs']]
        if args.solver:
            command += ['--solver'] + [str(Path(args.solver[0]).resolve()), args.solver[1], str(Path(args.solver[2]).resolve())]
        if args.default_solver_type:
            command += ['--default-solver-type', args.default_solver_type]
        started = time.time()
        try:
            done = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
                                  timeout=test.timeout + runner.PROCESS_TIMEOUT_MARGIN)
            code, output = done.returncode, done.stdout.decode('utf-8', 'replace')
        except subprocess.TimeoutExpired:
            code, output = None, 'TIMEOUT'
        (args.output / (test.file_stem + '.log')).write_text(output, encoding='utf-8')
        problems = []
        if code != 0:
            problems.append(f'exit code {code}, expected 0')
        if 'TEST PASSED' not in output:
            problems.append('no TEST PASSED')
        entry = {'test': test.label, 'seconds': round(time.time() - started, 1)}
        if problems:
            entry['problems'] = problems
            report['failed'].append(entry)
        else:
            report['passed'].append(entry)
        print(('PASS ' if not problems else 'FAIL ') + test.label + ('' if not problems else ': ' + '; '.join(problems)))
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f"passed {len(report['passed'])}, failed {len(report['failed'])}, pending {len(report['pending'])}")
    return 1 if report['failed'] else 0


if __name__ == '__main__':
    sys.exit(main())

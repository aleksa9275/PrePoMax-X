#!/usr/bin/env python3
"""Repeat the pinned synthetic CalculiX reference on native Windows x64."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shutil
import struct
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solver', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    reference_folder = ROOT / '.project/reports/local-completion/solver-crossover'
    reference = json.loads((reference_folder / 'reference.json').read_text())
    spec = importlib.util.spec_from_file_location('solver_reference', HERE / 'run-reference.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = {'success': False, 'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
              'evidenceKind': 'Native Windows x64; pinned synthetic solver slice only',
              'host': {'os': platform.system(), 'machine': platform.machine(),
                       'processBits': struct.calcsize('P') * 8, 'python': platform.python_version()},
              'threads': 1, 'privateInputUsed': False,
              'toolSha256': sha(Path(__file__)), 'analyticalCheckerSha256': sha(HERE / 'run-reference.py')}
    try:
        if platform.system() != 'Windows' or platform.machine().lower() not in ('amd64', 'x86_64') or struct.calcsize('P') != 8:
            raise ValueError('Native Windows x64 process is required')
        report['solverFiles'] = {p.name: sha(p) for p in sorted(args.solver.parent.iterdir())
                                 if p.suffix.lower() in {'.exe', '.dll'}}
        report['solverFilesMatchReference'] = report['solverFiles'] == reference['solverFiles']
        report['fixtureSha256'] = sha(HERE / 'uniaxial-cube.inp')
        if not report['solverFilesMatchReference'] or report['fixtureSha256'] != reference['fixtureSha256']:
            raise ValueError('Solver/runtime/fixture differs from the pinned reference; no substitute accepted')
        shutil.copyfile(HERE / 'uniaxial-cube.inp', args.output_dir / 'uniaxial.inp')
        done = subprocess.run([str(args.solver.resolve()), '-i', 'uniaxial'],
                              cwd=args.output_dir, env=dict(os.environ, OMP_NUM_THREADS='1', MKL_NUM_THREADS='1'),
                              capture_output=True, text=True, timeout=120)
        report.update(exitCode=done.returncode, stdout=done.stdout, stderr=done.stderr)
        version = re.search(r'Version\s+([\d.]+)', done.stdout)
        report['solverVersion'] = version.group(1) if version else None
        if done.returncode or report['solverVersion'] != '2.22':
            raise ValueError('Pinned solver execution/version failed')
        blocks = module.parse_dat((args.output_dir / 'uniaxial.dat').read_text())
        report['checks'] = module.analytical_checks(blocks)
        altered = {key: [row[:] for row in rows] for key, rows in blocks.items()}
        altered['displacements'][0][1] += 0.01
        report['negativeControlRejected'] = not all(c['passed'] for c in module.analytical_checks(altered))
        baseline = module.parse_dat((reference_folder / 'uniaxial.dat').read_text())
        report['referenceNumericComparison'] = {}
        for key, tolerance in [('displacements', 1e-9), ('forces', 1e-5), ('stresses', 1e-4)]:
            left, right = sorted(blocks[key]), sorted(baseline[key])
            id_columns = 2 if key == 'stresses' else 1
            shape = len(left) == len(right) and all(len(a) == len(b) and a[:id_columns] == b[:id_columns] for a, b in zip(left, right))
            error = max((abs(a[i] - b[i]) for a, b in zip(left, right)
                         for i in range(id_columns, min(len(a), len(b)))), default=0.0)
            report['referenceNumericComparison'][key] = {'sameIdsAndShape': shape,
                'maximumAbsoluteDifference': error, 'absoluteTolerance': tolerance,
                'matches': shape and error <= tolerance}
        report['outputHashes'] = {p.name: sha(p) for p in sorted(args.output_dir.glob('uniaxial.*'))
                                  if p.suffix in {'.inp', '.dat', '.frd', '.sta', '.cvg'}}
        report['success'] = (all(c['passed'] for c in report['checks']) and report['negativeControlRejected']
                             and all(c['matches'] for c in report['referenceNumericComparison'].values()))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        report['error'] = str(error).replace(str(args.output_dir), '<output>').replace(str(args.solver.parent), '<solver>')
    (args.output_dir / 'reference.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report.get(k) for k in ['success', 'solverVersion', 'checks', 'referenceNumericComparison', 'error']}))
    return 0 if report['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

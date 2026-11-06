#!/usr/bin/env python3
"""Strict original-export/native-reconstruction result comparison, one solver."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def verify(original_deck, native_frd, solver, inspector, output):
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(original_deck, output/'analysis.inp')
    env = dict(os.environ, OMP_NUM_THREADS='1', CCX_NPROC_RESULTS='1', CCX_NPROC_STIFFNESS='1')
    with (output/'solver.log').open('w') as log:
        subprocess.run([str(solver.resolve()), '-i', 'analysis'], cwd=output, env=env,
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
    def decode(path):
        command = (['dotnet', str(inspector)] if inspector.suffix == '.dll' else [str(inspector)])
        return json.loads(subprocess.check_output(command+['inspect-frd',str(path.resolve())], text=True))
    original, native = decode(output/'analysis.frd'), decode(native_frd)
    checks = {key: original[key] == native[key] for key in ['nodes','elements','nodeIdsInValueOrder','fields']}
    report = {'success': all(checks.values()), 'checks': checks,
              'originalDeckSha256': hashlib.sha256(original_deck.read_bytes()).hexdigest(),
              'nativeDeckSha256': hashlib.sha256(native_frd.with_suffix('.inp').read_bytes()).hexdigest(),
              'scope': 'One pinned native solver; exact original decoded fields; no tolerance relaxation'}
    (output/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
    return report['success']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ['original_deck','native_frd','solver','inspector','output']: parser.add_argument(name,type=Path)
    args = parser.parse_args()
    raise SystemExit(0 if verify(**vars(args)) else 1)

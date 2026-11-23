#!/usr/bin/env python3
"""Check a CalculiX build's direct solvers against each other: SPOOLES, PaStiX (mixed precision, the CalculiX
default) and PaStiX with PASTIX_MIXED_PRECISION=0 on a solid cantilever (C3D20R) and a thin clamped plate (S8R, the
forum's thin-shell case), plus a nonlinear contact-free NLGEOM run and a frequency step (ARPACK with the solver).

    python3 X/Build/Pastix/verify_solvers.py --ccx <ccx> --work <new folder> [--report report.json]

Passes when every run finishes on the requested threads (SPOOLES: --spooles-threads) (--threads, as PrePoMax's OMP_NUM_THREADS) and the
displacements agree with SPOOLES within the tolerance (relative to the
largest displacement; the frequencies relative to each value).
"""
import argparse
import json
import os
import re
import subprocess
import time
from pathlib import Path


# Failures the original Windows ccx_dynamic.exe shows on the same deck (checked in the CrossOver reference, 23 November
# 2026): CalculiX's mixed-precision PaStiX does not converge on the thin plate (0.32 for 65.1 on Windows, 0.27 here);
# PASTIX_MIXED_PRECISION=0 is the remedy. They are reported as failures with this note.
SAME_ON_WINDOWS = {('plate-static', 'pastix'): 'same wrong result from the original Windows ccx_dynamic.exe (mixed '
                                               'precision on a thin shell); use PASTIX_MIXED_PRECISION=0'}


def block(nx, ny, nz, lx, ly, lz):
    """A C3D20R brick mesh: nodes on the full grid of the quadratic element (corner and mid-side nodes)."""
    nodes, ids = [], {}
    for k in range(2 * nz + 1):
        for j in range(2 * ny + 1):
            for i in range(2 * nx + 1):
                odd = (i % 2) + (j % 2) + (k % 2)
                if odd > 1:
                    continue
                ids[i, j, k] = len(nodes) + 1
                nodes.append((lx * i / (2 * nx), ly * j / (2 * ny), lz * k / (2 * nz)))
    elements = []
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                I, J, K = 2 * i, 2 * j, 2 * k
                c = [(I, J, K), (I + 2, J, K), (I + 2, J + 2, K), (I, J + 2, K),
                     (I, J, K + 2), (I + 2, J, K + 2), (I + 2, J + 2, K + 2), (I, J + 2, K + 2)]
                m = [(I + 1, J, K), (I + 2, J + 1, K), (I + 1, J + 2, K), (I, J + 1, K),
                     (I + 1, J, K + 2), (I + 2, J + 1, K + 2), (I + 1, J + 2, K + 2), (I, J + 1, K + 2),
                     (I, J, K + 1), (I + 2, J, K + 1), (I + 2, J + 2, K + 1), (I, J + 2, K + 1)]
                elements.append([ids[p] for p in c + m])
    return nodes, elements, ids


def solid_deck(solver, step):
    nodes, elements, ids = block(30, 4, 4, 300.0, 40.0, 40.0)
    fixed = [n for (i, j, k), n in ids.items() if i == 0]
    tip = [n for (i, j, k), n in ids.items() if i == 60]
    lines = ['*NODE, NSET=NALL'] + [f'{n + 1}, {x:.6f}, {y:.6f}, {z:.6f}' for n, (x, y, z) in enumerate(nodes)]
    lines += ['*ELEMENT, TYPE=C3D20R, ELSET=EALL'] + [f'{e + 1}, ' + ', '.join(map(str, c[:15])) + ',\n' + ', '.join(map(str, c[15:]))
                                                      for e, c in enumerate(elements)]
    lines += ['*NSET, NSET=FIX'] + [str(n) for n in fixed] + ['*NSET, NSET=TIP'] + [str(n) for n in tip]
    lines += ['*MATERIAL, NAME=STEEL', '*ELASTIC', '210000, 0.3', '*DENSITY', '7.85e-9', '*SOLID SECTION, ELSET=EALL, MATERIAL=STEEL',
              '*BOUNDARY', 'FIX, 1, 3']
    lines += step(solver, len(tip))
    return '\n'.join(lines) + '\n'


def plate_deck(solver, step):
    # 1000 x 1000 x 1 mm plate (span/thickness 1000), clamped edges, pressure: the thin-shell case
    n, size = 40, 1000.0
    ids, nodes = {}, []
    for j in range(2 * n + 1):
        for i in range(2 * n + 1):
            if i % 2 and j % 2:
                continue
            ids[i, j] = len(nodes) + 1
            nodes.append((size * i / (2 * n), size * j / (2 * n), 0.0))
    elements = []
    for j in range(n):
        for i in range(n):
            I, J = 2 * i, 2 * j
            elements.append([ids[I, J], ids[I + 2, J], ids[I + 2, J + 2], ids[I, J + 2],
                             ids[I + 1, J], ids[I + 2, J + 1], ids[I + 1, J + 2], ids[I, J + 1]])
    edge = [v for (i, j), v in ids.items() if i in (0, 2 * n) or j in (0, 2 * n)]
    lines = ['*NODE, NSET=NALL'] + [f'{k + 1}, {x:.6f}, {y:.6f}, {z:.6f}' for k, (x, y, z) in enumerate(nodes)]
    lines += ['*ELEMENT, TYPE=S8R, ELSET=EALL'] + [f'{e + 1}, ' + ', '.join(map(str, c)) for e, c in enumerate(elements)]
    lines += ['*NSET, NSET=FIX'] + [str(v) for v in edge]
    lines += ['*MATERIAL, NAME=STEEL', '*ELASTIC', '210000, 0.3', '*DENSITY', '7.85e-9',
              '*SHELL SECTION, ELSET=EALL, MATERIAL=STEEL', '1.0', '*BOUNDARY', 'FIX, 1, 6']
    lines += step(solver, None)
    return '\n'.join(lines) + '\n'


def static(solver, tip_count, nlgeom=False):
    load = ['*CLOAD', 'TIP, 3, ' + f'{-20000.0 / tip_count:.6f}'] if tip_count else ['*DLOAD', 'EALL, P, 0.001']
    return [f'*STEP{", NLGEOM" if nlgeom else ""}', f'*STATIC, SOLVER={solver}'] + (['0.25, 1.0'] if nlgeom else []) + load + \
           ['*NODE PRINT, NSET=NALL', 'U', '*END STEP']


def frequency(solver, tip_count):
    return ['*STEP', f'*FREQUENCY, SOLVER={solver}', '6', '*END STEP']


def displacements(dat):
    values = {}
    text = dat.read_text(errors='replace')
    last = text.rfind('displacements (vx,vy,vz)')
    for line in text[last:].splitlines()[2:]:
        parts = line.split()
        if len(parts) != 4:
            if values:
                break
            continue
        try:
            values[int(parts[0])] = tuple(float(v) for v in parts[1:])
        except ValueError:
            break
    return values


def frequencies(dat):
    text = dat.read_text(errors='replace')
    i = text.find('E I G E N V A L U E   O U T P U T')
    result = []
    for line in text[i:].splitlines():
        parts = line.split()
        if len(parts) == 5 and parts[0].isdigit():
            result.append(float(parts[3]))   # cycles/time
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--ccx', type=Path, required=True)
    p.add_argument('--work', type=Path, required=True)
    p.add_argument('--report', type=Path)
    p.add_argument('--tolerance', type=float, default=1e-6)
    p.add_argument('--threads', default='4')
    p.add_argument('--spooles-threads', type=int, help='the threads SPOOLES must report (1: a serial SPOOLES build)')
    a = p.parse_args()
    a.work.mkdir(parents=True, exist_ok=False)
    cases = {'solid-static': (solid_deck, lambda s, t: static(s, t)),
             'plate-static': (plate_deck, lambda s, t: static(s, t)),
             'solid-nlgeom': (solid_deck, lambda s, t: static(s, t, True)),
             'solid-frequency': (solid_deck, frequency)}
    variants = [('spooles', 'SPOOLES', {}), ('pastix', 'PASTIX', {}),
                ('pastix-double', 'PASTIX', {'PASTIX_MIXED_PRECISION': '0'})]
    report, ok = {'ccx': str(a.ccx), 'tolerance': a.tolerance, 'cases': {}}, True
    for case, (deck, step) in cases.items():
        results = {}
        for name, solver, extra in variants:
            folder = a.work / case / name
            folder.mkdir(parents=True)
            (folder / 'job.inp').write_text(deck(solver, step))
            env = dict(os.environ, OMP_NUM_THREADS=a.threads, CCX_NPROC_EQUATION_SOLVER=a.threads, **extra)
            started = time.monotonic()
            run = subprocess.run([str(a.ccx.resolve()), '-i', 'job'], cwd=folder, env=env, capture_output=True, text=True)
            (folder / 'ccx.log').write_text(run.stdout + run.stderr)
            elapsed = round(time.monotonic() - started, 2)
            log = run.stdout + run.stderr
            used = 'pastix' if re.search(r'pastix', log, re.I) and solver == 'PASTIX' else solver.lower()
            entry = {'exitCode': run.returncode, 'seconds': elapsed, 'errors': [l for l in log.splitlines() if '*ERROR' in l][:5]}
            dat = folder / 'job.dat'
            if run.returncode == 0 and dat.exists():
                entry['values'] = frequencies(dat) if 'frequency' in case else displacements(dat)
            # Every direct solver runs multithreaded: SPOOLES's MT variant and PaStiX report the threads they use
            # (SPOOLES is serial on ARM64, B022: --spooles-threads 1; it then reports "Using 1 cpu for spooles")
            spooles = re.findall(r'Using up to (\d+) cpu\(s\) for spooles', log) or re.findall(r'Using (1) cpu for spooles', log)
            pastix = re.findall(r'Number of threads per process:\s+(\d+)', log)
            found = pastix if solver == 'PASTIX' else spooles
            entry['solverThreads'] = int(found[0]) if found else 0
            entry['threadsOk'] = entry['solverThreads'] == (int(a.threads) if solver == 'PASTIX' else a.spooles_threads or int(a.threads))
            results[name] = entry
        reference = results['spooles'].get('values')
        for name, entry in results.items():
            values = entry.pop('values', None)
            if not values or not reference:
                entry['pass'] = False
            elif 'frequency' in case:
                entry['frequencies'] = values
                entry['maxRelative'] = max(abs(x - y) / abs(y) for x, y in zip(values, reference)) if len(values) == len(reference) else None
                entry['pass'] = entry['maxRelative'] is not None and entry['maxRelative'] <= a.tolerance
            else:
                scale = max(abs(c) for v in reference.values() for c in v)
                diff = max(abs(c - d) for n, v in values.items() for c, d in zip(v, reference[n]))
                entry['maxDisplacement'] = max(abs(c) for v in values.values() for c in v)
                entry['maxRelative'] = diff / scale
                entry['pass'] = entry['maxRelative'] <= a.tolerance
            entry['pass'] = entry['pass'] and entry['threadsOk']
            if not entry['pass'] and (case, name) in SAME_ON_WINDOWS:
                entry['note'] = SAME_ON_WINDOWS[case, name]   # a recorded failure; it stays one
            ok &= entry['pass']
        report['cases'][case] = results
        print(case, {k: (v['pass'], v.get('maxRelative'), v['seconds'], v['solverThreads']) for k, v in results.items()}, flush=True)
    report['pass'] = ok
    if a.report:
        a.report.write_text(json.dumps(report, indent=2) + '\n')
    print('PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())

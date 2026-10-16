#!/usr/bin/env python3
"""Check only task 0011's controlled cube decks; not a general INP reader."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

COORDINATES = [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
               [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(path):
    result = {'nodes': {}, 'elements': {}, 'nodeSets': {}, 'elementSets': {},
              'materials': {}, 'sections': [], 'steps': [], 'units': None}
    keyword = None
    attributes = {}
    material = None
    step = None
    canonical = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith('**'):
            continue
        if line.startswith('Hash:'):
            match = re.search(r'Unit system:\s*(\w+)', line)
            result['units'] = match.group(1) if match else None
            continue
        canonical.append(re.sub(r'\s+', '', line).upper())
        if line.startswith('*'):
            tokens = [item.strip().upper() for item in line.split(',')]
            keyword = tokens[0]
            attributes = dict(token.split('=', 1) for token in tokens[1:] if '=' in token)
            if keyword == '*MATERIAL':
                material = attributes['NAME']
                result['materials'][material] = {}
            elif keyword == '*SOLID SECTION':
                result['sections'].append({'elementSet': attributes['ELSET'], 'material': attributes['MATERIAL']})
            elif keyword == '*STEP':
                step = {'type': None, 'static': [], 'boundaries': [], 'loads': []}
                result['steps'].append(step)
            elif keyword == '*STATIC':
                step['type'] = 'Static'
            continue
        data = [value.strip().upper() for value in line.split(',') if value.strip()]
        if keyword == '*NODE':
            result['nodes'][int(data[0])] = list(map(float, data[1:]))
        elif keyword == '*ELEMENT':
            result['elements'][int(data[0])] = {'type': attributes['TYPE'], 'connectivity': list(map(int, data[1:]))}
        elif keyword in ('*NSET', '*ELSET'):
            group = 'nodeSets' if keyword == '*NSET' else 'elementSets'
            name = attributes['NSET' if keyword == '*NSET' else 'ELSET']
            result[group].setdefault(name, []).extend(map(int, data))
        elif keyword in ('*ELASTIC', '*DENSITY'):
            result['materials'][material][keyword[1:].lower()] = list(map(float, data))
        elif keyword == '*STATIC':
            step['static'] = list(map(float, data))
        elif keyword == '*BOUNDARY':
            step['boundaries'].append([data[0], *map(float, data[1:])])
        elif keyword == '*CLOAD':
            step['loads'].append([data[0], *map(float, data[1:])])
    return result, canonical


def checks(value, engineering):
    rows = []
    def check(name, observed, expected):
        rows.append({'name': name, 'passed': observed == expected, 'expected': expected, 'observed': observed})
    check('node IDs and coordinates', value['nodes'], dict(enumerate(COORDINATES, 1)))
    check('element ID, type and connectivity', value['elements'], {1: {'type': 'C3D8', 'connectivity': list(range(1, 9))}})
    check('units', value['units'], 'MM_TON_S_C')
    if engineering:
        check('named node sets', value['nodeSets'], {'NALL': list(range(1, 9)), 'X0': [1, 4, 5, 8],
                                                    'Y0': [1, 2, 5, 6], 'Z0': [1, 2, 3, 4], 'X1': [2, 3, 6, 7]})
        check('named element set', value['elementSets'].get('XSOLID'), [1])
        check('material values in MPa and ton/mm3', value['materials'], {'XSTEEL': {'elastic': [210000, 0.3], 'density': [7.85e-9]}})
        check('section-to-material-and-region association', value['sections'], [{'elementSet': 'XSOLID', 'material': 'XSTEEL'}])
        check('one static step', [s['type'] for s in value['steps']], ['Static'])
        step = value['steps'][0] if len(value['steps']) == 1 else {}
        check('initial increment and total time', step.get('static', [])[:2], [1, 1])
        check('region, DOF and displacement values', step.get('boundaries'),
              [['X0', 1, 1, 0], ['Y0', 2, 2, 0], ['Z0', 3, 3, 0]])
        check('load region, DOF and force per node', step.get('loads'), [['X1', 1, 25]])
    else:
        check('mesh-only definitions absent', [value['materials'], value['sections'], value['steps']], [{}, [], []])
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = {'success': False, 'toolSha256': sha(Path(__file__)), 'evidenceScope': 'Controlled export semantics only', 'cases': {}}
    for name, engineering in [('cube-export.inp', False), ('cube-reopened-export.inp', False),
                              ('definitions-reopened-export.inp', True), ('definitions-regenerated-export.inp', True)]:
        path = args.capture_dir / name
        value, canonical = snapshot(path)
        report['cases'][name] = {'sha256': sha(path), 'checks': checks(value, engineering), 'snapshot': value}
    left = snapshot(args.capture_dir / 'definitions-reopened-export.inp')
    right = snapshot(args.capture_dir / 'definitions-regenerated-export.inp')
    report['regeneratedSemanticSnapshotMatches'] = left[0] == right[0]
    report['regeneratedAllNonvolatileDeckLinesMatch'] = left[1] == right[1]
    report['negativeControls'] = []
    for label in ('connectivity', 'material', 'association'):
        altered = deepcopy(left[0])
        if label == 'connectivity': altered['elements'][1]['connectivity'][0] = 8
        elif label == 'material': altered['materials']['XSTEEL']['elastic'][0] += 100
        else: altered['sections'][0]['elementSet'] = 'WRONG'
        report['negativeControls'].append({'name': label, 'rejected': not all(c['passed'] for c in checks(altered, True))})
    report['success'] = (all(c['passed'] for case in report['cases'].values() for c in case['checks'])
                         and report['regeneratedSemanticSnapshotMatches'] and report['regeneratedAllNonvolatileDeckLinesMatch']
                         and all(c['rejected'] for c in report['negativeControls']))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'success': report['success'], 'checks': sum(len(c['checks']) for c in report['cases'].values()),
                      'regeneratedSemanticSnapshotMatches': report['regeneratedSemanticSnapshotMatches']}))
    return 0 if report['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

"""Desktop definition validation contracts using original writer/reference deck."""
import copy
import hashlib
import json


def verify(run, cli, root, work):
    mesh = root / 'X/Analysis/StaticDeck/cube-mesh.inp'
    analysis = root / 'X/Analysis/StaticDeck/cube-analysis.json'
    builder = work / 'build/bin/StaticDeck/release/PrePoMaxX.StaticDeck.dll'
    output = work / 'desktop-reference.inp'
    run(['dotnet', builder, 'build-static', mesh, analysis, output])
    expected_hash = hashlib.sha256(output.read_bytes()).hexdigest()
    command = ['dotnet', cli, '--registry', work / 'absent-registry.json', 'validate-static', mesh, analysis]
    original = json.loads(run(command).stdout)
    if original != {'success': True, 'solverExecuted': False, 'unitSystem': 'mm-N-s-C',
            'nodes': 8, 'elements': 1, 'materials': 1, 'sections': 1, 'constraints': 3,
            'loads': 1, 'nonlinearGeometry': False, 'pressureLoads': 0, 'gravityLoads': 0,
            'deckSha256': expected_hash}:
        raise ValueError('Desktop validation does not match original standalone deck')
    spec = json.loads(analysis.read_text())
    changed = copy.deepcopy(spec)
    changed['materials'][0]['youngsModulus'] = '105 GPa'
    changed['step']['loads'][0]['forcePerNode'][0] = '50 N'
    edited = work / 'desktop-edited.json'
    edited.write_text(json.dumps(changed))
    value = json.loads(run(['dotnet', cli, 'validate-static', mesh, edited]).stdout)
    if not value['success'] or value['solverExecuted'] or value['deckSha256'] == expected_hash:
        raise ValueError('Desktop material/load edit lost before original writer')
    rejected = []
    for label in ('units', 'material', 'node set', 'free-only support'):
        bad = copy.deepcopy(spec)
        if label == 'units': bad['unitSystem'] = ''
        elif label == 'material': bad['sections'][0]['material'] = 'Missing'
        elif label == 'node set': bad['step']['loads'][0]['nodeSet'] = 'Missing'
        else: bad['step']['constraints'][0]['displacements'] = [None, None, None]
        path = work / ('desktop-bad-' + label.replace(' ', '-') + '.json')
        path.write_text(json.dumps(bad))
        done = run(['dotnet', cli, 'validate-static', mesh, path], 1)
        result = json.loads(done.stderr)
        if done.stdout or result['success'] or result['solverExecuted'] or not result.get('error'):
            raise ValueError('Invalid desktop definition reached solver or lost diagnostics')
        rejected.append(label)
    return {'success': True, 'originalDeckSha256': expected_hash,
        'validationWithoutSolverRegistry': original, 'editedDefinition': value,
        'rejected': rejected, 'solverExecuted': False}

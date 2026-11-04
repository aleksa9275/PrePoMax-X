#!/usr/bin/env python3
"""Check PMX static graph values against the official app's reference exports."""
from copy import deepcopy
import json
from pathlib import Path
from runpy import run_path
import struct
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
probe = run_path(str(HERE / 'inspect-static-project.py'))
results = run_path(str(HERE / 'compare-embedded-frd.py'))
snapshot = run_path(str(ROOT / 'X/Feasibility/Data/check-windows-capture.py'))['snapshot']


def number(equation):
    return float(equation.split()[0])


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_graph(graph, expected):
    for key in ('units', 'nodeSets', 'elementSets'):
        actual = graph['unitSystem'] if key == 'units' else graph[key]
        if key != 'units':
            actual = {name.upper(): labels for name, labels in actual.items()}
        require(actual == expected[key], f'Mismatch in {key}')
    properties = {'CaeModel.Elastic': ('elastic', 2), 'CaeModel.Density': ('density', 1)}
    materials = {}
    for material in graph['materials']:
        require(not material['temperatureDependent'], 'Unexpected temperature dependence')
        values = {}
        for prop in material['properties']:
            name, width = properties[prop['type']]
            require(len(prop['rows']) == 1, 'Unexpected material table length')
            values[name] = [number(eq) for eq in prop['rows'][0][:width]]
        materials[material['name']] = values
    require(materials == expected['materials'], 'Material equations differ')
    sections = [{'elementSet': section['region'], 'material': section['material']}
                for section in graph['sections']]
    require(sections == expected['sections'], 'Sections differ')
    require(len(graph['steps']) == len(expected['steps']), 'Step counts differ')
    for step, reference in zip(graph['steps'], expected['steps']):
        times = [step[key] for key in ('initialTimeIncrement', 'timePeriod',
                                      'minTimeIncrement', 'maxTimeIncrement')]
        require(times == reference['static'], 'Incrementation differs')
        constraints = []
        for condition in step['constraints']:
            require(condition['rotations'] == ['Unconstrained'] * 3, 'Unexpected rotations')
            constraints.extend([condition['region'], axis, axis, number(value)]
                               for axis, value in enumerate(condition['displacements'], 1)
                               if value != 'Unconstrained')
        require(constraints == reference['boundaries'], 'Supports differ')
        loads = [[load['region'], axis, number(value)] for load in step['loads']
                 for axis, value in enumerate(load['force'], 1) if number(value)]
        require(loads == reference['loads'], 'Loads differ')


def main(mesh_decoder, graph_decoder, fixtures):
    captures = {}
    for name in ('cube', 'definitions', 'definitions-with-results'):
        actual = probe['inspect'](fixtures / (name + '.pmx'), mesh_decoder, graph_decoder)
        reference = fixtures / ('cube-export.inp' if name == 'cube' else 'definitions-export.inp')
        check_graph(actual['graph'], snapshot(reference)[0])
        captures[name] = actual
    require(captures['definitions']['graph'] == captures['definitions-with-results']['graph'],
            'Embedding a result changed the static graph')

    reference = captures['definitions']
    material = reference['graph']['materials'][0]
    require([prop['rows'] for prop in material['properties']] ==
            [[['210000 MPa', '0.3', '0 °C']], [['7.85E-09 t/mm³', '0 °C']]],
            'Material units or stored equation text changed')
    step = reference['graph']['steps'][0]
    require(step['outputFrequency'] == -2147483648 and step['maxIncrements'] == 100
            and [field['variables'] for field in step['fieldOutputs']] == [3, 1],
            'Static output or incrementation defaults changed')
    mutations = [
        ('dangling-node-set', lambda graph: graph['nodeSets']['X1'].append(9999)),
        ('wrong-part-id', lambda graph: graph['parts'][0].update(id=9999)),
        ('wrong-part-name', lambda graph: graph['parts'][0].update(name='missing')),
        ('missing-section-material', lambda graph: graph['sections'][0].update(material='missing')),
        ('missing-load-region', lambda graph: graph['steps'][0]['loads'][0].update(region='missing')),
    ]
    rejected = []
    for name, mutate in mutations:
        graph = deepcopy(reference['graph'])
        mutate(graph)
        try:
            probe['bind_mesh'](reference['mesh'], graph)
        except ValueError:
            rejected.append(name)
        else:
            raise ValueError(f'Accepted {name}')
    require('Cube' in captures['cube']['graph']['elementSets'], 'Set name case was lost')
    embedded, result_rejections = check_results(fixtures, mesh_decoder)
    print(json.dumps({'captures': captures, 'rejected': rejected,
                      'embeddedResult': embedded, 'resultRejections': result_rejections}, indent=2))


def check_results(fixtures, decoder):
    pmx = fixtures / 'definitions-with-results.pmx'
    frd = fixtures / 'cube-results.frd'
    compared = results['compare'](pmx, frd, decoder)
    framing = results['inspect'](pmx)
    with tempfile.TemporaryDirectory() as directory, pmx.open('rb') as stream:
        frames = [Path(directory) / row['kind'] for row in framing['chunks']]
        payloads = [results['read_payload'](stream, row) for row in framing['chunks']]
        command = ['dotnet', str(decoder), '--compare-results', str(frd), *map(str, frames)]
        mutations = [
            ('duplicate-result-node-slot', 0, len(payloads[0]) - 4, 0, 'node lookup'),
            ('modified-result-value', 1, len(payloads[1]) - 17, 0x3F800000, 'differs from FRD'),
        ]
        rejected = []
        for label, frame_index, offset, value, message in mutations:
            for path, data in zip(frames, payloads):
                path.write_bytes(data)
            bad = bytearray(payloads[frame_index])
            struct.pack_into('<i', bad, offset, value)
            frames[frame_index].write_bytes(bad)
            output = subprocess.run(command, text=True, capture_output=True, timeout=60)
            require(output.returncode == 1 and message in output.stderr, f'Accepted {label}')
            rejected.append(label)
    return compared, rejected


if __name__ == '__main__':
    main(*(Path(argument).resolve() for argument in sys.argv[1:]))

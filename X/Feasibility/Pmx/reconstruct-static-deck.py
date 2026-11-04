#!/usr/bin/env python3
"""Rebuild a deck from a bounded PMX 3.0.0 static-solid model."""
import argparse
import hashlib
import json
from pathlib import Path
from runpy import run_path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
reader = run_path(str(HERE / 'inspect-static-project.py'))


def project_definition(graph):
    if graph['unitSystem'] != 'MM_TON_S_C' or len(graph['steps']) != 1 or len(graph['materials']) != 1:
        raise ValueError('Expected the controlled static-solid definition.')
    material = graph['materials'][0]
    properties = {prop['type']: prop['rows'] for prop in material['properties']}
    if (material['temperatureDependent'] or len(material['properties']) != 2
            or set(properties) != {'CaeModel.Elastic', 'CaeModel.Density'}):
        raise ValueError('Expected temperature-independent elastic and density properties.')
    elastic, density = properties['CaeModel.Elastic'], properties['CaeModel.Density']
    if (len(elastic) != 1 or len(elastic[0]) != 3 or elastic[0][2] != '0 °C'
            or len(density) != 1 or len(density[0]) != 2):
        raise ValueError('Unsupported material table.')
    step = graph['steps'][0]
    if (step['nonlinearGeometry'] or step['perturbation'] or not step['runAnalysis']
            or step['solverType'] != 0 or step['incrementationType'] != 1
            or step['historyOutputCount'] or any(
                condition['rotations'] != ['Unconstrained'] * 3 for condition in step['constraints'])):
        raise ValueError('Unsupported controlled static step.')
    return {
        'analysis': {
            'schemaVersion': 1, 'unitSystem': 'mm-N-s-C',
            'materials': [{'name': material['name'], 'youngsModulus': elastic[0][0],
                           'poissonsRatio': elastic[0][1]}],
            'sections': [{'name': section['name'], 'material': section['material'],
                          'elementSet': section['region']} for section in graph['sections']],
            'step': {
                'name': step['name'], 'timePeriod': step['timePeriod'],
                'initialTimeIncrement': step['initialTimeIncrement'],
                'minimumTimeIncrement': step['minTimeIncrement'],
                'maximumTimeIncrement': step['maxTimeIncrement'],
                'maximumIncrements': step['maxIncrements'], 'outputFrequency': 1,
                'constraints': [{'name': condition['name'], 'nodeSet': condition['region'],
                                 'displacements': [None if value == 'Unconstrained' else value
                                                   for value in condition['displacements']]}
                                for condition in step['constraints']],
                'loads': [{'name': load['name'], 'nodeSet': load['region'],
                           'forcePerNode': load['force']} for load in step['loads']],
                'nodalHistorySets': [], 'elementHistorySets': [],
            },
        },
        'density': density[0], 'outputFrequency': step['outputFrequency'], 'outputs': step['fieldOutputs'],
    }


def mesh_input(project):
    mesh = project['mesh']
    graph = project['graph']
    lines = ['*Node']
    for node in mesh['nodes']:
        lines.append(', '.join(map(str, [node['id'], *node['coordinates']])))
    lines.append('*Element, Type=C3D8')
    for element in mesh['elements']:
        lines.append(', '.join(map(str, [element['id'], *element['connectivity']])))
    for keyword, sets in (('Nset', graph['nodeSets']), ('Elset', graph['elementSets'])):
        for name, labels in sets.items():
            lines.append(f'*{keyword}, {keyword}={name}')
            for start in range(0, len(labels), 8):
                lines.append(', '.join(map(str, labels[start:start + 8])))
    return '\n'.join(lines) + '\n'


def validate_shape(project, framing, graph, graph_decoder):
    if project['inputSha256'] != framing['inputSha256']:
        raise ValueError('PMX changed during the shape check.')
    if framing['header'] != 'PrePoMax v3.0.0':
        raise ValueError('The static workflow requires the PMX 3.0.0 header.')
    tail = framing['opaqueTail']
    if tail['bytes'] != 4 or tail['sha256'] != hashlib.sha256(bytes(4)).hexdigest():
        raise ValueError('The static workflow requires a project without saved results.')
    with tempfile.TemporaryDirectory(prefix='prepomaxx-pmx-shape-') as directory:
        path = Path(directory) / 'graph.nrbf'
        path.write_bytes(graph)
        return reader['decode'](graph_decoder, ['--static-edit-contract', path])


def build_project_deck(project, deck_builder, output):
    with tempfile.TemporaryDirectory(prefix='prepomaxx-pmx-deck-') as directory:
        mesh = Path(directory) / 'mesh.inp'
        definition = Path(directory) / 'definition.json'
        mesh.write_text(mesh_input(project), encoding='utf-8')
        definition.write_text(json.dumps(project_definition(project['graph'])), encoding='utf-8')
        built = reader['decode'](deck_builder, [mesh, definition, output.resolve()])
    return {'pmxSha256': project['inputSha256'], **built}


def reconstruct(pmx, mesh_decoder, graph_decoder, deck_builder, output, *, validate_input_shape=False):
    project = reader['inspect'](pmx, mesh_decoder, graph_decoder)
    if validate_input_shape:
        with pmx.open('rb') as source:
            framing, graph, _ = reader['read_frames'](source)
        validate_shape(project, framing, graph, graph_decoder)
    else:
        fixture = json.loads((ROOT / '.project/reports/pmx-3.0.0-reference/edited-capture.json').read_text())
        if project['inputSha256'] not in (fixture['originalPmxSha256'], fixture['editedPmxSha256']):
            raise ValueError('Deck reconstruction is limited to the pinned baseline and edited captures.')
    return build_project_deck(project, deck_builder, output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ('pmx', 'mesh_decoder', 'graph_decoder', 'deck_builder', 'output'):
        parser.add_argument(argument, type=Path)
    parser.add_argument('--validate-shape', action='store_true',
                        help='check the experimental result-free static project contract')
    args = parser.parse_args()
    try:
        print(json.dumps(reconstruct(args.pmx, args.mesh_decoder, args.graph_decoder,
                                     args.deck_builder, args.output, validate_input_shape=args.validate_shape)))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()

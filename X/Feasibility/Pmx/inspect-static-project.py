#!/usr/bin/env python3
"""Inspect the supported mesh and static records of a PMX 3.0.0 file."""
import argparse
import json
from pathlib import Path
from runpy import run_path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
read_frames = run_path(str(HERE / 'inspect-pmx.py'))['read_frames']


def decode(decoder, args):
    result = subprocess.run(['dotnet', str(decoder.resolve()), *map(str, args)],
                            capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise ValueError((result.stderr or result.stdout).strip())
    return json.loads(result.stdout)


def bind_mesh(mesh, graph):
    nodes = {node['id'] for node in mesh['nodes']}
    elements = {element['id']: element for element in mesh['elements']}
    for sets, known in ((graph['nodeSets'], nodes), (graph['elementSets'], elements)):
        if any(not set(labels).issubset(known) for labels in sets.values()):
            raise ValueError('A named set refers to an ID missing from the mesh.')

    if set(mesh['partNames']) != {part['name'] for part in graph['parts']}:
        raise ValueError('Part names differ between graph and binary mesh.')

    assigned = set()
    part_ids = set()
    for part in graph['parts']:
        if part['id'] in part_ids or not part['elements']:
            raise ValueError('Duplicate or empty analysis mesh part.')
        part_ids.add(part['id'])
        part_nodes = set()
        for label in part['elements']:
            element = elements.get(label)
            if not element or element['partId'] != part['id'] or label in assigned:
                raise ValueError('Part membership differs between graph and mesh.')
            assigned.add(label)
            part_nodes.update(element['connectivity'])
        if set(part['nodes']) != part_nodes:
            raise ValueError('Part node membership differs from its elements.')
    if assigned != elements.keys():
        raise ValueError('A mesh element has no graph part.')

    materials = {material['name'] for material in graph['materials']}
    for section in graph['sections']:
        if (section['material'] not in materials or section['regionType'] != 4
                or section['region'] not in graph['elementSets']):
            raise ValueError('A section refers to an unsupported or missing region or material.')
    for step in graph['steps']:
        for assignment in step['constraints'] + step['loads']:
            if assignment['regionType'] != 2 or assignment['region'] not in graph['nodeSets']:
                raise ValueError('A support or load refers to an unsupported or missing region.')


def inspect(path, mesh_decoder, graph_decoder):
    with path.open('rb') as stream:
        framing, records, model = read_frames(stream)
    if framing['header'] != 'PrePoMax v3.0.0':
        raise ValueError('The static-project probe requires the PrePoMax v3.0.0 header.')
    with tempfile.TemporaryDirectory(prefix='prepomaxx-pmx-project-') as directory:
        work = Path(directory)
        graph_path = work / 'graph.nrbf'
        model_path = work / 'model.bin'
        graph_path.write_bytes(records)
        model_path.write_bytes(model)
        mesh = decode(mesh_decoder, [model_path])
        graph = decode(graph_decoder, ['--static-graph', graph_path])
    bind_mesh(mesh, graph)
    return {'inputSha256': framing['inputSha256'], 'mesh': mesh, 'graph': graph,
            'unparsedResultBytes': framing['opaqueTail']['bytes']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ('input', 'mesh_decoder', 'graph_decoder'):
        parser.add_argument(argument, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(inspect(args.input, args.mesh_decoder, args.graph_decoder)))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()

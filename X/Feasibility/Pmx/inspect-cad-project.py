#!/usr/bin/env python3
"""Bounded original CAD/C3D4 PMX projection; no payload type activation."""
import argparse
from pathlib import Path
from runpy import run_path
import tempfile

HERE = Path(__file__).resolve().parent
base = run_path(str(HERE / 'inspect-static-project.py'))


def inspect(path, mesh_decoder, graph_decoder, *, property_edits=False):
    with Path(path).open('rb') as stream:
        framing, records, model = base['read_frames'](stream)
    if framing['header'] != 'PrePoMax v3.0.0':
        raise ValueError('The CAD project boundary requires original PMX 3.0.0.')
    with tempfile.TemporaryDirectory(prefix='prepomaxx-cad-pmx-') as directory:
        root = Path(directory)
        graph_file, model_file = root/'graph.nrbf', root/'model.bin'
        graph_file.write_bytes(records)
        model_file.write_bytes(model)
        mesh = base['decode'](mesh_decoder, ['--cad-model', model_file])
        graph = base['decode'](graph_decoder, ['--cad-static-graph', graph_file])
        targets = base['decode'](graph_decoder, ['--cad-property-contract' if property_edits else '--cad-edit-contract', graph_file])
        base['bind_mesh'](mesh, graph['definition'])
    geometry = graph['geometry']
    if (len(geometry) != 1 or [p['Name'] for p in geometry] != mesh['geometry']['partNames'] or
            geometry[0]['Id'] != mesh['geometry']['partId'] or
            sorted(geometry[0]['Nodes']) != mesh['geometry']['nodeIds'] or
            sorted(geometry[0]['Elements']) != mesh['geometry']['elementIds']):
        raise ValueError('CAD graph membership differs from original binary geometry.')
    import hashlib
    tail = framing['opaqueTail']
    if tail['bytes'] != 4 or tail['sha256'] != hashlib.sha256(bytes(4)).hexdigest():
        raise ValueError('The CAD editing boundary requires a result-free PMX.')
    return {'inputSha256': framing['inputSha256'], 'mesh': mesh, 'graph': graph['definition'],
            'cadGeometry': geometry, 'editTargets': targets, 'unparsedResultBytes': tail['bytes']}


if __name__ == '__main__':
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['input', 'mesh_decoder', 'graph_decoder']:
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.input, args.mesh_decoder, args.graph_decoder)))

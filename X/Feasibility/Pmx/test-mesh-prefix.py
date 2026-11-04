#!/usr/bin/env python3
"""Compare the bounded PMX probe with the official app's exported mesh."""
import json
from pathlib import Path
from runpy import run_path
import struct
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
read_frames = run_path(str(HERE / 'inspect-pmx.py'))['read_frames']
snapshot = run_path(str(ROOT / 'X/Feasibility/Data/check-windows-capture.py'))['snapshot']


def main(decoder, fixtures):
    verified = {}
    for name in ('cube', 'definitions', 'definitions-with-results'):
        pmx = fixtures / (name + '.pmx')
        export = fixtures / ('cube-export.inp' if name == 'cube' else 'definitions-export.inp')
        expected, _ = snapshot(export)
        command = [sys.executable, str(HERE / 'inspect-mesh-prefix.py'), str(pmx), str(decoder)]
        observed = json.loads(subprocess.check_output(command, text=True, timeout=40))
        nodes = {node['id']: node['coordinates'] for node in observed['nodes']}
        elements = {element['id']: {key: element[key] for key in ('type', 'connectivity')}
                    for element in observed['elements']}
        if (nodes != expected['nodes'] or elements != expected['elements']
                or observed['meshAssembly'] != 'CaeMesh'):
            raise ValueError(f'{name}: decoded mesh differs from official export')
        verified[name] = observed

    with (fixtures / 'cube.pmx').open('rb') as stream:
        _, _, original = read_frames(stream)
    element_offset = 24 + len(verified['cube']['nodes']) * 28 + 4
    controls = [
        ('nonempty-geometry', 4, 1, 'geometry'),
        ('oversized-node-count', 20, 2**30, 'Mesh count'),
        ('unsupported-cell-type', element_offset + 8, 999, 'eight-node'),
        ('unknown-node-reference', element_offset + 16, 999, 'element'),
    ]
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'model.bin'
        for label, offset, value, diagnostic in controls:
            corrupted = bytearray(original)
            struct.pack_into('<i', corrupted, offset, value)
            path.write_bytes(corrupted)
            result = subprocess.run(['dotnet', str(decoder), str(path)],
                                    capture_output=True, text=True, timeout=30)
            if result.returncode != 1 or result.stdout or diagnostic not in result.stderr:
                raise ValueError(f'{label}: malformed model block was not rejected as expected')
    print(json.dumps({'verified': verified, 'rejected': [case[0] for case in controls]}, indent=2))


if __name__ == '__main__':
    main(*(Path(argument).resolve() for argument in sys.argv[1:]))

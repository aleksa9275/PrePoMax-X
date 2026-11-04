#!/usr/bin/env python3
"""Compare decks reconstructed from the two pinned PMX fixtures with their exports."""
import hashlib
import json
from pathlib import Path
from runpy import run_path
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
reconstruct = run_path(str(HERE / 'reconstruct-static-deck.py'))['reconstruct']
snapshot = run_path(str(ROOT / 'X/Feasibility/Data/check-windows-capture.py'))['snapshot']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def output_cards(lines):
    return [item for index, line in enumerate(lines[:-1])
            if line in ('*NODEFILE', '*ELFILE') for item in (line, lines[index + 1])]


def main(fixtures, mesh, graph, builder):
    verified = {}
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / 'reconstructed.inp'
        for name in ('definitions', 'definitions-edited'):
            pmx = fixtures / (name + '.pmx')
            original = fixtures / (name + '-export.inp')
            summary = reconstruct(pmx, mesh, graph, builder, output)
            expected, reference_lines = snapshot(original)
            actual, lines = snapshot(output)
            if (actual['units'] is not None or expected['units'] != 'MM_TON_S_C'
                    or 'UNITSYSTEM:MM_TON_S_C' not in lines
                    or 'MODELSPACE:THREED' not in lines):
                raise ValueError('Unexpected deck unit heading.')
            actual['units'] = expected['units']
            if (actual != expected or output_cards(lines) != output_cards(reference_lines)
                    or '*STEP,INC=100' not in lines or '*OUTPUT,FREQUENCY=1' not in lines
                    or digest(pmx) != summary['pmxSha256']):
                raise ValueError(f'{name}: reconstructed deck differs from expected settings.')
            verified[name] = {**summary, 'deckSha256': digest(output),
                              'originalExportSha256': digest(original)}
            if name == 'definitions':
                output.unlink()

        original_digest = digest(output)
        for fixture, diagnostic in (('definitions', 'already exists'),
                                    ('definitions-with-results', 'limited to the pinned')):
            try:
                reconstruct(fixtures / (fixture + '.pmx'), mesh, graph, builder, output)
            except ValueError as error:
                if diagnostic not in str(error):
                    raise
            else:
                raise ValueError(f'Unexpected reconstruction of {fixture}')
        if digest(output) != original_digest:
            raise ValueError('Failed reconstruction changed the existing deck.')
    print(json.dumps({'verified': verified, 'overwriteRejected': True,
                      'otherValidCaptureRejected': True}, indent=2))


if __name__ == '__main__':
    main(*(Path(argument).resolve() for argument in sys.argv[1:]))

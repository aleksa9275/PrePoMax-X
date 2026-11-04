#!/usr/bin/env python3
"""Verify the experimental shape-checked PMX edit and deck workflow."""
import hashlib
import json
from pathlib import Path
from runpy import run_path
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
writer = run_path(str(HERE / 'write-controlled-edit.py'))
decks = writer['decks']
reader = writer['reader']
snapshot = run_path(str(ROOT / 'X/Feasibility/Data/check-windows-capture.py'))['snapshot']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(condition, message):
    if not condition:
        raise ValueError(message)


def main(fixtures, mesh, graph, builder):
    source = fixtures / 'shape-reference.pmx'
    original = digest(source)
    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        output = work / 'edited.pmx'
        unsupported_version = work / 'old.pmx'
        data = source.read_bytes()
        unsupported_version.write_bytes(data.replace(b'PrePoMax v3.0.0', b'PrePoMax v2.6.0', 1))
        refused = []
        for label, path, options, expected in (
            ('unpinned-default', source, {}, 'approved official'),
            ('saved-results', fixtures / 'definitions-with-results.pmx',
             {'deck_builder': builder}, 'no saved results'),
            ('unsupported-formulation', fixtures / 'shape-reduced.pmx',
             {'deck_builder': builder}, 'full-integration C3D8'),
            ('unsupported-version', unsupported_version, {'deck_builder': builder}, '3.0.0 header'),
        ):
            try:
                writer['write_edit'](path, output, mesh, graph, **options)
            except ValueError as error:
                check(expected in str(error) and not output.exists(), f'Incorrect refusal for {label}: {error}')
                refused.append(label)
            else:
                raise ValueError(f'Accepted {label}')

        with (fixtures / 'Profile.pmx').open('rb') as stream:
            _, profile_graph, _ = writer['read_frames'](stream)
        history = work / 'profile.nrbf'
        history.write_bytes(profile_graph)
        try:
            reader['decode'](graph, ['--static-edit-contract', history])
        except ValueError as error:
            check('empty command history' in str(error), 'Wrong command history refusal')
            refused.append('nonempty-command-history')
        else:
            raise ValueError('Accepted a graph containing stored commands.')

        written = writer['write_edit'](
            source, output, mesh, graph, deck_builder=builder, modulus_mpa='84500.5', force_n='42.25')
        rebuilt = work / 'edited.inp'
        decks['reconstruct'](output, mesh, graph, builder, rebuilt, validate_input_shape=True)
        reference, _ = snapshot(fixtures / 'shape-official-edit.inp')
        actual, lines = snapshot(rebuilt)
        check('UNITSYSTEM:MM_TON_S_C' in lines and reference['units'] == 'MM_TON_S_C',
              'Unit metadata changed')
        actual['units'] = reference['units']
        check(actual == reference, 'Reopened portable PMX does not reproduce the official edit')
        check(list(actual['nodes']) == [13, 23, 33, 43, 53, 63, 73, 83]
              and list(actual['elements']) == [7001], 'Nonsequential mesh IDs were lost')

        second = work / 'second.pmx'
        repeated = writer['write_edit'](
            output, second, mesh, graph, deck_builder=builder, modulus_mpa='80000', force_n='40')
        reloaded = reader['inspect'](second, mesh, graph)['graph']
        check(reloaded['materials'][0]['properties'][0]['rows'][0][0] == '80000 MPa'
              and reloaded['steps'][0]['loads'][0]['force'][0] == '40 N',
              'Could not edit a project created by the portable writer')
        before = digest(output)
        try:
            writer['write_edit'](source, output, mesh, graph, deck_builder=builder)
        except FileExistsError:
            refused.append('existing-output')
        else:
            raise ValueError('Overwrote an existing PMX')
        check(digest(source) == original and digest(output) == before, 'A source or existing PMX changed')
        print(json.dumps({'firstWrite': written, 'secondWrite': repeated,
                          'deckSha256': digest(rebuilt), 'officialDeckSemanticsMatch': True,
                          'refused': refused}, indent=2))


if __name__ == '__main__':
    main(*(Path(argument).resolve() for argument in sys.argv[1:]))

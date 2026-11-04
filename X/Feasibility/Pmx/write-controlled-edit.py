#!/usr/bin/env python3
"""Write bounded modulus and axial load edits to a checked PMX model."""
from copy import deepcopy
from decimal import Decimal
import argparse
import hashlib
import json
import os
from pathlib import Path
from runpy import run_path
import re
import struct
import subprocess
import tempfile
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
reader = run_path(str(HERE / 'inspect-static-project.py'))
read_frames = reader['read_frames']
decks = run_path(str(HERE / 'reconstruct-static-deck.py'))

def positive_decimal(value):
    if not re.fullmatch(r'[0-9]{1,9}(?:\.[0-9]{1,6})?', value) or Decimal(value) <= 0:
        raise ValueError('Use a positive decimal with up to nine integer and six fractional digits.')
    return format(Decimal(value).normalize(), 'f')


def string_record(record_id, value):
    data = value.encode('ascii')
    if len(data) > 127:
        raise ValueError('Controlled equation exceeds the single-byte string length limit.')
    return struct.pack('<BiB', 6, record_id, len(data)) + data


def locate_strings(graph, graph_decoder):
    with tempfile.TemporaryDirectory(prefix='prepomaxx-pmx-targets-') as directory:
        path = Path(directory) / 'graph.nrbf'
        path.write_bytes(graph)
        targets = reader['decode'](graph_decoder, ['--edit-strings', path])
    if sorted(target['Role'] for target in targets) != ['force', 'magnitude', 'modulus']:
        raise ValueError('Unexpected graph edit targets.')
    return targets


def patch_graph(graph, targets, modulus='105000 MPa', force='50 N'):
    replacements = []
    for target in targets:
        record_id = target['RecordId']
        start = target['Offset']
        old = string_record(record_id, target['Value'])
        if start < 0 or graph[start:start + len(old)] != old:
            raise ValueError('Discovered equation record differs from the wire bytes.')
        replacement = modulus if target['Role'] == 'modulus' else force
        replacements.append((start, old, string_record(record_id, replacement)))
    patched = bytearray(graph)
    previous = len(graph)
    for start, old, new in sorted(replacements, reverse=True):
        if start + len(old) > previous:
            raise ValueError('Discovered equation records overlap.')
        patched[start:start + len(old)] = new
        previous = start
    return bytes(patched)


def write_edit(source, output, mesh_decoder, graph_decoder, *, modulus_mpa='105000', force_n='50',
               deck_builder=None):
    modulus = positive_decimal(modulus_mpa) + ' MPa'
    force = positive_decimal(force_n) + ' N'
    if source.resolve() == output.resolve():
        raise ValueError('Output must differ from the input.')
    with source.open('rb') as stream:
        framing, graph, model = read_frames(stream)
        if deck_builder is None:
            reports = ROOT / '.project/reports/pmx-3.0.0-reference'
            receipt = json.loads((reports / 'edited-capture.json').read_text())
            extra = json.loads((reports / 'edit-discovery-fixture.json').read_text())
            allowed = {receipt['originalPmxSha256'], receipt['editedPmxSha256'], extra['extraSetPmxSha256']}
            if framing['inputSha256'] not in allowed:
                raise ValueError('Only the exact controlled baseline and approved official PMX captures are supported.')
        stream.seek(0)
        header = stream.read(32)
        stream.seek(framing['opaqueTail']['offset'])
        tail = stream.read(4)
        if tail != bytes(4) or stream.read(1):
            raise ValueError('The controlled fixture must have no saved results.')
        stream.seek(0)
        if hashlib.file_digest(stream, 'sha256').hexdigest() != framing['inputSha256']:
            raise ValueError('Input changed during the read.')

    baseline = reader['inspect'](source, mesh_decoder, graph_decoder)
    if baseline['inputSha256'] != framing['inputSha256']:
        raise ValueError('Input changed during verification.')
    expected = deepcopy(baseline['graph'])
    expected['materials'][0]['properties'][0]['rows'][0][0] = modulus
    expected['steps'][0]['loads'][0]['force'][0] = force

    targets = (locate_strings(graph, graph_decoder) if deck_builder is None
               else decks['validate_shape'](baseline, framing, graph, graph_decoder))
    patched = patch_graph(graph, targets, modulus, force)
    verified = {target['Role']: (target['RecordId'], target['Value'])
                for target in locate_strings(patched, graph_decoder)}
    for target in targets:
        role = target['Role']
        if verified[role] != (target['RecordId'], modulus if role == 'modulus' else force):
            raise ValueError('Edited equation records failed graph verification.')
    payload = struct.pack('<q', len(patched)) + patched + model
    compressed = zlib.compress(payload, wbits=-15)
    contents = header + struct.pack('<i', len(compressed)) + compressed + tail
    with tempfile.TemporaryDirectory(prefix='.prepomaxx-pmx-write-', dir=output.parent) as directory:
        staged = Path(directory) / 'candidate.pmx'
        staged.write_bytes(contents)
        observed = reader['inspect'](staged, mesh_decoder, graph_decoder)
        if (observed['graph'] != expected or observed['mesh'] != baseline['mesh']
                or observed['unparsedResultBytes'] != len(tail)):
            raise ValueError('Edited PMX failed semantic readback.')
        if deck_builder is not None:
            decks['build_project_deck'](baseline, deck_builder, Path(directory) / 'baseline.inp')
            decks['build_project_deck'](observed, deck_builder, Path(directory) / 'edited.inp')
        os.link(staged, output)
    return {'inputSha256': framing['inputSha256'], 'outputSha256': observed['inputSha256'],
            'editedGraphSha256': hashlib.sha256(patched).hexdigest(),
            'modelBlockSha256': framing['mainFrame']['opaqueModelSha256'],
            'patchedStringRecords': sorted(target['RecordId'] for target in targets),
            'portableReadbackPassed': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ('source', 'output', 'mesh_decoder', 'graph_decoder'):
        parser.add_argument(argument, type=Path)
    parser.add_argument('--modulus-mpa', default='105000')
    parser.add_argument('--force-n', default='50')
    parser.add_argument('--deck-builder', type=Path,
                        help='enable the experimental static shape check and validate both decks')
    args = parser.parse_args()
    try:
        result = write_edit(args.source, args.output, args.mesh_decoder, args.graph_decoder,
                            modulus_mpa=args.modulus_mpa, force_n=args.force_n, deck_builder=args.deck_builder)
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, subprocess.SubprocessError, zlib.error) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()

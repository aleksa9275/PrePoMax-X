#!/usr/bin/env python3
"""Verify the pinned PMX edit and refuse unsafe destination or input cases."""
import hashlib
import json
from pathlib import Path
from runpy import run_path
import struct
import sys
import tempfile

HERE = Path(__file__).resolve().parent
writer = run_path(str(HERE / 'write-controlled-edit.py'))
inspect = writer['reader']['inspect']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frame(path):
    with path.open('rb') as source:
        return writer['read_frames'](source)


def check_shared_records(raw, graph_decoder):
    # The baseline object[] has a fourth member reference at offset 41.
    # Repoint it to the force container or its string without changing the
    # static projection. The third control shares the container from a class slot.
    controls = [
        ('array-shared-container', 41, 5, 501, 'exactly one owner'),
        ('array-shared-string', 41, 5, 555, 'may be shared'),
        ('class-shared-container', 63026, 554, 501, 'exactly one owner'),
    ]
    decode = writer['reader']['decode']
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'ownership.nrbf'
        path.write_bytes(raw)
        baseline = decode(graph_decoder, ['--static-graph', path])
        rejected = []
        for label, offset, original, target, diagnostic in controls:
            if raw[offset:offset + 5] != struct.pack('<Bi', 9, original):
                raise ValueError('Controlled alias mutation no longer matches the fixture.')
            changed = bytearray(raw)
            struct.pack_into('<i', changed, offset + 1, target)
            path.write_bytes(changed)
            if decode(graph_decoder, ['--static-graph', path]) != baseline:
                raise ValueError('Alias control unexpectedly changed the static projection.')
            try:
                writer['locate_strings'](changed, graph_decoder)
            except ValueError as error:
                if diagnostic not in str(error):
                    raise
                rejected.append(label)
            else:
                raise ValueError(f'Accepted {label}.')
    return rejected


def main(fixtures, mesh, graph):
    source = fixtures / 'definitions.pmx'
    original_edit = fixtures / 'definitions-edited.pmx'
    source_hash = digest(source)
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / 'edited.pmx'
        receipt = writer['write_edit'](source, output, mesh, graph)
        output_hash = digest(output)
        before_framing, before_graph, before_model = frame(source)
        after_framing, after_graph, after_model = frame(output)
        if (output_hash != receipt['outputSha256'] or source_hash != receipt['inputSha256']
                or before_model != after_model
                or after_graph != writer['patch_graph'](before_graph, writer['locate_strings'](before_graph, graph))
                or before_framing['opaqueTail']['sha256'] != after_framing['opaqueTail']['sha256']):
            raise ValueError('Unexpected bytes changed in the controlled edit.')
        expected = inspect(original_edit, mesh, graph)
        observed = inspect(output, mesh, graph)
        for key in ('mesh', 'graph', 'unparsedResultBytes'):
            if expected[key] != observed[key]:
                raise ValueError(f'Portable edit differs from official edit in {key}.')

        rejected = []
        for label, input_path, destination, message in (
            ('existing-output', source, output, 'File exists'),
            ('source-as-output', source, source, 'differ from the input'),
            ('other-valid-pmx', fixtures / 'definitions-with-results.pmx', output,
             'exact controlled baseline'),
        ):
            try:
                writer['write_edit'](input_path, destination, mesh, graph)
            except (ValueError, FileExistsError) as error:
                if message not in str(error):
                    raise
                rejected.append(label)
            else:
                raise ValueError(f'Accepted {label}.')
        if digest(source) != source_hash or digest(output) != output_hash:
            raise ValueError('A refused write changed an existing file.')

        variant = Path(directory) / 'decimal.pmx'
        variant_receipt = writer['write_edit'](
            source, variant, mesh, graph, modulus_mpa='98765.500', force_n='007.1250')
        variant_framing, variant_graph, variant_model = frame(variant)
        projected = inspect(variant, mesh, graph)['graph']
        if (len(variant_graph) != len(before_graph) + 7 or variant_model != before_model
                or variant_framing['opaqueTail']['sha256'] != before_framing['opaqueTail']['sha256']
                or projected['materials'][0]['properties'][0]['rows'][0][0] != '98765.5 MPa'
                or projected['steps'][0]['loads'][0]['force'][0] != '7.125 N'):
            raise ValueError('Variable-length equation edit failed.')

        shifted = Path(directory) / 'decimal-from-edited.pmx'
        shifted_receipt = writer['write_edit'](
            original_edit, shifted, mesh, graph, modulus_mpa='98765.5', force_n='7.125')
        shifted_projection = inspect(shifted, mesh, graph)
        variant_projection = inspect(variant, mesh, graph)
        if any(shifted_projection[key] != variant_projection[key] for key in
               ('mesh', 'graph', 'unparsedResultBytes')):
            raise ValueError('The second pinned graph produced different edited semantics.')

        third = Path(directory) / 'extra-set-edited.pmx'
        third_source = fixtures / 'official-extra-set.pmx'
        third_receipt = writer['write_edit'](
            third_source, third, mesh, graph, modulus_mpa='123456.75', force_n='19.25')
        before, raw_before, model_before = frame(third_source)
        after, raw_after, model_after = frame(third)
        third_targets = writer['locate_strings'](raw_before, graph)
        if (set(third_receipt['patchedStringRecords']) & set(receipt['patchedStringRecords'])
                or model_before != model_after
                or before['opaqueTail']['sha256'] != after['opaqueTail']['sha256']
                or raw_after != writer['patch_graph'](raw_before, third_targets, '123456.75 MPa', '19.25 N')
                or inspect(third, mesh, graph)['graph']['nodeSets'].get('X1-1') != [2, 3, 6, 7]):
            raise ValueError('Graph discovery failed with changed IDs or lost the extra named set.')

        for bad in ('0', '-1', '1e3', 'NaN', '1234567890', '1.1234567'):
            invalid = Path(directory) / 'invalid.pmx'
            try:
                writer['write_edit'](source, invalid, mesh, graph, force_n=bad)
            except ValueError as error:
                if 'positive decimal' not in str(error) or invalid.exists():
                    raise
            else:
                raise ValueError(f'Accepted invalid magnitude {bad}.')

    print(json.dumps({**receipt, 'matchesOfficialEditedProjection': True,
                      'modelAndResultTailPreserved': True, 'rejected': rejected,
                      'variableLengthEdit': variant_receipt,
                      'variableLengthEditFromOfficialEdit': shifted_receipt,
                      'discoveredEditFromExtraSet': third_receipt,
                      'sharedRecordRejections': check_shared_records(before_graph, graph),
                      'invalidMagnitudeCount': 6}, indent=2))


if __name__ == '__main__':
    main(*(Path(argument).resolve() for argument in sys.argv[1:]))

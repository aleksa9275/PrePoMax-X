#!/usr/bin/env python3
"""Edit audited original CAD PMX member slots without changing shared strings."""
from copy import deepcopy
from decimal import Decimal
import hashlib
import os
from pathlib import Path
from runpy import run_path
import re
import struct
import tempfile
import zlib

HERE = Path(__file__).resolve().parent
original = run_path(str(HERE/'write-cad-edit.py'))
reader, decks = original['reader'], original['decks']
positive_decimal = original['positive_decimal']


def decimal_value(value):
    if not isinstance(value, str) or len(value) > 48 or not re.fullmatch(
            r'[+-]?[0-9]{1,12}(?:\.[0-9]{1,12})?(?:[eE][+-]?[0-9]{1,2})?', value):
        raise ValueError('Use a finite decimal number with up to twelve fractional digits.')
    number = Decimal(value)
    if not number.is_finite() or abs(number) > Decimal('1e30') or (number and abs(number) < Decimal('1e-30')):
        raise ValueError('Number is outside the supported finite range.')
    return number


def material_values(modulus, poisson, density):
    values = {'modulus': positive_decimal(modulus)+' MPa'}
    ratio, mass = decimal_value(poisson), decimal_value(density)
    if not -1 < ratio < Decimal('0.5'):
        raise ValueError('Poisson’s ratio must be greater than -1 and less than 0.5.')
    if mass <= 0:
        raise ValueError('Density must be positive.')
    values.update(poisson=str(ratio.normalize()), density=str(mass.normalize())+' t/mm³')
    return values


def string_record(record_id, value):
    data = value.encode('utf-8')
    if not 0 < len(data) <= 4096 or not 0 < record_id < 2**31:
        raise ValueError('Invalid new string record.')
    size, prefix = len(data), bytearray()
    while size >= 128:
        prefix.append((size & 127) | 128)
        size >>= 7
    prefix.append(size)
    return struct.pack('<Bi', 6, record_id)+prefix+data


def patch_members(graph, targets, values):
    if not targets or len({target['Role'] for target in targets}) != len(targets):
        raise ValueError('Duplicate or absent member edit roles.')
    by_role = {target['Role']: target for target in targets}
    if set(values) - by_role.keys():
        raise ValueError('Unknown member edit role.')
    maximum = max(target['MaximumId'] for target in targets)
    replacements, preserved = [], []
    for index, (role, value) in enumerate(values.items(), 1):
        target = by_role[role]
        start, length = target['Offset'], target['Length']
        old = graph[start:start+length]
        expected = (string_record(target['RecordId'], target['Value']) if target['Kind'] == 6 else
                    struct.pack('<Bi', 9, target['RecordId']) if target['Kind'] == 9 else None)
        if start < 17 or expected is None or old != expected:
            raise ValueError('Audited member slot differs from its wire bytes.')
        if target['Kind'] == 6:
            # Preserve its original ID/value for every other reference. NRBF
            # permits forward references; retain the definition before MessageEnd.
            preserved.append(old)
        replacements.append((start, length, string_record(maximum+index, value)))
    patched, previous = bytearray(graph), len(graph)-1
    if not graph or graph[-1] != 11:
        raise ValueError('Missing NRBF MessageEnd.')
    for start, length, new in sorted(replacements, reverse=True):
        if start+length > previous:
            raise ValueError('Member edit slots overlap.')
        patched[start:start+length] = new
        previous = start
    return bytes(patched[:-1])+b''.join(preserved)+bytes([11])


def contract(graph, graph_decoder):
    with tempfile.TemporaryDirectory(prefix='prepomaxx-member-contract-') as directory:
        path = Path(directory)/'graph.nrbf'
        path.write_bytes(graph)
        return reader['base']['decode'](graph_decoder, ['--cad-property-contract', path])


def write_edit(source, output, mesh_decoder, graph_decoder, *, deck_builder,
               modulus_mpa='105000', force_n='50', poisson=None, density=None):
    source, output = Path(source), Path(output)
    if output.exists() or output.is_symlink() or source.resolve() == output.resolve():
        raise FileExistsError('Choose a new PMX destination.')
    baseline = reader['inspect'](source, mesh_decoder, graph_decoder)
    with source.open('rb') as stream:
        framing, graph, model = reader['base']['read_frames'](stream)
        stream.seek(0); header = stream.read(32)
        stream.seek(framing['opaqueTail']['offset']); tail = stream.read()
    if framing['inputSha256'] != baseline['inputSha256']:
        raise ValueError('CAD PMX changed during validation.')
    targets = contract(graph, graph_decoder)
    stored = {target['Role']: target['Value'] for target in targets}
    values = material_values(modulus_mpa, poisson if poisson is not None else stored['poisson'],
                             density if density is not None else stored['density'].removesuffix(' t/mm³'))
    values.update(force=positive_decimal(force_n)+' N', magnitude=positive_decimal(force_n)+' N')
    patched = patch_members(graph, targets, values)
    expected = deepcopy(baseline['graph'])
    properties = {prop['type']: prop['rows'] for prop in expected['materials'][0]['properties']}
    properties['CaeModel.Elastic'][0][:2] = [values['modulus'], values['poisson']]
    properties['CaeModel.Density'][0][0] = values['density']
    expected['steps'][0]['loads'][0]['force'][0] = values['force']
    compressed = zlib.compress(struct.pack('<q', len(patched))+patched+model, wbits=-15)
    contents = header+struct.pack('<i', len(compressed))+compressed+tail
    with tempfile.TemporaryDirectory(prefix='.prepomaxx-cad-properties-', dir=output.parent) as directory:
        staged = Path(directory)/'candidate.pmx'
        staged.write_bytes(contents)
        observed = reader['inspect'](staged, mesh_decoder, graph_decoder)
        if (observed['graph'] != expected or observed['mesh'] != baseline['mesh'] or
                observed['cadGeometry'] != baseline['cadGeometry']):
            raise ValueError('Edited CAD PMX failed semantic readback.')
        with staged.open('rb') as stream:
            _, after_graph, after_model = reader['base']['read_frames'](stream)
        if after_model != model or after_graph != patched:
            raise ValueError('CAD/model bytes differ after packaging.')
        fresh = {target['Role']: target['Value'] for target in contract(after_graph, graph_decoder)}
        if any(fresh[role] != value for role, value in values.items()):
            raise ValueError('Edited members changed ownership.')
        decks['build_project_deck'](baseline, deck_builder, Path(directory)/'baseline.inp')
        decks['build_project_deck'](observed, deck_builder, Path(directory)/'edited.inp')
        os.link(staged, output)
    return {'inputSha256': baseline['inputSha256'], 'outputSha256': observed['inputSha256'],
            'modelBlockSha256': hashlib.sha256(model).hexdigest(),
            'cadBrepSha256': baseline['cadGeometry'][0]['BrepSha256'],
            'editedMembers': list(values), 'portableReadbackPassed': True,
            'unchangedGeometryMeshAndHistory': True}

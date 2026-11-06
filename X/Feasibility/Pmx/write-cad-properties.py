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
legacy_reader, decks = original['reader'], original['decks']
positive_decimal = original['positive_decimal']


def inspect(path, mesh_decoder, graph_decoder):
    project = legacy_reader['inspect'](path, mesh_decoder, graph_decoder, property_edits=True)
    magnitude = next(t['Value'] for t in project['editTargets'] if t['Role'] == 'magnitude')
    if not magnitude.endswith(' N') or decimal_value(magnitude.removesuffix(' N'), digits=30) < 0:
        raise ValueError('Expected a finite nonnegative stored load magnitude in N.')
    return project


reader = dict(legacy_reader, inspect=inspect)


def decimal_value(value, *, digits=12):
    if not isinstance(value, str) or len(value) > 48 or not re.fullmatch(
            rf'[+-]?[0-9]{{1,{digits}}}(?:\.[0-9]{{1,{digits}}})?(?:[eE][+-]?[0-9]{{1,2}})?', value):
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


def force_values(components, deck_builder):
    if not isinstance(components, (list, tuple)) or len(components) != 3:
        raise ValueError('Provide three signed force components in N.')
    equations = [str(decimal_value(value).normalize())+' N' for value in components]
    original_values = reader['base']['decode'](deck_builder, ['--force-vector', *equations])
    if not original_values['magnitude'].endswith(' N') or decimal_value(original_values['magnitude'].removesuffix(' N'), digits=30) < 0:
        raise ValueError('Original load owner returned an invalid force magnitude.')
    return dict(zip(['force','force2','force3'], equations), magnitude=original_values['magnitude'])


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


def assign_regions(expected, assignments):
    if assignments is None:
        return {}
    if not isinstance(assignments, dict) or set(assignments)-{'section','load','supports'}:
        raise ValueError('Unknown region assignment fields.')
    values = {}
    def assign(owner, selected, regions, role):
        if not isinstance(selected, str) or selected not in regions or not regions[selected]:
            raise ValueError('Choose a compatible existing nonempty named region.')
        if selected != owner['region']:
            owner['region'] = selected
            values[role] = selected
    if 'section' in assignments:
        assign(expected['sections'][0], assignments['section'], expected['elementSets'], 'sectionRegion')
    step = expected['steps'][0]
    if 'load' in assignments:
        assign(step['loads'][0], assignments['load'], expected['nodeSets'], 'loadRegion')
    if 'supports' in assignments:
        supports = {support['name']:support for support in step['constraints']}
        selected = assignments['supports']
        if not isinstance(selected, dict) or set(selected)-supports.keys():
            raise ValueError('Unknown support assignment.')
        for name, region in selected.items():
            assign(supports[name], region, expected['nodeSets'], 'supportRegion:'+name)
    return values


def write_edit(source, output, mesh_decoder, graph_decoder, *, deck_builder,
               modulus_mpa='105000', force_n='50', poisson=None, density=None, force_vector=None,
               assignments=None):
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
    components = force_vector if force_vector is not None else [force_n,
        stored['force2'].removesuffix(' N'), stored['force3'].removesuffix(' N')]
    values.update(force_values(components, deck_builder))
    expected = deepcopy(baseline['graph'])
    values.update(assign_regions(expected, assignments))
    patched = patch_members(graph, targets, values)
    properties = {prop['type']: prop['rows'] for prop in expected['materials'][0]['properties']}
    properties['CaeModel.Elastic'][0][:2] = [values['modulus'], values['poisson']]
    properties['CaeModel.Density'][0][0] = values['density']
    expected['steps'][0]['loads'][0]['force'] = [values[role] for role in ['force','force2','force3']]
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

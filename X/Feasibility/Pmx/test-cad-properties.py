#!/usr/bin/env python3
"""Persistent material edits, wire ownership and publication refusal checks."""
import argparse
import hashlib
import json
from pathlib import Path
from runpy import run_path
import struct
import tempfile
import zlib

HERE = Path(__file__).resolve().parent
writer = run_path(str(HERE/'write-cad-properties.py'))
reader = writer['reader']


def verify(source, mesh, graph, deck, resave=None):
    checks = []
    def check(name, passed):
        checks.append({'name': name, 'passed': bool(passed)})
        if not passed: raise ValueError(name)
    baseline = reader['inspect'](source, mesh, graph)
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    with source.open('rb') as stream: framing, records, model = reader['base']['read_frames'](stream)
    def pack(records):
        compressed = zlib.compress(struct.pack('<q', len(records))+records+model, wbits=-15)
        return source.read_bytes()[:32]+struct.pack('<i', len(compressed))+compressed+bytes(4)
    with tempfile.TemporaryDirectory(prefix='prepomaxx-material-tests-') as directory:
        root = Path(directory)
        def write(source, output, **kw):
            return writer['write_edit'](source, output, mesh, graph, deck_builder=deck,
                modulus_mpa='84500.5', force_n='42.25', **kw)
        output = root/'material.pmx'
        receipt = write(source, output, poisson='0.25', density='8.1e-9')
        edited = reader['inspect'](output, mesh, graph)
        props = {p['type']: p['rows'] for p in edited['graph']['materials'][0]['properties']}
        check('modulus and Poisson ratio persisted', props['CaeModel.Elastic'][0][:2] == ['84500.5 MPa', '0.25'])
        check('density persisted in original units', props['CaeModel.Density'][0][0] == '8.1E-9 t/mm³')
        check('CAD and mesh semantics preserved', baseline['mesh'] == edited['mesh'] and baseline['cadGeometry'] == edited['cadGeometry'])
        with output.open('rb') as stream: _, changed, changed_model = reader['base']['read_frames'](stream)
        check('exact binary CAD/mesh frame preserved', changed_model == model and receipt['modelBlockSha256'] == hashlib.sha256(model).hexdigest())
        second = root/'second.pmx'
        write(output, second, poisson='-0.2', density='7.85e-9')
        again = reader['inspect'](second, mesh, graph)
        check('repeated editing accepts a negative Poisson ratio', next(p for p in again['graph']['materials'][0]['properties'] if p['type'] == 'CaeModel.Elastic')['rows'][0][1] == '-0.2')
        targets = writer['contract'](records, graph)
        ratio = next(t for t in targets if t['Role'] == 'poisson')
        alias_id = targets[0]['MaximumId']+1
        alias = struct.pack('<BiiBi', 17, alias_id, 1, 9, ratio['RecordId'])
        shared = root/'shared.pmx'
        shared.write_bytes(pack(records[:-1]+alias+records[-1:]))
        shared_output = root/'shared-edited.pmx'
        write(shared, shared_output, poisson='0.25', density='8.1e-9')
        with shared_output.open('rb') as stream: _, shared_graph, _ = reader['base']['read_frames'](stream)
        check('shared original string definition and references preserved', alias in shared_graph and
              writer['string_record'](ratio['RecordId'], ratio['Value']) in shared_graph)
        check('shared-string edit changes only the selected member', reader['inspect'](shared_output, mesh, graph)['graph'] == edited['graph'])
        for name, kwargs in [('poisson-upper', {'poisson': '0.5'}), ('poisson-lower', {'poisson': '-1'}),
                             ('density-zero', {'density': '0'}), ('density-negative', {'density': '-1'}),
                             ('nan', {'poisson': 'NaN'}), ('infinite', {'density': 'Infinity'}),
                             ('excessive-exponent', {'density': '1e-99'})]:
            bad = root/(name+'.pmx')
            try: write(source, bad, **kwargs)
            except ValueError: check(name+' refused without publication', not bad.exists())
            else: raise ValueError('Accepted '+name)
        try: write(source, output)
        except FileExistsError: check('existing destination unchanged', hashlib.sha256(output.read_bytes()).hexdigest() == receipt['outputSha256'])
        else: raise ValueError('Overwrote destination')
        malformed = root/'unsupported-wire.pmx'
        malformed.write_bytes(pack(records[:-1]+bytes([21])+records[-1:]))
        try: write(malformed, root/'bad-wire.pmx')
        except ValueError: check('unsupported wire input refused', not (root/'bad-wire.pmx').exists())
        else: raise ValueError('Accepted unsupported wire record')
        broken = dict(targets[0], Offset=targets[0]['Offset']+1)
        try: writer['patch_members'](records, [broken], {'modulus': '1 MPa'})
        except ValueError: check('incorrect slot offset refused', True)
        else: raise ValueError('Accepted incorrect slot')
        if resave:
            official = reader['inspect'](resave, mesh, graph)
            check('original app resave preserves edited semantics', all(official[k] == edited[k] for k in ['mesh','graph','cadGeometry']))
    check('original source unchanged', hashlib.sha256(source.read_bytes()).hexdigest() == source_hash)
    return {'success': True, 'checks': checks, 'sourceSha256': source_hash}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('source','mesh','graph','deck','output'): parser.add_argument(name, type=Path)
    parser.add_argument('--original-resave', type=Path)
    a = parser.parse_args()
    try: report = verify(a.source, a.mesh, a.graph, a.deck, a.original_resave)
    except Exception as error: report = {'success': False, 'error': str(error)}
    a.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report)); raise SystemExit(0 if report['success'] else 1)

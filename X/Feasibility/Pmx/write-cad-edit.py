#!/usr/bin/env python3
"""Checked original CAD PMX edits; geometry/model/history bytes are preserved."""
from copy import deepcopy
import hashlib
import os
from pathlib import Path
from runpy import run_path
import struct
import tempfile
import zlib

HERE = Path(__file__).resolve().parent
original = run_path(str(HERE/'write-controlled-edit.py'))
reader = run_path(str(HERE/'inspect-cad-project.py'))
decks = original['decks']
positive_decimal = original['positive_decimal']


def write_edit(source, output, mesh_decoder, graph_decoder, *, deck_builder,
               modulus_mpa='105000', force_n='50'):
    source, output = Path(source), Path(output)
    if output.exists() or output.is_symlink() or source.resolve() == output.resolve():
        raise FileExistsError('Choose a new PMX destination.')
    modulus = positive_decimal(modulus_mpa)+' MPa'
    force = positive_decimal(force_n)+' N'
    baseline = reader['inspect'](source, mesh_decoder, graph_decoder)
    with source.open('rb') as stream:
        framing, graph, model = reader['base']['read_frames'](stream)
        stream.seek(0)
        header = stream.read(32)
        stream.seek(framing['opaqueTail']['offset'])
        tail = stream.read()
    if framing['inputSha256'] != baseline['inputSha256']:
        raise ValueError('CAD PMX changed during validation.')
    targets = baseline['editTargets']
    patched = original['patch_graph'](graph, targets, modulus, force)
    expected = deepcopy(baseline['graph'])
    expected['materials'][0]['properties'][0]['rows'][0][0] = modulus
    expected['steps'][0]['loads'][0]['force'][0] = force
    compressed = zlib.compress(struct.pack('<q',len(patched))+patched+model,wbits=-15)
    contents = header+struct.pack('<i',len(compressed))+compressed+tail
    with tempfile.TemporaryDirectory(prefix='.prepomaxx-cad-pmx-',dir=output.parent) as directory:
        staged = Path(directory)/'candidate.pmx'
        staged.write_bytes(contents)
        observed = reader['inspect'](staged,mesh_decoder,graph_decoder)
        if observed['graph'] != expected or observed['mesh'] != baseline['mesh'] or observed['cadGeometry'] != baseline['cadGeometry']:
            raise ValueError('Edited CAD PMX failed semantic readback.')
        with staged.open('rb') as stream:
            _, after_graph, after_model = reader['base']['read_frames'](stream)
        if after_model != model or after_graph != patched:
            raise ValueError('CAD/model bytes differ after packaging.')
        verified = {t['Role']:(t['RecordId'],t['Value']) for t in observed['editTargets']}
        if any(verified[t['Role']] != (t['RecordId'],modulus if t['Role']=='modulus' else force) for t in targets):
            raise ValueError('Edited CAD equations changed ownership.')
        decks['build_project_deck'](baseline,deck_builder,Path(directory)/'baseline.inp')
        decks['build_project_deck'](observed,deck_builder,Path(directory)/'edited.inp')
        os.link(staged,output)
    return {'inputSha256':baseline['inputSha256'],'outputSha256':observed['inputSha256'],
            'modelBlockSha256':hashlib.sha256(model).hexdigest(),
            'cadBrepSha256':baseline['cadGeometry'][0]['BrepSha256'],
            'patchedStringRecords':sorted(t['RecordId'] for t in targets),
            'portableReadbackPassed':True,'unchangedGeometryMeshAndHistory':True}

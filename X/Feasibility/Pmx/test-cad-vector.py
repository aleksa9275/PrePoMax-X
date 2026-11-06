#!/usr/bin/env python3
"""Signed global vector force, magnitude and shared-zero persistence checks."""
import argparse
import hashlib
import json
from pathlib import Path
from runpy import run_path
import tempfile

HERE = Path(__file__).resolve().parent
w = run_path(str(HERE/'write-cad-properties.py'))


def verify(source, mesh, graph, deck, resave=None):
    checks = []
    def check(name, condition):
        checks.append({'name':name,'passed':bool(condition)})
        if not condition: raise ValueError(name)
    baseline = w['inspect'](source, mesh, graph)
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    with source.open('rb') as stream: _, records, model = w['reader']['base']['read_frames'](stream)
    original_slots = w['contract'](records, graph)
    check('all component slots are audited', {'force','force2','force3','magnitude'} <= {t['Role'] for t in original_slots})
    with tempfile.TemporaryDirectory(prefix='prepomaxx-vector-tests-') as directory:
        root = Path(directory)
        def write(output, vector, source=source):
            return w['write_edit'](source, output, mesh, graph, deck_builder=deck,
                modulus_mpa='84500.5',poisson='0.25',density='8.1e-9',force_vector=vector)
        output = root/'vector.pmx'
        write(output, ['-3','4','-12'])
        observed = w['inspect'](output, mesh, graph)
        check('all signed components persist',observed['graph']['steps'][0]['loads'][0]['force'] == ['-3 N','4 N','-12 N'])
        with output.open('rb') as stream: _, changed, after_model = w['reader']['base']['read_frames'](stream)
        slots = {t['Role']:t['Value'] for t in w['contract'](changed, graph)}
        check('original CLoad magnitude equals 13 N',slots['magnitude'] == '13 N')
        check('shared zero strings do not change supports',observed['graph']['steps'][0]['constraints'] == baseline['graph']['steps'][0]['constraints'])
        check('CAD topology, mesh and binary model preserved', observed['mesh'] == baseline['mesh'] and observed['cadGeometry'] == baseline['cadGeometry'] and after_model == model)
        negative = root/'negative.pmx'
        write(negative, ['-42.25','0','0'])
        with negative.open('rb') as stream: _, ng, _ = w['reader']['base']['read_frames'](stream)
        check('negative axial force has positive magnitude',next(t['Value'] for t in w['contract'](ng,graph) if t['Role']=='magnitude') == '42.25 N')
        zero = root/'zero.pmx'
        try: write(zero, ['0','0','0'])
        except ValueError: check('existing nonzero-force engineering gate preserved',not zero.exists())
        else: raise ValueError('Accepted zero vector outside the static deck contract')
        repeat = root/'repeat.pmx'
        write(repeat, ['1.234567','-2.345678','3.456789'], source=output)
        check('reopened vector can be changed again',w['inspect'](repeat,mesh,graph)['graph']['steps'][0]['loads'][0]['force'] == ['1.234567 N','-2.345678 N','3.456789 N'])
        for label, vector in [('short',['1','2']), ('nonfinite',['1','NaN','2']),
                              ('equation',['=1+2','0','0']), ('excessive',['1e99','0','0'])]:
            bad = root/(label+'.pmx')
            try: write(bad, vector)
            except ValueError: check(label+' refused without publication',not bad.exists())
            else: raise ValueError('Accepted '+label)
        # Fresh member IDs make the expanded output unsuitable for the older
        # exclusive positive-axial editing contract; its refusal stays explicit.
        try: w['legacy_reader']['inspect'](output, mesh, graph)
        except ValueError: check('older axial-only contract still refuses transverse loads',True)
        else: raise ValueError('Legacy axial boundary widened silently')
        if resave:
            official = w['inspect'](resave, mesh, graph)
            check('original app resave retains vector/material/CAD semantics',all(official[k]==observed[k] for k in ['graph','mesh','cadGeometry']))
    check('source PMX unchanged',hashlib.sha256(source.read_bytes()).hexdigest()==before)
    return {'success':True,'checks':checks,'sourceSha256':before}


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    for name in ['source','mesh','graph','deck','output']:parser.add_argument(name,type=Path)
    parser.add_argument('--original-resave',type=Path)
    a=parser.parse_args()
    try:r=verify(a.source,a.mesh,a.graph,a.deck,a.original_resave)
    except Exception as error:r={'success':False,'error':str(error)}
    a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
    raise SystemExit(0 if r['success'] else 1)

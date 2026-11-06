#!/usr/bin/env python3
"""Existing named-region assignment edits retain all shared names and labels."""
import argparse
import hashlib
import json
import struct
import zlib
from pathlib import Path
from runpy import run_path
import tempfile

HERE=Path(__file__).resolve().parent
w=run_path(str(HERE/'write-cad-properties.py'))
ASSIGNMENTS={'section':'SOLID_Copy','load':'X0_Copy',
             'supports':{'X0':'X1_Copy','Y0':'Y0_Copy','Z0':'Z0_Copy'}}


def verify(source,mesh,graph,deck,resave=None):
    checks=[]
    def check(name,condition):
        checks.append({'name':name,'passed':bool(condition)})
        if not condition:raise ValueError(name)
    baseline=w['inspect'](source,mesh,graph)
    before=hashlib.sha256(source.read_bytes()).hexdigest()
    with source.open('rb') as f:_,records,model=w['reader']['base']['read_frames'](f)
    targets=w['contract'](records,graph)
    regions=[t for t in targets if 'Region' in t['Role']]
    check('all assignment members audited',len(regions)==5)
    with tempfile.TemporaryDirectory(prefix='prepomaxx-assignment-tests-') as directory:
        root=Path(directory)
        # An equivalent graph with forward-referenced assignment strings covers
        # the MemberReference member layout, independent of formatter interning.
        referenced=bytearray(records)
        preserved=[]
        for target in sorted(regions,key=lambda t:t['Offset'],reverse=True):
            start,length=target['Offset'],target['Length']
            preserved.append(records[start:start+length])
            referenced[start:start+length]=struct.pack('<Bi',9,target['RecordId'])
        referenced=bytes(referenced[:-1])+b''.join(preserved)+bytes([11])
        compressed=zlib.compress(struct.pack('<q',len(referenced))+referenced+model,wbits=-15)
        shared=root/'referenced.pmx'
        shared.write_bytes(source.read_bytes()[:32]+struct.pack('<i',len(compressed))+compressed+bytes(4))
        check('referenced assignment members retain baseline semantics',w['inspect'](shared,mesh,graph)['graph']==baseline['graph'])
        check('all referenced member slots audited',all(t['Kind']==9 for t in w['contract'](referenced,graph) if 'Region' in t['Role']))
        def write(source,output,assignments):
            return w['write_edit'](source,output,mesh,graph,deck_builder=deck,
                modulus_mpa='84500.5',poisson='0.25',density='8.1e-9',
                force_vector=['-3','4','-12'],assignments=assignments)
        output=root/'assigned.pmx'
        receipt=write(shared,output,ASSIGNMENTS)
        observed=w['inspect'](output,mesh,graph)
        definition=observed['graph'];step=definition['steps'][0]
        check('solid section uses compatible element region',definition['sections'][0]['region']=='SOLID_Copy')
        check('load moves to opposite face',step['loads'][0]['region']=='X0_Copy')
        check('supports persist all chosen node regions',{s['name']:s['region'] for s in step['constraints']}==ASSIGNMENTS['supports'])
        check('all set names and membership remain unchanged',all(definition[k]==baseline['graph'][k] for k in ['nodeSets','elementSets']))
        check('all object names remain unchanged',
              [s['name'] for s in step['constraints']]==[s['name'] for s in baseline['graph']['steps'][0]['constraints']] and
              definition['sections'][0]['name']==baseline['graph']['sections'][0]['name'] and step['loads'][0]['name']=='Force')
        check('CAD and mesh semantics preserved',observed['cadGeometry']==baseline['cadGeometry'] and observed['mesh']==baseline['mesh'])
        with output.open('rb') as f:_,_,after_model=w['reader']['base']['read_frames'](f)
        check('binary CAD/mesh bytes unchanged',after_model==model)
        check('receipt names all changed assignment slots',{t['Role'] for t in regions}<=set(receipt['editedMembers']))
        again=root/'again.pmx'
        write(output,again,{'section':'SOLID','load':'X1','supports':{'X0':'X0','Y0':'Y0','Z0':'Z0'}})
        reopened=w['inspect'](again,mesh,graph)['graph']
        check('reopened assignments can return to original regions',reopened['sections']==baseline['graph']['sections'] and
              reopened['steps'][0]['constraints']==baseline['graph']['steps'][0]['constraints'] and reopened['steps'][0]['loads'][0]['region']=='X1')
        for name,assignments in [('missing',{'load':'MISSING'}),('wrong-load-kind',{'load':'SOLID'}),
                                 ('wrong-section-kind',{'section':'X0'}),('unknown-support',{'supports':{'Missing':'X0'}}),
                                 ('unknown-field',{'rename':'No'}),('invalid-support-map',{'supports':'X0'}),
                                 ('nonstring-region',{'load':123})]:
            bad=root/(name+'.pmx')
            try:write(source,bad,assignments)
            except ValueError:check(name+' refused without publication',not bad.exists())
            else:raise ValueError('Accepted '+name)
        if resave:
            official=w['inspect'](resave,mesh,graph)
            check('original app resave retains assignments and shared names',all(official[k]==observed[k] for k in ['graph','mesh','cadGeometry']))
    check('original project unchanged',hashlib.sha256(source.read_bytes()).hexdigest()==before)
    return {'success':True,'checks':checks,'sourceSha256':before}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ['source','mesh','graph','deck','output']:parser.add_argument(name,type=Path)
    parser.add_argument('--original-resave',type=Path)
    a=parser.parse_args()
    try:r=verify(a.source,a.mesh,a.graph,a.deck,a.original_resave)
    except Exception as error:r={'success':False,'error':str(error)}
    a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
    raise SystemExit(0 if r['success'] else 1)

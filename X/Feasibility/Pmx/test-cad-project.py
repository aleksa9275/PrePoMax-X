#!/usr/bin/env python3
"""Original CAD PMX projection/write refusals and byte-preserving interoperability."""
import argparse
import hashlib
import json
from pathlib import Path
from runpy import run_path
import struct
import tempfile
import zlib

HERE=Path(__file__).resolve().parent
reader=run_path(str(HERE/'inspect-cad-project.py'))
writer=run_path(str(HERE/'write-cad-edit.py'))


def verify(source,mesh,graph,deck,original_resave=None):
    checks=[]
    def check(name,value):
        checks.append({'name':name,'passed':bool(value)})
        if not value:raise ValueError(name)
    baseline=reader['inspect'](source,mesh,graph)
    check('original CAD/C3D4 mesh and assigned regions',len(baseline['mesh']['nodes'])==276 and len(baseline['mesh']['elements'])==843 and set(baseline['graph']['nodeSets'])=={'X0','Y0','Z0','X1'})
    check('original CAD BREP and matching topology ownership',baseline['cadGeometry'][0]['Name']=='Solid_part-1' and baseline['cadGeometry'][0]['Id']==1)
    before=hashlib.sha256(source.read_bytes()).hexdigest()
    with source.open('rb') as f:framing,records,model=reader['base']['read_frames'](f)
    with tempfile.TemporaryDirectory(prefix='prepomaxx-cad-project-tests-') as directory:
        root=Path(directory);output=root/'edited.pmx'
        receipt=writer['write_edit'](source,output,mesh,graph,deck_builder=deck,modulus_mpa='105000',force_n='50')
        edited=reader['inspect'](output,mesh,graph)
        check('portable changed modulus and axial force',edited['graph']['materials'][0]['properties'][0]['rows'][0][0]=='105000 MPa' and edited['graph']['steps'][0]['loads'][0]['force']==['50 N','0 N','0 N'])
        check('all CAD and mesh records retained',baseline['cadGeometry']==edited['cadGeometry'] and baseline['mesh']==edited['mesh'])
        with output.open('rb') as f:_,changed_graph,changed_model=reader['base']['read_frames'](f)
        check('exact original binary geometry/mesh frame preserved',changed_model==model and receipt['modelBlockSha256']==hashlib.sha256(model).hexdigest())
        expected=writer['original']['patch_graph'](records,baseline['editTargets'],'105000 MPa','50 N')
        check('only three audited string records change; history untouched',changed_graph==expected)
        if original_resave:
            official=reader['inspect'](original_resave,mesh,graph)
            check('original app resave retains native-edited semantics',official['graph']==edited['graph'] and official['mesh']==edited['mesh'] and official['cadGeometry']==edited['cadGeometry'])
        def packed(g,b,tail=bytes(4),header=source.read_bytes()[:32]):
            compressed=zlib.compress(struct.pack('<q',len(g))+g+b,wbits=-15)
            return header+struct.pack('<i',len(compressed))+compressed+tail
        quadr=struct.pack('<iiii',1,1,10,4)
        check('quadratic mutation target unambiguous',model.count(quadr)==1)
        invalid=list((
            ('old-header',source.read_bytes().replace(b'PrePoMax v3.0.0',b'PrePoMax v2.6.0',1)),
            ('truncated-mesh',packed(records,model[:-1])),
            ('nonfinite-cad-coordinate',packed(records,model[:12]+struct.pack('<d',float('nan'))+model[20:])),
            ('quadratic-tetra-gate',packed(records,model.replace(quadr,struct.pack('<iiii',1,1,24,4),1))),
            ('unsupported-history',packed(records.replace(b'PrePoMax.Commands.CImportFile',b'PrePoMax.Commands.CImportFyle'),model)),
            ('saved-results',packed(records,model,bytes(8))),
        ))
        for label,content in invalid:
            bad=root/(label+'.pmx');bad.write_bytes(content)
            try:reader['inspect'](bad,mesh,graph)
            except (ValueError,OSError):check(label+' refused',True)
            else:raise ValueError('Accepted '+label)
        try:writer['write_edit'](source,output,mesh,graph,deck_builder=deck)
        except FileExistsError:check('existing output refused',True)
        else:raise ValueError('Overwrote existing project')
        try:writer['write_edit'](source,root/'bad.pmx',mesh,graph,deck_builder=deck,modulus_mpa='0')
        except ValueError:check('invalid physical edit publishes no file',not(root/'bad.pmx').exists())
        else:raise ValueError('Accepted invalid modulus')
    check('original file unchanged',hashlib.sha256(source.read_bytes()).hexdigest()==before)
    return {'success':True,'checks':checks,'inputSha256':before,'scope':'Checked one-part CAD/C3D4 PMX; full project corpus and release gates remain'}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('source','mesh','graph','deck','output'):parser.add_argument(name,type=Path)
    parser.add_argument('--original-resave',type=Path)
    a=parser.parse_args()
    try:r=verify(a.source,a.mesh,a.graph,a.deck,a.original_resave)
    except Exception as error:r={'success':False,'error':str(error)}
    a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'success':r['success'],'checks':len(r.get('checks',[])),'error':r.get('error')}))
    raise SystemExit(0 if r['success'] else 1)

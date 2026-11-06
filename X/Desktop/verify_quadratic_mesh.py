#!/usr/bin/env python3
"""Native quadratic geometry/topology evidence; numerical calculation is checked separately."""
import argparse,hashlib,json,shutil
from pathlib import Path
from cad_import import NativeCadTool,file_sha256,run_process
from cad_document import CadDocument,CadMesh


def verify(runtime,inspector,mesh_host,source,output):
    output.mkdir(parents=True,exist_ok=False)
    checks=[];report={'success':False,'checks':checks,'sourceSha256':file_sha256(source)}
    def check(name,condition):
        checks.append({'name':name,'passed':bool(condition)})
        if not condition:raise ValueError(name)
    def read(command,*,cancel=None):
        r=run_process(command,cancel=cancel)
        if r.returncode:raise ValueError(r.stderr.decode(errors='replace'))
        return json.loads(r.stdout)
    command=['dotnet',str(mesh_host)]
    def decode(path,*,cancel=None):return read(['dotnet',str(inspector),'scene',str(path)],cancel=cancel)
    doc=CadDocument(source,NativeCadTool(runtime),decode)
    linear=quad=None
    try:
        linear=CadMesh(doc,command,read,5)
        quad=CadMesh(doc,command,read,5,element_order=2)
        a,b=linear.scene,quad.scene
        check('all quadratic tetrahedra retain ten distinct nodes',all(e['vtkCellType']==24 and len(set(e['nodeIds']))==10 for e in b['elements']))
        check('quadratic native mesh retains every original part',len(a['cadMesh']['parts'])==len(b['cadMesh']['parts'])==len(doc.parts))
        check('quadratic profile supports native static calculations',b['cadMesh']['elementOrder']==2 and b['cadMesh']['analysisEligible'] is True)
        check('linear default remains analysis eligible',a['cadMesh']['elementOrder']==1 and a['cadMesh']['analysisEligible'] is True)
        check('quadratic mesh adds midside nodes',len(b['nodes'])>len(a['nodes']))
        check('native parameter receipts declare original second order',quad.parameter_result['elementOrder']==2 and quad.parameter_result['analysisEligible'] is True)
        frozen=quad.freeze(output/'frozen')
        check('frozen mesh records order and static eligibility',frozen['elementOrder']==2 and frozen['analysisEligible'] is True)
        check('all frozen original CAD and mesh hashes verify',all(file_sha256(output/'frozen'/f['file'])==f['sha256'] for f in frozen['files']))
        reopened=read([*command,str(quad.mesh)])
        check('original INP reader retains exact quadratic connectivity',reopened['elements']==b['elements'])
        face_counts={s['name']:s['count'] for s in b['nodeSets'] if '_FACE_' in s['name']}
        check('quadratic CAD face sets retain midside nodes',face_counts and all(v>=6 for v in face_counts.values()))
        check('original source file unchanged',file_sha256(source)==report['sourceSha256'])
        doc.verify()
        shutil.copyfile(quad.mesh,output/'quadratic.inp');shutil.copyfile(linear.mesh,output/'linear.inp')
        report.update(success=True,linear={'nodes':len(a['nodes']),'elements':len(a['elements'])},quadratic={'nodes':len(b['nodes']),'elements':len(b['elements'])},faceSets=face_counts,meshSha256=file_sha256(quad.mesh))
    except Exception as error:report['error']=str(error)
    finally:
        if quad:quad.close()
        if linear:linear.close()
        doc.close()
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ['runtime','inspector','mesh_host','source','output']:parser.add_argument(name,type=Path)
    a=parser.parse_args();r=verify(*(getattr(a,n).resolve() for n in ['runtime','inspector','mesh_host','source','output']))
    print(json.dumps(r));raise SystemExit(0 if r['success'] else 1)

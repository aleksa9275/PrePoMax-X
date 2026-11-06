#!/usr/bin/env python3
"""Real original native CAD edits; analytical and retained Windows comparisons."""
import argparse
import json
import math
from pathlib import Path
import shutil
import sys

from cad_import import NativeCadTool,file_sha256,run_process
from cad_document import CadDocument
from cad_edit import apply_edit,prepare_export
from cad_history import GeometryHistory

ROOT=Path(__file__).resolve().parents[2]


def verify(runtime,inspector,output,operations=('translate','split','repair','export')):
    output.mkdir(parents=True,exist_ok=False)
    checks=[]
    def check(name,passed):
        checks.append({'name':name,'passed':bool(passed)})
        if not passed:raise ValueError(name)
    def decode(path,*,cancel=None):
        command=['dotnet',str(inspector)] if inspector.suffix=='.dll' else [str(inspector)]
        result=run_process([*command,'scene',str(path)],cancel=cancel)
        if result.returncode:raise ValueError(result.stderr.decode(errors='replace'))
        return json.loads(result.stdout)
    def solids(document):
        return [decode(v)['cad']['entities']['solid'][0]['properties'] for b,v in document.parts]
    fixture=ROOT/'APIs/Python/Test_Scripts/Models/sweep_two_apart.brep'
    before=file_sha256(fixture)
    reference=json.loads((ROOT/'.project/reports/native-cad-operations/windows-reference.json').read_text())
    pins={r['operation']:r for r in reference['operations']}
    document=CadDocument(fixture,NativeCadTool(runtime),decode)
    report={'success':False,'checks':checks,'operations':{}}
    try:
        baseline=solids(document)
        if 'history' in operations:
            history=GeometryHistory()
            edited=apply_edit(document,decode,1,'translate',[7,-3,5])
            translated_hashes=[[file_sha256(p) for p in pair] for pair in edited.parts]
            active=edited
            try:
                history.validate_edit(document,edited);history.edited(document)
                restored=history.target('undo');history.restored('undo',active);active=restored
                check('native undo restores original BREP and VIS bytes',all(file_sha256(a)==file_sha256(b) for p,q in zip(active.parts,document.parts) for a,b in zip(p,q)))
                restored=history.target('redo');history.restored('redo',active);active=restored
                check('native redo restores translated BREP and VIS exactly',[[file_sha256(p) for p in pair] for pair in active.parts]==translated_hashes)
                check('undo source remains independently owned',document.root.exists() and active.root.exists())
                # The outer scope owns the initial document; detach it before
                # releasing only the checkpoint-generated document here.
                history.undo.clear();history.redo.clear()
            finally:edited.close()
        if 'translate' in operations:
            edited=apply_edit(document,decode,1,'translate',[7,-3,5])
            try:
                values=solids(edited)
                check('translation preserves two owned CAD parts',len(edited.parts)==2)
                check('translation matches original Windows BREP bytes',edited.edits[-1]['outputBrepSha256']==pins['translate']['brepSha256'])
                check('translated center is analytical',all(math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-10) for a,b in zip(values[0]['center_of_mass'],[12,2,15])))
                check('translation retains volume',math.isclose(values[0]['volume'][0],2000,rel_tol=1e-12,abs_tol=1e-9))
                check('unselected BREP and VIS bytes unchanged',all(file_sha256(a)==file_sha256(b) for a,b in zip(document.parts[1],edited.parts[1])))
                check('unselected measured geometry unchanged',values[1]==baseline[1])
                check('edit provenance retains original part origins',edited.edits[-1]['partOrigins']==[1,2])
                shutil.copytree(edited.root,output/'translate')
                report['operations']['translate']=edited.edits[-1]
            finally:edited.close()
        if 'split' in operations:
            edited=apply_edit(document,decode,1,'split',{'origin':[0,0,10],'normal':[0,0,1]})
            try:
                values=solids(edited)
                check('split retains unselected part plus two new solids',len(edited.parts)==3)
                check('split matches original Windows BREP bytes',edited.edits[-1]['outputBrepSha256']==pins['split']['brepSha256'])
                check('both split volumes are analytical',all(math.isclose(v['volume'][0],1000,rel_tol=1e-12,abs_tol=1e-9) for v in values[:2]))
                centers=sorted([v['center_of_mass'] for v in values[:2]],key=lambda v:v[2])
                check('split centers are analytical',all(math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-10) for actual,expected in zip(centers,[[5,5,5],[5,5,15]]) for a,b in zip(actual,expected)))
                check('split source origins map to selected original part',edited.edits[-1]['partOrigins']==[1,1,2])
                check('split preserves unselected BREP/VIS bytes',all(file_sha256(a)==file_sha256(b) for a,b in zip(document.parts[1],edited.parts[2])))
                shutil.copytree(edited.root,output/'split');report['operations']['split']=edited.edits[-1]
            finally:edited.close()
            for values in [{'origin':[0,0,10],'normal':[0,0,0]},{'origin':[0,0,100],'normal':[0,0,1]}]:
                try:apply_edit(document,decode,1,'split',values)
                except ValueError:check('invalid or non-intersecting plane refused '+str(values),True)
                else:raise ValueError('Non-splitting plane accepted')
        if 'rotate' in operations:
            edited=apply_edit(document,decode,1,'rotate',{'center':[1,2,3],'axis':[0,0,1],'degrees':90})
            try:
                values=solids(edited);scene=decode(edited.parts[0][1])
                check('rotation volume is analytical',math.isclose(values[0]['volume'][0],2000,rel_tol=1e-12,abs_tol=1e-9))
                check('off-origin axis rotation center is analytical',all(math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-10) for a,b in zip(values[0]['center_of_mass'],[-2,6,10])))
                bounds=[v for axis in ('x','y','z') for v in [min(n[axis] for n in scene['nodes']),max(n[axis] for n in scene['nodes'])]]
                check('rotation bounds are analytical',all(math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-10) for a,b in zip(bounds,[-7,3,1,11,0,20])))
                check('rotation retains untouched BREP and VIS bytes',all(file_sha256(a)==file_sha256(b) for a,b in zip(document.parts[1],edited.parts[1])))
                check('rotation retains original face identities',[f['id'] for f in scene['cad']['entities']['face']]==[f['id'] for f in decode(document.parts[0][1])['cad']['entities']['face']])
                report['operations']['rotate']=edited.edits[-1];shutil.copytree(edited.root,output/'rotate')
            finally:edited.close()
            for values in [{'center':[0,0,0],'axis':[0,0,0],'degrees':90},{'center':[0,0,0],'axis':[0,0,1],'degrees':0},{'center':[0,0,0],'axis':[0,0,1],'degrees':float('inf')}]:
                try:apply_edit(document,decode,1,'rotate',values)
                except ValueError:check('invalid rotation refused '+str(values),True)
                else:raise ValueError('Invalid rotation accepted')
        if 'mirror' in operations:
            edited=apply_edit(document,decode,1,'mirror',{'origin':[1,2,3],'normal':[1,1,0]})
            try:
                values=solids(edited);scene=decode(edited.parts[0][1]);original=decode(document.parts[0][1])
                check('mirror retains positive analytical volume',math.isclose(values[0]['volume'][0],2000,rel_tol=1e-12,abs_tol=1e-9))
                check('oblique off-origin mirror centroid is analytical',all(math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-10) for a,b in zip(values[0]['center_of_mass'],[-2,-2,10])))
                bounds=[v for axis in ('x','y','z') for v in [min(n[axis] for n in scene['nodes']),max(n[axis] for n in scene['nodes'])]]
                check('mirror bounds are analytical',all(math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-10) for a,b in zip(bounds,[-7,3,-7,3,0,20])))
                check('mirror retains face edge and vertex identities',all([e['id'] for e in scene['cad']['entities'][kind]]==[e['id'] for e in original['cad']['entities'][kind]] for kind in ['face','edge','vertex']))
                check('mirror retains untouched BREP and VIS bytes',all(file_sha256(a)==file_sha256(b) for a,b in zip(document.parts[1],edited.parts[1])))
                check('mirror origin mapping is retained',edited.edits[-1]['partOrigins']==[1,2])
                report['operations']['mirror']=edited.edits[-1];shutil.copytree(edited.root,output/'mirror')
            finally:edited.close()
            for values in [{'origin':[0,0,0],'normal':[0,0,0]},{'origin':[float('nan'),0,0],'normal':[0,0,1]}]:
                try:apply_edit(document,decode,1,'mirror',values)
                except ValueError:check('invalid mirror refused '+str(values),True)
                else:raise ValueError('Invalid mirror accepted')
        if 'scale' in operations:
            for label,factors,center,bounds in [('uniform',[2,2,2],[9,8,17],[-1,19,-2,18,-3,37]),('nonuniform',[2,.5,1.5],[9,3.5,13.5],[-1,19,1,6,-1.5,28.5])]:
                edited=apply_edit(document,decode,1,'scale',{'center':[1,2,3],'factors':factors})
                try:
                    values=solids(edited);scene=decode(edited.parts[0][1]);original=decode(document.parts[0][1])
                    check(label+' scale volume is analytical',math.isclose(values[0]['volume'][0],2000*math.prod(factors),rel_tol=1e-12,abs_tol=1e-9))
                    check(label+' scale centroid is analytical',all(math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-10) for a,b in zip(values[0]['center_of_mass'],center)))
                    actual=[v for axis in ('x','y','z') for v in [min(n[axis] for n in scene['nodes']),max(n[axis] for n in scene['nodes'])]]
                    check(label+' scale bounds are analytical',all(math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-10) for a,b in zip(actual,bounds)))
                    check(label+' scale retains face edge and vertex identities',all([e['id'] for e in scene['cad']['entities'][kind]]==[e['id'] for e in original['cad']['entities'][kind]] for kind in ['face','edge','vertex']))
                    check(label+' scale retains untouched BREP and VIS bytes',all(file_sha256(a)==file_sha256(b) for a,b in zip(document.parts[1],edited.parts[1])))
                    check(label+' scale origin mapping retained',edited.edits[-1]['partOrigins']==[1,2])
                    report['operations']['scale-'+label]=edited.edits[-1];shutil.copytree(edited.root,output/('scale-'+label))
                finally:edited.close()
            for factors in [[0,1,1],[-1,1,1],[1,1,1],[float('inf'),1,1],[1001,1,1]]:
                try:apply_edit(document,decode,1,'scale',{'center':[0,0,0],'factors':factors})
                except ValueError:check('invalid scale refused '+str(factors),True)
                else:raise ValueError('Invalid scale accepted')
        if 'repair' in operations:
            edited=apply_edit(document,decode,1,'repair',1e-6)
            try:
                values=solids(edited)
                check('valid-box repair matches original Windows BREP bytes',edited.edits[-1]['outputBrepSha256']==pins['repair']['brepSha256'])
                check('repair preserves both part measurements',values==baseline)
                check('repair preserves untouched part bytes',all(file_sha256(a)==file_sha256(b) for a,b in zip(document.parts[1],edited.parts[1])))
                shutil.copytree(edited.root,output/'repair');report['operations']['repair']=json.loads(json.dumps(edited.edits[-1]))
                edited.edits[-1]['parameters']['tolerance']=.5
                try:edited.verify()
                except ValueError:check('changed in-memory edit history refused',True)
                else:raise ValueError('Tampered edit history accepted')
            finally:edited.close()
            for value in [0,-1,float('nan'),2]:
                try:apply_edit(document,decode,1,'repair',value)
                except ValueError:check('invalid repair tolerance refused '+str(value),True)
                else:raise ValueError('Invalid tolerance accepted')
        if 'export' in operations:
            export=prepare_export(document,decode,1)
            target=output/'export.step'
            try:
                target.write_bytes(b'preserve existing destination')
                try:export.publish(target)
                except FileExistsError:check('existing STEP bytes preserved',target.read_bytes()==b'preserve existing destination')
                else:raise ValueError('STEP destination overwritten')
                target=output/'verified.step'
                receipt=export.publish(target)
                check('STEP published only after native readback',receipt['nativeReadbackPassed'] and file_sha256(target)==receipt['outputSha256'])
                report['operations']['export']=receipt
            finally:export.close()
            reopened=CadDocument(target,document.tool,decode)
            try:
                values=solids(reopened)
                check('STEP roundtrip retains one selected solid',len(values)==1)
                check('STEP roundtrip volume is analytical',math.isclose(values[0]['volume'][0],2000,rel_tol=1e-12,abs_tol=1e-9))
                check('STEP roundtrip center is analytical',all(math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-10) for a,b in zip(values[0]['center_of_mass'],[5,5,10])))
            finally:reopened.close()
        if 'export_all' in operations:
            export=prepare_export(document,decode,None)
            target=output/'whole-model.step'
            try:
                receipt=export.publish(target)
                check('whole model uses original unchanged assembly command',receipt['command']=='STEP_ASSEMBLY')
                check('whole model retains both solid origins',len(receipt['solidOrigins'])==2 and {o['sourcePartId'] for o in receipt['solidOrigins']}=={1,2})
                check('whole model output bytes verified',file_sha256(target)==receipt['outputSha256'])
                try:export.publish(target)
                except FileExistsError:check('whole model existing destination preserved',file_sha256(target)==receipt['outputSha256'])
                else:raise ValueError('Whole STEP overwritten')
                report['operations']['export_all']=receipt
            finally:export.close()
            reopened=CadDocument(target,document.tool,decode)
            try:
                values=solids(reopened)
                check('whole model roundtrip retains two solids',len(values)==2)
                check('whole model roundtrip retains analytical volumes',all(math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-9) for a,b in zip(sorted(v['volume'][0] for v in values),[768,2000])))
            finally:reopened.close()
        for part,values in [(0,[1,0,0]),(1,[0,0,0]),(1,[float('nan'),0,0]),(1,[1,2])]:
            try:apply_edit(document,decode,part,'translate',values)
            except (ValueError,TypeError):check('invalid translation refused '+str((part,values)),True)
            else:raise ValueError('Invalid translation accepted')
        document.verify()
        check('original fixture unchanged',file_sha256(fixture)==before)
        report['success']=True
    except Exception as error:report['error']=str(error)
    finally:document.close()
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ['runtime','inspector','output']:parser.add_argument(name,type=Path)
    parser.add_argument('--operation',action='append',choices=['translate','rotate','mirror','scale','split','repair','export','export_all','history'])
    a=parser.parse_args();r=verify(a.runtime,a.inspector.resolve(),a.output,a.operation or ['translate','rotate','mirror','scale','split','repair','export','export_all','history'])
    print(json.dumps(r));raise SystemExit(0 if r['success'] else 1)

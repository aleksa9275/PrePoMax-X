#!/usr/bin/env python3
"""Research only: exact recorded Windows solver through existing CrossOver."""
import argparse,hashlib,importlib.util,json,os,re,shutil,subprocess,tempfile
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--solver',required=True,type=Path);p.add_argument('--wine',required=True,type=Path);p.add_argument('--bottle',required=True);p.add_argument('--output-dir',required=True,type=Path);a=p.parse_args()
 a.output_dir.mkdir(parents=True,exist_ok=False)
 spec=importlib.util.spec_from_file_location('reference',ROOT/'X/Feasibility/Solver/run-reference.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 expected=json.loads((ROOT/'X/Execution/solver-builds.json').read_text())['builds'][0]['files'];actual={name:sha(a.solver.parent/name)for name in expected}
 if actual!=expected:raise ValueError('Exact solver/runtime fingerprint mismatch; no substitute accepted')
 baseline=module.parse_dat((ROOT/'.project/reports/windows-reference/solver/uniaxial.dat').read_text())
 text=(ROOT/'X/Feasibility/Solver/uniaxial-cube.inp').read_text();rows=[]
 for backend in ['Default','Pardiso','PaStiX','Spooles','IterativeScaling','IterativeCholesky']:
  row={'backend':backend,'success':False};folder=a.output_dir/backend;folder.mkdir()
  with tempfile.TemporaryDirectory(prefix='prepomaxx-exact-solver-')as temp:
   work=Path(temp);inp=text if backend=='Default'else re.sub(r'^\*STATIC\s*$', '*STATIC, SOLVER='+backend,text,flags=re.M|re.I)
   if backend!='Default'and inp==text:raise ValueError('Static solver selector not inserted')
   (work/'uniaxial.inp').write_text(inp);shutil.copyfile(work/'uniaxial.inp',folder/'uniaxial.inp')
   environment=dict(os.environ,OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',CCX_NPROC_EQUATION_SOLVER='1',CCX_NPROC_RESULTS='1')
   done=subprocess.run([str(a.wine),'--bottle',a.bottle,str(a.solver),'-i','uniaxial'],cwd=work,env=environment,text=True,capture_output=True,timeout=120)
   def clean(s):return s.replace(temp,'<temporary>').replace(str(a.solver.parent),'<solver>')
   row.update(exitCode=done.returncode,stdout=clean(done.stdout),stderr=clean(done.stderr),inputSha256=sha(work/'uniaxial.inp'))
   match=re.search(r'CalculiX Version\s+([\d.]+)',done.stdout);row['solverVersion']=match.group(1)if match else None
   if (work/'uniaxial.dat').exists():
    blocks=module.parse_dat((work/'uniaxial.dat').read_text());row['checks']=module.analytical_checks(blocks);row['comparisonToNativeWindows']={}
    for field,tol in [('displacements',1e-9),('forces',1e-5),('stresses',1e-4)]:
     left,right=sorted(blocks.get(field,[])),sorted(baseline[field]);ids=2 if field=='stresses'else 1
     shape=len(left)==len(right)and all(len(x)==len(y)and x[:ids]==y[:ids]for x,y in zip(left,right))
     error=max((abs(x[i]-y[i])for x,y in zip(left,right)for i in range(ids,min(len(x),len(y)))),default=0)
     row['comparisonToNativeWindows'][field]={'sameIdsAndShape':shape,'maximumAbsoluteDifference':error,'absoluteTolerance':tol,'matches':shape and error<=tol}
    row['success']=done.returncode==0 and row['solverVersion']=='2.22'and all(c['passed']for c in row['checks'])and all(c['matches']for c in row['comparisonToNativeWindows'].values())
   for suffix in ['dat','frd','sta','cvg']:
    f=work/('uniaxial.'+suffix)
    if f.exists():shutil.copyfile(f,folder/f.name)
   row['files']={f.name:sha(f)for f in folder.iterdir()if f.is_file()}
   (folder/'result.json').write_text(json.dumps(row,indent=2)+'\n');rows.append(row)
   print(json.dumps({'backend':backend,'success':row['success'],'exitCode':row['exitCode'],'checks':sum(c['passed']for c in row.get('checks',[]))}),flush=True)
 report={'success':all(r['success']for r in rows),'recordedAtUtc':datetime.now(timezone.utc).isoformat(),'evidenceKind':'Exact Windows executable/runtime through existing CrossOver on Apple Silicon; not native macOS solver acceptance','solverFiles':actual,'toolSha256':sha(Path(__file__)),'analyticalCheckerSha256':sha(ROOT/'X/Feasibility/Solver/run-reference.py'),'threads':1,'runs':rows,'limits':['One synthetic C3D8 cube only; no frequency/buckling/contact/nonlinear/full RC2 application acceptance','No production solver/backend/default changed','No native solver or bitwise cross-platform result claim']}
 (a.output_dir/'verification.json').write_text(json.dumps(report,indent=2)+'\n');return 0 if report['success']else 1
if __name__=='__main__':raise SystemExit(main())

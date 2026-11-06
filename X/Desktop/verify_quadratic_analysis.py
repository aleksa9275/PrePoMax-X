#!/usr/bin/env python3
"""Real force-driven and curved-boundary C3D10 CalculiX/FRD verification."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from quadratic_analysis import boundary_fixture, field_errors, force_fixture


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('solve','results','mesh_host','registry','solver_bin','curved_mesh','output'):
        p.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    p.add_argument('--solver-id',required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    r={'success':False,'checks':[],'commands':[]}
    def check(name,passed):
        r['checks'].append({'name':name,'passed':bool(passed)})
        if not passed:raise ValueError(name)
    def host(path):return ['dotnet',str(path)] if path.suffix=='.dll' else [str(path)]
    def run(command,expected=0):
        done=subprocess.run(list(map(str,command)),capture_output=True,text=True,timeout=180)
        r['commands'].append({'arguments':list(map(str,command)),'exitCode':done.returncode,'stdout':done.stdout,'stderr':done.stderr})
        if done.returncode!=expected:raise ValueError('Unexpected process exit; see commands')
        return json.loads(done.stdout or done.stderr)
    def solve(name,mesh,spec,expected=0):
        folder=a.output/name;folder.mkdir()
        (folder/'mesh.inp').write_bytes(mesh);(folder/'analysis.json').write_text(json.dumps(spec,indent=2)+'\n')
        outcome=run([*host(a.solve),'--registry',a.registry,'run-static',a.solver_id,a.solver_bin,folder/'mesh.inp',folder/'analysis.json',folder/'solve','90'],expected)
        if expected:return outcome
        check(name+' native solver completes',outcome['success'] and outcome['solverExecuted'] and outcome['versionMatches'])
        scene=run([*host(a.results),'inspect-frd',folder/'solve/analysis.frd'])
        (folder/'results.json').write_text(json.dumps(scene,indent=2)+'\n')
        original=run([*host(a.mesh_host),folder/'mesh.inp'])
        check(name+' all ten-node IDs/connectivity survive FRD',[{k:e[k] for k in ('id','vtkCellType','nodeIds')} for e in scene['elements']]==original['elements'] and len(scene['nodes'])==len(original['nodes']))
        errors=field_errors(scene);r[name]={'errors':errors,'meshSha256':hashlib.sha256(mesh).hexdigest(),'nodes':len(scene['nodes']),'elements':len(scene['elements'])}
        # Curved 100-mm fixture includes original E8 coordinates, CalculiX
        # extrapolation and six-significant-digit FRD fields. Bounds are fixed
        # for this new fixture; existing linear/kernel tolerances are unchanged.
        bounds = (2e-7, 2e-8, 1e-4, 1e-4) if name=='curved' else (2e-8, 1e-10, 1e-5, 1e-5)
        r[name]['bounds']=dict(zip(('displacement','lateral','stress','forceResultant'),bounds))
        check(name+' analytical axial displacement',errors['displacement']<=bounds[0] and errors['lateral']<=bounds[1])
        check(name+' analytical axial and other stresses',errors['axialStress']<=bounds[2] and errors['otherStress']<=bounds[2])
        check(name+' reaction/load equilibrium',max(map(abs,errors['forceResultant'].values()))<=bounds[3])
        return scene
    try:
        mesh,spec=force_fixture();solve('force',mesh,spec)
        original=run([*host(a.mesh_host),a.curved_mesh])
        curved,spec,geometry=boundary_fixture(a.curved_mesh.read_bytes(),original);r['curvedGeometry']=geometry
        check('curved test contains curved midsides and free interior nodes',geometry['curvedEdgeIncidences']>0 and geometry['interiorNodes']>0)
        solve('curved',curved,spec)
        mesh,spec=force_fixture()
        outcome=solve('invalid-jacobian',mesh.replace(b'8,0,0,.5',b'8,0,0,-5'),spec,1)
        check('native solver rejects curved inversion despite positive corners',outcome['solverExecuted'] and not outcome['success'] and 'nonpositive jacobian' in outcome['stdout'].lower())
        # The independent measurement refusal is still required.
        r.update(success=True,scope='C3D10 linear static native calculation; original measurement remains gated; no general curved-quality certification')
    except Exception as error:r['error']=str(error)
    (a.output/'verification.json').write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({'success':r['success'],'checks':len(r['checks']),'error':r.get('error')}))
    return 0 if r['success'] else 1

if __name__=='__main__':raise SystemExit(main())

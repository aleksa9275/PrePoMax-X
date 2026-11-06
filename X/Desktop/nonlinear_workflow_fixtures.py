"""Reproducible analytical/demo inputs for original mechanical solver workflows."""
import json
from pathlib import Path
from solid_workflow_fixtures import build_fixture,FORMULATIONS


def write_examples(folder,decode):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    inventories={}
    mesh,spec,inventory=build_fixture((*FORMULATIONS,'C3D5','C3D13'),pyramid_conversion='hexahedrons')
    spec['step']['constraints']=spec['step']['constraints'][:2]
    spec['step']['pressures']=[{'name':'Top-pressure','nodeSet':'TOP','magnitude':'-1'}]
    (folder/'pressure-solids.inp').write_bytes(mesh);(folder/'pressure-solids.json').write_text(json.dumps(spec,indent=2)+'\n')
    inventories['pressure-solids']=inventory
    mesh,base,inventory=build_fixture(('C3D20',))
    path=folder/'gravity-column.inp';path.write_bytes(mesh)
    spec=json.loads(json.dumps(base));spec['materials'][0]['density']='0.001'
    spec['step']['constraints']=spec['step']['constraints'][:2]
    spec['step']['gravityLoads']=[{'name':'Gravity','elementSet':'SOLID_1','acceleration':['0','0','1000']}]
    (folder/'gravity-column.json').write_text(json.dumps(spec,indent=2)+'\n')
    inventories['gravity-column']=inventory
    scene=decode(path);nodes=scene['nodes']
    text=mesh.decode()
    for key,axis in [('X0','x'),('Y0','y')]:
        ids=[n['id'] for n in nodes if n[axis]==0]
        text+='*Nset,Nset='+key+'\n'+','.join(map(str,ids))+'\n'
    for name,geometric,displacement in [('plastic-tension',False,'0.01'),('finite-tension',True,'0.2')]:
        spec=json.loads(json.dumps(base));spec['materials'][0]['poissonsRatio']='0.3'
        spec['step']['constraints']=[{'name':'Fix-X','nodeSet':'X0','displacements':['0',None,None]},
            {'name':'Fix-Y','nodeSet':'Y0','displacements':[None,'0',None]},
            {'name':'Bottom','nodeSet':'BOTTOM','displacements':[None,None,'0']},
            {'name':'Top','nodeSet':'TOP','displacements':[None,None,displacement]}]
        spec['step'].update(nonlinearGeometry=geometric,initialTimeIncrement=.05,maximumTimeIncrement=.05,maximumIncrements=1000)
        if not geometric:
            spec['materials'][0].update(plasticCurve=[['1','0'],['2','0.01']],hardening='Isotropic')
        (folder/(name+'.inp')).write_text(text);(folder/(name+'.json')).write_text(json.dumps(spec,indent=2)+'\n')
        inventories[name]=inventory
    return inventories

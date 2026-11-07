"""Analytical shell/membrane/line fixtures; no product mesh generation."""
import copy
import json
from plane_workflow_fixtures import build_fixture

CASES=('shell-tension','membrane-tension','membrane-quadratic','shell-bending','composite-tension','line-tension','beam-bending','beam-circular','shell-pressure','beam-centerline')


def grid(nx,ny,length=1.,width=1.,form='S8R'):
    nodes={};lookup={};elements=[]
    def node(x,y):
        if (x,y) not in lookup:
            n=11+3*len(nodes);lookup[(x,y)]=n;nodes[n]=(x,y,0.)
        return lookup[(x,y)]
    for j in range(ny):
        for i in range(nx):
            c=[(i*length/nx,j*width/ny),((i+1)*length/nx,j*width/ny),((i+1)*length/nx,(j+1)*width/ny),(i*length/nx,(j+1)*width/ny)]
            c += [((a[0]+b[0])/2,(a[1]+b[1])/2) for a,b in zip(c,c[1:]+c[:1])]
            elements.append((101+7*len(elements),[node(*p) for p in c]))
    rows=['*Node']+[f'{n}, {x:.17g}, {y:.17g}, {z:.17g}' for n,(x,y,z) in nodes.items()]
    rows+=['*Element,Type='+form+',Elset=PATCH']+[','.join(map(str,[e,*ids])) for e,ids in elements]
    return rows,nodes


def sets(rows,definitions):
    for name,ids in definitions.items():
        if not ids:continue
        rows.append('*Nset,Nset='+name)
        rows += [','.join(map(str,ids[i:i+8])) for i in range(0,len(ids),8)]


def fixture(case):
    _,base=build_fixture('plane-stress',('8R',));base.pop('modelSpace');base['sections']=[]
    base['step']['pressures']=[];base['step']['constraints']=[];base['step']['loads']=[];base['step']['nodalHistorySets']=[]
    if case in ('shell-tension','membrane-tension','membrane-quadratic'):
        raw,spec=build_fixture('plane-stress', ('6','8','8R') if case=='membrane-quadratic' else ('3','4','4R') if case=='membrane-tension' else ('3','6','4','4R','8','8R'));spec.pop('modelSpace');raw=raw.decode().replace('CPS','S' if case.startswith('shell') else 'M3D')
        raw=raw.replace('Type=S3,','Type=S3,')
        # Read our own generated fixture records solely to assign exact edge-load
        # weights. Product import/engineering parsing stays in original C#.
        nodes={};elements=[];block=None
        for line in raw.splitlines():
            if line=='*Node':block='node'
            elif line.startswith('*'):block='other'
            elif block=='node':
                n,x,y=map(float,line.split(','));nodes[int(n)]=(x,y,0.)
        for section in spec['sections']:section.update(kind='shell' if case.startswith('shell') else 'membrane',thickness='.1',offset='0')
        spec['step']['pressures']=[];spec['step']['loads']=[]
        spec['step']['constraints'].append({'name':'Planar','nodeSet':'ALL','displacements':[None,None,'0']})
        rows=raw.strip().splitlines();load_sets={};index=0
        for part,suffix in enumerate(('6','8','8R') if case=='membrane-quadratic' else ('3','4','4R') if case=='membrane-tension' else ('3','6','4','4R','8','8R')):
            xs=sorted((x,n) for n,(x,y,z) in nodes.items() if y==1 and 2*part<=x<=2*part+1)
            weights=[.025,.05,.025] if suffix in ('3','4','4R') else [.1/12,.1/3,.1/6,.1/3,.1/12]
            for (_,n),force in zip(xs,weights):
                index+=1;name='LOAD_'+str(index);load_sets[name]=[n];spec['step']['loads'].append({'name':name,'nodeSet':name,'forcePerNode':['0',str(force),'0']})
        if case=='membrane-quadratic':
            spec['step']['loads']=[];spec['step']['constraints']=[]
            for n,(x,y,z) in nodes.items():
                name='PRESCRIBED_'+str(n);load_sets[name]=[n];origin=2*int((x+1e-9)/2)
                spec['step']['constraints'].append({'name':name,'nodeSet':name,'displacements':[str(-.00025*(x-origin)),str(.001*y),'0']})
        sets(rows,load_sets);return ('\n'.join(rows)+'\n').encode(),spec
    if case=='beam-centerline':
        mesh,spec=fixture('beam-bending');spec['step']['elementOutput']='TwoD';return mesh,spec
    if case=='shell-pressure':
        mesh,spec=fixture('shell-bending');spec['step'].pop('moments',None);spec['step']['pressures']=[{'name':'Normal-pressure','elementSet':'PATCH','face':2,'magnitude':'.00001'}];return mesh,spec
    if case in ('shell-bending','composite-tension'):
        bending=case=='shell-bending';rows,nodes=grid(10 if bending else 20,2,length=10)
        end=10
        defs={'ROOT':[n for n,p in nodes.items() if p[0]==0],'TIP':[n for n,p in nodes.items() if p[0]==end], 'ALL':list(nodes),'Y0':[n for n,p in nodes.items() if p[1]==0]}
        base['sections']=[{'name':'Section','material':'ELASTIC','elementSet':'PATCH','kind':'shell' if bending else 'composite',**({'thickness':'.2','offset':'0'} if bending else {'layers':[{'material':'ELASTIC','thickness':'.05'},{'material':'STIFF','thickness':'.1'},{'material':'ELASTIC','thickness':'.05'}]})}]
        base['materials'][0]['poissonsRatio']='0'
        if bending:base['step']['constraints']=[{'name':'Clamp','nodeSet':'ROOT','displacements':['0','0','0'],'rotations':['0','0','0']}]
        else:
            base['materials'].append({'name':'STIFF','youngsModulus':'2000','poissonsRatio':'0'})
            base['step']['constraints']=[{'name':'Root','nodeSet':'ROOT','displacements':['0',None,None]},{'name':'Lateral','nodeSet':'Y0','displacements':[None,'0',None]},{'name':'Planar','nodeSet':'ALL','displacements':[None,None,'0']}]
        for i,(y,n) in enumerate(sorted((nodes[n][1],n) for n in defs['TIP'])):
            name='END_'+str(i);defs[name]=[n];weight=[1/12,1/3,1/6,1/3,1/12][i]
            if bending:base['step'].setdefault('moments',[]).append({'name':name,'nodeSet':name,'momentPerNode':['0',str(.001*weight),'0']})
            else:base['step']['loads'].append({'name':name,'nodeSet':name,'forcePerNode':[str(.3*weight),'0','0']})
        base['step']['elementOutput']='ThreeD'
        base['step']['nodalHistorySets']=['ROOT','TIP'];sets(rows,defs);return ('\n'.join(rows)+'\n').encode(),base
    forms=('B31','B31R','B21','B32','B32R','T3D2','T2D2','T3D3') if case=='line-tension' else ('B32R',)
    nodes={};lookup={};elements=[];blocks=[];defs={'ROOT':[],'TIP':[],'ALL':[],'BEAMS':[]}
    def node(x,y):
        if (x,y) not in lookup:
            n=11+3*len(nodes);lookup[(x,y)]=n;nodes[n]=(x,y,0.)
        return lookup[(x,y)]
    for part,form in enumerate(forms):
        ids=[]
        for i in range(10):
            points=[(i,3*part),(i+1,3*part)] if form not in ('B32','B32R','T3D3') else [(i,3*part),(i+.5,3*part),(i+1,3*part)]
            eid=101+7*len(elements);elements.append((eid,[node(*p) for p in points]));ids.append(eid)
        name='LINE_'+str(part);blocks.append((name,form,ids))
        defs['ROOT'].append(node(0,3*part));defs['TIP'].append(node(10,3*part))
        if form.startswith('B'):defs['BEAMS'] += [n for n,p in nodes.items() if p[1]==3*part]
        base['sections'].append({'name':'Section_'+str(part),'material':'ELASTIC','elementSet':name,'kind':'beam' if form.startswith('B') else 'truss','dimensions':['.2','.3'] if form.startswith('B') else ['.06'],**({'shape':'RECT','direction':[0,0,1]} if form.startswith('B') else {})})
    defs['ALL']=list(nodes);rows=['*Node']+[f'{n}, {x}, {y}, {z}' for n,(x,y,z) in nodes.items()]
    for name,form,ids in blocks:
        rows.append('*Element,Type='+form+',Elset='+name)
        rows += [','.join(map(str,[e,*conn])) for e,conn in elements if e in ids]
    base['materials'][0]['poissonsRatio']='0'
    if case=='line-tension':
        base['step']['constraints']=[{'name':'Axial-root','nodeSet':'ROOT','displacements':['0',None,None]},{'name':'Lateral','nodeSet':'ALL','displacements':[None,'0','0']},{'name':'Rotation','nodeSet':'BEAMS','displacements':[None,None,None],'rotations':['0','0','0']}]
        base['step']['loads']=[{'name':'Tension','nodeSet':'TIP','forcePerNode':['.06','0','0']}]
    else:
        base['step']['constraints']=[{'name':'Clamp','nodeSet':'ROOT','displacements':['0','0','0'],'rotations':['0','0','0']}]
        base['step']['moments']=[{'name':'Bending','nodeSet':'TIP','momentPerNode':['0','.001','0']}]
    if case=='beam-circular':base['sections'][0].update(shape='CIRC',dimensions=['.2','.2'])
    base['step']['nodalHistorySets']=['ROOT','TIP'];sets(rows,defs);return ('\n'.join(rows)+'\n').encode(),base


def write_examples(folder):
    for case in CASES:
        mesh,spec=fixture(case);(folder/(case+'.inp')).write_bytes(mesh);(folder/(case+'.json')).write_text(json.dumps(spec,indent=2)+'\n')

if __name__=='__main__':
    from pathlib import Path
    write_examples(Path(__file__).resolve().parents[1]/'Analysis/StaticDeck')

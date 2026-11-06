"""Analytical integration fixtures; not a product mesh generator or parser."""
import json
from pathlib import Path

FORMULATIONS=('C3D4','C3D10','C3D10T','C3D6','C3D15','C3D8','C3D8R','C3D8I','C3D20','C3D20R')
EDGES={
 'tet':[(0,1),(1,2),(2,0),(0,3),(1,3),(2,3)],
 'wedge':[(0,1),(1,2),(2,0),(3,4),(4,5),(5,3),(0,3),(1,4),(2,5)],
 'hex':[(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)],
 # Original INP pyramid factory expects Gmsh ordering; the original parser
 # restores its internal pyramid edge order before CalElement conversion.
 'pyramid':[(0,1),(0,3),(0,4),(1,2),(1,4),(2,3),(2,4),(3,4)]}


def build_fixture(forms=FORMULATIONS, *, pyramid_conversion=None):
    nodes={};elements=[];blocks=[];node_lookup={}
    def node(point):
        point=tuple(point)
        if point not in node_lookup:
            identity=11+len(nodes)*3;node_lookup[point]=identity;nodes[identity]=point
        return node_lookup[point]
    for part,form in enumerate(forms):
        offset=part*2
        def point(x,y,z):return (offset+x,y,z)
        def element(corners,kind):
            quadratic=form in ('C3D10','C3D10T','C3D15','C3D20','C3D20R','C3D13')
            coords=list(corners)
            if quadratic:coords += [tuple((corners[a][i]+corners[b][i])/2 for i in range(3)) for a,b in EDGES[kind]]
            identity=101+len(elements)*7
            elements.append({'id':identity,'formulation':form,'nodeIds':[node(p) for p in coords]})
            return identity
        ids=[]
        if form in ('C3D5','C3D13'):
            faces=[[(0,0,0),(1,0,0),(1,1,0),(0,1,0)],[(0,1,1),(1,1,1),(1,0,1),(0,0,1)],
                   [(0,0,1),(1,0,1),(1,0,0),(0,0,0)],[(0,1,0),(1,1,0),(1,1,1),(0,1,1)],
                   [(0,0,0),(0,1,0),(0,1,1),(0,0,1)],[(1,0,1),(1,1,1),(1,1,0),(1,0,0)]]
            for face in faces:ids.append(element([point(*p) for p in face]+[point(.5,.5,.5)],'pyramid'))
        else:
            for z in (0,.5):
                c=[point(x,y,z+dz) for x,y,dz in [(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,.5),(1,0,.5),(1,1,.5),(0,1,.5)]]
                if form in ('C3D4','C3D10','C3D10T'):
                    for tet in [(0,1,2,6),(0,2,3,6),(0,3,7,6),(0,7,4,6),(0,4,5,6),(0,5,1,6)]:ids.append(element([c[i] for i in tet],'tet'))
                elif form in ('C3D6','C3D15'):
                    for wedge in [(0,1,2,4,5,6),(0,2,3,4,6,7)]:ids.append(element([c[i] for i in wedge],'wedge'))
                else:ids.append(element(c,'hex'))
        blocks.append({'name':f'SOLID_{part+1}','formulation':form,'ids':ids})
    rows=['*Node']+[str(n)+','+','.join(format(v,'.17g') for v in p) for n,p in nodes.items()]
    for b in blocks:
        rows.append(f"*Element, Type={b['formulation']}, Elset={b['name']}")
        for e in elements:
            if e['id'] in b['ids']:
                record=[e['id'],*e['nodeIds']]
                rows += [','.join(map(str,record[i:i+16]))+(',' if i+16<len(record) else '') for i in range(0,len(record),16)]
    sets={'ALL':list(nodes),'BOTTOM':[n for n,p in nodes.items() if p[2]==0],'TOP':[n for n,p in nodes.items() if p[2]==1]}
    for name,ids in sets.items():
        rows.append('*Nset,Nset='+name);rows += [','.join(map(str,ids[i:i+8])) for i in range(0,len(ids),8)]
    spec={'schemaVersion':1,'unitSystem':'mm-N-s-C','materials':[{'name':'ELASTIC','youngsModulus':'1000','poissonsRatio':'0'}],
        'sections':[{'name':f'Section_{i}','material':'ELASTIC','elementSet':b['name']} for i,b in enumerate(blocks)],
        'step':{'name':'Static-1','timePeriod':1,'initialTimeIncrement':1,'minimumTimeIncrement':1e-5,'maximumTimeIncrement':1,'maximumIncrements':100,'outputFrequency':1,
            'constraints':[{'name':'Lateral','nodeSet':'ALL','displacements':['0','0',None]},
                           {'name':'Bottom','nodeSet':'BOTTOM','displacements':[None,None,'0']},
                           {'name':'Top','nodeSet':'TOP','displacements':[None,None,'0.001']}],
            'loads':[],'nodalHistorySets':['BOTTOM','TOP'],'elementHistorySets':[]}}
    if pyramid_conversion:spec['pyramidConversion']=pyramid_conversion
    return ('\n'.join(rows)+'\n').encode(),spec,{'formulations':list(forms),'nodes':len(nodes),'elements':len(elements),'freeAxialNodes':sum(0<p[2]<1 for p in nodes.values()),'blocks':blocks}


def write_examples(folder):
    folder.mkdir(parents=True,exist_ok=False)
    for name,forms,conversion in [('mixed-solids',FORMULATIONS,None),('mixed-pyramids',('C3D5','C3D13'),'wedges')]:
        mesh,spec,inventory=build_fixture(forms,pyramid_conversion=conversion)
        (folder/(name+'.inp')).write_bytes(mesh);(folder/(name+'.json')).write_text(json.dumps(spec,indent=2)+'\n')

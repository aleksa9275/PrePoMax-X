"""Reproducible rod/column examples; fixture preparation, not a product mesher."""
import json
from pathlib import Path
from solid_workflow_fixtures import EDGES


def column(length,cells,width=1,depth=1,form='C3D20'):
    nodes={};lookup={};elements=[]
    def node(p):
        p=tuple(p)
        if p not in lookup:
            identity=11+3*len(nodes);lookup[p]=identity;nodes[identity]=p
        return lookup[p]
    for k in range(cells):
        corners=[(x*width,y*depth,(k+z)*length/cells) for x,y,z in [(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)]]
        points=corners+[tuple((corners[a][i]+corners[b][i])/2 for i in range(3)) for a,b in EDGES['hex']]
        elements.append((101+7*k,[node(p) for p in points]))
    rows=['*Node']+[str(n)+','+','.join(format(v,'.17g') for v in p) for n,p in nodes.items()]
    rows+=['*Element,Type='+form+',Elset=SOLID']
    for identity,ids in elements:
        record=[identity,*ids];rows += [','.join(map(str,record[i:i+16]))+(',' if i+16<len(record) else '') for i in range(0,len(record),16)]
    for name,ids in {'ALL':list(nodes),'BOTTOM':[n for n,p in nodes.items() if p[2]==0],'TOP':[n for n,p in nodes.items() if p[2]==length]}.items():
        rows+=['*Nset,Nset='+name]
        rows += [','.join(map(str,ids[i:i+8])) for i in range(0,len(ids),8)]
    return ('\n'.join(rows)+'\n').encode()


def write_examples(folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    for name,kind,length,cells,depth in [('axial-frequency','frequency',1,12,.5),('column-buckling','buckling',10,20,.5)]:
        spec={'schemaVersion':1,'unitSystem':'mm-N-s-C','materials':[{'name':'ELASTIC','youngsModulus':'1000','poissonsRatio':'0'}],
            'sections':[{'name':'Section','material':'ELASTIC','elementSet':'SOLID'}],
            'step':{'name':kind.title()+'-1','kind':kind,'modes':3,'timePeriod':1,'initialTimeIncrement':1,'minimumTimeIncrement':1e-5,
                'maximumTimeIncrement':1,'maximumIncrements':100,'outputFrequency':1,'constraints':[], 'loads':[], 'nodalHistorySets':[],'elementHistorySets':[]}}
        if kind=='frequency':
            spec['materials'][0]['density']='0.001'
            spec['step']['constraints']=[{'name':'Lateral','nodeSet':'ALL','displacements':['0','0',None]}, {'name':'Bottom','nodeSet':'BOTTOM','displacements':[None,None,'0']}]
        else:
            spec['step']['constraints']=[{'name':'Clamp','nodeSet':'BOTTOM','displacements':['0','0','0']}]
            spec['step']['loads']=[{'name':'Reference-compression','nodeSet':'TOP','forcePerNode':['0','0','-0.0125']}]
        (folder/(name+'.inp')).write_bytes(column(length,cells,depth=depth))
        (folder/(name+'.json')).write_text(json.dumps(spec,indent=2)+'\n')

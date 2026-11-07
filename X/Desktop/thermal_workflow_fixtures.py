"""Small reproducible thermal examples, independent of the application mesher."""
import copy
import json
from pathlib import Path
from eigenmode_workflow_fixtures import column

CASES = ('steady-conduction','transient-heating','surface-heating','body-heating','film-cooling','nodal-heating')

def definition(name):
    s={'schemaVersion':1,'unitSystem':'mm-N-s-C','materials':[{'name':'THERMAL','conductivity':'1 mW/(mm·°C)'}],
       'sections':[{'name':'Solid','material':'THERMAL','elementSet':'SOLID'}],
       'step':{'name':name,'kind':'heat-transfer','timePeriod':1,'initialTimeIncrement':1,'minimumTimeIncrement':1e-5,
               'maximumTimeIncrement':1,'maximumIncrements':1000,'outputFrequency':1,'constraints':[],'loads':[],
               'nodalHistorySets':['BOTTOM','TOP'],'elementHistorySets':['SOLID'],'thermal':{'steadyState':True},
               'temperatures':[{'name':'Cold','nodeSet':'BOTTOM','temperature':'0 °C'}],'heatLoads':[]}}
    t=s['step']
    if name=='steady-conduction':t['temperatures'].append({'name':'Hot','nodeSet':'TOP','temperature':'100 °C'})
    elif name=='transient-heating':
        s['materials'][0].update(density='0.001',specificHeat='1000')
        t.update(timePeriod=1,initialTimeIncrement=.05,maximumTimeIncrement=.05,nodalHistorySets=['TOP'],elementHistorySets=[])
        t['thermal']={'steadyState':False,'initialTemperature':'10 °C','direct':True}
        t['temperatures']=[];t['heatLoads']=[{'name':'Heater','kind':'body','region':'SOLID','magnitude':'1'}]
    elif name=='surface-heating':t['heatLoads']=[{'name':'Input','kind':'surface','region':'TOP','magnitude':'10 mW/mm²'}]
    elif name=='body-heating':
        t['temperatures'].append({'name':'Top','nodeSet':'TOP','temperature':'0'})
        t['heatLoads']=[{'name':'Generation','kind':'body','region':'SOLID','magnitude':'8 mW/mm³'}]
    elif name=='film-cooling':
        t['temperatures'][0]['temperature']='100'
        t['heatLoads']=[{'name':'Convection','kind':'film','region':'TOP','magnitude':'2 mW/(mm²·°C)','sinkTemperature':'20 °C'}]
    elif name=='nodal-heating':
        # C3D8 top has four nodes. This is power per node, total 10 mW.
        t['heatLoads']=[{'name':'Nodal-heater','kind':'nodal','region':'TOP','magnitude':'2.5 mW'}]
    else:raise ValueError(name)
    return s


def mesh(name):
    data=column(1,4,width=1,depth=1)
    if name!='nodal-heating':return data
    # Retain only the corners of each original fixture cell and their nodes.
    rows=data.decode().splitlines();start=rows.index('*Element,Type=C3D20,Elset=SOLID');nodes={int(r.split(',')[0]):r for r in rows[1:start]}
    end=next(i for i in range(start+1,len(rows)) if rows[i].startswith('*'));records=[];used=set()
    for i in range(start+1,end,2):
        values=list(map(int,(rows[i]+rows[i+1]).split(',')));ids=values[1:9];used.update(ids);records.append(','.join(map(str,[values[0],*ids])))
    result=['*Node',*[nodes[n] for n in nodes if n in used],'*Element,Type=C3D8,Elset=SOLID',*records]
    for setname,z in [('ALL',None),('BOTTOM',0),('TOP',1)]:
        ids=[n for n in used if z is None or float(nodes[n].split(',')[3])==z]
        result+=['*Nset,Nset='+setname,','.join(map(str,sorted(ids)))]
    return ('\n'.join(result)+'\n').encode()


def write_examples(folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    for case in CASES:
        (folder/(case+'.inp')).write_bytes(mesh(case))
        (folder/(case+'.json')).write_text(json.dumps(definition(case),indent=2)+'\n')

if __name__=='__main__':write_examples(Path(__file__).resolve().parents[1]/'Analysis/StaticDeck')

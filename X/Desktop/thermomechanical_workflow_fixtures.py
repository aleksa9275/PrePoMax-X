"""Connected radiation, amplitude and thermal-stress verification examples."""
import copy
import json
from pathlib import Path
from eigenmode_workflow_fixtures import column
from thermal_workflow_fixtures import definition as thermal_definition

CASES=('radiation-cooling','temperature-conductivity','amplitude-heating','amplitude-force','free-expansion','restrained-expansion')

def fixture(case):
    root=Path(__file__).resolve().parents[2];cube=root/'X/Analysis/StaticDeck/cube-mesh.inp'
    if case in ('radiation-cooling','temperature-conductivity','amplitude-heating'):
        spec=thermal_definition('transient-heating' if case=='amplitude-heating' else 'steady-conduction');data=column(1,32 if case=='temperature-conductivity' else 4,width=1,depth=1)
        t=spec['step'];t['name']=case
        if case=='radiation-cooling':
            spec['materials'][0]['conductivity']='0.01';t['temperatures']=[{'name':'Hot','nodeSet':'BOTTOM','temperature':'100'}]
            t['heatLoads']=[{'name':'Radiation','kind':'radiation','region':'TOP','magnitude':'0.8','sinkTemperature':'20'}]
            t['thermal'].update(absoluteZero=-273.15,stefanBoltzmann=5.670374419e-11,initialTemperature='100')
        elif case=='temperature-conductivity':
            spec['materials'][0].pop('conductivity');spec['materials'][0]['conductivityTable']=[['1','0'],['2','100']];t.update(initialTimeIncrement=.025,maximumTimeIncrement=.025)
        else:
            spec['amplitudes']=[{'name':'Pulse','points':[[0,0],[.5,2],[1,0]]}]
            t['heatLoads'][0]['amplitude']='Pulse'
        return data,spec
    spec=json.loads((root/'X/Analysis/StaticDeck/cube-analysis.json').read_text());data=cube.read_bytes();t=spec['step'];t['name']=case
    spec['materials'][0]['youngsModulus']='1000';t.update(initialTimeIncrement=1,maximumTimeIncrement=1,maximumIncrements=1000)
    if case=='amplitude-force':
        spec['amplitudes']=[{'name':'Pulse','points':[[0,0],[.5,1],[1,.5]],'timeSpan':'TotalTime','shiftX':0,'shiftY':0}];t['loads'][0]['amplitude']='Pulse'
    else:
        spec['materials'][0].update(expansion='0.00001',expansionZeroTemperature='20');t['loads']=[];t['initialTemperature']='20'
        t['temperatureFields']=[{'name':'Heating','nodeSet':'NALL','temperature':'120'}]
        if case=='restrained-expansion':
            data+=b'*Nset,Nset=Z1\n5,6,7,8\n';t['constraints'].append({'name':'Top-restraint','nodeSet':'Z1','displacements':[None,None,'0']})
        elif case!='free-expansion':raise ValueError(case)
    return data,spec


def write_examples(folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    for case in CASES:
        data,spec=fixture(case);(folder/(case+'.inp')).write_bytes(data);(folder/(case+'.json')).write_text(json.dumps(spec,indent=2)+'\n')

if __name__=='__main__':write_examples(Path(__file__).resolve().parents[1]/'Analysis/StaticDeck')

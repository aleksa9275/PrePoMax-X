"""Single active axial mode: exact M=rho*V/3, K=EA/L in an original C3D8 cube."""
import json
from pathlib import Path

CASES=('implicit-ramp','implicit-damped','modal-ramp','modal-damped')
PERIOD=.0064
DT=.0001
OMEGA=(3_000_000.)**.5
ZETA=.05

def fixture(case):
    root=Path(__file__).resolve().parents[2];mesh=(root/'X/Analysis/StaticDeck/cube-mesh.inp').read_bytes();s=json.loads((root/'X/Analysis/StaticDeck/cube-analysis.json').read_text());s['materials'][0].update(youngsModulus='1000',poissonsRatio='0',density='0.001')
    t=s['step'];t.update(name=case,kind='modal-dynamics' if case.startswith('modal') else 'dynamic',timePeriod=PERIOD,initialTimeIncrement=DT,maximumTimeIncrement=DT,minimumTimeIncrement=1e-9,maximumIncrements=1000)
    t['constraints']=[{'name':'Lateral','nodeSet':'NALL','displacements':[None,'0','0']},{'name':'Clamp','nodeSet':'X0','displacements':['0',None,None]}]
    t['loads']=[{'name':'Ramp-load','nodeSet':'X1','forcePerNode':['0.25','0','0'],'amplitude':'Ramp'}]
    s['amplitudes']=[{'name':'Ramp','points':[[0,0],[PERIOD,1]],'timeSpan':'StepTime'}]
    t['dynamics']={'alpha':0,'direct':True,'damping':'Off','basisModes':1}
    if case=='implicit-damped':t['dynamics'].update(damping='Rayleigh',massDamping=2*ZETA*OMEGA)
    if case=='modal-damped':t['dynamics'].update(damping='Constant',modalDampingRatio=ZETA)
    return mesh,s

def write_examples(folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    for case in CASES:
        data,spec=fixture(case);(folder/(case+'.inp')).write_bytes(data);(folder/(case+'.json')).write_text(json.dumps(spec,indent=2)+'\n')

if __name__=='__main__':write_examples(Path(__file__).resolve().parents[1]/'Analysis/StaticDeck')

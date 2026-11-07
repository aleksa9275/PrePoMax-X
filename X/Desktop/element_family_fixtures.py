"""Reproducible discrete and cross-family calculation examples (original solver)."""
import json,copy
from pathlib import Path
CASES=['spring-pair', 'spring-axial', 'spring-ground', 'gap-compression', 'mass-spring-frequency', 'mass-spring-transient', 'beam-frequency', 'shell-frequency', 'plane-frequency', 'axisymmetric-frequency', 'mixed-solid-springs', 'beam-transient', 'beam-modal-transient']
def generate():
    base=Path(__file__).resolve().parents[1]/'Analysis/StaticDeck'
    def step(kind='static'):
     return dict(name='Step-1',timePeriod=1.,initialTimeIncrement=1.,minimumTimeIncrement=1e-7,maximumTimeIncrement=1.,maximumIncrements=100,outputFrequency=1,kind=kind,constraints=[dict(name='Guide',nodeSet='ALL',displacements=[None,'0','0']),dict(name='Fixed',nodeSet='ROOT',displacements=['0',None,None])],loads=[dict(name='Force',nodeSet='TIP',forcePerNode=['10','0','0'])],nodalHistorySets=['ROOT','TIP'],elementHistorySets=[])
    def write(name,mesh,spec):
     (base/(name+'.inp')).write_text(mesh);(base/(name+'.json')).write_text(json.dumps(spec,indent=2)+'\n')
    mesh='*Node, Nset=ALL\n1,0,0,0\n2,1,0,0\n*Element, Type=SPRING2, Elset=SPRINGS\n1,1,2\n*Nset,Nset=ROOT\n1\n*Nset,Nset=TIP\n2\n'
    spec=dict(schemaVersion=1,unitSystem='m-N-s-C',materials=[],sections=[dict(name='Spring',material='',elementSet='SPRINGS',kind='spring',dof=1,secondDof=1,stiffness='1000')],step=step())
    write('spring-pair',mesh,spec)
    a=copy.deepcopy(spec);a['sections'][0].update(dof=0,secondDof=0);write('spring-axial',mesh.replace('SPRING2','SPRINGA'),a)
    a=copy.deepcopy(spec);a['sections'][0]['secondDof']=0;a['step']['constraints']=a['step']['constraints'][:1];write('spring-ground',mesh.replace('SPRING2','SPRING1').replace('1,1,2','1,2'),a)
    a=copy.deepcopy(spec);a['sections'][0]=dict(name='Gap',material='',elementSet='SPRINGS',kind='gap',direction=[1,0,0],clearance='0',stiffness='1000',tensileForce='0.000001');a['step']['loads'][0]['forcePerNode']=['-10','0','0'];a['step'].update(initialTimeIncrement=.1,maximumTimeIncrement=.1,nonlinearGeometry=True);write('gap-compression',mesh.replace('SPRING2','GAPUNI'),a)
    a=copy.deepcopy(spec);a['sections'].append(dict(name='Mass',material='',elementSet='MASSES',kind='mass',mass='2'));a['step']=step('frequency');a['step']['loads']=[];a['step'].update(modes=1);m=mesh+'*Element,Type=MASS,Elset=MASSES\n2,2\n';write('mass-spring-frequency',m,a)
    a=copy.deepcopy(a);a['step']=step('dynamic');a['step'].update(timePeriod=.2,initialTimeIncrement=.005,maximumTimeIncrement=.005,dynamics=dict(alpha=0,direct=True));write('mass-spring-transient',m,a)
    # Existing family fixtures are copied unchanged; only calculation/density controls differ.
    for family,source in [('beam','beam-centerline'),('shell','shell-bending'),('plane','plane-stress'),('axisymmetric','axisymmetric')]:
     a=json.loads((base/(source+'.json')).read_text());a['step']['kind']='frequency';a['step']['modes']=3;a['step']['loads']=[];a['step']['moments']=[];a['step']['pressures']=[];a['step']['nodalHistorySets']=[];a['step']['elementHistorySets']=[]
     for material in a['materials']:material['density']='1'
     write(family+'-frequency',(base/(source+'.inp')).read_text(),a)

    (base/'mass-spring-frequency.inp').write_text('*Node,Nset=ALL\n1,0,0,0\n2,1,0,0\n3,2,0,0\n4,3,0,0\n5,4,0,0\n*Element,Type=SPRING2,Elset=SPRINGS\n1,1,2\n2,2,3\n3,3,4\n4,4,5\n*Element,Type=MASS,Elset=MASSES\n5,2\n6,3\n7,4\n8,5\n*Nset,Nset=ROOT\n1\n*Nset,Nset=TIP\n5\n')
    a=json.loads((base/'mass-spring-frequency.json').read_text());a['step']['modes']=2;(base/'mass-spring-frequency.json').write_text(json.dumps(a,indent=2)+'\n')
    # A continuum cube and four axial springs share the original root nodes.
    mesh='*Node,Nset=ALL\n1,0,0,0\n2,1,0,0\n3,1,1,0\n4,0,1,0\n5,0,0,1\n6,1,0,1\n7,1,1,1\n8,0,1,1\n9,-1,0,0\n10,-1,1,0\n11,-1,0,1\n12,-1,1,1\n*Element,Type=C3D8,Elset=BODY\n1,1,2,3,4,5,6,7,8\n*Element,Type=SPRINGA,Elset=SPRINGS\n2,9,1\n3,10,4\n4,11,5\n5,12,8\n*Nset,Nset=ROOT\n9,10,11,12\n*Nset,Nset=TIP\n2,3,6,7\n'
    a=copy.deepcopy(spec);a['materials']=[dict(name='Elastic',youngsModulus='1000',poissonsRatio='0',density='1')];a['sections'][0].update(dof=0,secondDof=0,stiffness='250');a['sections'].append(dict(name='Solid',material='Elastic',elementSet='BODY'));a['step']['loads'][0]['forcePerNode']=['25','0','0'];write('mixed-solid-springs',mesh,a)
    # Original beam transient and stored-basis paths on the same shared line mesh.
    for kind,name in [('dynamic','beam-transient'),('modal-dynamics','beam-modal-transient')]:
     a=json.loads((base/'beam-centerline.json').read_text());a['materials'][0]['density']='.001';a['step'].update(kind=kind,timePeriod=2,initialTimeIncrement=.025,maximumTimeIncrement=.025,moments=[],loads=[dict(name='Tip-force',nodeSet='TIP',forcePerNode=['0','0','-.001'])],dynamics=dict(alpha=0,direct=True,basisModes=3))
     write(name,(base/'beam-centerline.inp').read_text(),a)

if __name__=='__main__':generate()

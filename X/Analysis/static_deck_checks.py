"""Independent semantics checks for the retained analytical cube, tests only.

This deliberately handles only the small numeric fixture grammar. Application
INP parsing remains the original CaeModel reader; this is not another decoder.
"""
import hashlib
import json
from pathlib import Path
import copy


def cards(text):
    result=[]
    for raw in text.splitlines():
        line=raw.strip()
        if not line or line.startswith('**'):continue
        if line.startswith('*'):
            fields=[v.strip() for v in line.split(',')]
            parameters={}
            for field in fields[1:]:
                key,sep,value=field.partition('=')
                if not sep:parameters[key.upper()]=''
                else:parameters[key.upper()]=value.upper()
            result.append([fields[0].upper(),parameters,[]])
        elif result:result[-1][2].append([v.strip() for v in line.split(',')])
        else:raise ValueError('Fixture data before a keyword')
    return result


def snapshot(text):
    parsed=cards(text);nodes={};elements={};nsets={};esets={};materials={};sections=[];constraints={};loads={};outputs={};name=None
    for keyword,parameters,rows in parsed:
        if keyword=='*NODE':
            for row in rows:
                identifier=int(row[0]);nodes[identifier]=tuple(float(v) for v in row[1:])
                if 'NSET' in parameters:nsets.setdefault(parameters['NSET'],set()).add(identifier)
        elif keyword=='*ELEMENT':
            for row in rows:
                identifier=int(row[0]);elements[identifier]=(parameters['TYPE'],tuple(int(v) for v in row[1:]))
                if 'ELSET' in parameters:esets.setdefault(parameters['ELSET'],set()).add(identifier)
        elif keyword in ('*NSET','*ELSET'):
            key=keyword[1:];target=nsets if key=='NSET' else esets
            target.setdefault(parameters[key],set()).update(int(v) for row in rows for v in row if v)
        elif keyword=='*MATERIAL':name=parameters['NAME']
        elif keyword=='*ELASTIC':materials[name]=tuple(float(v) for v in rows[0][:2])
        elif keyword=='*SOLID SECTION':sections.append((parameters['ELSET'],parameters['MATERIAL']))
        elif keyword in ('*NODE FILE','*NODE PRINT','*EL FILE','*EL PRINT'):
            outputs.setdefault(keyword,set()).update(v.upper() for row in rows for v in row if v)
    def ids(region,sets):
        return {int(region)} if region.isdigit() else sets[region.upper()]
    for keyword,parameters,rows in parsed:
        if keyword=='*BOUNDARY':
            for row in rows:
                for identifier in ids(row[0],nsets):
                    for dof in range(int(row[1]),int(row[2])+1):
                        key=(identifier,dof)
                        if key in constraints:raise ValueError('Duplicate fixture BC')
                        constraints[key]=float(row[3]) if len(row)>3 else 0.0
        elif keyword=='*CLOAD':
            for row in rows:
                for identifier in ids(row[0],nsets):
                    key=(identifier,int(row[1]))
                    if key in loads:raise ValueError('Duplicate fixture force')
                    loads[key]=float(row[2])
    return {'nodes':nodes,'elements':elements,'materials':materials,'sections':sections,'constraints':constraints,'loads':loads,'outputs':outputs,
            'stepCount':sum(k=='*STEP' for k,_,_ in parsed),'staticCount':sum(k=='*STATIC' for k,_,_ in parsed),'endCount':sum(k=='*END STEP' for k,_,_ in parsed)}


def compare(text,reference_text):
    actual=snapshot(text);expected=snapshot(reference_text)
    for key in ('nodes','elements','materials','sections','constraints','loads','stepCount','staticCount','endCount'):
        if actual[key]!=expected[key]:raise ValueError('Static cube differs from retained reference: '+key)
    for key,variables in expected['outputs'].items():
        if not variables.issubset(actual['outputs'].get(key,set())):raise ValueError('Static cube lost required output: '+key)
    if len(actual['constraints'])!=12 or len(actual['loads'])!=4 or sum(actual['loads'].values())!=100:
        raise ValueError('Independent cube 12-constraint/100 N expectations failed')
    records=cards(text)
    if any('SOLVER' in p or 'NLGEOM' in p or 'PERTURBATION' in p for _,p,_ in records):raise ValueError('Unexpected solver/nonlinear policy')
    static=next(rows for keyword,_,rows in records if keyword=='*STATIC')
    if len(static)!=1 or tuple(float(v) for v in static[0])!=(1,1,1e-5,1):raise ValueError('Explicit original static times differ from configured cube')
    return {'matchesRetainedReference':True,'nodeIdsAndCoordinates':True,'elementIdsAndConnectivity':True,
            'elasticConstantsAndSectionReferences':True,'expandedConstraints':len(actual['constraints']),
            'expandedConcentratedForces':len(actual['loads']),'totalAxialForce':sum(actual['loads'].values()),
            'requiredFieldAndHistoryOutputsPreserved':True,'originalDefaultAdditionalElementFields':sorted(actual['outputs']['*EL FILE']-expected['outputs']['*EL FILE']),
            'explicitStaticTimePeriod':1,'solverExecuted':False}


def rejection_controls(text,reference):
    controls=[]
    for name,changed in [('force per node',text.replace('X1, 1, 25','X1, 1, 100')),
                         ('material modulus',text.replace('210000, 0.3','210001, 0.3')),
                         ('boundary DOF',text.replace('X0, 1, 1, 0','X0, 2, 2, 0')),
                         ('section material',text.replace('Material=ELASTIC','Material=MISSING'))]:
        if changed==text:raise ValueError('Fixture rejection anchor changed: '+name)
        try:compare(changed,reference)
        except (ValueError,KeyError):controls.append(name)
        else:raise ValueError('Fixture verifier accepted mutation: '+name)
    return controls


def verify(run,work,here,root):
    binary=work/'build/bin/StaticDeck/release/PrePoMaxX.StaticDeck.dll'
    mesh=here/'StaticDeck/cube-mesh.inp';definition=here/'StaticDeck/cube-analysis.json';output=work/'analysis.inp'
    command=['dotnet',binary,'build-static',mesh,definition,output]
    inputs={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (mesh,definition)}
    result=json.loads(run(command).stdout)
    if result!={'success':True,'analysisDeck':True,'unitSystem':'mm-N-s-C','nodes':8,'elements':1,'materials':1,'sections':1,'constraints':3,'loads':1,'outputWritten':True,'solverExecuted':False}:
        raise ValueError('Static CLI output differs from known cube')
    text=output.read_text();reference=root/'X/Feasibility/Solver/uniaxial-cube.inp';reference_text=reference.read_text()
    report={'sample':result,'deck':text,'deckSha256':hashlib.sha256(output.read_bytes()).hexdigest(),
            'reference':reference.relative_to(root).as_posix(),'referenceSha256':hashlib.sha256(reference.read_bytes()).hexdigest(),
            'comparison':compare(text,reference_text),'semanticRejectionControls':rejection_controls(text,reference_text),'cliControls':[]}
    initial=hashlib.sha256(output.read_bytes()).hexdigest();spec=json.loads(definition.read_text())
    controls=[('usage',['dotnet',binary],2),('existing output',command,1),
              ('missing mesh',['dotnet',binary,'build-static',work/'absent.inp',definition,work/'bad.inp'],1),
              ('missing definition',['dotnet',binary,'build-static',mesh,work/'absent.json',work/'bad.inp'],1)]
    variants={'malformed':'{','null root':'null','size limit':' '*(2*1024*1024+1),
              'duplicate property':definition.read_text().replace('"schemaVersion": 1','"schemaVersion": 1, "schemaVersion": 1')}
    for name in ['unknown property','unknown units','missing material','missing region','duplicate BC name','free-only BC','bad force vector','invalid increment','invalid output frequency','unsupported step flag']:
        value=copy.deepcopy(spec)
        if name=='unknown property':value['unknown']=1
        elif name=='unknown units':value['unitSystem']='automatic'
        elif name=='missing material':value['sections'][0]['material']='Absent'
        elif name=='missing region':value['step']['loads'][0]['nodeSet']='Absent'
        elif name=='duplicate BC name':value['step']['constraints'][1]['name']=value['step']['constraints'][0]['name']
        elif name=='free-only BC':value['step']['constraints'][0]['displacements']=[None,None,None]
        elif name=='bad force vector':value['step']['loads'][0]['forcePerNode']=['1']
        elif name=='invalid increment':value['step']['initialTimeIncrement']=2
        elif name=='invalid output frequency':value['step']['outputFrequency']=0
        else:value['step']['nlgeom']=True
        variants[name]=json.dumps(value)
    for index,(name,value) in enumerate(variants.items()):
        path=work/('bad-'+str(index)+'.json');path.write_text(value)
        controls.append((name,['dotnet',binary,'build-static',mesh,path,work/'bad.inp'],1))
    for name,content in [('mesh contains model definitions',text),('unsupported formulation',mesh.read_text().replace('TYPE=C3D8','TYPE=DC3D8'))]:
        path=work/(name.replace(' ','-')+'.inp');path.write_text(content)
        controls.append((name,['dotnet',binary,'build-static',path,definition,work/'bad.inp'],1))
    controls.append(('input alias output',['dotnet',binary,'build-static',mesh,definition,mesh],1))
    for name,arguments,code in controls:
        done=run(arguments,code)
        if done.stdout or (code==1 and json.loads(done.stderr).get('success') is not False):raise ValueError('Invalid static CLI success response')
        if (work/'bad.inp').exists() or hashlib.sha256(output.read_bytes()).hexdigest()!=initial:raise ValueError('Invalid static command modified an output')
        report['cliControls'].append(name)
    report['inputHashesUnchanged']=all(hashlib.sha256((root/p).read_bytes()).hexdigest()==h for p,h in inputs.items())
    if not report['inputHashesUnchanged']:raise ValueError('Static CLI changed an input')
    folder=work/'space Ω';folder.mkdir();new_mesh=folder/'cube mesh.inp';new_spec=folder/'analysis definition.json';new_output=folder/'new deck.inp'
    new_mesh.write_bytes(mesh.read_bytes());new_spec.write_bytes(definition.read_bytes())
    run(['dotnet',binary,'build-static',new_mesh,new_spec,new_output]);compare(new_output.read_text(),reference_text)
    report['spaceAndUnicodePaths']=True
    return report

"""Analytical test inputs for the original C3D10 deck/CalculiX/FRD path.

This module only prepares verification fixtures. It is not a product engineering
kernel, mesh parser, load converter or quality certification.
"""
import json
from pathlib import Path


def definition(sections, constraints, loads=(), histories=()):
    return {'schemaVersion': 1, 'unitSystem': 'mm-N-s-C',
        'materials': [{'name': 'ELASTIC', 'youngsModulus': '1000', 'poissonsRatio': '0'}],
        'sections': [{'name': 'Section_'+str(i), 'material': 'ELASTIC', 'elementSet': name}
                     for i, name in enumerate(sections)],
        'step': {'name': 'Static-1', 'timePeriod': 1, 'initialTimeIncrement': 1,
                 'minimumTimeIncrement': 1e-5, 'maximumTimeIncrement': 1,
                 'maximumIncrements': 100, 'outputFrequency': 1,
                 'constraints': list(constraints), 'loads': list(loads),
                 'nodalHistorySets': list(histories), 'elementHistorySets': []}}


def force_fixture():
    # Unit tetrahedron. Uniform sigma_zz=1 gives a z force of 1/6 on
    # each midside of the sloping face, zero on its corner nodes.
    # All Ux/Uy and bottom Uz are constrained; four Uz remain unknown.
    mesh = '''*Node
1,0,0,0
2,1,0,0
3,0,1,0
4,0,0,1
5,.5,0,0
6,.5,.5,0
7,0,.5,0
8,0,0,.5
9,.5,0,.5
10,0,.5,.5
*Element, Type=C3D10, Elset=SOLID
17,1,2,3,4,5,6,7,8,9,10
*Nset,Nset=ALL
1,2,3,4,5,6,7,8,9,10
*Nset,Nset=BOTTOM
1,2,3,5,6,7
*Nset,Nset=TRACTION
6,9,10
'''
    spec = definition(['SOLID'], [
        {'name': 'Lateral', 'nodeSet': 'ALL', 'displacements': ['0', '0', None]},
        {'name': 'Bottom', 'nodeSet': 'BOTTOM', 'displacements': [None, None, '0']}],
        [{'name': 'Traction', 'nodeSet': 'TRACTION', 'forcePerNode': ['0','0','=1/6']}], ['ALL'])
    return mesh.encode(), spec


def boundary_fixture(mesh_bytes, scene):
    # Manufactured affine solution on the true quadratic boundary. Boundary
    # DOFs are prescribed; every interior DOF is solved by native CalculiX.
    faces = [(0,1,2,4,5,6), (0,1,3,4,8,7), (1,2,3,5,9,8), (0,2,3,6,9,7)]
    counts = {}
    edges = [(0,1),(1,2),(2,0),(0,3),(1,3),(2,3)]
    curved = 0
    nodes = {n['id']: n for n in scene['nodes']}
    for e in scene['elements']:
        assert e['vtkCellType'] == 24 and len(e['nodeIds']) == 10
        ids = e['nodeIds']
        for face in faces:
            key = tuple(sorted(ids[i] for i in face))
            counts[key] = counts.get(key, 0)+1
        for i, (a,b) in enumerate(edges):
            mid, a, b = nodes[ids[4+i]], nodes[ids[a]], nodes[ids[b]]
            curved += any(abs(mid[k]-(a[k]+b[k])/2)>1e-8 for k in ('x','y','z'))
    boundary = {n for face, count in counts.items() if count == 1 for n in face}
    groups = {}
    for n in sorted(boundary):
        groups.setdefault(nodes[n]['z'], []).append(n)
    text = mesh_bytes.decode()+'\n'
    constraints = []
    for i, (z, ids) in enumerate(sorted(groups.items())):
        name = 'AFFINE_'+str(i)
        text += '*Nset, Nset='+name+'\n'
        text += '\n'.join(','.join(map(str, ids[j:j+8])) for j in range(0,len(ids),8))+'\n'
        constraints.append({'name': name, 'nodeSet': name, 'displacements': ['0','0',format(.001*z,'.17g')]})
    sections = [s['name'] for s in scene['elementSets']]
    return text.encode(), definition(sections,constraints), {
        'boundaryNodes': len(boundary), 'interiorNodes': len(nodes)-len(boundary),
        'curvedEdgeIncidences': curved, 'boundaryGroups': len(groups)}


def field_errors(scene):
    nodes = {n['id']: n for n in scene['nodes']}
    fields = {f['name']: f['components'] for f in scene['fields']}
    disp, stress = fields['DISP'], fields['STRESS']
    return {'displacement': max(abs(disp['U3'][i]-.001*nodes[n]['z']) for i,n in enumerate(scene['nodeIdsInValueOrder'])),
        'lateral': max(abs(v) for key in ('U1','U2') for v in disp[key]),
        'axialStress': max(abs(v-1) for v in stress['S33']),
        'otherStress': max(abs(v) for key in ('S11','S22','S12','S23','S13') for v in stress[key]),
        'forceResultant': {key: sum(value) for key,value in fields['FORC'].items() if key in ('F1','F2','F3')}}

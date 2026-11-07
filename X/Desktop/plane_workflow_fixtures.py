"""Independent rectangular patches; verification fixtures, not a product mesher."""
import json

FAMILIES = {'plane-stress': ('PlaneStress', 'CPS'), 'plane-strain': ('PlaneStrain', 'CPE'),
            'axisymmetric': ('Axisymmetric', 'CAX')}
SUFFIXES = ('3', '6', '4', '4R', '8', '8R')


def build_fixture(case, suffixes=SUFFIXES):
    space, prefix = FAMILIES[case]
    nodes, lookup, blocks = {}, {}, []
    left, bottom, top = [], [], []
    def node(x, y):
        key = (x, y)
        if key not in lookup:
            identity = 11 + 3 * len(nodes)
            lookup[key] = identity
            nodes[identity] = key
        return lookup[key]
    eid = 101
    for part, suffix in enumerate(suffixes):
        origin = 1 + 2 * part if space == 'Axisymmetric' else 2 * part
        elements = []
        for j in range(4):
            for i in range(2):
                corners = [(origin+i/2, j/4), (origin+(i+1)/2, j/4),
                           (origin+(i+1)/2, (j+1)/4), (origin+i/2, (j+1)/4)]
                patches = [[corners[k] for k in ids] for ids in ((0, 1, 2), (0, 2, 3))] if suffix in ('3', '6') else [corners]
                for patch in patches:
                    coords = list(patch)
                    if suffix in ('6', '8', '8R'):
                        coords += [((a[0]+b[0])/2, (a[1]+b[1])/2) for a, b in zip(patch, patch[1:]+patch[:1])]
                    elements.append((eid, [node(x, y) for x, y in coords]))
                    eid += 7
        blocks.append((f'PATCH_{part+1}', prefix+suffix, elements, origin))
        ids = {n for _, conn in elements for n in conn}
        left += [n for n in ids if nodes[n][0] == origin]
        bottom += [n for n in ids if nodes[n][1] == 0]
        top += [n for n in ids if nodes[n][1] == 1]
    rows = ['*Node'] + [f'{n}, {x:.17g}, {y:.17g}' for n, (x, y) in nodes.items()]
    for name, form, elements, _ in blocks:
        rows.append(f'*Element, Type={form}, Elset={name}')
        rows += [', '.join(map(str, [eid, *conn])) for eid, conn in elements]
    for name, ids in [('ALL', list(nodes)), ('LEFT', left), ('BOTTOM', bottom), ('TOP', top)]:
        rows.append('*Nset, Nset='+name)
        rows += [', '.join(map(str, ids[i:i+8])) for i in range(0, len(ids), 8)]
    sections = [{'name': 'Section_'+name, 'material': 'ELASTIC', 'elementSet': name,
                 **({'thickness': '2'} if space != 'Axisymmetric' else {})} for name, _, _, _ in blocks]
    supports = [{'name': 'Bottom', 'nodeSet': 'BOTTOM', 'displacements': [None, '0', None]}]
    if space != 'Axisymmetric':
        supports.append({'name': 'Left', 'nodeSet': 'LEFT', 'displacements': ['0', None, None]})
    spec = {'schemaVersion': 1, 'unitSystem': 'mm-N-s-C', 'modelSpace': space,
            'materials': [{'name': 'ELASTIC', 'youngsModulus': '1000', 'poissonsRatio': '0.25'}], 'sections': sections,
            'step': {'name': 'Static-1', 'timePeriod': 1, 'initialTimeIncrement': 1, 'minimumTimeIncrement': 1e-5,
                     'maximumTimeIncrement': 1, 'maximumIncrements': 100, 'outputFrequency': 1,
                     'constraints': supports, 'loads': [], 'pressures': [{'name': 'Tension', 'nodeSet': 'TOP', 'magnitude': '-1'}],
                     'nodalHistorySets': ['BOTTOM', 'TOP'], 'elementHistorySets': []}}
    return ('\n'.join(rows)+'\n').encode(), spec


def write_examples(folder):
    for case in FAMILIES:
        mesh, spec = build_fixture(case)
        (folder/(case+'.inp')).write_bytes(mesh)
        (folder/(case+'.json')).write_text(json.dumps(spec, indent=2)+'\n')
    mesh, spec = build_cylinder()
    (folder/'axisymmetric-cylinder.inp').write_bytes(mesh)
    (folder/'axisymmetric-cylinder.json').write_text(json.dumps(spec, indent=2)+'\n')


def build_cylinder():
    """Open-ended thick cylinder: nonzero radial and hoop stress, free axial contraction."""
    nodes, lookup, elements = {}, {}, []
    def node(x, y):
        if (x, y) not in lookup:
            identity = 11 + 3 * len(nodes)
            lookup[(x, y)] = identity
            nodes[identity] = (x, y)
        return lookup[(x, y)]
    for j in range(4):
        for i in range(32):
            corners = [(1+i/32, j/4), (1+(i+1)/32, j/4), (1+(i+1)/32, (j+1)/4), (1+i/32, (j+1)/4)]
            coords = corners + [((a[0]+b[0])/2, (a[1]+b[1])/2) for a, b in zip(corners, corners[1:]+corners[:1])]
            elements.append((101+7*len(elements), [node(x, y) for x, y in coords]))
    rows = ['*Node'] + [f'{n}, {x:.17g}, {y:.17g}' for n, (x, y) in nodes.items()]
    rows += ['*Element, Type=CAX8R, Elset=CYLINDER']
    rows += [', '.join(map(str, [eid, *conn])) for eid, conn in elements]
    for name, ids in [('BOTTOM', [n for n, (_, y) in nodes.items() if y == 0]),
                      ('INNER', [n for n, (x, _) in nodes.items() if x == 1])]:
        rows.append('*Nset, Nset='+name)
        rows += [', '.join(map(str, ids[i:i+8])) for i in range(0, len(ids), 8)]
    _, spec = build_fixture('axisymmetric', ('8R',))
    spec['sections'] = [{'name': 'Cylinder', 'material': 'ELASTIC', 'elementSet': 'CYLINDER'}]
    spec['step']['pressures'] = [{'name': 'Internal-pressure', 'nodeSet': 'INNER', 'magnitude': '1'}]
    spec['step']['nodalHistorySets'] = ['INNER']
    return ('\n'.join(rows)+'\n').encode(), spec


if __name__ == '__main__':
    from pathlib import Path
    write_examples(Path(__file__).resolve().parents[1]/'Analysis/StaticDeck')

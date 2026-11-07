#!/usr/bin/env python3
"""Checked original PMX family projection; never deserializes executable types."""
import hashlib
import json
from pathlib import Path
from runpy import run_path
import tempfile
HERE=Path(__file__).resolve().parent
reader=run_path(str(HERE/'inspect-static-project.py'))

def inspect(path,mesh_decoder,graph_decoder):
    with Path(path).open('rb') as stream:framing,graph,model=reader['read_frames'](stream)
    if framing['header']!='PrePoMax v3.0.0':raise ValueError('Family exchange requires original PMX 3.0.0.')
    tail=framing['opaqueTail']
    if tail['bytes']!=4 or tail['sha256']!=hashlib.sha256(bytes(4)).hexdigest():raise ValueError('Family analysis projection currently requires a result-free PMX; original files are preserved.')
    with tempfile.TemporaryDirectory(prefix='prepomaxx-family-pmx-') as name:
        work=Path(name);(work/'graph.nrbf').write_bytes(graph);(work/'model.bin').write_bytes(model)
        mesh=reader['decode'](mesh_decoder,['--family-mesh',work/'model.bin'])
        definition=reader['decode'](graph_decoder,['--family-graph',work/'graph.nrbf'])
    parts={p['id']:p for p in definition['parts']}
    if len(parts)!=len(definition['parts']) or {p['name'] for p in parts.values()}!=set(mesh['partNames']):raise ValueError('Original graph and mesh parts differ.')
    nodes={n['id'] for n in mesh['nodes']};elements={e['id']:e for e in mesh['elements']}
    for sets,known in [(definition['nodeSets'],nodes),(definition['elementSets'],elements.keys())]:
        if any(not set(ids)<=known for ids in sets.values()):raise ValueError('PMX named set refers to missing IDs.')
    assigned=set()
    for part in parts.values():
        ids=part['elements']
        if not ids or assigned.intersection(ids) or not set(ids)<=elements.keys():raise ValueError('Invalid or overlapping PMX part membership.')
        used=set()
        for identity in ids:
            e=elements[identity]
            if e['partId']!=part['id']:raise ValueError('PMX part identity differs between graph and mesh.')
            e['type']=part['formulations'].get(str(e['vtkCellType']))
            if e['type'] is None:raise ValueError('PMX part has no formulation for its element topology.')
            used.update(e['connectivity'])
        if used!=set(part['nodes']):raise ValueError('PMX part node membership differs from connectivity.')
        assigned.update(ids)
    if assigned!=elements.keys():raise ValueError('PMX mesh has elements outside its graph parts.')
    lines=['*Node']
    for n in mesh['nodes']:lines.append(', '.join([str(n['id']),*(format(v,'.17g') for v in n['coordinates'])]))
    for p in parts.values():
        for form in dict.fromkeys(elements[i]['type'] for i in p['elements']):
            lines.append('*Element,Type='+form)
            for i in p['elements']:
                e=elements[i]
                if e['type']==form:lines.append(', '.join(map(str,[e['id'],*e['connectivity']])))
    for keyword,sets in [('Nset',definition['nodeSets']),('Elset',definition['elementSets'])]:
        for name,ids in sets.items():
            if not ids:raise ValueError('Empty named PMX sets require full project support.')
            lines.append('*'+keyword+','+keyword+'='+name)
            for i in range(0,len(ids),8):lines.append(', '.join(map(str,ids[i:i+8])))
    return {'inputSha256':framing['inputSha256'],'mesh':mesh,'graph':definition,'meshText':'\n'.join(lines)+'\n','analysis':definition['analysis'],'originalGraphSha256':hashlib.sha256(graph).hexdigest(),'originalModelSha256':hashlib.sha256(model).hexdigest(),'newNativeSessionPersistence':False}

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('input','mesh_decoder','graph_decoder'):parser.add_argument(name,type=Path)
    args=parser.parse_args()
    try:print(json.dumps(inspect(args.input,args.mesh_decoder,args.graph_decoder)))
    except (OSError,ValueError) as error:parser.exit(1,str(error)+'\n')

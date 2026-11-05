#!/usr/bin/env python3
"""Real native CAD/first-order mesh/static solver/FRD probe, without Qt or defaults."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from cad_import import NativeCadTool
from cad_document import CadDocument, CadMesh


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('runtime', 'mesh', 'cad', 'solve', 'results', 'registry', 'solver_bin', 'source', 'analysis', 'output'):
        parser.add_argument('--' + name.replace('_', '-'), required=True, type=Path)
    parser.add_argument('--solver-id', required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    report = {'success': False, 'checks': []}
    document = mesh = None

    def check(name, condition):
        report['checks'].append({'name': name, 'passed': bool(condition)})
        if not condition:
            raise ValueError(name)

    def reader(command, *, cancel=None):
        done = subprocess.run(command, capture_output=True, timeout=90)
        if done.returncode:
            raise ValueError(done.stderr.decode(errors='replace')[-4000:])
        result = json.loads(done.stdout)
        if not result.get('success'):
            raise ValueError(str(result))
        return result

    try:
        tool = NativeCadTool(args.runtime)
        decoder = lambda path, **kw: reader(['dotnet', str(args.cad), 'scene', str(path)], **kw)
        document = CadDocument(args.source, tool, decoder)
        mesh = CadMesh(document, ['dotnet', str(args.mesh)], reader, 3)
        identity = mesh.freeze(args.output / 'cad')
        mesh_path = args.output / 'mesh.inp'
        mesh_path.write_bytes(mesh.mesh_bytes)
        report['mesh'] = mesh.scene
        check('two native parts merged without fusing nodes', len(mesh.scene['cadMesh']['parts']) == 2)
        check('original linear tetrahedral cells', all(e['vtkCellType'] == 10 for e in mesh.scene['elements']))
        outcome = reader(['dotnet', str(args.solve), '--registry', str(args.registry), 'run-static', args.solver_id,
                          str(args.solver_bin), str(mesh_path), str(args.analysis), str(args.output / 'solve'), '60'])
        report['outcome'] = outcome
        check('native solver executed and completed', outcome['success'] and outcome['solverExecuted'])
        result = reader(['dotnet', str(args.results), 'inspect-frd', str(args.output / 'solve/analysis.frd')])
        (args.output / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
        nodes = {n['id']: n for n in result['nodes']}
        fields = {f['name']: f['components'] for f in result['fields']}
        report['maximumDisplacementError'] = max(abs(fields['DISP']['U3'][i] - .001 * nodes[n]['z'])
                                                for i, n in enumerate(result['nodeIdsInValueOrder']))
        check('original FRD preserves all tetrahedra', len(result['elements']) == len(mesh.scene['elements']) and
              all(e['vtkCellType'] == 10 for e in result['elements']))
        check('analytical displacement at every node', report['maximumDisplacementError'] <= 2e-8 and
              max(map(abs, fields['DISP']['U1'])) <= 1e-12 and max(map(abs, fields['DISP']['U2'])) <= 1e-12)
        check('analytical unit axial stress at every node', max(abs(v-1) for v in fields['STRESS']['S33']) <= 1e-6)
        check('frozen CAD and meshing bytes match', all(hashlib.sha256((args.output / 'cad' / f['file']).read_bytes()).hexdigest() == f['sha256'] for f in identity['files']))
        report['success'] = True
    except Exception as error:
        report['error'] = str(error)
    finally:
        if mesh:
            mesh.close()
        if document:
            document.close()
        (args.output / 'workflow.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'success': report['success'], 'checks': len(report['checks']), 'error': report.get('error')}))
    return 0 if report['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

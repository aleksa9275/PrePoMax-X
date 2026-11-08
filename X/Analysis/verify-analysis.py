#!/usr/bin/env python3
"""Verify the original static-deck superset, pinned dependencies and CLIs."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
import static_deck_checks

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(data): return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream-revision', choices=['3.0.0-rc2', 'post-rc2-2026-10-17'])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expect-os', choices=['Darwin', 'Linux', 'Windows'])
    parser.add_argument('--expect-architecture', choices=['Arm64', 'X64'])
    parser.add_argument('--package-cache', type=Path, default=HERE / 'artifacts/packages')
    args = parser.parse_args()
    report = {'success': False, 'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
              'host': {'os': platform.system(), 'architecture': platform.machine()}, 'commands': []}
    temporary = None
    def clean(value):
        return value.replace(str(ROOT), '<repository>').replace(temporary or '<unused>', '<temporary>')
    try:
        arch = {'arm64':'Arm64','aarch64':'Arm64','amd64':'X64','x86_64':'X64'}.get(platform.machine().lower())
        if (args.expect_os and args.expect_os != platform.system()) or (args.expect_architecture and args.expect_architecture != arch):
            raise ValueError('Unexpected native verification host')
        if args.upstream_revision:
            raise ValueError('Historical upstream slice replays were retired with the whole-library build (D062)')
        sources = subprocess.run([sys.executable, str(ROOT/'X/Domain/domain_sources.py'), '--check'], cwd=ROOT,
                                 capture_output=True, text=True)
        if sources.returncode != 0: raise ValueError('Whole-library source lists are stale: '+sources.stdout.strip())
        report['sources'] = {'mode':'whole original assemblies (X/Domain)',
                             'manifestSha256':sha((ROOT/'X/Domain/domain-sources.json').read_bytes())}
        report['upstreamRevision'] = 'current'
        report['repository'] = {'head': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
                                'dirty': bool(subprocess.check_output(['git','status','--porcelain'], cwd=ROOT))}
        report['toolHashes'] = {p.relative_to(HERE).as_posix():sha(p.read_bytes()) for p in sorted(HERE.rglob('*')) if p.is_file() and not {'artifacts','bin','obj','__pycache__'}.intersection(p.relative_to(HERE).parts)}
        external_tools = ['X/Core/Tests/Program.cs','X/Feasibility/Data/Program.cs','X/Core/Tests/Data/TypeContracts.cs',
            'X/Core/Tests/Elements/Program.cs','X/Core/Tests/MeshDeck/Program.cs','X/Core/MeasureMesh/Program.cs',
            'X/Core/MeshDeck/Program.cs','X/Core/MeshDeck/unit-cube.inp','CaeMesh/Meshing/Transfinite/Cpp/three_block_vectors.txt']
        report['sharedRegressionToolHashes'] = {p:sha((ROOT/p).read_bytes()) for p in external_tools}
        with tempfile.TemporaryDirectory(prefix='prepomaxx-analysis-') as temporary:
            work = Path(temporary)
            def run(command, expected=0):
                done = subprocess.run(list(map(str,command)), cwd=ROOT, capture_output=True, text=True, timeout=180)
                report['commands'].append({'arguments':[clean(str(a)) for a in command], 'exitCode':done.returncode,
                                           'stdout':clean(done.stdout), 'stderr':clean(done.stderr)})
                if done.returncode != expected: raise ValueError('Analysis command failed; see retained command output')
                return done
            report['sdk'] = run(['dotnet','--version']).stdout.strip()
            run(['dotnet','build',HERE/'PrePoMaxX.Analysis.slnx','-c','Release','--disable-build-servers','-m:1',
                 '--artifacts-path',work/'build','-v:minimal'])
            # Package closure of the whole original assemblies, as locked by their projects.
            report['dependencies'] = {name: json.loads((ROOT/'X/Domain'/name/'packages.lock.json').read_text())['dependencies']['net10.0']
                                      for name in ('CaeGlobals','CaeResults')}
            post = False
            test_command=['dotnet',work/'build/bin/Tests/release/PrePoMaxX.Tests.dll']+(['--post-rc2'] if post else [])
            tests=json.loads(run(test_command).stdout)
            report['tests']=tests
            if not tests['success'] or tests['passed'] != 58 or tests['failed']: raise ValueError('Analysis tests incomplete or failed')
            report['regression'] = {}
            for project, assembly, expected_count, arguments in [('Mapping','CoreTests',25,[]),('Data','CoreDataTests',30,['--self-test']),('Elements','ElementTests',95,[]),('Mesh','MeshDeckTests',69,[])]:
                result = json.loads(run(['dotnet',work/'build/bin'/project/'release'/('PrePoMaxX.'+assembly+'.dll'),*arguments]).stdout)
                if not result['success'] or result['passed'] != expected_count or result['failed'] or result['runtime']['architecture'] != arch:
                    raise ValueError('Expanded-assembly original regression failed: '+project)
                report['regression'][project] = result
            element = report['regression']['Elements']
            if element['fullyAccepted'] or len(element['openCorrectnessChecks']) != 2 or any(c['passed'] for c in element['openCorrectnessChecks']):
                raise ValueError('Existing correctness failures must remain explicit')
            reference = json.loads((ROOT/'.project/reports/windows-reference/data-windows-x64.json').read_text())
            data = report['regression']['Data']
            if data['checks'] != reference['tests']['checks'] or data['observations'] != reference['tests']['observations']:
                raise ValueError('Expanded-assembly data differs from recorded native Windows observations')
            report['staticTests']=json.loads(run(['dotnet',work/'build/bin/StaticChecks/release/PrePoMaxX.StaticChecks.dll']).stdout)
            if not report['staticTests']['success'] or report['staticTests']['passed']!=74 or report['staticTests']['failed']:
                raise ValueError('Static-deck tests incomplete or failed')
            report['staticWorkflow']=static_deck_checks.verify(run,work,HERE,ROOT)
            cli=work/'build/bin/MaterialDeck/release/PrePoMaxX.MaterialDeck.dll'
            output=work/'steel.inp'
            command=['dotnet',cli,'write-isotropic','Steel','210 GPa','0.3',output,'--pressure-unit','MPa']
            result=json.loads(run(command).stdout)
            expected_text='*Material, Name=Steel\n*Elastic\n210000, 0.3\n'
            if output.read_text() != expected_text or result != {'success':True,'materialOnly':True,'pressureUnit':'MPa','youngsModulus':210000,'poissonsRatio':0.3,'outputWritten':True}: raise ValueError('CLI differs from independent material keyword expectations')
            report['cli']={'sample':result,'fragment':output.read_text(),'controls':[]}
            digest=sha(output.read_bytes())
            controls=[('existing output',command,1),('usage',['dotnet',cli],2)]
            for name,updates,code in [('zero modulus',{4:'0'},1),('unstable Poisson ratio',{5:'.5'},1),('invalid equation',{4:'=missing+1'},1),('input length',{4:'1'*4097},1),('unsupported unit',{8:'psi'},2),('invalid name',{3:'Steel Name'},1)]:
                changed=list(command);changed[6]=work/'invalid.inp'
                for i,v in updates.items():changed[i]=v
                controls.append((name,changed,code))
            for name,command,code in controls:
                done=run(command,code)
                if done.stdout or (code==1 and json.loads(done.stderr)['success']):raise ValueError('Invalid CLI success output')
                if (work/'invalid.inp').exists() or sha(output.read_bytes()) != digest:raise ValueError('Rejected CLI modified output')
                report['cli']['controls'].append(name)
            report['limits']=['Bounded full C3D8 static deck and material fragment; no solver execution or desktop installer',
                'NCalc 1.3.8 NU1701 compatibility warning retained; broader Windows/full-equation acceptance pending',
                'Whole original assemblies (X/Domain) keep original identities; never mix these DLLs with an original application',
                'Two earlier correctness failures and quadratic-tetra measurement gate remain unchanged']
            report['success']=True
    except (OSError,ValueError,KeyError,TypeError,RuntimeError,subprocess.SubprocessError) as error:
        report['error']=clean(str(error))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'success':report['success'],'tests':report.get('tests',{}).get('passed'),'staticChecks':report.get('staticTests',{}).get('passed'),'error':report.get('error')}))
    return 0 if report['success'] else 1


if __name__=='__main__': raise SystemExit(main())

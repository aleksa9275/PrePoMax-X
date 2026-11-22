#!/usr/bin/env python3
"""Focused whole-Controller build, persistence and original workflow checks."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--expect-os');p.add_argument('--expect-architecture')
    p.add_argument('--python-profile',type=Path)
    p.add_argument('--three-mf-library',type=Path)
    p.add_argument('--netgen',type=Path);p.add_argument('--gmsh-library',type=Path);p.add_argument('--cad-fixture',type=Path)
    p.add_argument('--solver-registry',type=Path);p.add_argument('--solver-id');p.add_argument('--solver-directory',type=Path)
    p.add_argument('--feed',type=Path)
    args=p.parse_args();output=args.output.resolve();folder=output.with_suffix('');folder.mkdir(parents=True,exist_ok=True)
    arch={'arm64':'Arm64','aarch64':'Arm64','x86_64':'X64','amd64':'X64'}.get(platform.machine().lower())
    report={'success':False,'recordedAtUtc':datetime.now(timezone.utc).isoformat(),'host':{'os':platform.system(),'architecture':arch},'steps':[],'pending':[]}
    env={**os.environ,'PREPOMAXX_PHASE_B_OUTPUT':str(folder/'session')}
    def run(name,command,extra=None):
        started=time.monotonic();done=subprocess.run([str(x) for x in command],cwd=ROOT,env={**env,**(extra or {})},capture_output=True,text=True,timeout=900)
        stdout=folder/(name+'.stdout.log');stderr=folder/(name+'.stderr.log');stdout.write_text(done.stdout);stderr.write_text(done.stderr)
        report['steps'].append({'name':name,'arguments':list(map(str,command)),'passed':done.returncode==0,'exitCode':done.returncode,'seconds':round(time.monotonic()-started,3),'stdout':str(stdout),'stdoutSha256':sha(stdout),'stderr':str(stderr),'stderrSha256':sha(stderr)})
        if done.returncode:raise RuntimeError(name+' failed; see '+str(stdout))
        return done.stdout
    try:
        if (args.expect_os and args.expect_os!=platform.system()) or (args.expect_architecture and args.expect_architecture!=arch):raise ValueError('Unexpected native host')
        run('source-lists',[sys.executable,ROOT/'X/Domain/domain_sources.py','--check'])
        ns={'m':'http://schemas.microsoft.com/developer/msbuild/2003'}
        original={e.get('Include').replace('\\','/') for e in ET.parse(ROOT/'PrePoMax/PrePoMax.csproj').findall('.//m:Compile',ns)}
        selected=set(json.loads((ROOT/'X/Domain/domain-sources.json').read_text())['assemblies']['PrePoMax']['include'])
        commands={s for s in original if s.startswith('Commands/')}
        if not commands<=selected:raise ValueError('Original command sources omitted: '+str(sorted(commands-selected)))
        report['commandSourceFiles']=len(commands)
        artifacts=folder/'build'
        build=['dotnet','build',HERE/'PrePoMaxX.Controller.slnx','-c','Release','--disable-build-servers','-m:1','-p:UseSharedCompilation=false','--artifacts-path',artifacts,'-v:minimal','-p:NativePreviewLockRoot='+str(folder/'locks')]
        if args.feed:build.append('-p:RestoreSources='+str(args.feed.resolve()))
        run('build',build)
        binary=lambda project,name:artifacts/'bin'/project/'release'/name
        runner=binary('Runner','Runner.dll')
        run('host-contract',['dotnet',binary('SourceGen','SourceGen.dll'),ROOT,'--check'])
        checks=run('persistence',['dotnet',runner,'--persistence'])
        report['persistence']=json.loads(next(line for line in checks.splitlines() if line.startswith('{')))
        run('solid-workflow',['dotnet',runner,'--workflow',ROOT/'.project/reports/windows-reference/fixtures/definitions.inp',folder/'solid'])
        run('fresh-process',['dotnet',runner,'--open',folder/'solid/project.pmx'])
        if args.python_profile:
            run('embedded-python',['dotnet',runner,'--python',args.python_profile.resolve()])
            run('spatial-replay',['dotnet',runner,'--spatial',args.python_profile.resolve()])
            # Scripts through the original command line run on X/App (X/App/verify-app.py, upstream's Run_Tests.py)
        else:report['pending'].append('Embedded Python/native spatial replay: no explicit profile supplied')
        if args.three_mf_library and args.python_profile:
            library=args.three_mf_library.resolve()
            manifest=folder/'exports.json'
            manifest.write_text(json.dumps({'schemaVersion':1,'tools':{'lib3mf.dll':{'path':str(library),'sha256':sha(library)}}},indent=2)+'\n')
            run('native-exports',['dotnet',runner,'--exports',manifest,args.python_profile.resolve()])
            # Decode the controlled PNG independently of its writer. Top rows are
            # blue, bottom rows red, with the original vertical texture mapping.
            import struct,zlib
            png=(folder/'session/texture.png').read_bytes();offset=8;compressed=b''
            while offset<len(png):
                size=struct.unpack('>I',png[offset:offset+4])[0];kind=png[offset+4:offset+8];data=png[offset+8:offset+8+size]
                if zlib.crc32(kind+data)!=struct.unpack('>I',png[offset+8+size:offset+12+size])[0]:raise ValueError('PNG checksum mismatch')
                if kind==b'IDAT':compressed+=data
                offset+=size+12
            expected=(b'\x00'+bytes([0,0,255,255])*2)*2+(b'\x00'+bytes([255,0,0,255])*2)*2
            if zlib.decompress(compressed)!=expected:raise ValueError('Texture pixel mapping differs')
        else:report['pending'].append('Native 3MF/surface exports: explicit lib3mf/Python profiles not supplied')
        if args.solver_registry and args.solver_id and args.solver_directory:
            run('solver-results',['dotnet',runner,'--solve',args.solver_registry.resolve(),args.solver_id,args.solver_directory.resolve(),folder/'solve'])
        else:report['pending'].append('Original Controller native solve/results: no explicit solver profile supplied')
        if args.netgen and args.gmsh_library and args.cad_fixture:
            caller=binary('GmshCaller','GmshCaller'+('.exe' if os.name=='nt' else ''))
            tools={key:{'path':str(path),'sha256':sha(path)} for key,path in [('\\Meshers\\Netgen\\NetGenMesher.exe',args.netgen.resolve()),('\\lib\\GmshCaller.exe',caller)]}
            manifest=folder/'tools.json';manifest.write_text(json.dumps({'schemaVersion':1,'tools':tools},indent=2)+'\n')
            run('cad-gmsh',['dotnet',runner,'--mesh',manifest,folder/'mesh',args.cad_fixture.resolve()],{'PREPOMAXX_GMSH_LIBRARY':str(args.gmsh_library.resolve())})
        else:report['pending'].append('Original Controller CAD/Gmsh: explicit native profile/fixture not supplied')
        report['success']=True
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:report['error']=str(error)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'success':report['success'],'steps':len(report['steps']),'pending':report['pending'],'error':report.get('error')}))
    return 0 if report['success'] else 1
if __name__=='__main__':raise SystemExit(main())

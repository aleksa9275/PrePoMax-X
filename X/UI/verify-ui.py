#!/usr/bin/env python3
"""Focused C1 build, original-property workflow and optional real-display GUI check."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--output',required=True,type=Path)
p.add_argument('--expect-os')
p.add_argument('--expect-architecture')
p.add_argument('--python-profile',type=Path)
p.add_argument('--feed',type=Path)
p.add_argument('--gui',action='store_true',help='Requires a display (Xvfb is supplemental Linux evidence)')
a=p.parse_args()
out=a.output.resolve()
folder=out.with_suffix('')
folder.mkdir(parents=True,exist_ok=True)
host={'os':platform.system(),'architecture':{'arm64':'Arm64','aarch64':'Arm64','x86_64':'X64','amd64':'X64'}.get(platform.machine().lower())}
report={'success':False,'recordedAtUtc':datetime.now(timezone.utc).isoformat(),'host':host,'steps':[],'pending':[]}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(name,command):
    result=subprocess.run(list(map(str,command)),cwd=ROOT,capture_output=True,text=True,timeout=300)
    log=folder/(name+'.log')
    log.write_text(result.stdout+'\n'+result.stderr)
    report['steps'].append({'name':name,'exitCode':result.returncode,'log':str(log),'sha256':sha(log),'command':list(map(str,command))})
    if result.returncode:raise RuntimeError(name+' failed: '+str(log))
try:
    if (a.expect_os and a.expect_os!=host['os']) or (a.expect_architecture and a.expect_architecture!=host['architecture']):raise ValueError('Unexpected host')
    if a.gui and not a.python_profile:raise ValueError('--gui requires --python-profile')
    for source in HERE.glob('*.py'):ast.parse(source.read_text(),str(source))
    run('sources',[sys.executable,ROOT/'X/Domain/domain_sources.py','--check'])
    build=['dotnet','build',HERE/'Workbench/Workbench.csproj','-c','Release','--disable-build-servers','-m:1',
           '-p:UseSharedCompilation=false','--artifacts-path',folder/'build','-p:NativePreviewLockRoot='+str(folder/'locks'),'-v:q']
    if a.feed:build += ['-p:RestoreSources='+str(a.feed.resolve())]
    extractor_build=build.copy()
    extractor_build[2]=HERE/'FormSourceGen/FormSourceGen.csproj'
    run('form-extractor-build',extractor_build)
    run('original-forms',[sys.executable,HERE/'generate-forms.py','--check','--extractor',folder/'build/bin/FormSourceGen/release/FormSourceGen.dll'])
    run('build',build)
    binary=folder/'build/bin/Workbench/release/PrePoMaxX.Workbench.dll'
    if a.python_profile:
        base=['dotnet',binary,a.python_profile.resolve(),folder/'session',HERE/'workbench.py']
        run('service',base+['--service-probe',folder/'service'])
        result=json.loads((folder/'service/service.json').read_text())
        if not result.get('success'):raise ValueError('Service workflow failed')
        report['service']=result
        run('authoring-service',base+['--authoring-service-probe',folder/'authoring/service'])
        result=json.loads((folder/'authoring/service/authoring.json').read_text())
        if not result.get('success'):raise ValueError('C2 authoring workflow failed')
        report['authoringService']=result
        if a.gui:
            run('gui',base+['--probe',folder/'gui'])
            result=json.loads((folder/'gui/gui.json').read_text())
            if not result.get('success'):raise ValueError('GUI workflow failed: '+str(result))
            report['gui']=result
            run('authoring-gui',base+['--authoring-probe',folder/'authoring/gui'])
            result=json.loads((folder/'authoring/gui/authoring-gui.json').read_text())
            if not result.get('success'):raise ValueError('C2 GUI workflow failed: '+str(result))
            report['authoringGui']=result
        else:report['pending'].append('GUI workflow not executed: --gui not supplied')
    else:report['pending'].append('Property/native UI workflow not executed: no explicit CPython profile')
    report['success']=True
except Exception as error:report['error']=str(error)
finally:
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'success':report['success'],'output':str(out),'pending':report['pending']}))
raise SystemExit(0 if report['success'] else 1)

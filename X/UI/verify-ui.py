#!/usr/bin/env python3
"""Focused C1 build, original-property workflow and optional real-display GUI check."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
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
p.add_argument('--native-tools',type=Path,help='Explicit fingerprinted native mesher tool manifest for C3')
p.add_argument('--gmsh-library',type=Path,help='Pinned Gmsh 4.13.0 library with adjacent gmsh-build.json')
p.add_argument('--cad-fixture',type=Path)
p.add_argument('--three-mf-library',type=Path,help='Explicit lib3mf 2.4.1 profile for C5 contour export')
p.add_argument('--solver-registry',type=Path)
p.add_argument('--solver-id')
p.add_argument('--solver-directory',type=Path)
p.add_argument('--gui',action='store_true',help='Requires a display (Xvfb is supplemental Linux evidence)')
a=p.parse_args()
out=a.output.resolve()
folder=out.with_suffix('')
folder.mkdir(parents=True,exist_ok=True)
host={'os':platform.system(),'architecture':{'arm64':'Arm64','aarch64':'Arm64','x86_64':'X64','amd64':'X64'}.get(platform.machine().lower())}
report={'success':False,'recordedAtUtc':datetime.now(timezone.utc).isoformat(),'host':host,'steps':[],'pending':[]}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(name,command,environment=None):
    result=subprocess.run(list(map(str,command)),cwd=ROOT,capture_output=True,text=True,timeout=300,env={**os.environ,**(environment or {})})
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
    run('original-geometry-forms',[sys.executable,HERE/'generate-geometry-forms.py','--check','--extractor',folder/'build/bin/FormSourceGen/release/FormSourceGen.dll'])
    run('original-results-forms',[sys.executable,HERE/'generate-results-forms.py','--check','--extractor',folder/'build/bin/FormSourceGen/release/FormSourceGen.dll'])
    run('original-application-forms',[sys.executable,HERE/'generate-application-forms.py','--check','--extractor',folder/'build/bin/FormSourceGen/release/FormSourceGen.dll'])
    run('original-keyword-editor',[sys.executable,HERE/'generate-keyword-editor.py','--check','--extractor',folder/'build/bin/FormSourceGen/release/FormSourceGen.dll'])
    run('original-automation',[sys.executable,ROOT/'X/Controller/generate-automation.py','--check'])
    run('original-advisor',[sys.executable,HERE/'generate-advisor.py','--check'])
    run('original-follower',[sys.executable,HERE/'generate-presentation-rules.py','--check'])
    run('ui-audit',[sys.executable,HERE/'audit-ui.py','--check','--extractor',folder/'build/bin/FormSourceGen/release/FormSourceGen.dll'])
    run('original-colormaps',[sys.executable,HERE/'generate-colormaps.py','--check'])
    run('original-main-menu',[sys.executable,HERE/'generate-main-menu.py','--check'])
    run('original-model-tree',[sys.executable,HERE/'generate-model-tree.py','--check'])
    run('build',build)
    binary=folder/'build/bin/Workbench/release/PrePoMaxX.Workbench.dll'
    if a.python_profile:
        base=['dotnet',binary,a.python_profile.resolve(),folder/'session',HERE/'workbench.py']
        native_manifest=a.native_tools
        if a.three_mf_library:
            tools=json.loads(a.native_tools.read_text()) if a.native_tools else {'schemaVersion':1,'tools':{}}
            tools['tools']['lib3mf.dll']={'path':str(a.three_mf_library.resolve()),'sha256':sha(a.three_mf_library.resolve())};native_manifest=folder/'tools-with-3mf.json';native_manifest.write_text(json.dumps(tools,indent=2)+'\n');base+=['--native-tools',native_manifest,'--check-3mf']
        run('service',base+['--service-probe',folder/'service'])
        result=json.loads((folder/'service/service.json').read_text())
        if not result.get('success'):raise ValueError('Service workflow failed')
        report['service']=result
        run('authoring-service',base+['--authoring-service-probe',folder/'authoring/service'])
        result=json.loads((folder/'authoring/service/authoring.json').read_text())
        if not result.get('success'):raise ValueError('C2 authoring workflow failed')
        report['authoringService']=result
        run('application-service',base+['--application-service-probe',folder/'application/service'])
        result=json.loads((folder/'application/service/application.json').read_text())
        if not result.get('success'):raise ValueError('C5 service workflow failed')
        report['applicationService']=result
        if a.native_tools and a.gmsh_library:
            geometry_base=base+['--native-tools',native_manifest.resolve()]
            if a.cad_fixture:geometry_base+=['--cad-fixture',a.cad_fixture.resolve()]
            geometry_env={'PREPOMAXX_GMSH_LIBRARY':str(a.gmsh_library.resolve())}
            run('geometry-service',geometry_base+['--geometry-service-probe',folder/'geometry/service'],geometry_env)
            result=json.loads((folder/'geometry/service/geometry.json').read_text())
            if not result.get('success'):raise ValueError('C3 geometry/meshing workflow failed')
            report['geometryService']=result
        else:report['pending'].append('C3 native CAD/meshing not executed: explicit --native-tools and --gmsh-library not supplied')
        if all([a.solver_registry,a.solver_id,a.solver_directory]):
            result_base=base+['--solver-registry',a.solver_registry.resolve(),'--solver-id',a.solver_id,'--solver-directory',a.solver_directory.resolve()]
            run('results-service',result_base+['--results-service-probe',folder/'results/service'])
            result=json.loads((folder/'results/service/results.json').read_text())
            if not result.get('success'):raise ValueError('C4 service workflow failed')
            report['resultsService']=result
            report['failedEngineeringChecks']=[c for c in result.get('engineeringChecks',[]) if not c['passed']]
        else:report['pending'].append('C4 solver/results workflow not executed: explicit solver registry/id/directory not supplied')
        if a.gui:
            run('gui',base+['--probe',folder/'gui'])
            result=json.loads((folder/'gui/gui.json').read_text())
            if not result.get('success'):raise ValueError('GUI workflow failed: '+str(result))
            report['gui']=result
            run('authoring-gui',base+['--authoring-probe',folder/'authoring/gui'])
            result=json.loads((folder/'authoring/gui/authoring-gui.json').read_text())
            if not result.get('success'):raise ValueError('C2 GUI workflow failed: '+str(result))
            report['authoringGui']=result
            if a.native_tools and a.gmsh_library:
                run('geometry-gui',geometry_base+['--geometry-probe',folder/'geometry/gui'],geometry_env)
                result=json.loads((folder/'geometry/gui/geometry-gui.json').read_text())
                if not result.get('success'):raise ValueError('C3 GUI workflow failed')
                report['geometryGui']=result
            if all([a.solver_registry,a.solver_id,a.solver_directory]):
                run('results-gui',result_base+['--results-probe',folder/'results/gui'])
                result=json.loads((folder/'results/gui/results-gui.json').read_text())
                if not result.get('success'):raise ValueError('C4 GUI workflow failed')
                report['resultsGui']=result
            run('application-gui',base+['--application-probe',folder/'application/gui'])
            result=json.loads((folder/'application/gui/application-gui.json').read_text())
            if not result.get('success'):raise ValueError('C5 GUI workflow failed: '+str(result))
            report['applicationGui']=result
            menu_results=folder/'results/service/results.pmx'
            menu=base+['--menu-probe',folder/'menu','--menu-model',folder/'application/service/application.pmx']
            if menu_results.is_file():menu+=['--menu-results',menu_results]
            else:report['pending'].append('Main-menu results view not executed: C4 results fixture not produced')
            run('menu-gui',menu)
            result=json.loads((folder/'menu/menu-gui.json').read_text())
            if not result.get('success'):raise ValueError('Original main-menu workflow failed: '+str(result.get('error')))
            report['menuGui']={k:result[k] for k in ('success','checks','leafItems','unmappedItems','smokeMappingErrors') if k in result}
        else:report['pending'].append('GUI workflow not executed: --gui not supplied')
    else:report['pending'].append('Property/native UI workflow not executed: no explicit CPython profile')
    report['success']=True
except Exception as error:report['error']=str(error)
finally:
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'success':report['success'],'output':str(out),'pending':report['pending']}))
raise SystemExit(0 if report['success'] else 1)

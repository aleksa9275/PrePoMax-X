#!/usr/bin/env python3
"""Build/launch the original-Controller C1 desktop host with explicit runtime inputs."""
import argparse
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--python-profile', required=True, type=Path)
p.add_argument('--work-directory', required=True, type=Path)
p.add_argument('--feed', type=Path, help='Optional offline NuGet feed')
p.add_argument('--gmsh-library',type=Path,help='Pinned Gmsh 4.13.0 library with adjacent gmsh-build.json')
p.add_argument('--native-tools',type=Path,help='Explicit fingerprinted native tool manifest')
p.add_argument('--no-build', action='store_true')
p.add_argument('project', nargs='?', type=Path)
a = p.parse_args()
if not a.no_build:
    command = ['dotnet','build',str(HERE/'Workbench/Workbench.csproj'),'-c','Release',
               '--disable-build-servers','-m:1','-p:UseSharedCompilation=false','-v:q']
    if a.feed:
        command += ['-p:RestoreSources='+str(a.feed.resolve())]
    subprocess.run(command, cwd=ROOT, check=True)
command = ['dotnet',str(HERE/'Workbench/bin/Release/net10.0/PrePoMaxX.Workbench.dll'),
           str(a.python_profile.resolve()),str(a.work_directory.resolve()),str(HERE/'workbench.py')]
if a.native_tools:command += ['--native-tools',str(a.native_tools.resolve())]
if a.project:
    command.append(str(a.project.resolve()))
environment=dict(os.environ)
if a.gmsh_library:environment['PREPOMAXX_GMSH_LIBRARY']=str(a.gmsh_library.resolve())
raise SystemExit(subprocess.call(command,cwd=ROOT,env=environment))

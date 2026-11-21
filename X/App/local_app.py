#!/usr/bin/env python3
"""Assemble a local, runnable macOS (ARM64) folder of the original application (X/App) with the Qt front end.

    python3 X/App/local_app.py --package <PrePoMax-X.app of P1> --solver <solver folder with build-registry.json> \
        --solver-id <build id> --output X/Build/artifacts/app-mac

The P1 package supplies CPython 3.12 with PyQt6, Netgen, Mmg, Gmsh, lib3mf and lp_solve; this repository supplies
X/App (built here), GmshCaller (built from the current sources), QuadWild (X/Build/QuadWild) and the vtkNative
runtime (X/Build/Vtk). The output holds app/ (PrePoMax, PrePoMax.com, PrePoMaxX.runtime.json, settings.bin),
profiles/ (python.json, tools.json) and PrePoMax-X.command, which starts the application. Nothing is installed or
copied over an existing application; the output folder is replaced only below it. A local working folder, not a
release package (P1/M5).
"""
import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV = {**os.environ, 'DOTNET_ROLL_FORWARD': os.environ.get('DOTNET_ROLL_FORWARD', 'Major')}


def run(*command, **kw):
    print('+', ' '.join(map(str, command)), flush=True)
    subprocess.run(list(map(str, command)), check=True, cwd=ROOT, env=ENV, **kw)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--package', type=Path, required=True, help='PrePoMax-X.app of P1 (X/Build/package_ui.py)')
    p.add_argument('--solver', type=Path, required=True, help='Solver folder with build-registry.json and bin/')
    p.add_argument('--solver-id', required=True)
    p.add_argument('--default-solver-type', default='Spooles')
    p.add_argument('--vtk-native', type=Path, default=ROOT / 'X/Build/artifacts/vtk-mac-arm64/vtkNative/runtime')
    p.add_argument('--quadwild', type=Path, default=ROOT / 'X/Build/artifacts/quadwild-mac-arm64/runtime')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    resources = a.package.resolve() / 'Contents/Resources'
    package = json.loads((resources / 'package.json').read_text())
    out = a.output.resolve()
    app, profiles = out / 'app', out / 'profiles'
    if out.exists() and not (out / 'local-app.json').exists() and any(out.iterdir()):
        raise SystemExit(f'{out} exists and was not made by this script')

    # Builds: the whole original application, its Configure tool and GmshCaller from the current sources
    run('python3', 'X/UI/generate-original-forms.py', '--check')
    run('dotnet', 'build', 'X/App/PrePoMax/PrePoMax.csproj', '-c', 'Release', '-v:q', f'-p:VtkNativeRuntime={a.vtk_native.resolve()}')
    run('dotnet', 'build', 'X/App/Configure/Configure.csproj', '-c', 'Release', '-v:q')
    run('dotnet', 'build', 'X/Domain/GmshCaller', '-c', 'Release', '-v:q')

    # The application folder
    if app.exists():
        shutil.rmtree(app)
    shutil.copytree(ROOT / 'X/App/PrePoMax/bin/Release/net10.0', app)
    shutil.copy2(app / 'PrePoMax', app / 'PrePoMax.com')
    # The 3D view: libvtkNative and the VTK libraries beside vtkControl.dll (an incremental build may skip the copy)
    for item in a.vtk_native.resolve().iterdir():
        if item.is_file() and not item.name.startswith('vtkControl.'):
            shutil.copy2(item, app / item.name, follow_symlinks=False)
    if not (app / 'libvtkNative.dylib').exists():
        raise SystemExit('The vtkNative runtime has no libvtkNative.dylib')
    lpsolve = resources / package['components']['lpsolve']['file'] if (resources / package['components']['lpsolve']['file']).exists() \
        else resources / 'app' / package['components']['lpsolve']['file']
    if sha(lpsolve) != package['components']['lpsolve']['sha256']:
        raise SystemExit('lp_solve does not match the package manifest')
    shutil.copy2(lpsolve, app / lpsolve.name)
    gmsh_caller = ROOT / 'X/Domain/GmshCaller/bin/Release/net10.0'
    shutil.copy2(lpsolve, gmsh_caller / lpsolve.name)

    # Profiles: the package's Python and tools, GmshCaller and QuadWild from this repository
    if profiles.exists():
        shutil.rmtree(profiles)
    interpreter = resources / package['components']['python']['interpreter']
    run(interpreter, '-I', resources / 'launch.py', '--profiles', profiles)
    tools = json.loads((profiles / 'tools.json').read_text())
    def put(ident, path):
        tools['tools'][ident] = {'path': str(path), 'sha256': sha(path)}
    put('\\lib\\GmshCaller.exe', gmsh_caller / 'GmshCaller')
    put('\\Meshers\\QuadWild\\quadwild.exe', a.quadwild / 'quadwild.exe')
    put('\\Meshers\\QuadWild\\quad_from_patches.exe', a.quadwild / 'quad_from_patches.exe')
    (profiles / 'tools.json').write_text(json.dumps(tools, indent=2) + '\n')

    # The runtime profile and the original settings with the solver
    gmsh = resources / package['components']['gmsh']['file']
    if sha(gmsh) != package['components']['gmsh']['sha256']:
        raise SystemExit('Gmsh does not match the package manifest')
    solver = a.solver.resolve()
    run('dotnet', ROOT / 'X/App/Configure/bin/Release/net10.0/PrePoMaxX.Configure.dll', '--app', app,
        '--python', profiles / 'python.json', '--ui', ROOT / 'X/UI', '--native-tools', profiles / 'tools.json',
        '--gmsh-library', gmsh, '--solver', solver / 'build-registry.json', a.solver_id, solver / 'bin',
        '--default-solver-type', a.default_solver_type)

    # The launcher: the application with its own runtime profile; a leftover recovery file of a killed run is the
    # user's to keep, so it is not removed here
    launcher = out / 'PrePoMax-X.command'
    launcher.write_text('#!/bin/bash\n# Starts the original PrePoMax (X/App) with the Qt front end; arguments as the original command line\n'
                        'export DOTNET_ROLL_FORWARD="${DOTNET_ROLL_FORWARD:-Major}"\n'
                        f'exec dotnet "{app}/PrePoMax.dll" "$@"\n')
    launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    (out / 'local-app.json').write_text(json.dumps({
        'schemaVersion': 1, 'package': str(a.package.resolve()), 'solver': str(solver), 'solverId': a.solver_id,
        'vtkNative': str(a.vtk_native.resolve()), 'quadwild': str(a.quadwild.resolve()),
        'revision': subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
    }, indent=2) + '\n')
    print(f'Ready: {launcher}')


if __name__ == '__main__':
    main()

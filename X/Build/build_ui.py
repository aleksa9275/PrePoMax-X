#!/usr/bin/env python3
"""Build every native input of the PrePoMax-X desktop for one target from the pinned recipes, then package it.

    python3 X/Build/build_ui.py --target linux-x64 --workspace /abs/workspace --jobs 8 --format tar.gz

Stages (each into <workspace>/<stage>, resumable: a finished stage is reused):

    lpsolve   X/Build/LpSolve/build.py        lp_solve 5.5.2.11
    mmg       X/Build/Mmg/build.py            mmgs 5.5.2, mmg3d 5.7.0
    lib3mf    official 2.4.1 library (macOS) / 2.4.1 source build (Linux)
    gmsh      X/Build/Gmsh/build.py           patched Gmsh 4.13.0 + static OCCT 7.7.0
    netgen    X/Build/NativeCad/build.py      original Netgen wrapper + OCCT 8.0.1
    quadwild  X/Build/QuadWild/build.py       PrePoMax's QuadWild-BiMDF fork (the 3.0.1 revision)
    vtk       X/Build/Vtk/build.py            VTK 9.7.1 + the original vtkNative (the 3D view)
    solver    X/Build/build.py ... solver     CalculiX 2.22, SPOOLES, ARPACK-ng, OpenBLAS
    package   X/Build/package_ui.py

Run it on a native host of the target (Linux x64: Podman on Windows per D059; Linux ARM64: the local Podman
machine; macOS ARM64: the Mac). For win-x64 the native stages are the vendored ThirdParty Windows binaries and
only the package stage runs (it may run on any host). Downloads are checked against the source locks;
compilers come from the host (recorded in each receipt). Use a dedicated workspace per target.
"""
import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LIB3MF = {'version': '2.4.1',
          'source': {'archive': 'lib3mf-2.4.1-source-with-submodules.zip',
                     'url': 'https://github.com/3MFConsortium/lib3mf/releases/download/v2.4.1/lib3mf-2.4.1-source-with-submodules.zip',
                     'sha256': '4e9e1776f4dd1b3dfce684ce9bb4ad1157dadf29908a1f3aabb6cd4358bf3248'},
          'windows': {'archive': 'lib3mf-2.4.1-Windows.zip',
                      'url': 'https://github.com/3MFConsortium/lib3mf/releases/download/v2.4.1/lib3mf-2.4.1-Windows.zip',
                      'sha256': '6083de92349ca3db54466e9d057b244acc3f426083a465dac0c115583524f0fa'},
          'darwin': {'archive': 'lib3mf-2.4.1-Darwin.zip',
                     'url': 'https://github.com/3MFConsortium/lib3mf/releases/download/v2.4.1/lib3mf-2.4.1-Darwin.zip',
                     'sha256': 'd3db960146af09cbde98eaafe87ecdaf7d5d22ac6a22bed286d9eb952ccc9d89'}}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fetch(cache, archive, url, digest):
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / archive
    if not path.exists():
        print('downloading', url, flush=True)
        urllib.request.urlretrieve(url, path)
    if sha(path) != digest:
        raise SystemExit(f'{path}: SHA-256 differs from its source lock')
    return path


def run(command, cwd=None):
    print('$', ' '.join(str(c) for c in command), flush=True)
    subprocess.run([str(c) for c in command], check=True, cwd=cwd)


def stage(workspace, name, build):
    """Runs build(output) once; a stage with done.json is reused."""
    output = workspace / name
    done = output / 'done.json'
    if done.exists():
        print(f'[{name}] reused', flush=True)
        return json.loads(done.read_text())
    if output.exists():
        shutil.rmtree(output)
    print(f'[{name}] building', flush=True)
    result = build(output)
    done.write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--target', required=True, choices=['osx-arm64', 'linux-x64', 'linux-arm64', 'win-x64'])
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--jobs', type=int, default=4)
    p.add_argument('--format', default=None, help='package format (default: dmg / tar.gz / zip)')
    p.add_argument('--skip', default='', help='comma-separated stages to leave out (recorded as missing)')
    a = p.parse_args()
    workspace = a.workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    cache = workspace / 'downloads'
    skip = {s for s in a.skip.split(',') if s}
    target = a.target
    py = sys.executable
    inputs = {}
    if target == 'win-x64' and 'lib3mf' not in skip:
        def lib3mf_windows(out):
            out.mkdir(parents=True)
            archive = fetch(cache, LIB3MF['windows']['archive'], LIB3MF['windows']['url'], LIB3MF['windows']['sha256'])
            with zipfile.ZipFile(archive) as z:
                z.extractall(out / 'release')
            library = next(p for p in (out / 'release').rglob('lib3mf.dll'))
            return {'library': str(library), 'sha256': sha(library)}
        inputs['--lib3mf'] = stage(workspace, 'lib3mf', lib3mf_windows)['library']
    if target != 'win-x64':
        if 'lpsolve' not in skip:
            r = stage(workspace, 'lpsolve', lambda out: (run([py, HERE / 'LpSolve/build.py', '--archive-cache', cache, '--output', out]),
                      {'library': str(next((out / 'runtime').glob('lpsolve55.dll.*')))})[1])
            inputs['--lpsolve'] = r['library']
        if 'mmg' not in skip:
            r = stage(workspace, 'mmg', lambda out: (run([py, HERE / 'Mmg/build.py', '--archive-cache', cache, '--output', out,
                                                          '--jobs', a.jobs]), {'runtime': str(out / 'runtime')})[1])
            inputs['--mmg'] = r['runtime']
        if 'lib3mf' not in skip:
            def lib3mf(out):
                out.mkdir(parents=True)
                if target == 'osx-arm64':
                    archive = fetch(cache, **{k: LIB3MF['darwin'][k] for k in ('archive', 'url')}, digest=LIB3MF['darwin']['sha256'])
                    with zipfile.ZipFile(archive) as z:
                        z.extractall(out / 'release')
                    library = next(p for p in (out / 'release').rglob('lib3mf.2.4.1.0.dylib'))
                else:
                    archive = fetch(cache, **{k: LIB3MF['source'][k] for k in ('archive', 'url')}, digest=LIB3MF['source']['sha256'])
                    with zipfile.ZipFile(archive) as z:
                        z.extractall(out / 'source')
                    source = next(p.parent for p in (out / 'source').rglob('CMakeLists.txt') if p.parent.parent == out / 'source')
                    run(['cmake', '-S', source, '-B', out / 'build', '-DCMAKE_BUILD_TYPE=Release', '-DLIB3MF_TESTS=OFF',
                         '-DCMAKE_INSTALL_PREFIX=' + str(out / 'runtime'), '-DCMAKE_POLICY_VERSION_MINIMUM=3.5'])
                    run(['cmake', '--build', out / 'build', '-j', a.jobs])
                    run(['cmake', '--install', out / 'build'])
                    library = next(p for p in (out / 'runtime').rglob('lib3mf.so.2.4.1.0'))
                return {'library': str(library), 'sha256': sha(library)}
            inputs['--lib3mf'] = stage(workspace, 'lib3mf', lib3mf)['library']
        if 'gmsh' not in skip:
            def gmsh(out):
                lock = json.loads((HERE / 'Gmsh/source-lock.json').read_text())
                for key in ('gmsh', 'occt'):
                    fetch(cache, lock[key]['archive'], lock[key]['url'], lock[key]['sha256'])
                run([py, HERE / 'Gmsh/build.py', '--archives', cache, '--output', out, '--jobs', a.jobs])
                library = next(p for p in (out / 'runtime').iterdir() if p.name in ('libgmsh.4.13.0.dylib', 'libgmsh.so.4.13.0'))
                return {'library': str(library)}
            inputs['--gmsh-library'] = stage(workspace, 'gmsh', gmsh)['library']
        if 'netgen' not in skip:
            r = stage(workspace, 'netgen', lambda out: (run([py, HERE / 'NativeCad/build.py', '--output', out, '--jobs', a.jobs]),
                      {'runtime': str(out / 'runtime')})[1])
            inputs['--netgen'] = r['runtime']
        if 'quadwild' not in skip:
            r = stage(workspace, 'quadwild', lambda out: (run([py, HERE / 'QuadWild/build.py', '--archive-cache', cache, '--output', out,
                                                               '--jobs', a.jobs]), {'runtime': str(out / 'runtime')})[1])
            inputs['--quadwild'] = r['runtime']
        if 'vtk' not in skip:
            r = stage(workspace, 'vtk', lambda out: (run([py, HERE / 'Vtk/build.py', '--archive-cache', cache, '--output', out,
                                                          '--jobs', a.jobs]), {'runtime': str(out / 'vtkNative/runtime')})[1])
            inputs['--vtk-native'] = r['runtime']
        if 'solver' not in skip:
            r = stage(workspace, 'solver', lambda out: (run([py, HERE / 'build.py', 'build', '--target', target, '--component', 'solver',
                                                             '--jobs', a.jobs, '--output', out]), {'build': str(out / 'solver')})[1])
            inputs['--solver-build'] = r['build']
    package_format = a.format or {'osx-arm64': 'dmg', 'win-x64': 'zip'}.get(target, 'tar.gz')
    out = workspace / 'package'
    if out.exists():
        shutil.rmtree(out)
    command = [py, HERE / 'package_ui.py', '--target', target, '--output', out, '--cache', cache, '--format', package_format]
    for key, value in inputs.items():
        command += [key, value]
    run(command)


if __name__ == '__main__':
    main()

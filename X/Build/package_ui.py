#!/usr/bin/env python3
"""Assemble the native components of a PrePoMax-X package for one target, from explicitly named, fingerprinted
inputs (the input of X/App/package_mac.py and X/App/package_linux.py: --p1).

    python3 X/Build/package_ui.py --target osx-arm64 --output /abs/new-output --cache /abs/download-cache \
        --netgen <NativeCad runtime> --gmsh-library <libgmsh.4.13.0.dylib> --lib3mf <lib3mf 2.4.1 library> \
        --lpsolve <X/Build/LpSolve runtime library> --mmg <X/Build/Mmg runtime> --solver-build <CalculiX build> \
        --format tar.gz

The layout is the same on every target:

    app/        lp_solve (the folder of the application, where CaeMesh loads it)
    tools/      gmsh, Netgen, Mmg, lib3mf, QuadWild (what was supplied)
    solver/     the relocated CalculiX build with its registry
    python/     CPython 3.12.14 (python-build-standalone) with the hash-pinned wheels of X/Build/python-requirements
                (numpy, for the original's Python features)
    package.json, Licenses/, NOTICE.md

Inputs that are not supplied are recorded as missing in package.json; nothing is substituted. QuadWild on macOS/Linux
is the runtime X/Build/QuadWild builds from the published fork (--quadwild); Windows layouts take the vendored
ThirdParty binaries. Until M3-1b this also packaged the Qt workbench (X/UI, retired with PyQt, D065); the application,
GmshCaller and the 3D view now come from X/App's packagers.
"""
import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CATALOG = json.loads((HERE / 'targets.json').read_text())
PYTHON = json.loads((HERE / 'python-runtime-lock.json').read_text())
NAME = 'PrePoMax-X'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Runner:
    """The small build interface the platform solver adapters use (run + log)."""

    def __init__(self, output, target):
        self.output = output
        self.target_id = target
        self.target = CATALOG['targets'][target]
        self.logs = output / 'logs'
        self.logs.mkdir(parents=True, exist_ok=True)
        self.report = {}

    def run(self, command, name=None):
        command = [str(c) for c in command]
        log = self.logs / ((name or Path(command[0]).name) + '.log')
        with open(log, 'a') as out:
            out.write('$ ' + ' '.join(command) + '\n')
            out.flush()
            result = subprocess.run(command, stdout=out, stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError(f'{command[0]} failed ({result.returncode}); see {log}')


def native_matches(target):
    entry = CATALOG['targets'][target]
    return platform.system() == entry['os'] and platform.machine().lower() in entry['machines']


def publish(runner, project, target, destination, name):
    runner.run(['dotnet', 'publish', ROOT / project, '-c', 'Release', '-r', target, '--self-contained', 'true',
                f'-p:RuntimeFrameworkVersion={CATALOG["runtimeFrameworkVersion"]}',
                f'-p:NativePreviewLockRoot={runner.output / "locks" / name}',
                '--artifacts-path', runner.output / 'dotnet' / name, '-o', destination, '-v:quiet'], 'publish-' + name)


def python_runtime(runner, target, cache, destination):
    entry = PYTHON['targets'][target]
    cache.mkdir(parents=True, exist_ok=True)
    archive = cache / entry['archive']
    if not archive.exists():
        url = PYTHON['baseUrl'] + entry['archive'].replace('+', '%2B')
        print('downloading', url)
        urllib.request.urlretrieve(url, archive)
    if sha(archive) != entry['sha256']:
        raise SystemExit(f'{archive}: SHA-256 differs from python-runtime-lock.json')
    with tarfile.open(archive) as tar:
        tar.extractall(destination.parent / 'python-extract', filter='data')
    shutil.move(destination.parent / 'python-extract' / 'python', destination)
    (destination.parent / 'python-extract').rmdir()
    interpreter = destination / entry['interpreter']
    requirements = HERE / 'python-requirements' / (target + '.txt')
    pip = ['install', '--disable-pip-version-check', '--no-cache-dir', '--require-hashes', '--only-binary=:all:',
           '--no-deps', '-r', requirements]
    if target.startswith('win') and sys.platform != 'win32':
        # Cross layout: the host pip installs the hash-pinned win_amd64 wheels into the Windows runtime.
        runner.run([sys.executable, '-m', 'pip'] + pip + ['--platform', 'win_amd64', '--python-version', '3.12',
                    '--implementation', 'cp', '--abi', 'cp312', '--target', destination / 'Lib/site-packages'], 'pip-install')
    else:
        runner.run([interpreter, '-I', '-m', 'pip'] + pip, 'pip-install')
    return entry


def copy_tree(source, destination):
    shutil.copytree(source, destination, symlinks=True)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--target', required=True, choices=sorted(CATALOG['targets']))
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--cache', type=Path, required=True, help='download cache (CPython archive)')
    p.add_argument('--quadwild', type=Path, help='QuadWild runtime folder from X/Build/QuadWild (macOS/Linux)')
    p.add_argument('--netgen', type=Path, help='NativeCad runtime folder (bin/NetGenMesher, lib/)')
    p.add_argument('--gmsh-library', type=Path, help='patched Gmsh 4.13.0 library with gmsh-build.json beside it')
    p.add_argument('--lib3mf', type=Path, help='lib3mf 2.4.1 library')
    p.add_argument('--lpsolve', type=Path, help='lp_solve 5.5.2.11 library from X/Build/LpSolve')
    p.add_argument('--mmg', type=Path, help='X/Build/Mmg runtime folder (mmgs, mmg3d)')
    p.add_argument('--solver-build', type=Path, help='verified native CalculiX build (build-registry.json)')
    p.add_argument('--format', choices=['folder', 'tar.gz', 'zip'], default='folder')
    a = p.parse_args()
    target = a.target
    windows = target.startswith('win')
    if a.output.exists() and any(a.output.iterdir()):
        raise SystemExit(f'{a.output} is not empty; use a new output directory')
    if not native_matches(target) and not windows:
        raise SystemExit(f'{target} is packaged on a matching native host (native tools and solver are relocated there)')
    a.output.mkdir(parents=True, exist_ok=True)
    runner = Runner(a.output, target)
    stage = a.output / 'stage' / NAME
    stage.mkdir(parents=True)
    manifest = {'schemaVersion': 1, 'name': NAME, 'target': target, 'components': {}, 'missing': {},
                'scope': 'Local test build for manual testing; not signed for distribution, not release acceptance'}
    try:
        manifest['source'] = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
        manifest['sourceDirty'] = bool(subprocess.check_output(['git', '-C', str(ROOT), 'status', '--porcelain', '--untracked-files=no'], text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        manifest['source'] = None

    (stage / 'app').mkdir(parents=True)
    exe = '.exe' if windows else ''
    tools = {}

    # lp_solve beside the application assemblies (CaeMesh); the packagers also put it beside GmshCaller
    lpsolve = a.lpsolve or (ROOT / 'ThirdParty/lpsolve/lpsolve55.dll' if windows else None)
    if lpsolve:
        shutil.copy2(lpsolve, stage / 'app' / lpsolve.name)
        manifest['components']['lpsolve'] = {'version': '5.5.2.11', 'file': lpsolve.name, 'sha256': sha(lpsolve)}
    else:
        manifest['missing']['lpsolve'] = 'not supplied: Gmsh interval assignment (default shell meshing, compound sweep) fails'

    # Gmsh
    if a.gmsh_library:
        receipt = a.gmsh_library.parent / 'gmsh-build.json'
        (stage / 'tools/gmsh').mkdir(parents=True)
        shutil.copy2(a.gmsh_library, stage / 'tools/gmsh' / a.gmsh_library.name)
        if receipt.exists():
            shutil.copy2(receipt, stage / 'tools/gmsh/gmsh-build.json')
        manifest['components']['gmsh'] = {'version': '4.13.0 (patched)', 'file': 'tools/gmsh/' + a.gmsh_library.name, 'sha256': sha(a.gmsh_library)}
    elif windows:
        manifest['missing']['gmsh'] = ('pending: the Windows (MSVC) build of the pinned patched Gmsh 4.13.0 (X/Build/Gmsh); '
                                       'Gmsh meshing is unavailable, Netgen meshing works')
    else:
        manifest['missing']['gmsh'] = 'not supplied: Gmsh meshing unavailable'

    # Netgen (original command wrapper + OCCT 8.0.1 closure)
    if a.netgen:
        copy_tree(a.netgen, stage / 'tools/Netgen')
        mesher = 'tools/Netgen/bin/NetGenMesher' + exe
        tools['\\Meshers\\Netgen\\NetGenMesher.exe'] = mesher
        manifest['components']['netgen'] = {'file': mesher, 'sha256': sha(stage / mesher)}
    elif windows:
        copy_tree(ROOT / 'ThirdParty/netgen', stage / 'tools/Netgen')
        tools['\\Meshers\\Netgen\\NetGenMesher.exe'] = 'tools/Netgen/NetGenMesher.exe'
        manifest['components']['netgen'] = {'file': 'tools/Netgen/NetGenMesher.exe', 'vendored': 'ThirdParty/netgen'}
    else:
        manifest['missing']['netgen'] = 'not supplied: CAD import and Netgen meshing unavailable'

    # Mmg
    mmg = a.mmg or (ROOT / 'ThirdParty/mmg' if windows else None)
    if mmg:
        copy_tree(mmg, stage / 'tools/Mmg')
        tools['\\Meshers\\Mmg\\mmgs.exe'] = f'tools/Mmg/mmgs{exe}'
        tools['\\Meshers\\Mmg\\mmg3d.exe'] = f'tools/Mmg/mmg3d{exe}'
        manifest['components']['mmg'] = {'mmgs': '5.5.2', 'mmg3d': '5.7.0'}
    else:
        manifest['missing']['mmg'] = 'not supplied: Mmg remeshing unavailable'

    # QuadWild
    if windows:
        copy_tree(ROOT / 'ThirdParty/quadwild-bimdf', stage / 'tools/QuadWild')
        tools['\\Meshers\\QuadWild\\quadwild.exe'] = 'tools/QuadWild/quadwild.exe'
        tools['\\Meshers\\QuadWild\\quad_from_patches.exe'] = 'tools/QuadWild/quad_from_patches.exe'
        manifest['components']['quadwild'] = {'vendored': 'ThirdParty/quadwild-bimdf'}
    elif a.quadwild:
        receipt = json.loads((a.quadwild / 'quadwild-build.json').read_text())
        for name, expected in receipt['files'].items():
            if sha(a.quadwild / name) != expected:
                raise SystemExit(f'{a.quadwild / name}: differs from quadwild-build.json')
        copy_tree(a.quadwild, stage / 'tools/QuadWild')
        tools['\\Meshers\\QuadWild\\quadwild.exe'] = 'tools/QuadWild/quadwild.exe'
        tools['\\Meshers\\QuadWild\\quad_from_patches.exe'] = 'tools/QuadWild/quad_from_patches.exe'
        manifest['components']['quadwild'] = {'revision': receipt['source']['revision'], 'repository': receipt['source']['repository'],
                                              'receipt': 'tools/QuadWild/quadwild-build.json',
                                              'receiptSha256': sha(a.quadwild / 'quadwild-build.json')}
    else:
        manifest['missing']['quadwild'] = 'not supplied: build it with X/Build/QuadWild/build.py and pass --quadwild'

    # lib3mf
    if a.lib3mf:
        (stage / 'tools/lib3mf').mkdir(parents=True)
        shutil.copy2(a.lib3mf, stage / 'tools/lib3mf' / a.lib3mf.name)
        tools['lib3mf.dll'] = 'tools/lib3mf/' + a.lib3mf.name
        manifest['components']['lib3mf'] = {'version': '2.4.1', 'sha256': sha(a.lib3mf)}
    else:
        manifest['missing']['lib3mf'] = 'not supplied: 3MF export unavailable'

    # Solver
    solver = None
    if a.solver_build:
        sys.path.insert(0, str(HERE))
        sys.path.insert(0, str(HERE / 'platforms'))
        if target == 'osx-arm64':
            import macos
            macos.bundle_solver(runner, stage, a.solver_build, stage / 'solver')
        else:
            import linux
            linux.bundle_solver(runner, a.solver_build, stage / 'solver')
        manifest['solverRelocation'] = runner.report.get('solverRelocation')
        registry = json.loads((stage / 'solver/build-registry.json').read_text())
        solver = {'registry': 'solver/build-registry.json', 'id': registry['builds'][0]['id'], 'directory': 'solver/bin'}
        manifest['components']['calculix'] = {'version': registry['builds'][0]['version'], 'id': solver['id'],
                                              'backend': registry['builds'][0].get('backend')}
    else:
        manifest['missing']['calculix'] = ('not supplied: set the CalculiX executable in Settings (Windows: the native solver '
                                           'build is pending; the Intel/PARDISO build is excluded)')

    # Python
    entry = python_runtime(runner, target, a.cache, stage / 'python')
    manifest['components']['python'] = {'version': PYTHON['version'], 'release': PYTHON['release'],
                                        'library': 'python/' + entry['library'],
                                        'librarySha256': sha(stage / 'python' / entry['library']),
                                        'moduleDirectories': ['python/' + d for d in entry['moduleDirectories']],
                                        'interpreter': 'python/' + entry['interpreter'],
                                        'wheels': 'X/Build/python-requirements/' + target + '.txt'}

    # Licenses and notices
    copy_tree(ROOT / 'Licenses', stage / 'Licenses')
    shutil.copy2(ROOT / 'LICENSE', stage / 'Licenses/PrePoMax-LICENSE')
    shutil.copy2(HERE / 'package-notice.md', stage / 'NOTICE.md')

    manifest['tools'] = {k: {'path': v, 'sha256': sha(stage / v)} for k, v in tools.items()}
    manifest['solver'] = solver
    (stage / 'package.json').write_text(json.dumps(manifest, indent=2) + '\n')
    manifest['kind'] = 'components'
    result = finish(runner, stage, target, a.format)
    print(json.dumps({'package': str(result), 'missing': manifest['missing']}, indent=2))


def finish(runner, stage, target, package_format):
    if package_format in ('folder', 'tar.gz', 'zip'):
        if package_format == 'folder':
            return stage
        base = runner.output / 'dist' / f'{NAME}-{target}'
        base.parent.mkdir(exist_ok=True)
        if package_format == 'zip':
            return Path(shutil.make_archive(str(base), 'zip', stage.parent, NAME))
        with tarfile.open(str(base) + '.tar.gz', 'w:gz') as tar:
            tar.add(stage, arcname=NAME)
        return Path(str(base) + '.tar.gz')
    raise SystemExit(f'unknown format {package_format}')

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Build VTK 9.7.1 (with upstream's patch) and the original vtkNative library on it, for macOS and Linux.

    python3 X/Build/Vtk/build.py --archive-cache /abs/cache --output /abs/new-output --jobs 12
    python3 X/Build/Vtk/build.py --vtk-prefix /abs/old-output/vtk --output /abs/new-output   # reuse a VTK build

VTK is configured shared and Release with only the modules vtkNative/CMakeLists.txt asks for (and what they need);
upstream enables whole module groups on Windows, which builds more but links the same modules. The vtkNative
sources are built unchanged from the repository with their own CMakeLists.txt; its post-build step copies the
library and the VTK libraries it loads into <output>/vtkNative/runtime. runtime/vtk-build.json records the source,
patch, options, host and hashes. Windows keeps upstream's Visual Studio build (README.md).
"""
import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import tarfile
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LOCK = json.loads((HERE / 'source-lock.json').read_text())
# The find_package(VTK COMPONENTS ...) list of vtkNative/CMakeLists.txt
MODULES = ['CommonCore', 'CommonDataModel', 'CommonTransforms', 'InteractionStyle', 'FiltersCore',
           'FiltersExtraction', 'FiltersGeneral', 'FiltersGeometry', 'FiltersHybrid', 'FiltersModeling',
           'FiltersSources', 'IOGeometry', 'IOImage', 'RenderingCore', 'RenderingFreeType', 'RenderingLabel',
           'RenderingOpenGL2', 'RenderingUI']
GROUPS = ['Imaging', 'MPI', 'Qt', 'Rendering', 'StandAlone', 'Views', 'Web']


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(command, **kw):
    print('+', ' '.join(map(str, command)), flush=True)
    subprocess.run(list(map(str, command)), check=True, **kw)


def rpath_origin():
    return '@loader_path' if platform.system() == 'Darwin' else '$ORIGIN'


def vtk_options(prefix):
    options = ['-DCMAKE_BUILD_TYPE=Release', '-DBUILD_SHARED_LIBS=ON', '-DCMAKE_INSTALL_PREFIX=' + str(prefix),
               '-DVTK_BUILD_TESTING=OFF', '-DVTK_BUILD_EXAMPLES=OFF', '-DVTK_BUILD_DOCUMENTATION=OFF',
               '-DVTK_WRAP_PYTHON=OFF', '-DVTK_WRAP_JAVA=OFF', '-DVTK_ENABLE_REMOTE_MODULES=OFF',
               '-DVTK_BUILD_ALL_MODULES=OFF', '-DCMAKE_INSTALL_RPATH=' + rpath_origin()]
    if platform.system() == 'Darwin':options.append('-DCMAKE_INSTALL_NAME_DIR=@rpath')
    options += ['-DVTK_GROUP_ENABLE_%s=DONT_WANT' % g for g in GROUPS]
    options += ['-DVTK_MODULE_ENABLE_VTK_%s=YES' % m for m in MODULES]
    return options


def build_vtk(a, receipt):
    source = LOCK['source']
    archive = a.archive_cache / source['archive']
    if not archive.exists():
        a.archive_cache.mkdir(parents=True, exist_ok=True)
        print('downloading', source['url'])
        urllib.request.urlretrieve(source['url'], archive)
    if sha256(archive) != source['sha256']:
        raise SystemExit(f'{archive}: SHA-256 differs from source-lock.json')
    work = a.output / 'vtk-source'
    work.mkdir()
    with tarfile.open(archive) as tar:
        tar.extractall(work, filter='data')
    src = next(work.iterdir())
    for patch in LOCK['patches']:
        run(['patch', '-p1', '--forward', '-i', ROOT / patch], cwd=src)
    prefix = a.output / 'vtk'
    build = a.output / 'vtk-build'
    options = vtk_options(prefix)
    run(['cmake', '-S', src, '-B', build] + options)
    run(['cmake', '--build', build, '--parallel', a.jobs])
    run(['cmake', '--install', build])
    shutil.copy2(src / 'Copyright.txt', prefix / 'Copyright.txt')
    receipt['vtk'] = {'version': source['version'], 'archiveSha256': source['sha256'],
                      'patches': {p: sha256(ROOT / p) for p in LOCK['patches']}, 'options': options}
    (prefix / 'vtk-build.json').write_text(json.dumps(receipt['vtk'], indent=2) + '\n')
    return prefix


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--archive-cache', type=Path)
    p.add_argument('--vtk-prefix', type=Path, help='An installed VTK from an earlier run of this recipe')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--jobs', type=int, default=8)
    a = p.parse_args()
    if platform.system() not in ('Darwin', 'Linux'):
        raise SystemExit('Windows uses upstream\'s Visual Studio build (README.md)')
    if bool(a.archive_cache) == bool(a.vtk_prefix):
        p.error('give exactly one of --archive-cache and --vtk-prefix')
    a.output = a.output.resolve()
    if a.output.exists() and any(a.output.iterdir()):
        raise SystemExit(f'{a.output} is not empty; use a new output directory')
    a.output.mkdir(parents=True, exist_ok=True)
    receipt = {'schemaVersion': 1, 'system': platform.system(), 'machine': platform.machine()}
    if a.vtk_prefix:
        prefix = a.vtk_prefix.resolve()
        receipt['vtk'] = json.loads((prefix / 'vtk-build.json').read_text())
        if receipt['vtk']['version'] != LOCK['source']['version'] or receipt['vtk']['archiveSha256'] != LOCK['source']['sha256']:
            raise SystemExit(f'{prefix}: not a VTK build of this recipe')
    else:
        prefix = build_vtk(a, receipt)
    vtk_dir = next((prefix / 'lib').glob('cmake/vtk-9.7'), None) or next(prefix.glob('lib*/cmake/vtk-9.7'))
    build = a.output / 'vtkNative'
    origin = rpath_origin()
    run(['cmake', '-S', ROOT / 'vtkNative', '-B', build, '-DCMAKE_BUILD_TYPE=Release', '-DVTK_DIR=' + str(vtk_dir),
         '-DCMAKE_BUILD_RPATH=' + origin + ';' + str(vtk_dir.parents[1]), '-DCMAKE_BUILD_WITH_INSTALL_NAME_DIR=OFF'])
    run(['cmake', '--build', build, '--parallel', a.jobs])
    runtime = build / 'runtime'
    shutil.copy2(prefix / 'Copyright.txt', runtime / 'VTK-Copyright.txt')
    receipt['vtkNative'] = {'sources': sha256_tree(ROOT / 'vtkNative'),
                            'files': {f.name: sha256(f) for f in sorted(runtime.iterdir()) if f.is_file()}}
    (runtime / 'vtk-build.json').write_text(json.dumps(receipt, indent=2) + '\n')
    library = 'libvtkNative.dylib' if platform.system() == 'Darwin' else 'libvtkNative.so'
    print(json.dumps({'runtime': str(runtime), 'library': str(runtime / library), 'vtkPrefix': str(prefix)}))


def sha256_tree(folder):
    digest = hashlib.sha256()
    for f in sorted(x for x in folder.rglob('*') if x.is_file() and 'build' not in x.relative_to(folder).parts):
        digest.update(str(f.relative_to(folder)).encode() + b'\0' + f.read_bytes())
    return digest.hexdigest()


if __name__ == '__main__':
    main()

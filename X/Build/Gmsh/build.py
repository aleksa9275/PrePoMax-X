#!/usr/bin/env python3
"""Build pinned PrePoMax Gmsh + static OCCT 7.7 in an isolated workspace.

Archives must be supplied locally; this command never downloads dependencies.
The recipe is for macOS/Linux. Windows MSVC acceptance remains separate.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile

HERE = Path(__file__).resolve().parent


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def extract(archive, target, digest):
    if sha(archive) != digest:
        raise ValueError('Source archive hash mismatch: ' + str(archive))
    with tarfile.open(archive) as source:
        for member in source.getmembers():
            relative = Path(*Path(member.name).parts[1:])
            if relative.is_absolute() or '..' in relative.parts or member.issym() or member.islnk():
                raise ValueError('Unsafe source member: ' + member.name)
            if member.isfile():
                destination = target / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                data = source.extractfile(member).read()
                if not destination.exists() or destination.read_bytes() != data:
                    destination.write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archives', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    if platform.system() not in ('Darwin', 'Linux') or args.jobs < 1:
        parser.error('Use a native macOS/Linux host and positive --jobs')
    lock = json.loads((HERE / 'source-lock.json').read_text())
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    receipt = {'success': False, 'host': {'os': platform.system(), 'architecture': platform.machine()},
               'sources': lock, 'recipeSha256': sha(Path(__file__)), 'commands': [], 'releaseAccepted': False}

    def run(command):
        command = list(map(str, command))
        receipt['commands'].append(command)
        with (out / 'build.log').open('a') as log:
            log.write('\n' + repr(command) + '\n'); log.flush()
            subprocess.run(command, cwd=out, stdout=log, stderr=subprocess.STDOUT, check=True)

    try:
        for name in ('gmsh', 'occt'):
            pin = lock[name]
            extract(args.archives / pin['archive'], out / 'source' / pin['root'], pin['sha256'])
        occt = out / 'occt'
        pic = ['-DCMAKE_POSITION_INDEPENDENT_CODE=ON'] if platform.system() == 'Linux' else []
        run(['cmake', '-S', out / 'source' / lock['occt']['root'], '-B', out / 'occt-build',
             '-DCMAKE_POLICY_VERSION_MINIMUM=3.5', '-DCMAKE_BUILD_TYPE=Release',
             '-DCMAKE_EXPORT_NO_PACKAGE_REGISTRY=ON', *pic,
             '-DCMAKE_INSTALL_PREFIX=' + str(occt), '-DBUILD_LIBRARY_TYPE=Static',
             '-DBUILD_MODULE_ApplicationFramework=OFF', '-DBUILD_MODULE_DataExchange=OFF',
             '-DBUILD_MODULE_Draw=OFF', '-DBUILD_MODULE_Visualization=OFF',
             '-DBUILD_ADDITIONAL_TOOLKITS=TKSTEP;TKIGES;TKOffset;TKFeat;TKFillet;TKMesh;TKHLR',
             '-DUSE_TCL=OFF', '-DUSE_TK=OFF', '-DUSE_FREETYPE=OFF', '-DUSE_OPENGL=OFF',
             '-DUSE_GLES2=OFF', '-DUSE_XLIB=OFF', '-DBUILD_DOC_Overview=OFF'])
        run(['cmake', '--build', out / 'occt-build', '--parallel', args.jobs])
        run(['cmake', '--install', out / 'occt-build'])
        run(['cmake', '-S', out / 'source' / lock['gmsh']['root'], '-B', out / 'gmsh-build',
             '-DCMAKE_POLICY_VERSION_MINIMUM=3.5', '-DCMAKE_BUILD_TYPE=Release',
             '-DCMAKE_PREFIX_PATH=' + str(occt), '-DENABLE_BUILD_SHARED=ON',
             '-DENABLE_OCC=ON', '-DENABLE_OCC_STATIC=ON', '-DENABLE_OCC_CAF=OFF',
             '-DENABLE_FLTK=OFF', '-DENABLE_OPENMP=OFF', '-DENABLE_MPI=OFF',
             '-DENABLE_PETSC=OFF', '-DENABLE_SLEPC=OFF', '-DENABLE_MED=OFF',
             '-DENABLE_CGNS=OFF', '-DENABLE_GMP=OFF', '-DENABLE_TESTS=OFF'])
        options = (out / 'gmsh-build/src/common/GmshConfig.h').read_text()
        if '#define HAVE_OCC' not in options:
            raise ValueError('Gmsh configured without the required OCCT kernel')
        run(['cmake', '--build', out / 'gmsh-build', '--target', 'shared', '--parallel', args.jobs])
        extension = 'libgmsh.4.13.0.dylib' if platform.system() == 'Darwin' else 'libgmsh.so.4.13.0'
        library = out / 'runtime' / extension
        library.parent.mkdir(exist_ok=True)
        shutil.copy2(out / 'gmsh-build' / extension, library)
        profile = {'schemaVersion': 1, 'version': lock['gmsh']['version'],
                   'revision': lock['gmsh']['revision'], 'occtVersion': lock['occt']['version'],
                   'librarySha256': sha(library)}
        (library.parent / 'gmsh-build.json').write_text(json.dumps(profile, indent=2) + '\n')
        receipt.update(success=True, library=str(library), runtime=profile,
                       configurationSha256=sha(out / 'gmsh-build/CMakeCache.txt'))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        receipt['error'] = str(error)
    (out / 'build-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: receipt[k] for k in ('success', 'releaseAccepted')}))
    return 0 if receipt['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

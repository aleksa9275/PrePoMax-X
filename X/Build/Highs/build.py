#!/usr/bin/env python3
"""Build HiGHS 1.16.0 as the shared library CaeMesh loads for the interval assignment (PrePoMax 3.0.2).

Upstream vendors the unmodified highs.dll of the HiGHS 1.16.0 release (git f3f113d, 32-bit HighsInt) for Windows
(ThirdParty/highs). macOS and Linux build the same commit with HiGHS's own CMake defaults (32-bit HighsInt, no
zlib, no tests or executables beyond the library). The library is named highs.dll.dylib / highs.dll.so, the first
name .NET probes for the original DllImport("highs.dll"), and placed next to GmshCaller and the application
assemblies, as lp_solve was before 3.0.2.

    python3 X/Build/Highs/build.py --archive-cache /abs/cache --output /abs/new-output

The archive is downloaded into the cache when missing and always checked against source-lock.json.
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
LOCK = json.loads((HERE / 'source-lock.json').read_text())
OPTIONS = ['-DCMAKE_BUILD_TYPE=Release', '-DBUILD_SHARED_LIBS=ON', '-DBUILD_TESTING=OFF', '-DBUILD_EXAMPLES=OFF',
           '-DFAST_BUILD=ON', '-DZLIB=OFF', '-DHIGHSINT64=OFF', '-DPYTHON_BUILD_SETUP=OFF', '-DBUILD_CXX_EXE=OFF',
           '-DCMAKE_INSTALL_RPATH=@loader_path' if platform.system() == 'Darwin' else '-DCMAKE_INSTALL_RPATH=$ORIGIN',
           '-DCMAKE_OSX_DEPLOYMENT_TARGET=13.0']


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--archive-cache', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--jobs', type=int, default=os.cpu_count() or 4)
    a = p.parse_args()
    if a.output.exists() and any(a.output.iterdir()):
        raise SystemExit(f'{a.output} is not empty; use a new output directory')
    system = platform.system()
    if system == 'Darwin':
        name = 'highs.dll.dylib'
    elif system == 'Linux':
        name = 'highs.dll.so'
    else:
        raise SystemExit('Windows uses the vendored ThirdParty/highs/highs.dll (the HiGHS 1.16.0 release)')
    a.archive_cache.mkdir(parents=True, exist_ok=True)
    archive = a.archive_cache / LOCK['archive']
    if not archive.exists():
        print('downloading', LOCK['url'])
        urllib.request.urlretrieve(LOCK['url'], archive)
    if sha256(archive) != LOCK['sha256']:
        raise SystemExit(f'{archive}: SHA-256 differs from source-lock.json')
    work = a.output / 'source'
    work.mkdir(parents=True)
    with tarfile.open(archive) as tar:
        tar.extractall(work, filter='data')
    src = work / f"HiGHS-{LOCK['commit']}"
    build = a.output / 'build'
    configure = ['cmake', '-S', str(src), '-B', str(build)] + OPTIONS
    subprocess.run(configure, check=True)
    subprocess.run(['cmake', '--build', str(build), '--target', 'highs', '-j', str(a.jobs)], check=True)
    built = [f for f in (build / 'lib').iterdir() if f.name.startswith('libhighs') and not f.is_symlink()
             and (f.suffix in ('.dylib',) or '.so' in f.name)]
    if len(built) != 1:
        raise SystemExit(f'expected one libhighs, found {[f.name for f in built]}')
    runtime = a.output / 'runtime'
    runtime.mkdir()
    shutil.copy2(built[0], runtime / name)
    if system == 'Darwin':
        subprocess.run(['install_name_tool', '-id', '@rpath/' + name, str(runtime / name)], check=True)
        subprocess.run(['codesign', '--force', '--sign', '-', str(runtime / name)], check=True)
    compiler = subprocess.run(['c++', '--version'], capture_output=True, text=True).stdout.splitlines()[0]
    receipt = {'schemaVersion': 1, 'name': 'HiGHS', 'version': LOCK['version'], 'commit': LOCK['commit'],
               'archiveSha256': LOCK['sha256'], 'library': name, 'librarySha256': sha256(runtime / name),
               'system': system, 'machine': platform.machine(), 'compiler': compiler, 'options': OPTIONS,
               'note': 'Same release as the vendored Windows highs.dll (ThirdParty/highs)'}
    (runtime / 'highs-build.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'library': str(runtime / name), 'sha256': receipt['librarySha256']}))


if __name__ == '__main__':
    main()

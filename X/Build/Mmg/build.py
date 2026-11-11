#!/usr/bin/env python3
"""Build the Mmg remeshers PrePoMax runs (Meshers/Mmg): mmgs 5.5.2 and mmg3d 5.7.0, the releases of the shipped
Windows executables (ThirdParty/mmg), configured as those were: no VTK, Elas or Scotch. Each comes from its own
release, as on Windows.

    python3 X/Build/Mmg/build.py --archive-cache /abs/cache --output /abs/new-output --jobs 8

Archives are downloaded into the cache when missing and always checked against source-lock.json. The runtime
folder holds mmgs and mmg3d (static Mmg libraries; only system libraries are linked dynamically).
"""
import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import tarfile
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCK = json.loads((HERE / 'source-lock.json').read_text())
OPTIONS = ['-DCMAKE_BUILD_TYPE=Release', '-DUSE_SCOTCH=OFF', '-DUSE_ELAS=OFF', '-DUSE_VTK=OFF', '-DBUILD_TESTING=OFF',
           '-DLIBMMG_STATIC=ON', '-DLIBMMG_SHARED=OFF', '-DLIBMMGS_STATIC=ON', '-DLIBMMGS_SHARED=OFF',
           '-DLIBMMG3D_STATIC=ON', '-DLIBMMG3D_SHARED=OFF', '-DLIBMMG2D_STATIC=OFF', '-DLIBMMG2D_SHARED=OFF',
           '-DCMAKE_POLICY_VERSION_MINIMUM=3.5']


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--archive-cache', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--jobs', type=int, default=4)
    a = p.parse_args()
    if a.output.exists() and any(a.output.iterdir()):
        raise SystemExit(f'{a.output} is not empty; use a new output directory')
    if platform.system() == 'Windows':
        raise SystemExit('Windows uses the vendored ThirdParty/mmg executables')
    a.archive_cache.mkdir(parents=True, exist_ok=True)
    runtime = a.output / 'runtime'
    runtime.mkdir(parents=True)
    receipt = {'schemaVersion': 1, 'system': platform.system(), 'machine': platform.machine(), 'options': OPTIONS, 'tools': {}}
    for tool, source in LOCK['sources'].items():
        archive = a.archive_cache / source['archive']
        if not archive.exists():
            print('downloading', source['url'])
            urllib.request.urlretrieve(source['url'], archive)
        if sha256(archive) != source['sha256']:
            raise SystemExit(f'{archive}: SHA-256 differs from source-lock.json')
        work = a.output / ('source-' + tool)
        work.mkdir()
        with tarfile.open(archive) as tar:
            tar.extractall(work, filter='data')
        src = next(work.iterdir())
        build = a.output / ('build-' + tool)
        subprocess.run(['cmake', '-S', str(src), '-B', str(build)] + OPTIONS, check=True)
        target = 'mmgs' if tool == 'mmgs' else 'mmg3d'
        subprocess.run(['cmake', '--build', str(build), '--target', target, '--parallel', str(a.jobs)], check=True)
        found = [f for f in (build / 'bin').iterdir() if f.name.startswith(target) and not f.name.endswith('.a')]
        if len(found) != 1:
            raise SystemExit(f'{tool}: expected one executable in {build / "bin"}, found {found}')
        shutil.copy2(found[0], runtime / tool)
        receipt['tools'][tool] = {'version': source['version'], 'archiveSha256': source['sha256'],
                                  'built': found[0].name, 'sha256': sha256(runtime / tool)}
    (runtime / 'mmg-build.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({t: str(runtime / t) for t in receipt['tools']}))


if __name__ == '__main__':
    main()

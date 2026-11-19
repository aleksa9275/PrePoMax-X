#!/usr/bin/env python3
"""Build the modified QuadWild-BiMDF of PrePoMax 3.0.1 (github.com/PrePoMax/QuadWild) for macOS and Linux.

    python3 X/Build/QuadWild/build.py --archive-cache /abs/cache --output /abs/new-output --jobs 8

The fork's revision behind the Windows binaries upstream ships (source-lock.json) is built with its own CMake files,
Release, Blossom-V off and without Gurobi, as the fork's CI builds it; GMM, the one library its CMakeLists.txt
downloads, comes from the archive cache, checked against the SHA-224 that file names. <output>/runtime holds what
the original QuadWildMesherRunner expects beside its executable (QuadWildRuntime): quadwild.exe, quad_from_patches.exe
(the original file names, native executables) and the config/ tree, plus LICENSE and quadwild-build.json (source, options, host, compiler and file hashes, and whether
config/ equals upstream's ThirdParty/quadwild-bimdf/config). Windows keeps upstream's vendored binaries.
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
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LOCK = json.loads((HERE / 'source-lock.json').read_text())
EXECUTABLES = ['quadwild', 'quad_from_patches']
# The original names: CaeMesh SweepQuadWildMesher finds both beside each other by QuadWildRuntime.MesherFileName and
# PatchMesherFileName (quadwild.exe, quad_from_patches.exe), not through the tool manifest
RUNTIME_NAMES = {'quadwild': 'quadwild.exe', 'quad_from_patches': 'quad_from_patches.exe'}


def digest(path, algorithm='sha256'):
    h = hashlib.new(algorithm)
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def run(command, log, **kw):
    with open(log, 'ab') as output:
        output.write(('\n+ ' + ' '.join(map(str, command)) + '\n').encode())
        output.flush()
        subprocess.run(list(map(str, command)), check=True, stdout=output, stderr=subprocess.STDOUT, **kw)


def fetch(cache, entry, algorithm):
    archive = cache / entry['archive']
    if not archive.exists():
        cache.mkdir(parents=True, exist_ok=True)
        print('downloading', entry['url'], flush=True)
        urllib.request.urlretrieve(entry['url'], archive)
    if digest(archive, algorithm) != entry[algorithm]:
        raise SystemExit(f'{archive}: {algorithm.upper()} differs from source-lock.json')
    return archive


def extract(archive, destination):
    destination.mkdir(parents=True)
    with tarfile.open(archive) as tar:
        tar.extractall(destination, filter='data')
    return next(destination.iterdir())


def tree_hash(directory):
    """SHA-256 over the relative paths and contents of every file (sorted)."""
    h = hashlib.sha256()
    for path in sorted(p for p in directory.rglob('*') if p.is_file()):
        h.update(path.relative_to(directory).as_posix().encode() + b'\0' + digest(path).encode() + b'\n')
    return h.hexdigest()


def compiler_version():
    try:
        return subprocess.check_output(['c++', '--version'], text=True).splitlines()[0]
    except (OSError, subprocess.CalledProcessError):
        return None


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--archive-cache', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--jobs', type=int, default=os.cpu_count() or 4)
    a = p.parse_args()
    a.output, a.archive_cache = a.output.resolve(), a.archive_cache.resolve()
    if a.output.exists() and any(a.output.iterdir()):
        raise SystemExit(f'{a.output} is not empty; use a new output directory')
    a.output.mkdir(parents=True, exist_ok=True)
    log = a.output / 'build.log'
    source = extract(fetch(a.archive_cache, LOCK['source'], 'sha256'), a.output / 'source')
    gmm = extract(fetch(a.archive_cache, LOCK['gmm'], 'sha224'), a.output / 'gmm')
    build = a.output / 'build'
    options = LOCK['options'] + ['-DFETCHCONTENT_SOURCE_DIR_GMM=' + str(gmm), '-DFETCHCONTENT_FULLY_DISCONNECTED=ON']
    run(['cmake', '-S', source, '-B', build] + options, log)
    run(['cmake', '--build', build, '--parallel', a.jobs, '--target'] + EXECUTABLES, log)
    runtime = a.output / 'runtime'
    runtime.mkdir()
    for name in EXECUTABLES:
        shutil.copy2(build / 'Build/bin' / name, runtime / RUNTIME_NAMES[name])
    shutil.copytree(source / 'config', runtime / 'config')
    shutil.copy2(source / 'LICENSE', runtime / 'LICENSE')
    upstream_config = ROOT / 'ThirdParty/quadwild-bimdf/config'
    receipt = {
        'schemaVersion': 1, 'component': 'quadwild-bimdf (PrePoMax fork)',
        'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
        'source': LOCK['source'], 'gmm': LOCK['gmm'], 'options': LOCK['options'],
        'host': {'os': platform.system(), 'machine': platform.machine(), 'release': platform.release()},
        'compiler': compiler_version(),
        'files': {name: digest(runtime / name) for name in list(RUNTIME_NAMES.values()) + ['LICENSE']},
        'config': {'sha256': tree_hash(runtime / 'config'),
                   'equalsUpstreamVendoredConfig': tree_hash(runtime / 'config') == tree_hash(upstream_config)},
        'scope': 'local build of the published source behind upstream 3.0.1 binaries; not a signed release',
    }
    (runtime / 'quadwild-build.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'success': True, 'runtime': str(runtime), 'files': receipt['files'],
                      'configEqualsUpstream': receipt['config']['equalsUpstreamVendoredConfig']}, indent=2))


if __name__ == '__main__':
    main()

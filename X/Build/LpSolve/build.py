#!/usr/bin/env python3
"""Build lp_solve 5.5.2.11 as the shared library GmshCaller and CaeMesh load for the interval assignment.

The original Windows lpsolve55.dll (ThirdParty/lpsolve) is built from the same lp_solve 5.5.2.11 sources with
lp_solve's own flags (lpsolve55/cvc8msvcrt.bat): the same 26 sources (no fortify.c) and defines. On macOS and
Linux the library is named lpsolve55.dll.dylib / lpsolve55.dll.so, the first name .NET probes for the
original DllImport("lpsolve55.dll"), and placed next to GmshCaller and the application assemblies.

    python3 X/Build/LpSolve/build.py --archive-cache /abs/cache --output /abs/new-output

The archive is downloaded into the cache when missing and always checked against source-lock.json.
"""
import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCK = json.loads((HERE / 'source-lock.json').read_text())
SOURCES = ['lp_MDO.c', 'shared/commonlib.c', 'shared/mmio.c', 'shared/myblas.c', 'ini.c', 'colamd/colamd.c', 'lp_rlp.c',
           'lp_crash.c', 'bfp/bfp_LUSOL/lp_LUSOL.c', 'bfp/bfp_LUSOL/LUSOL/lusol.c', 'lp_Hash.c', 'lp_lib.c', 'lp_wlp.c',
           'lp_matrix.c', 'lp_mipbb.c', 'lp_MPS.c', 'lp_params.c', 'lp_presolve.c', 'lp_price.c', 'lp_pricePSE.c',
           'lp_report.c', 'lp_scale.c', 'lp_simplex.c', 'lp_SOS.c', 'lp_utils.c', 'yacc_read.c']
DEFINES = ['-DYY_NEVER_INTERACTIVE', '-DPARSER_LP', '-DINVERSE_ACTIVE=INVERSE_LUSOL', '-DRoleIsExternalInvEngine',
           '-DINTEGERTIME']
INCLUDES = ['.', 'shared', 'bfp', 'bfp/bfp_LUSOL', 'bfp/bfp_LUSOL/LUSOL', 'colamd']


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--archive-cache', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--cc', default='cc')
    a = p.parse_args()
    if a.output.exists() and any(a.output.iterdir()):
        raise SystemExit(f'{a.output} is not empty; use a new output directory')
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
    src = work / 'lp_solve_5.5'
    system = platform.system()
    if system == 'Darwin':
        name, link = 'lpsolve55.dll.dylib', ['-dynamiclib', '-install_name', '@rpath/lpsolve55.dll.dylib',
                                             '-compatibility_version', '5.5.0', '-current_version', '5.5.0']
    elif system == 'Linux':
        name, link = 'lpsolve55.dll.so', ['-shared', '-Wl,-soname,lpsolve55.dll.so', '-ldl']
    else:
        raise SystemExit('Windows uses the vendored ThirdParty/lpsolve/lpsolve55.dll (build_lpsolve55.bat)')
    runtime = a.output / 'runtime'
    runtime.mkdir()
    command = [a.cc, '-O2', '-fPIC', '-fno-common', '-w'] + [f'-I{src / i}' for i in INCLUDES] + DEFINES + \
              [str(src / s) for s in SOURCES] + link + ['-lm', '-o', str(runtime / name)]
    subprocess.run(command, check=True)
    compiler = subprocess.run([a.cc, '--version'], capture_output=True, text=True).stdout.splitlines()[0]
    receipt = {'schemaVersion': 1, 'name': 'lp_solve', 'version': LOCK['version'], 'archiveSha256': LOCK['sha256'],
               'library': name, 'librarySha256': sha256(runtime / name), 'system': system,
               'machine': platform.machine(), 'compiler': compiler, 'command': command[:5] + ['...'],
               'sources': SOURCES, 'defines': DEFINES,
               'note': 'Same sources and defines as the original lpsolve55.dll (cvc8msvcrt.bat flags)'}
    (runtime / 'lpsolve-build.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'library': str(runtime / name), 'sha256': receipt['librarySha256']}))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Build the PaStiX stack of CalculiX 2.22 with 8-byte integers, as its README.INSTALL and make_*.sh describe:
OpenBLAS (INTERFACE64), hwloc, PaRSEC (the mfaverge fork), Scotch 6.0.8 (INTSIZE64), PaStiX4CalculiX (its CUDA-optional
branch). CUDA is left out (NVIDIA only); everything is static, so ccx links no new runtime library.

    python3 X/Build/Pastix/build.py --archive-cache /abs/cache --output /abs/new-output --jobs 8

The output's prefix/ holds the installed headers and static libraries for ThirdParty/Build/calculix-cpu.py
(--pastix), and each component's license texts in prefix/licenses. Archives are checked against source-lock.json; the git sources are checked by commit and tree.
--resume continues an interrupted output (development only; a release build starts from an empty output).
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
# 2019-era C under GCC 14+ (C23 by default since GCC 15): these were warnings when the sources were written
LEGACY_C = '-O2 -std=gnu17 -fcommon -Wno-error=implicit-function-declaration -Wno-error=int-conversion ' \
           '-Wno-error=incompatible-pointer-types -Wno-error=implicit-int'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--archive-cache', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--jobs', type=int, default=4)
    p.add_argument('--cc', default='gcc-16' if platform.system() == 'Darwin' else 'gcc')
    p.add_argument('--cxx', default='g++-16' if platform.system() == 'Darwin' else 'g++')
    p.add_argument('--fc', default='gfortran')
    p.add_argument('--resume', action='store_true')
    a = p.parse_args()
    out = a.output.resolve()
    if out.exists() and any(out.iterdir()) and not a.resume:
        raise SystemExit(f'{out} is not empty; use a new output directory')
    cache = a.archive_cache.resolve()
    cache.mkdir(parents=True, exist_ok=True)
    prefix = out / 'prefix'
    prefix.mkdir(parents=True, exist_ok=True)
    darwin = platform.system() == 'Darwin'
    env = dict(os.environ, ZERO_AR_DATE='1')
    if darwin:   # bison 2.3 of macOS is too old for PaRSEC's grammar
        for tool in ('bison', 'flex'):
            brew = Path(f'/opt/homebrew/opt/{tool}/bin')
            if brew.is_dir():
                env['PATH'] = f'{brew}:{env["PATH"]}'
    receipt_path = out / 'receipt.json'
    receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else \
        {'schemaVersion': 1, 'system': platform.system(), 'machine': platform.machine(), 'integers': 'int64',
         'compilers': {}, 'components': {}}
    for name, tool in (('C', a.cc), ('C++', a.cxx), ('Fortran', a.fc)):
        receipt['compilers'][name] = subprocess.check_output([tool, '--version'], text=True).splitlines()[0]

    def run(command, cwd, extra=None):
        print('$', ' '.join(map(str, command)), flush=True)
        subprocess.run(list(map(str, command)), cwd=cwd, check=True, env=dict(env, **(extra or {})))

    def unpack(name):
        source = LOCK['sources'][name]
        work = out / ('source-' + name)
        if work.exists():
            shutil.rmtree(work)
        work.mkdir()
        if 'git' in source:
            mirror = cache / (name + '-' + hashlib.sha256(source['git'].encode()).hexdigest()[:12] + '.git')
            if not mirror.exists():
                run(['git', 'clone', '--bare', '--quiet', source['git'], mirror], cache)
            if subprocess.run(['git', '-C', mirror, 'cat-file', '-e', source['commit'] + '^{commit}']).returncode:
                run(['git', '-C', mirror, 'fetch', '--quiet', 'origin', '+refs/heads/*:refs/heads/*'], cache)
            tree = subprocess.check_output(['git', '-C', mirror, 'rev-parse', source['commit'] + '^{tree}'], text=True).strip()
            if tree != source['tree']:
                raise SystemExit(f'{name}: tree {tree} differs from source-lock.json')
            archive = subprocess.run(['git', '-C', mirror, 'archive', '--format=tar', source['commit']],
                                     check=True, capture_output=True).stdout
            subprocess.run(['tar', '-x', '-C', work], input=archive, check=True)
            receipt['components'][name] = {'commit': source['commit'], 'tree': tree}
            return work
        archive = cache / source['archive']
        if not archive.exists():
            print('downloading', source['url'], flush=True)
            urllib.request.urlretrieve(source['url'], archive)
        if sha256(archive) != source['sha256']:
            raise SystemExit(f'{archive}: SHA-256 differs from source-lock.json')
        with tarfile.open(archive) as tar:
            tar.extractall(work, filter='data')
        receipt['components'][name] = {'version': source['version'], 'sha256': source['sha256']}
        return next(work.iterdir())

    def licenses(name, src):
        target = prefix / 'licenses' / name
        target.mkdir(parents=True, exist_ok=True)
        for f in src.iterdir():
            if f.is_file() and f.name.upper().startswith(('LICEN', 'COPYING', 'GOTOBLAS_00LICENSE')):
                shutil.copy2(f, target / f.name)
        assert any(target.iterdir()), f'{name}: no license text found'

    def step(name, build):
        marker = out / f'.done-{name}'
        if marker.exists():
            print(f'[{name}] done before', flush=True)
            return
        print(f'[{name}] building', flush=True)
        src = unpack(name)
        build(src)
        licenses(name, src)
        marker.write_text('')
        receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')

    def openblas(src):
        # Sequential BLAS with locking: PaStiX runs its own threads and calls BLAS from them
        options = [f'CC={a.cc}', f'FC={a.fc}', 'INTERFACE64=1', 'USE_THREAD=0', 'USE_OPENMP=0', 'USE_LOCKING=1',
                   'NO_SHARED=1', 'NO_CBLAS=0', 'NO_LAPACKE=0']
        options += ['TARGET=VORTEX'] if darwin else ['DYNAMIC_ARCH=1', 'TARGET=GENERIC' if platform.machine() == 'aarch64' else 'TARGET=HASWELL']
        run(['make', f'-j{a.jobs}', 'libs', 'netlib'] + options, src)
        run(['make', 'install', f'PREFIX={prefix}'] + options, src)
        receipt['components']['openblas']['options'] = options

    def hwloc(src):
        options = ['--enable-static', '--disable-shared', '--disable-libxml2', '--disable-cairo', '--disable-opencl',
                   '--disable-cuda', '--disable-nvml', '--disable-gl', '--disable-pci', '--disable-libudev',
                   '--disable-rsmi', '--disable-levelzero', f'CC={a.cc}', f'CXX={a.cxx}', 'CFLAGS=-O2']
        if darwin:   # hwloc 2.1.0's config.guess predates Apple Silicon
            options += ['--build=aarch64-apple-darwin']
        run(['./configure', f'--prefix={prefix}'] + options, src)
        run(['make', f'-j{a.jobs}'], src)
        run(['make', 'install'], src)
        receipt['components']['hwloc']['options'] = options

    def scotch(src):
        s = src / 'src'
        template = 'Make.inc/Makefile.inc.i686_mac_darwin10' if darwin else 'Make.inc/Makefile.inc.x86-64_pc_linux2'
        text = (s / template).read_text()
        lines = []
        for line in text.splitlines():
            key = line.split('=')[0].strip()
            if key in ('CCS', 'CCP', 'CCD'):
                line = f'{key}\t\t= {a.cc}'
            elif key == 'CFLAGS':   # make_scotch.sh: -DINTSIZE64 appended to the template's flags
                line = line.replace('-m32', '').replace('-arch i386', '') + ' -DINTSIZE64 ' + LEGACY_C
            elif key == 'LDFLAGS':
                line = line.replace('-m32', '').replace('-arch i386', '')
            lines.append(line)
        (s / 'Makefile.inc').write_text('\n'.join(lines) + '\n')
        receipt['components']['scotch']['makefile'] = {'template': template, 'sha256': sha256(s / 'Makefile.inc')}
        run(['make', 'scotch'], s)   # its recursive makefiles are not parallel-safe
        run(['make', 'esmumps'], s)
        run(['make', f'prefix={prefix}', 'install'], s)

    def parsec(src):
        # make_parsec.sh's fix: bindthread returns the core when it cannot bind (macOS has no thread binding)
        bind = src / 'parsec/bindthread.c'
        text = bind.read_text()
        assert text.count('-1 == cpu') >= 1
        index = text.index('-1 == cpu')
        line_start = text.rfind('\n', 0, index) + 1
        bind.write_text(text[:line_start] + 'return cpu;\n' + text[line_start:])
        receipt['components']['parsec']['patches'] = ['parsec/bindthread.c: return cpu; before the first -1 == cpu (make_parsec.sh)']
        options = ['-DCMAKE_BUILD_TYPE=Release', f'-DCMAKE_C_COMPILER={a.cc}', f'-DCMAKE_CXX_COMPILER={a.cxx}',
                   f'-DCMAKE_Fortran_COMPILER={a.fc}', f'-DCMAKE_INSTALL_PREFIX={prefix}', f'-DHWLOC_DIR={prefix}',
                   '-DBUILD_SHARED_LIBS=OFF', '-DPARSEC_GPU_WITH_CUDA=OFF', '-DPARSEC_DIST_WITH_MPI=OFF',
                   '-DSUPPORT_FORTRAN=OFF', '-DBUILD_DPLASMA=OFF', '-DBUILD_TESTING=OFF', '-DPARSEC_PROF_TRACE=OFF',
                   '-DCMAKE_POLICY_VERSION_MINIMUM=3.5', f'-DCMAKE_C_FLAGS={LEGACY_C}', '-DCMAKE_DISABLE_FIND_PACKAGE_MPI=ON',
                   '-DCMAKE_DISABLE_FIND_PACKAGE_PAPI=ON', '-DCMAKE_DISABLE_FIND_PACKAGE_CUDA=ON',
                   '-DCMAKE_DISABLE_FIND_PACKAGE_GTG=ON', '-DCMAKE_DISABLE_FIND_PACKAGE_AYUDAME=ON']
        run(['cmake', '-S', src, '-B', out / 'build-parsec'] + options, out)
        run(['cmake', '--build', out / 'build-parsec', '--parallel', a.jobs], out)
        run(['cmake', '--install', out / 'build-parsec'], out)
        # PaRSEC's 16-byte atomics need GCC's libatomic, which PaStiX's PaRSEC finder does not add: its objects go into
        # the static libparsec.a, which then links on its own
        atomic = subprocess.check_output([a.cc, '-print-file-name=libatomic.a'], text=True).strip()
        objects = out / 'libatomic-objects'
        shutil.rmtree(objects, ignore_errors=True)
        objects.mkdir()
        run(['ar', 'x', atomic], objects)
        run(['ar', 'r', prefix / 'lib/libparsec.a'] + sorted(p.name for p in objects.iterdir() if p.suffix == '.o'), objects)
        run(['ranlib', prefix / 'lib/libparsec.a'], objects)
        receipt['components']['parsec']['libatomic'] = {'path': atomic, 'sha256': sha256(atomic)}
        # PaStiX4CalculiX includes parsec/utils/zone_malloc.h (for code it has commented out), which PaRSEC does not
        # install; the header needs only parsec_config.h
        shutil.copy2(src / 'parsec/utils/zone_malloc.h', prefix / 'include/parsec/utils/zone_malloc.h')
        receipt['components']['parsec']['options'] = options

    def pastix(src):
        # Its linker flags replace the caller's, so they are appended to them instead (the static OpenBLAS's LAPACK
        # needs the Fortran runtime in the configure checks); its archiver is a fixed 'gcc-ar', CMake's own is used
        cmake = src / 'CMakeLists.txt'
        text = cmake.read_text()
        patched = text.replace('SET(CMAKE_EXE_LINKER_FLAGS " -lstdc++', 'SET(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -lstdc++') \
                      .replace('SET(CMAKE_AR  "gcc-ar")', '# SET(CMAKE_AR  "gcc-ar")')
        assert '-march=native' not in text and '/yaprod/' not in text and '\nSET(CMAKE_AR  "gcc-ar")' not in patched \
            and '"${CMAKE_EXE_LINKER_FLAGS} -lstdc++' in patched
        cmake.write_text(patched)
        # The precision generator imports Python's imp module (removed in 3.12) and does not use it
        generator = src / 'cmake_modules/morse_cmake/modules/precision_generator/genDependencies.py'
        text = generator.read_text()
        assert text.count('import imp;\n') == 1
        generator.write_text(text.replace('import imp;\n', ''))
        # Python 3.7+ rejects unknown escapes in a re.sub replacement: '#\\s*define' is a pattern only, as a
        # replacement it means '#define'
        for name in ('Conversion.py', 'genDependencies.py'):
            path = src / 'cmake_modules/morse_cmake/modules/precision_generator' / name
            text = path.read_text()
            anchor = "        data = re.sub(search, replace, data);"
            assert text.count(anchor) == 1
            path.write_text(text.replace(anchor, "        replace = replace.replace('\\\\s*', '');\n" + anchor))
        receipt['components']['pastix']['patches'] = [
            'CMakeLists.txt: CMAKE_EXE_LINKER_FLAGS appended to, not replaced; the fixed CMAKE_AR gcc-ar left to CMake',
            'precision_generator/genDependencies.py: the unused import of imp removed (Python 3.12+)',
            'precision_generator/Conversion.py, genDependencies.py: \\s* dropped from replacements (Python 3.7+)',
            'include/ and spm/include/ cblas.h, lapacke.h forward to OpenBLAS ILP64 headers (were 32-bit reference headers)']
        # Its bundled reference cblas.h and lapacke.h declare 32-bit int arguments and shadow OpenBLAS's ILP64 headers:
        # a mismatch at every BLAS/LAPACKE call (on Apple ARM64 stack arguments are not widened, cblas_?ger's lda
        # arrives as garbage). Each becomes a forward to the next header of that name on the include path, OpenBLAS's.
        for header in ('include/cblas.h', 'include/lapacke.h', 'spm/include/cblas.h', 'spm/include/lapacke.h'):
            (src / header).write_text(f'/* PrePoMax-X: OpenBLAS ILP64 header instead of the 32-bit reference one */\n'
                                      f'#include_next <{Path(header).name}>\n')
        # OpenBLAS carries LAPACKE; the finder looks for a library of that name
        lapacke = prefix / 'lib/liblapacke.a'
        if not lapacke.exists():
            lapacke.symlink_to('libopenblas.a')
        fortran_lib = Path(subprocess.check_output([a.fc, '-print-file-name=libgfortran.a'], text=True).strip()).parent
        options = ['-DCMAKE_BUILD_TYPE=Release', f'-DCMAKE_C_COMPILER={a.cc}', f'-DCMAKE_CXX_COMPILER={a.cxx}',
                   f'-DCMAKE_Fortran_COMPILER={a.fc}', f'-DCMAKE_INSTALL_PREFIX={prefix}', f'-DBLAS_DIR={prefix}',
                   f'-DLAPACKE_DIR={prefix}', f'-DCBLAS_DIR={prefix}', f'-DTMG_DIR={prefix}', '-DBLA_VENDOR=Open',
                   f'-DCMAKE_EXE_LINKER_FLAGS=-L{fortran_lib} -lgfortran',
                   f'-DHWLOC_DIR={prefix}', f'-DPARSEC_DIR={prefix}', f'-DSCOTCH_DIR={prefix}',
                   '-DPASTIX_WITH_PARSEC=ON', '-DPASTIX_WITH_CUDA=OFF', '-DPASTIX_ORDERING_SCOTCH=ON',
                   '-DPASTIX_INT64=ON', '-DBUILD_SHARED_LIBS=OFF', '-DPASTIX_WITH_FORTRAN=OFF', '-DPASTIX_WITH_MPI=OFF',
                   '-DCMAKE_POLICY_VERSION_MINIMUM=3.5',
                   # OpenBLAS's lapacke_config.h takes 32-bit lapack_int unless LAPACK_ILP64 is defined; the library is ILP64
                   f'-DCMAKE_C_FLAGS=-fopenmp -DLAPACK_ILP64 {LEGACY_C}',
                   '-DCMAKE_DISABLE_FIND_PACKAGE_MPI=ON', '-DBUILD_TESTING=OFF']
        run(['cmake', '-S', src, '-B', out / 'build-pastix'] + options, out)
        run(['cmake', '--build', out / 'build-pastix', '--parallel', a.jobs], out)
        run(['cmake', '--install', out / 'build-pastix'], out)
        receipt['components']['pastix']['options'] = options

    for name, build in (('openblas', openblas), ('hwloc', hwloc), ('scotch', scotch), ('parsec', parsec), ('pastix', pastix)):
        step(name, build)
    receipt['libraries'] = {p.name: sha256(p) for p in sorted((prefix / 'lib').glob('*.a'))}
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'prefix': str(prefix), 'libraries': sorted(receipt['libraries'])}, indent=2))


if __name__ == '__main__':
    main()

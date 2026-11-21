#!/usr/bin/env python3
"""Builds PrePoMax-X.app for macOS ARM64 (M3-1a): the original application (X/App) on the Avalonia front end, with no
PyQt and no installed .NET needed.

  python3 X/App/package_mac.py --p1 <PrePoMax-X.app of P1> --output DIR [--zip]

Contents/Resources:
  app/      X/App published self-contained for osx-arm64 (.NET runtime included), the vtkNative runtime, lp_solve,
            and the original Configure step (PrePoMaxX.Configure) that writes the runtime profile at first start
  python/   CPython 3.12 of P1 for the original's Python features, without PyQt6 and VTK's Python modules
  tools/    Netgen, Mmg, Gmsh and lib3mf of P1 (checked against its manifest), GmshCaller published self-contained,
            QuadWild from X/Build/artifacts/quadwild-mac-arm64
  solver/   the CalculiX build of the local app (X/Build/artifacts/solver-m2), its Homebrew libraries copied beside
            it and their load paths made relative (relocation.json records the original fingerprints)
  launch.py X/App/bundle_launch.py: clones app/ into ~/Library/Application Support/PrePoMax-X and configures it
  Licenses/ the license texts; NOTICE.md lists the components
The bundle is signed ad hoc (not notarized). --zip writes PrePoMax-X-macos-arm64.zip beside it (ditto).
"""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NUGET = Path.home() / '.nuget/packages'


MIT = """{0}

The MIT License (MIT)

{1}

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


def run(*command, **kw):
    print('+', ' '.join(str(c) for c in command), flush=True)
    subprocess.run([str(c) for c in command], check=True, **kw)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def macho(path):
    with open(path, 'rb') as f:
        return f.read(4) in (b'\xcf\xfa\xed\xfe', b'\xca\xfe\xba\xbe')


def dependencies(binary):
    lines = subprocess.run(['otool', '-L', str(binary)], capture_output=True, text=True, check=True).stdout.splitlines()[1:]
    return [l.strip().split(' (')[0] for l in lines]


def rpaths(binary):
    out = subprocess.run(['otool', '-l', str(binary)], capture_output=True, text=True, check=True).stdout.splitlines()
    return [out[i + 2].split('path ')[1].split(' (offset')[0] for i, l in enumerate(out) if 'LC_RPATH' in l]


def relocate_solver(source, target):
    """ccx and the non-system libraries it loads (recursively), side by side with relative load paths."""
    target.mkdir(parents=True)
    registry = json.loads((source / 'build-registry.json').read_text())
    build = registry['builds'][0]
    original = {'ccx': sha(source / 'bin/ccx'), **build.get('externalFiles', {})}
    shutil.copy2(source / 'bin/ccx', target / 'ccx')
    origin = {'ccx': (source / 'bin/ccx').resolve()}
    pending, done = [target / 'ccx'], set()

    def locate(dep, binary):
        # An absolute dependency is where it says; @rpath/@loader_path ones are found through the original's rpaths
        if dep.startswith('/'):
            return Path(dep).resolve()
        name = dep.split('/', 1)[1]
        here = origin[binary.name].parent
        for rp in rpaths(binary) + [str(here)]:
            folder = Path(rp.replace('@loader_path', str(here)).replace('@executable_path', str(here)))
            if (folder / name).exists():
                return (folder / name).resolve()
        raise SystemExit(f'{binary.name}: {dep} not found')

    while pending:
        binary = pending.pop()
        if binary.name in done:
            continue
        done.add(binary.name)
        for dep in dependencies(binary):
            if dep.startswith(('/usr/lib/', '/System/')) or dep.startswith('@loader_path/') and (target / Path(dep).name).exists():
                continue
            if dep == '@rpath/' + binary.name or Path(dep).name == binary.name:
                continue
            name = Path(dep).name
            local = target / name
            if not local.exists():
                origin[name] = locate(dep, binary)
                shutil.copy2(origin[name], local)
                local.chmod(0o755)
                run('install_name_tool', '-id', '@loader_path/' + name, local)
                pending.append(local)
            run('install_name_tool', '-change', dep, '@loader_path/' + name, binary)
    for binary in target.iterdir():
        for path in rpaths(binary):
            if path.startswith('/'):
                run('install_name_tool', '-delete_rpath', path, binary)
        run('codesign', '--force', '-s', '-', binary)
    files = {p.name: sha(p) for p in sorted(target.iterdir())}
    relocated = dict(build)
    relocated.pop('externalFiles', None)
    relocated.update({'id': build['id'] + '-bundle', 'files': files,
                      'scope': 'The build of the local app with its libraries relocated beside it; original backend unchanged'})
    (target.parent / 'build-registry.json').write_text(json.dumps({'schemaVersion': registry['schemaVersion'], 'builds': [relocated]}, indent=2) + '\n')
    (target.parent / 'relocation.json').write_text(json.dumps({'sourceBuild': build['id'], 'originalFiles': original,
                                                               'relocatedFiles': files}, indent=2) + '\n')
    return relocated['id']


def strip_absolute_rpaths(folder):
    """Load paths of the build machine (absolute LC_RPATH entries) are removed from every Mach-O file."""
    for path in folder.rglob('*'):
        if path.is_file() and not path.is_symlink() and macho(path):
            changed = False
            for rp in rpaths(path):
                if rp.startswith('/'):
                    run('install_name_tool', '-delete_rpath', rp, path)
                    changed = True
            if changed:
                run('codesign', '--force', '-s', '-', path)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--p1', type=Path, required=True, help='PrePoMax-X.app of P1 (Python, meshers, Gmsh, licenses)')
    p.add_argument('--solver', type=Path, default=ROOT / 'X/Build/artifacts/solver-m2/solver')
    p.add_argument('--vtk-native', type=Path, default=ROOT / 'X/Build/artifacts/vtk-mac-arm64/vtkNative/runtime')
    p.add_argument('--quadwild', type=Path, default=ROOT / 'X/Build/artifacts/quadwild-mac-arm64/runtime')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--zip', action='store_true')
    a = p.parse_args()
    p1 = a.p1.resolve() / 'Contents/Resources'
    package = json.loads((p1 / 'package.json').read_text())
    bundle = a.output.resolve() / 'PrePoMax-X.app'
    if bundle.exists():
        shutil.rmtree(bundle)
    res = bundle / 'Contents/Resources'
    app = res / 'app'
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()

    # The application, self-contained; the build machine's paths are mapped out of the assemblies
    publish = ['-c', 'Release', '-r', 'osx-arm64', '--self-contained', 'true', '-v:q', '-p:DebugType=none',
               f'-p:PathMap={ROOT}=/PrePoMax-X', f'-p:VtkNativeRuntime={a.vtk_native.resolve()}']
    run('dotnet', 'publish', ROOT / 'X/App/PrePoMax/PrePoMax.csproj', '-o', app, *publish)
    run('dotnet', 'publish', ROOT / 'X/App/Configure/Configure.csproj', '-o', app, *publish)
    for item in a.vtk_native.resolve().iterdir():
        if item.is_file() and not item.name.startswith('vtkControl.'):
            if (app / item.name).exists() or (app / item.name).is_symlink():
                (app / item.name).unlink()
            shutil.copy2(item, app / item.name, follow_symlinks=False)
    lpsolve = p1 / 'app' / package['components']['lpsolve']['file']
    if sha(lpsolve) != package['components']['lpsolve']['sha256']:
        raise SystemExit('lp_solve does not match the P1 manifest')
    shutil.copy2(lpsolve, app / lpsolve.name)
    shutil.copy2(app / 'PrePoMax', app / 'PrePoMax.com')
    for leftover in ('settings.bin', 'history.pmh', 'PrePoMaxX.runtime.json'):
        (app / leftover).unlink(missing_ok=True)

    # Python without PyQt6 and VTK's Python modules (the Avalonia front end needs neither)
    python = package['components']['python']
    shutil.copytree(p1 / 'python', res / 'python', symlinks=True, ignore=shutil.ignore_patterns(
        'PyQt6', 'pyqt6*', 'vtkmodules', 'vtk.py', 'vtk-*.dist-info', '__pycache__'))
    left = [n for n in (res / 'python/lib/python3.12/site-packages').iterdir() if n.name.lower().startswith(('pyqt', 'vtk'))]
    if left:
        raise SystemExit(f'PyQt/VTK left in Python: {left}')

    # Tools: P1's meshers and Gmsh (checked), GmshCaller and QuadWild from this repository
    tools = {}
    for ident, tool in package['tools'].items():
        if ident.endswith('GmshCaller.exe'):
            continue
        if sha(p1 / tool['path']) != tool['sha256']:
            raise SystemExit(f'{tool["path"]} does not match the P1 manifest')
        tools[ident] = {'path': tool['path'], 'sha256': tool['sha256']}
    for name in ('Netgen', 'Mmg', 'gmsh', 'lib3mf'):
        shutil.copytree(p1 / 'tools' / name, res / 'tools' / name, symlinks=True)
    run('dotnet', 'publish', ROOT / 'X/Domain/GmshCaller', '-o', res / 'tools/GmshCaller', *publish)
    shutil.copy2(lpsolve, res / 'tools/GmshCaller' / lpsolve.name)
    tools['\\lib\\GmshCaller.exe'] = {'path': 'tools/GmshCaller/GmshCaller', 'sha256': sha(res / 'tools/GmshCaller/GmshCaller')}
    shutil.copytree(a.quadwild.resolve(), res / 'tools/QuadWild')
    for exe in ('quadwild.exe', 'quad_from_patches.exe'):
        tools['\\Meshers\\QuadWild\\' + exe] = {'path': 'tools/QuadWild/' + exe, 'sha256': sha(res / 'tools/QuadWild' / exe)}
    gmsh = package['components']['gmsh']
    if sha(res / gmsh['file']) != gmsh['sha256']:
        raise SystemExit('Gmsh does not match the P1 manifest')

    # CalculiX: the local app's build, relocated
    solver_id = relocate_solver(a.solver.resolve(), res / 'solver/bin')

    # Licenses and notices
    shutil.copytree(p1 / 'Licenses', res / 'Licenses')
    shutil.copy2(ROOT / 'LICENSE', res / 'Licenses/PrePoMax-LICENSE')
    extra = {'dotnet': NUGET / 'microsoft.netcore.app.runtime.osx-arm64/10.0.14', 'skiasharp': NUGET / 'skiasharp/2.88.9',
             'harfbuzzsharp': NUGET / 'harfbuzzsharp/8.3.1.1'}
    for name, folder in extra.items():
        (res / 'Licenses' / name).mkdir()
        for f in folder.iterdir():
            if f.name.upper().startswith(('LICENSE', 'THIRD-PARTY')):
                shutil.copy2(f, res / 'Licenses' / name / f.name)
    (res / 'Licenses/avalonia').mkdir()
    (res / 'Licenses/avalonia/LICENSE.md').write_text(MIT.format('Avalonia 11.3.23 (github.com/AvaloniaUI/Avalonia)', 'Copyright (c) AvaloniaUI OÜ All Rights Reserved'))
    shutil.copy2(a.vtk_native.resolve() / 'VTK-Copyright.txt', res / 'Licenses/VTK-Copyright.txt')
    shutil.copy2(ROOT / 'X/App/bundle_NOTICE.md', res / 'NOTICE.md')

    # Launcher, manifest, Info.plist
    shutil.copy2(ROOT / 'X/App/bundle_launch.py', res / 'launch.py')
    build_id = revision[:12] + '-' + hashlib.sha256(b''.join(sha(f).encode() for f in sorted(app.rglob('*')) if f.is_file())).hexdigest()[:12]
    (res / 'bundle.json').write_text(json.dumps({
        'schemaVersion': 1, 'name': 'PrePoMax-X', 'target': 'osx-arm64', 'build': build_id, 'source': revision,
        'frontEnd': 'avalonia', 'python': {'version': python['version'], 'home': 'python', 'library': python['library'],
                                           'librarySha256': python['librarySha256'], 'moduleDirectories': python['moduleDirectories']},
        'tools': tools, 'gmsh': gmsh['file'],
        'solver': {'registry': 'solver/build-registry.json', 'id': solver_id, 'directory': 'solver/bin'},
        'missing': {'PARDISO': 'the Intel MKL PARDISO solver has no macOS ARM64 build (use SPOOLES)'},
    }, indent=2) + '\n')
    macos = bundle / 'Contents/MacOS'
    macos.mkdir(parents=True)
    (macos / 'PrePoMax-X').write_text('#!/bin/sh\nRES="$(cd "$(dirname "$0")/../Resources" && pwd)"\n'
                                      f'exec "$RES/{python["interpreter"]}" -I "$RES/launch.py" "$@"\n')
    (macos / 'PrePoMax-X').chmod(0o755)
    (bundle / 'Contents/Info.plist').write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleDisplayName</key><string>PrePoMax-X</string>
	<key>CFBundleExecutable</key><string>PrePoMax-X</string>
	<key>CFBundleIdentifier</key><string>org.prepomax-x.desktop</string>
	<key>CFBundleName</key><string>PrePoMax-X</string>
	<key>CFBundlePackageType</key><string>APPL</string>
	<key>CFBundleShortVersionString</key><string>3.0.1</string>
	<key>CFBundleVersion</key><string>3.0.1.{build_id}</string>
	<key>LSMinimumSystemVersion</key><string>13.0</string>
	<key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
''')
    # Build manifests carry the build machine's paths; the bundle's copies name them relative to the repository
    for manifest in bundle.rglob('*.json'):
        text = manifest.read_text(errors='ignore')
        if str(Path.home()) in text:
            manifest.write_text(text.replace(str(ROOT), 'PrePoMax-X').replace(str(Path.home()), '~'))
    strip_absolute_rpaths(bundle)
    run('codesign', '--force', '--deep', '-s', '-', bundle)
    print('Bundle:', bundle, subprocess.run(['du', '-sh', str(bundle)], capture_output=True, text=True).stdout.split()[0])
    if a.zip:
        archive = a.output.resolve() / 'PrePoMax-X-macos-arm64.zip'
        archive.unlink(missing_ok=True)
        run('ditto', '-c', '-k', '--keepParent', bundle, archive)
        print('Archive:', archive, archive.stat().st_size // (1024 * 1024), 'MiB', sha(archive))


if __name__ == '__main__':
    main()

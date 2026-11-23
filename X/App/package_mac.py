#!/usr/bin/env python3
"""Builds PrePoMax-X.app for macOS ARM64 (M3-1a): the original application (X/App) on the Avalonia front end, with no
PyQt and no installed .NET needed.

  python3 X/App/package_mac.py --p1 <PrePoMax-X.app of P1> --output DIR [--zip]

Contents/Resources:
  app/      X/App published self-contained for osx-arm64 (.NET runtime included), the vtkNative runtime, HiGHS,
            and the original Configure step (PrePoMaxX.Configure) that writes the runtime profile at first start
  python/   CPython 3.12 of P1 for the original's Python features, without PyQt6 and VTK's Python modules
  tools/    Netgen, Mmg, Gmsh and lib3mf of P1 (checked against its manifest), GmshCaller published self-contained,
            QuadWild from X/Build/artifacts/quadwild-mac-arm64
  solver/   the CalculiX build (ThirdParty/Build/calculix-cpu.py; --pastix: i8 with PaStiX, D070), its Homebrew libraries copied beside
            it and their load paths made relative (relocation.json records the original fingerprints)
  launch.py X/App/bundle_launch.py: clones app/ into ~/Library/Application Support/PrePoMax-X and configures it
  Licenses/ the license texts; NOTICE.md lists the components
The bundle is signed ad hoc (not notarized). --zip writes PrePoMax-X-macos-arm64.zip beside it (ditto).
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NUGET = Path.home() / '.nuget/packages'
# The .NET runtime the packages ship: the project's pin (X/Build/targets.json; without it the SDK takes the newest patch
# it can restore). The published output is checked against it (check_runtime)
DOTNET_RUNTIME = json.loads((ROOT / 'X/Build/targets.json').read_text())['runtimeFrameworkVersion']


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


def build_paths(folder):
    """Release gate: the files that still hold a path of this build host (sources compiled in by __FILE__, rpaths).
    A release requires none; the native recipes map them away when built through X/Build/build_ui.py."""
    # The repository's own folders, the home folder and a build workspace (PREPOMAXX_BUILD_WORKSPACE, the Linux build
    # kit); the repository root alone is too short in the build container (/src) and matches third-party strings
    paths = [ROOT / 'X', ROOT / 'ThirdParty', ROOT / 'CaeGlobals', ROOT / 'vtkNative', Path.home()]
    if os.environ.get('PREPOMAXX_BUILD_WORKSPACE'):
        paths.append(Path(os.environ['PREPOMAXX_BUILD_WORKSPACE']))
    needles = [(str(p) + '/').encode() for p in paths if len(str(p)) > 5]
    found = []
    for f in sorted(folder.rglob('*')):
        if f.is_file() and not f.is_symlink():
            data = f.read_bytes()
            if any(n in data for n in needles):
                found.append(f.relative_to(folder).as_posix())
    return found


def check_runtime(app, target):
    """The published application carries the pinned runtime pack."""
    deps = (app / 'PrePoMax.deps.json').read_text()
    if f'runtimepack.Microsoft.NETCore.App.Runtime.{target}/{DOTNET_RUNTIME}' not in deps:
        raise SystemExit(f'the published runtime is not .NET {DOTNET_RUNTIME}')


def copy_ui_resources(target):
    """The original images the front end reads at run time (FrontEnd.Bitmap/Named), at their repository-relative paths:
    the icon folders searched by name, and every image file and .resx named by the compiled designer code."""
    import re
    files = {ROOT / 'PrePoMax/main.ico'}
    for folder in ('PrePoMax/Icons', 'PrePoMax/Resources', 'UserControls/Resources'):
        files.update(p for p in (ROOT / folder).rglob('*') if p.is_file() and p.name != '.DS_Store')
    for base in (ROOT / 'X/UI/Workbench/OriginalForms', ROOT / 'X/App/Original'):
        for source in base.rglob('*.g.cs'):
            text = source.read_text(encoding='utf-8')
            for relative in re.findall(r'ResxResources\("([^"]+)"\)', text) + \
                    re.findall(r'ImageResource\("[^"]*", "([^"]+)"\)', text):
                files.add(ROOT / relative)
    missing = sorted(str(p.relative_to(ROOT)) for p in files if not p.is_file())
    if missing:
        raise SystemExit('UI resources missing: ' + ', '.join(missing[:10]))
    for path in sorted(files):
        destination = target / path.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
    print(f'UI resources: {len(files)} files')


def make_icns(icon, target, work):
    """The application icon from the original's main.ico (32x32, as the Windows build has it), scaled for the iconset."""
    iconset = work / 'PrePoMax-X.iconset'
    iconset.mkdir(parents=True)
    run('sips', '-s', 'format', 'png', icon, '--out', work / 'main.png', capture_output=True)
    for size in (16, 32, 128, 256, 512):
        for scale, suffix in ((1, ''), (2, '@2x')):
            run('sips', '-z', str(size * scale), str(size * scale), work / 'main.png',
                '--out', iconset / f'icon_{size}x{size}{suffix}.png', capture_output=True)
    run('iconutil', '-c', 'icns', iconset, '-o', target)
    shutil.rmtree(work)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--p1', type=Path, required=True, help='the native components: X/Build/package_ui.py output folder (or the P1 PrePoMax-X.app)')
    p.add_argument('--solver', type=Path, default=ROOT / 'X/Build/artifacts/solver-m2/solver')
    p.add_argument('--vtk-native', type=Path, default=ROOT / 'X/Build/artifacts/vtk-mac-arm64-302/vtkNative/runtime')
    p.add_argument('--highs', type=Path, default=ROOT / 'X/Build/artifacts/highs-mac-arm64/runtime/highs.dll.dylib',
                   help='HiGHS 1.16.0 from X/Build/Highs (3.0.2 replaced lp_solve by HiGHS)')
    p.add_argument('--netgen', type=Path, help='a NetGenMesher runtime of X/Build/NativeCad (bin, lib, licenses); '
                   'default: the one of --p1')
    p.add_argument('--original', type=Path, required=True,
                   help='the extracted PrePoMax 3.0.1 release (materials.lib, Models, Tools/abqodb_to_ccxfrd.py)')
    p.add_argument('--quadwild', type=Path, default=ROOT / 'X/Build/artifacts/quadwild-mac-arm64/runtime')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--zip', action='store_true')
    a = p.parse_args()
    # P1's PrePoMax-X.app (Contents/Resources) or a component folder of X/Build/package_ui.py
    p1 = a.p1.resolve() / 'Contents/Resources' if (a.p1 / 'Contents/Resources').is_dir() else a.p1.resolve()
    package = json.loads((p1 / 'package.json').read_text())
    bundle = a.output.resolve() / 'PrePoMax-X.app'
    if bundle.exists():
        shutil.rmtree(bundle)
    res = bundle / 'Contents/Resources'
    app = res / 'app'
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    # Uncommitted changes, before the publish rewrites the lock files (Finder's .DS_Store files do not count)
    dirty = bool(subprocess.run(['git', 'status', '--porcelain', '--untracked-files=no', '--', '.', ':!**/.DS_Store'],
                                cwd=ROOT, capture_output=True, text=True).stdout.strip())

    # The application, self-contained; the build machine's paths are mapped out of the assemblies
    publish = ['-c', 'Release', '-r', 'osx-arm64', '--self-contained', 'true', '-v:q', '-p:DebugType=none',
               f'-p:RuntimeFrameworkVersion={DOTNET_RUNTIME}',
               f'-p:PathMap={ROOT}=/PrePoMax-X', f'-p:VtkNativeRuntime={a.vtk_native.resolve()}']
    run('dotnet', 'publish', ROOT / 'X/App/PrePoMax/PrePoMax.csproj', '-o', app, *publish)
    run('dotnet', 'publish', ROOT / 'X/App/Configure/Configure.csproj', '-o', app, *publish)
    check_runtime(app, 'osx-arm64')
    for item in a.vtk_native.resolve().iterdir():
        if item.is_file() and not item.name.startswith('vtkControl.'):
            if (app / item.name).exists() or (app / item.name).is_symlink():
                (app / item.name).unlink()
            shutil.copy2(item, app / item.name, follow_symlinks=False)
    # HiGHS (3.0.2): beside the assemblies and GmshCaller, as the original PostBuildEvent places highs.dll
    highs = a.highs.resolve()
    highs_receipt = json.loads((highs.parent / 'highs-build.json').read_text())
    if highs_receipt['librarySha256'] != sha(highs):
        raise SystemExit('HiGHS does not match its build receipt')
    shutil.copy2(highs, app / highs.name)
    shutil.copy2(app / 'PrePoMax', app / 'PrePoMax.com')
    for leftover in ('settings.bin', 'history.pmh', 'PrePoMaxX.runtime.json'):
        (app / leftover).unlink(missing_ok=True)
    copy_ui_resources(app / 'resources')

    # The release's data files beside the original program, which the repository does not hold: the material library
    # (FrmMaterialLibrary reads StartupPath/materials.lib), the example models and the Abaqus ODB conversion script
    original = a.original.resolve()
    if not (original / 'PrePoMax.exe').is_file():
        raise SystemExit(f'{original} is not an extracted PrePoMax release')
    shutil.copy2(original / 'materials.lib', app / 'materials.lib')
    shutil.copytree(original / 'Models', app / 'Models')
    release_files = {str(f.relative_to(app)): sha(f) for f in [app / 'materials.lib', *sorted((app / 'Models').rglob('*'))] if f.is_file()}

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
        if ident.endswith('GmshCaller.exe') or (a.netgen and ident.endswith('NetGenMesher.exe')):
            continue
        if sha(p1 / tool['path']) != tool['sha256']:
            raise SystemExit(f'{tool["path"]} does not match the P1 manifest')
        tools[ident] = {'path': tool['path'], 'sha256': tool['sha256']}
    for name in ('Mmg', 'gmsh', 'lib3mf') + (() if a.netgen else ('Netgen',)):
        shutil.copytree(p1 / 'tools' / name, res / 'tools' / name, symlinks=True)
    if a.netgen:
        netgen = a.netgen.resolve()
        shutil.copytree(netgen, res / 'tools/Netgen', symlinks=True,
                        ignore=shutil.ignore_patterns('*.json', 'include', 'cmake'))
        tools['\\Meshers\\Netgen\\NetGenMesher.exe'] = {'path': 'tools/Netgen/bin/NetGenMesher',
                                                         'sha256': sha(res / 'tools/Netgen/bin/NetGenMesher')}
    run('dotnet', 'publish', ROOT / 'X/Domain/GmshCaller', '-o', res / 'tools/GmshCaller', *publish)
    shutil.copy2(highs, res / 'tools/GmshCaller' / highs.name)
    tools['\\lib\\GmshCaller.exe'] = {'path': 'tools/GmshCaller/GmshCaller', 'sha256': sha(res / 'tools/GmshCaller/GmshCaller')}
    shutil.copytree(a.quadwild.resolve(), res / 'tools/QuadWild')
    (res / 'tools/Tools').mkdir()
    shutil.copy2(original / 'Tools/abqodb_to_ccxfrd.py', res / 'tools/Tools/abqodb_to_ccxfrd.py')
    tools['\\Tools\\abqodb_to_ccxfrd.py'] = {'path': 'tools/Tools/abqodb_to_ccxfrd.py', 'sha256': sha(res / 'tools/Tools/abqodb_to_ccxfrd.py')}
    release_files['tools/Tools/abqodb_to_ccxfrd.py'] = tools['\\Tools\\abqodb_to_ccxfrd.py']['sha256']
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
    shutil.rmtree(res / 'Licenses/lpsolve', ignore_errors=True)   # 3.0.2 has no lp_solve
    shutil.copytree(ROOT / 'Licenses/highs', res / 'Licenses/highs')
    if (a.solver.resolve() / 'licenses').is_dir():   # the solver's static libraries (the PaStiX stack, D070)
        shutil.copytree(a.solver.resolve() / 'licenses', res / 'Licenses/solver')
    extra = {'dotnet': NUGET / f'microsoft.netcore.app.runtime.osx-arm64/{DOTNET_RUNTIME}', 'skiasharp': NUGET / 'skiasharp/2.88.9',
             'harfbuzzsharp': NUGET / 'harfbuzzsharp/8.3.1.1'}
    for name, folder in extra.items():
        (res / 'Licenses' / name).mkdir()
        for f in folder.iterdir():
            if f.name.upper().startswith(('LICENSE', 'THIRD-PARTY')):
                shutil.copy2(f, res / 'Licenses' / name / f.name)
    (res / 'Licenses/avalonia').mkdir()
    (res / 'Licenses/avalonia/LICENSE.md').write_text(MIT.format('Avalonia 11.3.23 (github.com/AvaloniaUI/Avalonia)', 'Copyright (c) AvaloniaUI OÜ All Rights Reserved'))
    shutil.copy2(a.vtk_native.resolve() / 'VTK-Copyright.txt', res / 'Licenses/VTK-Copyright.txt')
    (res / 'NOTICE.md').write_text((ROOT / 'X/App/bundle_NOTICE.md').read_text().replace('@DOTNET@', DOTNET_RUNTIME))

    # Launcher, manifest, Info.plist
    shutil.copy2(ROOT / 'X/App/bundle_launch.py', res / 'launch.py')
    make_icns(ROOT / 'PrePoMax/main.ico', res / 'PrePoMax-X.icns', a.output.resolve() / 'icon-work')
    build_id = revision[:12] + '-' + hashlib.sha256(b''.join(sha(f).encode() for f in sorted(app.rglob('*')) if f.is_file())).hexdigest()[:12]
    (res / 'bundle.json').write_text(json.dumps({
        'schemaVersion': 1, 'name': 'PrePoMax-X', 'target': 'osx-arm64', 'build': build_id, 'source': revision,
        'sourceDirty': dirty, 'buildPaths': build_paths(res),
        'frontEnd': 'avalonia', 'python': {'version': python['version'], 'home': 'python', 'library': python['library'],
                                           'librarySha256': python['librarySha256'], 'moduleDirectories': python['moduleDirectories']},
        'tools': tools, 'gmsh': gmsh['file'],
        'netgen': (json.loads((a.netgen.resolve() / 'build-receipt.json').read_text())['netgenRevision'] if a.netgen
                   else 'the NetGenMesher of --p1 (c5ecb0ba3782b91649e06823e858480f6fe33aeb)'),
        'highs': {'version': highs_receipt['version'], 'commit': highs_receipt['commit'], 'file': 'app/' + highs.name},
        'solver': {'registry': 'solver/build-registry.json', 'id': solver_id, 'directory': 'solver/bin'},
        'release': {'version': '3.0.1', 'note': 'materials.lib, Models and Tools of the latest release (3.0.2 has none yet)',
                    'files': release_files},
        'missing': {'PARDISO': 'the Intel MKL PARDISO solver has no macOS ARM64 build (use PaStiX or SPOOLES)',
                    'BidirectionalMeshConverter': 'Tools/BidirectionalMeshConverter.exe of the release is a Windows-only '
                                                  'third-party build without public source (B021)'},
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
	<key>CFBundleIconFile</key><string>PrePoMax-X</string>
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
    # Every fingerprint the runtime checks still holds after relocation and signing
    changed = [ident for ident, tool in tools.items() if sha(res / tool['path']) != tool['sha256']]
    changed += [gmsh['file']] if sha(res / gmsh['file']) != gmsh['sha256'] else []
    changed += [python['library']] if sha(res / python['library']) != python['librarySha256'] else []
    if changed:
        raise SystemExit(f'fingerprinted files changed while packaging: {changed}')
    print('Bundle:', bundle, subprocess.run(['du', '-sh', str(bundle)], capture_output=True, text=True).stdout.split()[0])
    if a.zip:
        archive = a.output.resolve() / 'PrePoMax-X-macos-arm64.zip'
        archive.unlink(missing_ok=True)
        run('ditto', '-c', '-k', '--keepParent', bundle, archive)
        print('Archive:', archive, archive.stat().st_size // (1024 * 1024), 'MiB', sha(archive))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Builds PrePoMax-X for Linux (M3-1b): the original application (X/App) on the Avalonia front end (X11), with no
PyQt and no installed .NET needed. Same contents as the macOS bundle (package_mac.py), as a folder and tar.gz:

  python3 X/App/package_linux.py --p1 <P1 PrePoMax-X-linux-arm64.tar.gz> --original <PrePoMax 3.0.1 release>
      --output DIR [--target linux-arm64] [--archive]

PrePoMax-X/
  PrePoMax-X   the launcher (sh): runs launch.py with the bundled CPython
  launch.py    X/App/bundle_launch.py: clones app/ into ~/.local/share/PrePoMax-X and configures it
  app/         X/App published self-contained for the target (.NET runtime included), the vtkNative runtime,
               lp_solve, the original's resources, help and release data, and the original Configure step
  python/      CPython 3.12 of P1, without PyQt6 and VTK's Python modules
  tools/       Netgen, Mmg, Gmsh and lib3mf of P1 (checked against its manifest), GmshCaller published from this
               repository, QuadWild (X/Build/QuadWild for the target), the ODB conversion script of the release
  solver/      the P1 CalculiX build with its libraries (relocated by P1; checked against its manifest)
  share/       a desktop entry and the application icon
  Licenses/, NOTICE.md, bundle.json
The native libraries' build-machine run paths are removed in the build container (X/Build/Linux/strip_rpaths.py,
patchelf). --archive writes PrePoMax-X-<target>.tar.gz beside the folder.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile
from pathlib import Path

from package_mac import DOTNET_RUNTIME, MIT, NUGET, ROOT, check_runtime, copy_ui_resources, run, sha

BUILD_IMAGE = 'prepomax-x-build:24.04'


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--p1', type=Path, required=True, help='the native components of the target: X/Build/package_ui.py --format tar.gz (or the P1 Linux tar.gz)')
    p.add_argument('--original', type=Path, required=True,
                   help='the extracted PrePoMax 3.0.1 release (materials.lib, Models, Tools/abqodb_to_ccxfrd.py)')
    p.add_argument('--target', default='linux-arm64', choices=('linux-arm64', 'linux-x64'))
    p.add_argument('--vtk-native', type=Path, default=ROOT / 'X/Build/artifacts/vtknative-linux-arm64-m3/vtkNative/runtime')
    p.add_argument('--quadwild', type=Path, default=ROOT / 'X/Build/artifacts/quadwild-linux-arm64/runtime')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--archive', action='store_true')
    a = p.parse_args()
    output = a.output.resolve()
    work = output / 'p1'
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    # Python's terminal database (share/terminfo) has names that differ only in case, which a case-insensitive
    # macOS volume cannot hold; PrePoMax runs Python scripts, never an interactive terminal, so it is left out
    with tarfile.open(a.p1) as archive:
        members = [m for m in archive.getmembers() if '/python/share/terminfo' not in m.name]
        archive.extractall(work, members=members, filter='tar')
    p1 = work / 'PrePoMax-X'
    package = json.loads((p1 / 'package.json').read_text())
    if package['target'] != a.target:
        raise SystemExit(f'the P1 package is for {package["target"]}, not {a.target}')
    root = output / 'PrePoMax-X'
    if root.exists():
        shutil.rmtree(root)
    app = root / 'app'
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()

    # The application, self-contained; the build machine's paths are mapped out of the assemblies
    publish = ['-c', 'Release', '-r', a.target, '--self-contained', 'true', '-v:q', '-p:DebugType=none',
               f'-p:RuntimeFrameworkVersion={DOTNET_RUNTIME}',
               f'-p:PathMap={ROOT}=/PrePoMax-X', f'-p:VtkNativeRuntime={a.vtk_native.resolve()}']
    run('dotnet', 'publish', ROOT / 'X/App/PrePoMax/PrePoMax.csproj', '-o', app, *publish)
    run('dotnet', 'publish', ROOT / 'X/App/Configure/Configure.csproj', '-o', app, *publish)
    check_runtime(app, a.target)
    for item in a.vtk_native.resolve().iterdir():
        if item.is_file() and not item.name.startswith('vtkControl.'):
            if (app / item.name).exists() or (app / item.name).is_symlink():
                (app / item.name).unlink()
            shutil.copy2(item, app / item.name, follow_symlinks=False)
    lpsolve = p1 / 'app' / package['components']['lpsolve']['file']
    if sha(lpsolve) != package['components']['lpsolve']['sha256']:
        raise SystemExit('lp_solve does not match the P1 manifest')
    shutil.copy2(lpsolve, app / lpsolve.name)
    # The original's console entry (PrePoMax.com, upstream's PrePoMaxCmd) is the same executable here
    shutil.copy2(app / 'PrePoMax', app / 'PrePoMax.com')
    for leftover in ('settings.bin', 'history.pmh', 'PrePoMaxX.runtime.json'):
        (app / leftover).unlink(missing_ok=True)
    copy_ui_resources(app / 'resources')

    # The release's data files beside the original program (as in package_mac.py)
    original = a.original.resolve()
    if not (original / 'PrePoMax.exe').is_file():
        raise SystemExit(f'{original} is not an extracted PrePoMax release')
    shutil.copy2(original / 'materials.lib', app / 'materials.lib')
    shutil.copytree(original / 'Models', app / 'Models')
    release_files = {str(f.relative_to(app)): sha(f) for f in [app / 'materials.lib', *sorted((app / 'Models').rglob('*'))] if f.is_file()}

    # Python without PyQt6 and VTK's Python modules
    python = package['components']['python']
    shutil.copytree(p1 / 'python', root / 'python', symlinks=True, ignore=shutil.ignore_patterns(
        'PyQt6', 'pyqt6*', 'vtkmodules', 'vtk.py', 'vtk-*.dist-info', 'vtk.libs', '__pycache__'))
    left = [n for n in (root / 'python/lib/python3.12/site-packages').iterdir() if n.name.lower().startswith(('pyqt', 'vtk'))]
    if left:
        raise SystemExit(f'PyQt/VTK left in Python: {left}')
    if sha(root / python['library']) != python['librarySha256']:
        raise SystemExit('libpython does not match the P1 manifest')

    # Tools: P1's meshers and Gmsh (checked), GmshCaller, QuadWild and the ODB script
    tools = {}
    for ident, tool in package['tools'].items():
        if ident.endswith('GmshCaller.exe'):
            continue
        if sha(p1 / tool['path']) != tool['sha256']:
            raise SystemExit(f'{tool["path"]} does not match the P1 manifest')
        tools[ident] = {'path': tool['path'], 'sha256': tool['sha256']}
    for name in ('Netgen', 'Mmg', 'gmsh', 'lib3mf'):
        shutil.copytree(p1 / 'tools' / name, root / 'tools' / name, symlinks=True)
    run('dotnet', 'publish', ROOT / 'X/Domain/GmshCaller', '-o', root / 'tools/GmshCaller', *publish)
    shutil.copy2(lpsolve, root / 'tools/GmshCaller' / lpsolve.name)
    tools['\\lib\\GmshCaller.exe'] = {'path': 'tools/GmshCaller/GmshCaller', 'sha256': sha(root / 'tools/GmshCaller/GmshCaller')}
    quadwild = json.loads((a.quadwild.resolve() / 'quadwild-build.json').read_text())
    shutil.copytree(a.quadwild.resolve(), root / 'tools/QuadWild', symlinks=True)
    for exe in ('quadwild.exe', 'quad_from_patches.exe'):
        tools['\\Meshers\\QuadWild\\' + exe] = {'path': 'tools/QuadWild/' + exe, 'sha256': sha(root / 'tools/QuadWild' / exe)}
    (root / 'tools/Tools').mkdir()
    shutil.copy2(original / 'Tools/abqodb_to_ccxfrd.py', root / 'tools/Tools/abqodb_to_ccxfrd.py')
    tools['\\Tools\\abqodb_to_ccxfrd.py'] = {'path': 'tools/Tools/abqodb_to_ccxfrd.py', 'sha256': sha(root / 'tools/Tools/abqodb_to_ccxfrd.py')}
    release_files['tools/Tools/abqodb_to_ccxfrd.py'] = tools['\\Tools\\abqodb_to_ccxfrd.py']['sha256']
    gmsh = package['components']['gmsh']
    if sha(root / gmsh['file']) != gmsh['sha256']:
        raise SystemExit('Gmsh does not match the P1 manifest')

    # CalculiX: P1's relocated build, checked file by file against P1's manifest
    shutil.copytree(p1 / 'solver', root / 'solver', symlinks=True)
    for name, digest in package['solverRelocation']['relocatedFiles'].items():
        if sha(root / 'solver/bin' / name) != digest:
            raise SystemExit(f'solver/bin/{name} does not match the P1 manifest')
    solver_id = json.loads((root / 'solver/build-registry.json').read_text())['builds'][0]['id']

    # Licenses and notices
    shutil.copytree(p1 / 'Licenses', root / 'Licenses')
    shutil.copy2(ROOT / 'LICENSE', root / 'Licenses/PrePoMax-LICENSE')
    extra = {'dotnet': NUGET / f'microsoft.netcore.app.runtime.{a.target}/{DOTNET_RUNTIME}', 'skiasharp': NUGET / 'skiasharp/2.88.9',
             'harfbuzzsharp': NUGET / 'harfbuzzsharp/8.3.1.1'}
    for name, folder in extra.items():
        (root / 'Licenses' / name).mkdir()
        for f in folder.iterdir():
            if f.name.upper().startswith(('LICENSE', 'THIRD-PARTY')):
                shutil.copy2(f, root / 'Licenses' / name / f.name)
    (root / 'Licenses/avalonia').mkdir()
    (root / 'Licenses/avalonia/LICENSE.md').write_text(MIT.format('Avalonia 11.3.23 (github.com/AvaloniaUI/Avalonia)', 'Copyright (c) AvaloniaUI OÜ All Rights Reserved'))
    shutil.copy2(a.vtk_native.resolve() / 'VTK-Copyright.txt', root / 'Licenses/VTK-Copyright.txt')
    notice = (ROOT / 'X/App/bundle_NOTICE.md').read_text().replace('@DOTNET@', DOTNET_RUNTIME)
    notice = notice.replace('macOS ARM64', a.target).replace('macOS (Apple Silicon)', 'Linux (' + a.target + ')') \
        .replace('`~/Library/Application Support/PrePoMax-X`', '`~/.local/share/PrePoMax-X`')
    (root / 'NOTICE.md').write_text(notice)

    # Desktop entry and icon (the original main.ico, 32x32 as on Windows; the .ico is read by desktops directly)
    share = root / 'share'
    share.mkdir()
    shutil.copy2(ROOT / 'PrePoMax/main.ico', share / 'PrePoMax-X.ico')
    (share / 'PrePoMax-X.desktop').write_text(
        '[Desktop Entry]\nType=Application\nName=PrePoMax-X\nComment=Pre- and post-processor for CalculiX\n'
        'Exec=@ROOT@/PrePoMax-X %f\nIcon=@ROOT@/share/PrePoMax-X.ico\nTerminal=false\nCategories=Science;Engineering;\n')
    installer = share / 'install-desktop-entry.sh'
    installer.write_text('#!/bin/sh\n# Adds PrePoMax-X to the desktop menu of this user (where the folder is now; run again after moving it)\n'
                         'ROOT="$(cd "$(dirname "$0")/.." && pwd)"\n'
                         'DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"\nmkdir -p "$DIR"\n'
                         'sed "s|@ROOT@|$ROOT|g" "$ROOT/share/PrePoMax-X.desktop" > "$DIR/PrePoMax-X.desktop"\n'
                         'echo "Installed $DIR/PrePoMax-X.desktop"\n')
    installer.chmod(0o755)

    # Launcher and manifest
    shutil.copy2(ROOT / 'X/App/bundle_launch.py', root / 'launch.py')
    build_id = revision[:12] + '-' + hashlib.sha256(b''.join(sha(f).encode() for f in sorted(app.rglob('*')) if f.is_file())).hexdigest()[:12]
    (root / 'bundle.json').write_text(json.dumps({
        'schemaVersion': 1, 'name': 'PrePoMax-X', 'target': a.target, 'build': build_id, 'source': revision,
        'frontEnd': 'avalonia', 'python': {'version': python['version'], 'home': 'python', 'library': python['library'],
                                           'librarySha256': python['librarySha256'], 'moduleDirectories': python['moduleDirectories']},
        'tools': tools, 'gmsh': gmsh['file'],
        'solver': {'registry': 'solver/build-registry.json', 'id': solver_id, 'directory': 'solver/bin'},
        'quadwild': {'repository': quadwild['source']['repository'], 'revision': quadwild['source']['revision']},
        'release': {'version': '3.0.1', 'files': release_files},
        'omitted': {'python/share/terminfo': 'the terminal database of CPython (interactive curses/readline only)'},
        'missing': {'PARDISO': f'the Intel MKL PARDISO solver has no {a.target} build (use SPOOLES)',
                    'BidirectionalMeshConverter': 'Tools/BidirectionalMeshConverter.exe of the release is Windows-only'},
    }, indent=2) + '\n')
    launcher = root / 'PrePoMax-X'
    launcher.write_text('#!/bin/sh\nHERE="$(cd "$(dirname "$0")" && pwd)"\n'
                        f'exec "$HERE/{python["interpreter"]}" -I "$HERE/launch.py" "$@"\n')
    launcher.chmod(0o755)
    for manifest in root.rglob('*.json'):
        text = manifest.read_text(errors='ignore')
        if str(Path.home()) in text:
            manifest.write_text(text.replace(str(ROOT), 'PrePoMax-X').replace(str(Path.home()), '~'))
    shutil.rmtree(work)

    # Build-machine run paths out of this repository's ELF builds (patchelf in the build container); P1's checked
    # files keep their fingerprints
    run('podman', 'run', '--rm', '-v', f'{root}:/package', '-v', f'{ROOT / "X/Build/Linux"}:/tools:ro', BUILD_IMAGE,
        'python3', '/tools/strip_rpaths.py', '/package/app', '/package/tools/QuadWild')
    # Every fingerprint the runtime checks still holds after the packaging steps
    changed = [ident for ident, tool in tools.items() if sha(root / tool['path']) != tool['sha256']]
    changed += [gmsh['file']] if sha(root / gmsh['file']) != gmsh['sha256'] else []
    changed += [python['library']] if sha(root / python['library']) != python['librarySha256'] else []
    changed += [name for name, digest in package['solverRelocation']['relocatedFiles'].items() if sha(root / 'solver/bin' / name) != digest]
    if changed:
        raise SystemExit(f'fingerprinted files changed while packaging: {changed}')
    print('Package:', root, subprocess.run(['du', '-sh', str(root)], capture_output=True, text=True).stdout.split()[0])
    if a.archive:
        target = output / f'PrePoMax-X-{a.target}.tar.gz'
        target.unlink(missing_ok=True)
        with tarfile.open(target, 'w:gz') as archive:
            archive.add(root, arcname='PrePoMax-X', filter=lambda i: (setattr(i, 'uid', 0), setattr(i, 'gid', 0),
                                                                       setattr(i, 'uname', ''), setattr(i, 'gname', ''), i)[-1])
        print('Archive:', target, target.stat().st_size // (1024 * 1024), 'MiB', sha(target))


if __name__ == '__main__':
    main()

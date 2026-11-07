"""Mac app/DMG packaging; shared engineering publication stays in build.py."""
import json
from pathlib import Path
import shutil
import subprocess
import sys


def dependencies(path):
    return [line.strip().split(' (', 1)[0] for line in subprocess.check_output(['otool', '-L', path], text=True).splitlines()[1:]]


def system_library(path):
    return path.startswith(('/usr/lib/', '/System/'))


def bundle_solver(build, root, source, destination):
    """Relocate only an explicitly verified native build; never choose a replacement."""
    from build import sha
    report = json.loads((source / 'build-report.json').read_text())
    registry = json.loads((source / 'build-registry.json').read_text())
    if not report.get('success') or report.get('target') != 'osx-arm64' or len(registry['builds']) != 1:
        raise ValueError('A successful pinned native Mac solver build is required')
    profile = registry['builds'][0]
    if profile['os'] != 'Darwin' or profile['architecture'] != 'Arm64' or profile['executable'] != 'ccx':
        raise ValueError('Wrong solver profile target')
    if (report.get('version') != profile['version'] or
            report.get('executableSha256') != profile['files'].get('ccx') or
            report.get('externalRuntimes') != profile['externalFiles'] or
            report.get('backend') != profile.get('backend')):
        raise ValueError('Solver registry does not match its build report')
    inputs = {str(source / 'bin' / n): h for n, h in profile['files'].items()}
    inputs.update(profile['externalFiles'])
    files = {}
    for name, expected in inputs.items():
        path = Path(name)
        if sha(path) != expected:
            raise ValueError('Native solver input changed: ' + name)
        if path.name in files and sha(files[path.name]) != expected:
            raise ValueError('Conflicting runtime basenames: ' + path.name)
        files[path.name] = path
    bin_dir = destination / 'bin'
    bin_dir.mkdir(parents=True)
    for name, path in files.items():
        shutil.copy2(path, bin_dir / name)
    for name in files:
        target = bin_dir / name
        if name.endswith('.dylib'):
            build.run(['install_name_tool', '-id', '@loader_path/' + name, target])
        for dep in dependencies(target):
            if system_library(dep):
                continue
            basename = Path(dep).name
            if basename not in files:
                raise ValueError('Unpinned native dependency: ' + dep)
            build.run(['install_name_tool', '-change', dep, '@loader_path/' + basename, target])
        lines = subprocess.check_output(['otool', '-l', target], text=True).splitlines()
        for i, line in enumerate(lines):
            if line.strip() == 'cmd LC_RPATH':
                value = next(x.strip()[5:].split(' (offset', 1)[0] for x in lines[i+1:i+4] if x.strip().startswith('path '))
                build.run(['install_name_tool', '-delete_rpath', value, target])
        build.run(['codesign', '--force', '--sign', '-', target])
        build.run(['codesign', '--verify', '--strict', target])
        for dep in dependencies(target):
            if not system_library(dep) and (not dep.startswith('@loader_path/') or not (bin_dir / Path(dep).name).is_file()):
                raise ValueError('Non-relocatable solver dependency: ' + dep)
    profile['id'] = 'osx-arm64-2.22-spooles-local-preview'
    profile['files'] = {p.name: sha(p) for p in sorted(bin_dir.iterdir())}
    profile.pop('externalFiles')
    profile['scope'] = 'Relocated ad-hoc local static-solid preview; original backend unchanged; not release acceptance'
    (destination / 'build-registry.json').write_text(json.dumps(registry, indent=2) + '\n')
    provenance = {'originalBuildReportSha256': sha(source / 'build-report.json'),
        'originalRegistrySha256': sha(source / 'build-registry.json'),
        'originalFiles': inputs, 'relocatedFiles': profile['files'],
        'backend': profile['backend'], 'adapterSha256': sha(Path(__file__)),
        'scope': profile['scope']}
    (destination / 'relocation.json').write_text(json.dumps(provenance, indent=2) + '\n')
    build.report['solverRelocation'] = provenance


def package(build, root, solver_build=None):
    output = build.output
    example_dir = output / 'examples'
    example_dir.mkdir()
    for name in ('cube-mesh.inp', 'cube-analysis.json', 'mixed-solids.inp', 'mixed-solids.json', 'mixed-pyramids.inp', 'mixed-pyramids.json', 'pressure-solids.inp', 'pressure-solids.json', 'gravity-column.inp', 'gravity-column.json', 'plastic-tension.inp', 'plastic-tension.json', 'finite-tension.inp', 'finite-tension.json', 'axial-frequency.inp', 'axial-frequency.json', 'column-buckling.inp', 'column-buckling.json'):
        shutil.copy2(root / 'X/Analysis/StaticDeck' / name, example_dir / name)
    for case in ('steady-conduction','transient-heating','surface-heating','body-heating','film-cooling','nodal-heating','radiation-cooling','temperature-conductivity','amplitude-heating','amplitude-force','free-expansion','restrained-expansion','implicit-ramp','implicit-damped','modal-ramp','modal-damped'):
        for suffix in ('.inp','.json'):
            shutil.copy2(root / 'X/Analysis/StaticDeck' / (case+suffix), example_dir / (case+suffix))
    pmx = (['--add-data', f"{output / 'pmx-tools'}:pmx-tools", '--hidden-import', 'decimal']
           if (output / 'pmx-tools').is_dir() else [])
    build.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--windowed', '--onedir',
        '--name', 'PrePoMax-X-Viewport', '--osx-bundle-identifier', 'org.prepomaxx.preview', '--target-architecture', 'arm64', '--collect-all', 'vtkmodules',
        '--add-data', f"{output / 'hosts'}:hosts", '--add-data', f"{output / 'source-identity.json'}:.",
        '--add-data', f"{root / 'X/Build/targets.json'}:.", '--add-data', f'{example_dir}:examples',
        '--add-data', f"{root / '.project/reports/l-bracket-cad-reference/verification.json'}:cad-reference",
        *pmx, '--distpath', output / 'dist', '--workpath', output / 'build', '--specpath', output,
        root / 'X/Desktop/viewport.py'])
    app = output / 'dist/PrePoMax-X-Viewport.app'
    if not app.is_dir():
        raise ValueError('Mac package directory not created')
    if solver_build:
        bundle_solver(build, root, solver_build.resolve(), app / 'Contents/Resources/native-solver')
        build.run(['codesign', '--force', '--sign', '-', app])
    build.run(['codesign', '--verify', '--deep', '--strict', app])
    return app


def dmg(build, root, app):
    from build import sha
    stage = build.output / 'dmg-payload'
    stage.mkdir()
    build.run(['ditto', app, stage / app.name])
    (stage / 'Applications').symlink_to('/Applications', target_is_directory=True)
    shutil.copy2(root / 'X/Desktop/INSTALL-macos.md', stage / 'READ-ME-FIRST.md')
    shutil.copy2(root / 'X/Desktop/UNINSTALL-macos.md', stage / 'UNINSTALL-AND-RESET.md')
    shutil.copy2(root / 'LICENSE', stage / 'COPYING-PrePoMax-X.txt')
    shutil.copytree(build.output / 'examples', stage / 'Examples')
    image = build.output / 'dist/PrePoMax-X-Preview-arm64.dmg'
    build.run(['hdiutil', 'create', '-volname', 'PrePoMax-X Preview', '-srcfolder', stage,
               '-fs', 'HFS+', '-format', 'UDZO', image])
    build.run(['hdiutil', 'verify', image])
    build.report['dmg'] = {'path': str(image), 'sha256': sha(image), 'bytes': image.stat().st_size,
        'signing': 'App is ad-hoc signed; DMG is not Developer-ID signed or notarized',
        'scope': 'Internal local preview; clean macOS and downloaded Gatekeeper acceptance pending'}
    return image

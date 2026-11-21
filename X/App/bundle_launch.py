"""PrePoMax-X.app launcher (Contents/Resources/launch.py, run by the bundled CPython in isolated mode).

The original application keeps its settings beside itself (Application.StartupPath), and the runtime profile takes
absolute paths, so the bundle does not run in place: the application folder is cloned into the user's data folder
(~/Library/Application Support/PrePoMax-X; PREPOMAXX_DATA overrides it) when the bundle is new or was updated, and
the original Configure step writes the runtime profile for the bundle's location (again when the bundle moves).
The user's settings.bin survives updates. Arguments go to the original command line (-f FILE ...).
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    bundle = json.loads((HERE / 'bundle.json').read_text())
    data = Path(os.environ.get('PREPOMAXX_DATA') or Path.home() / 'Library/Application Support/PrePoMax-X')
    app, profiles, work = data / 'app', data / 'profiles', data / 'work'
    for folder in (data, profiles, work):
        folder.mkdir(parents=True, exist_ok=True)
    marker, located = app / '.bundle-build', data / 'bundle-location'
    settings = app / 'settings.bin'
    kept = settings.read_bytes() if settings.exists() else None
    fresh = not marker.exists() or marker.read_text() != bundle['build']
    if fresh:
        if app.exists():
            shutil.rmtree(app)
        # A clone on APFS (cp -c) costs no space; a plain copy elsewhere
        if subprocess.run(['cp', '-cR', str(HERE / 'app'), str(app)]).returncode != 0:
            shutil.copytree(HERE / 'app', app, symlinks=True)
        if kept is not None:
            settings.write_bytes(kept)
        marker.write_text(bundle['build'])
    if fresh or not located.exists() or located.read_text() != str(HERE):
        python = bundle['python']
        (profiles / 'python.json').write_text(json.dumps({
            'schemaVersion': 1, 'version': python['version'], 'home': str(HERE / python['home']),
            'library': str(HERE / python['library']), 'librarySha256': python['librarySha256'],
            'moduleDirectories': [str(HERE / d) for d in python['moduleDirectories']]}, indent=2) + '\n')
        (profiles / 'tools.json').write_text(json.dumps({
            'schemaVersion': 1, 'tools': {k: {'path': str(HERE / v['path']), 'sha256': v['sha256']}
                                          for k, v in bundle['tools'].items()}}, indent=2) + '\n')
        solver = bundle['solver']
        code = subprocess.run([str(app / 'PrePoMaxX.Configure'), '--app', str(app),
                               '--python', str(profiles / 'python.json'), '--native-tools', str(profiles / 'tools.json'),
                               '--gmsh-library', str(HERE / bundle['gmsh']),
                               '--solver', str(HERE / solver['registry']), solver['id'], str(HERE / solver['directory']),
                               '--default-solver-type', 'Spooles', '--work-directory', str(work),
                               *(['--replace-settings'] if settings.exists() else [])]).returncode
        if code != 0:
            raise SystemExit(f'PrePoMax-X: the configuration step failed ({code})')
        located.write_text(str(HERE))
    os.execv(str(app / 'PrePoMax'), [str(app / 'PrePoMax'), *sys.argv[1:]])


if __name__ == '__main__':
    main()

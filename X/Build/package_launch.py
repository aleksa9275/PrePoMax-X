"""PrePoMax-X launcher (packaged as launch.py, run by the bundled CPython in isolated mode).

The .NET host takes absolute, fingerprinted runtime profiles. This writes them for the current install location
into the user's PrePoMax-X data folder (macOS: ~/Library/Application Support/PrePoMax-X, Linux:
$XDG_DATA_HOME/PrePoMax-X or ~/.local/share/PrePoMax-X, Windows: %LOCALAPPDATA%\\PrePoMax-X) and starts the host
with them. Arguments are passed on to the UI (e.g. a project file). PREPOMAXX_DATA overrides the data folder.

    launch.py --profiles DIR   only writes the profiles to DIR and the matching X/UI/verify-ui.py arguments to
                               DIR/verify-arguments.json (repository verification with this package's runtime)
"""
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def data_folder():
    if os.environ.get('PREPOMAXX_DATA'):
        return Path(os.environ['PREPOMAXX_DATA'])
    if sys.platform == 'darwin':
        return Path.home() / 'Library/Application Support/PrePoMax-X'
    if sys.platform == 'win32':
        return Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local')) / 'PrePoMax-X'
    return Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'PrePoMax-X'


def main():
    package = json.loads((HERE / 'package.json').read_text())
    data = data_folder()
    profiles, work = data / 'profiles', data / 'work'
    profiles_only = len(sys.argv) == 3 and sys.argv[1] == '--profiles'
    if profiles_only:
        profiles = Path(sys.argv[2]).resolve()
    profiles.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    python = package['components']['python']
    (profiles / 'python.json').write_text(json.dumps({
        'schemaVersion': 1, 'version': python['version'], 'home': str(HERE / 'python'),
        'library': str(HERE / python['library']), 'librarySha256': python['librarySha256'],
        'moduleDirectories': [str(HERE / d) for d in python['moduleDirectories']]}, indent=2) + '\n')
    (profiles / 'tools.json').write_text(json.dumps({
        'schemaVersion': 1, 'tools': {k: {'path': str(HERE / v['path']), 'sha256': v['sha256']}
                                      for k, v in package['tools'].items()}}, indent=2) + '\n')
    if profiles_only:
        arguments = ['--python-profile', str(profiles / 'python.json'), '--native-tools', str(profiles / 'tools.json')]
        gmsh = package['components'].get('gmsh')
        if gmsh:
            arguments += ['--gmsh-library', str(HERE / gmsh['file'])]
        if package.get('solver'):
            solver = package['solver']
            arguments += ['--solver-registry', str(HERE / solver['registry']), '--solver-id', solver['id'],
                          '--solver-directory', str(HERE / solver['directory'])]
        (profiles / 'verify-arguments.json').write_text(json.dumps(arguments, indent=2) + '\n')
        print(' '.join(arguments))
        return
    environment = dict(os.environ)
    gmsh = package['components'].get('gmsh')
    if gmsh:
        environment['PREPOMAXX_GMSH_LIBRARY'] = str(HERE / gmsh['file'])
    host = HERE / package['components']['dotnet']['host']
    command = [str(host), str(profiles / 'python.json'), str(work), str(HERE / package['components']['ui']['script']),
               '--native-tools', str(profiles / 'tools.json')]
    solver = package.get('solver')
    if solver:
        command += ['--solver-registry', str(HERE / solver['registry']), '--solver-id', solver['id'],
                    '--solver-directory', str(HERE / solver['directory'])]
    command += sys.argv[1:]
    if sys.platform == 'win32':
        raise SystemExit(subprocess.call(command, env=environment, cwd=str(work)))
    os.chdir(work)
    os.execve(command[0], command, environment)


if __name__ == '__main__':
    main()

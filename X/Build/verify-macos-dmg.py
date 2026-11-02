#!/usr/bin/env python3
"""Verify a local DMG and execute the copied app's actual native cube workflow."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import plistlib
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    package, out = args.package.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {'success': False, 'commands': [], 'scope': 'Local mounted/copy test, not a clean macOS or downloaded Gatekeeper test'}
    mount = out / 'Mounted preview'
    attached = False

    def run(command, name, env=None, timeout=180):
        done = subprocess.run(list(map(str, command)), capture_output=True, env=env, timeout=timeout)
        (out / (name + '.stdout')).write_bytes(done.stdout)
        (out / (name + '.stderr')).write_bytes(done.stderr)
        report['commands'].append({'arguments': list(map(str, command)), 'exitCode': done.returncode, 'log': name})
        if done.returncode:
            raise ValueError(name + ' failed: ' + done.stderr.decode(errors='replace')[-1500:])
        return done.stdout

    try:
        manifest = json.loads((package / 'package.json').read_text())
        if not manifest['success'] or manifest['target'] != 'osx-arm64':
            raise ValueError('Successful Mac package manifest required')
        image = Path(manifest['dmg']['path'])
        if sha(image) != manifest['dmg']['sha256']:
            raise ValueError('DMG changed after packaging')
        report.update(dmgSha256=sha(image), packageManifestSha256=sha(package / 'package.json'))
        run(['hdiutil', 'verify', image], 'verify-image')
        run(['hdiutil', 'attach', '-readonly', '-noautoopen', '-mountpoint', mount, '-plist', image], 'mount')
        attached = True
        source_app = mount / 'PrePoMax-X-Viewport.app'
        run(['codesign', '--verify', '--deep', '--strict', source_app], 'mounted-signature')
        installed = out / 'Installed copy/PrePoMax-X-Viewport.app'
        installed.parent.mkdir()
        run(['ditto', source_app, installed], 'copy-app')
        run(['hdiutil', 'detach', mount], 'eject')
        attached = False
        run(['codesign', '--verify', '--deep', '--strict', installed], 'installed-signature')
        hashes = {p.relative_to(installed).as_posix(): sha(p) for p in sorted(installed.rglob('*')) if p.is_file() and not p.is_symlink()}
        if hashes != manifest['fileHashes']:
            raise ValueError('Copied app bytes differ from package manifest')
        links = {p.relative_to(installed).as_posix(): os.readlink(p) for p in sorted(installed.rglob('*')) if p.is_symlink()}
        if links != manifest['symlinkTargets']:
            raise ValueError('Copied app links differ from package manifest')
        for name in links:
            if not (installed / name).resolve().is_relative_to(installed):
                raise ValueError('App symlink escapes its bundle: ' + name)
        env = dict(os.environ, PATH='/usr/bin:/bin', DOTNET_ROOT='/nonexistent-external-dotnet')
        for name in ('PYTHONHOME', 'PYTHONPATH', 'DYLD_LIBRARY_PATH', 'DYLD_FRAMEWORK_PATH'):
            env.pop(name, None)
        executable = installed / 'Contents/MacOS/PrePoMax-X-Viewport'
        gui_file = out / 'desktop-workflow.json'
        run([executable, '--run-example', '--jobs-root', out / 'Job workspace', '--self-test', gui_file,
             '--screenshot', out / 'desktop-workflow.png'], 'desktop', env)
        gui = json.loads(gui_file.read_text())
        if not gui['success']:
            raise ValueError('Desktop workflow checks failed')
        job = gui['desktopJob']
        if not job['success'] or not job['outcome']['solverExecuted']:
            raise ValueError('No actual successful native desktop solve')
        module = importlib.util.spec_from_file_location('reference', ROOT / 'X/Feasibility/Solver/run-reference.py')
        reference = importlib.util.module_from_spec(module)
        module.loader.exec_module(reference)
        data = reference.parse_dat((Path(job['directory']) / 'analysis.dat').read_text())
        checks = reference.analytical_checks(data)
        altered = {key: [row[:] for row in rows] for key, rows in data.items()}
        altered['displacements'][0][1] += 0.01
        rejected = not all(c['passed'] for c in reference.analytical_checks(altered))
        if not all(c['passed'] for c in checks) or not rejected:
            raise ValueError('Native numerical check or negative control failed')
        report.update(success=True, installedApp=str(installed), appFiles=len(hashes), appLinks=len(links),
            guiChecks=gui['checks'], analyticalChecks=checks, alteredDisplacementRejected=rejected,
            jobDirectory=job['directory'], nativeSolverExecuted=True, externalBuildToolsOnPath=False,
            developerIdSigned=False, notarized=False)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        report['error'] = str(error)
    finally:
        if attached:
            run(['hdiutil', 'detach', mount], 'cleanup-eject')
        (out / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report.get(k) for k in ('success', 'installedApp', 'nativeSolverExecuted', 'error')}))
    return 0 if report['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Exercise the real Gmsh C# adapter and reject unpinned native runtimes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    library = args.library.resolve()
    report = {'success': False, 'host': {'os': platform.system(), 'architecture': platform.machine()},
              'commands': [], 'rejections': [], 'scope': 'Native adapter checks; not full mesher/original Windows parity'}

    def run(command, env=None, expected=0):
        done = subprocess.run(list(map(str, command)), env=env, capture_output=True, text=True, timeout=180)
        report['commands'].append({'arguments': list(map(str, command)), 'exitCode': done.returncode,
                                   'stdout': done.stdout, 'stderr': done.stderr})
        if done.returncode != expected:
            raise ValueError('Unexpected process outcome; see retained command output')
        return done

    try:
        report['buildProfile'] = json.loads((library.parent / 'gmsh-build.json').read_text())
        report['librarySha256'] = hashlib.sha256(library.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(prefix='prepomaxx-gmsh-') as temporary:
            work = Path(temporary)
            run(['dotnet', 'build', HERE / 'GmshSmoke/GmshSmoke.csproj', '-c', 'Release', '--disable-build-servers',
                 '-m:1', '-p:UseSharedCompilation=false', '--artifacts-path', work / 'build', '-v:quiet'])
            binary = work / 'build/bin/GmshSmoke/release/GmshSmoke.dll'
            env = dict(os.environ, PREPOMAXX_GMSH_LIBRARY=str(library))
            done = run(['dotnet', binary, out / 'workflow'], env)
            report['tests'] = json.loads(done.stdout.splitlines()[-1])
            if not report['tests']['success'] or report['tests']['passed'] != 18:
                raise ValueError('Native adapter checks incomplete')
            cases = [('missing manifest', None, 'gmsh-build.json are required'),
                     ('wrong version', {'version': '4.15.2'}, 'does not match the pinned'),
                     ('wrong source revision', {'revision': 'stock'}, 'does not match the pinned'),
                     ('wrong OCCT version', {'occtVersion': '8.0.1'}, 'does not match the pinned'),
                     ('changed library fingerprint', {'librarySha256': '0'*64}, 'fingerprint does not match')]
            for index, (name, changes, message) in enumerate(cases):
                folder = work / str(index); folder.mkdir()
                link = folder / library.name; link.symlink_to(library)
                if changes is not None:
                    profile = dict(report['buildProfile'], **changes)
                    (folder / 'gmsh-build.json').write_text(json.dumps(profile))
                env['PREPOMAXX_GMSH_LIBRARY'] = str(link)
                rejected = run(['dotnet', binary], env, 1)
                if message not in rejected.stderr:
                    raise ValueError('Wrong rejection reason: ' + name)
                report['rejections'].append(name)
            env['PREPOMAXX_GMSH_LIBRARY'] = library.name
            rejected = run(['dotnet', binary], env, 1)
            if 'must be an absolute path' not in rejected.stderr:
                raise ValueError('Relative runtime path accepted')
            report['rejections'].append('relative runtime override')
            env.pop('PREPOMAXX_GMSH_LIBRARY')
            rejected = run(['dotnet', binary], env, 1)
            if 'pinned PrePoMax Gmsh runtime is missing' not in rejected.stderr:
                raise ValueError('Unexpected implicit runtime lookup')
            report['rejections'].append('implicit system runtime lookup')
        report['success'] = True
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        report['error'] = str(error)
    (out / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'success': report['success'], 'passed': report.get('tests', {}).get('passed'),
                      'rejections': len(report['rejections']), 'error': report.get('error')}))
    return 0 if report['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

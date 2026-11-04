"""Task 0045 research proof. Run with the current Release Solve DLL."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


LIMITS = {'manifest.json': 4096, 'mesh.inp': 16 * 1024**2,
          'analysis.json': 2 * 1024**2}


def digest(content):
    return hashlib.sha256(content).hexdigest()


def unique_object(pairs):
    result = dict(pairs)
    if len(result) != len(pairs):
        raise ValueError('Duplicate manifest key')
    return result


def read_project(path):
    if path.stat().st_size > sum(LIMITS.values()) + 4096:
        raise ValueError('Container exceeds proof size limit')
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if sorted(entry.filename for entry in entries) != sorted(LIMITS):
            raise ValueError('Unexpected, missing or duplicate project entry')
        for entry in entries:
            if entry.compress_type != zipfile.ZIP_STORED or entry.file_size > LIMITS[entry.filename]:
                raise ValueError('Unsupported project entry encoding or size')
        files = {name: archive.read(name) for name in LIMITS}
    manifest = json.loads(files.pop('manifest.json'), object_pairs_hook=unique_object)
    if (not isinstance(manifest, dict)
            or type(manifest.get('version')) is not int or manifest['version'] != 1
            or manifest.get('kind') != 'static-solid-proof'
            or set(manifest) != {'version', 'kind', 'sha256', 'links'}):
        raise ValueError('Unsupported project manifest')
    if manifest['sha256'] != {name: digest(content) for name, content in files.items()}:
        raise ValueError('Project payload digest mismatch')
    links = manifest['links']
    if not isinstance(links, dict) or set(links) != {'source', 'result'} or any(
            not isinstance(value, str) or len(value) != 64
            or any(char not in '0123456789abcdef' for char in value)
            for value in links.values()):
        raise ValueError('Unsupported link identity')
    return files, links


def write_project(path, files, manifest):
    with zipfile.ZipFile(path, 'x') as archive:
        archive.writestr('manifest.json', json.dumps(manifest))
        for name, content in files.items():
            archive.writestr(name, content)


def validate(host, folder, files):
    folder.mkdir()
    for name, content in files.items():
        (folder / name).write_bytes(content)
    result = subprocess.run(['dotnet', str(host), 'validate-static',
                             str(folder / 'mesh.inp'), str(folder / 'analysis.json')],
                            capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise ValueError(result.stderr.strip())
    return json.loads(result.stdout)


def main(host):
    root = Path(__file__).resolve().parents[2]
    cube = root / 'X/Analysis/StaticDeck'
    mesh = (root / 'X/Desktop/nonsequential-cube.inp').read_bytes() + (
        b'\n*NSET,NSET=NALL\n61,17,105,200,4,99,300,500'
        b'\n*NSET,NSET=X0\n61,200,4,500\n*NSET,NSET=Y0\n61,17,4,99'
        b'\n*NSET,NSET=Z0\n61,17,105,200\n*NSET,NSET=X1\n17,105,99,300\n')
    analysis = json.loads((cube / 'cube-analysis.json').read_bytes())
    baseline = {'mesh.inp': mesh, 'analysis.json': json.dumps(analysis).encode()}
    analysis['materials'][0]['youngsModulus'] = '105 GPa'
    analysis['step']['loads'][0]['forcePerNode'][0] = '50 N'
    edited = {**baseline, 'analysis.json': json.dumps(analysis).encode()}
    links = {'source': digest(mesh), 'result': digest(b'synthetic result identity')}
    manifest = {'kind': 'static-solid-proof', 'version': 1, 'links': links,
                'sha256': {name: digest(content) for name, content in edited.items()}}
    rejected = []
    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        archive = work / 'model.proof'
        original = validate(host, work / 'baseline', baseline)
        before = validate(host, work / 'before', edited)
        write_project(archive, edited, manifest)
        reopened, reopened_links = read_project(archive)
        after = validate(host, work / 'after', reopened)
        if (reopened != edited or reopened_links != links or after != before
                or before['deckSha256'] == original['deckSha256']
                or after['solverExecuted']):
            raise RuntimeError('Round-trip validation failed')
        try:
            write_project(archive, baseline, manifest)
        except FileExistsError:
            rejected.append('existing-destination')
        else:
            raise RuntimeError('Overwrote an existing project')
        controls = [
            ('future-version', edited, {**manifest, 'version': 2}),
            ('unknown-field', edited, {**manifest, 'extra': True}),
            ('unknown-member', {**edited, '../extra': b'unsupported'}, manifest),
            ('changed-payload', {**edited, 'analysis.json': b'{}'}, manifest),
        ]
        for label, files, metadata in controls:
            path = work / (label + '.proof')
            write_project(path, files, metadata)
            try:
                read_project(path)
            except ValueError:
                rejected.append(label)
            else:
                raise RuntimeError('Accepted ' + label)
        analysis['materialOrientations'] = []
        unsupported = {**edited, 'analysis.json': json.dumps(analysis).encode()}
        path = work / 'unsupported-engineering.proof'
        write_project(path, unsupported, {**manifest, 'sha256': {
            name: digest(content) for name, content in unsupported.items()}})
        try:
            validate(host, work / 'unsupported', read_project(path)[0])
        except ValueError as error:
            if 'materialOrientations' not in str(error):
                raise
            rejected.append('unknown-engineering-field')
        else:
            raise RuntimeError('Accepted an unknown engineering field')
    print(json.dumps({'baseline': original, 'beforeSave': before,
                      'afterReopen': after, 'identicalPayloadsAndLinks': True,
                      'rejected': rejected}, indent=2))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())

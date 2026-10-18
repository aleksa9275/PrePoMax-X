"""Guard the source-linked analysis superset and original net48 ownership."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
import static_layout

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'X/Core'))
import verify as core_verify

BASELINE = core_verify.BASELINE
EXTENSIONS = 'CaeGlobals/Extensions.cs'
FORMATTING = 'CaeGlobals/Extensions.Calculix.cs'
BOUNDARY = 'CaeModel/FileInOut/Output/Calculix/MaterialDeckWriter.cs'
BOUNDARIES = {BOUNDARY, 'CaeModel/FileInOut/Output/Calculix/StaticAnalysisDeckWriter.cs'}
REMOVED = {
    'CaeGlobals/Equation/EquationContainer.cs': 'using System.Runtime.Remoting.Contexts;\n',
    'CaeGlobals/Equation/EquationString.cs': 'using System.Runtime.Remoting.Contexts;\n',
    'CaeGlobals/CommonClasses/OrderedDictionary.cs': 'using System.Runtime.InteropServices.WindowsRuntime;\n',
    'CaeGlobals/UnitSystem/StringToDouble/StringNewtonGravityUndefinedConverter.cs': 'using System.Windows.Forms;\n',
}
PACKAGES = {'ncalc': '1.3.8', 'UnitsNet': '4.89.1'}


def original(revision, path):
    return subprocess.check_output(['git', 'show', revision + ':' + path], cwd=ROOT)


def formatting_sources(data):
    return {p:t.encode() for p,t in static_layout.render_extensions(data.decode('utf-8')).items()}


def adapt(path, data):
    if path in REMOVED:
        line = REMOVED[path].encode()
        if data.count(line) != 1:
            raise ValueError('Unused-import anchor changed: ' + path)
        return data.replace(line, b'')
    return data


def source_rows(revision=BASELINE):
    core_rows = core_verify.sources()
    manifest = json.loads((HERE / 'analysis-sources.json').read_text())
    if manifest['baseline'] != BASELINE:
        raise ValueError('Analysis baseline changed')
    rows = manifest['sources']
    if len({row['path'] for row in rows}) != len(rows):
        raise ValueError('Duplicate source manifest entry')
    variants = manifest.get('reviewedVariants', {}).get(revision, {})
    mechanical = static_layout.render(ROOT, revision)
    mechanical_baseline = static_layout.render(ROOT, BASELINE)
    if mechanical != mechanical_baseline:
        raise ValueError('Unreviewed upstream static-deck mechanical boundary changed')
    for path, expected in mechanical.items():
        if (ROOT/path).read_bytes() != expected:
            raise ValueError('Mechanical static-deck source extraction changed: '+path)
        if path.endswith('.Legacy.cs') or path.endswith(('Tools.Equations.cs','Tools.Results.cs')):
            owner=path.split('/')[0]
            ns={'m':'http://schemas.microsoft.com/developer/msbuild/2003'}
            project=ET.parse(ROOT/owner/(owner+'.csproj'))
            if sum(c.attrib['Include'].replace('\\','/')==path[len(owner)+1:] for c in project.findall('.//m:Compile',ns)) != 1:
                raise ValueError('Original net48 extraction inclusion changed: '+path)
    moved = formatting_sources(original(revision, EXTENSIONS))
    if moved != formatting_sources(original(BASELINE, EXTENSIONS)):
        raise ValueError('Upstream numeric formatting changed; review extraction')
    for path, expected in moved.items():
        if (ROOT / path).read_bytes() != expected:
            raise ValueError('Original numeric formatting extraction changed: ' + path)
    for row in rows:
        name = row['path']
        data = (ROOT / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('Reviewed analysis source changed: ' + name)
        if name not in mechanical and name not in BOUNDARIES:
            upstream = adapt(name, original(revision, name))
            baseline = adapt(name, original(BASELINE, name))
            if data != baseline:
                raise ValueError('Current analysis engineering source changed: ' + name)
            if name in variants:
                if hashlib.sha256(upstream).hexdigest() != variants[name]:
                    raise ValueError('Reviewed upstream material variant changed: ' + name)
            elif upstream != baseline:
                raise ValueError('Unreviewed upstream analysis source changed: ' + name)
    variant_additions = set().union(*(set(v) for v in manifest.get('reviewedVariants', {}).values())) - {r['path'] for r in rows}
    expected = {r['path'] for r in core_rows + rows} | variant_additions
    actual = []
    for owner in ['CaeGlobals', 'CaeMesh', 'CaeResults', 'CaeModel']:
        project = ET.parse(HERE / owner / (owner + '.csproj'))
        owned = [c.attrib['Include'].replace('$(RepositoryRoot)', '') for c in project.findall('.//Compile')]
        if any(not p.startswith(owner + '/') for p in owned):
            raise ValueError('Original assembly ownership changed: ' + owner)
        actual.extend(owned)
        packages = {p.attrib['Include']: p.attrib['Version'] for p in project.findall('.//PackageReference')}
        if packages != ({k: '[' + v + ']' for k, v in PACKAGES.items()} if owner == 'CaeGlobals' else {}):
            raise ValueError('Analysis package pins changed')
        legacy = ET.parse(ROOT / owner / (owner + '.csproj'))
        ns = {'m': 'http://schemas.microsoft.com/developer/msbuild/2003'}
        included = [c.attrib['Include'].replace('\\', '/') for c in legacy.findall('.//m:Compile', ns)]
        for p in owned:
            if p in variant_additions:
                items = project.findall('.//Compile')
                declaration = [c for c in items if c.attrib['Include'].replace('$(RepositoryRoot)', '') == p]
                if len(declaration) != 1 or declaration[0].attrib.get('Condition') != "Exists('$(RepositoryRoot)" + p + "')":
                    raise ValueError('Optional upstream-only source declaration changed')
                if (ROOT / p).exists():
                    raise ValueError('Upstream-only type must not silently enter the baseline build')
                continue
            if included.count(p[len(owner) + 1:]) != 1:
                raise ValueError('Source must remain in original net48 project exactly once: ' + p)
    if set(actual) != expected or len(actual) != len(expected):
        raise ValueError('Analysis assembly source closure changed')
    upstream_packages = {p.attrib['id']: p.attrib['version'] for p in ET.parse(ROOT / 'CaeGlobals/packages.config').getroot()}
    if any(upstream_packages[k] != v for k, v in PACKAGES.items()):
        raise ValueError('Portable packages no longer match upstream versions')
    selected = [dict(r) for r in core_rows + rows]
    for name, expected_hash in variants.items():
        data = original(revision, name)
        if hashlib.sha256(data).hexdigest() != expected_hash:
            raise ValueError('Pinned upstream variant hash mismatch: ' + name)
        row = next((r for r in selected if r['path'] == name), None)
        if row is None:
            ns = {'m': 'http://schemas.microsoft.com/developer/msbuild/2003'}
            project = ET.fromstring(original(revision, 'CaeModel/CaeModel.csproj').decode('utf-8-sig'))
            if sum(c.attrib['Include'].replace('\\', '/') == name[len('CaeModel/'):] for c in project.findall('.//m:Compile', ns)) != 1:
                raise ValueError('Upstream composite type lost original net48 ownership')
            row = {'path': name, 'kind': 'upstream-only material type'}
            selected.append(row)
        row.update(sha256=expected_hash, upstreamVariant=revision)
    return selected

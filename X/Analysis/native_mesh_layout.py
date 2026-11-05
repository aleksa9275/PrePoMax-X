"""Task 0067 original VOL/parameter ownership and mechanical extraction guard."""
import hashlib
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
PIN = 'a293e892971214e6141b44e16838ef916701b5c3'
VOL = 'CaeModel/FileInOut/Input/Netgen/NetgenVolFileReader'
SETUP = 'CaeMesh/Meshing/Base/MeshSetupItem'
ADDITIONS = [
 'CaeGlobals/Comparers/CompareDoubleArray.cs', SETUP + '.cs',
 'CaeMesh/Meshing/Base/MeshingParameters.cs', 'CaeMesh/Meshing/Base/MesherTypeEnum.cs',
 'CaeMesh/Meshing/Gmsh/Enums/TransfiniteThreeSidedEnum.cs',
 'CaeMesh/Meshing/Netgen/Enums/NetgenTransfiniteFacesEnum.cs',
 VOL + '.Parsing.cs', VOL + '.MeshData.cs',
 'CaeModel/FileInOut/Input/Netgen/NetgenVolKeywords.cs']
PORTABLE_ONLY = {VOL + '.MeshData.cs'}


def original(path):
    return subprocess.check_output(['git', 'show', PIN + ':' + path], cwd=ROOT).decode('utf-8-sig')


def rows():
    old = original(VOL + '.cs')
    marker = '        static private List<List<string>> GetDataSets'
    front, tail = old.split(marker, 1)
    expected = front.replace('public static class NetgenVolFileReader', 'public static partial class NetgenVolFileReader') + '    }\n}\n'
    # The existing method separator belongs to the retained Read implementation.
    actual = (ROOT / (VOL + '.cs')).read_text(encoding='utf-8-sig')
    if actual.rstrip() != expected.rstrip():
        raise ValueError('Original Windows VOL orchestration changed')
    header = front[:front.index('    [Serializable]')]
    parsing = header + '    public static partial class NetgenVolFileReader\n    {\n' + marker + tail
    for token in ['record1[0]', 'record1[1]', 'record1[2]', 'record[9]', 'record[11]']:
        parsing = parsing.replace('double.Parse(' + token + ')', 'double.Parse(' + token + ', System.Globalization.CultureInfo.InvariantCulture)')
    if (ROOT / (VOL + '.Parsing.cs')).read_text() != parsing:
        raise ValueError('Original VOL helper extraction/permutations changed')
    setup = original(SETUP + '.cs')
    start = setup.index('        public void CopyFrom(')
    end = setup.index('\n        }', start) + len('\n        }')
    method = setup[start:end]
    expected = setup[:start] + setup[end + 1:]
    expected = expected.replace('using Octree;\n', '').replace('abstract class MeshSetupItem', 'abstract partial class MeshSetupItem')
    if (ROOT / (SETUP + '.cs')).read_text(encoding='utf-8-sig') != expected:
        raise ValueError('Original meshing setup extraction changed')
    if method not in (ROOT / (SETUP + '.Legacy.cs')).read_text():
        raise ValueError('Original Windows selection copying changed')
    for path in ADDITIONS:
        if path not in {SETUP + '.cs', VOL + '.Parsing.cs', VOL + '.MeshData.cs'}:
            if (ROOT / path).read_text(encoding='utf-8-sig') != original(path):
                raise ValueError('Original native meshing engineering source changed: ' + path)
    for path in [VOL + '.Parsing.cs', SETUP + '.Legacy.cs']:
        owner, rest = path.split('/', 1)
        project = ET.parse(ROOT / owner / (owner + '.csproj'))
        ns = {'m': 'http://schemas.microsoft.com/developer/msbuild/2003'}
        if sum(c.attrib['Include'].replace('\\', '/') == rest for c in project.findall('.//m:Compile', ns)) != 1:
            raise ValueError('Windows extraction ownership changed: ' + path)
    return [{'path': p, 'sha256': hashlib.sha256((ROOT / p).read_bytes()).hexdigest(),
             'kind': 'native mesh boundary', 'originalReference': PIN} for p in ADDITIONS]

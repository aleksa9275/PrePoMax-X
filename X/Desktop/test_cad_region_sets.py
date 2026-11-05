"""Real C# source-set unions: overlap, entity kind, limits and atomic failures."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class CadRegionSets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configured = os.environ.get('DESKTOP_TEST_MESH_HOST')
        host = Path(configured) if configured else ROOT / 'X/Desktop/MeshScene/bin/Release/net10.0/PrePoMaxX.MeshScene.dll'
        cls.command = (['dotnet', str(host)] if host.suffix == '.dll' else [str(host)])

    def run_set(self, source, output, kind, name, sources, operation='add-region-set'):
        return subprocess.run([*self.command, operation, str(source), str(output), kind, name, sources],
                              capture_output=True, text=True, timeout=30)

    def test_overlapping_faces_union_through_original_reader(self):
        with tempfile.TemporaryDirectory() as folder:
            original = ROOT / 'X/Analysis/StaticDeck/cube-mesh.inp'
            before = original.read_bytes()
            target = Path(folder) / 'union.inp'
            done = self.run_set(original, target, 'node', 'SupportFaces', 'X0,Y0')
            self.assertEqual(done.returncode, 0, done.stderr)
            result = json.loads(done.stdout)
            self.assertEqual(result['authoredSet']['ids'], [1, 2, 4, 5, 6, 8])
            self.assertEqual(result['authoredSet']['kind'], 'node')
            self.assertEqual(original.read_bytes(), before)
            again = self.run_set(original, target, 'node', 'Another', 'X1')
            self.assertNotEqual(again.returncode, 0)
            self.assertEqual(json.loads(done.stdout)['SourceSha256'], __import__('hashlib').sha256(target.read_bytes()).hexdigest())

    def test_element_source_sets_remain_elements(self):
        with tempfile.TemporaryDirectory() as folder:
            done = self.run_set(ROOT / 'X/Analysis/StaticDeck/cube-mesh.inp', Path(folder)/'set.inp', 'element', 'PartSection', 'SOLID')
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual(json.loads(done.stdout)['authoredSet']['ids'], [1])

    def test_invalid_sources_publish_no_output(self):
        cases = [('node','Bad',''), ('node','Bad','Missing'), ('node','Bad','X0,X0'),
                 ('node','Bad','X0,x0'), ('node','Bad','SOLID'), ('element','Bad','NALL'),
                 ('node','NALL','X0'), ('node','bad name','X0'), ('node','Bad',','.join(['X0']*257))]
        with tempfile.TemporaryDirectory() as folder:
            for index, (kind,name,sources) in enumerate(cases):
                with self.subTest(kind=kind,name=name,sources=sources[:30]):
                    output = Path(folder)/f'{index}.inp'
                    done = self.run_set(ROOT/'X/Analysis/StaticDeck/cube-mesh.inp', output, kind, name, sources)
                    self.assertNotEqual(done.returncode, 0)
                    self.assertFalse(output.exists())
                    self.assertFalse(json.loads(done.stderr)['success'])

    def test_whole_part_regions_exceed_manual_id_entry_limit(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder)/'large.inp'
            lines = ['*NODE,NSET=WholePart']
            unit = [(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)]
            for cell in range(251):
                for i,(x,y,z) in enumerate(unit,1):
                    lines.append(f'{cell*8+i},{cell*2+x},{y},{z}')
            lines.append('*ELEMENT,TYPE=C3D8,ELSET=Solids')
            for cell in range(251):
                lines.append(','.join(map(str,[cell+1,*range(cell*8+1,cell*8+9)])))
            source.write_text('\n'.join(lines)+'\n')
            output=Path(folder)/'selected.inp'
            done=self.run_set(source,output,'node','SelectedPart','WholePart')
            self.assertEqual(done.returncode,0,done.stderr)
            self.assertEqual(json.loads(done.stdout)['authoredSet']['ids'],list(range(1,2009)))
            done=self.run_set(source,Path(folder)/'manual.inp','node','Manual',','.join(map(str,range(1,1002))),operation='add-set')
            self.assertNotEqual(done.returncode,0)


if __name__ == '__main__':
    unittest.main()

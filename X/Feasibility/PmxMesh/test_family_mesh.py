"""Original PMX topology closure and bounded binary transport checks."""
import json
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[3]
HOST=ROOT/'X/Feasibility/PmxMesh/bin/Release/net10.0/PmxMesh.dll'

class FamilyMesh(unittest.TestCase):
    def run_mesh(self,data):
        with tempfile.TemporaryDirectory() as name:
            p=Path(name)/'model.bin';p.write_bytes(data)
            return subprocess.run(['dotnet',str(HOST),'--family-mesh',str(p)],capture_output=True,text=True)
    def binary(self,vtk,length):
        b=bytearray(struct.pack('<iii',0,1,20))
        for i in range(1,21):b.extend(struct.pack('<iddd',i,float(i),0.,0.))
        b.extend(struct.pack('<iiiii',1,7,31,vtk,length))
        b.extend(struct.pack('<'+'i'*length,*range(1,length+1)))
        b.extend(struct.pack('<i',1));b.extend(b'\x04Part');b.extend(struct.pack('<i',-1));return b
    def test_all_original_serialized_topologies_use_unchanged_factories(self):
        for vtk,count in [(3,2),(21,3),(5,3),(9,4),(22,6),(23,8),(10,4),(14,5),(13,6),(12,8),(24,10),(27,13),(26,15),(25,20)]:
            with self.subTest(vtk=vtk):
                done=self.run_mesh(self.binary(vtk,count));self.assertEqual(done.returncode,0,done.stderr)
                e=json.loads(done.stdout)['elements'][0];self.assertEqual((e['id'],e['partId'],e['vtkCellType'],e['connectivity']),(31,7,vtk,list(range(1,count+1))))
    def test_unknown_topology_and_wrong_connectivity_cannot_fall_back(self):
        for vtk,length in [(0,1),(100,8),(24,4),(3,3)]:
            self.assertNotEqual(self.run_mesh(self.binary(vtk,length)).returncode,0)
        b=self.binary(3,2);self.assertNotEqual(self.run_mesh(b[:-1]).returncode,0)
        b=self.binary(3,2);b[-20:-16]=struct.pack('<i',9999) # Invalid node reference or part framing, never accepted.
        self.assertNotEqual(self.run_mesh(b).returncode,0)
    def test_family_formulation_table_matches_original_enum_values(self):
        original=(ROOT/'CaeMesh/Elements/FeElementType.cs').read_text(encoding='utf-8-sig')
        adapter=(ROOT/'X/Feasibility/Pmx/StaticGraph.Families.cs').read_text()
        for enum,choices in re.findall(r'"(FeElementType\w+)",Choices\((.*?)\)\)',adapter):
            block=re.search(r'enum '+enum+r'\s*\{(.*?)\n    \}',original,re.S).group(1)
            values={name:int(number) for name,number in re.findall(r'\b(\w+)\s*=\s*(\d+)',block)}
            for number,name in re.findall(r'\((\d+),"(\w+)"\)',choices+')'):
                self.assertEqual(values[name],int(number))

if __name__=='__main__':unittest.main()

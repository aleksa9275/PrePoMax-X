"""Structural engineering controls and original keyword transport contracts."""
from pathlib import Path
import json
import subprocess
import tempfile
import unittest
from PyQt6 import QtWidgets
from analysis_editor import AnalysisDialog,validate_definition
from structural_workflow_fixtures import CASES,fixture
from viewport import decode


class StructuralAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    def reject(self,case,change):
        data,spec=fixture(case);change(spec)
        with self.assertRaises(ValueError):validate_definition(data,spec)
    def test_all_examples_editor_roundtrip_and_original_validation(self):
        with tempfile.TemporaryDirectory() as name:
            for case in CASES:
                with self.subTest(case=case):
                    data,spec=fixture(case);path=Path(name)/(case+'.inp');path.write_bytes(data)
                    d=AnalysisDialog(None,decode(path),data,spec)
                    self.assertTrue(d.validate_current(),d.message.text())
                    self.assertEqual(d.definition['sections'],spec['sections'])
                    self.assertEqual(d.definition['step']['constraints'],spec['step']['constraints'])
                    self.assertEqual(d.definition['step'].get('moments'),spec['step'].get('moments'));d.close()
    def test_section_topology_mismatch_and_missing_thickness_refused(self):
        self.reject('shell-tension',lambda s:s['sections'][0].update(kind='solid'))
        self.reject('shell-tension',lambda s:s['sections'][0].pop('thickness'))
        self.reject('line-tension',lambda s:s['sections'][0].update(kind='truss'))
    def test_line_dimensions_and_parallel_direction_refused(self):
        self.reject('beam-bending',lambda s:s['sections'][0].update(dimensions=['0','.2']))
        self.reject('beam-bending',lambda s:s['sections'][0].update(direction=[1,0,0]))
        self.reject('beam-bending',lambda s:s['sections'][0].update(direction=[0,0,0]))
        self.reject('beam-bending',lambda s:s['sections'][0].update(shape='Unknown'))
    def test_rotations_and_moments_require_appropriate_structural_nodes(self):
        self.reject('membrane-tension',lambda s:s['step']['constraints'][0].update(rotations=['0',None,None]))
        self.reject('line-tension',lambda s:s['step']['constraints'].append({'name':'Bad','nodeSet':'ALL','displacements':[None,None,None],'rotations':['0',None,None]}))
        self.reject('line-tension',lambda s:s['step'].update(moments=[{'name':'Bad','nodeSet':'ALL','momentPerNode':['1','0','0']}]))
    def test_layers_must_be_positive_assigned_and_supported(self):
        self.reject('composite-tension',lambda s:s['sections'][0]['layers'][0].update(thickness='0'))
        self.reject('composite-tension',lambda s:s['sections'][0]['layers'][0].update(material='Missing'))
        self.reject('composite-tension',lambda s:s['sections'][0].update(layers=[]))
    def test_shell_pressure_requires_explicit_side(self):
        self.reject('shell-pressure',lambda s:s['step'].update(pressures=[{'name':'Bad','nodeSet':'TIP','magnitude':'1'}]))
        self.reject('shell-pressure',lambda s:s['step']['pressures'][0].update(face=3))
    def test_expanded_output_dimension_is_explicit_and_validated(self):
        self.reject('shell-bending',lambda s:s['step'].update(elementOutput='Unknown'))
        data,spec=fixture('shell-bending');spec['step']['elementOutput']='TwoD';self.assertTrue(validate_definition(data,spec)['success'])
    def test_original_line_alias_is_preserved_in_solver_input(self):
        data,spec=fixture('line-tension');data=data.replace(b'Type=T3D3,',b'Type=T2D3,')
        with tempfile.TemporaryDirectory() as name:
            p=Path(name);(p/'mesh.inp').write_bytes(data);(p/'analysis.json').write_text(json.dumps(spec))
            host=Path(__file__).resolve().parents[1]/'Analysis/StaticDeck/bin/Release/net10.0/PrePoMaxX.StaticDeck.dll'
            done=subprocess.run(['dotnet',str(host),'build-static',str(p/'mesh.inp'),str(p/'analysis.json'),str(p/'deck.inp')],capture_output=True,text=True)
            self.assertEqual(done.returncode,0,done.stderr);text=(p/'deck.inp').read_text();self.assertIn('Type=T2D3,',text)
            self.assertNotIn('Type=T3D3,',text)


if __name__=='__main__':unittest.main()

"""Meaningful discrete controls and owned mesh-edit publication regressions."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from PyQt6 import QtWidgets
from analysis_editor import AnalysisDialog,validate_definition
from element_family_fixtures import CASES
from viewport import ROOT,Viewport,decode,mesh_command

BASE=ROOT/'X/Analysis/StaticDeck'

def fixture(case):return (BASE/(case+'.inp')).read_bytes(),json.loads((BASE/(case+'.json')).read_text())

class ElementFamilies(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    def test_calculations_and_discrete_editor_preserve_definition(self):
        for case in CASES:
            with self.subTest(case=case):
                data,spec=fixture(case);scene=decode(BASE/(case+'.inp'))
                dialog=AnalysisDialog(None,scene,data,spec)
                self.assertTrue(dialog.validate_current(),dialog.message.text())
                actual=dialog.definition
                self.assertEqual(validate_definition(data,actual)['deckSha256'],validate_definition(data,spec)['deckSha256'])
                dialog.deleteLater()
    def test_discrete_section_compatibility_and_finite_controls(self):
        for case,change in [
            ('spring-pair',lambda s:s['sections'][0].update(secondDof=0)),
            ('spring-axial',lambda s:s['sections'][0].update(dof=1)),
            ('spring-ground',lambda s:s['sections'][0].update(dof=4)),
            ('spring-pair',lambda s:s['sections'][0].update(stiffness='0')),
            ('gap-compression',lambda s:s['sections'][0].update(direction=[0,0,0])),
            ('gap-compression',lambda s:s['sections'][0].update(clearance='NaN')),
            ('mass-spring-frequency',lambda s:s['sections'][1].update(mass='-1')),
            ('mass-spring-frequency',lambda s:s['sections'][1].update(material='Missing'))]:
            with self.subTest(case=case):
                data,spec=fixture(case);change(spec)
                with self.assertRaises(ValueError):validate_definition(data,spec)
    def test_discrete_connectivity_is_exact_and_formulation_preserved(self):
        with tempfile.TemporaryDirectory() as name:
            p=Path(name);data,spec=fixture('spring-pair');(p/'bad.inp').write_bytes(data.replace(b'1,1,2',b'1,1,1'))
            with self.assertRaises(ValueError):decode(p/'bad.inp')
            (p/'bad.inp').write_bytes(data.replace(b'SPRING2',b'SPRING20'))
            with self.assertRaises(ValueError):decode(p/'bad.inp')
    def window(self):
        w=Viewport();w.automated_workflow=True;w.confirm_discard=lambda:True
        data,spec= ((BASE/'cube-mesh.inp').read_bytes(),json.loads((BASE/'cube-analysis.json').read_text()))
        w.load(BASE/'cube-mesh.inp',as_model=True,definition=spec)
        self.addCleanup(w.deleteLater);return w
    def test_owned_mesh_transform_undo_redo_and_failure_preserve_bytes(self):
        w=self.window();original=w.mesh_bytes;before=copy.deepcopy(w.model_scene);w.analysis_valid=True
        w.apply_mesh_edit({'operation':'translate','vector':[2,3,4]})
        transformed=w.mesh_bytes;self.assertNotEqual(original,transformed);self.assertFalse(w.analysis_valid)
        self.assertEqual(w.model_scene['elements'],before['elements'])
        for a,b in zip(before['nodes'],w.model_scene['nodes']):self.assertEqual([b[k]-a[k] for k in ('x','y','z')],[2,3,4])
        w.undo_mesh_edit();self.assertEqual(w.mesh_bytes,original);self.assertTrue(w.analysis_valid)
        w.redo_mesh_edit();self.assertEqual(w.mesh_bytes,transformed);self.assertFalse(w.analysis_valid)
        with self.assertRaises(ValueError):w.apply_mesh_edit({'operation':'scale','vector':[0,1,1],'center':[0,0,0]})
        self.assertEqual(w.mesh_bytes,transformed);self.assertEqual(len(w.mesh_undo),1)
    def test_renumber_maps_all_sets_and_boundary_mesh_requires_complete_region(self):
        w=self.window();w.apply_mesh_edit({'operation':'renumber','startNode':101,'startElement':501})
        self.assertEqual([n['id'] for n in w.model_scene['nodes']],list(range(101,109)))
        self.assertEqual(w.model_scene['elements'][0]['id'],501)
        self.assertIn(b'*Nset, Nset=Z0\n101, 102, 103, 104\n',w.mesh_bytes)
        w.undo_mesh_edit();w.apply_mesh_edit({'operation':'surface','nodeSet':'Z0','formulation':'S4'})
        self.assertEqual(len(w.model_scene['elements']),1);self.assertEqual(len(w.model_scene['nodes']),4)
        self.assertEqual(w.model_scene['elementBlocks'][0]['formulation'],'S4');self.assertEqual(w.definition['sections'],[])
        w.apply_mesh_edit({'operation':'edge','nodeSet':'Y0','formulation':'B31'})
        self.assertEqual(w.model_scene['elements'][0]['nodeIds'],[1,2])
        self.assertEqual(w.model_scene['elementBlocks'][0]['formulation'],'B31')
    def test_mesh_command_existing_output_and_duplicate_recipe_leave_source(self):
        with tempfile.TemporaryDirectory() as name:
            p=Path(name);source=BASE/'cube-mesh.inp';before=source.read_bytes();(p/'out.inp').write_bytes(b'keep')
            (p/'recipe.json').write_text('{"operation":"translate","vector":[1,2,3]}')
            done=subprocess.run(mesh_command()+['edit-mesh',str(source),str(p/'recipe.json'),str(p/'out.inp')],capture_output=True,text=True)
            self.assertNotEqual(done.returncode,0);self.assertEqual((p/'out.inp').read_bytes(),b'keep');self.assertEqual(source.read_bytes(),before)
            (p/'recipe.json').write_text('{"operation":"translate","operation":"renumber"}')
            done=subprocess.run(mesh_command()+['edit-mesh',str(source),str(p/'recipe.json'),str(p/'new.inp')],capture_output=True,text=True)
            self.assertNotEqual(done.returncode,0);self.assertFalse((p/'new.inp').exists())

if __name__=='__main__':unittest.main()

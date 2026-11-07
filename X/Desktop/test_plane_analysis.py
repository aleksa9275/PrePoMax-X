"""Plane/axisymmetric engineering admission and editable desktop round trips."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from PyQt6 import QtWidgets
from analysis_editor import AnalysisDialog, validate_definition
from plane_workflow_fixtures import FAMILIES, build_fixture, build_cylinder
from viewport import decode, mesh_command


class PlaneAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def reject(self, change, case='plane-stress', mesh_change=None):
        data, spec = build_fixture(case)
        change(spec)
        if mesh_change:
            data = mesh_change(data)
        with self.assertRaises(ValueError):
            validate_definition(data, spec)

    def test_all_family_examples_editor_original_validation_and_thickness(self):
        with tempfile.TemporaryDirectory() as name:
            for case in (*FAMILIES, 'axisymmetric-cylinder'):
                with self.subTest(case=case):
                    data, spec = build_cylinder() if case.endswith('cylinder') else build_fixture(case)
                    path = Path(name)/(case+'.inp'); path.write_bytes(data)
                    dialog = AnalysisDialog(None, decode(path), data, spec)
                    self.assertTrue(dialog.validate_current(), dialog.message.text())
                    self.assertEqual(dialog.definition['modelSpace'], spec['modelSpace'])
                    self.assertEqual(dialog.definition['sections'], spec['sections'])
                    dialog.close()

    def test_mismatched_or_unspecified_model_space_rejected(self):
        self.reject(lambda s: s.pop('modelSpace'))
        self.reject(lambda s: s.update(modelSpace='PlaneStrain'))
        self.reject(lambda s: s.update(modelSpace='Unknown'))

    def test_explicit_finite_positive_plane_thickness_required(self):
        self.reject(lambda s: s['sections'][0].pop('thickness'))
        for thickness in ('0', '-1', 'NaN', 'Infinity'):
            with self.subTest(thickness=thickness):
                self.reject(lambda s: s['sections'][0].update(thickness=thickness))

    def test_out_of_plane_values_cannot_be_silently_discarded(self):
        self.reject(lambda s: s['step']['constraints'][0].update(displacements=[None, '0', '1']))
        self.reject(lambda s: s['step']['loads'].append({'name': 'Bad', 'nodeSet': 'TOP', 'forcePerNode': ['1', '0', '2 N']}))
        self.reject(lambda s: s['step'].update(gravityLoads=[{'name': 'Bad', 'elementSet': 'PATCH_1', 'acceleration': ['0', '1', '1']}]))

    def test_xy_plane_and_nonnegative_axisymmetric_radius_required(self):
        self.reject(lambda s: None, mesh_change=lambda b: b.replace(b'11, 0, 0', b'11, 0, 0, 1', 1))
        self.reject(lambda s: None, case='axisymmetric', mesh_change=lambda b: b.replace(b'11, 1, 0', b'11, -1, 0', 1))

    def test_pressure_requires_edges_and_complete_boundary(self):
        for face in (1, 2):
            self.reject(lambda s: s['step'].update(pressures=[{'name': 'Bad', 'elementSet': 'PATCH_1', 'face': face, 'magnitude': '1'}]))
        self.reject(lambda s: s['step'].update(pressures=[{'name': 'Bad', 'nodeSet': 'ALL', 'magnitude': 'NaN'}]))

    def test_planar_formulation_changes_preserve_topology_and_require_matching_model_space(self):
        data, spec = build_fixture('plane-stress')
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name); source = folder/'source.inp'; target = folder/'target.inp'; choices = folder/'choices.json'
            source.write_bytes(data); before = decode(source)
            choices.write_text(json.dumps([b['formulation'].replace('CPS', 'CPE') for b in before['elementBlocks']]))
            done = subprocess.run([*mesh_command(), 'set-solid-formulations', str(source), str(target), str(choices)], capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stderr)
            after = decode(target)
            self.assertEqual(before['nodes'], after['nodes']); self.assertEqual(before['elements'], after['elements'])
            self.assertEqual(source.read_bytes(), data)
            with self.assertRaises(ValueError): validate_definition(target.read_bytes(), spec)
            spec['modelSpace'] = 'PlaneStrain'
            self.assertTrue(validate_definition(target.read_bytes(), spec)['success'])


if __name__ == '__main__':
    unittest.main()

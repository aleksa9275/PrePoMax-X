"""Real Qt fields -> original C# validation; no engineering evaluator in Python."""
import copy
import json
import subprocess
import unittest
from pathlib import Path
from PyQt6 import QtWidgets
from analysis_editor import AnalysisDialog, new_definition, validate_definition
from jobs import ROOT


class AnalysisEditorBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        cls.mesh = (ROOT / 'X/Analysis/StaticDeck/cube-mesh.inp').read_bytes()
        cls.spec = json.loads((ROOT / 'X/Analysis/StaticDeck/cube-analysis.json').read_text())
        done = subprocess.run(['dotnet', str(ROOT / 'X/Desktop/MeshScene/bin/Release/net10.0/PrePoMaxX.MeshScene.dll'),
            str(ROOT / 'X/Analysis/StaticDeck/cube-mesh.inp')], capture_output=True, text=True, check=True, timeout=60)
        cls.scene = json.loads(done.stdout)

    def dialog(self, definition=None):
        return AnalysisDialog(None, self.scene, self.mesh, definition if definition is not None else self.spec)

    def test_named_sets_come_from_original_reader(self):
        self.assertEqual({row['name']: row['count'] for row in self.scene['nodeSets']},
                         {'NALL': 8, 'X0': 4, 'Y0': 4, 'Z0': 4, 'X1': 4})
        self.assertEqual(self.scene['elementSets'], [{'name': 'SOLID', 'count': 1}])

    def test_controls_preserve_free_dofs_and_per_node_force(self):
        dialog = self.dialog()
        self.assertEqual(dialog.collect(), self.spec)
        self.assertTrue(dialog.validate_current(), dialog.message.text())
        self.assertFalse(dialog.validation['solverExecuted'])

    def test_changed_material_and_force_reach_original_writer(self):
        dialog = self.dialog()
        before = validate_definition(self.mesh, self.spec)
        dialog.materials.table.item(0, 1).setText('105 GPa')
        dialog.loads.table.item(0, 2).setText('50 N')
        dialog.apply()
        self.assertEqual(dialog.result(), QtWidgets.QDialog.DialogCode.Accepted)
        self.assertEqual(dialog.definition['materials'][0]['youngsModulus'], '105 GPa')
        self.assertEqual(dialog.definition['step']['loads'][0]['forcePerNode'][0], '50 N')
        self.assertNotEqual(dialog.validation['deckSha256'], before['deckSha256'])
        self.assertEqual(self.spec['materials'][0]['youngsModulus'], '210 GPa')

    def test_bad_reference_cannot_apply_and_preserves_original(self):
        before = copy.deepcopy(self.spec)
        dialog = self.dialog()
        dialog.sections.table.item(0, 1).setText('MissingMaterial')
        dialog.apply()
        self.assertNotEqual(dialog.result(), QtWidgets.QDialog.DialogCode.Accepted)
        self.assertIsNone(dialog.definition)
        self.assertTrue(dialog.message.text())
        self.assertEqual(self.spec, before)

    def test_new_model_requires_explicit_units_and_properties(self):
        fresh = new_definition()
        self.assertEqual(fresh['unitSystem'], '')
        self.assertEqual(fresh['step']['constraints'], [])
        dialog = self.dialog(fresh)
        self.assertFalse(dialog.validate_current())
        self.assertIn('Explicit', dialog.message.text())

    def test_missing_set_is_preserved_for_authoritative_rejection(self):
        spec = copy.deepcopy(self.spec)
        spec['step']['constraints'][0]['nodeSet'] = 'MissingSet'
        dialog = self.dialog(spec)
        self.assertEqual(dialog.collect()['step']['constraints'][0]['nodeSet'], 'MissingSet')
        self.assertFalse(dialog.validate_current())

    def test_edit_invalidates_previous_validation(self):
        dialog = self.dialog()
        self.assertTrue(dialog.validate_current())
        dialog.loads.table.item(0, 2).setText('not a force')
        self.assertIsNone(dialog.validation)
        self.assertIsNone(dialog.definition)
        self.assertFalse(dialog.validate_current())


if __name__ == '__main__':
    unittest.main()

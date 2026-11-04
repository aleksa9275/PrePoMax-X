"""Session set authoring through the real desktop host and editor."""
import json
import unittest

from PyQt6 import QtCore, QtWidgets

from analysis_editor import AnalysisDialog, validate_definition
from jobs import ROOT
from viewport import Viewport


class NamedSetWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self):
        self.window = Viewport()
        self.addCleanup(self.window.deleteLater)
        base = ROOT / 'X/Analysis/StaticDeck'
        self.mesh = base / 'cube-mesh.inp'
        definition = json.loads((base / 'cube-analysis.json').read_text())
        self.window.load(self.mesh, as_model=True, definition=definition)
        self.window.analysis_valid = True

    def test_new_sets_reach_original_validation_and_keep_source(self):
        original = self.mesh.read_bytes()
        self.window.add_named_set('node', 'LoadedNodes', '2 3,6,7')
        self.window.add_named_set('element', 'SolidPick', '1')
        self.assertFalse(self.window.analysis_valid)
        self.assertTrue(self.window.editor_dirty)
        self.assertEqual(self.mesh.read_bytes(), original)
        dialog = AnalysisDialog(None, self.window.model_scene, self.window.mesh_bytes,
                                self.window.definition)
        self.addCleanup(dialog.deleteLater)
        self.assertGreaterEqual(dialog.loads.table.cellWidget(0, 1).findText('LoadedNodes'), 0)
        self.assertGreaterEqual(dialog.sections.table.cellWidget(0, 2).findText('SolidPick'), 0)
        self.window.definition['step']['loads'][0]['nodeSet'] = 'LoadedNodes'
        self.window.definition['sections'][0]['elementSet'] = 'SolidPick'
        outcome = validate_definition(self.window.mesh_bytes, self.window.definition)
        self.assertTrue(outcome['success'])

    def test_bad_ids_and_existing_name_leave_model_unchanged(self):
        original = self.window.mesh_bytes
        for kind, name, ids in [('node', 'nall', '2'), ('node', 'Bad', '999'),
                                ('node', 'Repeated', '2,2'), ('element', 'WrongKind', '2')]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.window.add_named_set(kind, name, ids)
        self.assertEqual(self.window.mesh_bytes, original)
        self.assertTrue(self.window.analysis_valid)
        self.assertFalse(self.window.editor_dirty)

    def test_dialog_can_seed_original_nonsequential_pick(self):
        source = ROOT / 'X/Desktop/nonsequential-cube.inp'
        self.window.load(source, as_model=True)
        self.window.selection = {'elementId': 7001, 'nearestVertexNodeId': 105}
        errors = []

        def submit():
            dialog = self.app.activeModalWidget()
            try:
                self.assertIsInstance(dialog, QtWidgets.QDialog)
                kind = dialog.findChild(QtWidgets.QComboBox)
                kind.setCurrentIndex(1)
                pick = next(button for button in dialog.findChildren(QtWidgets.QPushButton)
                            if button.text() == 'Use picked ID')
                pick.click()
                name, ids = dialog.findChildren(QtWidgets.QLineEdit)
                self.assertEqual(ids.text(), '7001')
                name.setText('PickedElement')
                dialog.findChild(QtWidgets.QDialogButtonBox).button(
                    QtWidgets.QDialogButtonBox.StandardButton.Ok).click()
            except (AssertionError, AttributeError, StopIteration) as error:
                errors.append(error)
                if dialog is not None:
                    dialog.reject()

        QtCore.QTimer.singleShot(0, submit)
        self.window.add_set_dialog()
        if errors:
            raise errors[0]
        self.assertIn({'name': 'PickedElement', 'count': 1}, self.window.model_scene['elementSets'])


if __name__ == '__main__':
    unittest.main()

"""Check that a read-only VIS document stays separate from editable analysis state."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PyQt6 import QtWidgets

from viewport import ROOT, Viewport


class CadWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_replacing_documents_keeps_analysis_and_geometry_separate(self):
        window = Viewport()
        self.addCleanup(window.deleteLater)
        mesh = ROOT / "X/Desktop/nonsequential-cube.inp"
        vis = ROOT / "X/Feasibility/Cad/fixtures/l-bracket.vis"
        results = ROOT / ".project/reports/windows-reference/solver/uniaxial.frd"
        window.load(mesh, as_model=True)
        original = window.model_scene
        window.editor_dirty = True
        with patch.object(window, "confirm_discard", return_value=False):
            window.load(vis)
        self.assertIs(window.model_scene, original)
        self.assertIs(window.scene, original)

        with patch.object(window, "confirm_discard", return_value=True), TemporaryDirectory() as directory:
            invalid = Path(directory) / "invalid.vis"
            invalid.write_text("VIS file format: 1\n")
            with self.assertRaises(ValueError):
                window.load(invalid)
            self.assertIs(window.model_scene, original)
            self.assertIs(window.scene, original)
            self.assertTrue(window.editor_dirty)
            window.load(vis)

        self.assertIsNone(window.model_scene)
        self.assertIsNone(window.mesh_bytes)
        self.assertFalse(window.run_action.isEnabled())
        self.assertFalse(window.editor_dirty)
        cylinder = window.cad_faces[9]
        self.assertEqual(cylinder.text(1), "Cylinder")
        self.assertEqual({cylinder.child(i).text(0): cylinder.child(i).text(1)
                          for i in range(cylinder.childCount())}["Radius"], "10")

        window.load(results)
        self.assertFalse(window.cad_edge_actor.GetVisibility())
        self.assertFalse(window.cad_faces)
        self.assertGreater(window.fields.count(), 1)
        window.load(mesh, as_model=True)
        self.assertTrue(window.run_action.isEnabled())
        self.assertTrue(window.add_set_action.isEnabled())
        self.assertEqual(window.scene["elements"][0]["id"], 7001)


if __name__ == "__main__":
    unittest.main()

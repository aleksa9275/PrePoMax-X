"""GUI publication/cancellation boundaries; engineering parsing uses real host checks."""
import time
import unittest
from unittest.mock import Mock, patch
from PyQt6 import QtCore, QtWidgets
from viewport import ROOT, Viewport
from cad_import import CadImportCancelled


class NativeMeshLifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def wait(self, predicate):
        deadline = time.monotonic() + 5
        while not predicate() and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(.01)
        self.assertTrue(predicate())

    def window(self):
        window = Viewport()
        self.addCleanup(window.deleteLater)
        window.automated_workflow = True
        window.load(ROOT / 'X/Feasibility/Cad/fixtures/l-bracket.vis')
        window.cad_document = Mock()
        return window

    def test_cancel_and_failed_mesh_keep_document_and_previous_scene(self):
        for mode in ('cancel', 'failure', 'late-cancel'):
            with self.subTest(mode=mode):
                window = self.window()
                document, scene = window.cad_document, window.scene
                mesh = Mock()
                def create(*args, cancel, **kwargs):
                    if mode == 'cancel':
                        cancel.wait(5)
                        raise CadImportCancelled()
                    if mode == 'failure':
                        raise ValueError('invalid native mesh')
                    return mesh
                with patch('cad_job.CadMesh', side_effect=create):
                    window.start_cad_mesh(3)
                    self.assertTrue(window.busy)
                    self.assertFalse(window.open_action.isEnabled())
                    if mode == 'cancel':
                        QtCore.QTimer.singleShot(10, window.cancel_operation)
                    elif mode == 'late-cancel':
                        self.assertTrue(window.mesh_job.wait(5000))
                        window.cancel_operation()
                    self.wait(lambda: window.mesh_job is None)
                self.assertFalse(window.mesh_result['success'])
                self.assertIs(window.scene, scene)
                self.assertIs(window.cad_document, document)
                self.assertTrue(window.mesh_action.isEnabled())
                document.close.assert_not_called()
                if mode == 'late-cancel':
                    mesh.close.assert_called_once()
                window.editor_dirty = False
                window.close()
                document.close.assert_called_once()

    def test_close_waits_for_mesher_before_cleaning_document(self):
        window = self.window()
        document = window.cad_document
        def create(*args, cancel, **kwargs):
            cancel.wait(5)
            document.close.assert_not_called()
            raise CadImportCancelled()
        with patch('cad_job.CadMesh', side_effect=create):
            window.start_cad_mesh(3)
            QtCore.QTimer.singleShot(10, window.close)
            self.wait(lambda: window.mesh_job is None and window.cad_document is None)
        document.close.assert_called_once()
        self.assertTrue(window.mesh_result['cancelled'])


if __name__ == '__main__':
    unittest.main()

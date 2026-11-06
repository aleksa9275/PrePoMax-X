"""Atomic CAD publication, stale results, cancellation and deferred closing."""
import time
import unittest
from unittest.mock import Mock,patch
from PyQt6 import QtCore,QtWidgets
from cad_import import CadImportCancelled
from viewport import ROOT,Viewport


class CadEditLifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def wait(self,predicate):
        until=time.monotonic()+5
        while not predicate() and time.monotonic()<until:
            self.app.processEvents();time.sleep(.01)
        self.assertTrue(predicate())

    def window(self):
        w=Viewport();w.automated_workflow=True
        w.confirm_discard=Mock(return_value=True)
        self.addCleanup(w.deleteLater)
        w.load(ROOT/'X/Feasibility/Cad/fixtures/l-bracket.vis')
        w.cad_document=Mock();w.cad_mesh=Mock()
        w.model_scene=w.scene;w.definition={'original':True};w.mesh_bytes=b'original mesh'
        w.analysis_valid=True;w.editor_dirty=True
        return w

    def test_failure_cancel_and_late_cancel_preserve_every_active_input(self):
        for mode in ['failure','cancel','late-cancel']:
            with self.subTest(mode=mode):
                w=self.window();doc,mesh,scene=w.cad_document,w.cad_mesh,w.scene
                output=Mock()
                def apply(*args,cancel,**kw):
                    if mode=='failure':raise ValueError('CAD failed before publication')
                    if mode=='cancel':cancel.wait(5);raise CadImportCancelled()
                    return output
                with patch('cad_operations.apply_edit',side_effect=apply):
                    w.operations.start(1,'translate',[1,2,3])
                    self.assertTrue(w.busy);self.assertFalse(w.open_action.isEnabled())
                    if mode=='cancel':QtCore.QTimer.singleShot(10,w.cancel_operation)
                    if mode=='late-cancel':self.assertTrue(w.operations.job.wait(5000));w.cancel_operation()
                    self.wait(lambda:w.operations.job is None)
                self.assertFalse(w.operations.result['success'])
                self.assertIs(w.cad_document,doc);self.assertIs(w.cad_mesh,mesh);self.assertIs(w.scene,scene)
                self.assertEqual(w.mesh_bytes,b'original mesh');self.assertEqual(w.definition,{'original':True})
                self.assertTrue(w.editor_dirty);doc.close.assert_not_called();mesh.close.assert_not_called()
                if mode=='late-cancel':output.close.assert_called_once()
                w.editor_dirty=False;w.close()

    def test_success_clears_dependent_mesh_analysis_and_regions(self):
        w=self.window();doc,mesh=w.cad_document,w.cad_mesh
        output=Mock(scene=w.scene,source=ROOT/'X/Feasibility/Cad/fixtures/l-bracket.vis')
        with patch('cad_operations.apply_edit',return_value=output):
            w.operations.start(1,'translate',[1,2,3]);self.wait(lambda:w.operations.job is None)
        self.assertTrue(w.operations.result['success']);self.assertIs(w.cad_document,output)
        self.assertIsNone(w.cad_mesh);self.assertIsNone(w.model_scene);self.assertIsNone(w.definition)
        self.assertIsNone(w.mesh_bytes);self.assertFalse(w.analysis_valid);self.assertTrue(w.editor_dirty)
        self.assertFalse(w.regions.refs);self.assertIsNone(w.regions.result)
        doc.close.assert_called_once();mesh.close.assert_called_once()
        w.editor_dirty=False;w.close()

    def test_close_waits_for_worker_before_releasing_geometry(self):
        w=self.window();doc=w.cad_document
        def apply(*args,cancel,**kw):
            cancel.wait(5);doc.close.assert_not_called();raise CadImportCancelled()
        with patch('cad_operations.apply_edit',side_effect=apply):
            w.operations.start(1,'translate',[1,2,3]);QtCore.QTimer.singleShot(10,w.close)
            self.wait(lambda:w.operations.job is None and w.cad_document is None)
        doc.close.assert_called_once();self.assertTrue(w.operations.result['cancelled'])

    def test_pmx_geometry_mutation_refused(self):
        w=self.window();w.pmx_session=Mock()
        with self.assertRaises(ValueError):w.operations.start(1,'translate',[1,2,3])
        self.assertIsNone(w.operations.job)
        w.editor_dirty=False;w.close()

    def test_export_success_preserves_document_mesh_definition_and_unsaved_state(self):
        w=self.window();doc,mesh,scene=w.cad_document,w.cad_mesh,w.scene
        w.pmx_session=Mock()  # Geometry exchange may read an immutable PMX preview.
        export=Mock();export.publish.return_value={'nativeReadbackPassed':True}
        with patch('cad_operations.prepare_export',return_value=export):
            w.operations.start(1,'export','unused.step');self.wait(lambda:w.operations.job is None)
        self.assertTrue(w.operations.result['success']);export.publish.assert_called_once_with('unused.step')
        export.close.assert_called_once();self.assertIs(w.cad_document,doc);self.assertIs(w.cad_mesh,mesh)
        self.assertIs(w.scene,scene);self.assertTrue(w.analysis_valid);self.assertTrue(w.editor_dirty)
        w.editor_dirty=False;w.close()

    def test_late_export_cancel_publishes_nothing(self):
        w=self.window();doc,mesh=w.cad_document,w.cad_mesh;export=Mock()
        with patch('cad_operations.prepare_export',return_value=export):
            w.operations.start(1,'export','unused.step')
            self.assertTrue(w.operations.job.wait(5000));w.cancel_operation()
            self.wait(lambda:w.operations.job is None)
        self.assertTrue(w.operations.result['cancelled']);export.publish.assert_not_called()
        export.close.assert_called_once();self.assertIs(w.cad_document,doc);self.assertIs(w.cad_mesh,mesh)
        w.editor_dirty=False;w.close()


if __name__=='__main__':unittest.main()

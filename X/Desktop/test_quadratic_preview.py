"""C3D10 configuration/job transport and checked lossless mesh export."""
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock,patch
from PyQt6 import QtWidgets
from mesh_export import publish_mesh
from viewport import Viewport,ROOT


class QuadraticPreview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_quadratic_open_allows_configuration_and_frozen_job_submission(self):
        from quadratic_analysis import force_fixture
        from analysis_editor import validate_definition
        w=Viewport();w.automated_workflow=True;self.addCleanup(w.deleteLater)
        with TemporaryDirectory() as directory:
            path=Path(directory)/'quadratic.inp'
            mesh,spec=force_fixture();path.write_bytes(mesh)
            w.load(path,as_model=True,definition=spec)
            self.assertTrue(w.quadratic_mesh);self.assertTrue(w.run_action.isEnabled());self.assertTrue(w.configure_action.isEnabled())
            self.assertTrue(w.export_mesh_action.isEnabled())
            self.assertTrue(validate_definition(mesh,spec)['success'])
            w.analysis_valid=True
            with patch.object(w.job,'start') as start:
                w.run_model()
                start.assert_called_once()
                self.assertEqual(start.call_args.kwargs['mesh_bytes'],mesh)
                self.assertEqual(start.call_args.kwargs['definition'],spec)
            w.load(ROOT/'X/Desktop/nonsequential-cube.inp',as_model=True)
            self.assertFalse(w.quadratic_mesh);self.assertTrue(w.configure_action.isEnabled())
        w.editor_dirty=False;w.close()

    def test_mesh_export_refuses_changed_bytes_readback_and_existing_destinations(self):
        data=b'verified mesh';scene={'SourceSha256':hashlib.sha256(data).hexdigest(),'nodes':[{'id':1}],'elements':[{'id':1}]}
        with TemporaryDirectory() as directory:
            target=Path(directory)/'mesh.inp';decode=Mock(return_value=scene)
            with self.assertRaises(ValueError):publish_mesh(b'changed',scene,target,decode)
            self.assertFalse(target.exists());decode.assert_not_called()
            with self.assertRaises(ValueError):publish_mesh(data,scene,target,lambda p:{**scene,'elements':[]})
            self.assertFalse(target.exists())
            receipt=publish_mesh(data,scene,target,decode)
            self.assertTrue(receipt['originalReadbackPassed']);self.assertEqual(target.read_bytes(),data)
            with self.assertRaises(FileExistsError):publish_mesh(data,scene,target,decode)
            self.assertEqual(target.read_bytes(),data)


if __name__=='__main__':unittest.main()

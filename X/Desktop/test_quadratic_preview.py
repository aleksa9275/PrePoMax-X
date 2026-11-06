"""Quadratic mesh inspection/export never authorizes a numerical job."""
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

    def test_quadratic_open_gates_controls_and_direct_job_calls(self):
        w=Viewport();w.automated_workflow=True;self.addCleanup(w.deleteLater)
        with TemporaryDirectory() as directory:
            path=Path(directory)/'quadratic.inp'
            path.write_text('*Node\n1,0,0,0\n2,1,0,0\n3,0,1,0\n4,0,0,1\n5,.5,0,0\n6,.5,.5,0\n7,0,.5,0\n8,0,0,.5\n9,.5,0,.5\n10,0,.5,.5\n*Element, Type=C3D10, Elset=SOLID\n1,1,2,3,4,5,6,7,8,9,10\n')
            w.load(path,as_model=True)
            self.assertTrue(w.quadratic_preview);self.assertFalse(w.run_action.isEnabled());self.assertFalse(w.configure_action.isEnabled())
            self.assertTrue(w.export_mesh_action.isEnabled())
            with patch.object(w.job,'start') as start:
                for action in [w.run_model,w.configure_model,lambda:w.start_job(path,None,definition=w.definition,mesh_bytes=w.mesh_bytes)]:
                    with self.assertRaises(ValueError):action()
                start.assert_not_called()
            w.load(ROOT/'X/Desktop/nonsequential-cube.inp',as_model=True)
            self.assertFalse(w.quadratic_preview);self.assertTrue(w.configure_action.isEnabled())
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

"""Partial native copy output inventories cannot replace the active geometry."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock,patch
from cad_import import NativeCadTool,CadImportCancelled,file_sha256
from cad_edit import apply_edit


class CopyOutputTransactions(unittest.TestCase):
    def test_partial_extra_and_cancelled_copy_outputs_are_cleaned_before_decoding(self):
        scene={'cad':{'entities':{
            'solid':[{'id':1,'properties':{'volume':[1.],'surface_area':[6.],
                'center_of_mass':[0.,0.,0.],'inertia_at_center_of_mass':[1.,0.,0.,0.,1.,0.,0.,0.,1.],
                'shell_ids':[1],'face_ids':[1]}}],
            'shell':[{'id':1}],'face':[{'id':1,'properties':{'edge_ids':[1]}}],
            'edge':[{'id':1,'properties':{'vertex_ids':[1,2]}}],'vertex':[{'id':1},{'id':2}]}}}
        for mode in ['partial','extra','cancelled']:
            with self.subTest(mode=mode),TemporaryDirectory() as directory:
                source=Path(directory)/'original.brep';source.write_bytes(b'original CAD bytes')
                tool=Mock(spec=NativeCadTool);tool.command=['unused-native-command']
                document=Mock(tool=tool,parts=[(source,Path(directory)/'original.vis')],edits=[],
                              identities={source:file_sha256(source)},source=source)
                roots=[]
                def command(arguments,work,*args,**kwargs):
                    roots.append(work.parent)
                    for i in range(1,4 if mode=='extra' else 2):
                        (work/f'operation-0001-output_{i:04d}.brep').write_bytes(b'partial copy')
                    if mode=='cancelled':raise CadImportCancelled('cancelled during copies')
                with patch('cad_edit.run_stage',side_effect=command):
                    with self.assertRaises(CadImportCancelled if mode=='cancelled' else ValueError):
                        apply_edit(document,lambda *a,**k:scene,1,'copy_translate',{'translation':[1,0,0],'copies':2})
                self.assertTrue(roots);self.assertTrue(all(not p.exists() for p in roots))
                self.assertEqual(source.read_bytes(),b'original CAD bytes');self.assertEqual(document.edits,[])
                tool.convert_parts.assert_not_called();document.close.assert_not_called()


if __name__=='__main__':unittest.main()

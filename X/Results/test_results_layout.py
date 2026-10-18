import unittest
from unittest.mock import patch
from pathlib import Path
import results_layout as layout

class SourceContracts(unittest.TestCase):
 def test_all_source_pins(self):
  for pin in [layout.BASELINE,'912fb3d08014f246d48bef14d62a2cba0fdf5bb0','f6273e39983e06042ae8b06e9a3dd0f729ea4b91']:
   self.assertGreaterEqual(len(layout.verify(pin)),155)
 def test_upstream_decoder_change_rejected(self):
  original=layout.original
  def changed(pin,path):
   data=original(pin,path)
   return data.replace(b'width = 12;',b'width = 13;')if pin!=layout.BASELINE and path==layout.FRD else data
  with patch.object(layout,'original',changed),self.assertRaises(AssertionError):layout.verify('f6273e39983e06042ae8b06e9a3dd0f729ea4b91')
 def test_invariant_math_change_rejected(self):
  read=Path.read_bytes
  def changed(path):
   data=read(path)
   return data.replace(b'vonMises',b'changed')if str(path).endswith('/Field.cs')else data
  with patch.object(Path,'read_bytes',changed),self.assertRaises((AssertionError,ValueError)):layout.verify()
 def test_stream_decoder_change_rejected(self):
  read=Path.read_bytes
  def changed(path):
   data=read(path)
   return data+b'changed'if str(path).endswith('/FrdStreamReader.cs')else data
  with patch.object(Path,'read_bytes',changed),self.assertRaises((AssertionError,ValueError)):layout.verify()
 def test_legacy_orchestration_preserved(self):
  result=layout.render();legacy=result[layout.FRD[:-3]+'.Legacy.cs']
  self.assertIn(b'prevFieldData = fieldData.DeepClone();',legacy)
  self.assertIn(b'FeMesh mesh = new FeMesh(',legacy)
  self.assertIn(b'results.ScaleFieldValues',legacy)
  self.assertNotIn(b'FeResults Read(',result[layout.FRD])
 def test_original_tools_helper_edit_rejected(self):
  read=Path.read_bytes
  def changed(path):
   data=read(path)
   return data+b'changed'if str(path).endswith('/Tools.Results.cs')else data
  with patch.object(Path,'read_bytes',changed),self.assertRaises(ValueError):layout.verify()

 def test_upstream_dat_numeric_decoder_edit_rejected(self):
  original=layout.original
  def changed(pin,path):
   data=original(pin,path)
   return data.replace(b'if (!double.TryParse(valueAsString, out value))',b'if (false)')if pin!=layout.BASELINE and path==layout.DAT else data
  with patch.object(layout,'original',changed),self.assertRaises(AssertionError):layout.verify('f6273e39983e06042ae8b06e9a3dd0f729ea4b91')
 def test_original_history_entry_edit_rejected(self):
  read=Path.read_bytes
  def changed(path):
   data=read(path)
   return data.replace(b'_values.Add(value);',b'_values.Add(0);')if str(path).endswith('/HistoryResultEntries.cs')else data
  with patch.object(Path,'read_bytes',changed),self.assertRaises(AssertionError):layout.verify()
 def test_legacy_dat_and_persistence_preserved(self):
  result=layout.render_dat();legacy=result[layout.DAT[:-3]+'.Legacy.cs']
  self.assertIn(b'GetAxisymmetricSegmentsPerRevolution',legacy)
  self.assertIn(b'HistoryResults Read(',legacy)
  self.assertIn(b'GetHistoryOutput(',legacy)
  self.assertNotIn(b'HistoryResults Read(',result[layout.DAT])
  self.assertIn(b'Tools.Compress',result[layout.ENTRIES[:-3]+'.Legacy.cs'])
  self.assertNotIn(b'Tools.Compress',result[layout.ENTRIES])

if __name__=='__main__':unittest.main()

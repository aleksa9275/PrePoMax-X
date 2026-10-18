import unittest
from pathlib import Path
from unittest.mock import patch
import job_layout
class JobContracts(unittest.TestCase):
 def test_all_source_pins(self):
  for revision in [job_layout.BASELINE,'912fb3d08014f246d48bef14d62a2cba0fdf5bb0','f6273e39983e06042ae8b06e9a3dd0f729ea4b91']:self.assertEqual(len(job_layout.verify(revision)),5)
 def test_changed_shared_body_rejected(self):
  read=Path.read_bytes
  def modified(path):return read(path)+b'changed'if path==job_layout.ROOT/'CaeJob/ExecutableJob.cs'else read(path)
  with patch.object(Path,'read_bytes',modified),self.assertRaises(ValueError):job_layout.verify()
 def test_changed_legacy_body_rejected(self):
  read=Path.read_bytes
  def modified(path):return read(path)+b'changed'if path==job_layout.ROOT/'CaeJob/ExecutableJob.Legacy.cs'else read(path)
  with patch.object(Path,'read_bytes',modified),self.assertRaises(ValueError):job_layout.verify()
 def test_changed_enum_rejected(self):
  read=Path.read_bytes
  def modified(path):return read(path).replace(b'        OK,',b'        Other,')if path==job_layout.ROOT/'CaeJob/JobStatus.cs'else read(path)
  with patch.object(Path,'read_bytes',modified),self.assertRaises(ValueError):job_layout.verify()
if __name__=='__main__':unittest.main()

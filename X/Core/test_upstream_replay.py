"""Regression controls for upstream replay provenance; no network or branch mutations."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).parent))

SPEC = importlib.util.spec_from_file_location("core_verify", Path(__file__).with_name("verify.py"))
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class UpstreamReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = VERIFY.sources()

    def replay(self, name="3.0.0-rc2"):
        with tempfile.TemporaryDirectory(prefix="prepomaxx-replay-control-") as folder:
            destination = Path(folder)
            report = VERIFY.prepare_upstream_sources(name, destination, self.sources)
            for row in report["sources"]:
                self.assertEqual(VERIFY.sha((destination / row["path"]).read_bytes()), row["compiledSha256"])
            fixture = report["fixture"]
            self.assertEqual(VERIFY.sha((destination / fixture["path"]).read_bytes()), fixture["sha256"])
            return report

    def test_both_reviewed_snapshots_reproduce_the_guarded_source_closure(self):
        for name in ("3.0.0-rc2", "post-rc2-2026-10-17"):
            with self.subTest(name=name):
                report = self.replay(name)
                self.assertEqual(len(report["sources"]), 48)
                self.assertEqual(sum(row["adapter"] is not None for row in report["sources"]), 7)

    def test_moving_branch_ref_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "not a reviewed immutable replay pin"):
            self.replay("master")

    def test_unreviewed_immutable_commit_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "not a reviewed immutable replay pin"):
            self.replay(VERIFY.BASELINE)

    def reject_altered_git_blob(self, path, transform, message):
        original = subprocess.check_output

        def altered(command, **kwargs):
            data = original(command, **kwargs)
            if command[:2] == ["git", "show"] and command[2].endswith(":" + path):
                return transform(data)
            return data

        with patch.object(VERIFY.subprocess, "check_output", side_effect=altered):
            with self.assertRaisesRegex(ValueError, message):
                self.replay()

    def test_changed_upstream_engineering_blob_is_rejected(self):
        self.reject_altered_git_blob("CaeMesh/Nodes/FeNode.cs", lambda data: data + b"\n// changed upstream\n",
                                     "Upstream engineering source changed")

    def test_changed_exception_extraction_boundary_is_rejected(self):
        # Alter only the replay object; the baseline and working source stay intact.
        original = subprocess.check_output

        def altered(command, **kwargs):
            data = original(command, **kwargs)
            if command[:2] == ["git", "show"] and command[2] == \
                    "912fb3d08014f246d48bef14d62a2cba0fdf5bb0:CaeGlobals/ExceptionTools.cs":
                return data + b"\n// changed exception boundary\n"
            return data

        with patch.object(VERIFY.subprocess, "check_output", side_effect=altered):
            with self.assertRaisesRegex(ValueError, "exception boundary changed"):
                self.replay()

    def test_changed_windows_import_adapter_is_rejected(self):
        self.reject_altered_git_blob("CaeMesh/GeometryTools.cs",
                                     lambda data: data.replace(b"using System.Windows.Forms.VisualStyles;\n", b""),
                                     "GeometryTools import boundary changed")

    def test_changed_upstream_vectors_are_rejected(self):
        self.reject_altered_git_blob("CaeMesh/Meshing/Transfinite/Cpp/three_block_vectors.txt",
                                     lambda data: data + b"\nchanged vectors\n", "mapping vectors changed")

    def test_changed_original_mesh_parser_is_rejected(self):
        self.reject_altered_git_blob("CaeModel/FileInOut/Input/InpModel/InpFileReader.cs",
                                     lambda data: data + b"\n// changed parser\n", "source extraction changed")

    def test_changed_original_enum_metadata_is_rejected(self):
        self.reject_altered_git_blob("CaeGlobals/DynamicTypeDescriptor/DynamicTypeDescriptor.cs",
                                     lambda data: data + b"\n// changed metadata boundary\n", "source extraction changed")

    def test_changed_reviewed_portable_boundary_is_rejected(self):
        original = Path.read_bytes

        def altered(path):
            data = original(path)
            return data + b"\n// unreviewed boundary change\n" if path.name == "InpFileReader.MeshData.cs" else data

        with patch.object(Path, "read_bytes", altered):
            with self.assertRaisesRegex(ValueError, "Reviewed mesh workflow source changed"):
                VERIFY.sources()


if __name__ == "__main__":
    unittest.main()

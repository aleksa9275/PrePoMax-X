"""Exercise the CAD process boundary without requiring the Windows runtime."""
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from cad_import import REFERENCE_RECEIPT, ReferenceCadTool, convert_cad


TOOL = """
from pathlib import Path
import sys
mode, operation, source, target, *options = sys.argv[1:]
source, target = Path(source), Path(target)
if operation == "BREP_VISUALIZATION":
    assert options == ["0.01", "1", "0.26"]
    assert source.read_text() in {"STEP", "BREP"}
    if mode != "no vis":
        target.write_text("visualization")
else:
    assert operation == ("STEP" if source.suffix == ".step" else "BREP") + "_ASSEMBLY_SPLIT_TO_COMPOUNDS"
    assert not options
    if mode != "no part":
        target.with_name("part_solid_0001.brep").write_text(source.read_text())
    if mode == "two parts":
        target.with_name("part_solid_0002.brep").write_text("another part")
    if mode == "modified input":
        source.write_text("modified")
    if mode == "stale vis":
        (target.parent / "geometry.vis").write_text("stale")
    if mode == "failure":
        sys.exit(7)
"""


class CadImport(unittest.TestCase):
    def setUp(self):
        scratch = TemporaryDirectory(prefix="cad test ")
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        self.tool = self.root / "fake tool.py"
        self.tool.write_text(TOOL)

    def command(self, mode="success"):
        return [sys.executable, str(self.tool), mode]

    def test_split_and_visualize_step_and_brep(self):
        for suffix in (".STEP", ".brep"):
            with self.subTest(suffix=suffix):
                source = self.root / ("source model" + suffix)
                expected = suffix[1:].upper()
                source.write_text(expected)
                brep, vis = convert_cad(source, self.root / ("work" + suffix), self.command())
                self.assertEqual(brep.read_text(), expected)
                self.assertEqual(vis.read_text(), "visualization")
                self.assertEqual(source.read_text(), expected)

    def test_refuses_invalid_outputs_and_does_not_modify_original(self):
        source = self.root / "model.step"
        source.write_text("STEP")
        for mode, diagnostic in (("no part", "got 0"), ("two parts", "got 2"), ("no vis", "geometry.vis"),
                                 ("failure", "status 7"), ("stale vis", "unexpectedly wrote"),
                                 ("modified input", "modified its staged input")):
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, diagnostic):
                convert_cad(source, self.root / mode, self.command(mode))
            self.assertEqual(source.read_text(), "STEP")

    def test_refuses_existing_workspace_and_oversized_input(self):
        source = self.root / "model.step"
        source.write_bytes(b"STEP")
        with self.assertRaises(FileExistsError):
            convert_cad(source, self.root, self.command())
        with patch("cad_import.MAX_CAD_BYTES", 2), self.assertRaisesRegex(ValueError, "no larger"):
            convert_cad(source, self.root / "oversized", self.command())

    def test_reference_refuses_missing_or_changed_runtime(self):
        runtime = self.root / "runtime"
        runtime.mkdir()
        with patch("cad_import.platform.system", return_value="Darwin"):
            with self.assertRaisesRegex(ValueError, "38 original"):
                ReferenceCadTool(runtime, "reference", wine=self.tool)
            expected = json.loads(REFERENCE_RECEIPT.read_text())["bundledNetgen"]["releaseFileHashes"]
            for name in expected:
                (runtime / name).write_bytes(b"incorrect")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                ReferenceCadTool(runtime, "reference", wine=self.tool)


if __name__ == "__main__":
    unittest.main()

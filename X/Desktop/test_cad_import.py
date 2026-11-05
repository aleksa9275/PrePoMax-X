"""Exercise the CAD process boundary without requiring the Windows runtime."""
import json
import os
from pathlib import Path
import sys
import subprocess
from threading import Event, Thread
import time
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from cad_import import CadImportCancelled, REFERENCE_RECEIPT, ReferenceCadTool, convert_cad, convert_cad_parts, run_process


TOOL = """
from pathlib import Path
import sys
mode, operation, source, target, *options = sys.argv[1:]
source, target = Path(source), Path(target)
if operation == "BREP_VISUALIZATION":
    if mode == "second vis failure" and target.name == "geometry-0002.vis":
        sys.exit(7)
    assert options == ["0.01", "1", "0.26"]
    assert source.read_text() in {"STEP", "BREP"}
    if mode != "no vis":
        target.write_text("visualization")
else:
    assert operation == ("STEP" if source.suffix == ".step" else "BREP") + "_ASSEMBLY_SPLIT_TO_COMPOUNDS"
    assert not options
    if mode != "no part":
        target.with_name("part_solid_0001.brep").write_text(source.read_text())
    if mode in {"two parts", "second vis failure"}:
        target.with_name("part_solid_0002.brep").write_text(source.read_text())
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

    def test_all_parts_finish_before_outputs_are_returned(self):
        source = self.root / "model.brep"
        source.write_text("BREP")
        outputs = convert_cad_parts(source, self.root / "two", self.command("two parts"))
        self.assertEqual([brep.name for brep, _ in outputs], ["part_solid_0001.brep", "part_solid_0002.brep"])
        self.assertEqual([vis.name for _, vis in outputs], ["geometry-0001.vis", "geometry-0002.vis"])
        for _, vis in outputs:
            self.assertEqual(vis.read_text(), "visualization")
        with self.assertRaisesRegex(ValueError, "status 7"):
            convert_cad_parts(source, self.root / "failed", self.command("second vis failure"))
        with patch("cad_import.MAX_TOTAL_VIS_BYTES", 1), self.assertRaisesRegex(ValueError, "Combined visualization"):
            convert_cad_parts(source, self.root / "too large", self.command("two parts"))

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

    @unittest.skipUnless(os.name == "posix", "Process group ownership uses POSIX sessions")
    def test_cancel_and_timeout_stop_owned_descendants(self):
        child = self.root / "child.py"
        heartbeat = self.root / "heartbeat"
        child.write_text("from pathlib import Path\nimport time\np=Path(" + repr(str(heartbeat)) + ")\n"
                         "while True:\n    p.write_text(str(time.monotonic_ns()))\n    time.sleep(0.01)\n")
        self.tool.write_text("import subprocess,sys,time\n"
                             "subprocess.Popen([sys.executable," + repr(str(child)) + "])\n"
                             "time.sleep(60)\n")
        cancel = Event()

        def cancel_after_child_starts():
            deadline = time.monotonic() + 5
            while not heartbeat.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            cancel.set()

        requester = Thread(target=cancel_after_child_starts)
        requester.start()
        try:
            with self.assertRaises(CadImportCancelled):
                run_process([sys.executable, str(self.tool)], cancel=cancel)
        finally:
            requester.join()
        self.assertTrue(heartbeat.exists())
        stopped = heartbeat.read_bytes()
        time.sleep(0.1)
        self.assertEqual(heartbeat.read_bytes(), stopped)

        with self.assertRaises(subprocess.TimeoutExpired):
            run_process([sys.executable, str(self.tool)], timeout=0.2)
        stopped = heartbeat.read_bytes()
        time.sleep(0.1)
        self.assertEqual(heartbeat.read_bytes(), stopped)

    def test_cancelled_process_never_starts(self):
        cancel = Event()
        cancel.set()
        with self.assertRaises(CadImportCancelled), patch("cad_import.subprocess.Popen") as launch:
            run_process(self.command(), cancel=cancel)
        launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()

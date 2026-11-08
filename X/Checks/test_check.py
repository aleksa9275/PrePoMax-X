"""Regressions for profile selection, retained failures and diagnostic boundaries."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import check


class CheckProfiles(unittest.TestCase):
    def test_fast_selects_current_requested_area(self):
        steps = check.plan("fast", ["results"], Path("out"), {"os": "Linux", "architecture": "Arm64"})
        self.assertEqual([(s["area"], s["revision"]) for s in steps], [("results", "current")])
        self.assertNotIn("--upstream-revision", steps[0]["arguments"])

    def test_zero_exit_without_successful_report_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            step = {"area": "results", "revision": "current", "arguments": ["fake"], "result": root / "missing.json"}
            def fake(*args, **kwargs):
                return subprocess.CompletedProcess(args[0], 0, "not a verifier result", "")
            row = check.run_step(step, root, fake)
            self.assertEqual(row["status"], "failed")
            self.assertTrue((root / row["log"]).exists())

    def test_report_failure_is_not_hidden_by_zero_exit(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            result = root / "result.json"
            result.write_text(json.dumps({"success": False}))
            step = {"area": "results", "revision": "current", "arguments": ["fake"], "result": result}
            row = check.run_step(step, root, lambda *a, **kw: subprocess.CompletedProcess(a[0], 0, "", ""))
            self.assertEqual(row["status"], "failed")

    def test_nonzero_preserves_stderr(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            step = {"area": "execution", "revision": "current", "arguments": ["fake"], "result": None}
            row = check.run_step(step, root, lambda *a, **kw: subprocess.CompletedProcess(a[0], 3, "", "reproducer"))
            self.assertEqual(row["exitCode"], 3)
            self.assertEqual(row["status"], "failed")
            self.assertIn("reproducer", (root / row["log"]).read_text())

    def test_malformed_report_is_a_retained_failure(self):
        for content in ["not JSON", "[]"]:
            with self.subTest(content=content), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                result = root / "result.json"
                result.write_text(content)
                step = {"area": "results", "revision": "current", "arguments": ["fake"], "result": result}
                row = check.run_step(step, root, lambda *a, **kw: subprocess.CompletedProcess(a[0], 0, "", ""))
                self.assertEqual(row["status"], "failed")
                self.assertIn("error", row)

    def test_snapshot_excludes_user_data_and_generated_outputs(self):
        for name in [".project/private/model.pmx", "X/Checks/artifacts/model.json", "X/Checks/new-data.json", "../outside.cs", "/tmp/outside.cs"]:
            self.assertFalse(check.safe_code_path(name, False), name)
        self.assertTrue(check.safe_code_path("X/Checks/check.py", False))
        self.assertTrue(check.safe_code_path("X/Analysis/dependency-artifacts.json", True))


if __name__ == "__main__":
    unittest.main()

"""Regression gates against independently recorded platform observations."""
from copy import deepcopy
import json
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from probe_evidence import compare

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / ".project/reports/core-feasibility"
SPEC = importlib.util.spec_from_file_location("ci_runner", Path(__file__).with_name("run-ci.py"))
CI_RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CI_RUNNER)


class EvidenceTests(unittest.TestCase):
    def test_recorded_linux_results_match_both_mac_references(self):
        for label in ("baseline", "v2.6.0"):
            with self.subTest(label=label):
                reference = EVIDENCE / f"macos-arm64-{label}.json"
                report = json.loads((EVIDENCE / "podman" / f"linux-arm64-{label}.json").read_text())
                self.assertTrue(compare(report, json.loads(reference.read_text()), reference, ROOT))

    def test_runtime_and_build_details_do_not_change_behavior_comparison(self):
        reference = EVIDENCE / "macos-arm64-baseline.json"
        recorded = json.loads(reference.read_text())
        report = deepcopy(recorded)
        report["tests"]["runtime"] = {"os": "Linux", "architecture": "X64"}
        report["sdk"] = "another patch version"
        report["buildLog"] = "another machine path"
        self.assertTrue(compare(report, recorded, reference, ROOT))

    def test_changes_to_each_measured_contract_fail_the_gate(self):
        reference = EVIDENCE / "macos-arm64-baseline.json"
        recorded = json.loads(reference.read_text())
        for field in ("sourceFiles", "fixture", "checks", "observations", "cliContracts", "geometry"):
            with self.subTest(field=field):
                report = deepcopy(recorded)
                if field in ("checks", "observations"):
                    report["tests"][field] = {"changed": True}
                elif field == "geometry":
                    report["inspection"][field] = {"changed": True}
                else:
                    report[field] = {"changed": True}
                self.assertFalse(compare(report, recorded, reference, ROOT))
                self.assertFalse(report["success"])

    def test_missing_contract_cannot_pass(self):
        reference = EVIDENCE / "macos-arm64-baseline.json"
        recorded = json.loads(reference.read_text())
        report = deepcopy(recorded)
        del report["cliContracts"]
        with self.assertRaises(KeyError):
            compare(report, recorded, reference, ROOT)

    def test_probe_failure_replaces_stale_replay_and_retains_diagnostic(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            (output / "v2.6.0.json").write_text('{"success": true}')
            failed = subprocess.CompletedProcess([], 1, "", "probe build failed")
            with patch("sys.argv", ["run-ci.py", "--output-dir", folder]), \
                    patch.object(CI_RUNNER.platform, "system", return_value="Linux"), \
                    patch.object(CI_RUNNER.platform, "machine", return_value="x86_64"), \
                    patch.object(CI_RUNNER.subprocess, "run", return_value=failed) as child, \
                    patch.dict(CI_RUNNER.os.environ, {"CI_JOB_TOKEN": "secret-sentinel"}):
                with self.assertRaises(RuntimeError):
                    CI_RUNNER.main()
            baseline = json.loads((output / "baseline.json").read_text())
            replay = json.loads((output / "v2.6.0.json").read_text())
            self.assertFalse(baseline["success"])
            self.assertIn("probe build failed", baseline["error"])
            self.assertFalse(replay["success"])
            self.assertEqual(replay["status"], "not run")
            self.assertEqual(child.call_count, 1)
            self.assertNotIn("secret-sentinel", (output / "baseline.json").read_text())

    def test_comparison_failure_retains_measured_report_and_stops_replay(self):
        recorded = json.loads((EVIDENCE / "macos-arm64-baseline.json").read_text())
        recorded["inspection"]["geometry"]["triangleCount"] = 999
        changed = subprocess.CompletedProcess([], 0, json.dumps(recorded), "")
        with tempfile.TemporaryDirectory() as folder:
            with patch("sys.argv", ["run-ci.py", "--output-dir", folder]), \
                    patch.object(CI_RUNNER.platform, "system", return_value="Linux"), \
                    patch.object(CI_RUNNER.platform, "machine", return_value="x86_64"), \
                    patch.object(CI_RUNNER.subprocess, "run", return_value=changed) as child:
                with self.assertRaises(RuntimeError):
                    CI_RUNNER.main()
            report = json.loads((Path(folder) / "baseline.json").read_text())
            self.assertFalse(report["success"])
            self.assertFalse(report["comparison"]["matches"])
            self.assertEqual(report["inspection"]["geometry"]["triangleCount"], 999)
            self.assertEqual(child.call_count, 1)


if __name__ == "__main__":
    unittest.main()

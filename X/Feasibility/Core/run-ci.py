#!/usr/bin/env python3
"""Run both pinned probes and compare evidence; no fetch, commit or push.

Defaults enforce Linux/X64. Explicit overrides allow a local host rehearsal,
which is recorded as such and cannot satisfy the native Linux x64 gate.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

from probe_evidence import compare

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
# Only selected non-secret CI identifiers are retained; never dump the environment.
CI_FIELDS = ("CI_COMMIT_SHA", "CI_JOB_ID", "CI_JOB_URL", "CI_PIPELINE_ID",
             "CI_PIPELINE_URL", "CI_PROJECT_PATH", "CI_RUNNER_ID",
             "CI_RUNNER_DESCRIPTION", "CI_RUNNER_TAGS", "CI_RUNNER_VERSION",
             "CI_RUNNER_EXECUTABLE_ARCH", "CI_JOB_IMAGE")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=HERE / "artifacts" / "ci")
    parser.add_argument("--expect-os", choices=["macOS", "Linux", "Windows"], default="Linux")
    parser.add_argument("--expect-architecture", choices=["Arm64", "X64", "X86"], default="X64")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((HERE / "source-manifest.json").read_text())
    hosted = os.environ.get("GITLAB_CI") == "true"
    metadata = {"environment": "GitLab CI" if hosted else "local rehearsal",
                "hostOS": platform.system(), "hostArchitecture": platform.machine(),
                "expectedOS": args.expect_os, "expectedArchitecture": args.expect_architecture,
                "recordedAtUtc": datetime.now(timezone.utc).isoformat(),
                "identifiers": {key: os.environ[key] for key in CI_FIELDS if key in os.environ},
                "toolHashes": {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                               for name in ("run-ci.py", "run-probe.py", "probe_evidence.py", "gitlab-ci.yml")}}
    revisions = [("baseline", None), ("v2.6.0", manifest["replayCommit"])]
    # Replace previous results with explicit pending records before any execution.
    # A baseline failure must never leave a stale successful replay artifact.
    for label, revision in revisions:
        (args.output_dir / f"{label}.json").write_text(json.dumps({
            "schemaVersion": 1, "success": False, "status": "not run",
            "sourceCommit": revision or manifest["baselineCommit"],
            "verificationEnvironment": metadata}, indent=2) + "\n")
    for label, revision in revisions:
        destination = args.output_dir / f"{label}.json"
        # Stdout holds the complete report, so a stale output cannot mask failure.
        command = [sys.executable, str(HERE / "run-probe.py"),
                   "--expect-os", args.expect_os, "--expect-architecture", args.expect_architecture]
        if revision:
            command.extend(["--revision", revision])
        report = {"schemaVersion": 1, "sourceCommit": revision or manifest["baselineCommit"]}
        matches = False
        try:
            result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=240)
            if result.returncode:
                raise RuntimeError(f"Probe failed ({result.returncode}):\n{result.stderr}\n{result.stdout}")
            report = json.loads(result.stdout)
            reference = ROOT / ".project/reports/core-feasibility" / f"macos-arm64-{label}.json"
            matches = compare(report, json.loads(reference.read_text()), reference, ROOT)
            if not matches:
                raise ValueError("Observations differ from the recorded macOS reference.")
        except (ValueError, KeyError, OSError, RuntimeError, subprocess.SubprocessError) as error:
            report["success"] = False
            report["error"] = str(error).replace(str(ROOT), "<repository>")
        report["verificationEnvironment"] = metadata
        destination.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"report": str(destination), "success": report["success"],
                          "runtime": report.get("tests", {}).get("runtime"),
                          "matchesMacReference": matches}), flush=True)
        if not report["success"]:
            raise RuntimeError("CI probe failed; diagnostic report: " + str(destination))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, RuntimeError, subprocess.SubprocessError) as error:
        print("CI PROBE FAILED: " + str(error), file=sys.stderr)
        sys.exit(1)

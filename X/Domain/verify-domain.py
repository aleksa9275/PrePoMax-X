#!/usr/bin/env python3
"""Verify the whole original domain assemblies (D062): source lists match the
original projects, the portable .NET 10 build succeeds, and the original
Windows net48 sources still compile with the PrePoMax-X edits."""
import argparse
import collections
import json
import platform
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expect-os", choices=["Darwin", "Linux", "Windows"])
    parser.add_argument("--expect-architecture", choices=["Arm64", "X64"])
    args = parser.parse_args()
    arch = {"arm64": "Arm64", "aarch64": "Arm64", "amd64": "X64", "x86_64": "X64"}.get(platform.machine().lower())
    report = {"success": False, "recordedAtUtc": datetime.now(timezone.utc).isoformat(),
              "host": {"os": platform.system(), "architecture": arch}, "commands": []}
    try:
        if (args.expect_os and args.expect_os != platform.system()) or (args.expect_architecture and args.expect_architecture != arch):
            raise ValueError("Unexpected native verification host")

        def run(command):
            done = subprocess.run([str(c) for c in command], cwd=ROOT, capture_output=True, text=True, timeout=900)
            report["commands"].append({"arguments": [str(c).replace(str(ROOT), "<repository>") for c in command],
                                       "exitCode": done.returncode, "stdout": done.stdout[-20000:], "stderr": done.stderr[-5000:]})
            if done.returncode:
                raise ValueError("Command failed: " + " ".join(map(str, command[:3])))
            return done

        run([sys.executable, HERE / "domain_sources.py", "--check"])
        with tempfile.TemporaryDirectory(prefix="prepomaxx-domain-") as temp:
            build = run(["dotnet", "build", HERE / "PrePoMaxX.Domain.slnx", "-c", "Release", "--disable-build-servers",
                         "-m:1", "-p:UseSharedCompilation=false",
                         "--artifacts-path", Path(temp) / "build", "-v:minimal", "-clp:Summary"])
            warnings = sorted({re.sub(r"\s*\[[^\]]*\]\s*$", "", line).replace(str(ROOT) + "/", "").strip()
                               for line in build.stdout.splitlines() if ": warning " in line})
            codes = collections.Counter(m for w in warnings for m in re.findall(r": warning (\w+)", w))
            report["build"] = {"warnings": len(warnings), "warningCodes": dict(sorted(codes.items()))}
        net48 = run([sys.executable, HERE / "net48_check.py"])
        report["net48"] = net48.stdout.strip().splitlines()
        report["assemblies"] = json.loads((HERE / "domain-sources.json").read_text())["assemblies"]
        report["success"] = True
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        report["error"] = str(error)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"success": report["success"], "warnings": report.get("build", {}).get("warnings"),
                      "net48": report.get("net48"), "error": report.get("error")}))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

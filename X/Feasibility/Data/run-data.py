#!/usr/bin/env python3
"""Verify unchanged upstream data contracts. No fetch, source patch or Git mutation."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def capture(command, timeout=180):
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {command}\n{result.stdout}\n{result.stderr}")
    return result.stdout


def portable(report):
    return {"sources": report["sourceFiles"], "checks": report["tests"]["checks"],
            "observations": report["tests"]["observations"], "cliContracts": report["cliContracts"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "artifacts" / "data.json")
    parser.add_argument("--expect-os", choices=["macOS", "Linux", "Windows"])
    parser.add_argument("--expect-architecture", choices=["Arm64", "X64"])
    parser.add_argument("--reference", type=Path, help="Compare portable observations with this recorded result")
    args = parser.parse_args()
    report = {"schemaVersion": 1, "success": False}
    temporary_path = None
    try:
        manifest = json.loads((HERE / "source-manifest.json").read_text())
        report["sourceCommit"] = manifest["baselineCommit"]
        includes = [e.attrib["Include"].removeprefix("$(UpstreamSourceRoot)/")
                    for e in ET.parse(HERE / "DataProbe.csproj").findall(".//Compile")]
        if sorted(includes) != sorted(s["path"] for s in manifest["sourceFiles"]):
            raise ValueError("Source links and manifest disagree")
        tree = ET.parse(HERE / "DataProbe.csproj")
        if tree.findall(".//PackageReference") or tree.findall(".//ProjectReference"):
            raise ValueError("Zero-package/project closure changed")
        report["sourceFiles"] = []
        for source in manifest["sourceFiles"]:
            original = subprocess.check_output(["git", "show", manifest["baselineCommit"] + ":" + source["path"]], cwd=ROOT)
            if digest(original) != source["sha256"] or (ROOT / source["path"]).read_bytes() != original:
                raise ValueError("Source differs from pinned upstream: " + source["path"])
            report["sourceFiles"].append(source)
        report["sdk"] = capture(["dotnet", "--version"]).strip()
        report["environment"] = {"kind": "GitLab CI" if os.environ.get("GITLAB_CI") == "true" else "native host",
                                 "hostOS": platform.system(), "hostArchitecture": platform.machine(),
                                 "recordedAtUtc": datetime.now(timezone.utc).isoformat(),
                                 "ci": {key: os.environ[key] for key in (
                                     "CI_COMMIT_SHA", "CI_JOB_ID", "CI_JOB_URL", "CI_PIPELINE_ID", "CI_PIPELINE_URL",
                                     "CI_RUNNER_ID", "CI_RUNNER_DESCRIPTION", "CI_RUNNER_EXECUTABLE_ARCH", "CI_JOB_IMAGE") if key in os.environ}}
        report["toolHashes"] = {name: digest((HERE / name).read_bytes()) for name in (
            "Program.cs", "DataProbe.csproj", "run-data.py", "source-manifest.json", "NuGet.Config", "gitlab-ci.yml")}
        environment = dict(os.environ)
        environment.update(DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_SKIP_FIRST_TIME_EXPERIENCE="1",
                           DOTNET_CLI_WORKLOAD_UPDATE_NOTIFY_DISABLE="1")
        with tempfile.TemporaryDirectory(prefix="prepomax-x-data-") as folder:
            temporary_path = folder
            result = subprocess.run(["dotnet", "build", str(HERE / "DataProbe.csproj"), "-c", "Release",
                                     "--disable-build-servers", "--no-incremental", "--artifacts-path", folder,
                                     "-v:minimal"], cwd=ROOT, env=environment, text=True, capture_output=True, timeout=180)
            report["buildLog"] = (result.stdout + result.stderr).replace(folder, "<temporary>").replace(str(ROOT), "<repository>")
            if result.returncode:
                raise RuntimeError("Source-linked build failed")
            assemblies = list((Path(folder) / "bin").rglob("PrePoMaxX.DataProbe.dll"))
            if len(assemblies) != 1:
                raise ValueError("Expected exactly one probe executable")
            assembly = assemblies[0]
            measured = subprocess.run(["dotnet", str(assembly), "--self-test"], cwd=ROOT,
                                      env=environment, text=True, capture_output=True, timeout=60)
            report["tests"] = json.loads(measured.stdout)
            if measured.returncode:
                raise ValueError("Data contract assertions failed")
            contracts = []
            for name, arguments in (("missing_arguments", []), ("unknown_command", ["unknown"])):
                usage = subprocess.run(["dotnet", str(assembly), *arguments], cwd=ROOT, text=True, capture_output=True, timeout=30)
                if usage.returncode != 2 or json.loads(usage.stdout).get("success") is not False:
                    raise ValueError("CLI usage contract failed: " + name)
                contracts.append({"name": name, "status": "passed", "exitCode": 2})
            report["cliContracts"] = contracts
        runtime = report["tests"]["runtime"]
        if args.expect_os and runtime["os"] != args.expect_os:
            raise ValueError("Unexpected OS: " + runtime["os"])
        if args.expect_architecture and (runtime["architecture"] != args.expect_architecture or runtime["osArchitecture"] != args.expect_architecture):
            raise ValueError("Unexpected architecture: " + str(runtime))
        if not report["tests"]["success"] or report["tests"]["failed"]:
            raise ValueError("Data contract assertions failed")
        if args.reference:
            reference = json.loads(args.reference.read_text())
            matches = portable(report) == portable(reference)
            report["comparison"] = {"reference": args.reference.as_posix(), "referenceSha256": digest(args.reference.read_bytes()), "matches": matches}
            if not matches:
                raise ValueError("Portable observations differ from reference")
        report["success"] = True
    except (ValueError, KeyError, RuntimeError, OSError, subprocess.SubprocessError) as error:
        message = str(error).replace(str(ROOT), "<repository>")
        report["error"] = message.replace(temporary_path, "<temporary>") if temporary_path else message
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"report": str(args.output), "success": report["success"],
                      "passed": report.get("tests", {}).get("passed"), "failed": report.get("tests", {}).get("failed"),
                      "runtime": report.get("tests", {}).get("runtime"), "matchesReference": report.get("comparison", {}).get("matches")}))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    sys.exit(main())

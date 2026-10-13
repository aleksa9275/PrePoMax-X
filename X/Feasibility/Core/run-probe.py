#!/usr/bin/env python3
"""Verify source identity, build and execute the bounded upstream-source probe.

No fetch, checkout, source patch, external package installation or Git mutation.
Replay builds link a temporary snapshot of seven files from an upstream revision.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROJECT = HERE / "CoreProbe.csproj"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(command, environment, timeout=120):
    result = subprocess.run(command, cwd=ROOT, env=environment, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {command}\n{result.stdout}")
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", help="Replay the pinned release commit or a baseline ancestor; defaults to verified current files")
    parser.add_argument("--output", type=Path, help="Write the evidence report to this path")
    parser.add_argument("--expect-os", choices=["macOS", "Linux", "Windows"])
    parser.add_argument("--expect-architecture", choices=["Arm64", "X64", "X86"])
    args = parser.parse_args()
    manifest = json.loads((HERE / "source-manifest.json").read_text())
    baseline = manifest["baselineCommit"]
    revision = git("rev-parse", "--verify", (args.revision or baseline) + "^{commit}").decode().strip()
    # Release branches can diverge from master. The explicitly verified release
    # pin is allowed as well as master ancestors; arbitrary fork commits are not.
    if revision != manifest["replayCommit"] and subprocess.run(
            ["git", "merge-base", "--is-ancestor", revision, baseline], cwd=ROOT).returncode:
        raise ValueError("Replay must be the pinned upstream release or an ancestor of the recorded baseline.")
    tree = ET.parse(PROJECT)
    includes = [item.attrib["Include"].removeprefix("$(UpstreamSourceRoot)/")
                for item in tree.findall(".//Compile")]
    if sorted(includes) != sorted(item["path"] for item in manifest["sourceFiles"]):
        raise ValueError("Project source links and source manifest disagree.")
    if tree.findall(".//PackageReference") or tree.findall(".//ProjectReference"):
        raise ValueError("This probe's zero-package/zero-project-reference closure has changed.")
    fixture = ROOT / manifest["fixture"]["path"]
    if digest(fixture.read_bytes()) != manifest["fixture"]["sha256"]:
        raise ValueError("Shared fixture changed; review/update the baseline manifest first.")

    environment = dict(os.environ)
    environment.update(DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_SKIP_FIRST_TIME_EXPERIENCE="1",
                       DOTNET_CLI_WORKLOAD_UPDATE_NOTIFY_DISABLE="1")
    sources = []
    with tempfile.TemporaryDirectory(prefix="prepomax-x-core-") as folder:
        temporary = Path(folder)
        source_root = temporary / "upstream" if args.revision else ROOT
        for item in manifest["sourceFiles"]:
            path = item["path"]
            original = git("show", f"{baseline}:{path}")
            if digest(original) != item["sha256"]:
                raise ValueError("Recorded source hash disagrees with baseline Git object: " + path)
            selected = git("show", f"{revision}:{path}")
            if args.revision:
                destination = source_root / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(selected)
            elif (ROOT / path).read_bytes() != selected:
                raise ValueError("Working source differs from pinned upstream: " + path)
            sources.append({"path": path, "sha256": digest(selected), "changedFromBaseline": selected != original})

        artifacts = temporary / "artifacts"
        command = ["dotnet", "build", str(PROJECT), "-c", "Release", "--disable-build-servers",
                   "--no-incremental", "--artifacts-path", str(artifacts),
                   "-p:UpstreamSourceRoot=" + str(source_root), "-v:minimal"]
        build_log = run(command, environment)
        assemblies = list((artifacts / "bin").rglob("PrePoMaxX.CoreProbe.dll"))
        if len(assemblies) != 1:
            raise ValueError("Expected one built probe executable, found " + str(len(assemblies)))
        assembly = assemblies[0]
        tests = json.loads(run(["dotnet", str(assembly), "--self-test"], environment, timeout=30))
        inspection = json.loads(run(["dotnet", str(assembly), "inspect", str(fixture)], environment, timeout=30))
        malformed = temporary / "truncated.stl"
        malformed.write_bytes(b"Binary truncated STL")
        cli_contracts = []
        for name, arguments, expected_exit in [
                ("malformed_input_is_json_failure", ["inspect", str(malformed)], 1),
                ("missing_arguments_are_json_usage_error", [], 2)]:
            result = subprocess.run(["dotnet", str(assembly), *arguments], cwd=ROOT, env=environment,
                                    text=True, capture_output=True, timeout=30)
            answer = json.loads(result.stdout)
            if result.returncode != expected_exit or answer.get("success") is not False:
                raise ValueError("CLI error contract failed: " + name)
            cli_contracts.append({"name": name, "status": "passed", "exitCode": result.returncode})
        runtime = tests["runtime"]
        if args.expect_os and runtime["os"] != args.expect_os:
            raise ValueError("Expected OS " + args.expect_os + ", got " + runtime["os"])
        if args.expect_architecture and runtime["architecture"] != args.expect_architecture:
            raise ValueError("Expected architecture " + args.expect_architecture + ", got " + runtime["architecture"])
        if tests["failed"] != 0 or not inspection["success"]:
            raise ValueError("Probe did not meet its test/inspection contract.")
        report = {"schemaVersion": 1, "sourceCommit": revision, "baselineCommit": baseline,
                  "sourceMode": "temporary Git snapshot" if args.revision else "unchanged working-tree links",
                  "targetFramework": manifest["targetFramework"], "sdk": run(["dotnet", "--version"], environment).strip(),
                  "sourceFiles": sources, "fixture": manifest["fixture"],
                  "tests": tests, "cliContracts": cli_contracts, "inspection": inspection,
                  "buildLog": build_log.replace(str(temporary), "<temporary>").replace(str(ROOT), "<repository>"),
                  "limitations": "Bounded source slice; no Windows-reference, PMX, whole-core, controller, VTK, mesher or solver equivalence claim."}
    serialized = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized)
        print(json.dumps({"report": str(args.output), "sourceCommit": revision, "runtime": runtime,
                          "passed": tests["passed"], "failed": tests["failed"]}))
    else:
        print(serialized, end="")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as error:
        print("PROBE FAILED: " + str(error), file=sys.stderr)
        sys.exit(1)

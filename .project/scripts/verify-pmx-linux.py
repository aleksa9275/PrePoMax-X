#!/usr/bin/env python3
"""Offline PMX research checks in an already-running cached ARM64 Podman VM."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
PMX = ROOT / "X/Feasibility/Pmx"
MAC = ROOT / ".project/reports/pmx-record-inspection"

TEST_CODE = '''import importlib.util,io,json,platform,subprocess,unittest
from pathlib import Path
p=Path("X/Feasibility/Pmx/test-inspection.py")
s=importlib.util.spec_from_file_location("inspection_tests",p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
log=io.StringIO()
r=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(m))
print(json.dumps({"success":r.wasSuccessful(),"tests":r.testsRun,"failures":len(r.failures),"errors":len(r.errors),"log":log.getvalue(),"privateInputUsed":False,"os":platform.system(),"architecture":platform.machine(),"python":platform.python_version(),"dotnetInfo":subprocess.check_output(["dotnet","--info"],text=True)}))
raise SystemExit(0 if r.wasSuccessful() else 1)
'''
INSPECT_CODE = '''import json,subprocess
r=subprocess.run(["python3","X/Feasibility/Pmx/inspect-pmx.py","/inputs/reference.pmx","--output","/tmp/inspection.json"],capture_output=True,text=True,timeout=240)
with open("/tmp/inspection.json") as f: report=json.load(f)
print(json.dumps(report))
raise SystemExit(r.returncode)
'''


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def projection(report):
    graph = report["graphInventory"]
    return {key: report[key] for key in ("schemaVersion", "success", "sourceBaseline", "framing", "sourceContext", "toolHashes")} | {
        "graphInventory": {key: value for key, value in graph.items() if key not in ("runtime", "decoder", "loadedAssemblyNames")}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, help="Cached image ID; never pulled/built")
    parser.add_argument("--legacy-input", required=True, type=Path)
    parser.add_argument("--saved-input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    # Fail before any output write if the caller accidentally selects an input directory.
    output = args.output_dir.resolve()
    inputs = [args.legacy_input.resolve(), args.saved_input.resolve()]
    if any(path.is_relative_to(output) for path in inputs):
        parser.error("Output directory must not contain private input files")
    report = {"success": False, "recordedAtUtc": datetime.now(timezone.utc).isoformat(),
              "evidenceKind": "Linux ARM64 PMX record inspection, not application/semantic parity",
              "network": "none", "checkoutMount": "read-only", "inputMount": "read-only",
              "commands": [], "comparisons": [], "toolSha256": sha(Path(__file__))}
    output.mkdir(parents=True, exist_ok=True)
    try:
        image = json.loads(subprocess.check_output(["podman", "image", "inspect", args.image], text=True, timeout=30))[0]
        recipe = sha(ROOT / "X/Feasibility/Core/Containerfile")
        if image["Os"] != "linux" or image["Architecture"] != "arm64":
            raise ValueError("Expected cached Linux ARM64 image; no translated execution accepted")
        if image.get("Labels", {}).get("org.prepomaxx.core-probe.recipe-sha256") != recipe:
            raise ValueError("Cached image recipe label differs from current recipe")
        report["image"] = {key: image.get(key) for key in ("Id", "Digest", "Os", "Architecture", "Labels")}
        report["podmanVersion"] = subprocess.check_output(["podman", "version", "--format", "json"], text=True, timeout=30)
        report["recipeSha256"] = recipe

        def run(code, source=None):
            command = ["podman", "run", "--rm", "--pull=never", "--network=none", "--read-only",
                       "--tmpfs", "/tmp:rw,size=1g", "--env", "PYTHONDONTWRITEBYTECODE=1",
                       "--volume", str(ROOT) + ":/workspace:ro"]
            if source:
                command += ["--volume", str(source) + ":/inputs/reference.pmx:ro"]
            command += ["--entrypoint", "python3", image["Id"], "-c", code]
            completed = subprocess.run(command, capture_output=True, text=True, timeout=300)
            diagnostic = completed.stderr.replace(str(ROOT), "<repository>")
            for private_input in inputs:
                diagnostic = diagnostic.replace(str(private_input), "<private-input>")
            report["commands"].append({"kind": "private reference inventory" if source else "synthetic tests",
                                       "exitCode": completed.returncode, "stderr": diagnostic})
            result = json.loads(completed.stdout)
            if completed.returncode or not result.get("success"):
                raise ValueError("Container check failed: " + json.dumps(result))
            return result

        tests = run(TEST_CODE)
        tests["testToolSha256"] = sha(PMX / "test-inspection.py")
        (output / "synthetic-tests.json").write_text(json.dumps(tests, indent=2) + "\n")
        if tests["tests"] != 24 or tests["os"] != "Linux" or tests["architecture"] != "aarch64":
            raise ValueError("Unexpected test count or actual process platform")
        for source, name in zip(inputs, ("legacy-2.5.1", "crossover-saved-2.6.0")):
            expected = json.loads((MAC / (name + "-macos-arm64.json")).read_text())
            before = sha(source)
            if before != expected["framing"]["inputSha256"]:
                raise ValueError("Private reference differs from recorded Mac input")
            actual = run(INSPECT_CODE, source)
            (output / (name + "-linux-arm64.json")).write_text(json.dumps(actual, indent=2) + "\n")
            matches = projection(actual) == projection(expected)
            loaded = set(actual["graphInventory"]["loadedAssemblyNames"])
            mac_loaded = set(expected["graphInventory"]["loadedAssemblyNames"])
            added, removed = sorted(loaded - mac_loaded), sorted(mac_loaded - loaded)
            # Observed SDK/runtime support delta, retained separately. All unknown
            # additions/removals (including payload assemblies) fail the check.
            assembly_guard = set(added) <= {"System.Collections.Concurrent"} and not removed
            no_payload = not any(name.startswith("Cae") or (name.startswith("PrePoMax") and name != "PrePoMaxX.NrbfInventory") for name in loaded)
            unchanged = before == sha(source) == actual["framing"]["inputSha256"]
            runtime = actual["graphInventory"]["runtime"]
            native = runtime["os"] == "Linux" and runtime["architecture"] == runtime["osArchitecture"] == "Arm64"
            report["comparisons"].append({"reference": name, "exactPortableInventoryMatch": matches,
                                           "inputUnchanged": unchanged, "nativeLinuxArm64": native,
                                           "runtimeAssembliesAdded": added, "runtimeAssembliesRemoved": removed,
                                           "runtimeAssemblyGuardPassed": assembly_guard,
                                           "noPayloadAssembliesLoaded": no_payload,
                                           "records": actual["graphInventory"]["recordCount"],
                                           "types": len(actual["graphInventory"]["types"])})
            if not (matches and unchanged and native and assembly_guard and no_payload):
                raise ValueError("Linux/Mac comparison or input/platform guard failed")
        report["success"] = True
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        message = str(error)
        for source in inputs:
            message = message.replace(str(source), "<private-input>")
        report["error"] = message
    (output / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report.get(key) for key in ("success", "comparisons", "error")}))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

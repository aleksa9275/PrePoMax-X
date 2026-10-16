#!/usr/bin/env python3
"""Build the shared libraries and verify mapping, source and host contracts."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASELINE = "de8f73032a72746e3d6d9afd53d9fbd289eb310a"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def sources():
    paths = set()
    for project in (HERE / "CaeGlobals/CaeGlobals.csproj", HERE / "CaeMesh/CaeMesh.csproj"):
        tree = ET.parse(project)
        if tree.findall(".//PackageReference"):
            raise ValueError("The first shared slice has no package dependencies")
        paths.update(item.attrib["Include"].replace("$(RepositoryRoot)", "") for item in tree.findall(".//Compile"))
    expected = {"CaeGlobals/CaeException.cs", "CaeGlobals/CommonClasses/Matrix.cs", "CaeGlobals/CommonClasses/Vec3D.cs",
                "CaeMesh/Nodes/FeNode.cs", "CaeMesh/Meshing/Transfinite/TransfiniteSideTriple.cs",
                "CaeMesh/Meshing/Transfinite/ThreeBlockGrid.cs", "CaeMesh/Meshing/Transfinite/ThreeBlockMapping.cs"}
    if paths != expected:
        raise ValueError("Shared library source closure changed")
    rows = []
    for name in sorted(paths - {"CaeGlobals/CaeException.cs"}):
        original = subprocess.check_output(["git", "show", BASELINE + ":" + name], cwd=ROOT)
        if original != (ROOT / name).read_bytes():
            raise ValueError("Engineering source changed: " + name)
        rows.append({"path": name, "sha256": sha(original), "unchangedFromBaseline": True})
    original = subprocess.check_output(["git", "show", BASELINE + ":CaeGlobals/ExceptionTools.cs"], cwd=ROOT).decode()
    start = original.index("    public class CaeException : Exception\n")
    end = original.index("    //\n    public static class ExceptionTools", start)
    body = original[start:end]
    moved = (ROOT / "CaeGlobals/CaeException.cs").read_text(encoding="utf-8")
    if body not in moved or (ROOT / "CaeGlobals/ExceptionTools.cs").read_text(encoding="utf-8") != original[:start] + original[end + 7:]:
        raise ValueError("Exception extraction changed existing class behavior or Windows presentation")
    ns = {"m": "http://schemas.microsoft.com/developer/msbuild/2003"}
    items = ET.parse(ROOT / "CaeGlobals/CaeGlobals.csproj").findall(".//m:Compile", ns)
    if sum(item.attrib.get("Include") == "CaeException.cs" for item in items) != 1:
        raise ValueError("Legacy Windows project must include the separated class exactly once")
    rows.append({"path": "CaeGlobals/CaeException.cs", "sha256": sha(moved.encode()), "originalClassBodyUnchanged": True})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expect-os", choices=["Windows", "Linux", "Darwin"])
    parser.add_argument("--expect-architecture", choices=["X64", "Arm64"])
    args = parser.parse_args()
    report = {"success": False, "recordedAtUtc": datetime.now(timezone.utc).isoformat(),
              "host": {"os": platform.system(), "architecture": platform.machine()},
              "baseline": BASELINE, "commands": []}
    folder = None
    try:
        if args.expect_os and platform.system() != args.expect_os:
            raise ValueError("Unexpected native operating system")
        native_arch = {"amd64": "X64", "x86_64": "X64", "arm64": "Arm64", "aarch64": "Arm64"}.get(platform.machine().lower())
        if args.expect_architecture and native_arch != args.expect_architecture:
            raise ValueError("Unexpected native architecture")
        report["sources"] = sources()
        report["toolHashes"] = {str(p.relative_to(HERE)).replace("\\", "/"): sha(p.read_bytes())
                                for p in HERE.rglob("*") if p.is_file() and not {"bin", "obj", "artifacts", "__pycache__"}.intersection(p.parts)
                                and p.suffix in {".py", ".cs", ".csproj", ".props", ".slnx", ".json", ".Config"}}
        with tempfile.TemporaryDirectory(prefix="prepomaxx-core-") as folder:
            work = Path(folder)
            def run(command, code=0):
                done = subprocess.run(list(map(str, command)), cwd=ROOT, text=True, capture_output=True, timeout=180)
                def clean(value):
                    for path, label in [(str(ROOT), "<repository>"), (folder, "<temporary>")]:
                        value = value.replace(path.replace("\\", "\\\\"), label).replace(path, label)
                    return value
                report["commands"].append({"arguments": [clean(str(v)) for v in command], "exitCode": done.returncode,
                                           "stdout": clean(done.stdout), "stderr": clean(done.stderr)})
                if done.returncode != code:
                    raise RuntimeError("Unexpected exit code; see retained command output")
                return done
            report["sdk"] = run(["dotnet", "--version"]).stdout.strip()
            run(["dotnet", "build", HERE / "PrePoMaxX.Core.slnx", "-c", "Release", "--disable-build-servers",
                 "-m:1", "--artifacts-path", work / "build", "-p:RestoreConfigFile=" + str(HERE / "NuGet.Config"), "-v:minimal"])
            test = work / "build/bin/CoreTests/release/PrePoMaxX.CoreTests.dll"
            result = json.loads(run(["dotnet", test]).stdout)
            report["mappingTests"] = result
            if not result["success"] or result["passed"] != 25:
                raise ValueError("Shared mapping checks failed or were not all executed")
            if result["runtime"]["architecture"] != native_arch:
                raise ValueError("Managed process differs from native host architecture")
            cli = work / "build/bin/MapFace/release/PrePoMaxX.MapFace.dll"
            sample = HERE / "MapFace/equilateral.json"
            sample_hash = sha(sample.read_bytes())
            output = json.loads(run(["dotnet", cli, sample]).stdout)
            if not output["success"] or output["NumberOfBoundaryNodes"] != 6 or len(output["Quads"]) != 3:
                raise ValueError("CLI sample contract failed")
            if abs(output["InnerUv"][0][0] - 1) > 1e-10 or abs(output["InnerUv"][0][1] - 3**0.5 / 3) > 1e-10:
                raise ValueError("CLI sample centroid failed")
            controls = []
            for arguments, code, name in [([], 2, "usage"), ([work / "missing.json"], 1, "missing input")]:
                run(["dotnet", cli, *arguments], code); controls.append(name)
            bad_cases = {"malformed": "{", "null root": "null", "missing sides": "{}",
                         "null side": json.dumps({"sideUv": [None, [], []], "sideXyz": [[], [], []]}),
                         "size limit": " " * (1024 * 1024 + 1)}
            face = json.loads(sample.read_text())
            face["sideUv"][0][-1][0] += 0.1
            bad_cases["open boundary"] = json.dumps(face)
            face = json.loads(sample.read_text())
            for key in ["sideUv", "sideXyz"]:
                face[key] = [[side[0], side[-1]] for side in face[key]]
            bad_cases["invalid block counts"] = json.dumps(face)
            for name, content in bad_cases.items():
                path = work / "invalid.json"; path.write_text(content)
                rejected = run(["dotnet", cli, path], 1)
                if rejected.stdout or json.loads(rejected.stderr)["success"]:
                    raise ValueError("CLI rejection contract failed")
                controls.append(name)
            report["cli"] = {"sample": output, "negativeControls": controls, "inputUnchanged": sha(sample.read_bytes()) == sample_hash}
            if not report["cli"]["inputUnchanged"]:
                raise ValueError("CLI modified input")
            report["success"] = True
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        report["error"] = str(error).replace(str(ROOT), "<repository>").replace(folder or "<unused>", "<temporary>")
    report["limits"] = ["First source-linked library slice, not the full application or PMX reader",
                        "Required Mac/Linux platform runs and CAD/VTK integration remain separate"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"success": report["success"], "mappingChecks": report.get("mappingTests", {}).get("passed"),
                      "cliControls": len(report.get("cli", {}).get("negativeControls", [])), "error": report.get("error")}))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

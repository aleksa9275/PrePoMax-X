#!/usr/bin/env python3
"""Build partial shared libraries and verify mapping, data, source and host contracts."""
import argparse
import copy
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
import mesh_workflow_checks

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def sources():
    """Whole original assemblies (D062): the source lists must match the original projects."""
    check = subprocess.run([sys.executable, str(ROOT / "X/Domain/domain_sources.py"), "--check"], cwd=ROOT,
                           capture_output=True, text=True)
    if check.returncode != 0:
        raise ValueError("Whole-library source lists are stale: " + check.stdout.strip())
    manifest = ROOT / "X/Domain/domain-sources.json"
    return {"mode": "whole original assemblies (X/Domain)", "manifest": "X/Domain/domain-sources.json",
            "manifestSha256": sha(manifest.read_bytes()), "generatedListsCurrent": True}


def validate_data(result, reference):
    if not result["success"] or result["passed"] != 30 or result["failed"]:
        raise ValueError("Shared data checks failed or were not all executed")
    if result["checks"] != reference["tests"]["checks"] or result["observations"] != reference["tests"]["observations"]:
        raise ValueError("Shared data contracts differ from retained native Windows observations")
    contracts = result["sharedTypeContracts"]
    owners = {"CaeGlobals.Matrix": ("CaeGlobals", True, False),
              "CaeMesh.GeometryMetadata": ("CaeMesh", True, True),
              "CaeMesh.GeometryMetadataEntity": ("CaeMesh", True, True),
              "CaeMesh.GeometryMetadataProperty": ("CaeMesh", True, True),
              "CaeMesh.IntegrationScale": ("CaeMesh", True, True),
              "CaeMesh.IntegrationScaleType": ("CaeMesh", True, True),
              "CaeResults.FrdStreamReader": ("CaeResults", False, False)}
    if len(contracts["types"]) != len(owners) or {row["name"] for row in contracts["types"]} != set(owners):
        raise ValueError("Shared data type closure changed")
    for row in contracts["types"]:
        # 3.0.2 (upstream storage): the stored types carry [PmxType] where 3.0.1 had [Serializable]; none keeps
        # [Serializable]. The Windows reference was observed on 3.0.1 (re-observe on Windows for 3.0.2, M3/M4).
        owner, public, stored = owners[row["name"]]
        identity = row["name"] + ", " + owner + ", Version=1.0.0.0, Culture=neutral, PublicKeyToken=null"
        if row["identity"] != identity or row["isPublic"] != public or row["stored"] != stored or row["serializable"]:
            raise ValueError("Shared type identity/visibility/serialization marker changed: " + row["name"])
    if not contracts["metadataImplementsOriginalInterfaces"]:
        raise ValueError("Metadata serialization interfaces changed")
    if {row["name"] for row in contracts["assemblies"]} != {"CaeGlobals", "CaeMesh", "CaeResults"}:
        raise ValueError("Shared data assembly closure changed")
    # Whole original assemblies (D062) reference their original packages and the portable
    # GmshCommon/vtkControl/WinForms-compat assemblies; real desktop frameworks stay excluded.
    # Microsoft.Win32.Registry: original Tools.cs reads the Windows registry (runtime portability item).
    # PrePoMaxX.FormsCompat (M2): the original CaeMesh project references System.Windows.Forms for
    # Application.DoEvents (GmshAPI); the portable headless control model provides it.
    allowed = {"CaeGlobals", "CaeMesh", "CaeResults", "GmshCommon", "vtkControl", "PrePoMaxX.WinFormsCompat", "PrePoMaxX.FormsCompat",
               "NCalc", "UnitsNet", "ExtendedNumerics.BigDecimal", "Parlot", "PriorityQueue", "Microsoft.CSharp",
               "Microsoft.Win32.Registry", "netstandard", "mscorlib",
               # 3.0.2: upstream's storage serializer (CaeGlobals/Serialization) on MessagePack with Zstandard
               "MessagePack", "ZstdSharp"}
    for assembly in contracts["assemblies"]:
        if any(not (name in allowed or name == "System" or name.startswith("System.")) or
               any(token in name for token in ("System.Windows.Forms", "Presentation", "Kitware"))
               for name in assembly["references"]):
            raise ValueError("Unexpected platform/package reference: " + assembly["name"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expect-os", choices=["Windows", "Linux", "Darwin"])
    parser.add_argument("--expect-architecture", choices=["X64", "Arm64"])
    parser.add_argument("--upstream-revision", help="Retired with the whole-library build (D062)")
    args = parser.parse_args()
    report = {"success": False, "recordedAtUtc": datetime.now(timezone.utc).isoformat(),
              "host": {"os": platform.system(), "architecture": platform.machine()},
              "commands": []}
    folder = None
    try:
        if args.expect_os and platform.system() != args.expect_os:
            raise ValueError("Unexpected native operating system")
        native_arch = {"amd64": "X64", "x86_64": "X64", "arm64": "Arm64", "aarch64": "Arm64"}.get(platform.machine().lower())
        if args.expect_architecture and native_arch != args.expect_architecture:
            raise ValueError("Unexpected native architecture")
        report["sources"] = sources()
        report["repository"] = {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                                "dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT))}
        report["toolHashes"] = {str(p.relative_to(HERE)).replace("\\", "/"): sha(p.read_bytes())
                                for p in HERE.rglob("*") if p.is_file() and not {"bin", "obj", "artifacts", "__pycache__"}.intersection(p.parts)
                                and p.suffix in {".py", ".cs", ".csproj", ".props", ".slnx", ".json", ".Config", ".yml", ".inp"}}
        report["toolHashes"]["../Feasibility/Data/Program.cs"] = sha((HERE.parent / "Feasibility/Data/Program.cs").read_bytes())
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
            if args.upstream_revision:
                raise ValueError("Historical upstream slice replays were retired with the whole-library build (D062)")
            run(["dotnet", "build", HERE / "PrePoMaxX.Core.slnx", "-c", "Release", "--disable-build-servers",
                 "-m:1", "--artifacts-path", work / "build", "-v:minimal"])
            test = work / "build/bin/CoreTests/release/PrePoMaxX.CoreTests.dll"
            result = json.loads(run(["dotnet", test]).stdout)
            report["mappingTests"] = result
            if not result["success"] or result["passed"] != 25:
                raise ValueError("Shared mapping checks failed or were not all executed")
            if result["runtime"]["architecture"] != native_arch:
                raise ValueError("Managed process differs from native host architecture")
            data = work / "build/bin/CoreDataTests/release/PrePoMaxX.CoreDataTests.dll"
            report["dataTests"] = json.loads(run(["dotnet", data, "--self-test"]).stdout)
            reference_path = ROOT / ".project/reports/windows-reference/data-windows-x64.json"
            reference = json.loads(reference_path.read_text())
            validate_data(report["dataTests"], reference)
            runtime = report["dataTests"]["runtime"]
            expected_os = {"Darwin": "macOS", "Linux": "Linux", "Windows": "Windows"}[platform.system()]
            if runtime["architecture"] != native_arch or runtime["osArchitecture"] != native_arch or runtime["os"] != expected_os:
                raise ValueError("Shared data process differs from native host")
            report["dataComparison"] = {"reference": str(reference_path.relative_to(ROOT)),
                                        "sha256": sha(reference_path.read_bytes()), "matches": True}
            report["dataRejectionControls"] = []
            for name in ("moved serialized type", "changed metadata wire bytes", "missing data check", "desktop dependency"):
                altered = copy.deepcopy(report["dataTests"])
                if name == "moved serialized type":
                    altered["sharedTypeContracts"]["types"][1]["identity"] = "CaeMesh.GeometryMetadata, PrePoMaxX.CoreDataTests"
                elif name == "changed metadata wire bytes":
                    altered["observations"]["singleFaceBlockHex"] = "00"
                elif name == "missing data check":
                    altered["checks"].pop()
                else:
                    altered["sharedTypeContracts"]["assemblies"][0]["references"].append("System.Windows.Forms")
                try:
                    validate_data(altered, reference)
                except ValueError:
                    report["dataRejectionControls"].append(name)
                else:
                    raise ValueError("Data verifier accepted control: " + name)
            report["dataCliControls"] = []
            for name, arguments in (("missing_arguments", []), ("unknown_command", ["unknown"])):
                usage = json.loads(run(["dotnet", data, *arguments], 2).stdout)
                if usage.get("success") is not False:
                    raise ValueError("Shared data CLI usage contract failed")
                report["dataCliControls"].append({"name": name, "status": "passed", "exitCode": 2})
            if report["dataCliControls"] != reference["cliContracts"]:
                raise ValueError("Shared data CLI controls differ from Windows reference")
            element_tests = work / "build/bin/ElementTests/release/PrePoMaxX.ElementTests.dll"
            report["elementTests"] = json.loads(run(["dotnet", element_tests]).stdout)
            elements = report["elementTests"]
            if not elements["success"] or elements["passed"] != 95 or elements["failed"] or elements["runtime"]["architecture"] != native_arch:
                raise ValueError("Accepted element-kernel checks failed or did not all execute")
            # 3.0.2 fixed the quadratic pyramid classification (D029); the quadratic tetrahedron integral stays open
            if len(elements["openCorrectnessChecks"]) != 1 or elements["fullyAccepted"] or any(c["passed"] for c in elements["openCorrectnessChecks"]):
                raise ValueError("Unresolved original-source correctness checks must remain explicit")
            measure_cli = work / "build/bin/MeasureMesh/release/PrePoMaxX.MeasureMesh.dll"
            measure_sample = HERE / "MeasureMesh/unit-tetra.json"
            measured = json.loads(run(["dotnet", measure_cli, measure_sample]).stdout)
            cell = measured["elements"][0]
            if not measured["success"] or len(measured["elements"]) != 1 or cell["Id"] != 101 or cell["PartId"] != 8:
                raise ValueError("Measurement CLI identity contract failed")
            if abs(cell["Measure"] - 1 / 6) > 1e-12 or abs(cell["Integral"] - 1 / 3) > 1e-12 or cell["Centroid"] != [0.25] * 3:
                raise ValueError("Measurement CLI independent tetrahedron contract failed")
            report["measurementCli"] = {"sample": measured, "controls": []}
            for arguments, code, name in [([], 2, "usage"), ([work / "missing-mesh.json"], 1, "missing input")]:
                run(["dotnet", measure_cli, *arguments], code)
                report["measurementCli"]["controls"].append(name)
            sample_mesh = json.loads(measure_sample.read_text())
            invalid_meshes = {"malformed": "{", "null root": "null", "missing arrays": "{}", "size limit": " " * (4*1024*1024+1)}
            for name in ("unknown property", "duplicate node", "duplicate element", "wrong node count", "missing node", "duplicate connectivity", "unsupported type", "quadratic tetrahedron gate", "invalid scale", "nonfinite value", "degenerate geometry"):
                altered = copy.deepcopy(sample_mesh)
                if name == "unknown property": altered["unexpected"] = 1
                elif name == "duplicate node": altered["nodes"][1]["id"] = 11
                elif name == "duplicate element": altered["elements"].append(copy.deepcopy(altered["elements"][0]))
                elif name == "wrong node count": altered["elements"][0]["nodeIds"].pop()
                elif name == "missing node": altered["elements"][0]["nodeIds"][0] = 999
                elif name == "duplicate connectivity": altered["elements"][0]["nodeIds"][0] = 29
                elif name == "unsupported type": altered["elements"][0]["type"] = "UnknownElement"
                elif name == "quadratic tetrahedron gate": altered["elements"][0]["type"] = "ParabolicTetraElement"
                elif name == "invalid scale": altered["scale"] = "unknown"
                elif name == "nonfinite value": altered["nodes"][0]["value"] = "NaN"
                else:
                    for node in altered["nodes"]: node.update(x=0,y=0,z=0)
                invalid_meshes[name] = json.dumps(altered)
            for name, content in invalid_meshes.items():
                path = work / "invalid-mesh.json"; path.write_text(content)
                rejected = run(["dotnet", measure_cli, path], 1)
                if rejected.stdout or json.loads(rejected.stderr)["success"]:
                    raise ValueError("Measurement CLI rejection contract failed: " + name)
                report["measurementCli"]["controls"].append(name)
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
            report["meshWorkflow"] = mesh_workflow_checks.verify(run, work, native_arch)
            report["success"] = True
    except (OSError, KeyError, TypeError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        report["error"] = str(error).replace(str(ROOT), "<repository>").replace(folder or "<unused>", "<temporary>")
    report["limits"] = ["Whole original domain assemblies (X/Domain); not the full application or PMX reader",
                        "Full persistence/history/clone, CAD/interactive VTK and native-source release gates remain open",
                        "Element slice still needs native Windows and exact-commit Linux x64 execution",
                        "Two original-source analytical/classifier checks remain unresolved; quadratic tetrahedra are gated in the host"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"success": report["success"], "mappingChecks": report.get("mappingTests", {}).get("passed"),
                      "dataChecks": report.get("dataTests", {}).get("passed"),
                      "elementChecks": report.get("elementTests", {}).get("passed"),
                      "meshWorkflowChecks": report.get("meshWorkflow", {}).get("tests", {}).get("passed"),
                      "openCorrectnessChecks": len(report.get("elementTests", {}).get("openCorrectnessChecks", [])),
                      "cliControls": len(report.get("cli", {}).get("negativeControls", [])), "error": report.get("error")}))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

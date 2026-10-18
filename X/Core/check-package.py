#!/usr/bin/env python3
"""Verify the development archive, rebuild its source and execute its published CLIs."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import platform
import subprocess
import tempfile
import zipfile


def inspect(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if len(names) > 512 or len(set(names)) != len(names) or sum(e.file_size for e in entries) > 64 * 1024 * 1024:
            raise ValueError("Unexpected archive size or duplicate entries")
        if any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts or
               "\\" in name or ":" in name or entry.is_dir()
               for name, entry in zip(names, entries)):
            raise ValueError("Unsafe or unexpected archive path")
        manifest = json.loads(archive.read("manifest.json"))
        if manifest["kind"] != "framework-dependent-development-build" or set(names) != set(manifest["files"]) | {"manifest.json"}:
            raise ValueError("Manifest does not cover the complete archive")
        required = {"LICENSE", "source/LICENSE", "README.md", "MapFace/PrePoMaxX.MapFace.dll",
                    "MeasureMesh/PrePoMaxX.MeasureMesh.dll", "examples/equilateral.json", "examples/unit-tetra.json",
                    "source/X/Core/PrePoMaxX.Core.slnx", "source/X/Core/NuGet.Config"}
        required.update({"MeshDeck/PrePoMaxX.MeshDeck.dll", "examples/unit-cube.inp"})
        if not required.issubset(names):
            raise ValueError("Missing development binaries, examples, source or license")
        for name, expected in manifest["files"].items():
            if hashlib.sha256(archive.read(name)).hexdigest() != expected:
                raise ValueError("Checksum mismatch: " + name)
        return manifest


def controls(data):
    passed = []
    for name in ("changed binary", "unmanifested file", "parent traversal"):
        changed = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(data)) as source, zipfile.ZipFile(changed, "w") as target:
            for entry in source.infolist():
                value = source.read(entry.filename)
                if name == "changed binary" and entry.filename == "MeasureMesh/PrePoMaxX.MeasureMesh.dll": value += b"changed"
                target.writestr(entry.filename, value)
            if name == "unmanifested file": target.writestr("extra.txt", "unexpected")
            if name == "parent traversal": target.writestr("../outside.txt", "unexpected")
        try:
            inspect(changed.getvalue())
        except ValueError:
            passed.append(name)
        else:
            raise ValueError("Archive verifier accepted control: " + name)
    return passed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--expect-os", choices=["Darwin", "Linux", "Windows"])
    parser.add_argument("--expect-architecture", choices=["Arm64", "X64"])
    args = parser.parse_args()
    report = {"success": False, "host": {"os": platform.system(), "architecture": platform.machine()}, "commands": []}
    folder = None
    try:
        arch = {"arm64": "Arm64", "aarch64": "Arm64", "amd64": "X64", "x86_64": "X64"}.get(platform.machine().lower())
        if (args.expect_os and args.expect_os != platform.system()) or (args.expect_architecture and args.expect_architecture != arch):
            raise ValueError("Unexpected native package-verification host")
        data = args.archive.read_bytes()
        manifest = inspect(data)
        report.update(archiveSha256=hashlib.sha256(data).hexdigest(), sourceCommit=manifest["head"],
                      workingTreeChangesIncluded=manifest["workingTreeChangesIncluded"], manifestEntriesVerified=len(manifest["files"]))
        report["rejectionControls"] = controls(data)
        with tempfile.TemporaryDirectory(prefix="prepomaxx-package-check-") as folder:
            work = Path(folder)
            with zipfile.ZipFile(io.BytesIO(data)) as archive: archive.extractall(work)
            def run(command, code=0):
                done = subprocess.run(list(map(str, command)), cwd=work, text=True, capture_output=True, timeout=180)
                clean = lambda value: value.replace(folder, "<extracted>")
                report["commands"].append({"arguments": [clean(str(v)) for v in command], "exitCode": done.returncode,
                                           "stdout": clean(done.stdout), "stderr": clean(done.stderr)})
                if done.returncode != code: raise RuntimeError("Extracted source/CLI check failed; see retained command output")
                return done
            source = work / "source/X/Core"
            run(["dotnet", "build", source / "PrePoMaxX.Core.slnx", "-c", "Release", "--disable-build-servers", "-m:1",
                 "--artifacts-path", work / "build", "-p:RestoreConfigFile=" + str(source / "NuGet.Config"), "-v:minimal"])
            report["sourceRebuild"] = True
            report["publishedSmoke"] = {}
            for host, sample in (("MapFace", "equilateral"), ("MeasureMesh", "unit-tetra")):
                result = json.loads(run(["dotnet", work / host / ("PrePoMaxX." + host + ".dll"), work / "examples" / (sample + ".json")]).stdout)
                if not result["success"]: raise ValueError("Published sample failed")
                report["publishedSmoke"][host] = result
            mapped = report["publishedSmoke"]["MapFace"]
            cell = report["publishedSmoke"]["MeasureMesh"]["elements"][0]
            if mapped["NumberOfBoundaryNodes"] != 6 or len(mapped["Quads"]) != 3 or abs(cell["Measure"] - 1/6) > 1e-12 or abs(cell["Integral"] - 1/3) > 1e-12:
                raise ValueError("Published examples differ from independent geometry expectations")
            gated = json.loads((work / "examples/unit-tetra.json").read_text())
            gated["elements"][0]["type"] = "ParabolicTetraElement"
            path = work / "gated.json"; path.write_text(json.dumps(gated))
            rejected = run(["dotnet", work / "MeasureMesh/PrePoMaxX.MeasureMesh.dll", path], 1)
            if rejected.stdout or json.loads(rejected.stderr)["success"]: raise ValueError("Published tetrahedron gate failed")
            report["quadraticTetrahedronGate"] = True
            mesh_cli = work / "MeshDeck/PrePoMaxX.MeshDeck.dll"
            sample = work / "examples/unit-cube.inp"
            mesh = json.loads(run(["dotnet", mesh_cli, "measure", sample]).stdout)
            export = work / "mesh-export.inp"
            run(["dotnet", mesh_cli, "export-mesh", sample, export])
            reopened = json.loads(run(["dotnet", mesh_cli, "inspect", export]).stdout)
            if abs(mesh["measurements"][0]["Measure"] - 1) > 1e-12 or reopened["mesh"] != mesh["mesh"]:
                raise ValueError("Published mesh workflow geometry/ID/set roundtrip failed")
            run(["dotnet", mesh_cli, "export-mesh", sample, export], 1)
            report["meshWorkflow"] = {"unitCubeMeasured": True, "exportReopened": True, "overwriteRejected": True}
        report["success"] = True
    except (OSError, KeyError, TypeError, ValueError, RuntimeError, zipfile.BadZipFile, subprocess.SubprocessError) as error:
        report["error"] = str(error).replace(folder or "<unused>", "<extracted>")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"success": report["success"], "manifestEntriesVerified": report.get("manifestEntriesVerified"), "error": report.get("error")}))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Publish and smoke-test a framework-dependent development CLI bundle with source."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=HERE / "artifacts/development-build")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {"success": False, "host": {"os": platform.system(), "architecture": platform.machine()}, "commands": []}
    try:
        with tempfile.TemporaryDirectory(prefix="prepomaxx-package-") as folder:
            work = Path(folder)
            bundle = work / "bundle"; bundle.mkdir()
            def run(command):
                done = subprocess.run(list(map(str, command)), cwd=ROOT, text=True, capture_output=True, timeout=180)
                def clean(text): return text.replace(str(ROOT), "<repository>").replace(folder, "<temporary>")
                report["commands"].append({"arguments": [clean(str(v)) for v in command], "exitCode": done.returncode,
                                           "stdout": clean(done.stdout), "stderr": clean(done.stderr)})
                if done.returncode: raise RuntimeError("Development publish/smoke failed; see command evidence")
                return done.stdout
            report["sdk"] = run(["dotnet", "--version"]).strip()
            for host in ("MapFace", "MeasureMesh", "MeshDeck"):
                run(["dotnet", "publish", HERE / host / (host + ".csproj"), "-c", "Release", "--self-contained", "false",
                     "--disable-build-servers", "-m:1", "-p:UseAppHost=false", "--artifacts-path", work / "build",
                     "-p:RestoreConfigFile=" + str(HERE / "NuGet.Config"), "-o", bundle / host, "-v:minimal"])
            examples = bundle / "examples"; examples.mkdir()
            shutil.copyfile(HERE / "MapFace/equilateral.json", examples / "equilateral.json")
            shutil.copyfile(HERE / "MeasureMesh/unit-tetra.json", examples / "unit-tetra.json")
            shutil.copyfile(HERE / "MeshDeck/unit-cube.inp", examples / "unit-cube.inp")
            map_result = json.loads(run(["dotnet", bundle / "MapFace/PrePoMaxX.MapFace.dll", examples / "equilateral.json"]))
            measure_result = json.loads(run(["dotnet", bundle / "MeasureMesh/PrePoMaxX.MeasureMesh.dll", examples / "unit-tetra.json"]))
            mesh_result = json.loads(run(["dotnet", bundle / "MeshDeck/PrePoMaxX.MeshDeck.dll", "measure", examples / "unit-cube.inp"]))
            cell = measure_result["elements"][0]
            if not map_result["success"] or map_result["NumberOfBoundaryNodes"] != 6 or len(map_result["Quads"]) != 3:
                raise ValueError("Published MapFace sample failed")
            if not measure_result["success"] or abs(cell["Measure"] - 1/6) > 1e-12 or abs(cell["Integral"] - 1/3) > 1e-12:
                raise ValueError("Published MeasureMesh sample failed")
            report["publishedSmoke"] = {"mapFace": map_result, "measureMesh": measure_result}
            if not mesh_result["success"] or abs(mesh_result["measurements"][0]["Measure"] - 1) > 1e-12:
                raise ValueError("Published mesh workflow cube failed")
            report["publishedSmoke"]["meshDeck"] = mesh_result
            sources = {ROOT / "LICENSE", ROOT / "X/Feasibility/Data/Program.cs",
                       ROOT / "CaeMesh/Meshing/Transfinite/Cpp/three_block_vectors.txt",
                       ROOT / ".project/reports/windows-reference/data-windows-x64.json"}
            for project in HERE.glob("Cae*/*.csproj"):
                for item in ET.parse(project).findall(".//Compile"):
                    sources.add(ROOT / item.attrib["Include"].replace("$(RepositoryRoot)", ""))
            sources.update(p for p in HERE.rglob("*") if p.is_file() and
                           not {"artifacts", "bin", "obj", "__pycache__"}.intersection(p.relative_to(HERE).parts))
            for path in sorted(sources):
                target = bundle / "source" / path.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(path, target)
            shutil.copyfile(ROOT / "LICENSE", bundle / "LICENSE")
            (bundle / "README.md").write_text("""# PrePoMax-X core development build

Requires the native .NET 10 runtime on Windows x64, Linux x64/ARM64 or macOS ARM64.
This framework-dependent bundle contains no runtime, solver, CAD mesher or GUI.

From the extracted directory:

    dotnet MapFace/PrePoMaxX.MapFace.dll examples/equilateral.json
    dotnet MeasureMesh/PrePoMaxX.MeasureMesh.dll examples/unit-tetra.json
    dotnet MeshDeck/PrePoMaxX.MeshDeck.dll inspect examples/unit-cube.inp
    dotnet MeshDeck/PrePoMaxX.MeshDeck.dll measure examples/unit-cube.inp
    dotnet MeshDeck/PrePoMaxX.MeshDeck.dll export-mesh examples/unit-cube.inp new-mesh.inp

MeshDeck reads standalone INP mesh data with the original node/connectivity/set
parser. Mesh-only export preserves IDs and formulations through the original
element writer and lists omitted model keywords. It is not a full model/deck
or solver/results workflow. Includes, coordinate transforms and scoped assemblies
are rejected. Formulation fallbacks are reported and refused for export; pyramid
export requires --pyramids wedges or --pyramids hexahedrons. Existing output files
are never overwritten. Measurement retains the quadratic-tetrahedron gate.

MapFace calls the original structured mapping. MeasureMesh reports original
element measures/centroids, field integrals and VTK/Gmsh connectivity for 13
linear/parabolic beam/surface/solid classes. Quadratic tetrahedra are rejected
because an analytical integration check fails in the unchanged upstream code.
The original quadratic-pyramid IsParabolic helper also returns false; this host
uses explicit types. Both correctness issues remain open. A complete mesh-quality,
curved-element, persistence/history, CAD/VTK and native Windows differential pass
is not claimed. JSON is tool input, not a production document/serializer choice.

GPLv3 and original Matej Borovinšek attribution are retained; see LICENSE and
source headers. Corresponding source for this partial build is included.
Rebuild with an installed .NET 10 SDK:

    dotnet build source/X/Core/PrePoMaxX.Core.slnx -c Release -m:1

Source/host verification with Git provenance uses X/Core/verify.py in the full
repository with its pinned baseline available. No application DLL should be
copied over an original Windows PrePoMax installation.
""")
            hashes = {p.relative_to(bundle).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in sorted(bundle.rglob("*")) if p.is_file()}
            (bundle / "manifest.json").write_text(json.dumps({"kind": "framework-dependent-development-build",
                "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "workingTreeChangesIncluded": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)),
                "files": hashes}, indent=2) + "\n")
            output = args.output_dir / "PrePoMaxX-Core-development.zip"
            with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
                for path in sorted(bundle.rglob("*")):
                    if path.is_file(): archive.write(path, path.relative_to(bundle).as_posix())
            report.update(success=True, archive=output.name, archiveSha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                          archiveBytes=output.stat().st_size, sourceFiles=sum(name.startswith("source/") for name in hashes))
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        report["error"] = str(error).replace(str(ROOT), "<repository>")
    (args.output_dir / "package-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report.get(key) for key in ("success", "archive", "archiveBytes", "error")}))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

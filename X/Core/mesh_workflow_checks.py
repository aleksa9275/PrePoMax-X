"""Executable mesh workflow acceptance through original reader/writer libraries."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def verify(run, work, architecture):
    tests = work / "build/bin/MeshDeckTests/release/PrePoMaxX.MeshDeckTests.dll"
    result = json.loads(run(["dotnet", tests]).stdout)
    if not result["success"] or result["passed"] != 68 or result["failed"] or result["runtime"]["architecture"] != architecture:
        raise ValueError("Mesh workflow checks failed, changed count or used a nonnative process")
    cli = work / "build/bin/MeshDeck/release/PrePoMaxX.MeshDeck.dll"
    sample = HERE / "MeshDeck/unit-cube.inp"
    original = sample.read_bytes()
    inspected = json.loads(run(["dotnet", cli, "inspect", sample]).stdout)
    measured = json.loads(run(["dotnet", cli, "measure", sample]).stdout)
    if (not inspected["success"] or inspected["mesh"]["nodes"] != 8 or inspected["mesh"]["elements"] != 1 or
            inspected["mesh"]["bounds"] != [[0, 0, 0], [1, 1, 1]] or
            abs(measured["measurements"][0]["Measure"] - 1) > 1e-12 or
            measured["runtime"]["architecture"] != architecture):
        raise ValueError("Mesh CLI sample geometry differs from independent cube expectations")
    output = work / "mesh-export.inp"
    exported = json.loads(run(["dotnet", cli, "export-mesh", sample, output]).stdout)
    reopened = json.loads(run(["dotnet", cli, "inspect", output]).stdout)
    if not exported["success"] or not exported["outputWritten"] or reopened["mesh"] != inspected["mesh"]:
        raise ValueError("Actual mesh CLI export/reopen differs in geometry, IDs, sets or formulation")
    controls = []
    for name, arguments, code in [
        ("usage", [], 2), ("unknown command", ["unknown", sample], 2),
        ("invalid conversion choice", ["export-mesh", sample, output, "--pyramids", "automatic"], 2),
        ("missing input", ["inspect", work / "missing.inp"], 1),
        ("existing output", ["export-mesh", sample, output], 1),
        ("input as output", ["export-mesh", sample, sample], 1)]:
        rejected = run(["dotnet", cli, *arguments], code)
        if rejected.stdout or (code == 1 and json.loads(rejected.stderr)["success"]):
            raise ValueError("Mesh CLI rejection contract failed: " + name)
        controls.append(name)
    invalid = {"missing connectivity": "*NODE\n1,0,0,0\n*ELEMENT,TYPE=C3D4\n1,1,2,3\n",
               "include boundary": original.decode() + "*INCLUDE,INPUT=missing.inp\n",
               "indented keyword": "  *NODE\n1,0,0,0\n",
               "invalid coordinates": original.decode().replace("11, 0, 0, 0", "11, NaN, 0, 0"),
               "input size limit": " " * (16 * 1024 * 1024 + 1)}
    for name, content in invalid.items():
        path = work / "invalid-mesh.inp"
        path.write_text(content)
        rejected = run(["dotnet", cli, "inspect", path], 1)
        if rejected.stdout or json.loads(rejected.stderr)["success"]:
            raise ValueError("Mesh CLI accepted invalid input: " + name)
        controls.append(name)
    if sample.read_bytes() != original:
        raise ValueError("Mesh workflow modified its input")
    return {"tests": result, "cli": {"inspect": inspected, "measure": measured,
            "exportReopened": reopened, "inputUnchanged": True, "rejectionControls": controls},
            "limits": ["Standalone mesh data, not full FeMesh/FeModel or a solve/results workflow",
                       "Include files, assemblies and coordinate transforms require the full model reader",
                       "Mesh-only export lists omitted model keywords; no material/load/step serialization claim",
                       "Quadratic tetrahedron measurement remains gated; pyramid conversion must be explicit"]}

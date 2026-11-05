#!/usr/bin/env python3
"""Check native CAD identity/coverage and original Netgen linear volume meshes.

This records a separate native experiment. It does not relax replay-import.py's
exact Windows-scene requirement or the existing tetrahedron engineering gate.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "X/Desktop"))
from cad_import import convert_cad_parts, file_sha256, run_process


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def dot(a, b):
    return math.fsum(x*y for x, y in zip(a, b))


def decode(inspector, vis):
    value = json.loads(subprocess.check_output(["dotnet", str(inspector), "scene", str(vis)], timeout=30))
    if value.get("success") is not True or value["SourceSha256"] != file_sha256(vis):
        raise ValueError("VIS decoder did not identify its input")
    return value


def face_coverage(scene, face_id):
    points = {n["id"]: (n["x"], n["y"], n["z"]) for n in scene["nodes"]}
    edges = Counter()
    areas, vectors, moments = [], [], []
    triangles = [e["nodeIds"] for e in scene["elements"] if e["sourceFaceId"] == face_id]
    for ids in triangles:
        a, b, c = [points[i] for i in ids]
        normal = cross(sub(b, a), sub(c, a))
        area = math.sqrt(dot(normal, normal)) / 2
        if area <= 0:
            raise ValueError("Degenerate visualization triangle")
        areas.append(area)
        vectors.append(tuple(x / 2 for x in normal))
        moments.append(tuple(area * (a[k] + b[k] + c[k]) / 3 for k in range(3)))
        for i, j in ((0, 1), (1, 2), (2, 0)):
            edges[tuple(sorted((ids[i], ids[j])))] += 1
    if not triangles or any(n > 2 for n in edges.values()):
        raise ValueError("Missing or nonmanifold face tessellation")
    return {"area": math.fsum(areas),
            "areaVector": [math.fsum(v[k] for v in vectors) for k in range(3)],
            "firstMoment": [math.fsum(v[k] for v in moments) for k in range(3)],
            "boundary": sorted(edge for edge, count in edges.items() if count == 1)}


def compare_scene(reference, actual):
    # Source nodes and CAD edges must retain their exact identity and coordinates.
    for key in ("nodes",):
        if reference[key] != actual[key]:
            raise ValueError("Native source nodes/coordinates changed")
    if reference["cad"]["edgeSegments"] != actual["cad"]["edgeSegments"]:
        raise ValueError("Native CAD edge identity changed")
    if reference["cad"]["lengthUnit"] != actual["cad"]["lengthUnit"]:
        raise ValueError("Native length unit changed")
    if ([e["id"] for e in reference["elements"]] != [e["id"] for e in actual["elements"]]
            or any(e["vtkCellType"] != 5 or len(e["nodeIds"]) != 3 for e in actual["elements"])):
        raise ValueError("Native triangle IDs, types or count changed")
    deltas = []

    def compare(a, b, path="", numeric_bound=1e-10):
        if isinstance(a, dict) and isinstance(b, dict) and a.keys() == b.keys():
            for key in a:
                # Inertia has length^5 units; near-zero entries suffer cancellation.
                bound = 1e-8 if key == "inertia_at_center_of_mass" else numeric_bound
                if key.endswith("_ids") or key == "id":
                    if a[key] != b[key]:
                        raise ValueError("Native entity IDs changed at " + path + "/" + key)
                else:
                    compare(a[key], b[key], path + "/" + key, bound)
        elif isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)) and len(a) == len(b):
            for i, (x, y) in enumerate(zip(a, b)):
                compare(x, y, path + "/" + str(i), numeric_bound)
        elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
            if not math.isfinite(a) or not math.isfinite(b) or not math.isclose(a, b, rel_tol=1e-12, abs_tol=numeric_bound):
                raise ValueError("Native measurement exceeds bound at " + path)
            if a != b:
                deltas.append({"path": path, "reference": a, "native": b, "absoluteDelta": abs(a-b)})
        elif a != b:
            raise ValueError("Native CAD metadata changed at " + path)

    compare(reference["cad"]["entities"], actual["cad"]["entities"], "metadata")
    changed = []
    for face in reference["cad"]["entities"]["face"]:
        face_id = face["id"]
        old = [e for e in reference["elements"] if e["sourceFaceId"] == face_id]
        new = [e for e in actual["elements"] if e["sourceFaceId"] == face_id]
        if old != new:
            if face["properties"]["type"] != ["Plane"] or len(old) != len(new):
                raise ValueError("A curved face tessellation or face triangle count changed")
            before, after = face_coverage(reference, face_id), face_coverage(actual, face_id)
            if before["boundary"] != after["boundary"]:
                raise ValueError("Planar face boundary changed")
            compare(before, after, "coverage/" + str(face_id))
            changed.append(face_id)
    return {"exactDecodedSceneMatch": {k:v for k,v in reference.items() if k != "SourceSha256"}
            == {k:v for k,v in actual.items() if k != "SourceSha256"},
            "sourceNodesAndEdgesExact": True, "metadataWithinBounds": True,
            "changedPlanarTriangulations": changed, "measurementDifferences": deltas}


def mesh_parameters(path, size, threads):
    # Same ordered text protocol as original MeshingParameters.WriteToFile.
    values = [1, size, 0, 0.5, 0.3, 2, 2, 0, 2, 0, 0.0001, 0, 0, "", 1, 1,
              3, 3, 0, 0, 1, 1, 0.01, threads, 0, 135, ""]
    path.write_text("".join(f"parameter {i}\n{value}\n" for i, value in enumerate(values)))


def inspect_mesh(path):
    """Independent first-order geometric oracle; not an application VOL reader."""
    lines = path.read_text().splitlines()
    def section(keyword):
        if lines.count(keyword) != 1:
            raise ValueError("Expected one VOL " + keyword + " section")
        i = lines.index(keyword)
        n = int(lines[i+1])
        if n <= 0 or n > 100000:
            raise ValueError("Invalid bounded mesh section count")
        return [row.split() for row in lines[i+2:i+2+n]]
    points = [tuple(map(float, row)) for row in section("points")]
    if any(len(p) != 3 or not all(map(math.isfinite, p)) for p in points):
        raise ValueError("Invalid mesh coordinates")
    faces, volumes, used, domains = Counter(), [], set(), set()
    for row in section("volumeelements"):
        values = list(map(int, row))
        if len(values) != 6 or values[1] != 4:
            raise ValueError("This measurement probe requires linear tetrahedra")
        ids = values[2:]
        if len(set(ids)) != 4 or min(ids) < 1 or max(ids) > len(points):
            raise ValueError("Invalid tetrahedron node reference")
        # Original GetLinearTetraElement swaps positions 2 and 3 on VOL import.
        a, c, b, d = [points[i-1] for i in ids]
        volume = dot(sub(b, a), cross(sub(c, a), sub(d, a))) / 6
        if volume <= 1e-12:
            raise ValueError("Nonpositive tetrahedron after original VOL permutation")
        volumes.append(volume)
        used.update(ids)
        domains.add(values[0])
        for indices in ((0,1,2), (0,1,3), (0,2,3), (1,2,3)):
            faces[tuple(sorted(ids[i] for i in indices))] += 1
    if any(n not in (1, 2) for n in faces.values()) or len(used) != len(points):
        raise ValueError("Nonmanifold volume mesh or unused volume nodes")
    surface = []
    source_faces = set()
    for row in section("surfaceelementsuv"):
        if int(row[4]) != 3:
            raise ValueError("Expected triangular mesh boundary")
        surface.append(tuple(sorted(map(int, row[5:8]))))
        source_faces.add(int(row[1]))
    if len(set(surface)) != len(surface) or set(surface) != {face for face,n in faces.items() if n == 1}:
        raise ValueError("Volume boundary differs from the emitted CAD surface mesh")
    return {"sha256": file_sha256(path), "nodes": len(points), "tetrahedra": len(volumes),
            "surfaceTriangles": len(surface), "sourceFaceIds": sorted(source_faces), "domains": sorted(domains),
            "volume": math.fsum(volumes), "minimumTetraVolume": min(volumes),
            "boundaryConforms": True, "allTetrahedraPositiveAfterOriginalPermutation": True}


def compare_original_mesh(actual):
    reference_dir = ROOT / ".project/reports/native-cad-meshing-reference"
    receipt = json.loads((reference_dir / "receipt.json").read_text())
    original = reference_dir / "l-bracket.vol"
    if file_sha256(original) != receipt["original"]["sha256"]:
        raise ValueError("Original Windows volume mesh fixture changed")
    def sections(path):
        lines = path.read_text().splitlines()
        def read(key):
            i = lines.index(key)
            return [row.split() for row in lines[i+2:i+2+int(lines[i+1])]]
        return (read("volumeelements"), [row[:8] for row in read("surfaceelementsuv")],
                [tuple(map(float, row)) for row in read("points")])
    before, after = sections(original), sections(actual)
    if before[:2] != after[:2] or len(before[2]) != len(after[2]):
        raise ValueError("Native L-bracket mesh connectivity differs from original Windows")
    delta = max(abs(x-y) for a,b in zip(before[2], after[2]) for x,y in zip(a,b))
    if delta > 1e-8:
        raise ValueError("Native L-bracket mesh coordinates exceed 1e-8 model-unit bound")
    return {"originalSha256": file_sha256(original), "volumeConnectivityExact": True,
            "surfaceConnectivityAndCadIdsExact": True, "maximumCoordinateAbsoluteDifference": delta,
            "coordinateAbsoluteBound": 1e-8}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mesher", type=Path, required=True)
    parser.add_argument("--inspector", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True)
    report = {"success": False, "host": platform.system(), "architecture": platform.machine(),
              "nativeExecutableSha256": file_sha256(args.mesher), "fixtures": [],
              "criteria": {"metadataRelativeBound": 1e-12, "metadataAbsoluteBound": 1e-10,
                           "inertiaAbsoluteBound": 1e-8, "nodesEdgesAndIds": "exact",
                           "changedTriangles": "planes only, same boundary, area, orientation and first moment"},
              "tetrahedronEngineeringGateClosed": False}
    try:
        fixtures = [(ROOT / "APIs/Python/Test_Scripts/Models/L_bracket_r.step", [HERE / "fixtures/l-bracket.vis"]),
                    (ROOT / "APIs/Python/Test_Scripts/Models/sweep_two_apart.brep",
                     [HERE / "fixtures/two-parts/part-1.vis", HERE / "fixtures/two-parts/part-2.vis"])]
        for source, originals in fixtures:
            fixture = {"source": source.name, "sourceSha256": file_sha256(source), "runs": []}
            report["fixtures"].append(fixture)
            for repeat in (1, 2):
                work = args.output / f"{source.stem}-{repeat}"
                parts = convert_cad_parts(source, work, [str(args.mesher.resolve())])
                if len(parts) != len(originals):
                    raise ValueError("Native CAD part count differs from original")
                run = []
                for index, ((brep, vis), original) in enumerate(zip(parts, originals), 1):
                    scene = decode(args.inspector.resolve(), vis)
                    item = {"part": index, "brepSha256": file_sha256(brep), "visSha256": file_sha256(vis),
                            "comparison": compare_scene(decode(args.inspector.resolve(), original), scene)}
                    parameters = work / f"mesh-{index}.parameters"
                    mesh = work / f"mesh-{index}.vol"
                    mesh_parameters(parameters, 10 if len(originals) == 1 else 3, 1)
                    with (work / f"mesh-{index}.log").open("xb") as log:
                        result = run_process([str(args.mesher.resolve()), "BREP_MESH", str(brep), str(mesh),
                                              str(parameters)], cwd=work, stdout=log, stderr=subprocess.STDOUT)
                    if result.returncode:
                        raise ValueError("Native volume meshing failed")
                    item["mesh"] = inspect_mesh(mesh)
                    if len(originals) == 1:
                        item["mesh"]["originalComparison"] = compare_original_mesh(mesh)
                    if item["mesh"]["sourceFaceIds"] != [f["id"] for f in scene["cad"]["entities"]["face"]]:
                        raise ValueError("Volume mesh lost CAD face identities")
                    if len(originals) == 2:
                        volume = scene["cad"]["entities"]["solid"][0]["properties"]["volume"][0]
                        if not math.isclose(item["mesh"]["volume"], volume, rel_tol=1e-12, abs_tol=1e-9):
                            raise ValueError("Native box volume does not match exact CAD volume")
                    run.append(item)
                fixture["runs"].append(run)
            if fixture["runs"][0] != fixture["runs"][1]:
                raise ValueError("Native CAD/meshing run was not repeatable")
        if file_sha256(args.mesher) != report["nativeExecutableSha256"]:
            raise ValueError("Mesher changed during verification")
        report["success"] = True
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        report["error"] = str(error)
    (args.output / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k:v for k,v in report.items() if k != "fixtures"}))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Verify original two-body VIS fixtures and their part-scoped rendering IDs."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import platform
from runpy import run_path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "X/Desktop"))
from cad_scene import compose_cad_parts


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspector", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checks = []

    def check(name, passed):
        checks.append({"name": name, "passed": bool(passed)})
        if not passed:
            raise ValueError(name)

    report = {"success": False, "os": platform.system(), "architecture": platform.machine(), "checks": checks}
    try:
        reference = json.loads((ROOT / ".project/reports/multipart-cad-reference.json").read_text())
        app_path = ROOT / ".project/reports/multipart-cad-reference/geometry.json"
        check("original Windows application capture", sha(app_path) == reference["originalAppGeometrySha256"])
        app_parts = sorted(json.loads(app_path.read_text())["parts"], key=lambda p: p["part"]["centerOfMass"][0])
        compare = run_path(str(HERE / "verify-vis.py"))["compare"]
        check("original BREP fixture", sha(ROOT / reference["sourcePath"]) == reference["sourceSha256"])
        parts = []
        for index, part in enumerate(reference["parts"], 1):
            vis = HERE / f"fixtures/two-parts/part-{index}.vis"
            check(f"part {index} original VIS bytes", sha(vis) == part["visSha256"])
            scene = json.loads(subprocess.check_output(["dotnet", str(args.inspector.resolve()), "scene", str(vis)], timeout=30))
            check(f"part {index} original nodes and triangles", len(scene["nodes"]) == part["nodeCount"]
                  and len(scene["elements"]) == part["triangleCount"] and scene["SourceSha256"] == part["visSha256"])
            check(f"part {index} canonical solid properties",
                  scene["cad"]["entities"]["solid"][0]["properties"] == part["solidProperties"])
            inspected = json.loads(subprocess.check_output(["dotnet", str(args.inspector.resolve()), str(vis)], timeout=30))
            app_part = copy.deepcopy(app_parts[index - 1])
            # Windows assigns global mesh node IDs after reading each VIS.
            # Relate its vertices to this part's source nodes by exact coordinates.
            node_ids = {tuple(node["coordinates"]): node["id"] for node in inspected["nodes"]}
            for vertex in app_part["vertices"]:
                vertex["nodeId"] = node_ids[tuple(vertex["coordinates"])]
            compare(inspected, app_part, lambda name, passed: check(f"part {index} app {name}", passed))
            parts.append((part["name"], scene))
        combined = compose_cad_parts(parts)
        check("parts retain their separate nodes", len(combined["nodes"]) == sum(len(p["nodes"]) for _, p in parts))
        for part_id, (_, source) in enumerate(parts, 1):
            actual_nodes = [node for node in combined["nodes"] if node["sourcePartId"] == part_id]
            source_ids = {node["id"]: node["sourceNodeId"] for node in actual_nodes}
            check(f"part {part_id} exact coordinates and source node IDs",
                  [{key: node["sourceNodeId"] if key == "id" else node[key] for key in ("id", "x", "y", "z")}
                   for node in actual_nodes] == source["nodes"])
            actual_elements = [element for element in combined["elements"] if element["sourcePartId"] == part_id]
            check(f"part {part_id} original triangles and faces",
                  [{"id": e["sourceElementId"], "vtkCellType": e["vtkCellType"],
                    "nodeIds": [source_ids[n] for n in e["nodeIds"]], "sourceFaceId": e["sourceFaceId"]}
                   for e in actual_elements] == source["elements"])
            actual_edges = [edge for edge in combined["cad"]["edgeSegments"] if edge["sourcePartId"] == part_id]
            check(f"part {part_id} original edge IDs and segments",
                  [{"nodeIds": [source_ids[n] for n in e["nodeIds"]], "sourceEdgeIds": e["sourceEdgeIds"]}
                   for e in actual_edges] == source["cad"]["edgeSegments"])
            check(f"part {part_id} all original metadata", combined["cad"]["parts"][part_id - 1]["entities"]
                  == source["cad"]["entities"])
        report.update(success=True, combinedSceneSha256=sha_json(combined))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        report["error"] = str(error)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({**{key: value for key, value in report.items() if key != "checks"}, "checkCount": len(checks)}))
    return 0 if report["success"] else 1


def sha_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

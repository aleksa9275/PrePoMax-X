#!/usr/bin/env python3
"""Compare the portable VIS slice with the retained original application capture."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve().parent
REFERENCE = HERE.parents[2] / ".project/reports/l-bracket-cad-reference"
FIXTURE = HERE / "fixtures/l-bracket.vis"


def add_first_face_edge(raw, polyline):
    first = b"Number of edge polylines: 4 (Edge Id, N1, N2, N3 ...)\r\nEdge polyline: 1 1 2"
    modified = first.replace(b"polylines: 4", b"polylines: 5") + b"\r\nEdge polyline: " + polyline
    return raw.replace(first, modified, 1)


def compare(observed, reference, check):
    nodes = {row["id"]: row["coordinates"] for row in observed["nodes"]}
    vertices = reference["vertices"]
    part = reference["part"]
    check("merged tessellation node and triangle counts", len(nodes) == part["nodeCount"] and
          len(observed["triangles"]) == part["elementCount"])
    check("original vertex IDs and coordinates", observed["vertexNodeIds"] == sorted(v["nodeId"] for v in vertices)
          and all(nodes[v["nodeId"]] == v["coordinates"] for v in vertices))
    metadata = observed["metadata"]
    expected_metadata = reference["metadata"]
    check("VIS metadata framing", all(metadata[k] == expected_metadata[k]
          for k in ("formatVersion", "coordinateSystem", "lengthUnit")))

    source = {kind: {row["id"]: row["properties"] for row in rows}
              for kind, rows in metadata["entities"].items()}
    maps = {kind: {int(row["properties"]["source_id"]): row["id"] for row in rows}
            for kind, rows in expected_metadata["entities"].items()}
    for kind, rows in expected_metadata["entities"].items():
        check(f"{kind} source IDs", set(source[kind]) == set(maps[kind]) and len(maps[kind]) == len(rows))
        for row in rows:
            source_id = int(row["properties"]["source_id"])
            for key, expected in row["properties"].items():
                if key == "source_id":
                    continue
                actual = source[kind][source_id]["vertex_ids" if key == "source_vertex_ids" else key]
                if key in ("face_ids", "edge_ids", "shell_ids"):
                    actual = [maps[key[:-4]][value] for value in actual]
                if not isinstance(expected, list) and len(actual) == 1:
                    actual = actual[0]
                check(f"{kind} {source_id} property {key}", actual == expected)

    for kind, group, measure in (("face", "faces", "area"), ("edge", "edges", "length")):
        topology = {row["id"]: row for row in reference[group]}
        check(f"{kind} tessellation source IDs", {row["id"] for row in observed[group]} == set(maps[kind]))
        for row in observed[group]:
            expected = topology[maps[kind][row["id"]]]
            properties = source[kind][row["id"]]
            check(f"{kind} {row['id']} topology and canonical measurement",
                  row["type"] == expected["type"] and properties[measure][0] == expected[measure] and
                  properties["centroid"] == expected["centroid"] and set(row["nodeIds"]) <= nodes.keys())
    triangle_nodes = {row["id"]: set() for row in observed["faces"]}
    for triangle in observed["triangles"]:
        triangle_nodes[triangle["sourceFaceId"]].update(triangle["nodeIds"])
    check("triangles retain original source face membership", all(
        triangle_nodes[row["id"]] == set(row["nodeIds"]) for row in observed["faces"]))

    solid, = source["solid"].values()
    for name, actual, expected in (
        ("volume", solid["volume"][0], part["volume"]),
        ("surface area", solid["surface_area"][0], part["surfaceArea"]),
        ("center of mass", solid["center_of_mass"], part["centerOfMass"]),
        ("bounding box", solid["bounding_box"], part["boundingBox"]),
        ("center of mass inertia", solid["inertia_at_center_of_mass"], sum(part["inertiaAtCenterOfMass"], [])),
    ):
        check(f"solid {name}", actual == expected)


def compare_scene(scene, observed, check):
    check("scene uses the same source bytes", scene["success"] and scene["SourceSha256"] == observed["sourceSha256"])
    check("scene preserves node IDs and coordinates", [
        (node["id"], [node["x"], node["y"], node["z"]]) for node in scene["nodes"]
    ] == [(node["id"], node["coordinates"]) for node in observed["nodes"]])
    check("scene preserves triangles and source face IDs", [
        {key: value for key, value in element.items() if key != "vtkCellType"}
        for element in scene["elements"] if element["vtkCellType"] == 5
    ] == observed["triangles"])
    cad = scene["cad"]
    check("scene preserves original CAD measurements and units",
          cad["entities"] == observed["metadata"]["entities"] and cad["lengthUnit"] == observed["metadata"]["lengthUnit"])
    sides = {tuple(sorted((a, b))) for triangle in observed["triangles"]
             for a, b in zip(triangle["nodeIds"], triangle["nodeIds"][1:] + triangle["nodeIds"][:1])}
    segments = [tuple(segment["nodeIds"]) for segment in cad["edgeSegments"]]
    check("edge segments are unique triangle sides", len(set(segments)) == len(segments) and set(segments) <= sides)
    edge_nodes = {edge["id"]: set() for edge in observed["edges"]}
    for segment in cad["edgeSegments"]:
        check(f"segment {segment['nodeIds']} retains a source edge", bool(segment["sourceEdgeIds"]))
        for source_id in segment["sourceEdgeIds"]:
            edge_nodes[source_id].update(segment["nodeIds"])
    check("segments cover every original edge and its nodes",
          edge_nodes == {edge["id"]: set(edge["nodeIds"]) for edge in observed["edges"]})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspector", type=Path, required=True, help="Built PrePoMaxX.InspectVis.dll")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    command = ["dotnet", str(args.inspector.resolve())]
    checks = []

    def check(name, passed):
        checks.append({"name": name, "passed": passed})
        if not passed:
            raise ValueError(name)

    result = {"success": False, "os": platform.system(), "architecture": platform.machine(), "checks": checks}
    try:
        hashes = json.loads((REFERENCE / "verification.json").read_text())["outputs"]
        raw = FIXTURE.read_bytes()
        expected = (REFERENCE / "geometry.json").read_bytes()
        check("exact original VIS bytes", hashlib.sha256(raw).hexdigest() == hashes[FIXTURE.name]["sha256"])
        check("exact original geometry capture",
              hashlib.sha256(expected).hexdigest() == hashes["geometry.json"]["sha256"])
        observed = json.loads(subprocess.check_output([*command, FIXTURE], timeout=30))
        check("portable read identifies the original bytes", observed["success"] and
              observed["sourceSha256"] == hashes[FIXTURE.name]["sha256"])
        compare(observed, json.loads(expected), check)
        scene = json.loads(subprocess.check_output([*command, "scene", FIXTURE], timeout=30))
        compare_scene(scene, observed, check)
        with TemporaryDirectory(prefix="prepomaxx-vis-controls-") as temp:
            alias = Path(temp) / "alias.vis"
            # Assign the same first segment to two CAD edges before the shared deduplication.
            alias.write_bytes(add_first_face_edge(raw, b"2 1 2"))
            aliased = json.loads(subprocess.check_output([*command, "scene", alias], timeout=30))
            check("merged segment retains coincident source edge IDs",
                  any(segment["sourceEdgeIds"] == [1, 2] for segment in aliased["cad"]["edgeSegments"]))
            partial = Path(temp) / "partial-face.vis"
            # In this face, 1-3 is a free side and 3-2 is shared by two triangles.
            # 1-2 is a free side too, but it skips a node on the added edge 5.
            partial.write_bytes(add_first_face_edge(raw, b"5 1 3 2"))
            partial_scene = json.loads(subprocess.check_output([*command, "scene", partial], timeout=30))
            by_nodes = {tuple(segment["nodeIds"]): segment["sourceEdgeIds"]
                        for segment in partial_scene["cad"]["edgeSegments"]}
            check("consecutive free side keeps the source edge ID", by_nodes[1, 3] == [2, 5])
            check("nonconsecutive chord does not acquire a false edge ID", by_nodes[1, 2] == [1])
            for name, content in (
                ("unsupported version", raw.replace(b"VIS file format: 2", b"VIS file format: 1", 1)),
                ("missing tessellation", raw.split(b"Number of visualization vertices:", 1)[0]),
            ):
                path = Path(temp) / "refused.vis"
                path.write_bytes(content)
                for mode in ([], ["scene"]):
                    run = subprocess.run([*command, *mode, path], capture_output=True, timeout=30)
                    check(name + " refused in " + ("scene" if mode else "inspect"),
                          run.returncode == 1 and not run.stdout and json.loads(run.stderr)["success"] is False)
        result.update(success=True, decodedSha256=hashlib.sha256(
            json.dumps(observed, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            sceneSha256=hashlib.sha256(json.dumps(scene, sort_keys=True, separators=(",", ":")).encode()).hexdigest())
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        result["error"] = str(error)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"success": result["success"], "checks": len(checks),
                      "decodedSha256": result.get("decodedSha256"), "sceneSha256": result.get("sceneSha256"),
                      "error": result.get("error")}))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Compose renderer IDs while retaining CAD IDs within their original parts."""
import hashlib
import json


def read_cad_parts(source, tool, decoder, work, *, cancel=None):
    outputs = tool.convert_parts(source, work, cancel=cancel)
    decoded = [(brep.stem, decoder(vis, cancel=cancel)) for brep, vis in outputs]
    scene = compose_cad_parts(decoded)
    description = getattr(tool, "description", "CAD command protocol")
    scene["cad"]["conversion"] = description if isinstance(description, str) else "CAD command protocol"
    return scene


def compose_cad_parts(parts):
    if not parts:
        raise ValueError("CAD import produced no decoded parts.")
    for _, scene in parts:
        if scene.get("success") is not True or not scene["nodes"] or not scene["elements"]:
            raise ValueError("Every CAD part must decode successfully with display triangles.")
    if len(parts) == 1:
        return parts[0][1]
    nodes, elements, segments, records = [], [], [], []
    length_unit = parts[0][1]["cad"]["lengthUnit"]
    for part_id, (name, scene) in enumerate(parts, 1):
        if scene.get("success") is not True or scene["cad"]["lengthUnit"] != length_unit:
            raise ValueError("CAD parts must decode successfully with the same length unit.")
        metadata = scene["cad"]["entities"]
        face_ids = {entity["id"] for entity in metadata.get("face", [])}
        edge_ids = {entity["id"] for entity in metadata.get("edge", [])}
        node_map = {}
        for node in scene["nodes"]:
            if node["id"] in node_map:
                raise ValueError("A CAD part contains duplicate source node IDs.")
            render_id = len(nodes) + 1
            node_map[node["id"]] = render_id
            nodes.append({**node, "id": render_id, "sourceNodeId": node["id"], "sourcePartId": part_id})
        triangle_ids = set()
        for element in scene["elements"]:
            if (element["id"] in triangle_ids or element["vtkCellType"] != 5 or len(element["nodeIds"]) != 3
                    or element["sourceFaceId"] not in face_ids):
                raise ValueError("Invalid CAD triangle identity or source face.")
            triangle_ids.add(element["id"])
            elements.append({**element, "id": len(elements) + 1,
                             "nodeIds": [node_map[node] for node in element["nodeIds"]],
                             "sourceElementId": element["id"], "sourcePartId": part_id})
        for segment in scene["cad"]["edgeSegments"]:
            if len(segment["nodeIds"]) != 2 or not segment["sourceEdgeIds"] or not set(segment["sourceEdgeIds"]) <= edge_ids:
                raise ValueError("Invalid CAD segment identity or source edge.")
            segments.append({**segment, "nodeIds": [node_map[node] for node in segment["nodeIds"]],
                             "sourcePartId": part_id})
        records.append({"id": part_id, "name": name, "sourceSha256": scene["SourceSha256"],
                        "nodeCount": len(scene["nodes"]), "triangleCount": len(scene["elements"]),
                        "entities": metadata})
    identity = [{"id": record["id"], "sourceSha256": record["sourceSha256"]} for record in records]
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"success": True, "SourceSha256": digest, "sourceHashKind": "ordered-vis-parts",
            "nodes": nodes, "elements": elements,
            "cad": {"lengthUnit": length_unit, "parts": records, "edgeSegments": segments}}

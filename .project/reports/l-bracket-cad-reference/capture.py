# Run inside original PrePoMax 3.0.0 with L_bracket_r.step already open.
import json


def plain(value):
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if hasattr(value, "tolist"):
        return plain(value.tolist())
    if hasattr(value, "item"):
        return plain(value.item())
    return [plain(item) for item in value]


parts = pmx.model.geometry.parts
part = parts.first()
if len(parts) != 1 or not part.is_cad_part:
    raise RuntimeError("Expected one imported CAD part")

faces = part.get_face_data()
edges = part.get_edge_data()
vertices = part.get_vertex_data()
metadata = part.get_geometry_metadata()
if not metadata.available:
    raise RuntimeError("Expected supplemental CAD metadata")

result = {
    "unitSystem": str(pmx.model.properties.unit_system),
    "part": {
        "id": int(part.id),
        "name": str(part.name),
        "volume": float(part.volume),
        "surfaceArea": float(part.surface_area),
        "boundingBox": plain(part.get_bounding_box()),
        "centerOfMass": plain(part.center_of_mass),
        "inertiaAtCenterOfMass": plain(part.get_inertia_at_center_of_mass()),
        "inertiaAtOrigin": plain(part.get_inertia_at_origin()),
        "nodeCount": int(part.node_count),
        "elementCount": int(part.element_count),
    },
    "faces": [
        {"id": int(faces.ids[i]), "geometryId": int(faces.geometry_ids[i]),
         "type": str(faces.types[i]), "area": float(faces.areas[i]),
         "centroid": plain(faces.centroids[i]), "normal": plain(faces.normals[i])}
        for i in range(faces.count)
    ],
    "edges": [
        {"id": int(edges.ids[i]), "geometryId": int(edges.geometry_ids[i]),
         "type": str(edges.types[i]), "length": float(edges.lengths[i]), "centroid": plain(edges.centroids[i])}
        for i in range(edges.count)
    ],
    "vertices": [
        {"nodeId": int(vertices.node_ids[i]), "geometryId": int(vertices.geometry_ids[i]),
         "coordinates": plain(vertices.coordinates[i])}
        for i in range(vertices.count)
    ],
    "metadata": {
        "formatVersion": plain(metadata.format_version),
        "coordinateSystem": str(metadata.coordinate_system),
        "lengthUnit": str(metadata.length_unit),
        "entities": {
            str(kind): [
                {"id": int(entity.id),
                 "properties": {str(name): plain(entity.get_property(name)) for name in entity.property_names}}
                for entity in metadata.get_entities(kind)
            ]
            for kind in metadata.entity_kinds
        },
    },
}
with open("geometry.json", "w", encoding="utf-8", newline="\n") as stream:
    json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
    stream.write("\n")
print("CAD REFERENCE CAPTURED")

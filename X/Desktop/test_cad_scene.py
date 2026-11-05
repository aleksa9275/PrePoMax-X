"""Part identity must survive source ID collisions and coincident coordinates."""
import copy
import unittest

from cad_scene import compose_cad_parts


def triangle_scene(digest, volume):
    return {"success": True, "SourceSha256": digest,
            "nodes": [{"id": n, "x": x, "y": y, "z": 0} for n, x, y in ((1, 0, 0), (2, 1, 0), (3, 0, 1))],
            "elements": [{"id": 7, "vtkCellType": 5, "nodeIds": [1, 2, 3], "sourceFaceId": 1}],
            "cad": {"lengthUnit": "model", "entities": {
                "face": [{"id": 1, "properties": {"area": [0.5]}}],
                "edge": [{"id": 1, "properties": {"length": [1]}}],
                "solid": [{"id": 1, "properties": {"volume": [volume]}}]},
                "edgeSegments": [{"nodeIds": [1, 2], "sourceEdgeIds": [1]}]}}


class CadPartIdentity(unittest.TestCase):
    def test_part_ids_preserve_coincident_nodes_and_repeated_entity_ids(self):
        first, second = triangle_scene("first", 1), triangle_scene("second", 2)
        originals = copy.deepcopy([first, second])
        result = compose_cad_parts([("first", first), ("second", second)])
        self.assertEqual([first, second], originals)
        self.assertEqual(len(result["nodes"]), 6)
        self.assertEqual({node["id"] for node in result["nodes"]}, set(range(1, 7)))
        self.assertEqual([(e["sourcePartId"], e["sourceElementId"], e["sourceFaceId"]) for e in result["elements"]],
                         [(1, 7, 1), (2, 7, 1)])
        self.assertEqual([e["nodeIds"] for e in result["elements"]], [[1, 2, 3], [4, 5, 6]])
        self.assertEqual([s["nodeIds"] for s in result["cad"]["edgeSegments"]], [[1, 2], [4, 5]])
        self.assertEqual([p["entities"] for p in result["cad"]["parts"]],
                         [first["cad"]["entities"], second["cad"]["entities"]])
        self.assertEqual(result, compose_cad_parts([("first", first), ("second", second)]))
        second["SourceSha256"] = "changed"
        changed = compose_cad_parts([("first", first), ("second", second)])
        self.assertNotEqual(result["SourceSha256"], changed["SourceSha256"])

    def test_single_part_retains_its_existing_scene_contract(self):
        original = triangle_scene("single", 1)
        self.assertIs(compose_cad_parts([("single", original)]), original)

    def test_native_single_part_keeps_part_scope_for_picking_and_mesh_regions(self):
        original = triangle_scene("single", 1)
        result = compose_cad_parts([("single", original)], force_parts=True)
        self.assertEqual(result["cad"]["parts"][0]["id"], 1)
        self.assertEqual(result["elements"][0]["sourcePartId"], 1)
        self.assertEqual(result["elements"][0]["sourceElementId"], 7)
        self.assertEqual(result["elements"][0]["sourceFaceId"], 1)
        self.assertEqual(result["cad"]["edgeSegments"][0]["sourcePartId"], 1)
        self.assertNotIn("parts", original["cad"])

    def test_refuses_invalid_part_identity_and_units(self):
        first = triangle_scene("first", 1)
        changes = [
            lambda s: s["nodes"].append(s["nodes"][0]),
            lambda s: s["cad"].update(lengthUnit="mm"),
            lambda s: s["elements"][0].update(sourceFaceId=2),
            lambda s: s["elements"][0].update(nodeIds=[1, 2, 99]),
            lambda s: s["cad"]["edgeSegments"][0].update(sourceEdgeIds=[99]),
            lambda s: s.update(success=False),
        ]
        for change in changes:
            second = triangle_scene("second", 2)
            change(second)
            with self.subTest(change=change), self.assertRaises((ValueError, KeyError)):
                compose_cad_parts([("first", first), ("second", second)])


if __name__ == "__main__":
    unittest.main()

"""Regression checks for the independent native geometry verification oracle."""
import copy
from pathlib import Path
from runpy import run_path
import unittest

compare_scene = run_path(str(Path(__file__).with_name("verify-native.py")))["compare_scene"]


class NativeCoverage(unittest.TestCase):
    def setUp(self):
        self.scene = {
            "success": True, "SourceSha256": "reference",
            "nodes": [{"id": i+1, "x": x, "y": y, "z": 0}
                      for i, (x, y) in enumerate(((0,0), (1,0), (1,1), (0,1)))],
            "elements": [{"id": 1, "vtkCellType": 5, "nodeIds": [1,2,3], "sourceFaceId": 1},
                         {"id": 2, "vtkCellType": 5, "nodeIds": [1,3,4], "sourceFaceId": 1}],
            "cad": {"lengthUnit": "Model", "edgeSegments": [], "entities": {
                "face": [{"id": 1, "properties": {"type": ["Plane"], "area": [1], "edge_ids": [1,2,3,4]}}]}}}

    def alternative(self):
        value = copy.deepcopy(self.scene)
        value["SourceSha256"] = "native"
        value["elements"][0]["nodeIds"] = [1,2,4]
        value["elements"][1]["nodeIds"] = [2,3,4]
        return value

    def test_allows_only_equivalent_planar_diagonal(self):
        result = compare_scene(self.scene, self.alternative())
        self.assertFalse(result["exactDecodedSceneMatch"])
        self.assertEqual(result["changedPlanarTriangulations"], [1])

    def test_rejects_orientation_overlap_boundary_or_curvature_change(self):
        for change in ("reverse", "overlap", "boundary", "curved"):
            with self.subTest(change=change):
                native = self.alternative()
                if change == "reverse":
                    native["elements"][0]["nodeIds"].reverse()
                elif change == "overlap":
                    native["elements"][1]["nodeIds"] = [1,2,3]
                elif change == "boundary":
                    native["elements"][1]["nodeIds"] = [1,2,4]
                else:
                    native["cad"]["entities"]["face"][0]["properties"]["type"] = ["Cylinder"]
                with self.assertRaises(ValueError):
                    compare_scene(self.scene, native)

    def test_preserves_exact_source_coordinates_ids_and_measurement_bounds(self):
        for change in ("coordinate", "face", "edge", "area"):
            with self.subTest(change=change):
                native = self.alternative()
                if change == "coordinate":
                    native["nodes"][0]["x"] += 1e-15
                elif change == "face":
                    native["cad"]["entities"]["face"][0]["id"] = 2
                elif change == "edge":
                    native["cad"]["entities"]["face"][0]["properties"]["edge_ids"][-1] = 5
                else:
                    native["cad"]["entities"]["face"][0]["properties"]["area"] = [1.001]
                with self.assertRaises(ValueError):
                    compare_scene(self.scene, native)


if __name__ == "__main__":
    unittest.main()

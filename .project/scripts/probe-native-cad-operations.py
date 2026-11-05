#!/usr/bin/env python3
"""Measure bounded original CAD command roundtrips on an analytical box."""
import argparse
import json
import math
from pathlib import Path
import platform
from runpy import run_path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "X/Desktop"))
from cad_import import NativeCadTool, ReferenceCadTool, file_sha256, run_stage

decode = run_path(str(ROOT / "X/Feasibility/Cad/verify-native.py"))["decode"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--native-runtime", type=Path)
    modes.add_argument("--reference-runtime", type=Path)
    parser.add_argument("--bottle")
    parser.add_argument("--inspector", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if bool(args.reference_runtime) != bool(args.bottle):
        parser.error("Use --reference-runtime and --bottle together")
    out = args.output.resolve()
    out.mkdir(parents=True)
    tool = (ReferenceCadTool(args.reference_runtime, args.bottle) if args.bottle
            else NativeCadTool(args.native_runtime))
    report = {"success": False, "host": platform.system(), "machine": platform.machine(),
              "conversion": tool.description, "executableSha256": file_sha256(Path(tool.command[-1])),
              "operations": [], "generalCadRepairAccepted": False}

    def tool_path(path):
        return "Z:" + str(path).replace("/", "\\") if args.bottle else str(path)

    def command(operation, *parameters):
        tool.verify_runtime()
        arguments = [tool_path(x) if isinstance(x, Path) else str(x) for x in parameters]
        run_stage([*tool.command, operation, *arguments], out,
                  f"command-{len(list(out.glob('command-*.log'))):02d}-{operation}.log")
        tool.verify_runtime()

    def inspect(brep, name):
        vis = out / (name + ".vis")
        command("BREP_VISUALIZATION", brep, vis, "0.01", "1", "0.26")
        return decode(args.inspector.resolve(), vis)

    def solids(scene):
        return scene["cad"]["entities"]["solid"]

    def assert_box(scene, expected_center):
        if len(solids(scene)) != 1 or len(scene["cad"]["entities"]["face"]) != 6:
            raise ValueError("Box lost its one-solid/six-face topology")
        properties = solids(scene)[0]["properties"]
        if not math.isclose(properties["volume"][0], 2000, rel_tol=1e-12, abs_tol=1e-9):
            raise ValueError("Box volume changed")
        if any(not math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-10)
               for a,b in zip(properties["center_of_mass"], expected_center)):
            raise ValueError("Box center differs from analytical expectation")
        return {"solidCount": 1, "faceCount": 6, "volume": properties["volume"][0],
                "center": properties["center_of_mass"]}

    try:
        fixture = ROOT / "APIs/Python/Test_Scripts/Models/sweep_two_apart.brep"
        source_sha = file_sha256(fixture)
        reference = json.loads((ROOT / ".project/reports/multipart-cad-reference.json").read_text())
        if source_sha != reference["sourceSha256"]:
            raise ValueError("Original two-part BREP fixture changed")
        parts = tool.convert_parts(fixture, out / "input")
        source = parts[0][0]
        input_sha = file_sha256(source)
        baseline = inspect(source, "baseline")
        report["baseline"] = assert_box(baseline, [5,5,10])
        for operation, center in (("repair", [5,5,10]), ("translate", [12,2,15])):
            result = out / (operation + ".brep")
            if operation == "repair":
                command("BREP_REPAIR", source, result, "1", "0.000001")
            else:
                definition = out / "translate.txt"
                definition.write_text("Transform type: Translate\nDirection: 7 -3 5\n")
                command("BREP_TRANSFORM", source, result, definition)
            data = inspect(result, operation)
            report["operations"].append({"operation": operation, "brepSha256": file_sha256(result),
                                          **assert_box(data, center)})

        definition = out / "split.txt"
        definition.write_text("Tool type: Plane\nExtent: 0 10 0 10 0 20\n"
                              "Plane origin: 0 0 10\nPlane normal: 0 0 1\n")
        result = out / "split.brep"
        command("BREP_SPLIT", source, result, definition)
        data = inspect(result, "split")
        masses = [s["properties"]["volume"][0] for s in solids(data)]
        centers = sorted((s["properties"]["center_of_mass"] for s in solids(data)), key=lambda p: p[2])
        if len(masses) != 2 or any(not math.isclose(v, 1000, abs_tol=1e-9) for v in masses):
            raise ValueError("Mid-plane split did not preserve volume in two equal solids")
        for actual, expected in zip(centers, ([5,5,5], [5,5,15])):
            if any(not math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-10) for a,b in zip(actual, expected)):
                raise ValueError("Split solid center differs from analytical expectation")
        origins = result.with_suffix(".brep.origins").read_text().split()
        if origins != ["1", "1"]:
            raise ValueError("Split lost the source-solid origin mapping")
        report["operations"].append({"operation": "split", "brepSha256": file_sha256(result),
                                      "volumes": masses, "centers": centers, "sourceSolidOrigins": origins})

        step = out / "roundtrip.step"
        command("SAVE_BREP_AS_STEP", source, step)
        reimported = tool.convert_parts(step, out / "roundtrip")
        if len(reimported) != 1:
            raise ValueError("STEP roundtrip changed part count")
        data = decode(args.inspector.resolve(), reimported[0][1])
        report["operations"].append({"operation": "STEP roundtrip", "stepSha256": file_sha256(step),
                                      **assert_box(data, [5,5,10])})
        if file_sha256(source) != input_sha or file_sha256(fixture) != source_sha:
            raise ValueError("CAD command modified its input")
        report.update(success=True, fixtureSha256=source_sha, inputBrepSha256=input_sha)
    except Exception as error:
        report["error"] = str(error)
    (out / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

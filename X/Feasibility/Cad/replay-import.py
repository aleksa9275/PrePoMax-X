#!/usr/bin/env python3
"""Replay the original L-bracket CAD protocol and compare the portable scene."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "X/Desktop"))
from cad_import import CROSSOVER_WINE, REFERENCE_RECEIPT, ReferenceCadTool, convert_cad, file_sha256


def scene(inspector, path, source_hash):
    run = subprocess.run(["dotnet", str(inspector), "scene", str(path)], capture_output=True, timeout=30, check=True)
    value = json.loads(run.stdout)
    if value.get("success") is not True or value.pop("SourceSha256") != source_hash:
        raise ValueError("The portable reader did not identify the expected VIS input.")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--mesher", type=Path, help="Explicit executable for direct candidate replay")
    modes.add_argument("--reference-runtime", type=Path, help="Original 3.0.0 Meshers/Netgen directory")
    parser.add_argument("--bottle", help="Existing isolated CrossOver bottle for the Windows reference")
    parser.add_argument("--wine", type=Path, default=CROSSOVER_WINE)
    parser.add_argument("--inspector", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if bool(args.reference_runtime) != bool(args.bottle):
        parser.error("--reference-runtime and --bottle must be supplied together")
    out = args.output.resolve()
    out.mkdir(parents=True)
    report = {"success": False, "os": platform.system(), "architecture": platform.machine(),
              "mode": "windows-reference-through-crossover" if args.bottle else "direct-candidate",
              "runs": []}
    try:
        reference = json.loads(REFERENCE_RECEIPT.read_text())
        fixture = ROOT / reference["fixture"]["path"]
        vis = HERE / "fixtures/l-bracket.vis"
        expected_vis = reference["outputs"][vis.name]["sha256"]
        expected_brep = reference["outputs"]["l-bracket_solid_0001.brep"]["sha256"]
        report["stepSha256"] = file_sha256(fixture)
        if report["stepSha256"] != reference["fixture"]["sha256"] or file_sha256(vis) != expected_vis:
            raise ValueError("The tracked STEP or VIS differs from the recorded original fixture.")
        inspector = args.inspector.resolve()
        baseline = scene(inspector, vis, expected_vis)
        tool = ReferenceCadTool(args.reference_runtime, args.bottle, wine=args.wine) if args.bottle else None
        executable = tool.runtime / "NetGenMesher.exe" if tool else args.mesher.resolve()
        report["executableSha256"] = file_sha256(executable)
        for name in ("first run", "repeat run"):
            work = out / name
            if tool:
                brep, generated = tool.convert(fixture, work)
            else:
                brep, generated = convert_cad(fixture, work, [str(executable)])
            run = {"brepSha256": file_sha256(brep), "visSha256": file_sha256(generated)}
            report["runs"].append(run)
            run["sceneMatches"] = scene(inspector, generated, run["visSha256"]) == baseline
            if not run["sceneMatches"]:
                raise ValueError(f"{name} does not match the original decoded L-bracket scene.")
        if report["runs"][0] != report["runs"][1]:
            raise ValueError("Repeat conversion produced different output.")
        run = report["runs"][0]
        report["originalBytesMatch"] = run["brepSha256"] == expected_brep and run["visSha256"] == expected_vis
        if tool and not report["originalBytesMatch"]:
            raise ValueError("Windows reference replay differs from the original BREP or VIS bytes.")
        if file_sha256(fixture) != report["stepSha256"] or file_sha256(executable) != report["executableSha256"]:
            raise ValueError("The original input or executable changed during replay.")
        report["decodedSceneSha256"] = hashlib.sha256(
            json.dumps(baseline, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        report["success"] = True
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        report["error"] = str(error)
    (out / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

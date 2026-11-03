#!/usr/bin/env python3
"""Run the original bounded deck/job/readers with an explicit native research build."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--hosts-dir", type=Path, help="Verified shared build output with self-contained hosts")
    args = parser.parse_args()
    build, out = args.build.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    registry = build / "build-registry.json"
    report = {"success": False, "recordedAtUtc": datetime.now(timezone.utc).isoformat(),
        "os": platform.system(), "architecture": platform.machine(), "commands": [],
        "toolSha256": sha(Path(__file__)), "threads": 1,
        "scope": "One C3D8 static cube; not broad numerical/backend/performance/release acceptance"}
    def run(command, name):
        done = subprocess.run(list(map(str, command)), cwd=ROOT, text=True, capture_output=True, timeout=180)
        (out / (name + ".stdout")).write_text(done.stdout)
        (out / (name + ".stderr")).write_text(done.stderr)
        report["commands"].append({"arguments": list(map(str, command)), "exitCode": done.returncode, "log": name})
        if done.returncode:
            raise RuntimeError(f"{name} failed: {done.stderr[-1000:]}")
        return json.loads(done.stdout)
    try:
        profile = json.loads(registry.read_text())["builds"][0]
        report["buildReportSha256"] = sha(build / "build-report.json")
        report["registrySha256"] = sha(registry)
        solve = ROOT / "X/Execution/Solve/bin/Release/net10.0/PrePoMaxX.Solve.dll"
        inspect = ROOT / "X/Results/Inspect/bin/Release/net10.0/PrePoMaxX.InspectResults.dll"
        solve_command, inspect_command = ["dotnet", solve], ["dotnet", inspect]
        if args.hosts_dir:
            sys.path.insert(0, str(ROOT / "X/Build"))
            from build import verify_hosts, require_native, catalog
            hosts = args.hosts_dir.resolve()
            target_id = json.loads((hosts / "build.json").read_text())["target"]
            require_native(catalog()["targets"][target_id])
            host_report = verify_hosts(hosts, target_id)
            suffix = catalog()["targets"][target_id]["executableSuffix"]
            solve = hosts / "hosts/solve" / ("PrePoMaxX.Solve" + suffix)
            inspect = hosts / "hosts/results" / ("PrePoMaxX.InspectResults" + suffix)
            solve_command, inspect_command = [solve], [inspect]
            report["hostBuildSha256"] = sha(hosts / "build.json")
            report["target"] = target_id
        report["hostHashes"] = {str(p): sha(p) for p in [solve, inspect]}
        mesh = ROOT / "X/Analysis/StaticDeck/cube-mesh.inp"
        spec = ROOT / "X/Analysis/StaticDeck/cube-analysis.json"
        report["inputs"] = {str(p.relative_to(ROOT)): sha(p) for p in [mesh, spec]}
        job = run([*solve_command, "--registry", registry, "run-static", profile["id"], build / "bin", mesh, spec, out / "run", "120"], "solve")
        report["solverExecuted"] = job["solverExecuted"]
        report["transportCompleted"] = job["success"]
        frd = run([*inspect_command, "inspect-frd", out / "run/analysis.frd"], "frd")
        dat = run([*inspect_command, "inspect-dat", out / "run/analysis.dat"], "dat")
        monitor = run([*solve_command, "inspect-monitor", out / "run/analysis.sta", out / "run/analysis.cvg"], "monitor")
        module = importlib.util.spec_from_file_location("reference", ROOT / "X/Feasibility/Solver/run-reference.py")
        reference = importlib.util.module_from_spec(module)
        module.loader.exec_module(reference)
        blocks = reference.parse_dat((out / "run/analysis.dat").read_text())
        checks = reference.analytical_checks(blocks)
        altered = {key: [row[:] for row in rows] for key, rows in blocks.items()}
        altered["displacements"][0][1] += 0.01
        report["alteredDisplacementRejected"] = not all(c["passed"] for c in reference.analytical_checks(altered))
        checks.extend([
            {"name": "original FRD node IDs retained", "passed": sorted(n["id"] for n in frd["nodes"]) == list(range(1, 9))},
            {"name": "original FRD element ID retained", "passed": [e["id"] for e in frd["elements"]] == [1]},
            {"name": "original FRD displacement and stress fields decoded", "passed": {"DISP", "STRESS"}.issubset(f["name"] for f in frd["fields"])},
            {"name": "original DAT history contains records", "passed": dat["DataSetCount"] > 0 and len(dat["histories"]) > 0},
            {"name": "original monitor records completed increment", "passed": monitor["status"]["Count"] == 1 and monitor["status"]["TotalTimes"] == [1]},
        ])
        report["checks"] = checks
        report["frdFields"] = [{k: f[k] for k in ["name", "stepId", "incrementId", "time"]} for f in frd["fields"]]
        report["datHistories"] = len(dat["histories"])
        report["outputHashes"] = {p.name: sha(p) for p in (out / "run").iterdir() if p.is_file()}
        report["success"] = all(c["passed"] for c in checks) and report["alteredDisplacementRejected"]
    except (OSError, ValueError, RuntimeError, KeyError, IndexError, subprocess.SubprocessError) as error:
        report["error"] = str(error)
    (out / "workflow.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report.get(k) for k in ["success", "solverExecuted", "checks", "error"]}))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

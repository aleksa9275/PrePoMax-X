#!/usr/bin/env python3
"""Run existing portable checks by area; retain fresh results and a reproduction manifest."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
# Whole original assemblies (D062): every area builds X/Domain; historical slice
# replays and source-layout guards were retired with the slice projects.
AREAS = {
    "domain": "X/Domain/verify-domain.py",
    "controller": "X/Controller/verify-controller.py",
    "app": "X/App/verify-app.py",
    "core": "X/Core/verify.py",
    "analysis": "X/Analysis/verify-analysis.py",
    "execution": "X/Execution/verify-execution.py",
    "results": "X/Results/verify-results.py",
}
SOURCE_ROOTS = ("X/", "CaeGlobals/", "CaeMesh/", "CaeModel/", "CaeResults/", "CaeJob/", "vtkControl/", "PrePoMax/", "APIs/", "UserControls/", "GmshCaller/")
SOURCE_SUFFIXES = {".cs", ".cpp", ".h", ".py", ".csproj", ".props", ".targets", ".slnx", ".yml", ".yaml", ".Config"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(*arguments):
    return subprocess.check_output(["git", *arguments], cwd=ROOT)


def plan(profile, areas, output, host):
    steps = []
    for area in areas:
        result = output / f"{area}-current.json"
        arguments = [sys.executable, AREAS[area], "--expect-os", host["os"],
            "--expect-architecture", host["architecture"], "--output", str(result)]
        steps.append({"area": area, "revision": "current", "result": result, "arguments": arguments})
    return steps


def safe_code_path(name, tracked):
    path = Path(name)
    if path.is_absolute() or ".." in path.parts or {"artifacts", "bin", "obj", "__pycache__"}.intersection(path.parts):
        return False
    if name == ".gitlab-ci.yml":
        return tracked
    # JSON/config files are copied only when already tracked; never collect arbitrary untracked data.
    return name.startswith(SOURCE_ROOTS) and (path.suffix in SOURCE_SUFFIXES or name == "X/Persistence/allowed-types.txt" or (tracked and path.suffix in {".json", ".config"}))


def retain_source(output):
    tracked = set(git("ls-files", "-z").decode().split("\0"))
    changed = set(git("diff", "--name-only", "-z", "HEAD").decode().split("\0"))
    changed.update(git("ls-files", "--others", "--exclude-standard", "-z").decode().split("\0"))
    paths = sorted(p for p in changed if p and safe_code_path(p, p in tracked))
    rows = []
    for name in paths:
        source = ROOT / name
        if source.is_symlink():
            raise ValueError("Do not snapshot a symlinked source: " + name)
        if source.exists():
            data = source.read_bytes()
            target = output / "source" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            rows.append({"path": name, "state": "modified" if name in tracked else "untracked", "sha256": sha(data)})
        else:
            rows.append({"path": name, "state": "deleted"})
    tracked_paths = [p for p in paths if p in tracked]
    patch = git("diff", "--binary", "HEAD", "--", *tracked_paths) if tracked_paths else b""
    (output / "source.patch").write_bytes(patch)
    return {"head": git("rev-parse", "HEAD").decode().strip(),
        "dirty": bool(git("status", "--porcelain")), "patch": "source.patch", "patchSha256": sha(patch),
        "changedCode": rows, "scope": "changed build/test/shared source only; no user models or private files"}


def run_step(step, output, execute=subprocess.run):
    started = time.monotonic()
    label = f"{step['area']}-{step['revision']}"
    row = {"area": step["area"], "revision": step["revision"], "arguments": step["arguments"],
        "result": step["result"].name if step["result"] else None,
        "log": label + ".log", "status": "failed"}
    try:
        done = execute(step["arguments"], cwd=ROOT, text=True, capture_output=True, timeout=900)
        row["exitCode"] = done.returncode
        (output / row["log"]).write_text(done.stdout + "\n--- stderr ---\n" + done.stderr)
        if done.returncode != 0:
            raise ValueError("Check process returned nonzero")
        if step["result"]:
            result = json.loads(step["result"].read_text())
            if not isinstance(result, dict) or result.get("success") is not True:
                raise ValueError("Verifier did not report success")
            row["resultSha256"] = sha(step["result"].read_bytes())
            row["checks"] = result.get("tests", {}).get("passed")
            element = result.get("elementTests", result.get("regression", {}).get("Elements", {}))
            if "openCorrectnessChecks" in element:
                row["openCorrectnessChecks"] = element["openCorrectnessChecks"]
                row["fullyAccepted"] = element["fullyAccepted"]
        row["status"] = "passed"
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        row["error"] = str(error)
        if isinstance(error, subprocess.TimeoutExpired):
            def string(value):
                return value.decode(errors="replace") if isinstance(value, bytes) else value or ""
            (output / row["log"]).write_text(string(error.stdout) + "\n--- stderr ---\n" + string(error.stderr))
    row["elapsedSeconds"] = round(time.monotonic() - started, 3)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=["fast"], default="fast")
    parser.add_argument("--area", choices=list(AREAS), action="append", help="Repeat to select areas; default: all")
    parser.add_argument("--output", type=Path, help="New diagnostic directory; existing directories are refused")
    parser.add_argument("--dry-run", action="store_true", help="Show commands without executing or writing")
    args = parser.parse_args()
    host = {"os": platform.system(), "architecture": {"arm64": "Arm64", "aarch64": "Arm64", "amd64": "X64", "x86_64": "X64"}.get(platform.machine().lower())}
    if host["architecture"] is None:
        parser.error("Unsupported process architecture")
    areas = list(dict.fromkeys(args.area or list(AREAS)))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    output = (args.output or HERE / "artifacts" / stamp).resolve()
    steps = plan(args.profile, areas, output, host)
    if args.dry_run:
        print(json.dumps({"executed": False, "profile": args.profile, "steps": steps}, default=str, indent=2))
        return 0
    output.mkdir(parents=True, exist_ok=False)
    manifest = {"schemaVersion": 1, "profile": args.profile, "areas": areas, "host": host,
        "recordedAtUtc": datetime.now(timezone.utc).isoformat(), "steps": [], "success": False,
        "plannedStepCount": len(steps),
        "solverExecuted": False, "scope": "Existing engineering checks only; no desktop/native solver/release acceptance"}
    started = time.monotonic()
    try:
        manifest["repository"] = retain_source(output)
        manifest["runnerSha256"] = sha(Path(__file__).read_bytes())
        manifest["dotnetSdk"] = subprocess.check_output(["dotnet", "--version"], text=True, timeout=30).strip()
        for step in steps:
            row = run_step(step, output)
            manifest["steps"].append(row)
            manifest["elapsedSeconds"] = round(time.monotonic() - started, 3)
            (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
            print(f"{row['area']} / {row['revision']}: {row['status']} ({row['elapsedSeconds']} s)", flush=True)
            if row["status"] != "passed":
                break
        manifest["success"] = len(manifest["steps"]) == len(steps) and all(s["status"] == "passed" for s in manifest["steps"])
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        manifest["error"] = str(error)
    manifest["elapsedSeconds"] = round(time.monotonic() - started, 3)
    manifest["pendingSteps"] = [{"area": s["area"], "revision": s["revision"]} for s in steps[len(manifest["steps"]):]]
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"success": manifest["success"], "manifest": str(output / "manifest.json"), "elapsedSeconds": manifest["elapsedSeconds"]}))
    return 0 if manifest["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

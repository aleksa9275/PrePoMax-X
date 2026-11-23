#!/usr/bin/env python3
"""Plan a target and build its native CalculiX solver (the solver stage of X/Build/build_ui.py).

The host publication and the desktop package of the retired X/Desktop preview were removed with it (3.0.2 sync).
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = Path(__file__).with_name("targets.json")

def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

def catalog():
    value = json.loads(CATALOG_PATH.read_text())
    if value["schemaVersion"] != 1 or set(value["targets"]) != {"osx-arm64", "win-x64", "linux-x64", "linux-arm64"}:
        raise ValueError("Unknown shared target catalog")
    return value

def native(target):
    return target["os"] == platform.system() and platform.machine().lower() in target["machines"]

def require_native(target):
    if not native(target):
        raise ValueError("Native operation requires matching OS/architecture; cross-publishing is not execution")

def file_hashes(folder):
    return {p.relative_to(folder).as_posix(): sha(p) for p in sorted(folder.rglob("*")) if p.is_file() and not p.is_symlink()}

class Build:
    def __init__(self, target_id, output):
        self.catalog = catalog()
        self.target_id, self.target = target_id, self.catalog["targets"][target_id]
        self.output = output.resolve()
        self.output.mkdir(parents=True, exist_ok=False)
        self.started = time.monotonic()
        self.report = {"success": False, "target": target_id, "targetData": self.target,
            "recordedAtUtc": datetime.now(timezone.utc).isoformat(), "commands": [],
            "host": {"os": platform.system(), "machine": platform.machine()},
            "targetCatalogSha256": sha(CATALOG_PATH), "nativeExecution": False, "releaseAccepted": False}

    def run(self, command, name=None):
        command = list(map(str, command))
        log = self.output / (name or f"command-{len(self.report['commands']):02d}.log")
        env = dict(os.environ, DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_SKIP_FIRST_TIME_EXPERIENCE="1",
                   PYINSTALLER_CONFIG_DIR=str(self.output / "pyinstaller-cache"))
        with log.open("w") as stream:
            done = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT)
        self.report["commands"].append({"arguments": command, "exitCode": done.returncode, "log": log.name})
        if done.returncode:
            raise RuntimeError("Command failed; see " + str(log))
        return log.read_text()

    def identity(self):
        reproduction = self.output / "reproduction"
        reproduction.mkdir()
        self.report["repository"] = load_module(ROOT / "X/Checks/check.py", "check_source").retain_source(reproduction)
        # Add known native build inputs outside the existing X/Cae snapshot scope.
        inputs = [CATALOG_PATH, ROOT / "ThirdParty/Sources/source-lock.json",
            *sorted((ROOT / "ThirdParty/Build").glob("*.py")),
            *sorted((ROOT / "ThirdParty/Build/platforms").glob("*.py"))]
        self.report["buildInputs"] = {p.relative_to(ROOT).as_posix(): sha(p) for p in inputs}
        for source in inputs:
            target = reproduction / "source" / source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)

    def finish(self):
        self.report["elapsedSeconds"] = round(time.monotonic() - self.started, 3)
        (self.output / "build.json").write_text(json.dumps(self.report, indent=2) + "\n")

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["plan", "build"])
    parser.add_argument("--target", choices=list(catalog()["targets"]), required=True)
    parser.add_argument("--component", choices=["solver"], default="solver")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--jobs", type=int, default=6)
    args = parser.parse_args(argv)
    target = catalog()["targets"][args.target]
    if args.action == "plan":
        print(json.dumps({"target": args.target, "data": target, "matchingNativeHost": native(target),
            "nativeSolverRecipe": target["solverAdapter"] is not None, "executionVerified": False}, indent=2))
        return 0
    if not args.output:
        parser.error("build requires a new --output directory")
    build = None
    try:
        require_native(target)
        if target["solverAdapter"] is None:
            raise ValueError("Target recipe remains pending: solverAdapter")
        build = Build(args.target, args.output)
        build.identity()
        build.run([sys.executable, ROOT / "ThirdParty/Build/calculix-cpu.py", "--target", args.target,
            "--output", build.output / "solver", "--jobs", args.jobs])
        build.report.update(kind="native-cpu-solver-build", solverBuild="solver/build-report.json",
            nativeExecution=False, scope="Build only; execute common workflow separately")
        build.report["success"] = True
    except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError) as error:
        if build:
            build.report["error"] = str(error)
        else:
            print(json.dumps({"success": False, "error": str(error)}), file=sys.stderr)
            return 1
    finally:
        if build:
            build.finish()
    print(json.dumps({k: build.report.get(k) for k in ["success", "target", "kind", "elapsedSeconds", "error"]}))
    return 0 if build.report["success"] else 1

if __name__ == "__main__":
    raise SystemExit(main())

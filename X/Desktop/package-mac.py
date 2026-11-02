#!/usr/bin/env python3
"""Build a local, unsigned research viewport app with isolated self-contained C# readers."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        parser.error("This candidate recipe targets macOS ARM64")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {"success": False, "recordedAtUtc": datetime.now(timezone.utc).isoformat(),
        "commands": [], "python": sys.version, "os": platform.platform(),
        "scope": "Local research app; no Developer ID/notarization/clean-machine or public release acceptance"}
    def run(command):
        log = output / f"package-{len(report['commands']):02d}.log"
        with log.open("w") as stream:
            done = subprocess.run(list(map(str, command)), cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
        report["commands"].append({"arguments": list(map(str, command)), "exitCode": done.returncode, "log": log.name})
        if done.returncode:
            raise RuntimeError("Packaging command failed: " + str(log))
    try:
        identity = {"viewportSha256": hashlib.sha256((ROOT / "X/Desktop/viewport.py").read_bytes()).hexdigest(),
            "gitHead": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT))}
        (output / "source-identity.json").write_text(json.dumps(identity, indent=2) + "\n")
        report["sourceIdentity"] = identity
        for project, folder in [("X/Desktop/MeshScene/MeshScene.csproj", "mesh"), ("X/Results/Inspect/Inspect.csproj", "results")]:
            run(["dotnet", "publish", project, "-c", "Release", "-r", "osx-arm64", "--self-contained", "true",
                "-p:RuntimeFrameworkVersion=10.0.14", f"-p:NativePreviewLockRoot={output / 'locks' / folder}", "--disable-build-servers", "-m:1",
                "--source", ROOT / "X/Analysis/artifacts/offline-feed", "--source", "https://api.nuget.org/v3/index.json",
                "-o", output / "hosts" / folder, "-v:quiet"])
        run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--windowed", "--onedir",
            "--name", "PrePoMax-X-Viewport", "--target-architecture", "arm64", "--collect-all", "vtkmodules",
            "--add-data", f"{output / 'hosts'}:hosts", "--add-data", f"{output / 'source-identity.json'}:.", "--distpath", output / "dist",
            "--workpath", output / "build", "--specpath", output,
            ROOT / "X/Desktop/viewport.py"])
        app = output / "dist/PrePoMax-X-Viewport.app"
        report["app"] = str(app)
        report["fileHashes"] = {str(p.relative_to(app)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in app.rglob("*") if p.is_file() and not p.is_symlink()}
        report["success"] = app.is_dir()
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        report["error"] = str(error)
    (output / "package.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report.get(k) for k in ["success", "app", "error"]}))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

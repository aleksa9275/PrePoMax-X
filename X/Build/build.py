#!/usr/bin/env python3
"""Publish shared sources for explicit targets; record native execution separately."""
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
HOSTS = {
    "mesh": ("X/Desktop/MeshScene/MeshScene.csproj", "PrePoMaxX.MeshScene"),
    "cad": ("X/Feasibility/Cad/Inspect/Inspect.csproj", "PrePoMaxX.InspectVis"),
    "results": ("X/Results/Inspect/Inspect.csproj", "PrePoMaxX.InspectResults"),
    "solve": ("X/Execution/Solve/Solve.csproj", "PrePoMaxX.Solve"),
}

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
        if self.target["desktopPackageAdapter"] == "linux":
            inputs.extend([ROOT / f"X/Desktop/requirements-{self.target_id}.txt",
                           ROOT / "X/Desktop/INSTALL-linux.md"])
        self.report["buildInputs"] = {p.relative_to(ROOT).as_posix(): sha(p) for p in inputs}
        for source in inputs:
            target = reproduction / "source" / source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)

    def finish(self):
        self.report["elapsedSeconds"] = round(time.monotonic() - self.started, 3)
        (self.output / "build.json").write_text(json.dumps(self.report, indent=2) + "\n")

def publish_hosts(build, include=None):
    build.report["kind"] = "self-contained-shared-hosts"
    build.report["sdk"] = build.run(["dotnet", "--version"]).strip()
    include = tuple(include or HOSTS)
    feed = ROOT / "X/Analysis/artifacts/offline-feed"
    feed.mkdir(parents=True, exist_ok=True)
    for folder in include:
        build.run(["dotnet", "publish", HOSTS[folder][0], "-c", "Release", "-r", build.target_id,
            "--self-contained", "true", f"-p:RuntimeFrameworkVersion={build.catalog['runtimeFrameworkVersion']}",
            f"-p:NativePreviewLockRoot={build.output / 'locks' / folder}", "--disable-build-servers", "-m:1",
            "--source", feed, "--source", "https://api.nuget.org/v3/index.json",
            "-o", build.output / "hosts" / folder, "-v:quiet"])
    build.report["hostFiles"] = file_hashes(build.output / "hosts")
    if native(build.target):
        cases = {"mesh": [ROOT / "X/Desktop/nonsequential-cube.inp"],
            "cad": ["scene", ROOT / "X/Feasibility/Cad/fixtures/l-bracket.vis"],
            "results": ["inspect-frd", ROOT / ".project/reports/windows-reference/solver/uniaxial.frd"],
            "solve": ["thread-plan", "--threads", "1"]}
        build.report["smoke"] = []
        for folder in include:
            executable = build.output / "hosts" / folder / (HOSTS[folder][1] + build.target["executableSuffix"])
            value = json.loads(build.run([executable, *cases[folder]], "smoke-" + folder + ".log"))
            if value.get("success") is not True:
                raise ValueError("Native shared host rejected common fixture: " + folder)
            if folder == "mesh" and ([e["id"] for e in value["elements"]] != [7001] or len(value["nodes"]) != 8):
                raise ValueError("Original mesh IDs changed in published host")
            build.report["smoke"].append({"host": folder, "passed": True, "output": value})
        build.report["nativeExecution"] = True
        build.report["nativeExecutionScope"] = "Published C# host smoke only; GUI/installer and numerical solve are separate"
    else:
        build.report["executionPending"] = "Cross-published payload; execute on matching native worker"

def verify_hosts(path, target_id, required=("mesh", "results", "solve")):
    report = json.loads((path / "build.json").read_text())
    if report.get("success") is not True or report.get("target") != target_id:
        raise ValueError("Host build did not complete for requested target")
    if any(p.is_symlink() for p in (path / "hosts").rglob("*")):
        raise ValueError("Staged hosts cannot contain unverified symlinks")
    if file_hashes(path / "hosts") != report["hostFiles"]:
        raise ValueError("Staged host files changed after build")
    for name in required:
        if not any(p.startswith(name + "/") for p in report["hostFiles"]):
            raise ValueError("Required published host missing: " + name)
    return report

def package_preview(build, solver_build=None, package_format="app", pmx_preview=False):
    require_native(build.target)
    publish_hosts(build, ("mesh", "cad", "results", "solve") if solver_build else ("mesh", "cad", "results"))
    if pmx_preview:
        publish_pmx_preview(build)
    identity = {"viewportSha256": sha(ROOT / "X/Desktop/viewport.py"),
        "nativeCocoaSha256": sha(ROOT / "X/Desktop/native_cocoa.py"),
        "viewportProbeSha256": sha(ROOT / "X/Desktop/viewport_probe.py"),
        "analysisEditorSha256": sha(ROOT / "X/Desktop/analysis_editor.py"),
        "solidFormulationsSha256": sha(ROOT / "X/Desktop/solid_formulations.py"),
        "solidWorkflowProbeSha256": sha(ROOT / "X/Desktop/solid_workflow_probe.py"),
        "resultsToolsSha256": sha(ROOT / "X/Desktop/results_tools.py"),
        "thermalWorkflowProbeSha256": sha(ROOT / "X/Desktop/thermal_workflow_probe.py"),
        "thermalWorkflowFixturesSha256": sha(ROOT / "X/Desktop/thermal_workflow_fixtures.py"),
        "thermomechanicalWorkflowProbeSha256": sha(ROOT / "X/Desktop/thermomechanical_workflow_probe.py"),
        "thermomechanicalWorkflowFixturesSha256": sha(ROOT / "X/Desktop/thermomechanical_workflow_fixtures.py"),
        "structuralWorkflowProbeSha256": sha(ROOT / "X/Desktop/structural_workflow_probe.py"),
        "structuralWorkflowFixturesSha256": sha(ROOT / "X/Desktop/structural_workflow_fixtures.py"),
        "planeWorkflowProbeSha256": sha(ROOT / "X/Desktop/plane_workflow_probe.py"),
        "planeWorkflowFixturesSha256": sha(ROOT / "X/Desktop/plane_workflow_fixtures.py"),
        "dynamicsWorkflowProbeSha256": sha(ROOT / "X/Desktop/dynamics_workflow_probe.py"),
        "dynamicsWorkflowFixturesSha256": sha(ROOT / "X/Desktop/dynamics_workflow_fixtures.py"),
        "eigenmodeWorkflowProbeSha256": sha(ROOT / "X/Desktop/eigenmode_workflow_probe.py"),
        "nonlinearWorkflowProbeSha256": sha(ROOT / "X/Desktop/nonlinear_workflow_probe.py"),
        "editorProbeSha256": sha(ROOT / "X/Desktop/editor_probe.py"),
        "cadImportSha256": sha(ROOT / "X/Desktop/cad_import.py"),
        "cadJobSha256": sha(ROOT / "X/Desktop/cad_job.py"),
        "cadDocumentSha256": sha(ROOT / "X/Desktop/cad_document.py"),
        "cadEditSha256": sha(ROOT / "X/Desktop/cad_edit.py"),
        "cadOperationsSha256": sha(ROOT / "X/Desktop/cad_operations.py"),
        "cadHistorySha256": sha(ROOT / "X/Desktop/cad_history.py"),
        "quadraticProbeSha256": sha(ROOT / "X/Desktop/quadratic_probe.py"),
        "quadraticAnalysisSha256": sha(ROOT / "X/Desktop/quadratic_analysis.py"),
        "meshExportSha256": sha(ROOT / "X/Desktop/mesh_export.py"),
        "cadEditProbeSha256": sha(ROOT / "X/Desktop/cad_edit_probe.py"),
        "cadRegionsSha256": sha(ROOT / "X/Desktop/cad_regions.py"),
        "cadWorkflowProbeSha256": sha(ROOT / "X/Desktop/cad_workflow_probe.py"),
        "cadSceneSha256": sha(ROOT / "X/Desktop/cad_scene.py"),
        "desktopJobsSha256": sha(ROOT / "X/Desktop/jobs.py"), "target": build.target_id,
        "targetCatalogSha256": sha(CATALOG_PATH), "gitHead": build.report["repository"]["head"],
        "dirty": build.report["repository"]["dirty"]}
    if build.target["desktopPackageAdapter"] == "macos":
        identity["cadReferenceReceiptSha256"] = sha(ROOT / ".project/reports/l-bracket-cad-reference/verification.json")
    if pmx_preview:
        identity["pmxDesktopSha256"] = sha(ROOT / "X/Desktop/pmx_project.py")
        identity["pmxToolHashes"] = file_hashes(build.output / "pmx-tools")
    (build.output / "source-identity.json").write_text(json.dumps(identity, indent=2) + "\n")
    adapter = build.target["desktopPackageAdapter"]
    helper = load_module(Path(__file__).parent / "platforms" / (adapter + ".py"), "package_platform")
    app = helper.package(build, ROOT, solver_build)
    if package_format == "dmg":
        helper.dmg(build, ROOT, app)
    elif package_format == "tar.gz":
        helper.archive(build, app)
    build.report.update(kind="native-static-workflow-preview" if solver_build else "native-viewport-candidate", app=str(app), sourceIdentity=identity,
        fileHashes=file_hashes(app),
        symlinkTargets={p.relative_to(app).as_posix(): os.readlink(p) for p in sorted(app.rglob("*")) if p.is_symlink()},
        scope=("Local Linux preview; no distro support or release acceptance" if adapter == "linux" else
               "Ad-hoc local preview; no clean-machine/signing/release acceptance"), success=True)
    (build.output / "package.json").write_text(json.dumps(build.report, indent=2) + "\n")


def publish_pmx_preview(build):
    projects = {
        "pmx-mesh": ("X/Feasibility/PmxMesh/PmxMesh.csproj", []),
        "pmx-graph": ("X/Feasibility/Pmx/NrbfInventory.csproj", ["-p:UseOfficialNrbf=true"]),
        "pmx-deck": ("X/Feasibility/PmxDeck/PmxDeck.csproj", []),
    }
    for name, (project, properties) in projects.items():
        build.run(["dotnet", "publish", project, "-c", "Release", "-r", build.target_id,
                   "--self-contained", "true", f"-p:RuntimeFrameworkVersion={build.catalog['runtimeFrameworkVersion']}",
                   f"-p:NativePreviewLockRoot={build.output / 'locks' / name}",
                   "--disable-build-servers", "-m:1", "--source", ROOT / "X/Analysis/artifacts/offline-feed",
                   "--source", "https://api.nuget.org/v3/index.json", *properties,
                   "-o", build.output / "hosts" / name, "-v:quiet"], "publish-" + name + ".log")
    tools = build.output / "pmx-tools"
    tools.mkdir()
    for name in ("inspect-pmx.py", "inspect-static-project.py", "reconstruct-static-deck.py", "write-controlled-edit.py", "inspect-cad-project.py", "write-cad-edit.py", "write-cad-properties.py"):
        shutil.copy2(ROOT / "X/Feasibility/Pmx" / name, tools / name)
    build.report["hostFiles"] = file_hashes(build.output / "hosts")

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["plan", "build", "package"])
    parser.add_argument("--target", choices=list(catalog()["targets"]), required=True)
    parser.add_argument("--component", choices=["hosts", "solver"], default="hosts")
    parser.add_argument("--format", choices=["app", "dmg", "tar.gz"])
    parser.add_argument("--solver-build", type=Path, help="Explicit verified native solver build for desktop jobs")
    parser.add_argument("--pmx-preview", action="store_true", help="Bundle the checked static PMX desktop editor")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--jobs", type=int, default=6)
    args = parser.parse_args(argv)
    target = catalog()["targets"][args.target]
    adapter = target["desktopPackageAdapter"]
    if args.pmx_preview and (args.action != "package" or adapter is None):
        parser.error("--pmx-preview requires a supported desktop package")
    if args.action == "plan":
        print(json.dumps({"target": args.target, "data": target, "matchingNativeHost": native(target),
            "managedCrossPublish": True, "nativeSolverRecipe": target["solverAdapter"] is not None,
            "desktopPackageRecipe": target["desktopPackageAdapter"], "executionVerified": False}, indent=2))
        return 0
    if not args.output:
        parser.error("Build/package requires a new --output directory")
    build = None
    try:
        if args.action == "package" or args.component == "solver":
            require_native(target)
            field = "desktopPackageAdapter" if args.action == "package" else "solverAdapter"
            if target[field] is None:
                raise ValueError("Target recipe remains pending: " + field)
        if args.action == "package":
            args.format = args.format or ("tar.gz" if adapter == "linux" else "app")
            if adapter == "linux" and (args.format != "tar.gz" or not args.solver_build):
                raise ValueError("Linux preview requires tar.gz and an explicit --solver-build")
            if adapter == "macos" and (args.format == "tar.gz" or (args.format == "dmg" and not args.solver_build)):
                raise ValueError("macOS preview requires app or dmg; dmg needs an explicit --solver-build")
        build = Build(args.target, args.output)
        build.identity()
        if args.action == "package":
            package_preview(build, args.solver_build, args.format, args.pmx_preview)
        elif args.component == "hosts":
            publish_hosts(build)
        else:
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
    print(json.dumps({k: build.report.get(k) for k in ["success", "target", "kind", "app", "elapsedSeconds", "error"]}
                     | ({"archive": build.report["archive"]} if "archive" in build.report else {})))
    return 0 if build.report["success"] else 1

if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Extract the native preview and verify its actual Qt/VTK and solver workflows."""
import argparse
import json
import os
from pathlib import Path
import platform
from runpy import run_path
import subprocess
import tarfile

from build import ROOT, catalog, file_hashes, require_native, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pmx-fixture", type=Path, help="Retained task 0045 shape-reference.pmx")
    parser.add_argument("--pmx-reference-frd", type=Path, help="Task 0049 official-export solve reference")
    args = parser.parse_args()
    if bool(args.pmx_fixture) != bool(args.pmx_reference_frd):
        parser.error("Supply both the PMX fixture and the official-export reference FRD")
    package, out = args.package.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {"success": False, "commands": [], "architecture": platform.machine(),
              "distribution": platform.freedesktop_os_release()["PRETTY_NAME"],
              "scope": "Extracted archive under the supplied Linux display; no distro or release acceptance"}

    env = dict(os.environ, PATH="/usr/bin:/bin", DOTNET_ROOT="/nonexistent-external-dotnet",
               QT_QPA_PLATFORM="xcb", XDG_CONFIG_HOME=str(out / "config"), XDG_DATA_HOME=str(out / "data"),
               XDG_CACHE_HOME=str(out / "cache"))
    for name in ("PYTHONHOME", "PYTHONPATH", "LD_LIBRARY_PATH", "LD_LIBRARY_PATH_ORIG", "LD_PRELOAD", "QT_PLUGIN_PATH"):
        env.pop(name, None)

    def run(command, name, timeout=180):
        command = list(map(str, command))
        done = subprocess.run(command, capture_output=True, env=env, cwd=out, timeout=timeout)
        (out / (name + ".stdout")).write_bytes(done.stdout)
        (out / (name + ".stderr")).write_bytes(done.stderr)
        report["commands"].append({"arguments": command, "exitCode": done.returncode})
        if done.returncode:
            raise ValueError(f"{name} failed: {done.stderr.decode(errors='replace')[-1500:]}")
        return done.stdout

    try:
        manifest = json.loads((package / "package.json").read_text())
        target = manifest["target"]
        require_native(catalog()["targets"][target])
        if manifest["success"] is not True or not target.startswith("linux-"):
            raise ValueError("Successful Linux package manifest required")
        archive = package / "dist" / f"PrePoMax-X-Preview-{target}.tar.gz"
        report["archiveSha256"] = sha(archive)
        report["packageManifestSha256"] = sha(package / "package.json")
        if report["archiveSha256"] != manifest["archive"]["sha256"]:
            raise ValueError("Archive changed after packaging")
        installed = out / "Installed preview" / "PrePoMax-X-Preview"
        with tarfile.open(archive, "r:gz") as payload:
            payload.extractall(installed.parent, filter="data")
        hashes = file_hashes(installed)
        links = {p.relative_to(installed).as_posix(): os.readlink(p) for p in installed.rglob("*") if p.is_symlink()}
        if hashes != manifest["fileHashes"] or links != manifest["symlinkTargets"]:
            raise ValueError("Extracted files or links differ from package manifest")
        report.update(target=target, appFiles=len(hashes), appLinks=len(links))
        executable = installed / "PrePoMax-X-Preview"
        gui_path = out / "desktop-workflow.json"
        run([executable, "--run-example", "--jobs-root", out / "Job workspace",
             "--self-test", gui_path, "--screenshot", out / "desktop-workflow.png"], "desktop")
        gui = json.loads(gui_path.read_text())
        job = gui["desktopJob"]
        report.update(guiChecks=gui["checks"], renderer=gui["renderer"],
                      qtVersion=gui["qtVersion"], vtkVersion=gui["vtkVersion"])
        if not gui["success"] or gui["target"] != target or not job["outcome"]["solverExecuted"]:
            raise ValueError("No successful native desktop solve")
        reference = run_path(str(ROOT / "X/Feasibility/Solver/run-reference.py"))
        data = reference["parse_dat"]((Path(job["directory"]) / "analysis.dat").read_text())
        checks = reference["analytical_checks"](data)
        data["displacements"][0][1] += 0.01
        rejected = not all(c["passed"] for c in reference["analytical_checks"](data))
        report.update(analyticalChecks=checks, alteredDisplacementRejected=rejected, nativeSolverExecuted=True)
        if not all(c["passed"] for c in checks) or not rejected:
            raise ValueError("Analytical checks or displacement negative control failed")

        if args.pmx_fixture:
            pmx_out = out / "PMX workflow"
            baseline = json.loads((ROOT / ".project/reports/static-pmx-native-solve-verification.json").read_text())
            expected = baseline["pmxByViewport"]["frame-bridge"]
            if (sha(args.pmx_fixture) != expected["write"]["inputSha256"] or
                    sha(args.pmx_reference_frd) != baseline["originalReference"]["frdSha256"]):
                raise ValueError("PMX fixture or FRD reference differs from task 0049")
            run([executable, "--pmx-probe", args.pmx_fixture.resolve(), pmx_out], "pmx")
            pmx = json.loads((pmx_out / "verification.json").read_text())
            if not pmx["success"] or not all(c["passed"] for c in pmx["checks"]):
                raise ValueError("Desktop PMX reopen and solve failed")
            if (sha(pmx_out / "edited.pmx") != expected["write"]["outputSha256"] or
                    pmx["job"]["deckSha256"] != expected["job"]["deckSha256"]):
                raise ValueError("Saved PMX or executed deck differs from the checked task 0049 workflow")
            frd, = (pmx_out / "jobs").glob("*/solve/analysis.frd")
            reader = installed / "_internal/hosts/results/PrePoMaxX.InspectResults"
            observed = json.loads(run([reader, "inspect-frd", frd], "pmx-fields"))
            original = json.loads(run([reader, "inspect-frd", args.pmx_reference_frd.resolve()], "reference-fields"))
            keys = ("nodes", "elements", "nodeIdsInValueOrder", "fields")
            if any(observed[key] != original[key] for key in keys):
                raise ValueError("Decoded Linux PMX results differ from the task 0049 official-export solve")
            report.update(pmx=pmx, pmxReferenceFrdSha256=sha(args.pmx_reference_frd), pmxDecodedResultsMatch=True)
        report["success"] = True
    except (OSError, ValueError, KeyError, subprocess.SubprocessError, tarfile.TarError) as error:
        report["error"] = str(error)
    (out / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("success", "target", "archiveSha256", "error") if k in report}))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

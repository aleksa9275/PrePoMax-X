#!/usr/bin/env python3
"""Install, run and purge the preview in a disposable Ubuntu test environment."""
import argparse
import json
import os
from pathlib import Path
import platform
import pwd
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from build import ROOT, file_hashes, sha
from linux_deb import APP, DESKTOP, LAUNCHER, PACKAGE


def lifecycle(args, out, report):
    release = platform.freedesktop_os_release()
    if os.geteuid() != 0 or (release.get("ID"), release.get("VERSION_ID")) != ("ubuntu", "24.04"):
        raise ValueError("Run as root inside a disposable Ubuntu 24.04 environment")
    report["distribution"] = release["PRETTY_NAME"]
    if subprocess.run(["dpkg-query", "-W", PACKAGE], capture_output=True).returncode == 0:
        raise ValueError("The preview package already has state on this machine")
    manifest = json.loads((args.deb.parent / "deb.json").read_text())
    report["debSha256"] = sha(args.deb)
    if (manifest["success"] is not True or report["debSha256"] != manifest["deb"]["sha256"] or
            manifest["packageManifestSha256"] != sha(args.package / "package.json")):
        raise ValueError("Installer or source package manifest does not match its build receipt")
    control = subprocess.check_output(["dpkg-deb", "-f", args.deb, "Package", "Version", "Architecture"], text=True)
    architecture = subprocess.check_output(["dpkg", "--print-architecture"], text=True).strip()
    fields = dict(line.split(": ", 1) for line in control.splitlines())
    if fields != {"Package": PACKAGE, "Version": manifest["version"], "Architecture": architecture}:
        raise ValueError("Installer metadata differs from the preview or native target")
    report.update(package=fields, archiveSha256=manifest["archiveSha256"])

    def run(command, name):
        with (out / (name + ".log")).open("w") as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)

    account = pwd.getpwnam("nobody")
    with TemporaryDirectory(prefix="prepomaxx-install-") as scratch:
        Path(scratch).chmod(0o755)
        home = Path(scratch) / "Preview user"
        home.mkdir(mode=0o700)
        os.chown(home, account.pw_uid, account.pw_gid)
        fixture = args.pmx_fixture or ROOT / "X/Analysis/StaticDeck/cube-mesh.inp"
        model = home / ("User model" + fixture.suffix)
        shutil.copyfile(fixture, model)
        os.chown(model, account.pw_uid, account.pw_gid)
        report["userModelSha256"] = sha(model)
        user_report = home / "workflow"
        install = ["apt-get", "install", "-y", "--no-install-recommends", args.deb]
        try:
            run(install, "apt-install")
            paths = (APP, LAUNCHER, DESKTOP, Path("/usr/share/doc") / PACKAGE)
            if any(path.stat().st_uid != 0 for path in paths) or not os.access(LAUNCHER, os.X_OK):
                raise ValueError("Installed package files must be root owned with an executable launcher")
            if f"Exec={LAUNCHER} %f" not in DESKTOP.read_text().splitlines():
                raise ValueError("Desktop menu entry does not use the installed launcher")
            run(["desktop-file-validate", DESKTOP], "desktop-entry")
            pmx = ["--pmx-fixture", model, "--pmx-reference-frd", args.pmx_reference_frd] if args.pmx_fixture else []
            run(["runuser", "-u", account.pw_name, "--", "env", f"HOME={home}", "LIBGL_ALWAYS_SOFTWARE=1",
                 "xvfb-run", "-a", "-s", "-screen 0 1400x1000x24", sys.executable,
                 ROOT / "X/Build/verify-linux-preview.py", "--installed", "--package", args.package,
                 "--output", user_report, *pmx], "user-workflow")
            verification = json.loads((user_report / "verification.json").read_text())
            gui = json.loads((user_report / "desktop-workflow.json").read_text())
            job = Path(gui["desktopJob"]["directory"])
            if (verification["success"] is not True or verification["uid"] != account.pw_uid or
                    not job.is_relative_to(user_report / "data") or not (job / "analysis.frd").is_file()):
                raise ValueError("Installed preview did not produce an ordinary user's job in XDG data")
            before = file_hashes(home)
            if before[model.name] != report["userModelSha256"]:
                raise ValueError("Launching the preview changed the user's project")
            report.update(workflow=verification, userFilesChecked=len(before), userJobInXdgData=True)
            for action in ("remove", "purge"):
                if action == "purge":
                    # With no configuration files, removal forgets a local-only package.
                    # Reinstall so APT exercises purge on an installed copy.
                    run(install, "apt-reinstall")
                    if not APP.is_dir() or file_hashes(home) != before:
                        raise ValueError("APT reinstall did not restore the app or preserve user files")
                    report["reinstall"] = {"packageFilesRestored": True, "userFilesPreserved": True}
                run(["apt-get", action, "-y", PACKAGE], "apt-" + action)
                if any(path.exists() or path.is_symlink() for path in paths):
                    raise ValueError(f"APT {action} left package files behind")
                if file_hashes(home) != before:
                    raise ValueError(f"APT {action} changed files in the user's home")
                report[action] = {"packageFilesGone": True, "userFilesPreserved": True}
            if subprocess.run(["dpkg-query", "-W", PACKAGE], capture_output=True).returncode == 0:
                raise ValueError("APT purge left package state behind")
        finally:
            shutil.copytree(home, out / "User evidence", symlinks=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deb", type=lambda path: Path(path).resolve(), required=True)
    parser.add_argument("--package", type=lambda path: Path(path).resolve(), required=True)
    parser.add_argument("--output", type=lambda path: Path(path).resolve(), required=True)
    parser.add_argument("--pmx-fixture", type=lambda path: Path(path).resolve())
    parser.add_argument("--pmx-reference-frd", type=lambda path: Path(path).resolve())
    args = parser.parse_args()
    if bool(args.pmx_fixture) != bool(args.pmx_reference_frd):
        parser.error("Supply both the PMX fixture and the official-export reference FRD")
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"success": False, "scope": "Disposable Ubuntu environment with Xvfb/Mesa"}
    try:
        lifecycle(args, args.output, report)
        report["success"] = True
    except (OSError, KeyError, ValueError, subprocess.SubprocessError) as error:
        report["error"] = str(error)
    (args.output / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("success", "package", "debSha256", "error") if k in report}))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

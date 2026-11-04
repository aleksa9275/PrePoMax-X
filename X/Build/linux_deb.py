#!/usr/bin/env python3
"""Wrap a checked Linux desktop archive for Ubuntu 24.04 APT installation."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess
import tarfile
from tempfile import TemporaryDirectory

from build import sha
from platforms.linux import checked_archive, verify_payload

PACKAGE = "prepomaxx-preview"
APP = Path("/usr/lib") / PACKAGE
LAUNCHER = Path("/usr/bin") / PACKAGE
DESKTOP = Path("/usr/share/applications") / f"org.prepomaxx.preview.desktop"
ARCHITECTURES = {"linux-x64": "amd64", "linux-arm64": "arm64"}

# Ubuntu 24.04 runtime. The archived payload supplies Python, Qt, VTK, .NET and CalculiX.
DEPENDENCIES = (
    "libc6 (>= 2.39)", "libstdc++6", "libicu74", "libssl3t64", "libgssapi-krb5-2", "zlib1g",
    "libgl1", "libegl1", "libgl1-mesa-dri", "libxrender1", "libdbus-1-3", "libfontconfig1",
    "fonts-dejavu-core", "libglib2.0-0t64", "libxkbcommon-x11-0", "libxcb-cursor0",
    "libxcb-icccm4", "libxcb-image0", "libxcb-keysyms1", "libxcb-render-util0",
    "libxcb-shape0", "libxcb-xinerama0", "libxcb-xinput0", "libsm6",
)


def write_file(stage, location, contents, mode=0o644):
    path = stage / location.relative_to("/")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents)
    path.chmod(mode)


def wrap(package, output, report):
    manifest, archive = checked_archive(package)
    arch = ARCHITECTURES[manifest["target"]]
    head = manifest["repository"]["head"]
    if not re.fullmatch(r"[0-9a-f]{40}", head) or manifest["buildLibc"] != "glibc 2.39":
        raise ValueError("Expected a pinned Ubuntu 24.04 preview build")
    timestamp = datetime.fromisoformat(manifest["recordedAtUtc"]).strftime("%Y%m%d%H%M%S")
    version = f"0.0.0~preview+{timestamp}.git{head[:12]}"
    name = f"{PACKAGE}_{version}_{arch}.deb"
    report.update(package=PACKAGE, version=version, architecture=arch, sourceCommit=head,
                  target=manifest["target"], archiveSha256=manifest["archive"]["sha256"],
                  packageManifestSha256=sha(package / "package.json"), wrapperSha256=sha(Path(__file__)),
                  dependencies=DEPENDENCIES)
    with TemporaryDirectory(prefix="prepomaxx-deb-") as work:
        staging = Path(work) / "package"
        lib = staging / APP.parent.relative_to("/")
        lib.mkdir(parents=True)
        extracted = lib / "PrePoMax-X-Preview"
        with tarfile.open(archive, "r:gz") as payload:
            payload.extractall(lib, filter="data")
        if set(lib.iterdir()) != {extracted} or extracted.is_symlink() or not extracted.is_dir():
            raise ValueError("Expected a single preview application directory")
        report.update(verify_payload(extracted, manifest))
        extracted.rename(staging / APP.relative_to("/"))
        write_file(staging, LAUNCHER, f'#!/bin/sh\nexec {APP}/PrePoMax-X-Preview "$@"\n', 0o755)
        write_file(staging, DESKTOP,
                   "[Desktop Entry]\nType=Application\nName=PrePoMax-X Preview\n"
                   f"Exec={LAUNCHER} %f\nTryExec={LAUNCHER}\nTerminal=false\nCategories=Science;Engineering;\n")
        write_file(staging, Path("/usr/share/doc") / PACKAGE / "preview-build.json",
                   json.dumps({key: report[key] for key in ("version", "sourceCommit", "archiveSha256",
                                                             "packageManifestSha256")}, indent=2) + "\n")
        installed_kib = subprocess.check_output(["du", "-sk", staging], text=True).split()[0]
        write_file(staging, Path("/DEBIAN/control"),
                   f"Package: {PACKAGE}\nVersion: {version}\nArchitecture: {arch}\n"
                   "Maintainer: PrePoMax-X Preview <preview@prepomaxx.invalid>\n"
                   "Section: science\nPriority: optional\n"
                   f"Installed-Size: {installed_kib}\nDepends: {', '.join(DEPENDENCIES)}\n"
                   "Description: PrePoMax-X internal static analysis desktop preview\n"
                   " This preview contains the checked static workflow and native CalculiX.\n")
        # Stage the output alongside its final path so publishing the file is atomic.
        partial = output / (name + ".partial")
        try:
            with (output / "dpkg-deb.log").open("w") as log:
                subprocess.run(["dpkg-deb", "--root-owner-group", "-Zgzip", "-z3", "--build", staging, partial],
                               stdout=log, stderr=subprocess.STDOUT, check=True)
            report["deb"] = {"name": name, "sha256": sha(partial), "bytes": partial.stat().st_size}
            partial.rename(output / name)
        finally:
            partial.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True, help="Existing successful Linux archive build")
    parser.add_argument("--output", type=Path, required=True, help="New installer output directory")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {"success": False, "scope": "Internal Ubuntu 24.04 preview"}
    try:
        wrap(args.package.resolve(), output, report)
        report["success"] = True
    except (OSError, ValueError, KeyError, subprocess.SubprocessError, tarfile.TarError) as error:
        report["error"] = str(error)
    (output / "deb.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Relocatable native Linux desktop preview (same desktop and engineering hosts)."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile


def checked_archive(package):
    from build import catalog, require_native, sha
    manifest = json.loads((package / "package.json").read_text())
    target = manifest["target"]
    if manifest["success"] is not True or target not in ("linux-x64", "linux-arm64"):
        raise ValueError("Successful Linux package manifest required")
    require_native(catalog()["targets"][target])
    archive = package / "dist" / f"PrePoMax-X-Preview-{target}.tar.gz"
    if sha(archive) != manifest["archive"]["sha256"]:
        raise ValueError("Archive changed after packaging")
    return manifest, archive


def verify_payload(app, manifest):
    from build import file_hashes
    hashes = file_hashes(app)
    links = {p.relative_to(app).as_posix(): os.readlink(p) for p in app.rglob("*") if p.is_symlink()}
    if hashes != manifest["fileHashes"] or links != manifest["symlinkTargets"]:
        raise ValueError("Preview files or links differ from package manifest")
    return {"appFiles": len(hashes), "appLinks": len(links)}


def elf_links(path, library_dir=None):
    env = dict(os.environ, LC_ALL="C")
    env.pop("LD_LIBRARY_PATH", None)
    if library_dir is not None:
        env["LD_LIBRARY_PATH"] = str(library_dir)
    links = {}
    for line in subprocess.check_output(["ldd", path], env=env, text=True).splitlines():
        if "=>" in line:
            name, resolved = (part.strip() for part in line.split("=>", 1))
            resolved = Path(resolved.split(" (", 1)[0])
            if not resolved.is_absolute() or not resolved.is_file() or Path(name).name != name:
                raise ValueError("Unresolved or non-relocatable solver dependency: " + line.strip())
            links[name] = resolved
    return links


def bundle_solver(build, source, destination):
    from build import file_hashes, sha
    report = json.loads((source / "build-report.json").read_text())
    registry = json.loads((source / "build-registry.json").read_text())
    if report.get("success") is not True or report.get("target") != build.target_id or len(registry["builds"]) != 1:
        raise ValueError("A successful native solver build for the package target is required")
    profile = registry["builds"][0]
    inputs = profile["externalFiles"]
    original = source / "bin/ccx"
    if (profile["os"] != "Linux" or profile["architecture"] != build.target["architecture"] or
            profile["version"] != "2.22" or profile["executable"] != "ccx" or
            profile["version"] != report["version"] or profile["backend"] != report["backend"] or
            profile["files"] != {"ccx": report["executableSha256"]} or inputs != report["externalRuntimes"]):
        raise ValueError("Solver registry does not match the native build report")
    if sha(original) != profile["files"]["ccx"]:
        raise ValueError("Native solver executable changed after build")
    for name, digest in inputs.items():
        path = Path(name)
        if not path.is_absolute() or sha(path) != digest:
            raise ValueError("Native solver runtime changed: " + name)

    # Keep the distro's loader/glibc together; relocate the compiler and BLAS runtimes.
    system = {"libc.so.6", "libm.so.6", "libmvec.so.1", "libpthread.so.0", "libdl.so.2",
              "librt.so.1", "libresolv.so.2", "libutil.so.1", "libanl.so.1"}
    source_links = elf_links(original)
    bundled = {}
    bin_dir = destination / "bin"
    bin_dir.mkdir(parents=True)
    shutil.copy2(original, bin_dir / "ccx")
    for name, path in source_links.items():
        if str(path) not in inputs:
            raise ValueError("Unpinned native solver dependency: " + str(path))
        if name not in system:
            shutil.copy2(path, bin_dir / name)
            bundled[name] = str(path)
    for path in sorted(bin_dir.iterdir()):
        build.run(["patchelf", "--set-rpath", "$ORIGIN", path])
    relocated = elf_links(bin_dir / "ccx")
    if (set(relocated) != set(source_links) or
            any(relocated[name].resolve() != (bin_dir / name).resolve() for name in bundled) or
            any(relocated[name] != source_links[name] for name in system & relocated.keys())):
        raise ValueError("Relocated ELF closure differs from the checked solver build")

    profile.update(id=build.target_id + "-2.22-spooles-local-preview", files=file_hashes(bin_dir),
                   scope="Relocated native static-solid preview; original backend unchanged")
    profile.pop("externalFiles")
    (destination / "build-registry.json").write_text(json.dumps(registry, indent=2) + "\n")
    provenance = {"originalBuildReportSha256": sha(source / "build-report.json"),
                  "originalExecutableSha256": report["executableSha256"],
                  "originalRegistrySha256": sha(source / "build-registry.json"),
                  "originalRuntimes": inputs, "bundledLibraries": bundled,
                  "relocatedFiles": profile["files"], "backend": profile["backend"],
                  "adapterSha256": sha(Path(__file__))}
    (destination / "relocation.json").write_text(json.dumps(provenance, indent=2) + "\n")
    build.report["solverRelocation"] = provenance


# Frozen PyInstaller code needs its own library path. Give the external C#
# processes the original one, as they also launch the native solver.
NATIVE_LAUNCHER = """#!/bin/sh
if [ "${LD_LIBRARY_PATH_ORIG+x}" ]; then
    LD_LIBRARY_PATH=$LD_LIBRARY_PATH_ORIG
    export LD_LIBRARY_PATH
else
    unset LD_LIBRARY_PATH
fi
exec "$0.elf" "$@"
"""


def package(build, root, solver_build):
    from build import HOSTS
    if sys.version_info[:2] != (3, 12):
        raise ValueError("Linux desktop preview requires the pinned CPython 3.12 environment")
    output = build.output
    example_dir = output / "examples"
    example_dir.mkdir()
    for name in ("cube-mesh.inp", "cube-analysis.json", "mixed-solids.inp", "mixed-solids.json", "mixed-pyramids.inp", "mixed-pyramids.json"):
        shutil.copy2(root / "X/Analysis/StaticDeck" / name, example_dir / name)
    pmx = (["--add-data", f"{output / 'pmx-tools'}:pmx-tools", "--hidden-import", "decimal"]
           if (output / "pmx-tools").is_dir() else [])
    build.report["python"] = sys.version
    build.report["pythonPackages"] = json.loads(build.run([sys.executable, "-m", "pip", "list", "--format=json"]))
    build.report["buildLibc"] = os.confstr("CS_GNU_LIBC_VERSION")
    build.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--onedir",
               "--name", "PrePoMax-X-Preview", "--collect-all", "vtkmodules",
               "--add-data", f"{output / 'source-identity.json'}:.",
               "--add-data", f"{root / 'X/Build/targets.json'}:.",
               "--add-data", f"{example_dir}:examples", *pmx,
               "--distpath", output / "dist", "--workpath", output / "build", "--specpath", output,
               root / "X/Desktop/viewport.py"], "freeze.log")
    app = output / "dist/PrePoMax-X-Preview"
    internal = app / "_internal"
    xcb = internal / "PyQt6/Qt6/plugins/platforms/libqxcb.so"
    if not xcb.is_file():
        raise ValueError("PyInstaller did not collect the Qt X11 plugin; check the Linux build dependencies")
    elf_links(xcb, library_dir=internal)
    shutil.copytree(output / "hosts", internal / "hosts")
    executables = {folder: exe for folder, (_, exe) in HOSTS.items()}
    if pmx:
        executables.update({"pmx-mesh": "PmxMesh", "pmx-graph": "PrePoMaxX.NrbfInventory", "pmx-deck": "PmxDeck"})
    for folder, executable in executables.items():
        launcher = internal / "hosts" / folder / executable
        launcher.rename(launcher.with_suffix(launcher.suffix + ".elf"))
        launcher.write_text(NATIVE_LAUNCHER)
        launcher.chmod(0o755)
    bundle_solver(build, solver_build.resolve(), internal / "native-solver")
    shutil.copy2(root / "X/Desktop/INSTALL-linux.md", app / "READ-ME-FIRST.md")
    shutil.copy2(root / "LICENSE", app / "COPYING-PrePoMax-X.txt")
    return app


def archive(build, app):
    from build import sha
    target = app.with_name("PrePoMax-X-Preview-" + build.target_id + ".tar.gz")
    with tarfile.open(target, "x:gz", compresslevel=3) as payload:
        payload.add(app, arcname=app.name)
    build.report["archive"] = {"path": str(target), "sha256": sha(target), "bytes": target.stat().st_size}

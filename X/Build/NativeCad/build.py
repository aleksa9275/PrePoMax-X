#!/usr/bin/env python3
"""Build the original PrePoMax Netgen/OCCT tool in an isolated native workspace."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCES = REPO / "ThirdParty/Sources/NetgenMesher/c5ecb0ba"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run(args, log):
    with log.open("ab") as output:
        output.write(("\n" + repr([str(x) for x in args]) + "\n").encode())
        output.flush()
        subprocess.run([str(x) for x in args], stdout=output,
                       stderr=subprocess.STDOUT, check=True)


def runtime_closure(runtime, occt):
    """Copy the OCCT toolkits actually referenced by the executable/library graph."""
    queue = [runtime / "bin/NetGenMesher"]
    queue.extend((runtime / "lib").glob("*nglib*"))
    seen = set()
    while queue:
        binary = queue.pop()
        if binary in seen:
            continue
        seen.add(binary)
        if platform.system() == "Darwin":
            output = subprocess.check_output(["otool", "-L", str(binary)], text=True)
            names = [line.strip().split(" (", 1)[0].split("/")[-1]
                     for line in output.splitlines()[1:]]
        else:
            output = subprocess.check_output(["readelf", "-d", str(binary)], text=True)
            names = [line.split("[", 1)[1].split("]", 1)[0]
                     for line in output.splitlines() if "(NEEDED)" in line]
        for name in names:
            if not name.startswith("libTK"):
                continue
            target = runtime / "lib" / name
            if not target.exists():
                shutil.copy2(occt / "lib" / name, target)
                queue.append(target)
    return [{"path": p.relative_to(runtime).as_posix(), "sha256": sha(p)}
            for folder in ("bin", "lib") for p in sorted((runtime / folder).rglob("*")) if p.is_file()]


def original_sources():
    manifest = json.loads((SOURCES / "source-manifest.json").read_text())
    expected = set()
    for row in manifest["files"]:
        path = SOURCES / row["path"]
        if path.is_symlink() or not path.is_file() or sha(path) != row["sha256"]:
            raise ValueError("Original source changed: " + str(path))
        expected.add(path.relative_to(SOURCES / "src").as_posix())
    actual = {p.relative_to(SOURCES / "src").as_posix()
              for p in (SOURCES / "src").rglob("*") if p.is_file()}
    if actual != expected:
        raise ValueError("Original source inventory changed")
    return manifest


def extract_occt(archive, target, digest):
    if sha(archive) != digest:
        raise ValueError("OCCT source archive hash mismatch")
    # Always restore the verified original bytes before configuring an incremental build.
    with tarfile.open(archive) as source:
        members = source.getmembers()
        for member in members:
            relative = Path(*Path(member.name).parts[1:])
            if relative.is_absolute() or ".." in relative.parts or member.issym() or member.islnk():
                raise ValueError("Unsafe source archive member")
            if member.isfile():
                destination = target / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                data = source.extractfile(member).read()
                # Preserve mtimes of unchanged files for incremental compilation.
                if not destination.is_file() or destination.read_bytes() != data:
                    destination.write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--occt-archive", type=Path)
    parser.add_argument("--occt-prefix", type=Path,
                        help="Reuse an OCCT installation built by this recipe")
    parser.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 1) * 3 // 4))
    args = parser.parse_args()
    if platform.system() not in ("Darwin", "Linux") or args.jobs < 1:
        parser.error("Use a native Mac/Linux host and a positive worker count")
    manifest = original_sources()
    output = args.output.resolve()
    if output == REPO or REPO.is_relative_to(output) or output.is_relative_to(SOURCES):
        parser.error("Choose a separate build output directory")
    output.mkdir(parents=True, exist_ok=True)
    log = output / "build.log"
    lock = json.loads((HERE / "occt-lock.json").read_text())
    occt = args.occt_prefix.resolve() if args.occt_prefix else output / "occt-install"
    if args.occt_prefix:
        receipt = json.loads((occt / "prepomaxx-source.json").read_text())
        if receipt != lock:
            raise ValueError("Reused OCCT installation has another source identity")
    else:
        archive = args.occt_archive.resolve() if args.occt_archive else output / "occt-source.tar.gz"
        if not archive.exists():
            if args.occt_archive:
                raise FileNotFoundError(archive)
            with urllib.request.urlopen(lock["url"], timeout=120) as response, archive.open("wb") as stream:
                shutil.copyfileobj(response, stream)
        extract_occt(archive, output / "occt-source", lock["sha256"])
        run(["cmake", "-S", output / "occt-source", "-B", output / "occt-build",
             "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_INSTALL_PREFIX=" + str(occt),
             "-DBUILD_MODULE_Visualization=OFF", "-DBUILD_MODULE_Draw=OFF",
             "-DBUILD_MODULE_ApplicationFramework=ON", "-DBUILD_DOC_Overview=OFF",
             "-DUSE_TK=OFF", "-DUSE_FREETYPE=OFF", "-DUSE_OPENGL=OFF", "-DUSE_XLIB=OFF",
             "-DUSE_TBB=OFF", "-DUSE_FFMPEG=OFF", "-DUSE_FREEIMAGE=OFF",
             "-DCMAKE_INSTALL_RPATH=" + ("@loader_path" if platform.system() == "Darwin" else "$ORIGIN")], log)
        run(["cmake", "--build", output / "occt-build", "--parallel", args.jobs], log)
        run(["cmake", "--install", output / "occt-build"], log)
        (occt / "prepomaxx-source.json").write_text(json.dumps(lock, indent=2) + "\n")
    work = output / "source"
    # Patch only a disposable copy; the committed corresponding source stays unchanged.
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(SOURCES / "src", work)
    patches = sorted((SOURCES / "patches").glob("*.patch"))
    for patch in patches:
        with patch.open("rb") as stream, log.open("ab") as log_stream:
            subprocess.run(["patch", "-p1", "--batch"], cwd=work, stdin=stream,
                           stdout=log_stream, stderr=subprocess.STDOUT, check=True)
    root = work / "Netgen v5.3.1 port to OCCT 8.0.1/Netgen-master/netgen-5.3.1"
    mesher = work / "NetGenMesher 8.0.1/NetGenLibTest"
    project = root / "windows/nglib.vcxproj"
    ns = {"m": "http://schemas.microsoft.com/developer/msbuild/2003"}
    sources = [(project.parent / item.attrib["Include"].replace("\\", "/")).resolve()
               for item in ET.parse(project).findall(".//m:ClCompile", ns)
               if "Include" in item.attrib]
    build = output / "build"
    build.mkdir(exist_ok=True)
    def cmake_string(value):
        return str(value).replace("\\", "/").replace('"', '\\"').replace(";", "\\;").replace("$", "\\$")
    (build / "sources.cmake").write_text(
        'set(NETGEN_ROOT "' + cmake_string(root) + '")\n'
        'set(MESHER_ROOT "' + cmake_string(mesher) + '")\nset(NETGEN_SOURCES\n' +
        "".join('  "' + cmake_string(p) + '"\n' for p in sources) + ")\n")
    run(["cmake", "-S", HERE, "-B", build, "-DCMAKE_BUILD_TYPE=Release",
         "-DCMAKE_PREFIX_PATH=" + str(occt), "-DCMAKE_INSTALL_PREFIX=" + str(output / "runtime")], log)
    run(["cmake", "--build", build, "--parallel", args.jobs], log)
    if (output / "runtime").exists():
        shutil.rmtree(output / "runtime")
    run(["cmake", "--install", build], log)
    runtime = output / "runtime"
    runtime_files = runtime_closure(runtime, occt)
    licenses = runtime / "licenses"
    licenses.mkdir(exist_ok=True)
    shutil.copy2(SOURCES / "src/LICENSE", licenses / "Netgen-LGPL-2.1.txt")
    shutil.copy2(REPO / "LICENSE", licenses / "NetGenMesher-GPL-3.0.txt")
    for license in (REPO / "Licenses/netgen").glob("*"):
        if license.is_file():
            shutil.copy2(license, licenses / license.name)
    receipt = {
        "schemaVersion": 1, "nativeHost": {"system": platform.system(), "machine": platform.machine()},
        "netgenRevision": manifest["version"], "sourceManifestSha256": sha(SOURCES / "source-manifest.json"),
        "occt": lock, "occtPrefix": str(occt), "sourcesFromOriginalProject": len(sources),
        "patches": [{"path": p.name, "sha256": sha(p)} for p in patches],
        "cmakeSha256": sha(HERE / "CMakeLists.txt"),
        "builderSha256": sha(HERE / "build.py"),
        "compiler": subprocess.check_output(["c++", "--version"], text=True).splitlines()[0],
        "occtCmakeCacheSha256": sha(occt.parent / "occt-build/CMakeCache.txt")
            if (occt.parent / "occt-build/CMakeCache.txt").is_file() else None,
        "adapterFiles": [{"path": p.relative_to(HERE).as_posix(), "sha256": sha(p)}
                         for p in sorted((HERE / "compat").glob("*")) if p.is_file()],
        "runtimeFiles": runtime_files,
        "executableSha256": sha(output / "runtime/bin/NetGenMesher"),
        "releaseAccepted": False,
    }
    (output / "build-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    (runtime / "build-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()

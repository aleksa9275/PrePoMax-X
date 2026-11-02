#!/usr/bin/env python3
"""Build the pinned native CPU research solver; pristine sources are never edited."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cc", default="gcc-16")
    parser.add_argument("--fc", default="gfortran")
    parser.add_argument("--blas", type=Path, default=Path("/opt/homebrew/opt/openblas/lib/libopenblas.dylib"))
    parser.add_argument("--jobs", type=int, default=6)
    args = parser.parse_args()
    if platform.system() != "Darwin" or platform.machine().lower() != "arm64":
        parser.error("First reviewed recipe targets native macOS ARM64 only")
    if not 1 <= args.jobs <= 32:
        parser.error("jobs must be between 1 and 32")
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {"success": False, "kind": "native-calculix-cpu-research-build", "version": "2.22",
        "recordedAtUtc": datetime.now(timezone.utc).isoformat(), "os": platform.system(),
        "architecture": platform.machine(), "commands": [], "patches": [],
        "backend": "SPOOLES 2.2 serial; ARPACK-ng 3.9.1 int32 static; OpenBLAS LP64",
        "releaseReady": False, "numericalAcceptance": False}
    report["buildToolSha256"] = sha(Path(__file__))
    started = time.monotonic()
    env = dict(os.environ, ZERO_AR_DATE="1", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
    def run(command, cwd=ROOT):
        index = len(report["commands"])
        log = out / f"build-{index:02d}.log"
        before = time.monotonic()
        with log.open("w") as stream:
            result = subprocess.run(list(map(str, command)), cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT)
        report["commands"].append({"arguments": list(map(str, command)), "exitCode": result.returncode,
            "log": log.name, "elapsedSeconds": round(time.monotonic() - before, 3)})
        if result.returncode:
            raise RuntimeError(f"Build command failed; see {log}")
        return log.read_text()
    try:
        run(["python3", ROOT / "ThirdParty/Sources/verify-sources.py"])
        report["compilers"] = {name: subprocess.check_output([value, "--version"], text=True).splitlines()[0]
            for name, value in [("C", args.cc), ("Fortran", args.fc)]}
        report["sourceManifests"] = {name: sha(ROOT / "ThirdParty/Sources" / name / version / "source-manifest.json")
            for name, version in [("CalculiX", "2.22"), ("SPOOLES", "2.2"), ("ARPACK-ng", "3.9.1")]}
        sources = out / "work"
        sources.mkdir(exist_ok=True)
        spooles = sources / "spooles"
        ccx = sources / "ccx"
        shutil.copytree(ROOT / "ThirdParty/Sources/SPOOLES/2.2/src", spooles, dirs_exist_ok=True)
        shutil.copytree(ROOT / "ThirdParty/Sources/CalculiX/2.22/src", ccx, dirs_exist_ok=True)
        # This legacy recursive make does not propagate command-line overrides
        # on Apple's make. Configure only the disposable build copy.
        path = spooles / "Make.inc"
        text = path.read_text()
        for original, replacement in [("  CC = /usr/lang-4.0/bin/cc", f"  CC = {args.cc}"),
                ("  CFLAGS = $(OPTLEVEL)", "  CFLAGS = -O2 -std=gnu89"),
                ("  RANLIB = echo", "  RANLIB = ranlib")]:
            assert text.count(original) == 1
            text = text.replace(original, replacement)
        path.write_text(text)
        report["patches"].append({"path": "SPOOLES/Make.inc", "change": "Explicit native compiler, optimization, C dialect and archive indexer"})
        # The upstream installation guide identifies this nonexistent source filename.
        path = spooles / "Tree/src/makeGlobalLib"
        text = path.read_text()
        assert text.count("drawTree.c") == 1
        path.write_text(text.replace("drawTree.c", "draw.c"))
        report["patches"].append({"path": "SPOOLES/Tree/src/makeGlobalLib", "change": "drawTree.c -> draw.c (upstream README.INSTALL correction)"})
        path = spooles / "ETree/src/transform.c"
        text = path.read_text()
        count = text.count("IVinit(nfront, NULL)")
        assert count > 0
        path.write_text(text.replace("IVinit(nfront, NULL)", "IVinit(nfront, 0)"))
        report["patches"].append({"path": "SPOOLES/ETree/src/transform.c", "change": "integer zero instead of NULL for IVinit value", "occurrences": count})
        run(["make", "lib", f"CC={args.cc}", "CFLAGS=-O2 -std=gnu89", "RANLIB=ranlib"], spooles)
        arpack_build = sources / "arpack-build"
        run(["cmake", "-S", ROOT / "ThirdParty/Sources/ARPACK-ng/3.9.1/src", "-B", arpack_build,
            "-DCMAKE_BUILD_TYPE=Release", f"-DCMAKE_C_COMPILER={args.cc}", f"-DCMAKE_Fortran_COMPILER={args.fc}",
            "-DBUILD_SHARED_LIBS=OFF", "-DMPI=OFF", "-DINTERFACE64=OFF", "-DICB=OFF", "-DEXAMPLES=OFF", "-DTESTS=OFF",
            f"-DBLAS_LIBRARIES={args.blas}", f"-DLAPACK_LIBRARIES={args.blas}"])
        run(["cmake", "--build", arpack_build, "--parallel", args.jobs])
        arpack = next(arpack_build.rglob("libarpack.a"))
        flags = f'-O2 -fcommon -std=gnu89 -I{spooles} -DARCH=Linux -DSPOOLES -DARPACK -DMATRIXSTORAGE -DNETWORKOUT'
        # Retain original source lists. Avoid the original Makefile's local paths and
        # link-library prerequisites; compiler/ABI settings are explicit here.
        makefile = ccx / "Makefile.native"
        makefile.write_text(f'''include Makefile.inc
CC={args.cc}
FC={args.fc}
CFLAGS={flags}
FFLAGS=-O2 -fopenmp -fallow-argument-mismatch
OBJECTS=$(sort $(SCCXF:.f=.o) $(SCCXC:.c=.o))
.PHONY: all
all: ccx
%.o: %.c
\t$(CC) $(CFLAGS) -c $< -o $@
%.o: %.f
\t$(FC) $(FFLAGS) -c $< -o $@
ccx: ccx_2.22.o $(OBJECTS)
\t$(FC) -O2 -fopenmp -o $@ ccx_2.22.o $(OBJECTS) {spooles}/spooles.a {arpack} {args.blas} -lpthread -lm
''')
        report["generatedMakefileSha256"] = sha(makefile)
        report["legacyCompilerPolicy"] = "-fcommon retains pre-GCC-10 tentative-global behavior; sort deduplicates mafillmm.o from stale missing C entry"
        report["compileDatePolicy"] = "Original source banner retained; actual build time recorded here; byte reproducibility not asserted"
        run(["make", "-f", makefile.name, f"-j{args.jobs}", "all"], ccx)
        binary = out / "bin" / "ccx"
        binary.parent.mkdir(exist_ok=True)
        shutil.copy2(ccx / "ccx", binary)
        report["executableSha256"] = sha(binary)
        report["file"] = subprocess.check_output(["file", binary], text=True).strip()
        assert "arm64" in report["file"]
        runtime = {}
        pending = [binary]
        unresolved = []
        rpaths = []
        def expand(name, loader):
            return name.replace("@loader_path", str(loader.parent)).replace("@executable_path", str(binary.parent))
        while pending:
            file = pending.pop()
            lines = subprocess.check_output(["otool", "-l", file], text=True).splitlines()
            for i, line in enumerate(lines):
                if line.strip() == "cmd LC_RPATH":
                    for following in lines[i+1:i+4]:
                        if following.strip().startswith("path "):
                            rpaths.append(expand(following.strip()[5:].split(" (offset", 1)[0], file))
            for line in subprocess.check_output(["otool", "-L", file], text=True).splitlines()[1:]:
                name = line.strip().split(" (", 1)[0]
                if name.startswith(("/usr/lib/", "/System/")):
                    continue
                candidate = Path(expand(name, file))
                if name.startswith("@rpath/"):
                    candidates = [Path(directory) / name[7:] for directory in rpaths]
                    candidate = next((p for p in candidates if p.is_file()), candidate)
                if not candidate.is_file():
                    unresolved.append(name)
                    continue
                path = candidate.resolve()
                # Pin the load path too: Homebrew opt symlinks may be retargeted.
                if str(candidate) not in runtime:
                    runtime[str(candidate)] = sha(path)
                    pending.append(path)
        if unresolved:
            raise RuntimeError("Unresolved runtime paths: " + str(unresolved))
        report["externalRuntimes"] = runtime
        report["resolvedRpaths"] = list(dict.fromkeys(rpaths))
        profile = {"id": "macos-arm64-2.22-spooles-research", "os": "Darwin", "architecture": "Arm64",
            "version": "2.22", "executable": "ccx", "files": {"ccx": sha(binary)},
            "externalFiles": runtime, "backend": report["backend"], "sourceMatch": "Pinned core/SPOOLES/ARPACK sources and explicit native recipe; different from Windows backend build",
            "sourceManifest": "ThirdParty/Sources/CalculiX/2.22/source-manifest.json",
            "scope": "Research CPU profile; no production default or broad numerical/release acceptance"}
        (out / "build-registry.json").write_text(json.dumps({"schemaVersion": 1, "builds": [profile]}, indent=2) + "\n")
        report["success"] = True
    except (OSError, ValueError, RuntimeError, AssertionError, StopIteration, subprocess.SubprocessError) as error:
        report["error"] = str(error)
    report["elapsedSeconds"] = round(time.monotonic() - started, 3)
    (out / "build-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report.get(k) for k in ["success", "elapsedSeconds", "error", "executableSha256"]}))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

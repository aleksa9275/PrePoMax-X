#!/usr/bin/env python3
"""Build the pinned native CPU research solver; pristine sources are never edited."""
import argparse
import ctypes
import importlib.util
import sys
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
    parser.add_argument("--target", choices=["osx-arm64", "linux-x64", "linux-arm64"])
    parser.add_argument("--cc")
    parser.add_argument("--fc")
    parser.add_argument("--blas", type=Path)
    parser.add_argument("--jobs", type=int, default=6)
    parser.add_argument("--pastix", type=Path, help="prefix of X/Build/Pastix/build.py: the i8 build with PaStiX "
                        "(CalculiX's Makefile_i8), its OpenBLAS i8 for BLAS")
    args = parser.parse_args()
    catalog = json.loads((ROOT / "X/Build/targets.json").read_text())
    candidates = [rid for rid, data in catalog["targets"].items()
        if data["os"] == platform.system() and platform.machine().lower() in data["machines"]]
    target_id = args.target or (candidates[0] if len(candidates) == 1 else None)
    if target_id not in candidates or not catalog["targets"][target_id]["solverAdapter"]:
        parser.error("No native research solver recipe for this target/host; no cross-run or substitute selected")
    target = catalog["targets"][target_id]
    adapter_path = Path(__file__).parent / "platforms" / (target["solverAdapter"] + ".py")
    spec = importlib.util.spec_from_file_location("native_platform", adapter_path)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    try:
        defaults = adapter.defaults(args.blas)
        args.cc = args.cc or defaults["cc"]
        args.fc = args.fc or defaults["fc"]
        args.blas = (args.pastix.resolve() / "lib/libopenblas.a") if args.pastix else defaults["blas"].absolute()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.error(str(error))
    if not 1 <= args.jobs <= 32:
        parser.error("jobs must be between 1 and 32")
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {"success": False, "kind": "native-calculix-cpu-research-build", "version": "2.22",
        "recordedAtUtc": datetime.now(timezone.utc).isoformat(), "os": platform.system(),
        "architecture": platform.machine(), "target": target_id, "commands": [], "patches": [],
        "backend": ("PaStiX4CalculiX (PaRSEC, Scotch, hwloc) i8 static, multithreaded; SPOOLES 2.2; ARPACK-ng 3.9.1 i8 static; "
                    "OpenBLAS ILP64 static; external behaviours" if args.pastix else
                    "SPOOLES 2.2; ARPACK-ng 3.9.1 int32 static; OpenBLAS LP64; external behaviours"),
        "integers": "int64 (INTSIZE64, -fdefault-integer-8)" if args.pastix else "int32",
        "releaseReady": False, "numericalAcceptance": False}
    report["buildToolSha256"] = sha(Path(__file__))
    report["platformAdapterSha256"] = sha(adapter_path)
    report["targetCatalogSha256"] = sha(ROOT / "X/Build/targets.json")
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
        run([sys.executable, ROOT / "ThirdParty/Sources/verify-sources.py"])
        if args.pastix:
            receipt = json.loads((args.pastix.resolve().parent / "receipt.json").read_text())
            if receipt.get("integers") != "int64" or not args.blas.is_file():
                raise ValueError("--pastix needs the i8 prefix of X/Build/Pastix/build.py")
            report["pastixReceipt"] = receipt
            report["pastixReceiptSha256"] = sha(args.pastix.resolve().parent / "receipt.json")
        else:
            blas_library = ctypes.CDLL(str(args.blas))
            blas_library.openblas_get_config.restype = ctypes.c_char_p
            blas_config = blas_library.openblas_get_config().decode()
            if "OpenBLAS" not in blas_config or "USE64BITINT" in blas_config:
                raise ValueError("This recipe requires OpenBLAS LP64/int32")
            report["openblasConfig"] = blas_config
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
        # The multithreaded SPOOLES of CalculiX's Makefile_MT (USE_MT), as in the Windows build, on x86-64 only: its
        # threads hand data over through unsynchronized flags and list heads (ThreadSanitizer: 127 races in the MT
        # factorization and solve), which x86's ordered stores hide; on ARM64 eigenvalues come out wrong in 3 of 8 runs
        # (B022). ARM64 keeps the serial SPOOLES; PaStiX is the multithreaded direct solver there.
        spooles_mt = target["architecture"] == "X64"
        if spooles_mt:
            run(["make", "lib", f"CC={args.cc}", "CFLAGS=-O2 -std=gnu89", "RANLIB=ranlib"], spooles / "MT")
        report["spoolesThreads"] = "multithreaded (USE_MT)" if spooles_mt else "serial (B022: SPOOLES MT is not safe on ARM64)"
        arpack_build = sources / "arpack-build"
        run(["cmake", "-S", ROOT / "ThirdParty/Sources/ARPACK-ng/3.9.1/src", "-B", arpack_build,
            "-DCMAKE_BUILD_TYPE=Release", f"-DCMAKE_C_COMPILER={args.cc}", f"-DCMAKE_Fortran_COMPILER={args.fc}",
            "-DBUILD_SHARED_LIBS=OFF", "-DMPI=OFF", f"-DINTERFACE64={'ON' if args.pastix else 'OFF'}", "-DICB=OFF",
            "-DEXAMPLES=OFF", "-DTESTS=OFF",
            f"-DBLAS_LIBRARIES={args.blas}", f"-DLAPACK_LIBRARIES={args.blas}"])
        run(["cmake", "--build", arpack_build, "--parallel", args.jobs])
        arpack = next(arpack_build.rglob("libarpack.a"))
        # Makefile_MT (USE_MT), Makefile_MFront (external behaviours) and, with PaStiX, Makefile_i8
        flags = (f'-O2 -fcommon -std=gnu89 -fopenmp -I{spooles} -DARCH=Linux -DSPOOLES -DARPACK -DMATRIXSTORAGE -DNETWORKOUT '
                 '-DCALCULIX_EXTERNAL_BEHAVIOURS_SUPPORT' + (' -DUSE_MT=1' if spooles_mt else ''))
        fflags = "-O2 -fopenmp -fallow-argument-mismatch"
        libraries = (f"{spooles}/MT/src/spoolesMT.a " if spooles_mt else "") + f"{spooles}/spooles.a {arpack}"
        if args.pastix:
            prefix = args.pastix.resolve()
            flags += f' -I{prefix}/include -DINTSIZE64 -DPASTIX -DPASTIX_FP32 -DPASTIX_GPU'
            fflags += " -fdefault-integer-8"
            atomic = subprocess.check_output([args.cc, "-print-file-name=libatomic.a"], text=True).strip()
            libraries += " " + " ".join(str(prefix / "lib" / name) for name in [
                "libpastix.a", "libspm.a", "libpastix_parsec.a", "libpastix_kernels.a", "libparsec.a", "libhwloc.a",
                "libscotch.a", "libscotcherrexit.a", "libopenblas.a"]) + f" {atomic} -lz -lstdc++"
            if platform.system() == "Darwin":   # hwloc's macOS backend
                libraries += " -framework CoreFoundation -framework IOKit"
        else:
            libraries += f" {args.blas}"
        # Retain original source lists. Avoid the original Makefile's local paths and
        # link-library prerequisites; compiler/ABI settings are explicit here.
        makefile = ccx / "Makefile.native"
        makefile.write_text(f'''include Makefile.inc
CC={args.cc}
FC={args.fc}
CFLAGS={flags}
FFLAGS={fflags}
OBJECTS=$(sort $(SCCXF:.f=.o) $(SCCXC:.c=.o))
.PHONY: all
all: ccx
%.o: %.c
\t$(CC) $(CFLAGS) -c $< -o $@
%.o: %.f
\t$(FC) $(FFLAGS) -c $< -o $@
ccx: ccx_2.22.o $(OBJECTS)
\t$(FC) -O2 -fopenmp -o $@ ccx_2.22.o $(OBJECTS) {libraries} -lpthread -lm
''')
        report["generatedMakefileSha256"] = sha(makefile)
        report["legacyCompilerPolicy"] = "-fcommon retains pre-GCC-10 tentative-global behavior; sort deduplicates mafillmm.o from stale missing C entry"
        report["compileDatePolicy"] = "Original source banner retained; actual build time recorded here; byte reproducibility not asserted"
        run(["make", "-f", makefile.name, f"-j{args.jobs}", "all"], ccx)
        if args.pastix:   # the license texts of the statically linked PaStiX stack go with the binary
            shutil.copytree(args.pastix.resolve() / "licenses", out / "licenses")
        binary = out / "bin" / "ccx"
        binary.parent.mkdir(exist_ok=True)
        shutil.copy2(ccx / "ccx", binary)
        report["executableSha256"] = sha(binary)
        report.update(adapter.inspect(binary, target["architecture"], sha))
        runtime = report["externalRuntimes"]
        profile = {"id": target_id + ("-2.22-pastix-i8" if args.pastix else "-2.22-spooles-research"), "os": target["os"], "architecture": target["architecture"],
            "version": "2.22", "executable": "ccx", "files": {"ccx": sha(binary)},
            "externalFiles": runtime, "backend": report["backend"], "sourceMatch": "Pinned core/SPOOLES/ARPACK sources and explicit native recipe; different from Windows backend build",
            "sourceManifest": "ThirdParty/Sources/CalculiX/2.22/source-manifest.json",
            "scope": "Research CPU profile; no production default or broad numerical/release acceptance"}
        (out / "build-registry.json").write_text(json.dumps({"schemaVersion": 1, "builds": [profile]}, indent=2) + "\n")
        report["success"] = True
    except (OSError, AttributeError, ValueError, RuntimeError, AssertionError, StopIteration, subprocess.SubprocessError) as error:
        report["error"] = str(error)
    report["elapsedSeconds"] = round(time.monotonic() - started, 3)
    (out / "build-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report.get(k) for k in ["success", "elapsedSeconds", "error", "executableSha256"]}))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

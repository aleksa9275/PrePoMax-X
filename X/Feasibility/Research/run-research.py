#!/usr/bin/env python3
"""Public synthetic compute suite. No model/application/native solver dependencies."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[3]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output-dir",type=Path,required=True);parser.add_argument("--expect-architecture",choices=["Arm64","X64"],required=True);parser.add_argument("--fp-contract-off",action="store_true",help="Explicit structured-kernel diagnostic control, not default production policy");args=parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    report={"success":False,"recordedAtUtc":datetime.now(timezone.utc).isoformat(),"host":{"os":platform.system(),"architecture":platform.machine(),"python":platform.python_version()},"toolSha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"commands":[],"privateInputUsed":False}
    report["ci"]={name:os.environ[name] for name in ["CI_PIPELINE_ID","CI_PIPELINE_URL","CI_JOB_ID","CI_JOB_URL","CI_COMMIT_SHA","CI_COMMIT_REF_NAME","CI_RUNNER_DESCRIPTION","CI_RUNNER_EXECUTABLE_ARCH","CI_JOB_IMAGE"] if name in os.environ}
    cpu=Path("/proc/cpuinfo")
    report["cpuModel"]=next((line.split(":",1)[1].strip() for line in cpu.read_text().splitlines() if line.startswith("model name")),None) if cpu.exists() else None
    try:
        if report["host"]["os"]!="Linux" or platform.machine()!=dict(Arm64="aarch64",X64="x86_64")[args.expect_architecture]:raise ValueError("Native Linux process architecture differs from required target")
        def run(arguments,name=None):
            done=subprocess.run(arguments,cwd=ROOT,capture_output=True,text=True,timeout=300)
            report["commands"].append({"command":[str(a).replace(str(ROOT),"<repository>").replace(str(args.output_dir),"<output>") for a in arguments],"exitCode":done.returncode,"stdout":done.stdout.replace(str(ROOT),"<repository>"),"stderr":done.stderr.replace(str(ROOT),"<repository>")})
            if done.returncode:raise RuntimeError("Research command failed: "+str(arguments[0]))
            if name:
                value=json.loads(done.stdout);(args.output_dir/name).write_text(json.dumps(value,indent=2)+"\n");return value
            return done.stdout
        report["compilerTarget"]=run(["g++","-dumpmachine"]).strip()
        if not report["compilerTarget"].startswith("aarch64" if args.expect_architecture=="Arm64" else "x86_64"):raise ValueError("Compiler target architecture mismatch")
        module=load("inspection_tests","X/Feasibility/Pmx/test-inspection.py");log=io.StringIO();result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
        synthetic={"success":result.wasSuccessful(),"tests":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),"log":log.getvalue()}
        (args.output_dir/"pmx-synthetic.json").write_text(json.dumps(synthetic,indent=2)+"\n")
        if not synthetic["success"] or synthetic["tests"]!=24:raise ValueError("PMX tests failed or count changed")
        run([sys.executable,"X/Feasibility/PmxValues/test-values.py"],"pmx-values-synthetic.json")
        run([sys.executable,"X/Feasibility/ShellJunction/check-fixtures.py","--output",str(args.output_dir/"shell-fixtures.json")])
        run([sys.executable,"X/Feasibility/Meshing/run-meshing.py",*(["--fp-contract-off"] if args.fp_contract_off else []),"--output",str(args.output_dir/"meshing.json")])
        meshing=json.loads((args.output_dir/"meshing.json").read_text());reference=json.loads((ROOT/".project/reports/structured-meshing/macos-arm64.json").read_text())
        native=meshing["nativeGeometry"];managed=meshing["managedCountsGrid"]
        report["floatingPointContraction"]=meshing["floatingPointContraction"]
        compare={"upstreamVectors":meshing["upstreamVectors"]==reference["upstreamVectors"],"sources":meshing["sources"]==reference["sources"],"nativeChecks":native["checks"]==reference["nativeGeometry"]["checks"],"managedChecks":managed["checks"]==reference["managedCountsGrid"]["checks"],"countSignatures":native["countSignatures"]==reference["nativeGeometry"]["countSignatures"]==managed["countSignatures"],"triangleAreaWithin1eMinus12":abs(native["area"]-reference["nativeGeometry"]["area"])<1e-12}
        report["meshingMacComparison"]=compare
        if not all(compare.values()) or not meshing["success"]:raise ValueError("Structured-kernel portable observations differ")
        if managed["runtime"]["architecture"]!=args.expect_architecture or managed["runtime"]["osArchitecture"]!=args.expect_architecture:raise ValueError("Managed runtime architecture mismatch")
        run([sys.executable,"X/Feasibility/Data/run-data.py","--expect-os","Linux","--expect-architecture",args.expect_architecture,"--reference",str(ROOT/".project/reports/core-data/macos-arm64.json"),"--output",str(args.output_dir/"core-data.json")])
        report["success"]=True
    except (OSError,ValueError,RuntimeError,KeyError,subprocess.SubprocessError) as error:report["error"]=str(error).replace(str(ROOT),"<repository>")
    (args.output_dir/"research.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:report.get(k) for k in ["success","host","meshingMacComparison","error"]}))
    return 0 if report["success"] else 1


if __name__=="__main__":raise SystemExit(main())

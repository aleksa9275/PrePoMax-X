#!/usr/bin/env python3
"""Measure unchanged upstream vector checker under explicit compiler FP modes."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[3]
CPP=ROOT/"CaeMesh/Meshing/Transfinite/Cpp"


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",required=True,type=Path);args=parser.parse_args()
    report={"os":platform.system(),"architecture":platform.machine(),"toolSha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"compiler":subprocess.check_output(["g++","--version"],text=True),"target":subprocess.check_output(["g++","-dumpmachine"],text=True).strip(),"cases":[]}
    with tempfile.TemporaryDirectory(prefix="prepomaxx-fp-") as temp:
        for flags in [["-O0"],["-O2"],["-O2","-ffp-contract=off"],["-O2","-ffp-contract=fast"]]:
            executable=Path(temp)/"original-check"
            build=subprocess.run(["g++","-std=c++17",*flags,str(CPP/"three_block_mapping_check.cpp"),"-o",str(executable)],capture_output=True,text=True,timeout=90)
            if build.returncode:raise RuntimeError("Diagnostic build failed")
            run=subprocess.run([str(executable),str(CPP/"three_block_vectors.txt")],capture_output=True,text=True,timeout=90)
            report["cases"].append({"flags":flags,"exitCode":run.returncode,"stdout":run.stdout,"stderr":run.stderr})
    report["sourceHashes"]={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [CPP/"three_block_mapping_check.cpp",CPP/"three_block_mapping.h",CPP/"three_block_vectors.txt"]}
    args.output.write_text(json.dumps(report,indent=2)+"\n");print(json.dumps([{k:c[k] for k in ["flags","exitCode"]} for c in report["cases"]]))


if __name__=="__main__":main()

#!/usr/bin/env python3
"""Exact bundled solver, synthetic analytical reference through existing CrossOver."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_dat(text):
    blocks={};current=None
    for line in text.splitlines():
        if line.lstrip().startswith("displacements ("):current="displacements";blocks[current]=[]
        elif line.lstrip().startswith("forces ("):current="forces";blocks[current]=[]
        elif line.lstrip().startswith("stresses ("):current="stresses";blocks[current]=[]
        elif current and re.match(r"^\s+\d+\s+",line):
            blocks[current].append([float(v.replace("D","E")) for v in line.split()])
    return blocks


def analytical_checks(blocks):
    coordinates=[(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)]
    checks=[]
    def check(name,condition):checks.append({"name":name,"passed":bool(condition)})
    displacements=blocks.get("displacements",[]);forces=blocks.get("forces",[]);stresses=blocks.get("stresses",[])
    check("all eight displacement IDs exactly once",sorted(int(r[0]) for r in displacements)==list(range(1,9)))
    check("all eight force IDs exactly once",sorted(int(r[0]) for r in forces)==list(range(1,9)))
    expected=[(100/210000*x,-0.3*100/210000*y,-0.3*100/210000*z) for x,y,z in coordinates]
    check("all displacement components match uniform uniaxial strain",len(displacements)==8 and all(abs(row[k+1]-expected[int(row[0])-1][k])<=1e-9 for row in displacements for k in range(3)))
    check("eight integration-point stresses",len(stresses)==8 and all(int(row[0])==1 for row in stresses))
    check("axial stress 100 MPa, transverse/shear zero",len(stresses)==8 and all(abs(row[2]-100)<=1e-4 and all(abs(v)<=1e-5 for v in row[3:]) for row in stresses))
    reactions=sum(row[1] for row in forces if int(row[0]) in {1,4,5,8})
    check("supported face balances 100 N",len(forces)==8 and abs(reactions+100)<=1e-5)
    check("global nodal-force sum zero",len(forces)==8 and all(abs(sum(row[k+1] for row in forces))<=1e-5 for k in range(3)))
    return checks


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--solver",type=Path,required=True);parser.add_argument("--wine",type=Path,required=True);parser.add_argument("--bottle",required=True);parser.add_argument("--output-dir",type=Path,required=True);args=parser.parse_args()
    report={"success":False,"recordedAtUtc":datetime.now(timezone.utc).isoformat(),"evidenceKind":"Bundled Windows CalculiX through CrossOver; not native Mac/Linux solver parity","toolSha256":sha(Path(__file__)),"fixtureSha256":sha(HERE/"uniaxial-cube.inp"),"solverFiles":{p.name:sha(p) for p in sorted(args.solver.parent.iterdir()) if p.suffix.lower() in {".exe",".dll"}},"threads":1}
    args.output_dir.mkdir(parents=True,exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="prepomaxx-solver-",dir="/private/tmp") as temp:
            work=Path(temp);shutil.copyfile(HERE/"uniaxial-cube.inp",work/"uniaxial.inp")
            environment=dict(os.environ,OMP_NUM_THREADS="1",MKL_NUM_THREADS="1")
            done=subprocess.run([str(args.wine),"--bottle",args.bottle,str(args.solver),"-i","uniaxial"],cwd=work,env=environment,capture_output=True,text=True,timeout=120)
            report["exitCode"]=done.returncode;report["stdout"]=done.stdout.replace(temp,"<temporary>");report["stderr"]=done.stderr.replace(temp,"<temporary>")
            match=re.search(r"Version\s+([\d.]+)",done.stdout);report["solverVersion"]=match.group(1) if match else None
            if done.returncode or not (work/"uniaxial.dat").exists():raise RuntimeError("Bundled solver failed; no alternative substituted")
            for suffix in ["dat","frd","sta","cvg"]:
                path=work/("uniaxial."+suffix)
                if path.exists():shutil.copyfile(path,args.output_dir/path.name)
            blocks=parse_dat((work/"uniaxial.dat").read_text());report["checks"]=analytical_checks(blocks)
            if not all(c["passed"] for c in report["checks"]):raise RuntimeError("Analytical check failed")
            altered={k:[row[:] for row in rows] for k,rows in blocks.items()};altered["displacements"][0][1]+=0.01
            report["negativeControlRejected"]=not all(c["passed"] for c in analytical_checks(altered))
            report["success"]=report["negativeControlRejected"]
            report["outputHashes"]={p.name:sha(p) for p in args.output_dir.glob("uniaxial.*")}
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:report["error"]=str(error)
    (args.output_dir/"reference.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:report.get(k) for k in ["success","solverVersion","checks","error"]}))
    return 0 if report["success"] else 1


if __name__=="__main__":raise SystemExit(main())

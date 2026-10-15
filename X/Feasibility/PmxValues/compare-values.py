#!/usr/bin/env python3
"""Private shallow engineering-record comparison; emits no values/fingerprints."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location("pmx",HERE.parent/"Pmx/inspect-pmx.py")
pmx=importlib.util.module_from_spec(spec);spec.loader.exec_module(pmx)


def compare(before,after):
    with tempfile.TemporaryDirectory(prefix="prepomaxx-values-") as temp:
        work=Path(temp);graphs=[];metadata=[]
        for index,path in enumerate([before,after]):
            with path.open("rb") as stream:frame,graph=pmx.framing(stream)
            target=work/(str(index)+".nrbf");target.write_bytes(graph);graphs.append(target);metadata.append(frame)
        build=subprocess.run(["dotnet","build",str(HERE/"PmxValues.csproj"),"-c","Release","--disable-build-servers","--artifacts-path",str(work/"build"),"-v:q"],capture_output=True,text=True,timeout=90)
        if build.returncode:raise RuntimeError(build.stdout.replace(str(ROOT),"<repository>").replace(temp,"<temporary>"))
        assembly=next((work/"build/bin").rglob("PmxValues.dll"))
        done=subprocess.run(["dotnet",str(assembly),*map(str,graphs)],capture_output=True,text=True,timeout=90)
        report=json.loads(done.stdout)
        if done.returncode or not report["success"]:raise ValueError("Record comparison rejected inputs")
        for path,frame in zip([before,after],metadata):
            with path.open("rb") as stream:assert pmx.hash_stream(stream)==frame["inputSha256"]
        report["inputSha256"]=[row["inputSha256"] for row in metadata]
        report["inputUnchanged"]=True
        report["toolHashes"]={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),HERE/"Program.cs",HERE/"PmxValues.csproj",HERE/"NuGet.Config"]}
        return report


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("before",type=Path);parser.add_argument("after",type=Path);parser.add_argument("--output",required=True,type=Path);args=parser.parse_args()
    if any(args.output.resolve()==p.resolve() or (args.output.exists() and args.output.samefile(p)) for p in [args.before,args.after]):parser.error("Output aliases an input")
    report=compare(args.before,args.after);args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:report[k] for k in ["success","comparedTypes","matchingTypes","jobEnvironmentListSizes"]}))

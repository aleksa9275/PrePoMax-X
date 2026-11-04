#!/usr/bin/env python3
"""Read-only, bounded PMX envelope and record-only graph inventory."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import zlib

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BASELINE="de8f73032a72746e3d6d9afd53d9fbd289eb310a"
MAX_FILE=512*1024*1024
MAX_INFLATED=128*1024*1024


def hash_stream(stream):
    stream.seek(0)
    return hashlib.file_digest(stream,"sha256").hexdigest()


def read_exact(stream,size):
    value=stream.read(size)
    if len(value)!=size: raise ValueError("Truncated envelope")
    return value


def framing(stream,max_inflated=MAX_INFLATED):
    report, graph, _ = read_frames(stream, max_inflated)
    return report, graph


def read_frames(stream,max_inflated=MAX_INFLATED):
    if not 0<max_inflated<=MAX_INFLATED: raise ValueError("Invalid inflated-byte limit")
    size=stream.seek(0,2); stream.seek(0)
    if not 36<=size<=MAX_FILE: raise ValueError("File outside inspection size limits")
    before=hash_stream(stream); stream.seek(0)
    raw_header=read_exact(stream,32).rstrip(b"\0")
    try: header=raw_header.decode("ascii")
    except UnicodeDecodeError as error: raise ValueError("Unsupported PMX header encoding") from error
    match=re.fullmatch(r"PrePoMax v(\d+)\.(\d+)\.(\d+)(?: [ -~]+)?",header)
    if not match: raise ValueError("Unsupported or unrecognized PMX header")
    version=tuple(map(int,match.groups()))
    if version<(2,0,6): raise ValueError("Pre-2.0.6 PMX framing is outside this inspector")
    compressed_size=struct.unpack("<i",read_exact(stream,4))[0]
    if not 0<compressed_size<=size-36: raise ValueError("Compressed frame length outside file")
    inflater=zlib.decompressobj(-15)
    inflated=io.BytesIO(); remaining=compressed_size
    while remaining:
        chunk=read_exact(stream,min(64*1024,remaining)); remaining-=len(chunk)
        try: decoded=inflater.decompress(chunk,max_inflated-inflated.tell()+1)
        except zlib.error as error: raise ValueError("Invalid raw Deflate block") from error
        if inflated.tell()+len(decoded)>max_inflated: raise ValueError("Inflated-byte limit exceeded")
        inflated.write(decoded)
        if inflater.unconsumed_tail: raise ValueError("Inflated-byte limit exceeded")
        if inflater.eof and (inflater.unused_data or remaining): raise ValueError("Bytes after end of declared Deflate stream")
    if not inflater.eof: raise ValueError("Truncated Deflate block")
    inflated_size=inflated.tell(); inflated.seek(0)
    graph_size=struct.unpack("<q",read_exact(inflated,8))[0]
    if not 18<=graph_size<=min(MAX_INFLATED,inflated_size-8): raise ValueError("NRBF graph length outside inflated block")
    graph=read_exact(inflated,graph_size)
    if graph[0]!=0 or struct.unpack("<ii",graph[9:17])!=(1,0): raise ValueError("Unrecognized NRBF stream header")
    opaque_model=inflated.read()
    tail_offset=36+compressed_size
    tail_hash=hashlib.sha256()
    while chunk:=stream.read(64*1024): tail_hash.update(chunk)
    if hash_stream(stream)!=before: raise ValueError("Input changed during inspection")
    return {"inputSha256":before,"fileBytes":size,"header":header,"versionNumbers":list(version),
            "mainFrame":{"offset":36,"compressedBytes":compressed_size,"inflatedBytes":inflated_size,
                         "nrbfBytes":graph_size,"nrbfSha256":hashlib.sha256(graph).hexdigest(),
                         "opaqueModelBytes":len(opaque_model),"opaqueModelSha256":hashlib.sha256(opaque_model).hexdigest()},
            "opaqueTail":{"offset":tail_offset,"bytes":size-tail_offset,"sha256":tail_hash.hexdigest()},
            "inputUnchanged":True},graph,opaque_model


def build_decoder(folder,commands):
    result=subprocess.run(["dotnet","build",str(HERE/"NrbfInventory.csproj"),"-c","Release","--disable-build-servers",
                           "--artifacts-path",str(folder),"-v:minimal"],cwd=ROOT,capture_output=True,text=True,timeout=90)
    commands.append({"kind":"decoder build","exitCode":result.returncode,
                     "log":(result.stdout+result.stderr).replace(str(ROOT),"<repository>").replace(str(folder),"<temporary>")})
    if result.returncode: raise ValueError("Record decoder build failed")
    assemblies=list((folder/"bin").rglob("PrePoMaxX.NrbfInventory.dll"))
    if len(assemblies)!=1: raise ValueError("Expected one record decoder")
    return assemblies[0]


def decode_graph(graph,assembly,folder):
    path=folder/"bounded-graph.nrbf"; path.write_bytes(graph)
    done=subprocess.run(["dotnet",str(assembly),"--inventory",str(path)],cwd=ROOT,capture_output=True,text=True,timeout=90)
    try: result=json.loads(done.stdout)
    except json.JSONDecodeError as error: raise ValueError("Record decoder returned no valid report") from error
    if done.returncode or not result.get("success"): raise ValueError("Record decoder rejected graph: "+str(result.get("errorType","unknown failure")))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--max-inflated-mib",type=int,default=128)
    args=parser.parse_args()
    if (args.output.resolve()==args.input.resolve() or
        (args.output.exists() and args.input.exists() and os.path.samefile(args.output,args.input))):
        parser.error("Output must differ from input, including hard links")
    report={"schemaVersion":1,"success":False,"recordedAtUtc":datetime.now(timezone.utc).isoformat(),"commands":[],
            "sourceBaseline":BASELINE,"inputPathOmitted":True,"evidenceKind":"PMX framing and NRBF records, not application deserialization"}
    try:
        with args.input.open("rb") as stream: report["framing"],graph=framing(stream,args.max_inflated_mib*1024*1024)
        with tempfile.TemporaryDirectory(prefix="prepomaxx-pmx-") as work:
            folder=Path(work); assembly=build_decoder(folder/"build",report["commands"])
            report["graphInventory"]=decode_graph(graph,assembly,folder)
        report["toolHashes"]={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ["Program.cs","NrbfInventory.csproj","inspect-pmx.py","NuGet.Config"]}
        paths=["PrePoMax/Controller.cs","CaeGlobals/Extensions.cs","CaeGlobals/Tools.cs","CaeModel/FeModel.cs","CaeResults/ResultsCollection.cs"]
        report["sourceContext"]=[]
        for name in paths:
            data=(ROOT/name).read_bytes(); original=subprocess.check_output(["git","show",BASELINE+":"+name],cwd=ROOT)
            if data!=original: raise ValueError("Source context differs from pinned baseline")
            report["sourceContext"].append({"path":name,"sha256":hashlib.sha256(data).hexdigest(),"contextOnly":True})
        with args.input.open("rb") as stream:
            if hash_stream(stream)!=report["framing"]["inputSha256"]: raise ValueError("Input changed during record inspection")
        report["success"]=True
        report["limits"]=["No payload type loading, application object construction, or BinaryFormatter invocation",
                          "Version header is file metadata, not a verified producer binary/source identity",
                          "Custom model block and remaining file tail are opaque; no result field interpretation",
                          "No model string/primitive values or source file path emitted",
                          "Not an original-application reopen, history replay or round-trip proof",
                          "Byte caps and child timeout are not an OS memory quota"]
    except (OSError,ValueError,subprocess.SubprocessError) as error:
        report["error"]=str(error).replace(str(args.input),"<input>")
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"success":report["success"],"header":report.get("framing",{}).get("header"),
                      "records":report.get("graphInventory",{}).get("recordCount"),"types":len(report.get("graphInventory",{}).get("types",[])),"error":report.get("error")}))
    return 0 if report["success"] else 1


if __name__=="__main__": raise SystemExit(main())

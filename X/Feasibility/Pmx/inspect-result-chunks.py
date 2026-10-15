#!/usr/bin/env python3
"""Fingerprint single-result mesh/field frames; do not interpret numerical data."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib


def inspect(path):
    with path.open("rb") as source: initial_hash=hashlib.file_digest(source,"sha256").hexdigest()
    with path.open("rb") as stream:
        size=stream.seek(0,2);stream.seek(0)
        if not 36<=size<=512*1024*1024: raise ValueError("File size outside limits")
        def read(n):
            if n<0 or stream.tell()+n>size: raise ValueError("Truncated results framing")
            value=stream.read(n)
            if len(value)!=n: raise ValueError("Truncated results framing")
            return value
        def integer(): return struct.unpack("<i",read(4))[0]
        header=read(32).rstrip(b"\0").decode("ascii")
        if header not in {"PrePoMax v2.5.1 dev","PrePoMax v2.6.0"}: raise ValueError("Unverified version for results-frame probe")
        main=integer()
        if not 0<main<=size-36: raise ValueError("Invalid main frame")
        stream.seek(main,1)
        count=integer()
        if count!=1: raise ValueError("Only the observed single-result framing is supported")
        name_size=integer()
        if not 0<=name_size<=65536: raise ValueError("Result name size exceeds limit")
        name=read(name_size);name.decode("utf-8")
        if integer()!=1: raise ValueError("Only present result data supported")
        chunks=[];inflated_total=0
        def chunk(kind):
            nonlocal inflated_total
            compressed=integer()
            if not 0<compressed<=size-stream.tell(): raise ValueError("Invalid result chunk length")
            offset=stream.tell();remaining=compressed;decoder=zlib.decompressobj(-15);digest=hashlib.sha256();length=0
            while remaining:
                block=read(min(65536,remaining));remaining-=len(block)
                value=decoder.decompress(block,128*1024*1024-length+1)
                length+=len(value);inflated_total+=len(value)
                if length>128*1024*1024 or inflated_total>512*1024*1024 or decoder.unconsumed_tail: raise ValueError("Results inflated-byte limit exceeded")
                digest.update(value)
                if decoder.eof and (decoder.unused_data or remaining): raise ValueError("Data after result Deflate end")
            if not decoder.eof: raise ValueError("Truncated result Deflate")
            chunks.append({"kind":kind,"offset":offset,"compressedBytes":compressed,"inflatedBytes":length,"inflatedSha256":digest.hexdigest()})
        chunk("mesh-and-node-lookup")
        state=integer()
        if state not in {-1,1}: raise ValueError("Unrecognized fields state")
        fields=integer() if state==1 else 0
        if not 0<=fields<=10000: raise ValueError("Field count outside limits")
        for i in range(fields): chunk("field-"+str(i))
        history=read(size-stream.tell())
        if len(history)<4 or struct.unpack("<i",history[:4])[0] not in {-1,1}: raise ValueError("Unrecognized history trailer")
        with path.open("rb") as source:
            if hashlib.file_digest(source,"sha256").hexdigest()!=initial_hash: raise ValueError("Input changed during inspection")
        return {"success":True,"inputSha256":initial_hash,"header":header,"resultCount":count,"resultNameSha256":hashlib.sha256(name).hexdigest(),
                "fieldFrameCount":fields,"chunks":chunks,"opaqueHistoryTrailerBytes":len(history),"opaqueHistoryTrailerSha256":hashlib.sha256(history).hexdigest(),
                "limits":["Observed single-result versions only","Mesh/field payloads fingerprinted, not interpreted","History trailer remains opaque; no numerical or command equivalence claim"]}


def datatype_insertion_only(old,new):
    # Field.ReadFromBinaryReader adds Int32 DataType at version 2.5.3, before
    # Complex (1), DataState (4), and four trailing booleans (4).
    return (len(old)>=9 and len(new)==len(old)+4 and new[:-13]==old[:-9] and
            new[-9:]==old[-9:] and struct.unpack("<i",new[-13:-9])[0] in {0,1,2,3})


def compare(before,after):
    old=inspect(before);new=inspect(after)
    if old["header"]!="PrePoMax v2.5.1 dev" or new["header"]!="PrePoMax v2.6.0": raise ValueError("Field-layout comparison limited to observed 2.5.1-dev to 2.6.0 pair")
    if len(old["chunks"])!=len(new["chunks"]): raise ValueError("Different result frame counts")
    fields=[]
    with before.open("rb") as left,after.open("rb") as right:
        def payload(stream,row):
            stream.seek(row["offset"]);decoder=zlib.decompressobj(-15)
            value=decoder.decompress(stream.read(row["compressedBytes"]),128*1024*1024+1)
            if len(value)>128*1024*1024 or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
                raise ValueError("Result frame changed or exceeded limits during comparison")
            if hashlib.sha256(value).hexdigest()!=row["inflatedSha256"]: raise ValueError("Result frame changed during comparison")
            return value
        for a,b in zip(old["chunks"][1:],new["chunks"][1:]):
            u=payload(left,a);v=payload(right,b)
            same=datatype_insertion_only(u,v)
            fields.append({"kind":a["kind"],"originalBytesPreservedWithDatatypeInsertion":same,
                           "addedDataType":struct.unpack("<i",v[-13:-9])[0] if same else None})
    return {"comparisonCompleted":True,"semanticEquivalenceEstablished":False,"beforeSha256":old["inputSha256"],"afterSha256":new["inputSha256"],
            "resultMeshAndNodeLookupIdentical":old["chunks"][0]["inflatedSha256"]==new["chunks"][0]["inflatedSha256"],
            "fieldFrames":fields,"allOriginalFieldBytesPreservedWithDatatypeInsertion":all(row["originalBytesPreservedWithDatatypeInsertion"] for row in fields),
            "opaqueHistoryTrailerIdentical":old["opaqueHistoryTrailerSha256"]==new["opaqueHistoryTrailerSha256"],
            "limits":["Version-gated byte comparison, not a solver calculation or full document semantic comparison","Changed NRBF members and removed types still need review"]}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("input",type=Path);parser.add_argument("--compare-with",type=Path);parser.add_argument("--output",type=Path,required=True);args=parser.parse_args()
    if args.output.resolve()==args.input.resolve() or (args.output.exists() and args.input.exists() and args.output.samefile(args.input)): parser.error("Output must differ from input")
    if args.compare_with and (args.output.resolve()==args.compare_with.resolve() or (args.output.exists() and args.output.samefile(args.compare_with))): parser.error("Output must differ from comparison input")
    report=compare(args.input,args.compare_with) if args.compare_with else inspect(args.input)
    report["toolSha256"]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"success":True,"fieldFrames":len(report["fieldFrames"]) if args.compare_with else report["fieldFrameCount"],
                      "fieldBytesPreserved":report.get("allOriginalFieldBytesPreservedWithDatatypeInsertion")}))


if __name__=="__main__": main()

#!/usr/bin/env python3
"""Compare record inventories without mistaking version normalization for parity."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def normalize(name):
    return re.sub(r", Version=\d+\.\d+\.\d+\.\d+", "",name)


def compare(before,after):
    if not before.get("success") or not after.get("success"): raise ValueError("Both inspections must succeed")
    old={normalize(row["type"]):row for row in before["graphInventory"]["types"]}
    new={normalize(row["type"]):row for row in after["graphInventory"]["types"]}
    if len(old)!=len(before["graphInventory"]["types"]) or len(new)!=len(after["graphInventory"]["types"]):
        raise ValueError("Version normalization would merge distinct observed types")
    changes=[]
    for name in sorted(old.keys() & new.keys()):
        added=sorted(set(new[name]["members"])-set(old[name]["members"]))
        removed=sorted(set(old[name]["members"])-set(new[name]["members"]))
        if added or removed: changes.append({"typeIgnoringAssemblyVersion":name,"addedMembers":added,"removedMembers":removed})
    def controller_cycle(report):
        edges=report["graphInventory"]["referenceEdges"]
        return any(e["source"]=="PrePoMax.Controller" and e["member"]=="_commands" and
                   any(f["sourceOrdinal"]==e["targetOrdinal"] and f["member"]=="_controller" and f["targetOrdinal"]==e["sourceOrdinal"] for f in edges) for e in edges)
    return {"inspectionComparisonCompleted":True,"semanticEquivalenceEstablished":False,
            "beforeHeader":before["framing"]["header"],"afterHeader":after["framing"]["header"],
            "beforeSha256":before["framing"]["inputSha256"],"afterSha256":after["framing"]["inputSha256"],
            "modelBinaryBlockIdentical":before["framing"]["mainFrame"]["opaqueModelSha256"]==after["framing"]["mainFrame"]["opaqueModelSha256"],
            "remainingTailIdentical":before["framing"]["opaqueTail"]["sha256"]==after["framing"]["opaqueTail"]["sha256"],
            "controllerCommandCyclePresentInBoth":controller_cycle(before) and controller_cycle(after),
            "records":{"before":before["graphInventory"]["recordCount"],"after":after["graphInventory"]["recordCount"]},
            "types":{"before":len(old),"after":len(new),"addedIgnoringAssemblyVersion":sorted(new.keys()-old.keys()),"removedIgnoringAssemblyVersion":sorted(old.keys()-new.keys())},
            "memberChanges":changes,
            "limits":["Assembly version normalization is used only to pair records, not to declare compatibility",
                      "Primitive/string values and custom result semantics are not compared","Model-block byte identity proves only that block"]}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("before",type=Path);parser.add_argument("after",type=Path);parser.add_argument("--output",type=Path,required=True);args=parser.parse_args()
    report=compare(json.loads(args.before.read_text()),json.loads(args.after.read_text()))
    report["toolSha256"]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({key:report[key] for key in ["modelBinaryBlockIdentical","remainingTailIdentical","controllerCommandCyclePresentInBoth","semanticEquivalenceEstablished"]}))


if __name__=="__main__": main()

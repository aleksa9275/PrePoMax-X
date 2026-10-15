#!/usr/bin/env python3
"""Validate only this tiny fixture grammar; not a general INP reader/mesher."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent


def parse(path):
    nodes={}; elements={}; section=None; group=None
    for raw in path.read_text().splitlines():
        line=raw.strip()
        if not line or line.startswith("**"): continue
        if line.startswith("*"):
            parts=[p.strip().upper() for p in line.split(",")]
            section=parts[0]
            if section=="*NODE" and len(parts)==1: continue
            if section=="*ELEMENT" and "TYPE=S4" in parts and len(parts)==3:
                group=next(p.split("=",1)[1] for p in parts if p.startswith("ELSET="))
                if group in {"PLATE","WEB"}: continue
            raise ValueError("Unsupported fixture keyword: "+line)
        values=[p.strip() for p in line.split(",")]
        if section=="*NODE" and len(values)==4:
            label=int(values[0]); coordinate=tuple(map(float,values[1:]))
            if label in nodes or not all(math.isfinite(x) for x in coordinate): raise ValueError("Invalid node")
            nodes[label]=coordinate
        elif section=="*ELEMENT" and len(values)==5:
            label=int(values[0]); ids=tuple(map(int,values[1:]))
            if label in elements or len(set(ids))!=4: raise ValueError("Invalid element")
            elements[label]={"group":group,"nodes":ids}
        else: raise ValueError("Unsupported fixture record: "+line)
    if not elements or any(n not in nodes for e in elements.values() for n in e["nodes"]): raise ValueError("Missing nodes/elements")
    return nodes,elements


def observe(nodes,elements):
    groups={group:[e for e in elements.values() if e["group"]==group] for group in ["PLATE","WEB"]}
    used={group:{n for e in rows for n in e["nodes"]} for group,rows in groups.items()}
    edges={group:{tuple(sorted((e["nodes"][k],e["nodes"][(k+1)%4]))) for e in rows for k in range(4)} for group,rows in groups.items()}
    areas={}
    for group,rows in groups.items():
        area=0
        for element in rows:
            normal=[0.,0.,0.]
            for k in range(4):
                a=nodes[element["nodes"][k]]; b=nodes[element["nodes"][(k+1)%4]]
                normal[0]+=a[1]*b[2]-a[2]*b[1]; normal[1]+=a[2]*b[0]-a[0]*b[2]; normal[2]+=a[0]*b[1]-a[1]*b[0]
            area+=math.sqrt(sum(v*v for v in normal))/2
        areas[group]=area
    return {"nodeCount":len(nodes),"elementIds":sorted(elements),
            "plateElementIds":sorted(i for i,e in elements.items() if e["group"]=="PLATE"),
            "webElementIds":sorted(i for i,e in elements.items() if e["group"]=="WEB"),
            "sharedNodeIds":sorted(used["PLATE"] & used["WEB"]),
            "sharedEdges":[list(pair) for pair in sorted(edges["PLATE"] & edges["WEB"])],
            "coincidentDistinctIdPairs":[[a,b] for a in sorted(used["PLATE"]) for b in sorted(used["WEB"]) if a!=b and nodes[a]==nodes[b]],
            "areas":areas,"webMinimumZ":min(nodes[n][2] for n in used["WEB"])}


def require_expected(actual,expected):
    for key,value in expected.items():
        if actual[key]!=value: raise ValueError("Mismatch "+key+": "+repr(actual[key])+" != "+repr(value))


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--output",type=Path,required=True); args=parser.parse_args()
    manifest=json.loads((HERE/"manifest.json").read_text())
    report={"success":False,"cases":[],"regressions":[],"toolSha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "manifestSha256":hashlib.sha256((HERE/"manifest.json").read_bytes()).hexdigest(),"limits":["Hand-authored mesh fixtures only","Not a general INP reader, CAD mesh generation, solver or Windows readback"]}
    try:
        for case in manifest["cases"]:
            path=HERE/case["file"]
            if hashlib.sha256(path.read_bytes()).hexdigest()!=case["sha256"]: raise ValueError("Fixture hash changed: "+case["file"])
            nodes,elements=parse(path); actual=observe(nodes,elements); require_expected(actual,case["expected"])
            report["cases"].append({"file":case["file"],"sha256":case["sha256"],"status":"passed","observations":actual})
        nodes,elements=parse(HERE/"connected.inp")
        altered=copy.deepcopy(elements); altered[21]["nodes"]=(1,7,8,4)
        try: require_expected(observe(nodes,altered),manifest["cases"][0]["expected"])
        except ValueError: report["regressions"].append({"name":"wrong web attachment rejected","status":"passed"})
        else: raise ValueError("Connectivity mutation was accepted")
        nodes,elements=parse(HERE/"intentional-gap.inp"); altered=dict(nodes); altered[9]=(0,0,0); altered[10]=(0,200,0)
        try: require_expected(observe(altered,elements),manifest["cases"][3]["expected"])
        except ValueError: report["regressions"].append({"name":"closed intentional gap rejected","status":"passed"})
        else: raise ValueError("Gap mutation was accepted")
        report["success"]=True
    except (OSError,ValueError,KeyError) as error: report["error"]=str(error)
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"success":report["success"],"cases":len(report["cases"]),"regressions":len(report["regressions"]),"error":report.get("error")}))
    return 0 if report["success"] else 1


if __name__=="__main__": raise SystemExit(main())

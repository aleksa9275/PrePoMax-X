#!/usr/bin/env python3
"""Run unchanged structured-kernel contracts; no fetch or production mutation."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CPP = ROOT / "CaeMesh/Meshing/Transfinite/Cpp"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fp-contract-off", action="store_true", help="Explicit research control: disable compiler floating-point contraction")
    args = parser.parse_args()
    report = {"schemaVersion": 1, "success": False, "recordedAtUtc": datetime.now(timezone.utc).isoformat(),
              "host": {"os": platform.system(), "architecture": platform.machine()}, "commands": [],
              "floatingPointContraction": "off (explicit research control)" if args.fp_contract_off else "compiler default"}
    temporary = None
    try:
        manifest = json.loads((HERE / "source-manifest.json").read_text())
        report["sourceCommit"] = manifest["baselineCommit"]
        report["sources"] = manifest["sourceFiles"]
        baseline_exception = None
        for source in manifest["sourceFiles"]:
            original = subprocess.check_output(["git", "show", manifest["baselineCommit"]+":"+source["path"]], cwd=ROOT)
            actual = (ROOT/source["path"]).read_bytes()
            if source["path"] == "CaeGlobals/ExceptionTools.cs":
                baseline_exception = original
                if actual != original:
                    # Task 0013 only moves the existing domain exception out of
                    # Windows presentation. This historical experiment continues
                    # to measure its original, pinned compilation boundary below.
                    text = original.decode("utf-8")
                    start = text.index("    public class CaeException : Exception\n")
                    end = text.index("    //\n    public static class ExceptionTools", start)
                    body = text[start:end]
                    expected = (text[:start] + text[end+7:]).encode("utf-8")
                    moved = ROOT/"CaeGlobals/CaeException.cs"
                    if actual != expected or not moved.exists() or body not in moved.read_text():
                        raise ValueError("Unexpected exception-boundary source adaptation")
                    report["sourceAdaptations"] = [{"kind":"Mechanical CaeException file separation", "path":source["path"],
                        "currentSha256":sha(actual), "exceptionSha256":sha(moved.read_bytes()),
                        "boundaryUses":"original Git bytes, not adapted portable library"}]
                    actual = original
            if sha(original)!=source["sha256"] or actual!=original:
                raise ValueError("Source differs from pinned baseline: "+source["path"])
        tree=ET.parse(HERE/"MeshingProbe.csproj")
        expected={"CaeMesh/Meshing/Transfinite/TransfiniteSideTriple.cs", "CaeMesh/Meshing/Transfinite/ThreeBlockGrid.cs"}
        includes={item.attrib["Include"].removeprefix("$(UpstreamSourceRoot)/") for item in tree.findall(".//Compile")}
        if includes!=expected or tree.findall(".//PackageReference") or tree.findall(".//ProjectReference"):
            raise ValueError("Zero-package/source-link closure changed")
        report["toolHashes"]={name:sha((HERE/name).read_bytes()) for name in ["Program.cs","geometry-check.cpp","MeshingProbe.csproj","run-meshing.py","source-manifest.json","NuGet.Config"]}
        compiler=shutil.which("clang++") or shutil.which("g++")
        if not compiler: raise RuntimeError("Native C++17 compiler is required")
        environment=dict(os.environ, DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_SKIP_FIRST_TIME_EXPERIENCE="1")
        def run(command, expected_code=0):
            done=subprocess.run(command,cwd=ROOT,env=environment,text=True,capture_output=True,timeout=90)
            def clean(value): return value.replace(str(ROOT),"<repository>").replace(temporary or "<unused>","<temporary>")
            item={"command":[clean(str(x)) for x in command],"exitCode":done.returncode,
                  "stdout":clean(done.stdout),"stderr":clean(done.stderr)}
            report["commands"].append(item)
            if expected_code is not None and done.returncode!=expected_code:
                raise RuntimeError("Unexpected process result: "+str(item))
            return done
        report["compiler"]=run([compiler,"--version"]).stdout.strip()
        report["sdk"]=run(["dotnet","--version"]).stdout.strip()
        fp_flags=["-ffp-contract=off"] if args.fp_contract_off else []
        with tempfile.TemporaryDirectory(prefix="prepomaxx-meshing-") as folder:
            temporary=folder
            work=Path(folder)
            original_exe=work/"original-check"
            run([compiler,"-std=c++17","-O2",*fp_flags,"-Wall","-Wextra","-Werror",str(CPP/"three_block_mapping_check.cpp"),"-o",str(original_exe)])
            vectors=CPP/"three_block_vectors.txt"
            measured=run([str(original_exe),str(vectors)])
            names=[line.split()[1] for line in measured.stdout.splitlines() if line.startswith("ok ")]
            expected_names=[line.split()[1] for line in vectors.read_text().splitlines() if line.startswith("case ")]
            if names!=expected_names or len(names)!=13: raise ValueError("Original vector cases incomplete")
            report["upstreamVectors"]={"passed":len(names),"cases":names,"kind":"C++ execution against upstream C#-generated vectors"}
            # Verify that the existing comparator detects a material coordinate change.
            changed=vectors.read_text().splitlines()
            index=next(i for i,line in enumerate(changed) if line.startswith("inner "))+1
            row=changed[index].split(); row[0]=str(float(row[0])+0.01); changed[index]=" ".join(row)
            wrong=work/"changed-vectors.txt"; wrong.write_text("\n".join(changed)+"\n")
            rejection=run([str(original_exe),str(wrong)],1)
            if "FAILED" not in rejection.stdout: raise ValueError("Mutated vector was not identified")
            run([str(original_exe),str(work/"missing.txt")],2)
            geometry_exe=work/"geometry-check"
            run([compiler,"-std=c++17","-O2",*fp_flags,"-Wall","-Wextra","-Werror","-I",str(CPP),str(HERE/"geometry-check.cpp"),"-o",str(geometry_exe)])
            report["nativeGeometry"]=json.loads(run([str(geometry_exe)]).stdout)
            # Avoid duplicating all count signatures in the recorded process log.
            report["commands"][-1]["stdout"]="<JSON retained in nativeGeometry>"
            run(["dotnet","build",str(HERE/"MeshingProbe.csproj"),"-c","Release","--disable-build-servers","--no-incremental","--artifacts-path",str(work/"managed"),"-v:minimal"])
            assemblies=list((work/"managed/bin").rglob("PrePoMaxX.MeshingProbe.dll"))
            if len(assemblies)!=1: raise ValueError("Expected one probe assembly")
            report["managedCountsGrid"]=json.loads(run(["dotnet",str(assemblies[0]),"--self-test"]).stdout)
            report["commands"][-1]["stdout"]="<JSON retained in managedCountsGrid>"
            for arguments in [[],["unknown"]]:
                usage=run(["dotnet",str(assemblies[0]),*arguments],2)
                if json.loads(usage.stdout)["success"]: raise ValueError("CLI contract failed")
            managed=report["managedCountsGrid"]
            native=report["nativeGeometry"]
            if not managed["success"] or not native["success"]: raise ValueError("Analytical checks failed")
            if managed["countSignatures"]!=native["countSignatures"]: raise ValueError("C#/C++ count contracts differ")
            report["countComparison"]={"matches":True,"cases":len(managed["countSignatures"])}
            if platform.system()=="Darwin" and (platform.machine()!="arm64" or managed["runtime"]["architecture"]!="Arm64" or managed["runtime"]["osArchitecture"]!="Arm64"):
                raise ValueError("Native Mac ARM64 required")
            # Measure the real dependency boundary; no extracted exception or namespace stub.
            names=["CaeMesh/Meshing/Transfinite/ThreeBlockMapping.cs",*sorted(expected),"CaeGlobals/ExceptionTools.cs"]
            project=work/"boundary/Boundary.csproj"; project.parent.mkdir()
            (project.parent/"NuGet.Config").write_bytes((HERE/"NuGet.Config").read_bytes())
            original_exception=project.parent/"ExceptionTools.cs"
            original_exception.write_bytes(baseline_exception)
            project.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework><EnableDefaultCompileItems>false</EnableDefaultCompileItems><NuGetAudit>false</NuGetAudit></PropertyGroup><ItemGroup>'+''.join('<Compile Include="'+str(original_exception if name=="CaeGlobals/ExceptionTools.cs" else ROOT/name)+'" />' for name in names)+'</ItemGroup></Project>')
            boundary=run(["dotnet","build",str(project),"--disable-build-servers","-v:minimal"],1)
            if "CS0103" not in boundary.stdout or "MessageBoxes" not in boundary.stdout:
                raise ValueError("Unexpected full mapping boundary")
            report["mappingBoundary"]={"sourceFiles":names,"measuredError":"CS0103: MessageBoxes in original ExceptionTools.cs","sourcePatches":False,"namespaceStubs":False}
        report["success"]=True
        report["limits"]=["Full C# mapping execution blocked by error-reporting dependency", "Original C++ vectors derive from upstream C#: not an independent oracle", "No CAD engine, live shell joint mesh, VTK render, solver, PMX or Windows comparison"]
    except (ValueError,KeyError,RuntimeError,OSError,subprocess.SubprocessError) as error:
        report["error"]=str(error).replace(str(ROOT),"<repository>").replace(temporary or "<unused>","<temporary>")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"success":report["success"],"vectors":report.get("upstreamVectors",{}).get("passed"),
                      "nativeChecks":report.get("nativeGeometry",{}).get("passed"),"managedChecks":report.get("managedCountsGrid",{}).get("passed"),"comparison":report.get("countComparison"),"error":report.get("error")}))
    return 0 if report["success"] else 1


if __name__=="__main__":
    raise SystemExit(main())

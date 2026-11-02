#!/usr/bin/env python3
"""Bounded PrePoMac review diagnostics; does not launch the application or a solver."""
import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

PIN = "fb5a89dba6ac975956d9001edf6d6756f18fe0ca"
REVIEWED = [
    "README.md", "CONTRIBUTING.md", "CaeGlobals/Tools.cs",
    "CaeGlobals/TypeSerializationSurrogate.cs", "PrePoMax/Controller.cs",
    "PrePoMax/Settings/SolverSettings.cs", "CaeJob/AnalysisJob.cs",
    "CaeModel/FileInOut/Output/CodeAster/CodeAsterFileWriter.cs",
    "CaeModel/FileInOut/Output/CodeAster/CodeAsterPostScript.cs",
    "macOS/Native/CodeAster/Dockerfile", "macOS/Native/CodeAster/build.sh",
    "macOS/Directory.Build.props", "macOS/WinFormsCompat/WinFormsCompat.csproj",
    "macOS/WinFormsCompat/Forms/CompatApplication.cs", "macOS/vtkControl/vtkControl.csproj",
    "macOS/vtkControl/Mac/Gl/OffscreenRenderer.cs", "macOS/vtkControl/Mac/Gl/RenderSurface.cs",
    "macOS/vtkControl/Mac/Gl/SceneRenderer.cs", "macOS/vtkControl/Mac/Vtk/Filters.cs",
    "macOS/vtkControl/Mac/Vtk/Interaction.cs", "macOS/vtkControl/Mac/Vtk/DataModel.cs",
    "macOS/vtkControl/Mac/Vtk/IO.cs", "macOS/vtkControl/Mac/Vtk/Rendering.cs", "macOS/vtkControl/Mac/Gl/GL.cs",
    "CaeMesh/Elements/FeElement.cs", "CaeMesh/Elements/3D/ParabolicTetraElement.cs",
    "macOS/GmshCommon/QMorph.cs", "macOS/Native/Win32Compat.c",
    "macOS/Native/NetGenMesher/CMakeLists.txt", "macOS/Native/NetGenMesher/Mesh.cpp",
    "macOS/Native/Mmg/build.sh", "macOS/build.sh", "macOS/run.sh",
    "macOS/make-app.sh", "macOS/bundle-deps.py", ".github/workflows/build.yml",
    ".github/workflows/release.yml", "assets_composites/plate-validation/plate_validation.py",
    "assets_composites/plate-validation/run_validation.sh", "Licenses/README.md",
]


def extract_method(source, signature):
    # Selected methods contain no brace characters in string literals.
    start = source.index(signature)
    brace = source.index("{", start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start:end]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--harness-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.checkout.resolve()
    pin = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if pin != PIN:
        raise SystemExit("Unreviewed source pin: " + pin)
    out = {"commit": pin, "scope": "source/isolated methods; no application or numerical solve", "sources": {}}
    for relative in REVIEWED:
        data = (root / relative).read_bytes()
        out["sources"][relative] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    out["lineCounts"] = {}
    for folder in ("macOS/WinFormsCompat", "macOS/DrawingCompat", "macOS/vtkControl", "macOS/Native/NetGenMesher"):
        paths = list((root / folder).rglob("*.cs" if folder != "macOS/Native/NetGenMesher" else "*.cpp"))
        out["lineCounts"][folder] = {"files": len(paths), "physicalLines": sum(len(p.read_text().splitlines()) for p in paths)}
    python_files = list((root / "macOS").rglob("*.py")) + list((root / "assets_composites/plate-validation").glob("*.py"))
    for path in python_files:
        ast.parse(path.read_text(), filename=str(path))
    out["pythonSyntaxFiles"] = [str(p.relative_to(root)) for p in python_files]
    shell_files = ["macOS/build.sh", "macOS/run.sh", "macOS/make-app.sh", "macOS/Native/build.sh",
        "macOS/Native/CodeAster/build.sh", "macOS/Native/NetGenMesher/build.sh", "macOS/Native/Mmg/build.sh",
        "assets_composites/plate-validation/run_validation.sh"]
    for relative in shell_files:
        subprocess.run(["bash", "-n", str(root / relative)], check=True)
    out["shellSyntaxFiles"] = shell_files
    # Load only definitions/constants of the author's analytical fixture. Do not invoke main/pmx.
    path = root / "assets_composites/plate-validation/plate_validation.py"
    tree = ast.parse(path.read_text())
    tree.body = [n for n in tree.body if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and
                 isinstance(n.value.func, ast.Name) and n.value.func.id == "main")]
    scope = {"__file__": str(path)}
    exec(compile(tree, str(path), "exec"), scope)
    out["analyticalFixturesOnly"] = {case: scope["analytic"](case) for case in ("NAVIER", "TENSION", "CANTILEVER")}
    for case, values in out["analyticalFixturesOnly"].items():
        assert math.isfinite(values["value"]) and abs(values["reserve"] - 2) < 1e-10, case
        a, d, _ = scope["abd"](case)
        assert all(abs(m[i][j] - m[j][i]) < 1e-8 for m in (a, d) for i in range(3) for j in range(3))
    # Postprocessor syntax and exact helper behavior, with controlled field fixtures.
    text = (root / "CaeModel/FileInOut/Output/CodeAster/CodeAsterPostScript.cs").read_text()
    python = text.split('public const string Text = @"', 1)[1].rsplit('";', 1)[0].replace('""', '"')
    tree = ast.parse(python)
    selected = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("_ppm_e", "_ppm_nodal")]
    helpers = {}
    exec(compile(ast.Module(body=selected, type_ignores=[]), "extracted-postprocessor", "exec"), helpers)
    class Field:
        def getValuesWithDescription(self, component, groups):
            return {"DX": ([1.0, 2.0], [[0, 1]]), "DY": ([3.0], [[0]]), "DZ": ([4.0, 5.0], [[0, 1]])}[component]
    out["postprocessorHelpersOnly"] = {"nan": helpers["_ppm_e"](float("nan")),
        "positiveInfinity": helpers["_ppm_e"](float("inf")),
        "negativeInfinity": helpers["_ppm_e"](float("-inf")),
        "componentCoverageFixture": helpers["_ppm_nodal"](Field(), ["DX", "DY", "DZ"])}
    # Linux-sensitive literal paths in the SDK project lists (not a build).
    mismatches = []
    for project in (root / "macOS").rglob("*.csproj"):
        for item in ET.parse(project).iter():
            include = item.get("Include", "")
            if not include.startswith("$(RepoRoot)") or "*" in include or ";" in include:
                continue
            relative = include[len("$(RepoRoot)"):].replace("\\", "/")
            if (root / relative).exists():
                parent = root
                for part in Path(relative).parts:
                    names = [p.name for p in parent.iterdir()]
                    if part not in names:
                        mismatches.append({"project": str(project.relative_to(root)), "include": relative})
                        break
                    parent /= part
    out["literalProjectCaseMismatches"] = mismatches
    # Generate a package-free harness around unchanged selected C# methods and minimal element type fixtures.
    tools = (root / "CaeGlobals/Tools.cs").read_text()
    writer = (root / "CaeModel/FileInOut/Output/CodeAster/CodeAsterFileWriter.cs").read_text()
    methods = [extract_method(writer, s) for s in (
        "private static int[] GetCorners(", "private static void GetMshElement(",
        "private static int GetFrdType(", "private static int[] GetFrdNodes(", "private static void WriteExport(")]
    capability = extract_method(tools, "public static bool CalculixHasSolver(")
    types = ["LinearTriangleElement", "ParabolicTriangleElement", "LinearQuadrilateralElement", "ParabolicQuadrilateralElement",
        "LinearTetraElement", "ParabolicTetraElement", "LinearHexaElement", "ParabolicHexaElement", "LinearWedgeElement", "ParabolicWedgeElement"]
    code = '''using System; using System.IO; using System.Text; using System.Linq; using System.Collections.Generic;
using System.Text.Json;
class FeElement { public int[] NodeIds; }
class CaeException : Exception { public CaeException(string m): base(m) {} }
'''
    code += "\n".join("class " + t + " : FeElement {}" for t in types)
    code += "\nclass Program { private static readonly Dictionary<string,bool> _calculixSolverSupport = new();\n" + capability
    code += "\n" + "\n".join(methods)
    code += '''
static void Main(string[] args) {
var dir=args[0]; Directory.CreateDirectory(dir); var bin=Path.Combine(dir,"fake-ccx");
var results=new Dictionary<string,object>();
results["missingExecutableAssumedSupported"]=CalculixHasSolver(bin,"PASTIX");
File.WriteAllText(bin,"the PASTIX library is not linked");
results["negativeMarkerDetected"]=!CalculixHasSolver(bin,"PASTIX");
File.WriteAllText(bin,"new executable without missing-library marker");
results["samePathReplacementStillCachedUnsupported"]=!CalculixHasSolver(bin,"PASTIX");
results["arbitraryFileAssumedPardisoSupported"]=CalculixHasSolver(bin,"PARDISO");
var rows=new List<object>();
foreach(var e in new FeElement[]{new ParabolicTriangleElement{NodeIds=Enumerable.Range(1,6).ToArray()},
new ParabolicQuadrilateralElement{NodeIds=Enumerable.Range(1,8).ToArray()},
new ParabolicTetraElement{NodeIds=Enumerable.Range(1,10).ToArray()},
new ParabolicHexaElement{NodeIds=Enumerable.Range(1,20).ToArray()},
new ParabolicWedgeElement{NodeIds=Enumerable.Range(1,15).ToArray()}}) {
GetMshElement(e,out int t,out int[] n); rows.Add(new {type=e.GetType().Name,input=e.NodeIds.Length,mshType=t,mshNodes=n,frdType=GetFrdType(e),frdNodes=GetFrdNodes(e)}); }
results["elementTranslation"]=rows;
var export=Path.Combine(dir,"review.export"); WriteExport(export,"/work","job with space");
results["exportFile"]=File.ReadAllLines(export);
results["processorCount"]=Environment.ProcessorCount;
results["os"]=System.Runtime.InteropServices.RuntimeInformation.OSDescription;
results["architecture"]=System.Runtime.InteropServices.RuntimeInformation.ProcessArchitecture.ToString();
Console.WriteLine(JsonSerializer.Serialize(results));
}}
'''
    args.harness_dir.mkdir(parents=True, exist_ok=True)
    (args.harness_dir / "Program.cs").write_text(code)
    (args.harness_dir / "Review.csproj").write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework><NuGetAudit>false</NuGetAudit></PropertyGroup></Project>')
    (args.harness_dir / "NuGet.Config").write_text('<configuration><packageSources><clear /></packageSources></configuration>')
    out["harnessSourceSha256"] = hashlib.sha256(code.encode()).hexdigest()
    out["harnessScope"] = "exact extracted methods; minimal type fixtures, no application, FE assembly, matrix solve or renderer"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"commit":pin,"fingerprints":len(out["sources"]),"lineCounts":out["lineCounts"],
        "caseMismatches":len(mismatches),"analyticalFixtures":out["analyticalFixturesOnly"]}, indent=2))


if __name__ == "__main__":
    main()

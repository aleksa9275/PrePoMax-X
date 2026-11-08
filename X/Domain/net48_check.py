#!/usr/bin/env python3
"""Compile the ORIGINAL Windows (net48, C# 7.3) sources of selected assemblies
from macOS/Linux, using .NET Framework reference assemblies.

PrePoMax-X edits original files minimally (D062) and moves Windows-only code to
*.WinForms.cs / *.Windows.cs partials. This check proves those edits still
compile in the original Windows build without needing Visual Studio. Assemblies
that depend on native C++/CLI (GmshCommon) or ActiViz cannot be compiled here;
they are verified on Windows.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NS = {"m": "http://schemas.microsoft.com/developer/msbuild/2003"}
PACKAGES = {
    "CaeGlobals": [("ncalc", "1.3.8"), ("UnitsNet", "4.89.1"), ("ExtendedNumerics.BigDecimal", "2025.1001.2.129"),
                   ("Parlot", "0.0.28")],
    "CaeJob": [],
}
REFERENCES = ["System.Windows.Forms", "System.Design", "System.Drawing.Design", "System.Management", "System.Numerics",
              "System.Runtime.Serialization", "Microsoft.CSharp", "System.Drawing"]


def project(name: str, folder: Path) -> Path:
    original = ROOT / name / f"{name}.csproj"
    root = ET.parse(original).getroot()
    compile_items = [e.get("Include").replace("\\", "/") for e in root.iterfind(".//m:Compile", NS)]
    resources = [e.get("Include").replace("\\", "/") for e in root.iterfind(".//m:EmbeddedResource", NS)]
    lines = ['<Project Sdk="Microsoft.NET.Sdk">', "  <PropertyGroup>",
             f"    <TargetFramework>net48</TargetFramework><LangVersion>7.3</LangVersion><AssemblyName>{name}</AssemblyName>",
             "    <EnableDefaultCompileItems>false</EnableDefaultCompileItems><GenerateAssemblyInfo>false</GenerateAssemblyInfo>",
             "    <AllowUnsafeBlocks>true</AllowUnsafeBlocks><NoWarn>CS0618;CS0168;CS0219;CS0414;CS0649;CS0169;CS0162;CS0108;CS0114;CS0067</NoWarn>",
             "  </PropertyGroup>", "  <ItemGroup>"]
    lines += [f'    <Compile Include="{ROOT / name / c}" />' for c in compile_items]
    lines += [f'    <EmbeddedResource Include="{ROOT / name / r}" />' for r in resources]
    lines.append('    <PackageReference Include="Microsoft.NETFramework.ReferenceAssemblies" Version="1.0.3" />')
    lines += [f'    <PackageReference Include="{p}" Version="{v}" />' for p, v in PACKAGES[name]]
    lines += [f'    <Reference Include="{r}" />' for r in REFERENCES]
    if name != "CaeGlobals":
        lines.append(f'    <ProjectReference Include="{folder / "CaeGlobals" / "CaeGlobals.csproj"}" />')
    lines += ["  </ItemGroup>", "</Project>", ""]
    path = folder / name / f"{name}.csproj"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("assemblies", nargs="*", default=list(PACKAGES))
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="prepomaxx-net48-") as temp:
        folder = Path(temp)
        if "CaeGlobals" not in args.assemblies:
            project("CaeGlobals", folder)
        failed = False
        for name in args.assemblies:
            path = project(name, folder)
            done = subprocess.run(["dotnet", "build", str(path), "-v:q", "-clp:NoSummary"], capture_output=True, text=True)
            errors = sorted({line.split("[")[0].strip() for line in done.stdout.splitlines() if " error " in line})
            print(f"{name}: {'ok' if done.returncode == 0 else 'FAILED'}")
            for line in errors:
                print("  " + line.replace(str(ROOT) + "/", ""))
            failed |= done.returncode != 0
        return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

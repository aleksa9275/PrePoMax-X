#!/usr/bin/env python3
"""Read-only, standard-library project graph and portability signal inventory.

Run from any directory inside the checkout. Writes JSON only to stdout. Signals
include comments and unused imports: they are review leads, not portability proofs.
"""
from collections import Counter
from pathlib import Path
import json
import re
import subprocess
import xml.etree.ElementTree as ET

root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
tracked = [name for name in tracked if name]
ns = {"m": "http://schemas.microsoft.com/developer/msbuild/2003"}
projects = []
for name in sorted(tracked):
    if not name.endswith((".csproj", ".vcxproj")):
        continue
    tree = ET.parse(root / name)
    def values(tag):
        return [item.attrib.get("Include", item.text) for item in tree.findall(".//m:" + tag, ns)]
    projects.append({"path": name, "framework": values("TargetFrameworkVersion"),
                     "references": values("Reference"), "project_references": values("ProjectReference"),
                     "platforms": values("PlatformTarget"), "toolsets": values("PlatformToolset")})
patterns = {
    "winforms": r"System\.Windows\.Forms|\bApplication\.DoEvents\(",
    "windows_api": r"user32\.dll|kernel32\.dll|hid\.dll|Microsoft\.Win32|System\.Management|WindowsIdentity|PipeSecurity|DirectorySecurity",
    "wpf": r"System\.Windows\.(Input|Media)|using System\.Windows;|WindowsBase",
    "drawing_operations": r"\b(Bitmap|Graphics|Font|Image|Icon)\b",
    "vtk": r"Kitware|using vtkControl|\bvtk[A-Z]\w*",
    "gmsh_interop": r"GmshCommon|msclr|public ref class",
    "legacy_serialization": r"BinaryFormatter|\.DumpToFile\(|\.DumpToStream\(|LoadDumpFromFile|DeepClone\(",
    "process": r"ProcessStartInfo|Process\.Start|ChildProcessJob|KillAllProcessesSpawnedBy",
    "native_import": r"DllImport\(",
}
compiled = {key: re.compile(value) for key, value in patterns.items()}
signals, counts, source_counts = {}, {}, Counter()
for name in sorted(tracked):
    if not name.endswith((".cs", ".cpp", ".h", ".csproj", ".vcxproj", ".targets")):
        continue
    text = (root / name).read_text(encoding="utf-8-sig", errors="replace")
    source_counts[name.split("/")[0]] += 1
    hits = {}
    for key, regex in compiled.items():
        lines = [i for i, line in enumerate(text.splitlines(), 1) if regex.search(line)]
        if lines:
            hits[key] = lines
            counts.setdefault(name.split("/")[0], Counter())[key] += 1
    if hits:
        signals[name] = hits
result = {"upstream_baseline": subprocess.check_output(["git", "rev-parse", "upstream/HEAD"], cwd=root, text=True).strip(),
          "tracked_files": len(tracked), "scanned_files_by_directory": dict(source_counts),
          "pattern_definitions": patterns, "projects": projects,
          "signal_file_counts_by_directory": {key: dict(value) for key, value in counts.items()},
          "signal_lines": signals,
          "limitations": "Static textual inventory; includes unused imports/comments/generated code; no compile or runtime guarantee."}
print(json.dumps(result, indent=2, sort_keys=True))

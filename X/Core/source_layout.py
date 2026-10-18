"""Exact, reviewable source moves for the portable mesh-deck boundary.

This module verifies checked-in source; it does not generate application code at
build time. Original method bodies remain in the original assemblies/net48 build.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET

BASELINE = "de8f73032a72746e3d6d9afd53d9fbd289eb310a"
INP = "CaeModel/FileInOut/Input/InpModel/InpFileReader.cs"
ATTRIBUTE = "CaeGlobals/DynamicTypeDescriptor/DynamicTypeDescriptor.cs"
PARSING = "CaeModel/FileInOut/Input/InpModel/InpFileReader.MeshParsing.cs"
ATTRIBUTE_FILE = "CaeGlobals/DynamicTypeDescriptor/StandardValueAttribute.cs"
UNCHANGED = ["CaeGlobals/CommonClasses/NamedClass.cs", "CaeMesh/InpElementSet.cs",
             "CaeMesh/Enums/ConvertPyramidsToEnum.cs",
             "CaeModel/FileInOut/Output/Calculix/Keywords/CalculixKeyword.cs",
             "CaeModel/FileInOut/Output/Calculix/Keywords/ModelDefinition/CalElement.cs",
             "CaeModel/FileInOut/Output/Calculix/Keywords/Step/Load/CalLoadEnums.cs"]
ADDED = ["CaeModel/FileInOut/Input/InpModel/InpMeshData.cs",
         "CaeModel/FileInOut/Input/InpModel/InpFileReader.MeshData.cs",
         "CaeModel/FileInOut/Output/Calculix/MeshDeckWriter.cs"]


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("Source-move anchor changed: " + old[:90])
    return text.replace(old, new, 1)


def original(root, revision, path):
    return subprocess.check_output(["git", "show", revision + ":" + path], cwd=root).decode("utf-8")


def render(inp, attribute):
    """Only mechanical extraction and narrow set-name lookup parameterization."""
    changed = inp
    members = []

    def move(start, end):
        nonlocal changed
        a = changed.index(start)
        b = changed.index(end, a)
        block = changed[a:b]
        members.append(block)
        changed = changed[:a] + changed[b:]
        return block

    move("        private delegate FeElement ElementReader", "        private static HashSet<string> _knownKeywords")
    callback = "        private static Action<string> WriteDataToOutputStatic;\n"
    changed = replace_once(changed, callback, "")
    members.append(callback)
    move("        static public List<string> Errors", "\n\n        // Methods")
    move("        private static string[][] GetDataSets", "        //\n        private static int[] GetKeywordIndices")

    # Split the existing AddNodes into coordinate decoding and the legacy FeNodeSet wrapper.
    a = changed.index("        private static void AddNodes(")
    b = changed.index("        private static void AddElements(", a)
    add_nodes = changed[a:b]
    split = add_nodes.index("            //\n            if (nodeSetName != null && ids.Count > 0)")
    node_body = add_nodes[add_nodes.index("        {\n") + 10:split]
    node_body = replace_once(node_body, "            HashSet<int> ids = new HashSet<int>();", "            ids = new HashSet<int>();")
    node_body = replace_once(node_body, "            string nodeSetName = null;", "            nodeSetName = null;")
    members.append("        private static void AddNodeCoordinates(string[] lines, Dictionary<int, FeNode> nodes,\n"
                   "                                               out string nodeSetName, out HashSet<int> ids)\n"
                   "        {\n" + node_body + "        }\n")
    signature = add_nodes[:add_nodes.index("        {\n") + 10]
    wrapper = signature + "            string nodeSetName;\n            HashSet<int> ids;\n"
    wrapper += "            AddNodeCoordinates(lines, nodes, out nodeSetName, out ids);\n" + add_nodes[split:]
    changed = changed[:a] + wrapper + changed[b:]
    move("        private static void AddElements(", "        // Part name")

    # Preserve mesh/part lookup in the legacy wrapper; raw parsing receives only a label resolver.
    a = changed.index("        private static void GetNodeOrElementSet(")
    b = changed.index("        // Surface", a)
    set_method = changed[a:b]
    core_set = replace_once(set_method,
        "private static void GetNodeOrElementSet(string keywordName, string[] lines, FeMesh mesh, out string name, out int[] ids)",
        "private static void GetNodeOrElementSetData(string keywordName, string[] lines,\n"
        "                                                    Func<string, string, int[]> resolveSet, out string name, out int[] ids)")
    core_set = replace_once(core_set, "                    FeNodeSet nodeSet;\n                    FeElementSet elementSet;\n                    BasePart part;\n", "")
    start = core_set.index('                                if (keywordName == "NSET"')
    end = core_set.index("                            }\n                        }", start)
    core_set = core_set[:start] + (
        "                                int[] resolvedIds = resolveSet(keywordName, setName);\n"
        "                                if (resolvedIds != null) setIds.AddRange(resolvedIds);\n"
        "                                else WriteDataToOutputStatic(\"The set named '\" + setName + \"' was not found.\");\n"
    ) + core_set[end:]
    members.append(core_set)
    wrapper = set_method[:set_method.index("        {\n") + 10] + '''            GetNodeOrElementSetData(keywordName, lines, (kind, setName) =>
            {
                FeNodeSet nodeSet;
                FeElementSet elementSet;
                BasePart part;
                if (kind == "NSET" && mesh.NodeSets.TryGetValue(setName, out nodeSet)) return nodeSet.Labels;
                if (kind == "ELSET" && mesh.ElementSets.TryGetValue(setName, out elementSet)) return elementSet.Labels;
                if (kind == "ELSET" && mesh.Parts.TryGetValue(setName, out part)) return part.Labels;
                return null;
            }, out name, out ids);
        }
'''
    changed = changed[:a] + wrapper + changed[b:]
    move("        //  LINEAR ELEMENTS", "        private static void AddError(")
    a = changed.index("        private static void AddError(")
    b = changed.index("        private static void AddWarning(", a)
    end = changed.index("        }\n", b) + len("        }\n")
    members.append(changed[a:end])
    changed = changed[:a] + changed[end:]
    changed = replace_once(changed, "    [Serializable]\n    static public class InpFileReader", "    static public partial class InpFileReader")
    header = inp[:inp.index("using System;")]
    parsing = header + "using System;\nusing System.Collections.Generic;\nusing System.Linq;\nusing CaeMesh;\n\n"
    parsing += "namespace FileInOut.Input\n{\n    [Serializable]\n    static public partial class InpFileReader\n    {\n"
    parsing += "\n".join(members) + "    }\n}\n"

    a = attribute.index("    [AttributeUsage(AttributeTargets.Field, AllowMultiple = false, Inherited = true)]\n    public class StandardValueAttribute")
    b = attribute.index("    public class StandardValueEditor", a)
    body = attribute[a:b]
    attr_header = attribute[:attribute.index("using CaeGlobals;")]
    standalone = attr_header + "using System;\nusing System.Collections;\nusing System.Reflection;\n\n"
    standalone += "// Extracted unchanged from DynamicTypeDescriptor.cs; original framework references:\n"
    standalone += "// http://www.codeproject.com/Articles/189521/Dynamic-Properties-for-PropertyGrid\n"
    standalone += "// https://www.codeproject.com/Articles/415070/Dynamic-Type-Description-Framework-for-PropertyGri\n"
    standalone += "namespace DynamicTypeDescriptor\n{\n" + body + "}\n"
    return {INP: changed, PARSING: parsing, ATTRIBUTE: attribute[:a] + attribute[b:], ATTRIBUTE_FILE: standalone}


def verify_layout(root, revision=BASELINE):
    expected = render(original(root, revision, INP), original(root, revision, ATTRIBUTE))
    baseline = render(original(root, BASELINE, INP), original(root, BASELINE, ATTRIBUTE))
    if expected != baseline:
        raise ValueError("Upstream mesh parser/attribute boundary changed; review source extraction")
    for path, text in expected.items():
        if (root / path).read_bytes() != text.encode("utf-8"):
            raise ValueError("Mechanical mesh source extraction changed: " + path)
    for path in UNCHANGED:
        data = original(root, revision, path).encode("utf-8")
        if data != (root / path).read_bytes() or data != original(root, BASELINE, path).encode("utf-8"):
            raise ValueError("Mesh workflow engineering source changed: " + path)
    return expected


def compiled_paths():
    return UNCHANGED + [PARSING, ATTRIBUTE_FILE] + ADDED


def source_rows(root):
    verify_layout(root)
    manifest = json.loads((root / "X/Core/workflow-sources.json").read_text())
    if manifest["baseline"] != BASELINE or {row["path"] for row in manifest["sources"]} != set(compiled_paths()):
        raise ValueError("Mesh workflow source closure changed")
    rows = []
    for item in manifest["sources"]:
        path = item["path"]
        data = (root / path).read_bytes()
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise ValueError("Reviewed mesh workflow source changed: " + path)
        rows.append(dict(item))
    ns = {"m": "http://schemas.microsoft.com/developer/msbuild/2003"}
    for owner, names in {"CaeGlobals": [ATTRIBUTE_FILE], "CaeModel": [PARSING] + ADDED}.items():
        legacy = ET.parse(root / owner / (owner + ".csproj"))
        items = [item.attrib.get("Include") for item in legacy.findall(".//m:Compile", ns)]
        for path in names:
            if items.count(path[len(owner) + 1:].replace("/", "\\")) != 1:
                raise ValueError("Legacy project must include separated source exactly once: " + path)
    return rows

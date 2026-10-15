#!/usr/bin/env python3
"""Offline native identity/header audit; never executes a vendored binary."""
import argparse
import hashlib
import json
import platform
import re
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "de8f73032a72746e3d6d9afd53d9fbd289eb310a"
SDK = "ThirdParty/gmsh-4.13.0-Windows64-sdk"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def binary_identity(path):
    data = path.read_bytes()
    result = {"path": path.relative_to(ROOT).as_posix(), "bytes": len(data),
              "sha256": digest(data), "format": "unknown"}
    if data.startswith(b"MZ") and len(data) >= 64:
        offset = struct.unpack_from("<I", data, 60)[0]
        if offset + 26 <= len(data) and data[offset:offset + 4] == b"PE\0\0":
            machine = struct.unpack_from("<H", data, offset + 4)[0]
            result.update(format="PE/COFF", machine=hex(machine),
                          architecture={0x8664: "x64", 0x14c: "x86", 0xaa64: "ARM64"}.get(machine, "unknown"),
                          optional_header_magic=hex(struct.unpack_from("<H", data, offset + 24)[0]))
    elif data.startswith(b"!<arch>\n"):
        result["format"] = "ar archive (inspect member objects separately)"
    return result


def run(argv):
    completed = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=60)
    return {"command": argv, "exit_code": completed.returncode,
            "stdout": completed.stdout, "stderr": completed.stderr}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    selected = [ROOT / SDK / "lib/gmsh-4.13.dll", ROOT / "ThirdParty/netgen/NetGenMesher.exe",
                ROOT / "ThirdParty/netgen/nglib.dll", ROOT / "ThirdParty/quadwild-bimdf/quadwild.exe",
                ROOT / "ThirdParty/quadwild-bimdf/quad_from_patches.exe"]
    selected += sorted((ROOT / "ThirdParty/netgen").glob("TK*.dll"))
    selected += sorted((ROOT / "ThirdParty/QuadMesher/lib").rglob("*.lib"))
    selected += sorted((ROOT / "ThirdParty/mmg").glob("*.exe"))
    binaries = [binary_identity(p) for p in selected]
    source_paths = ["GmshCommon/GmshCommon.h", "GmshCommon/QMorph.h", "GmshCommon/GmshCommon.vcxproj",
                    f"{SDK}/include/gmsh.h", f"{SDK}/include/gmsh.h_original", f"{SDK}/include/gmshc.h",
                    "ThirdParty/QuadMesher/include/qmorph/qmorph.h",
                    "ThirdParty/QuadMesher/include/qmorph/qmorph_gmsh.h",
                    "ThirdParty/QuadMesher/THIRD_PARTY_NOTICES.md", "ThirdParty/netgen/README.md",
                    "ThirdParty/quadwild-bimdf/README.md", "Licenses/quadwild/NOTICE.md", "Licenses/README.md",
                    "PrePoMax/Meshing/Base/IMesherRunner.cs", "PrePoMax/Common/ExecutableJobRunner.cs",
                    "GmshCaller/Program.cs", "CaeMesh/Meshing/QuadWild/QuadWildRuntime.cs"]
    sources = []
    for name in source_paths:
        original = subprocess.run(["git", "show", f"{BASELINE}:{name}"], cwd=ROOT, capture_output=True, check=True).stdout
        actual = (ROOT / name).read_bytes()
        sources.append({"path": name, "sha256": digest(actual), "baseline_sha256": digest(original),
                        "matches_baseline": actual == original})
    claims = []
    actual_hashes = {Path(item["path"]).name: item["sha256"] for item in binaries}
    for name in ["Licenses/quadwild/NOTICE.md", "ThirdParty/quadwild-bimdf/README.md"]:
        for declared, binary in re.findall(r"([A-Fa-f0-9]{64})\s+(quadwild\.exe|quad_from_patches\.exe)", (ROOT / name).read_text()):
            claims.append({"notice": name, "binary": binary, "declared_sha256": declared.lower(),
                           "actual_sha256": actual_hashes[binary], "matches": declared.lower() == actual_hashes[binary]})
    wrapper = (ROOT / "GmshCommon/GmshCommon.h").read_text()
    wrapper = re.sub(r"/\*.*?\*/|//[^\n]*", "", wrapper, flags=re.S)
    calls = sorted(set(re.findall(r"\bgmsh::((?:\w+::)*\w+)\s*\(", wrapper)))
    compiler = shutil.which("clang++")
    c_compiler = shutil.which("clang")
    measurements = []
    if not compiler or not c_compiler:
        raise RuntimeError("Clang C and C++ compilers are required for measured header boundaries")
    with tempfile.TemporaryDirectory(prefix="prepomaxx-native-") as directory:
        temporary = Path(directory)
        c_probe = temporary / "c-api.c"
        c_probe.write_text('#include "gmshc.h"\n'
                           '_Static_assert(sizeof(size_t) == sizeof(void *), "size_t pointer width");\n'
                           'void signatures(void) {\n'
                           '  int ierr = 0; gmshInitialize(0, 0, 0, 0, &ierr);\n'
                           '  void *p = gmshMalloc(8); gmshFree(p);\n'
                           '  (void)&gmshModelOccFragment; (void)&gmshModelMeshGetNodes;\n'
                           '  (void)&gmshModelMeshGetElements; (void)&gmshModelMeshSetSizeCallback;\n'
                           '  gmshFinalize(&ierr);\n}\n')
        cpp_probe = temporary / "cpp-api.cpp"
        cpp_probe.write_text('#include "gmsh.h"\n#include "qmorph/qmorph_gmsh.h"\n'
                             'static_assert(sizeof(std::size_t) == sizeof(void *), "tag pointer width");\n'
                             'void signatures() {\n'
                             '  gmsh::initialize(); gmsh::model::mesh::generate(2); gmsh::finalize();\n'
                             '  qm::InputMesh input; qm::Options options;\n'
                             '  (void)qm::qmorph(input, options);\n'
                             '  (void)qmg::quadMeshSurfaces(std::vector<int>{1}, options);\n}\n')
        cli_probe = temporary / "cli.cpp"
        cli_probe.write_text('#include "GmshCommon.h"\n')
        for label, command, expect_success in [
            ("gmsh-c-api-syntax", [c_compiler, "-std=c11", "-Werror", "-fsyntax-only", "-I", str(ROOT / SDK / "include"), str(c_probe)], True),
            ("gmsh-qmorph-cpp-declarations", [compiler, "-std=c++17", "-Werror", "-fsyntax-only", "-I", str(ROOT / SDK / "include"), "-I", str(ROOT / "ThirdParty/QuadMesher/include"), str(cpp_probe)], True),
            ("original-cpp-cli-boundary", [compiler, "-std=c++17", "-fsyntax-only", "-ferror-limit=3", "-I", str(ROOT / SDK / "include"), "-I", str(ROOT / "GmshCommon"), str(cli_probe)], False),
        ]:
            item = run(command)
            item.update(label=label, expected_success=expect_success,
                        outcome_matches_expected=(item["exit_code"] == 0) == expect_success)
            if not expect_success:
                item["outcome_matches_expected"] = (item["exit_code"] != 0 and
                    "msclr\\marshal_cppstd.h" in item["stderr"] and "file not found" in item["stderr"])
            # Preserve the small probe so the recorded temporary command can be reproduced.
            item["probe_source"] = Path(command[-1]).read_text()
            measurements.append(item)
    result = {"baseline": BASELINE, "host": {"os": platform.system(), "architecture": platform.machine()},
              "audit_tool_sha256": digest(Path(__file__).read_bytes()),
              "compiler": run([compiler, "--version"]),
              "tooling": {tool: shutil.which(tool) for tool in ["cmake", "ninja", "clang", "clang++"]},
              "binaries": binaries, "sources": sources, "quadwild_checksum_claims": claims,
              "gmsh_wrapper_calls": calls, "gmsh_wrapper_call_count": len(calls), "compile_measurements": measurements,
              "limits": ["Header syntax/declarations only: no linking or native mesher execution",
                         "Wrapper call list is a textual inventory, not executed API coverage",
                         "Binary hashes do not establish source-to-binary correspondence",
                         "No original files modified; no native tool substituted"]}
    result["checks_passed"] = all(s["matches_baseline"] for s in sources) and all(m["outcome_matches_expected"] for m in measurements)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"checks_passed": result["checks_passed"], "binary_count": len(binaries),
                      "wrapper_call_count": len(calls), "checksum_mismatches": [x for x in claims if not x["matches"]],
                      "measurements": [{k: m[k] for k in ["label", "exit_code", "outcome_matches_expected"]} for m in measurements]}))
    return 0 if result["checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

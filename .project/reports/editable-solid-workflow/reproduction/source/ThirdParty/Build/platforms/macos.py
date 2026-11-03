"""macOS compiler defaults and Mach-O runtime inspection only."""
from pathlib import Path
import subprocess


def defaults(blas=None):
    return {"cc": "gcc-16", "fc": "gfortran", "blas": blas or Path("/opt/homebrew/opt/openblas/lib/libopenblas.dylib")}


def inspect(binary, architecture, sha):
    description = subprocess.check_output(["file", binary], text=True).strip()
    if architecture != "Arm64" or "arm64" not in description or "Mach-O" not in description:
        raise ValueError("Native Mach-O architecture differs from target")
    runtime, pending, unresolved, rpaths = {}, [binary], [], []
    def expand(name, loader):
        return name.replace("@loader_path", str(loader.parent)).replace("@executable_path", str(binary.parent))
    while pending:
        file = pending.pop()
        lines = subprocess.check_output(["otool", "-l", file], text=True).splitlines()
        for i, line in enumerate(lines):
            if line.strip() == "cmd LC_RPATH":
                for following in lines[i+1:i+4]:
                    if following.strip().startswith("path "):
                        rpaths.append(expand(following.strip()[5:].split(" (offset", 1)[0], file))
        for line in subprocess.check_output(["otool", "-L", file], text=True).splitlines()[1:]:
            name = line.strip().split(" (", 1)[0]
            if name.startswith(("/usr/lib/", "/System/")):
                continue
            candidate = Path(expand(name, file))
            if name.startswith("@rpath/"):
                candidate = next((Path(d) / name[7:] for d in rpaths if (Path(d) / name[7:]).is_file()), candidate)
            if not candidate.is_file():
                unresolved.append(name)
                continue
            if str(candidate) not in runtime:
                runtime[str(candidate)] = sha(candidate)
                pending.append(candidate.resolve())
    if unresolved:
        raise ValueError("Unresolved runtime paths: " + str(unresolved))
    return {"file": description, "externalRuntimes": runtime, "resolvedRpaths": list(dict.fromkeys(rpaths))}

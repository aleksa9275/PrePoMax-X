"""GNU/Linux compiler defaults and ELF runtime inspection only."""
from pathlib import Path
import subprocess


def defaults(blas=None):
    if blas is None:
        directory = subprocess.check_output(["pkg-config", "--variable=libdir", "openblas"], text=True).strip()
        if not directory:
            raise ValueError("pkg-config did not identify native OpenBLAS")
        blas = Path(directory) / "libopenblas.so"
    if not blas.is_file():
        raise ValueError("Install native OpenBLAS development libraries or provide --blas")
    return {"cc": "gcc", "fc": "gfortran", "blas": blas}


def inspect(binary, architecture, sha):
    description = subprocess.check_output(["file", binary], text=True).strip()
    marker = {"X64": "x86-64", "Arm64": "aarch64"}[architecture]
    if "ELF 64-bit" not in description or marker not in description:
        raise ValueError("Native ELF architecture differs from target")
    output = subprocess.check_output(["ldd", binary], text=True)
    runtime = {}
    for line in output.splitlines():
        if "not found" in line:
            raise ValueError("Unresolved ELF runtime: " + line.strip())
        value = line.split("=>", 1)[-1].strip().split(" (", 1)[0]
        if value.startswith("/"):
            path = Path(value)
            if not path.is_file():
                raise ValueError("Missing ELF runtime: " + value)
            runtime[str(path)] = sha(path)
    if not runtime:
        raise ValueError("No ELF runtime closure found")
    return {"file": description, "externalRuntimes": runtime,
        "libc": subprocess.check_output(["ldd", "--version"], text=True).splitlines()[0],
        "distribution": Path("/etc/os-release").read_text() if Path("/etc/os-release").is_file() else None}

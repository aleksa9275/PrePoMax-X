"""Single-part CAD conversion through the original NetGenMesher command protocol."""
import hashlib
import json
import os
from pathlib import Path
import platform
import stat
import subprocess


IMPORT_COMMANDS = {
    ".step": "STEP_ASSEMBLY_SPLIT_TO_COMPOUNDS",
    ".stp": "STEP_ASSEMBLY_SPLIT_TO_COMPOUNDS",
    ".brep": "BREP_ASSEMBLY_SPLIT_TO_COMPOUNDS",
}
CROSSOVER_WINE = Path("/Applications/CrossOver.app/Contents/SharedSupport/CrossOver/bin/wine")
REFERENCE_RECEIPT = (Path(__file__).resolve().parents[2] /
                     ".project/reports/l-bracket-cad-reference/verification.json")
MAX_CAD_BYTES = 16 * 1024 * 1024
MAX_VIS_BYTES = 1024 * 1024


def file_sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require_output(path, maximum):
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= maximum:
        raise ValueError(f"Missing, invalid or oversized CAD output: {path.name}")


def run_stage(command, work, log_name):
    log = work / log_name
    try:
        with log.open("xb") as stream:
            result = subprocess.run(command, cwd=work, stdout=stream, stderr=subprocess.STDOUT, timeout=60)
    except subprocess.TimeoutExpired as error:
        raise ValueError(f"{log.stem} exceeded the 60-second CAD conversion limit.") from error
    if result.returncode:
        with log.open("rb") as stream:
            stream.seek(max(0, log.stat().st_size - 2048))
            detail = stream.read().decode("utf-8", errors="replace").strip()
        raise ValueError(f"{log.stem} exited with status {result.returncode}. {detail}")


def convert_cad(source, work, command, *, windows_paths=False):
    """Return the split BREP and VIS from a new workspace, after both stages succeed."""
    suffix = source.suffix.lower()
    if suffix not in IMPORT_COMMANDS:
        raise ValueError("Choose a STEP or BREP file.")
    if not source.is_file():
        raise ValueError("CAD input must be a regular file.")
    work = work.resolve()
    work.mkdir()
    staged = work / ("source" + suffix)
    with source.open("rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("CAD input must be a regular file.")
        data = stream.read(MAX_CAD_BYTES + 1)
    if not 0 < len(data) <= MAX_CAD_BYTES:
        raise ValueError("CAD input must be nonempty and no larger than 16 MiB.")
    staged.write_bytes(data)

    def tool_path(path):
        return "Z:" + str(path).replace("/", "\\") if windows_paths else str(path)

    split_base = work / "part.brep"
    run_stage([*command, IMPORT_COMMANDS[suffix], tool_path(staged), tool_path(split_base)], work, "split.log")
    parts = list(work.glob("part*.brep"))
    if len(parts) != 1:
        raise ValueError(f"Expected one CAD part from the split, got {len(parts)}.")
    brep, = parts
    require_output(brep, MAX_CAD_BYTES)
    vis = work / "geometry.vis"
    if vis.exists() or vis.is_symlink():
        raise ValueError("The split unexpectedly wrote the VIS output.")
    run_stage([*command, "BREP_VISUALIZATION", tool_path(brep), tool_path(vis), "0.01", "1", "0.26"],
              work, "visualize.log")
    require_output(vis, MAX_VIS_BYTES)
    require_output(staged, MAX_CAD_BYTES)
    if file_sha256(staged) != hashlib.sha256(data).hexdigest():
        raise ValueError("The CAD tool modified its staged input.")
    return brep, vis


class ReferenceCadTool:
    """Explicit local compatibility tool using the pinned 3.0.0 runtime."""

    def __init__(self, runtime, bottle, receipt=REFERENCE_RECEIPT, wine=CROSSOVER_WINE):
        if platform.system() != "Darwin":
            raise ValueError("The CrossOver CAD reference is available on macOS.")
        if not bottle or bottle.startswith("-"):
            raise ValueError("Supply the name of an existing CrossOver bottle.")
        self.runtime = runtime.resolve()
        self.expected = json.loads(receipt.read_text())["bundledNetgen"]["releaseFileHashes"]
        if not wine.is_file():
            raise ValueError(f"CrossOver launcher is missing: {wine}")
        self.command = (str(wine.resolve()), "--bottle", bottle, "--no-gui",
                        str(self.runtime / "NetGenMesher.exe"))
        self.verify_runtime()

    def verify_runtime(self):
        files = {path.name: path for path in self.runtime.iterdir() if path.suffix.lower() in {".exe", ".dll"}}
        if files.keys() != self.expected.keys():
            raise ValueError("CAD reference runtime must contain the 38 original Netgen executable and DLL files.")
        for name, digest in self.expected.items():
            path = files[name]
            if path.is_symlink() or not path.is_file() or file_sha256(path) != digest:
                raise ValueError(f"CAD reference runtime hash mismatch: {name}")

    def convert(self, source, work):
        self.verify_runtime()
        outputs = convert_cad(source, work, self.command, windows_paths=True)
        self.verify_runtime()
        return outputs

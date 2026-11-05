"""CAD conversion through the original NetGenMesher command protocol."""
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import stat
import subprocess
import time


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
MAX_CAD_PARTS = 32
MAX_TOTAL_VIS_BYTES = 16 * 1024 * 1024


class NativeCadTool:
    """Explicit native research runtime, checked before and after conversion."""
    description = "Native Netgen 5.3.1 / OCCT 8.0.1"

    def __init__(self, runtime):
        self.runtime = Path(runtime).resolve()
        self.receipt = self.runtime / "build-receipt.json"
        self.receipt_sha256 = file_sha256(self.receipt)
        data = json.loads(self.receipt.read_text())
        if data.get("nativeHost") != {"system": platform.system(), "machine": platform.machine()}:
            raise ValueError("The native CAD runtime was built for another host architecture.")
        if (data.get("netgenRevision") != "c5ecb0ba3782b91649e06823e858480f6fe33aeb"
                or data.get("occt", {}).get("revision") != "b8f597c677811d1f9f4d8a97f5ae2825c0353a42"):
            raise ValueError("The native CAD runtime has another source identity.")
        self.expected = {}
        for row in data["runtimeFiles"]:
            path = Path(row["path"])
            if (not path.parts or path.is_absolute() or ".." in path.parts or row["path"] in self.expected
                    or path.parts[0] not in ("bin", "lib")):
                raise ValueError("Invalid native CAD runtime inventory.")
            self.expected[row["path"]] = row["sha256"]
        if "bin/NetGenMesher" not in self.expected or not any(p.startswith("lib/libnglib.") for p in self.expected):
            raise ValueError("Incomplete native CAD runtime inventory.")
        self.command = (str(self.runtime / "bin/NetGenMesher"),)
        self.verify_runtime()

    def verify_runtime(self):
        if self.receipt.is_symlink() or file_sha256(self.receipt) != self.receipt_sha256:
            raise ValueError("Native CAD build receipt changed.")
        files = {p.relative_to(self.runtime).as_posix(): p
                 for folder in ("bin", "lib") for p in (self.runtime / folder).rglob("*") if p.is_file() or p.is_symlink()}
        if files.keys() != self.expected.keys():
            raise ValueError("Native CAD runtime inventory changed.")
        for name, digest in self.expected.items():
            path = files[name]
            if path.is_symlink() or file_sha256(path) != digest:
                raise ValueError("Native CAD runtime hash mismatch: " + name)

    def convert(self, source, work, *, cancel=None):
        self.verify_runtime()
        outputs = convert_cad(source, work, self.command, cancel=cancel)
        self.verify_runtime()
        return outputs

    def convert_parts(self, source, work, *, cancel=None):
        self.verify_runtime()
        outputs = convert_cad_parts(source, work, self.command, cancel=cancel)
        self.verify_runtime()
        return outputs


class CadImportCancelled(ValueError):
    pass


def run_process(command, *, cwd=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60, cancel=None):
    """Run one owned process group and collect its output, with cooperative caller cancellation."""
    if cancel is not None and cancel.is_set():
        raise CadImportCancelled("CAD import cancelled.")
    with subprocess.Popen(command, cwd=cwd, stdout=stdout, stderr=stderr,
                          start_new_session=os.name == "posix") as process:
        deadline = time.monotonic() + timeout
        try:
            while True:
                if cancel is not None and cancel.is_set():
                    raise CadImportCancelled("CAD import cancelled.")
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(command, timeout)
                try:
                    output, errors = process.communicate(timeout=min(0.1, remaining))
                    break
                except subprocess.TimeoutExpired:
                    continue
            if cancel is not None and cancel.is_set():
                raise CadImportCancelled("CAD import cancelled.")
            return subprocess.CompletedProcess(command, process.returncode, output, errors)
        except BaseException:
            if os.name == "posix":
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                process.kill()
            process.communicate()
            raise


def file_sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require_output(path, maximum):
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= maximum:
        raise ValueError(f"Missing, invalid or oversized CAD output: {path.name}")


def run_stage(command, work, log_name, *, cancel=None):
    log = work / log_name
    try:
        with log.open("xb") as stream:
            result = run_process(command, cwd=work, stdout=stream, stderr=subprocess.STDOUT, cancel=cancel)
    except subprocess.TimeoutExpired as error:
        raise ValueError(f"{log.stem} exceeded the 60-second CAD conversion limit.") from error
    if result.returncode:
        with log.open("rb") as stream:
            stream.seek(max(0, log.stat().st_size - 2048))
            detail = stream.read().decode("utf-8", errors="replace").strip()
        raise ValueError(f"{log.stem} exited with status {result.returncode}. {detail}")


def convert_cad(source, work, command, *, windows_paths=False, cancel=None):
    """Return the split BREP and VIS from a new workspace, after both stages succeed."""
    outputs = convert_cad_parts(source, work, command, windows_paths=windows_paths, cancel=cancel, maximum_parts=1)
    return outputs[0]


def convert_cad_parts(source, work, command, *, windows_paths=False, cancel=None, maximum_parts=MAX_CAD_PARTS):
    """Return all split BREP/VIS pairs after every conversion stage succeeds."""
    if not 1 <= maximum_parts <= MAX_CAD_PARTS:
        raise ValueError("CAD conversion supports at most 32 emitted parts.")
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
    run_stage([*command, IMPORT_COMMANDS[suffix], tool_path(staged), tool_path(split_base)], work, "split.log",
              cancel=cancel)
    parts = sorted(work.glob("part*.brep"))
    if not 1 <= len(parts) <= maximum_parts:
        expected = "one CAD part" if maximum_parts == 1 else f"1 to {maximum_parts} CAD parts"
        raise ValueError(f"Expected {expected} from the split, got {len(parts)}.")
    for brep in parts:
        require_output(brep, MAX_CAD_BYTES)
    if sum(brep.stat().st_size for brep in parts) > 2 * MAX_CAD_BYTES:
        raise ValueError("Combined CAD part output exceeds 32 MiB.")
    if list(work.glob("geometry*.vis")):
        raise ValueError("The split unexpectedly wrote the VIS output.")
    outputs = []
    total_vis_bytes = 0
    for index, brep in enumerate(parts, 1):
        stem = "geometry" if len(parts) == 1 else f"geometry-{index:04d}"
        vis = work / (stem + ".vis")
        if vis.exists() or vis.is_symlink():
            raise ValueError("A conversion stage unexpectedly wrote another part's VIS output.")
        log = "visualize.log" if len(parts) == 1 else f"visualize-{index:04d}.log"
        run_stage([*command, "BREP_VISUALIZATION", tool_path(brep), tool_path(vis), "0.01", "1", "0.26"],
                  work, log, cancel=cancel)
        require_output(vis, MAX_VIS_BYTES)
        total_vis_bytes += vis.stat().st_size
        if total_vis_bytes > MAX_TOTAL_VIS_BYTES:
            raise ValueError("Combined visualization output exceeds 16 MiB.")
        outputs.append((brep, vis))
    require_output(staged, MAX_CAD_BYTES)
    if file_sha256(staged) != hashlib.sha256(data).hexdigest():
        raise ValueError("The CAD tool modified its staged input.")
    return outputs


class ReferenceCadTool:
    """Explicit local compatibility tool using the pinned 3.0.0 runtime."""
    description = "Original 3.0.0 via CrossOver"

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

    def convert(self, source, work, *, cancel=None):
        self.verify_runtime()
        outputs = convert_cad(source, work, self.command, windows_paths=True, cancel=cancel)
        self.verify_runtime()
        return outputs

    def convert_parts(self, source, work, *, cancel=None):
        self.verify_runtime()
        outputs = convert_cad_parts(source, work, self.command, windows_paths=True, cancel=cancel)
        self.verify_runtime()
        return outputs

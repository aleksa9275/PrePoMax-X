#!/usr/bin/env python3
"""Run both pinned source probes locally in Podman; never fetch, commit or push."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

from probe_evidence import compare

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ARCHITECTURES = {"arm64": "Arm64", "amd64": "X64"}


def capture(*command, timeout=60):
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {command}\n{result.stderr}\n{result.stdout}")
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=["native", "linux/arm64", "linux/amd64"], default="native")
    parser.add_argument("--output-dir", type=Path, default=HERE / "artifacts" / "podman")
    parser.add_argument("--skip-build", action="store_true", help="Reuse the cached local image without network access")
    args = parser.parse_args()
    try:
        info = json.loads(capture("podman", "info", "--format", "json"))
    except (RuntimeError, FileNotFoundError) as error:
        raise RuntimeError("Podman must be installed and running. On macOS use podman machine init/start.\n" + str(error)) from error
    server_arch = info["host"]["arch"]
    target = "linux/" + server_arch if args.platform == "native" else args.platform
    arch = target.split("/")[1]
    if arch not in ARCHITECTURES:
        raise ValueError("Only Linux arm64/amd64 probes are supported, got " + target)
    image_name = "localhost/prepomax-x-core-probe:" + arch
    recipe_hash = hashlib.sha256((HERE / "Containerfile").read_bytes()).hexdigest()
    if not args.skip_build:
        # Only the recipe is sent to the build engine: no repository or Git data.
        with tempfile.TemporaryDirectory(prefix="prepomax-x-image-") as folder:
            recipe = Path(folder) / "Containerfile"
            recipe.write_bytes((HERE / "Containerfile").read_bytes())
            subprocess.run(["podman", "build", "--platform", target, "--tag", image_name,
                            "--build-arg", "PREPOMAX_X_RECIPE_SHA256=" + recipe_hash,
                            "--file", str(recipe), folder], cwd=ROOT, check=True)
    image = json.loads(capture("podman", "image", "inspect", image_name))[0]
    if image["Architecture"] != arch or image["Os"] != "linux":
        raise ValueError("Cached image does not match requested platform " + target)
    if (image["Config"].get("Labels") or {}).get("org.prepomaxx.core-probe.recipe-sha256") != recipe_hash:
        raise ValueError("Cached image recipe differs; rerun without --skip-build.")
    # Execute the inspected immutable image ID, even if another process retags it.
    image_id = image["Id"]
    metadata = {"engine": "podman", "clientVersion": capture("podman", "--version").strip(),
                "serverVersion": info["version"]["Version"], "serverArchitecture": server_arch,
                "clientOS": platform.system(), "clientArchitecture": platform.machine(),
                "platform": target, "imageId": image_id, "imageName": image_name,
                "imageDigest": image.get("Digest"),
                "containerfileSha256": recipe_hash,
                "crossArchitecture": arch != server_arch,
                "execution": "translated/emulated; not native x64 acceptance" if arch != server_arch
                             else "native architecture Linux container (VM on macOS)",
                "network": "none", "repositoryMount": "read-only",
                "recordedAtUtc": datetime.now(timezone.utc).isoformat()}
    manifest = json.loads((HERE / "source-manifest.json").read_text())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for label, revision in [("baseline", None), ("v2.6.0", manifest["replayCommit"])]:
        command = ["podman", "run", "--rm", "--pull=never", "--platform", target,
                   "--network=none", "--read-only", "--tmpfs", "/tmp:rw,size=1g",
                   "--mount", f"type=bind,source={ROOT},destination=/workspace,ro=true",
                   image_id, "--expect-os", "Linux", "--expect-architecture", ARCHITECTURES[arch]]
        if revision:
            command.extend(["--revision", revision])
        destination = args.output_dir / f"linux-{arch}-{label}.json"
        try:
            report = json.loads(capture(*command, timeout=240))
        except (ValueError, RuntimeError, subprocess.SubprocessError) as error:
            failure = {"schemaVersion": 1, "success": False, "container": metadata,
                       "sourceCommit": revision or manifest["baselineCommit"],
                       "error": str(error).replace(str(ROOT), "<repository>")}
            destination.write_text(json.dumps(failure, indent=2) + "\n")
            raise RuntimeError("Container probe failed; diagnostic report: " + str(destination)) from error
        reference = ROOT / ".project/reports/core-feasibility" / f"macos-arm64-{label}.json"
        # Retain the complete result on a mismatch, but fail the command as a gate.
        reference_report = json.loads(reference.read_text())
        matches = compare(report, reference_report, reference, ROOT)
        report["container"] = metadata
        destination.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"report": str(destination), "runtime": report["tests"]["runtime"],
                          "passed": report["tests"]["passed"], "failed": report["tests"]["failed"],
                          "matchesMacReference": matches, "execution": metadata["execution"]}), flush=True)
        if not matches:
            raise ValueError("Linux observations differ from recorded macOS reference: " + str(destination))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, RuntimeError, OSError, subprocess.SubprocessError) as error:
        print("PODMAN PROBE FAILED: " + str(error), file=sys.stderr)
        sys.exit(1)

"""Portable evidence comparison shared by local Podman and hosted CI checks."""
import hashlib


def comparable(report):
    """Exclude platform versions, timing and paths, but retain measured behavior."""
    return {"sources": report["sourceFiles"], "fixture": report["fixture"],
            "checks": report["tests"]["checks"], "observations": report["tests"]["observations"],
            "cliContracts": report["cliContracts"], "geometry": report["inspection"]["geometry"]}


def compare(report, reference_report, reference, root):
    matches = comparable(report) == comparable(reference_report)
    report["success"] = matches
    report["comparison"] = {"reference": reference.relative_to(root).as_posix(),
                            "referenceSha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
                            "matches": matches,
                            "scope": "source/fixture hashes, checks, parser observations, CLI contracts and cube geometry"}
    return matches

#!/usr/bin/env python3
"""Fetch and fast-forward the clean upstream mirror; never push or integrate cp/main."""
import argparse
import os
from pathlib import Path
import subprocess
import sys


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def canonical(url):
    return url.removesuffix("/").removesuffix(".git").replace("git@gitlab.com:", "https://gitlab.com/")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="fetch and report; do not update a local branch")
    args = parser.parse_args()
    root = Path(git("rev-parse", "--show-toplevel"))
    os.chdir(root)
    if git("status", "--porcelain=v1", "--untracked-files=all"):
        raise ValueError("Working tree is dirty (including untracked files); commit or preserve work first.")
    for marker in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply", "sequencer"):
        if Path(git("rev-parse", "--git-path", marker)).exists():
            raise ValueError("An integration operation is in progress: " + marker)
    if git("rev-parse", "--is-shallow-repository") != "false":
        raise ValueError("Shallow history cannot establish the complete upstream mirror.")
    official = "https://gitlab.com/MatejB/PrePoMax"
    if canonical(git("config", "--get", "remote.upstream.url")) != official:
        raise ValueError("upstream must point to the official PrePoMax repository.")
    origin = canonical(git("config", "--get", "remote.origin.url"))
    if not origin.startswith("https://gitlab.com/") or origin == official:
        raise ValueError("origin must be a distinct GitLab fork; inspect remote configuration.")
    advertised = git("ls-remote", "--symref", "upstream", "HEAD")
    defaults = [line.split()[1] for line in advertised.splitlines() if line.startswith("ref: refs/heads/")]
    if len(defaults) != 1:
        raise ValueError("Cannot identify one advertised upstream default branch.")
    branch = defaults[0].removeprefix("refs/heads/")
    if branch.startswith(("cp/", "feature/", "integration/", "research/")):
        raise ValueError("Upstream default collides with a development branch namespace.")
    git("check-ref-format", "refs/heads/" + branch)
    # No pruning or forced tag replacement. The local-mirror ancestry check below
    # detects rewritten upstream history even if a remote-tracking ref moves back.
    git("fetch", "--tags", "upstream", "refs/heads/*:refs/remotes/upstream/*")
    target = git("rev-parse", "refs/remotes/upstream/" + branch)
    ref = "refs/heads/" + branch
    try:
        old = git("rev-parse", "--verify", ref)
    except subprocess.CalledProcessError:
        raise ValueError("Missing local mirror branch " + branch + "; establish it after reviewing history.")
    ahead, behind = map(int, git("rev-list", "--left-right", "--count", old + "..." + target).split())
    if ahead:
        raise ValueError(f"Local {branch} has {ahead} non-upstream commits; refusing to rewrite it.")
    if subprocess.run(["git", "merge-base", "--is-ancestor", old, target]).returncode != 0:
        raise ValueError("Upstream update is not a fast-forward; human review required.")
    attached = []
    for record in git("worktree", "list", "--porcelain").split("\n\n"):
        lines = record.splitlines()
        if "branch " + ref in lines:
            attached.append(next(line[9:] for line in lines if line.startswith("worktree ")))
    current = git("symbolic-ref", "-q", "HEAD") if attached else ""
    if attached and (len(attached) != 1 or Path(attached[0]).resolve() != root.resolve() or current != ref):
        raise ValueError("Mirror branch is checked out in another worktree; run there after checking its status.")
    print(f"Upstream default: {branch}; {old[:12]} -> {target[:12]}; new commits: {behind}")
    if behind:
        print(git("log", "--format=%h %s", "--max-count=20", old + ".." + target))
        if behind > 20:
            print(f"({behind - 20} additional commits; inspect git log {old}..{target})")
    if args.dry_run:
        print("Dry run: fetched refs only; local mirror unchanged.")
    elif behind:
        if current == ref:
            git("merge", "--ff-only", "--no-edit", target)
        else:
            # Ancestry was checked above. Compare-and-swap refuses a concurrent local change.
            git("update-ref", "-m", "PrePoMax-X verified fast-forward upstream mirror", ref, target, old)
        print("Local upstream mirror updated by fast-forward.")
    else:
        print("Local upstream mirror already equivalent.")
    print("cp/main untouched; no checkout, merge into development, or push performed.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, subprocess.CalledProcessError) as error:
        print("REFUSED: " + str(error), file=sys.stderr)
        sys.exit(1)

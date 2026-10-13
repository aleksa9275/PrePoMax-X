# Upstream synchronization and integration

## Repository lanes

`origin` is `git@gitlab.com:aleksa9275/pre-po-max-x.git`; `upstream` is `https://gitlab.com/MatejB/PrePoMax.git`. The advertised default is currently `master`, also referenced by origin/HEAD and upstream/HEAD. `master` mirrors upstream exactly. `x/main` is a separate reviewed integration lane; Phase 0 documentation stays on `feature/project-initialization`. New development branches use the maintainer's requested prefixes.

The repository is not shallow. Fetches preserve full history and tags. Do not replace upstream history with periodic source snapshots, synthetic squashed releases or forced mirror pushes. If the default changes or mirror diverges, stop and review history rather than reset. GitLab branch protections/default-branch changes were not configured; request approval of a concrete protection policy later. Suggested protections: fast-forward-only/restricted writers for master, reviewed integration for x/main, no forced pushes/deletions.

## Maintenance script

Python 3.9+ and Git required; no installed packages. Run from any location inside the checkout:

```sh
python3 .project/scripts/upstream-sync.py --dry-run
python3 .project/scripts/upstream-sync.py
```

Both modes check tracked/untracked work, active Git operations and shallow history; validate configured remotes; query the actual upstream HEAD; fetch upstream branches/tags; compare mirror ancestry; and print up to 20 new commits with a count. **Dry run still fetches remote-tracking refs and tags**, but never updates local branch content. Existing tags are never force-replaced. Git URL rewrite configuration is trusted local configuration and should be inspected before running automation.

Normal mode fast-forwards only the corresponding local default branch. If it is the current checked-out branch, use `merge --ff-only`; if unchecked out, an ancestry-validated compare-and-swap `update-ref` advances it without checking out files. The latter is a verified fast-forward ref operation, not a forced reset; concurrent local ref changes are rejected. A branch checked out in another worktree is refused. Run without concurrent checkout/worktree operations; the script is not a global lock for arbitrary Git commands. It refuses missing mirror branches and development-prefix collisions. Divergence/ahead commits or missing credentials are blockers to the mirror update, never reasons to rewrite history.

There is no checkout/stash, no development merge, no push, no branch deletion, no history rewrite and no pruning. A failing fetch can still update some remote refs, but cannot update a local branch because local mutation follows successful fetch/validation. `x/main` and feature branch contents stay untouched. Invocation during Phase 0 with uncommitted documentation correctly refuses; run after the local commit.

Verify with `git rev-list --left-right --count master...upstream/master` (expected `0 0`) and `git status --short --branch`, using the actually detected branch name in future. A local clean mirror can be published to the fork only after approval of the exact commit range and destination; script never publishes it. Never push to upstream.

## Separate integration workflow

1. Fetch/mirror and record upstream old/new immutable commits, release state and native/tool version changes. Inspect `git log --oneline OLD..NEW`, `git diff --stat OLD..NEW` and the full relevant diff. Reassess portability boundaries and serialized types before estimating scope.
2. Create `integration/upstream-<version-or-short-sha>` from `x/main` only when integration work is authorized. Preserve history with a reviewed merge of the pinned upstream commit; no automatic merge into x/main. Investigate conflicts by category below, preserving engineering behavior and upstream intent.
3. Run Windows oracle plus affected managed, compatibility, native, selection and full release suites. Compare old/new upstream Windows behavior first to distinguish intentional upstream changes from port regressions.
4. Record native manifest changes, adapted frontend features, unavailable capabilities and numerical/format deltas. Obtain approval for policy/architecture changes and any release limitations. A conflict-free merge does not remove this requirement.
5. After review, integrate into x/main, update docs/baseline and version-aligned package metadata (e.g. upstream version plus PrePoMax-X revision). Final 3.0 stable switch needs its exact commit/release artifact, fixtures and passing gates even if no tag exists.

| Incoming category | Handling and required review/tests |
|---|---|
| Engineering core | Prefer original algorithm changes unchanged; apply only boundary adapters. Re-run deck/result/units/connectivity and numerical differential tests |
| Controller/application logic | Keep one behavior implementation; extend shared services/gateways, update commands/journals/errors and session tests |
| GUI | Preserve Windows form changes; translate presentation into portable frontend and feature matrix; no duplicated engineering calculations. UI/workflow/keyboard/prompt checks |
| Visualization | Preserve VTK pipeline and mapping intent; adapt version/host differences. Pick/clip/deformation/contours/lifetime tests on actual render backends |
| Native dependencies | Recover exact source+patch/version/ABI; reproduce all RIDs, notices and hashes. CAD topology/mesh/solver regressions; do not substitute stock binaries silently |
| Build/packaging | Keep platform-specific packaging isolated; test clean-machine closure, permissions, assets and build reproducibility |
| Bug fixes | Classify by owning layer, add an appropriate regression fixture before adaptation, compare expected upstream behavior |
| Documentation | Merge applicable upstream content without losing PrePoMax-X records; verify agent/API guidance describes current capabilities |

## Hermes and other agents

No scheduled/unattended automation is configured. A future Hermes task can read AGENTS/STATUS, invoke the script with `--dry-run`, prepare a categorized impact report and run approved checks. It may perform a local clean-mirror fast-forward under the same authorization, but must report refusal and continue independent analysis when blocked. Grant only read/fetch/local-maintenance capabilities by default.

Human review remains necessary for public pushes, x/main merges, source substitutions, license exceptions, serializer/GUI/renderer decisions, acceptance-tolerance changes and releases. Hermes can prepare integration branches/conflict proposals and test reports after authorization; it cannot treat a Git merge, clean compile or generated test report as proof of compatibility. Never grant automatic upstream writes, forced mirror updates or unattended publishing.

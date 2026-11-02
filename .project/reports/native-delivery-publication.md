# Native delivery checkpoint publication

2 November 2026. Maintainer explicitly authorizes proceeding and committing/pushing
useful work with progress documentation. Only normal publication to
origin/research/native-feasibility is in scope; no upstream/master/x/main/release
write or force push.

- **66e3ca0fbce22ca17efa7222dae9bed5218c6a87**: PrePoMac/upstream review,
  accelerated plan and focused development checks/CI preparation. Pushed and
  independently verified with `git ls-remote`.
- Tasks **0037/0038**: native CPU workflow, B001 fix, dependency sources,
  packaged native viewport candidate and B002 evidence. Current checkpoint is
  being reviewed for normal commit/push; actual SHA is recorded after publication.

Relevant Mac checks and retained evidence are in
[CPU workflow](native-cpu-workflow.md) and [desktop candidate](native-desktop-preview.md).
Earlier known correctness failures/tetra gate and every remaining platform/release
requirement remain. Binary app/solver/build/package caches are ignored, not pushed.

Hosted CI has **not** been verified for these new commits. The available GitLab
browser session returned Sign In/404 for the private repository; glab is absent.
Remote branch verification establishes publication only. No raw hosted artifact
or native Linux/Windows pass is claimed. Existing CI remains prepared to run the
current-source engineering checks on native Linux x64; desktop/solver jobs are
not silently added or asserted successful.

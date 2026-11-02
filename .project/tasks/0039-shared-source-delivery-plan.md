# Task 0039 — macOS-first delivery with shared-source targets

2 November 2026. Maintainer reports a failed GitLab pipeline and requests a plan
adjustment: maximize speed toward native macOS PrePoMax while keeping Windows
and Linux Debian/Fedora/Arch awareness now and progressively testing later.
Ideally the same source is compiled for different targets.

Changed: rewrote the existing [delivery plan](../proposals/accelerated-native-delivery.md)
around one shared application/engineering source tree, four RIDs, target build/
native dependency helpers and thin distro package wrappers. Mac preview remains
the critical path; existing Linux x64 engineering feedback remains continuous.
Other-target compilation comes before complete Mac feature parity; native GUI/
installer/distro matrices occur at relevant checkpoints. Mac-only recipe and
test assumptions are identified from actual files, without claiming a port.

Checked: current status, task 0037/0038 outcomes, published CI templates, desktop/
solver/package scripts, primary .NET/PyInstaller/Qt/Arch documentation and local
document links/whitespace. Documentation only; no engineering suite rerun or
application/CI/solver/framework/dependency version changes.

Open: failed pipeline URL/job/commit/error was requested. No failed-job log was
identified in the reviewed records or supplied in this turn; no cause, fix or hosted pass is
claimed. Obtain the exact evidence before diagnosing or changing CI. Mac recipe
generalization, binding resolution, complete workflow and other-target/package
execution remain engineering work, not delivered by this plan.

Existing checkpoint publication authorization remains under D051; useful plan/
progress records may publish normally to origin/research/native-feasibility only.
No upstream/master/x/main/release write or production frontend/default format/
backend/precision decision. Both known failures/tetra gate and all final gates
remain. The sequence is a proposal for implementation, not a new full-product
or distro-version support claim.

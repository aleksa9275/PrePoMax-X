# Task 0024 — Portable native job boundary and organized dependency sources

2026-10-18. Maintainer requests continuing accepted native solver/results work
and explicitly requires an understandable final repository with third-party
source in appropriate folders and a public release branch serving installers,
Homebrew and other package managers. Preserve all uncommitted task 0022/0023
work; this is not an instruction to publish, change solver/numerical policy or
create public release artifacts now.

Investigate the existing CaeJob/ExecutableJobRunner seam, mechanically preserve
its original net48 implementation and introduce a narrow modern platform adapter
for native process execution, exit status, output/error/progress, working
paths, timeout/cancellation and child process cleanup. Keep original type/enum/
assembly ownership. Add source/fixture/version/hash preflight and an explicit
solver input/output command; no shell command construction or automatic solver
substitution. Exercise real native process behavior with test executables on
Mac/Linux ARM64 and replay both upstream pins. A helper process is transport
testing, not solver or numerical acceptance.

Recover authoritative CalculiX 2.22 source/build metadata in an organized
ThirdParty source area with checksums/notices/patch provenance. Compare against
existing bundled Windows PaStiX/MKL evidence. Run a native analytical solve only
if its source/build identity can be established within existing policy; otherwise
record the exact blocker and continue independent process/results preparation.
Do not promote a different sparse backend or stock build as a matching solver.
Record the accepted final organization/public-release-branch requirement with a
readable repository map; preserve upstream paths during current research and
keep downloaded/build/runtime outputs separate from checked-in sources.

Retain both correctness failures and all Windows/net48/RC2/four-target/native-
source/UI/persistence/CAD/installer/signing/Homebrew release gates. Leave changes
uncommitted. Status: completed within the bounded process/source-recovery/monitor increment.
Actual native numerical solve and full workflow remain pending, not accepted.

Mechanically split original job/enum ownership and retained legacy net48 methods;
modern CaeJob adapter/CLI supports actual process lifecycle, profile/hash preflight
and original STA/CVG inspection. All three source modes pass 33 native process/
monitor/preflight checks plus four CLI controls on Mac/Linux ARM64; four source
guards pass. All source/tool/engineering comparisons match. Recovered unchanged
official CalculiX 2.22 source (1188 files) with archive/per-file/manifest pins and
GPL text. Recorded accepted final repository map/third-party sources/x/release
requirement. All edits remain uncommitted; no new hosted/Windows/full net48 pass.

Matching native 2.22 source/patch/PaStiX/BLAS/runtime/ABI chain and actual RC2
bundle still need proof. No stock SPOOLES or other solver was substituted. The
first Linux container descendant check required an init reaper; its failure and
passing final runs are retained. Both correctness failures and every release
gate remain. Next independent work: original FRD/DAT field reader expansion and
continued matching native-source/build recovery. [Evidence](../reports/native-job-boundary.md).

# Portable CPU thread recommendations

2026-10-18, [task 0028](../tasks/0028-portable-thread-planning.md). The maintainer
authorized one bounded increment followed by publication/reset handoff.

`CaeJob.SolverThreadPlan.Create` is modern-only code in X/Execution/CaeJob;
original net48 application projects/settings are unchanged by this increment.
It computes `max(1,floor(available logical CPUs*3/4))` using overflow-safe integer
arithmetic, accepts an explicit manual total up to available CPUs, and divides
that total fairly among up to 1024 planned jobs. Every job receives at least one
thread; infeasible concurrency is rejected. Allocation ordering is deterministic
and returned plans cannot be mutated.

`PrePoMaxX.Solve thread-plan [--threads auto|N] [--jobs N]` uses modern .NET's
process-available CPU count and emits the total/per-job plan. Manual N means
the total across jobs. Unknown/duplicate options, missing values, zero/negative/
signed/overflow counts and overcommitted plans are rejected. This is a callable
recommendation, not a scheduler: no solver launch, settings change, CPU reservation,
affinity or utilization enforcement. Original pinned run-static OMP/MKL=1 controls
remain. GUI/default migration, active-job reallocation, solver-specific settings
and solver-type recommendations remain future work.

## Native verification

Current/RC2/post-RC2 pass on macOS ARM64 and native Linux ARM64 Podman:
**47 accepted execution/monitor/planning checks per build**, two positive CLI
plans and **13 CLI rejection controls**. Fourteen new checks cover automatic
rounding, one-CPU availability, manual override, fairness, no budget multiplication,
large-count overflow, invalid inputs, immutable output and allocation conservation
across CPU counts 1–128 and eligible job counts through 32. No numerical solver
or solver performance benchmark runs in these checks.

Final sources, tools, analysis dependencies, original job/monitor files and test
outcomes compare across hosts for each source pin. Actual available CPU counts
are host-specific and are validated individually rather than forced to match.
[Retained evidence and fingerprints](portable-thread-planning/verification.json).
Linux uses the cached native ARM64 image, offline/read-only mounts and `--init`.
Prepared GitLab x64 execution checks now install/use `tini -s` for equivalent
orphan reaping; no assumption about the runner's PID 1 behavior is required.

Commands:

```sh
python3 -m unittest discover -s X/Execution -p test_job_layout.py
python3 X/Execution/verify-execution.py --expect-os Darwin --expect-architecture Arm64 --output X/Execution/artifacts/thread-plan/current-macos-arm64.json
python3 X/Execution/verify-execution.py --upstream-revision 3.0.0-rc2 --expect-os Darwin --expect-architecture Arm64 --output X/Execution/artifacts/thread-plan/rc2-macos-arm64.json
python3 X/Execution/verify-execution.py --upstream-revision post-rc2-2026-10-17 --expect-os Darwin --expect-architecture Arm64 --output X/Execution/artifacts/thread-plan/post-rc2-macos-arm64.json
python3 X/Execution/run-podman.py --output-dir X/Execution/artifacts/thread-plan/linux-arm64
```

Publication review also reran nine analysis/four job/ten core replay guards,
1188-file unchanged CalculiX source verification, the full current Mac analysis
verifier (331 accepted checks and both known correctness failures retained),
and whitespace/content checks. Prior analysis three-pin Mac/Linux ARM64 evidence
remains in the task 0023 report; hosted x64 follows task 0029 publication.

The planner is not numerical acceptance. Both existing element correctness
failures/tetra host gate, native Windows/full net48/RC2, actual native solver,
FRD/DAT full fields, source/build closure, four-platform/full-workflow/installer
requirements remain. [Publication and reset handoff](analysis-execution-publication.md).

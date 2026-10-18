# Task 0027 — Solver guidance, thread defaults and GPU research

2026-10-18. Maintainer requests research/report on native ARM64 MUMPS, PaStiX,
SuperLU/UMFPACK/CHOLMOD candidates, recommendations by analysis type, using 75%
of available CPU threads, and NVIDIA/AMD/Apple GPU optimization. Treat solver
guidance and a 75% default as requested product direction; research implementation
details before changes. No production/default/precision change or new backend
integration in this increment. No new benchmarks requested; task 0026/D042's
licensing/functionality criterion and deferred numerical comparisons remain.

Read PROJECT/STATUS/DECISIONS and task 0026 before changes. Scope: public primary
documentation/source/package metadata, original PrePoMax/CalculiX read-only code
inspection and concrete proposed UX/thread/GPU policy. Preserve uncommitted work.
No publication, external communication or architecture/numerical-policy selection.

## Completion

Completed [research and proposed implementation direction](../reports/solver-guidance-threads-gpu.md).
MUMPS is a credible broad-capability fallback requiring a CalculiX adapter;
SuperLU_DIST has a documented AMD HIP path, unlike the reviewed PaStiX CUDA
path. MUMPS 5.9.1 also documents NVIDIA GPU offload. Apple Metal 4.1 does not
provide a double scalar type; no native Metal direct-solver path identified in
reviewed candidates. CPU acceleration and rendering are distinct from GPU solving.

Proposed guidance filters actual build capabilities and matrix requirements,
then gives an explained, overrideable recommendation. The 75% available-logical-
CPU default is a thread budget, not a utilization guarantee or optimal speed
claim; explicit user settings and a shared budget across concurrent jobs matter.
No new backend/default/precision/GPU/CPU settings are implemented or benchmarked.

Verification: cited primary sources read; original thread/default/dispatch paths
inspected. Downloaded Metal specification parsed locally because web PDF access
failed (version/hash recorded in report). Relative document links and whitespace
checked. Work remains uncommitted; both correctness failures/tetra gate and all
native Windows/net48/RC2/four-target/full-workflow/package gates remain.

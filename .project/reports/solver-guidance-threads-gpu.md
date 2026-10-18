# Solver recommendations, CPU threads and GPU feasibility

2026-10-18. [Task 0027](../tasks/0027-solver-guidance-threads-gpu-research.md).
Research and proposed design only. No solver/default/precision/GPU setting,
dependency, numerical code, benchmark, external contact or publication change.
Task 0026/D042's Panua exclusion and functionality criterion remain in force.

## Findings on the suggested libraries

Package availability is evidence of a usable library, not CalculiX integration,
equivalent numerical behavior, or a performance guarantee. Prefer existing
CalculiX SPOOLES/modified PaStiX first. If a required workload remains unusable,
MUMPS is the first broad-capability candidate to investigate, rather than adding
every library to the product. This ranking is an architectural inference.

| Candidate | Primary-source observation | Implication for PrePoMax-X |
| --- | --- | --- |
| MUMPS | Handles SPD, general symmetric and unsymmetric systems, real/complex arithmetic, factor/solve reuse, parallel execution and out-of-core numerical phases. [Official overview](https://mumps-solver.org/index.php). | Broad candidate for difficult/large systems; requires original CalculiX matrix/factor/solve/cleanup adapter and validation. |
| PaStiX | Existing CalculiX wrapper and modified fork; upstream documents LLt/LDLt/LU with static pivoting, pthreads, optional runtimes and CUDA. [Handbook](https://solverstack.gitlabpages.inria.fr/pastix/index.html). | Lowest integration distance alongside SPOOLES; recover exact source/configuration and validate difficult cases before recommendations. Generic current PaStiX is not a drop-in for the pinned wrapper. |
| SuperLU | General sparse LU; sequential and distributed families are different packages. [Maintainer repository](https://github.com/xiaoyeli/superlu). | Native C integration is possible; do not classify the entire family as limited to small models. |
| SuperLU_DIST | MPI/OpenMP solver; documents NVIDIA CUDA and AMD HIP factorization/triangular solve support. [Maintainer README](https://raw.githubusercontent.com/xiaoyeli/superlu_dist/master/README.md). | Serious later candidate when an AMD GPU requirement justifies a new adapter; adds distributed/runtime/build complexity. Not already part of CalculiX 2.22. |
| UMFPACK / scikit-umfpack | UMFPACK is sparse LU; scikit-umfpack is its Python interface. [SuiteSparse](https://github.com/DrTimothyAldenDavis/SuiteSparse). | Use the underlying C library for an adapter if ever selected; Python need not become an application/runtime dependency. |
| CHOLMOD | Designed for sparse symmetric positive-definite Cholesky factorization. [Maintainer README](https://raw.githubusercontent.com/DrTimothyAldenDavis/SuiteSparse/dev/CHOLMOD/README.txt). | Specialized candidate, not a general pivoted indefinite/unsymmetric replacement. An analysis label alone does not establish SPD. |

The supplied [pyoomph installation page](https://pyoomph.readthedocs.io/en/latest/tutorial/installation/pypa.html)
explicitly recommends native MUMPS on Apple ARM64. The supplied stable URL failed
in the web reader; the current latest page was read. Independently, the package
publisher lists `mumps-seq` for macOS ARM64, Linux aarch64/x64 and Windows x64:
[conda-forge metadata](https://anaconda.org/conda-forge/mumps-seq/manage).
That verifies package availability, not our pinned build or parallel performance.
No current Homebrew-core MUMPS formula was verified; historical homebrew-science
instructions are insufficient. A future package can use a maintained tap or our
own verified source recipe. Our Homebrew application delivery is a separate issue.

[PyPardiso's own README](https://raw.githubusercontent.com/haasad/PyPardiso/master/README.md)
confirms it wraps Intel MKL; it recommends scikit-umfpack on Apple Silicon. It is
not itself an ARM PARDISO engine. The supplied Stack Overflow page was read as
context, but technical conclusions above rely on the libraries' primary sources.

**Verified local boundary:** `CaeModel/Steps/Step.cs:31` exposes Default, PaStiX,
Pardiso, Spooles and two iterative options. Reviewed CalculiX dispatch/Makefiles
do not establish MUMPS, SuperLU, UMFPACK or CHOLMOD integration. Installing a
library cannot add a valid solver keyword. A future adapter must preserve matrix
symmetry/indefiniteness, indexing/ABI, shifted matrices, repeated right-hand sides,
complex support where used, error handling and cleanup. This is engineering work,
not simply a UI list extension.

## Proposed solver guidance

The maintainer requests solver recommendations. Implement as explained advice
with an explicit Apply action/manual override, rather than hidden per-run
substitution. Preserve saved explicit selections and original deck semantics.
Unavailable selections need a clear capability explanation, not automatic rewriting.

Filter by actual pinned executable/build capabilities first. Rank only validated
combinations using analysis type, shell/beam/solid content, constraints/contact,
matrix requirements where known, available memory and benchmark evidence. Do not
promise conditioning or exact peak memory from a model preview or node count.
Recommendations need a versioned rule/evidence record; unknown cases remain unknown.

| Analysis/model situation | Initial advice to validate later |
| --- | --- |
| Slender shells/beams, ordinary static analysis | SPOOLES as a conservative comparison when memory permits; PaStiX double precision as a performance candidate after thin-shell regression coverage. |
| Large solid or contact/plasticity analysis | PaStiX as a candidate; check convergence, memory and asymmetric requirements. Keep a verified comparison backend. |
| Frequency or linear buckling | SPOOLES comparison with a validated thread count; independent PARDISO-free PaStiX verification required. |
| Well-conditioned SPD solid/thermal system | A validated direct solver; iterative options may be offered after checking applicability. CHOLMOD is only a future option if integrated and SPD eligibility is established. |
| Indefinite, singular or unsymmetric systems | An eligible tested direct solver. Do not recommend CHOLMOD or a restricted iterative method merely because the analysis is labelled static. Explain possible model problems separately. |
| Memory/capacity limit | Explain the limit and candidate remedies. Consider MUMPS integration only if existing open routes cannot satisfy required workloads. |

These are proposed starting rules, **not validated solver assignments**. The
[prior assessment](without-pardiso-assessment.md) records shell/mixed-precision,
SPOOLES thread sensitivity and modal/buckling fallback risks. Original 2.22
`arpack.c`/`arpackbu.c` can invoke PARDISO for a PaStiX-labelled selection when
both are linked. A label-only pass cannot validate an independent PaStiX route.
The [official manual](https://www.dhondt.de/ccx_2.22.pdf) documents analysis and
thread controls; it does not establish a universally optimal recommendation table.

Proposed user-facing example after validation: “Recommended: [solver], because
this model contains thin shells. 12 of 16 available CPU threads. GPU acceleration:
unavailable in this solver build.” Keep detailed build/environment diagnostics
in a job report. Do not show unsupported or unvalidated modes as recommended.

## The 75% CPU default

Accepted product direction: automatically start from 75% of available threads.
Proposed rounding: `max(1, floor(0.75 * availableLogicalProcessors))`:
8 → 6, 12 → 9, 16 → 12, 32 → 24; a one-processor allocation still uses one.
Use an Auto (75%) setting plus an explicit manual count; retain existing manual
choices on migration rather than overwriting them.

[Microsoft's modern .NET documentation](https://learn.microsoft.com/en-us/dotnet/api/system.environment.processorcount?view=net-10.0)
reports process-available logical processors, considering affinity and CPU limits,
with caveats: the value is fixed at runtime startup, quotas are rounded, and an
environment override exists. Legacy net48 Windows semantics differ. Resolve the
actual execution host/allocation, not just the GUI machine's advertised count.

This is a thread budget, **not a hard 75% CPU-utilization cap**, a promise that
25% of physical compute is reserved, or proof of best performance. Logical SMT
threads and heterogeneous performance/efficiency cores are not equal resources.
Memory bandwidth, model size, thermal limits and concurrent work matter.
Do not implement affinity pinning or a P-core-only policy by inference here.

**Verified current code:** `PrePoMax/Settings/SolverSettings.cs:110` resets
`NumCPUs` to 1. `CaeJob/AnalysisJob.cs:922–946` sets `OMP_NUM_THREADS` and then
applies user environment overrides. New bounded `X/Execution/Solve/Program.cs`
currently pins OMP/MKL to 1 for reference execution. Do not change research
reference controls while adding a future user-facing automatic mode.

The actual solver worker count depends on its compiled backend and settings.
The original `pastix.c:199–240` reads MKL/OMP/CCX controls and sets its thread
parameter. Different CalculiX phases have their own controls. A future adapter
must coordinate OMP, CCX, MKL/OpenBLAS and scheduler/BLAS pools per build; nested
parallelism must not multiply the intended count. A sequential BLAS may be the
right choice inside an already parallel PaStiX scheduler, as its handbook notes.
Conflicting user environment settings must be visible and resolved explicitly.

Use one application-wide budget for simultaneous solver jobs, divided among
active jobs rather than allocating 75% to every job independently. Record requested
and effective settings; validate meaningful scaling at 1, physical-core-oriented,
75%-logical and all-available configurations later. Safety exceptions for a
backend/thread combination must be visible rather than silently ignored.

## GPU feasibility

Detecting a GPU is only the first condition: require a supported device/driver/OS,
the correct solver binary/runtime, sufficient memory and validated numerical
behavior. GPU rendering in the frontend is separate from numerical solving.

| GPU | Primary-source support | Proposed project treatment |
| --- | --- | --- |
| NVIDIA | PaStiX documents CUDA/cuBLAS via StarPU/PaRSEC. Original 2.22 `Makefile_i8` links CUDA/PaRSEC; wrapper has `PASTIX_GPU` and scheduler controls. | First optional GPU research route because an existing wrapper exists. Confirm the actual fork/build; an environment flag cannot create absent GPU kernels. |
| NVIDIA, additional fallback | MUMPS 5.9.1 section 5.27 documents cuBLASXT/XKBlas offloading with `ICNTL(51)`; default is off. [Current manual](https://mumps-solver.org/doc/userguide_5.9.1.pdf). | Possible benefit if MUMPS becomes necessary, not a reason alone to integrate it now. |
| AMD | SuperLU_DIST explicitly supports HIP. MUMPS documentation describes AMD work in XKBlas, but not an equivalent demonstrated end-to-end route for this project. | A credible separate integration investigation if justified. Verify exact device/OS/runtime support; do not claim existing CalculiX PaStiX supports AMD just because another runtime does. |
| Apple | Metal specification 4.1 section 2.1 has no `double` scalar type. No Metal backend identified in the reviewed sparse solvers. [Apple specification](https://developer.apple.com/metal/Metal-Shading-Language-Specification.pdf). | CPU-native solving first. A low-precision GPU factorization with CPU refinement would be a separate numerical project and cannot be assumed equivalent. |

The MUMPS current GPU manual includes limitations/compatibility controls; an AMD
development footnote is not evidence of a deployable matching integration.
SuperLU_DIST's GPU capability does not prove Windows HIP or every AMD consumer
card works. AMD's [hipSOLVER usage documentation](https://rocm.docs.amd.com/projects/hipSOLVER/en/docs-7.2.4/howto/usage.html)
also warns that sparse Cholesky paths depend on host SuiteSparse and that some QR
paths densify the matrix. A GPU API name alone is not evidence of scalable sparse
GPU factorization.

Apple [Accelerate](https://developer.apple.com/documentation/accelerate) explicitly
optimizes CPU computation. It may be useful for BLAS/LAPACK underneath a future
native build; it does not turn CalculiX into an Apple GPU solver. Preserve the
current source/ABI/numerical validation requirement for any BLAS choice.

NVIDIA cuDSS is another sparse direct library, documented for Linux/Windows and
supported ARM Linux configurations, but it is a separate integration under
NVIDIA's SDK license, not an open-source cross-vendor replacement:
[support](https://docs.nvidia.com/cuda/cudss/latest/index.html),
[license](https://docs.nvidia.com/cuda/cudss/license.html). It is not selected.

Suggested eventual UI: CPU default plus optional acceleration only for a verified
supported profile. Explain unsupported/insufficient-memory states, record actual
GPU use/timing, and avoid silent numerical/precision fallback. Large FP64-capable
devices may help; consumer marketing throughput does not predict sparse solve
speed. GPU/CPU timing must include transfer/setup and the complete job, not only
one factorization kernel. Recommend keeping GPU solving optional for the initial release.

## Recommended order and verification limits

1. Finish a reproducible native CPU CalculiX build and required regression coverage.
2. Add capability-aware solver advice and the explicit Auto (75%)/manual budget.
3. Measure representative workloads and thread scaling; refine advice from results.
4. Investigate optional NVIDIA PaStiX acceleration. Investigate MUMPS only if the
   existing open backends fail the required functionality/capacity criterion.
5. Pursue AMD/new-backend or Apple GPU numerical work only as a separately scoped
   experiment justified by need and evidence, rather than delaying native CPU delivery.

This order is a proposal, not implementation completed in this research turn.
No hardware/solver benchmark was performed. The Metal PDF could not be read by
the web PDF tool, so it was downloaded unchanged to `/private/tmp` and parsed
using `pdftotext`: version 4.1, SHA256
`41538b30d2f1140a5b2a0c84ce0a9f7b67bf0c707e224cfea0bfe5a44aa26cf5`.
No PDF/binary is added to Git. Source references distinguish verified code from
inferred suitability. Both known correctness failures/tetra host gate and every
native Windows/net48/RC2/full-workflow/four-target/installer requirement remain.

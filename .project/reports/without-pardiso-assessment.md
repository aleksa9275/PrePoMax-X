# CalculiX without PARDISO: research assessment

2026-10-18, [task 0026](../tasks/0026-without-pardiso-assessment.md).
Research only. No new benchmarks, binaries, backend/default/environment changes,
numerical acceptance, contact or publication. Existing implementation is preserved.

## Recommendation and maintainer constraint

Panua's machine-fingerprint licensing is unacceptable to the maintainer. Do not
pursue Panua as the ARM64 solution. The latest instruction narrows D041's earlier
complete-backend-identity requirement: require useful engineering functionality,
correctness and practical performance, rather than every proprietary backend.

**Architectural inference:** the evidence does not justify treating PARDISO as an
unconditional release prerequisite or starting another solver integration now.
CalculiX already has SPOOLES and PaStiX. Investigate those first; keep the original
CalculiX version, engineering algorithms, input semantics and explicit build
provenance. A new alternative becomes justified if these cannot deliver required
correct results or usable capacity/performance for representative workloads.
This is a research recommendation, not acceptance of a particular native build
or a selection of the production default.

## The maintainer's forum discussion

Located [A case for Calculix 2.22](https://prepomax.discourse.group/t/a-case-for-calculix-2-22/2016),
16–19 September 2024, under `aleksa`. The pontoon shell model improved with a
SPOOLES-only build; disabling PaStiX mixed precision also worked for the author.
Other contributors retained thin-shell concerns and reported multithreaded
SPOOLES buckling inconsistencies. Matej proposed PARDISO as the future default
on 18 September because of consistent results. This supports a correctness-led
default change, not a new analysis capability. Public topic JSON confirms the
username and dates; `aleksa9275` user-actions returned 404, so account-alias
metadata is not independently established.

Matej subsequently confirmed that nonphysical PaStiX results motivated the
default change in [the October 2024 discussion, post 7](https://prepomax.discourse.group/t/no-element-set-defined-on-gravity-load-applied-to-point-mass-in-multi-step-analysis/1955/7).
These are historical observations, not reproductions against today's native builds.

## What the performance evidence establishes

The [official 2.22 manual](https://www.dhondt.de/ccx_2.22.pdf), sections 7.62 and
7.122, lists SPOOLES and PaStiX alongside PARDISO for frequency/static analyses.
Its approximate 2x PARDISO-versus-SPOOLES statement is not a portable benchmark.
Its 3–8x PaStiX speed-up explicitly concerns large problems with a high-end
NVIDIA GPU; it cannot predict CPU-only Apple ARM64 performance. SPOOLES lacks
out-of-core support; iterative solvers can struggle severely with shells.

Concrete first-hand measurements illustrate why no universal slowdown factor
is defensible. [MichaelPE's October 2021 results, post 46](https://calculix.discourse.group/t/calculix-and-pastix-solver-windows-version/130/46)
used CalculiX 2.18 on a Ryzen 3700X, 64 GB RAM and an NVMe pagefile:

| Nodes / reported threads | PaStiX time / committed memory | PARDISO time / committed memory |
| --- | --- | --- |
| 489,035 / 6 | dynamic build 7m55s / 41 GB | dynamic build 11m08s / 31 GB |
| 1,871,515 / 4 | static i8 beta ~7h30m / 161 GB | dynamic build 2h21m28s / 103 GB |

The second comparison changes build configuration and heavily pages. It is not
a controlled current-version benchmark; it demonstrates a practical memory risk.
Smaller/faster and larger/slower cases both occur in this one report.

A [November 2024 first-hand build report](https://calculix.discourse.group/t/compile-calculix-with-pastix-solver/2422/3)
found MKL PARDISO twice as fast as modified PaStiX 6.0.1 without CUDA, and about
20% variation across PaStiX runs. It does not provide enough hardware/model/
precision detail to transfer that ratio to our targets. Together these sources
support workload-dependent advantages, not inevitable crippling without PARDISO.

## Correctness and analysis coverage

[Matej's 2022 shell reproducer](https://calculix.discourse.group/t/problems-with-pastix-solver-and-shell-elements/1169)
gave incorrect PaStiX results in 2.18/2.19; SPOOLES gave expected results. Matej
confirmed that `PASTIX_MIXED_PRECISION=0` fixed his case. That does not prove
every ill-conditioned thin shell is fixed or justify silently changing precision.

The [2023 cylinder modal case](https://prepomax.discourse.group/t/modal-analysis-of-solid-unshaped-cylinder-no-torsional-modes/716)
reported missing/incorrect PaStiX modes; SPOOLES recovered the expected modes,
including torsion. Builds differed, so preserve it as a regression candidate,
not a clean same-build performance comparison or proof of a current bug.

**Verified source observations**, not numerical tests: unchanged recovered
CalculiX 2.22 source, archive SHA256
`3a94dcc775a31f570229734b341d6b06301ebdc759863df901c8b9bf1854c0bc`:

- `src/linstatic.c:680–735` dispatches to SPOOLES, PARDISO and PaStiX. Unlike
  the built-in iterative choices, SPOOLES/PaStiX paths do not reject asymmetric
  matrices here. `nonlingeo.c:2854–3004` also has those direct-solver paths,
  including thermal equation selection. This is not full nonlinear acceptance.
- `src/arpack.c:601–669` and `src/arpackbu.c:292–337,539–562` offer SPOOLES and
  PaStiX paths for frequency/buckling. Importantly, when both PARDISO and PASTIX
  macros are defined, the PaStiX-selected factor/solve branches can call PARDISO.
  A PaStiX-labelled modal result from a combined build is insufficient evidence
  for a PARDISO-free build. The actual reference binary's route needs tracing.
- `src/pastix.c:754–780` forces double precision for separately invoked
  factorization; `:989–1015` defaults the generic solve to mixed precision,
  with explicit environment control and an input-format-3 double-precision
  exception. A generic statement that all PaStiX operations use mixed precision
  would therefore be inaccurate.
- The original GUI `SolverSettings.Reset` selects PARDISO; explicit
  `SOLVER=PARDISO` input fails in an executable without that library. We must
  detect unsupported selections and explain them. Never silently rewrite a
  saved analysis or pretend unsupported backend identity is retained.

**Inference:** no PARDISO-exclusive structural analysis category was identified
in these inspected paths. Static, nonlinear, modal and buckling calculations
have existing open-backend routes. This bounded review does not establish every
CalculiX feature or model works correctly without PARDISO. A slower/more memory-
hungry route can still make an otherwise supported large analysis impractical.
Iterative-only delivery would be a poor substitute for the reviewed direct routes.

## Later comparisons, intentionally not performed now

Retain SPOOLES and the corresponding modified PaStiX build as candidates. Recover
their source/configuration/BLAS/integer-width/runtime provenance and verify native
builds before numerical conclusions. Do not casually substitute generic newer
PaStiX: the existing wrapper uses a modified version.

Later compare against the pinned Windows PARDISO reference using representative
shell/beam/solid statics, the pontoon/very thin shell cases, analytic modal modes,
buckling and contact/plasticity plus an asymmetric/thermal case where relevant.
Verify actual backend calls, SPOOLES thread sensitivity, PaStiX precision,
eigenpairs and residuals/reactions as well as reported stress/displacement.
Measure total solve time, peak memory, paging, repeated-run variability, failure
and convergence behavior with fixed threads/build/configuration and known inputs.
Include a capacity case near available RAM; node count alone is not a sizing rule.

The earlier six-backend cube validates only a tiny static fixture through the
Windows binary in CrossOver. It neither resolves modal fallback nor establishes
native ARM64 reliability/performance. Existing two shared-core correctness
failures/tetra host gate, Windows/net48/RC2/full-workflow/four-target/package
acceptance remain. No numerical policy or production profile is changed here.

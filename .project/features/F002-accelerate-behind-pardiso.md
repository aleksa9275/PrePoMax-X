# F002 — Apple Accelerate behind the PARDISO solver option (macOS)

Status: **Deferred** (wishlist for future PrePoMax-X divergent work). Recorded 2026-11-26.
Source: forum post by Philipp Suppinger,
[Native Calculix Solver for Apple Silicone Chips](https://prepomax.discourse.group/t/native-calculix-solver-for-apple-silicone-chips/3882),
and his repository [PhilippSuppinger/ccx-accel-macos](https://github.com/PhilippSuppinger/ccx-accel-macos)
(GPL-2.0, v1.0.0, source read at `a693088b`). Priority and scheduling: unset. No code has changed.

## Maintainer decision

Not now: technically good, but it bypasses the missing PARDISO rather than providing it. If it is ever
implemented, it must be marked clearly **both in the release (notes, bundle notice) and in the software**
(solver choice and solver output), so users always know which solver ran. It would be a PrePoMax-X divergence
and needs its own decision in DECISIONS.md; D060's PARDISO exception stays as it is until then.

## What the work is

- `accel_pardiso.c` (~200 lines) provides CalculiX's `pardiso_` entry point and solves with Apple Accelerate's
  sparse direct solvers: symmetric → Cholesky, then LDLᵀ with threshold pivoting 0.01 (= SPOOLES τ 100);
  unsymmetric → LU. One factorization per PARDISO handle (CalculiX keeps `pt` and `ptcp` open together).
- Safety net: relative residual after each solve, up to 5 refinement steps above 1e-10, fallback to SPOOLES
  (`spooles_fallback.c`, CalculiX's own SPOOLES settings) if factorization fails or the residual stays above 1e-6;
  the better solution is kept. `mkl_service.h` is a stub.
- No PARDISO (Intel MKL or Panua) is involved: `SOLVER=PARDISO` runs Accelerate.
- Author's evidence (not reproduced here): 775 decks (CalculiX 2.24 suite with references, FreeCAD FEM tests,
  CalculiX-Examples); Accelerate matches the reference at least as often as SPOOLES in every feature group;
  9 of 775 differ from SPOOLES (8 round-off, 1 Newton abort). 2.4 M unknowns on M3 Pro: 37 s vs 64 s SPOOLES.

## What integration would take

- Take only `accel_pardiso.c`, `spooles_fallback.c`, `inc/mkl_service.h`; build them into our CalculiX 2.22
  (`pastix` stage, D070) with `-DPARDISO`. Not their binary (2.24, i4, no PaStiX) and not their `bin/ccx`
  launcher (it rewrites `SOLVER=` and routes nonlinear decks to SPOOLES).
- Adapt to our i8 build: `ITG` is `long long`; Accelerate and SPOOLES take 32-bit row indices, so copy and
  limit nonzeros to < 2³¹.
- Accelerate threads itself (GCD) and ignores `OMP_NUM_THREADS`, so PrePoMax's CPU setting does not apply.
- The SPOOLES fallback only prints `[accel] fallback…` to stderr; the marking requirement above needs more.
- macOS only. Linux ARM64 would need another backend; Windows x64 and Linux x64 have real Intel MKL PARDISO.
- Credit the author (GPL-2.0 is compatible with CalculiX and PrePoMax).

## Related observation for our build (not part of F002)

The author found ARM64 FMA contraction made CalculiX's Mohr-Coulomb test `mohr1` diverge and builds with
`-ffp-contract=off`. Our CalculiX build does not set that flag. Untested on our binary: run `mohr1` and record a
bug if it diverges.

## Candidate acceptance (if approved later)

1. `verify_solvers.py` compares PARDISO(Accelerate), SPOOLES and PaStiX on the solver corpus within reviewed
   tolerances; fallback cases are reported, not hidden.
2. The PrePoMax solver option and the solver log name Apple Accelerate; the release notes and bundle notice say
   "PARDISO = Apple Accelerate".
3. A PrePoMax default-settings job (`Pardiso`) runs to completion on macOS.

# B022 — SPOOLES's multithreaded solver gave wrong results on ARM64 (fixed 23 November 2026)

Found 23 November 2026 while building B020's fix (D070). With CalculiX's `Makefile_MT` (`USE_MT`), a frequency step
(ARPACK with SPOOLES; a C3D20R cantilever with a square section, so modes 3/4 are a pair) returned wrong eigenvalues
in some runs on Apple Silicon: 3 of 8 runs with 4 threads, 10 of 10 with 8 (e.g. 2210.9 for the pair 2144.4, or
values off by a factor of 5). Static solves stayed within 1e-7 of the serial result. Only SPOOLES's threads mattered
(`CCX_NPROC_EQUATION_SOLVER=1` with 4 OpenMP threads: 0 of 10 wrong; SPOOLES 4, rest 1: 4 of 10). The original Windows
`ccx_dynamic.exe` (also `USE_MT`) is stable on the same deck with 4 and 8 threads under Rosetta in the CrossOver
reference, which keeps x86's ordered stores.

ThreadSanitizer on SPOOLES 2.2 (clang `-fsanitize=thread`, the frequency deck, 8 threads): 127 data races in the
multithreaded factorization and solve. A first attempt (release/acquire on 44 status-flag sites) did not fix it.

## Cause

SPOOLES hands fronts (factorization) and solution blocks (solve) between threads through `ChvList`/`SubMtxList` and
`char` flags. `ChvList_init`/`SubMtxList_init` mark a list `'N'` ("no lock needed") when only one thread contributes
to it, but that thread is usually not the one that reads the list: producer and consumer then share the list head,
the objects and the count with no synchronization at all. `isListNonempty`, `isCountZero` and the `counts == 0` path
of `getList` also read without the lock. Under x86's ordered stores the consumer that sees the count reach zero also
sees the last object added; on ARM64 it can see the count first and the head (or the object's entries) late, and the
aggregate update is lost or read half-written. The solve's `frontIsDone[]` and `lowerIsDone/diagIsDone/upperIsDone[]`
flags are plain stores and loads, with the same problem for the solution blocks they publish.

## Fix

`ThirdParty/Build/patches/spooles-2.2-mt-memory-order.patch`, applied by `ThirdParty/Build/calculix-cpu.py` before
SPOOLES is built (recorded with its SHA-256 in the build report):
- `ChvList`/`SubMtxList`: when the list has a lock (the multithreaded case), every add, get and query takes it; the
  flags no longer skip it. A mutex orders the objects' contents with the hand-over.
- `FrontMtx/src/solveUtil.c`, `MT/src/solveMT.c`: the flags are written with release stores and read with acquire
  loads (`__atomic_store_n`/`__atomic_load_n`).
SPOOLES's algorithm and arithmetic are unchanged; the serial library behaves as before (no lock). ARM64 builds use
`USE_MT` again, as Windows does.

## Evidence (macOS ARM64)

- `X/Build/Pastix/verify_solvers.py` on the patched ccx, 10 runs with 4 threads and 10 with 8: SPOOLES reports 4/8
  threads; every SPOOLES result agrees with PaStiX (double) within 7.7e-7 (static; the thin plate) and the frequencies
  are identical to the serial SPOOLES build in all 20 runs (before the patch: 10 of 10 wrong with 8 threads). The one
  failing case is the known one (thin plate, PaStiX mixed precision, same on Windows).
- ThreadSanitizer, same deck, 8 threads: 11 reports, down from 127, all on statistics no result depends on: the timing
  array `cpus[]` that every solve thread adds to, and the entry counters `nentD`/`nentU` in `FrontMtx_storeFront`.
  The instrumented binary printed "Job finished" with correct frequencies and then exited with code 134; the normal
  build exits 0.

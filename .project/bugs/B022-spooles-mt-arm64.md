# B022 — SPOOLES's multithreaded solver gives wrong results on ARM64 (open; ARM64 builds use the serial SPOOLES)

Found 23 November 2026 while building B020's fix (D070). With CalculiX's `Makefile_MT` (`USE_MT`), a frequency step
(ARPACK with SPOOLES; a C3D20R cantilever with a square section, so modes 3/4 are a pair) returns wrong eigenvalues
in some runs on Apple Silicon: 3 of 8 runs with 4 threads, 10 of 10 with 8 (e.g. 2210.9 for the pair 2144.4, or
values off by a factor of 5). Static solves stayed within 1e-7 of the serial result. Only SPOOLES's threads matter
(`CCX_NPROC_EQUATION_SOLVER=1` with 4 OpenMP threads: 0 of 10 wrong; SPOOLES 4, rest 1: 4 of 10). The original Windows
`ccx_dynamic.exe` (also `USE_MT`) is stable on the same deck with 4 and 8 threads, run under Rosetta in the CrossOver
reference, which keeps x86's ordered stores.

ThreadSanitizer on SPOOLES 2.2 (clang `-fsanitize=thread`, the frequency deck, 8 threads): 127 data races in the
multithreaded factorization and solve (`FrontMtx_workerFactor`, `FrontMtx_workerSolve`, `assembleAggregates`,
`SubMtxList_getList`/`addObjectToList` and `ChvList` fast paths that test list heads before locking, `Chv_assembleChv`,
unlocked counters such as `nentU`). SPOOLES (1999) hands work between threads through plain flags and list heads that
it spins on; x86 hides this, ARM64's weaker ordering does not. Release/acquire on the status flags alone (44 sites) did
not fix it (2 of 20 wrong with 4 threads, 10 of 10 with 8).

Decision for now (D070): ARM64 builds (macOS, Linux ARM64) use the serial SPOOLES, which is correct and what the
previews had; PaStiX is the multithreaded direct solver there (stable: 10 of 10 runs on 8 threads, static and
frequency). x86-64 builds keep `USE_MT` as Windows has it. A real fix means making SPOOLES's MT layer (lists, flags,
counters) properly synchronized, then ThreadSanitizer clean and repeated-run checks; to discuss with the maintainer.

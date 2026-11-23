# B020 — SPOOLES ran on one thread on macOS/Linux (x86-64: multithreaded; ARM64: see B022)

Found in the solver audit of 23 November 2026 (D070). The original `ccx_dynamic.exe` links the multithreaded SPOOLES
(`FrontMtx_MT_factor`, "Using up to N cpu(s) for spooles"; CalculiX's `Makefile_MT`, `USE_MT`); our ccx linked the
serial library, so PrePoMax's CPU setting (OMP_NUM_THREADS) had no effect on the SPOOLES factorization.

Fix: `calculix-cpu.py` builds SPOOLES's `MT` library and ccx with `-DUSE_MT=1` on x86-64 (Linux x64, Windows).
On ARM64 the multithreaded SPOOLES gives wrong results in some runs (B022), so ARM64 builds keep the serial SPOOLES and
PaStiX is their multithreaded direct solver. `X/Build/Pastix/verify_solvers.py` checks the thread count each direct
solver reports (`--spooles-threads 1` for a serial build).

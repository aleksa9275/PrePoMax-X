# B020 — SPOOLES ran on one thread on macOS/Linux (fixed: multithreaded on every target)

Found in the solver audit of 23 November 2026 (D070). The original `ccx_dynamic.exe` links the multithreaded SPOOLES
(`FrontMtx_MT_factor`, "Using up to N cpu(s) for spooles"; CalculiX's `Makefile_MT`, `USE_MT`); our ccx linked the
serial library, so PrePoMax's CPU setting (OMP_NUM_THREADS) had no effect on the SPOOLES factorization.

Fix: `calculix-cpu.py` builds SPOOLES's `MT` library and ccx with `-DUSE_MT=1` on every target. On ARM64 that needed
B022's fix (SPOOLES's thread hand-over was safe only on x86). `X/Build/Pastix/verify_solvers.py` checks the thread
count each direct solver reports.

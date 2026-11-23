# B018 — CalculiX had no PaStiX in the macOS/Linux packages (fixed on macOS, D070)

Found by the maintainer, 23 November 2026, following the forum thread "A case for CalculiX 2.22"
(PASTIX_MIXED_PRECISION=0 for thin shells).

The original release ships `Solver/ccx_dynamic.exe` (the official CalculiX 2.22 Windows build) with PaStiX linked
statically (`pastix_task`, `PASTIX_MIXED_PRECISION`, `PASTIX_GPU`) and PARDISO through MKL. Our CalculiX 2.22
(`ThirdParty/Build/calculix-cpu.py`, `-DSPOOLES -DARPACK`) has neither: choosing PaStiX stops with "the PASTIX library
is not linked". So only SPOOLES works on macOS and Linux. D060 names PARDISO as the only accepted exception; PaStiX is
not one, and earlier records missed this.

CalculiX 2.22's own recipe (`README.INSTALL`, `Makefile_i8`, `make_*.sh`): an 8-byte-integer (i8) CalculiX linked
with PaStiX4CalculiX (github.com/Dhondtguido/PaStiX4CalculiX), hwloc, PaRSEC (the bitbucket fork), Scotch 6.0.8 (i8)
and an i8 OpenBLAS; CUDA optional (NVIDIA only, not on macOS). To do: recipes for these, an i8 build of the whole
solver (also SPOOLES and ARPACK), and checks of PaStiX against SPOOLES on solid and thin-shell cases, including
PASTIX_MIXED_PRECISION=0.

Fix (macOS ARM64, D070): `X/Build/Pastix/build.py` builds the stack from pinned sources (`source-lock.json`): OpenBLAS
0.3.34 ILP64 (sequential, locking), hwloc 2.1.0, Scotch 6.0.8 (INTSIZE64), PaRSEC (mfaverge fork `83ff82ec`), and
PaStiX4CalculiX from its CUDA-optional branch (Kabbone `1b15d792`, Dhondtguido's tree `d6b493bc` plus 5 commits that
make CUDA and PaRSEC optional; Dhondtguido's tree calls cuBLAS outside the GPU kernels and cannot build without CUDA;
the Windows binary has the CUDA entry points but no cuBLAS, so it was built with CUDA stubbed). Fixes needed on a
current toolchain, recorded in the recipe receipt: C17 for 2019 code under GCC 16, libatomic in the static PaRSEC,
PaRSEC's `zone_malloc.h` installed, PaStiX's fixed `gcc-ar` and linker flags, its precision generator on Python 3.12+,
and `LAPACK_ILP64` (OpenBLAS's LAPACKE header defaults to 32-bit integers; without it PaStiX crashed in sgemm).
`ThirdParty/Build/calculix-cpu.py --pastix` builds ccx as `Makefile_i8` (`-DINTSIZE64 -DPASTIX -DPASTIX_FP32
-DPASTIX_GPU`, `-fdefault-integer-8`, ARPACK i8). `X/Build/Pastix/verify_solvers.py` compares PaStiX (mixed
precision and `PASTIX_MIXED_PRECISION=0`) with SPOOLES. Linux: later (D070).

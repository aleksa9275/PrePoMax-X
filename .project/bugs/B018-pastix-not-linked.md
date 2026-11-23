# B018 — CalculiX has no PaStiX in the macOS/Linux packages (open, parity gap)

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

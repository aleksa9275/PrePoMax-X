# ARPACK-ng 3.9.1 source

All 479 regular files are retained unchanged under `src/`, removing only the
top-level directory of the official tag archive:
https://github.com/opencollab/arpack-ng/archive/refs/tags/3.9.1.tar.gz
(retrieved 2 November 2026). Archive SHA-256:
`f6641deb07fa69165b7815de9008af3ea47eb39b2bb97521fbf74c97aba6e844`.
The source manifest fingerprints every extracted file. Preserve original
attribution and the BSD license in `src/COPYING`.

The research recipe builds a static, sequential, 32-bit integer interface using
explicit OpenBLAS BLAS/LAPACK libraries. This is an identified native dependency,
not a claim to reproduce the unproven Windows ARPACK/PaStiX build chain. No MPI
library from the incidental Homebrew ARPACK installation is linked.

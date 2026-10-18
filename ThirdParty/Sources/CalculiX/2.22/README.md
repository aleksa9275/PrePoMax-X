# CalculiX CrunchiX 2.22

`src/` contains all 1188 regular files (11372771 bytes), byte-for-byte from the
official [2.22 source archive](https://www.dhondt.de/ccx_2.22.src.tar.bz2), retrieved
2026-10-18. The original `CalculiX/ccx_2.22/` archive prefix is removed, retaining
`src/` and every file unchanged. SHA-256 of the 1536859-byte archive:

`3a94dcc775a31f570229734b341d6b06301ebdc759863df901c8b9bf1854c0bc`

[source-manifest.json](source-manifest.json) fingerprints every extracted file.
There are no local patches. Preserve upstream attribution and the original
[GPL version 2 text](src/gpl-2.0.txt); this source carries its own license rather
than being relabeled with PrePoMax-X's root license.

The upstream `README.INSTALL`, Makefile and PaStiX build scripts are retained.
Default Makefile selects SPOOLES/ARPACK. PaStiX instructions additionally require
BLAS, hwloc, PaRSEC, Scotch and PaStiX4CalculiX, with integer-ABI requirements and
local build paths. Scripts are upstream examples, not verified portable recipes.

Existing retained native Windows solver evidence reports CalculiX 2.22 with
PaStiX 6.0.1 and pinned Intel MKL runtime DLLs. This archive alone does **not**
establish the corresponding source/patch/compiler/ABI chain for that binary.
No macOS/Linux binary is accepted, built or substituted by recovering source.
Additional solver/dependency source recovery and explicit backend/ABI comparison
remain before native numerical acceptance and public distribution.

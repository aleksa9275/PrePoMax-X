# B019 — CalculiX without external behaviours (user material libraries) on macOS/Linux (fixed on macOS, D070)

Found in the solver audit of 23 November 2026 (D070), comparing the original `Solver/ccx_dynamic.exe` with our ccx.

The Windows binary is built with `CALCULIX_EXTERNAL_BEHAVIOURS_SUPPORT` (CalculiX's `Makefile_MFront`): it carries
`calculix_registerExternalBehaviour`, `call_external_umat` and libltdl's `lt_dlopen`, so a `*MATERIAL` can name a
user material in a shared library (Abaqus UMAT interface, MFront) that ccx loads at run time. Our ccx was built
without the flag: such a material stops with an unknown material.

Fix: `ThirdParty/Build/calculix-cpu.py` builds with `-DCALCULIX_EXTERNAL_BEHAVIOURS_SUPPORT` (`external.c` uses
`dlopen` on macOS/Linux). Not yet checked with a real user material library (none in the test set).

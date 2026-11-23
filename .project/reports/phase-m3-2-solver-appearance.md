# M3-2 — the solver as the Windows release builds it; the dark appearance (D069, D070)

23 November 2026, macOS ARM64. The maintainer found that PaStiX did not work in the previews (B018), asked for the
PaStiX build and a dark theme for macOS (Linux after macOS is complete and local Forgejo CI exists), for every solver
to be multithreaded, and for certainty that PARDISO is the only missing piece.

## Audit: what the original release has that the previews did not

Compared with the 3.0.1 release (`Solver/ccx_dynamic.exe`: strings, linked libraries; every native file of the
release; `Globals.cs` paths):

| | Windows release | previews (≤ 4) | now (macOS ARM64) |
|---|---|---|---|
| SPOOLES | multithreaded (`USE_MT`) | serial | serial (B022), multithreaded on x86-64 builds |
| PaStiX (PaStiX4CalculiX, i8) | linked, CUDA stubbed | missing (B018) | linked, multithreaded |
| PARDISO (MKL) | linked | missing | missing (D060's exception) |
| external behaviours (user UMAT/MFront libraries) | linked | missing (B019) | linked |
| iterative scaling / Cholesky, ARPACK, SGI/TAUCS | built in / built in / not linked | same | same |
| Tools - Bidirectional Mesh Converter | third-party Windows PyInstaller exe | not shipped | not shipped (B021: no public source) |
| embedded Python 3.12 (Tk, ssl, sqlite) | yes | yes (python-build-standalone) | yes |

So the previews' claim "PARDISO is the only exception" was wrong in four places. The solver ones are fixed or recorded;
the Mesh Converter needs upstream (its source).

## PaStiX (B018)

`X/Build/Pastix/build.py` builds CalculiX 2.22's PaStiX stack from pinned sources (`source-lock.json`), static, 8-byte
integers: OpenBLAS 0.3.34 (ILP64, sequential with locking), hwloc 2.1.0, Scotch 6.0.8 (`INTSIZE64`), PaRSEC (mfaverge
fork `83ff82ec`) and PaStiX4CalculiX. Dhondtguido's repository (`d6b493bc`, the one README.INSTALL names) calls cuBLAS
outside the GPU kernels and does not build without CUDA; the Windows binary has the CUDA entry points but no cuBLAS. The
recipe uses the `cudaless` branch of Kabbone/PaStiX4CalculiX (`1b15d792`): the same tree plus 5 commits by the
contributor whose work that repository merged, making CUDA and PaRSEC optional.

Fixes the 2019 sources needed on a current toolchain (all in the recipe and its receipt): C17 (GCC 16 defaults to C23),
libatomic in the static PaRSEC, PaRSEC's `zone_malloc.h` installed, PaStiX's fixed `gcc-ar` and replaced linker flags,
its precision generator on Python 3.12+ (`imp`, `\s` in replacements), and the integer width at the BLAS boundary:
PaStiX bundles 32-bit reference `cblas.h`/`lapacke.h` that shadow OpenBLAS's ILP64 headers, and OpenBLAS's
`lapacke_config.h` needs `LAPACK_ILP64`. On Apple ARM64, stack arguments are not widened, so `cblas_?ger`/`?trsm`
received garbage leading dimensions and crashed; on Linux x86-64 this usually works by accident.

`ThirdParty/Build/calculix-cpu.py --pastix` builds ccx as `Makefile_i8` (`-DINTSIZE64 -DPASTIX -DPASTIX_FP32
-DPASTIX_GPU`, `-fdefault-integer-8`, ARPACK i8) with external behaviours (`Makefile_MFront`). `build_ui.py` has a
`pastix` stage before `solver`, and stage fingerprints: a finished stage is reused only while the SHA-256 of its recipe
files, source locks and the stages it uses are unchanged.

## Multithreading (B020, B022)

`X/Build/Pastix/verify_solvers.py` runs a C3D20R cantilever (static, NLGEOM, frequency) and a thin S8R plate (span/
thickness 1000) with SPOOLES, PaStiX and PaStiX with `PASTIX_MIXED_PRECISION=0`, and checks the threads each solver
reports. PaStiX: 4 threads, displacements within 2.5e-10 of SPOOLES, frequencies equal; 10 of 10 repeated runs on 8
threads correct.

Multithreaded SPOOLES (`USE_MT`, as Windows) returned wrong eigenvalues in some runs on Apple Silicon (3 of 8 with 4
threads, 10 of 10 with 8); the Windows binary is stable on the same deck (Rosetta keeps x86 ordering). ThreadSanitizer:
127 data races in SPOOLES 2.2's MT factorization and solve (unsynchronized flags, list heads, counters). Fencing the
44 flag sites was not enough. ARM64 builds therefore keep the serial SPOOLES (correct, as the previews had), PaStiX is
their multithreaded direct solver, and x86-64 builds keep `USE_MT`. A real fix is B022 (to discuss).

The thin plate with PaStiX's default mixed precision gives a wrong result (0.27 for 65.1; the iterative refinement does
not converge) — the forum thread's case. The original Windows `ccx_dynamic.exe` gives the same wrong result (0.32) and
the right one with `PASTIX_MIXED_PRECISION=0`, as ours does: CalculiX's behaviour, at parity, recorded as a failure in
the check with that note. B017 (the environment variables' Active check box) makes the variable usable in the app.

## The dark appearance (D069)

`X/App/FrontEnd/Theme.cs`: a palette in the manner of the Claude apps (warm greys, #262624 forms, #1F1E1D lists and
editors, clay accent), the original's system colours mapped, its fixed whites and greys inverted at the drawing,
colours with a hue kept (data), dark icon outlines lightened, the 3D view's background drawn as warm light greys (the
Graphics settings keep their colours; `VtkNativeView.BackgroundFilter`, a 4-line hook). One toggle button at the right
end of the main window's first tool strip row (the maintainer's placement) switches the running application; the
choice is PrePoMax-X's `appearance.json` (or `PREPOMAXX_THEME`), not the original's settings. Light stays the default
and unchanged. Forms probe in dark: 120 of 121, the same as light (the one failure: the local app has no
`materials.lib`, as always).

## Evidence (macOS ARM64)

The macOS package (preview 5, 215 MiB zip), unpacked, under `sandbox-exec` with the repository, the P1 checkout,
Homebrew and .NET denied, on a fresh HOME:
- `verify-app.py --scripts --legacy-pmx`: 12 of 12 steps; app probe 16/16; probe areas forms 126/126 (two more than
  M3-0: B017's environment-variable check box), geometry 4/4, results 9/9, elements 5/5; upstream's four Python tests;
  the release's Profile and Bearing_bracket open.
- `verify_solvers.py` on the bundled, relocated ccx (no Homebrew): SPOOLES 1 thread, PaStiX 4 threads; all cases pass
  except the recorded one (thin plate, PaStiX mixed precision, same on Windows).
- The bundled ccx is byte-identical across two builds from the same inputs (`b801d9d5…`).
- Dark appearance: forms probe 120/121 in dark and light alike on the local app; the live switch captured before and
  after (panels, tree, icons, view).
- Not run: upstream's full suite on this package (B016 unchanged); Linux.

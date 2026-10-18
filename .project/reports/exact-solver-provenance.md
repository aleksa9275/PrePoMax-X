# Exact PrePoMax solver: RC2 identity, source and native-platform constraints

Policy update, 2026-10-18: [task 0026 assessment](without-pardiso-assessment.md)
and D042 narrow the historical complete-backend requirement in this report.
Maintainer rejects Panua's machine-bound licensing and requires a new
alternative only if omitting PARDISO cripples functionality. Exact Windows
identity findings remain valid; reproducing Intel MKL on ARM64 is no longer
automatically a release prerequisite. Existing SPOOLES/PaStiX need native
correctness/capacity evaluation; no default or numerical policy is changed.

2026-10-18. [Task 0025](../tasks/0025-exact-solver-provenance.md), research only.
Maintainer requires the complete original software adjusted for cross-platform
use, with no solver/backend substitution or lost functionality. All existing
implementation remains uncommitted and unchanged by this research.

## Finding — RC2 uses the official Windows CalculiX binary unchanged

The earlier build-gap wording did not establish a different or Matej-modified
solver. The direct archive comparison now resolves the distributed binary:

| Downloaded authoritative archive | Bytes | SHA256 |
| --- | ---: | --- |
| [PrePoMax v3.0.0 RC2](https://prepomax.fs.um.si/Files/Downloads/PrePoMax%20v3.0.0%20RC2.zip), linked by the official downloads page on 17 October 2026 | 200965011 | 26d3c6f801651802a399c980c0ca7bab38d7a8433f3860b22832004fc0142fb3 |
| [Official CalculiX 2.22 Windows archive](https://www.dhondt.de/calculix_2.22_4win.zip) | 36675939 | a1f91281944c96d6cd914cc020421e8ae65973b3e15d055dc63a3e3e3066d281 |

RC2's 48560044-byte `Solver/ccx_dynamic.exe` has SHA256
`1c1f4ad9392c0a9537e9ff1d7adaf86ea0a6193da5916abb2912ae541e530c10`.
It is **byte-identical** to the official archive's executable and the exact
PrePoMax 2.6/native-Windows/CrossOver reference previously captured. RC2's five
bundled DLLs also match every previous reference checksum. Its README_Install
is byte-identical to the official README; http.txt points to the upstream kit.
This is direct observation, not a website's claim of equivalence.

[Archive/PE inspection](exact-solver-provenance/archive-comparison.json) records
all member sizes/hashes/CRC values, x64 PE machine type, import libraries and
file-version resources. The official binary imports KERNEL32, msvcrt and
mkl_rt.2.dll; the runtime closure additionally uses Windows CRT/runtime services.
Archives/binaries stay outside Git; only metadata, primary notices and synthetic
research evidence are retained. The official downloads page's older explanatory
2.20 link is stale relative to the actual RC2 package; it was not used as version
proof. [Official download listing](https://prepomax.fs.um.si/downloads/).

## Finding — the full solver is more than the default stock Makefile

The official README names **Rafał Brzegowy** as binary provider and points to the
same official ccx_2.22.src.tar.bz2 already recovered unchanged in ThirdParty/Sources.
It explicitly describes ccx_dynamic.exe as statically linked SPOOLES/PaStiX plus
dynamically linked PARDISO requiring Intel oneAPI MKL. ccx_static.exe omits PARDISO;
it is therefore not an equivalent replacement for PrePoMax's dynamic executable.

Verified executable markers, retained execution and PE resources establish:

| Component/capability | Evidence and identity status |
| --- | --- |
| CalculiX 2.22 | Actual version banner, official archive identity, official README source pointer; canonical core archive recovered unchanged |
| PARDISO | Dynamic Intel MKL backend; direct executable import of mkl_rt.2.dll and successful explicit PARDISO research run |
| Intel MKL | mkl_rt/core/intel_thread file-version resources 2022.2.1.0; mkl_def 2022.1.1.0; exact mixed DLL bytes pinned rather than replaced by a newer uniform set |
| Intel OpenMP runtime | Exact libiomp5md.dll fingerprint, PE version resource 5.0.2021.428 and dependent CRT imports retained |
| PaStiX | Runtime reports 6.0.1, Scotch ordering, no GPUs and PaRSEC disabled in this fixture; exact fork revision/complete flags remain unknown |
| SPOOLES | Original README and multithreaded FrontMtx_MT_* symbols; exact library source/patch/build still needs matching manifest |
| ARPACK-NG | Embedded arpack-ng-3.9.1 source paths and dsaupd_/dseupd_ symbols; eigensolver execution not covered by the cube |
| hwloc | Embedded hwloc-2.11.1 source paths; complete transitive source/build closure remains to recover |
| OpenBLAS | Embedded OpenBLAS implementation markers; precise version/configuration and linked call routing remain unresolved |
| Compiler/runtime | Embedded MSYS2 GCC/gfortran 14.1.0 and several other GCC archive version markers; one string cannot establish all component toolchains/flags |
| Iterative scaling/Cholesky | Original exposed options and successful explicit fixture executions |

PrePoMax's normal GUI default is **PARDISO**, verified in
PrePoMax/Settings/SolverSettings.cs Reset, FrmStep's new-step assignment and
CalStaticStep.GetKeywordString. Original SolverTypeEnum also exposes PaStiX,
Spooles and both iterative choices. Full parity must retain all those choices,
not only make the test cube solve. The bounded new development static-deck CLI
currently permits only SolverType.Default; that is a documented partial feature,
not full PrePoMax solver-default parity.

There are two distinct defaults. Original ccx ini_cal.c selects the executable's
compiled backend preference; with PASTIX defined it chooses PaStiX before PARDISO
and SPOOLES. Our no-SOLVER cube indeed reports PaStiX. PrePoMax's GUI explicitly
assigns PARDISO to new steps. Calling both simply “the default solver” obscures
this difference. Generic third-party claims that ccx always defaults to SPOOLES
are not valid for this binary. Preserve the actual application and executable
semantics separately. PaStiX precision/environment/thread behavior also matters;
original pastix.c and retained runtime settings must not be silently normalized.

## Verified experiment — unchanged exact program can execute on this Mac

The already isolated CrossOver reference bottle contains exactly those six
RC2-matching executable/runtime files. The new research harness verifies all six
fingerprints before executing, changes only the synthetic fixture's SOLVER
selection, uses disposable work directories and fixes the recorded thread
controls to one. The existing analytical checker and its tolerances are reused.
No production executable, solver profile/default, algorithm or model is changed.

| Fixture selection | Exit | Analytical checks | Comparison to retained native Windows |
| --- | ---: | --- | --- |
| No explicit solver | 0 | 7/7 pass | Pass; runtime chooses PaStiX |
| PARDISO | 0 | 7/7 pass | Pass |
| PaStiX | 0 | 7/7 pass | Pass |
| SPOOLES | 0 | 7/7 pass | Pass |
| Iterative scaling | 0 | 7/7 pass | Pass |
| Iterative Cholesky | 0 | 7/7 pass | Pass |

All six preserve displacement/stress/reaction IDs and agree within the already
reviewed printed-DAT tolerances (1e-9 mm displacement, 1e-5 N force, 1e-4 MPa
stress; the analytical checker separately checks transverse/shear zero at 1e-5).
Displacements have zero printed difference; the largest measured force/stress
component difference from the old native Windows reference is approximately
1.61e-13/1.12e-12. This is not byte-identical output or arbitrary-model acceptance.
[Actual commands/results and raw synthetic files](exact-solver-provenance/backend-research/verification.json)
are retained, including both streams and every input/output fingerprint.

These are **Windows x64 machine instructions through CrossOver on Apple Silicon**,
not native ARM64 solver builds. Six successes on one linear C3D8 cube do not prove
frequency/buckling, thermal, nonlinear/contact, large models, multithreading,
error behavior or full RC2 application parity. They establish a real compatibility
route for the exact executable and full exposed backend list on this fixture.
CodeWeavers documents Apple Silicon support; platform/runtime distribution and
broader compatibility remain separate work, not a frontend/runtime selection.

## Source/build recovery — useful leads, exact remaining gaps

The canonical CalculiX core source and binary publisher are now identified. The
remaining correspondence gap is the complete binary build, not an unknown
PrePoMax-only numerical engine. Required recovery includes exact local patches,
flags, integer widths at every interface, PaStiX/Scotch revisions, BLAS routing,
OpenBLAS settings, ARPACK/SPOOLES/hwloc inputs and compiler/runtime versions.

The executable's provider publicly references the CUDA-free
[Kabbone PaStiX4CalculiX fork](https://calculix.discourse.group/t/calculix-and-pastix-solver-windows-version/130?page=4).
Its cudaless branch's latest commit before the reference's August 2024 build is
[1b15d792bdf5c6ac4e89e377766668f225b5a4d4](https://github.com/Kabbone/PaStiX4CalculiX/commit/1b15d792bdf5c6ac4e89e377766668f225b5a4d4),
dated 2020-08-16. The inspected CMake file declares 6.0.1 and exposes CUDA/integer
options. This is a **candidate**, not a proven source revision for the RC2 binary:
the cited reply discusses an older version and does not give the August 2024
build manifest. Do not label it corresponding source merely because versions fit.

The same maintainer's public MSYS2 recipe is another lead, not an exact recipe
for this executable: history before the reference build contains a 2.21 package,
whereas today's recipe is 2.23 with newer patches/dependencies. The different
[Linux PaStiX build scripts](https://github.com/rsmith-nl/calculix-build-pastix)
apply patches and build an i8 executable, so they demonstrate build techniques,
not the exact shipped ABI/configuration.

A separately published [build provenance](https://github.com/OmnibusCloud/CalculiX/blob/main/PROVENANCE.md)
independently reports the same executable checksum, and its mirror explicitly
leaves the PaStiX/Scotch revision correspondence open. It is corroborating
builder research, not authority to accept their replacement binaries. Our hash,
PE and execution conclusions above were checked independently. No third-party
replacement was downloaded or selected.

Targeted source request to the named binary provider, if needed: identify
ccx_dynamic.exe SHA256 1c1f4ad9… built 2024-08-04; request exact ccx source/patches,
Makefile/CMake recipes, all static dependency archives/revisions/configuration,
Scotch/PaStiX commits, i4/i8/LP64/ILP64 boundaries, BLAS/LAPACK routing, toolchain
and threading/precision flags. Ask Matej to confirm retaining this bundle for
stable 3.0. No message has been sent; research does not authorize contacting them.

## Native ARM64 constraint and route that preserves identity

Intel's documentation supports the required MKL CPU component on **Intel 64**;
its macOS architecture page likewise identifies Intel 64, and macOS toolkit
support ends starting in 2024.0. No supported native ARM64 build of this exact
MKL/PARDISO implementation was identified for Apple Silicon or Linux ARM64.
This constraint applies even though CalculiX's own Fortran/C and other backends
can be compiled for ARM. The open-source oneMath interface project is not the
proprietary MKL CPU/PARDISO implementation and does not remove this gap.
[Intel 2022 requirements](https://www.intel.com/content/www/us/en/developer/articles/system-requirements/onemkl-system-requirements-2022.html),
[Intel macOS architecture](https://www.intel.com/content/www/us/en/docs/onemkl/developer-guide-macos/2024-0/architecture-support.html),
[Intel macOS support notice](https://www.intel.com/content/www/us/en/docs/onemkl/developer-guide-macos/2024-0/overview.html),
[oneMath supported domains/backends](https://github.com/uxlfoundation/oneMath).

| Target | Keeping the exact complete solver stack |
| --- | --- |
| Windows x64 | Use the already identified unchanged executable and five DLLs; recover complete source/build closure and validate full 3.0 workflow |
| Linux x64 | Native rebuild with the same ccx/backends and matching Linux MKL version is a feasible route, pending exact build recovery and broad comparisons; resulting ELF is a different binary, not yet proven equivalent |
| macOS ARM64 | Exact Windows executable works through existing CrossOver on the bounded fixture; that preserves program bytes but is not native ARM computation. Native PARDISO/MKL identity is unresolved |
| Linux ARM64 | Same native MKL/PARDISO gap; using an unchanged Windows solver on an x64 worker preserves the program. Local translation/emulation remains an experiment, not verified here |

If **complete unchanged solver software** is mandatory on every client, retain
the canonical Windows executable/runtime and investigate an explicit compatibility
or Windows-worker execution route for unsupported hosts. A native cross-platform
application can delegate an external solve, but remote/translated computation
is a product architecture decision and has not been selected. Preserve offline
and native requirements explicitly; do not present that route as native parity.
CodeWeavers's stable Linux requirements remain x86-oriented, while its announced
ARM preview work needs version-specific validation; “CrossOver runs on Linux”
alone does not establish Linux ARM64 support.
[CodeWeavers requirements](https://www.codeweavers.com/crossover),
[announced ARM work](https://www.codeweavers.com/blog/mjohnson/2026/06/11/whats-in-and-whats-out-for-crossover-27).

If native computation on all four targets is also mandatory, an alternate
PARDISO implementation or backend would be a substantive approved change, not
100% identical dependency software. Do not remove PARDISO, rewrite SOLVER= cards,
or silently fall back to PaStiX/SPOOLES to hide that mismatch. Also, identical
program source does not guarantee bitwise numerical output across CPU/compiler/
thread schedules. Keep source/backend identity and broad measured engineering
comparisons as separate acceptance gates; no tolerance is relaxed here.

The literal “all third-party source” objective also has a vendor-source gap:
Intel MKL is a vendor binary dependency, not recovered public source that can
simply be placed under ThirdParty/Sources. Do not silently claim an entirely
source-rebuildable original stack or weaken that release requirement.

Recommended next work: freeze the verified RC2 Windows bundle as conformance
reference; obtain the complete original build recipe; reproduce all available
backends on x64 and test nonlinear/contact, eigenvalue/buckling, thermal and
thread/error/output behavior; then make an explicit ARM execution decision.
Keep the exact original software as the oracle throughout. This research changes
no production solver, native build profile, default, numerical policy or package.

## Follow-up — can we port PARDISO itself to ARM64?

Maintainer asks whether PARDISO implementation source is available to port.
Checked 2026-10-18: the exact **Intel MKL PARDISO** used by the original binary
is closed source; no publicly available implementation source or supported ARM64
build was identified. CalculiX's GPL `src/pardiso.c`/`pardiso.h` are integration
code, not the sparse solver engine: they prepare matrices and call MKL's PARDISO
and MKL threading services (pardiso.c lines 28, 302–305, 341 onward). Making this
wrapper compile on ARM does not supply the missing backend implementation.
[Eigen's own MKL integration documentation](https://libeigen.gitlab.io/eigen/docs-master/TopicUsingIntelMKL.html)
explicitly identifies closed-source MKL and its x86-oriented availability;
[Intel-hosted source/interface clarification](https://community.intel.com/t5/Intel-oneAPI-Math-Kernel-Library/Intel-OneAPI-MKL-How-to-use-legac-FORTRAN-libraries-specififally/m-p/1445019/highlight/true)
distinguishes Fortran interface declarations from proprietary computational code.
The oneMath open-source interface project is also not that implementation.

**Panua-Pardiso already supports ARM**, according to its vendor. Its product page
lists Linux, Windows and Mac (Intel and Arm), requires vendor-account/license
provisioning and explicitly distinguishes its evolved implementation from the
Intel MKL branch. This is a viable native integration research lead, not an
ARM build of the exact Intel implementation. No public downloadable engine
source was identified on those vendor pages; source access and public-app/OEM/
redistribution arrangements would require direct vendor confirmation. Do not
infer permission to bundle it from a personal machine license.
[Panua product/platform/licensing information](https://panua.ch/pardiso/).

Possible work: seek Intel's ARM/source-access position for the exact engine;
or, if a different licensed implementation is explicitly accepted, assess the
Panua adapter/API and whole-application distribution requirements and validate
against the exact original reference. Matrix types, phases, integer ABI, option
meaning, errors, precision/threading and all relevant analysis classes require
comparison. No vendor contact, account/license purchase, code/backend change
or relaxation of the maintainer's identical-software requirement occurs here.

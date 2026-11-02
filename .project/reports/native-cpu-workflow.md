# Native CalculiX CPU workflow — task 0038

2 November 2026. **Verified:** original C# definitions/deck → native ARM64
CalculiX 2.22 → original FRD/DAT/STA readers completes on this Mac. Twelve bounded
workflow checks and the existing altered-displacement negative control pass.
This closes the first native cube workflow, not general solver acceptance.

The recipe builds unchanged recovered core sources with serial SPOOLES 2.2 and
sequential static ARPACK-ng 3.9.1/int32, using OpenBLAS 0.3.34/LP64, GCC/gfortran
16.2.0 and CMake 4.4.5. No PaStiX/PARDISO implementation is claimed. Backend and
dependency identity differ from the retained Windows 2.22 reference build; the
version is not silently upgraded to PrePoMac's 2.23.

`ThirdParty/Build/calculix-cpu.py` verifies the recovered source manifests,
builds in a new disposable directory and records portability changes, commands,
compilers, binary/load-path/runtime hashes. Three successful link outputs shared
the binary SHA-256 `c8eb0df883edff6bca85d0de05e9db188d6e08df5ed801044f31c1db7ee9b18b`;
this is an observation on this toolchain, not a universal reproducible-byte claim.
The pristine 1188 CalculiX, 1809 SPOOLES and 479 ARPACK-ng files remain unchanged.
The [build report](native-cpu-workflow/build-report.json) identifies the exact
recipe and runtime closure. Build transcripts stay in ignored local artifacts;
corresponding commands/source/compiler/runtime fingerprints are retained here.

The original job boundary accepts an explicitly supplied research build registry
and verifies both solver bytes and external runtime load-path hashes before
launch. Its default registry and Windows reference stay intact. Reference runs
set OMP/MKL/OpenBLAS threads to one. Completion/version/output checks remain
separate from numerical checks; run.json still says numericalAcceptance=false.

The 1 mm cube, E=210000 MPa, ν=0.3, 100 N loading passes the existing analytical
displacement tolerance 1e-9 mm, axial stress tolerance 1e-4 MPa and transverse/
shear/force tolerance 1e-5. Eight integration-point stresses and the supported
face's −100 N balance pass. Original FRD fields DISP/STRESS/TOSTRAIN/FORC retain
step 1, increment 1, time 1 and node/element IDs; original DAT yields 96 component
histories. [Workflow JSON](native-cpu-workflow/workflow.json), actual generated
[deck](native-cpu-workflow/analysis.inp), [DAT](native-cpu-workflow/analysis.dat),
[FRD](native-cpu-workflow/analysis.frd) and transport/status records are retained.

The first run exposed [B001](../bugs/B001-duplicate-element-set.md): our mesh
adapter emitted a set implicitly and explicitly, duplicating DAT stress rows.
It now delegates original element formatting without an inline set name and
writes explicit memberships once. Original parser/keyword/numerical algorithms
and tolerances are unchanged. A named regression and the actual solve cover the
failure; before-fix inputs/outputs remain in the evidence folder.

Affected current-source analysis passes **332 accepted checks**, preserving the
two original correctness failures/tetra gate. Current execution passes **49
checks**, positive planning/monitor/availability contracts and 13 rejection
controls, including external-runtime tampering. Ten replay and nine analysis
ownership guards pass. Targeted checks take about 15 s/13 s; unrelated historical
matrices were not repeated. Source/reproduction manifests remain in local
X/Checks artifacts, with verifier outcomes retained here.

**Open:** Linux/Windows execution of this new workflow, PaStiX performance route,
shell/modal/nonlinear/contact/capacity corpus, native runtime relocation and full
corresponding-source/license closure for OpenBLAS/compiler/transitive runtimes.
The executable currently requires its pinned Homebrew libraries. No public solver
binary, production default, precision change or complete four-target/native-tool
release acceptance follows. Existing correctness/full-graph/Windows/net48/RC2/
CAD/persistence/installers/Homebrew requirements remain.

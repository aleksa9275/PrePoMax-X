# Portable native job boundary and organized dependency source

2026-10-18. [Task 0024](../tasks/0024-native-job-boundary.md) continues the
accepted native solve/results work. The maintainer additionally requires an
understandable final source repository and a public release branch serving
installers, Homebrew and other package managers. [Repository map](../REPOSITORY_LAYOUT.md)
records this requirement and planned x/release lane. All task 0022–0024 work
remains **uncommitted**; no new branch, public package, push or integration occurs.

## Verified observation — native process implementation

A new X/Execution partial build reuses the existing original CaeJob.ExecutableJob
constructor, Submit/progress/status/output behavior and original JobStatus in
**CaeJob**. Mechanical source checks reconstruct original bodies from de8f7303
and require equal extraction at RC2 912fb3d0 and post-RC2 f6273e39. WMI process
traversal, Windows job registration and original Run/Kill stay in
ExecutableJob.Legacy.cs, included exactly once by the original net48 project.
JobStatus moves unchanged out of AnalysisJob.cs into its own original-owned file.
The full AnalysisJob remains coupled and is not claimed portable.

ExecutableJob.Portable.cs supplies the modern platform methods: structured
argument tokens, no shell, working directory/environment, actual exit status,
separate stdout/stderr, bounded deadline, cancellation and attached child-tree
termination. Fresh log files are reserved with CreateNew; existing evidence is
preserved. The existing concurrent-run flag serializes one executable within a
host unless explicitly enabled. New transient state is NonSerialized; original
persisted field/event shape and enum names/numbers are checked. This partial is
excluded from original net48, which retains its Windows implementation.

`PrePoMaxX.Solve` exposes:

- `availability`: pinned profiles for the native host; installed binary presence
  is not inferred without a directory.
- `run-static`: strict known profile/host/executable/runtime hash checks, original
  static deck generation, a new run directory, single-thread OMP/MKL execution,
  Ctrl-C cancellation and run.json with real status/exit, stdout/stderr, reported
  version and output-file fingerprints. Version/output-file checks do not imply
  numerical acceptance; the report explicitly keeps numericalAcceptance=false.
- `inspect-monitor`: reuse the **unchanged original CalculixMonitorDataParser**
  for actual retained Windows STA/CVG data. It preserves step/increment/attempt,
  iteration/time and convergence fields; no replacement decoder is written.
  Original permissive row skipping is retained, not treated as proof of a solve.

[Build/command instructions and limits](../../X/Execution/README.md).
The full solver command is prepared but **not executed**. No macOS/Linux solver
profile is admitted. The sole registry profile pins the already measured native
Windows x64 2.22 ccx_dynamic.exe/runtime bytes for research replay, with source
correspondence explicitly unproven. It is not RC2/full release acceptance.

## Verified observation — third-party source recovery

[CalculiX 2.22 source](../../ThirdParty/Sources/CalculiX/2.22/README.md) is now
organized under ThirdParty/Sources/CalculiX/2.22/src. All 1188 regular files
(11372771 bytes) are unchanged from the official archive:
[ccx_2.22.src.tar.bz2](https://www.dhondt.de/ccx_2.22.src.tar.bz2), retrieved
2026-10-18. Archive size is 1536859 bytes, SHA256
`3a94dcc775a31f570229734b341d6b06301ebdc759863df901c8b9bf1854c0bc`.
Source includes its original GPL-2 text and attribution. The archive prefix is
removed while preserving src/ layout and all file bytes; there are no patches.

Per-file/archive manifest and source-lock pin every recovered byte. The new
`python3 ThirdParty/Sources/verify-sources.py` checks manifest and source contents,
unexpected additions/removals and regular-file paths without downloading or
building. Upstream source scripts/Makefiles are preserved rather than rewritten
as if verified platform recipes. Nested Git attributes preserve recovered source/manifest and evidence bytes
on every checkout platform. Source recovery is incremental; the final
repository must cover all shipped third-party components and transitives.
Existing modified Netgen/Gmsh/QuadWild/Q-Morph/VTK/package/runtime source/license
and build gaps remain explicit in DEPENDENCIES/RELEASE records.

## Verified observation — six native runs

Current, RC2 and post-RC2 each pass on **macOS ARM64 and native-architecture
Linux ARM64**: **33 checks per build**, plus four CLI rejection controls.
Four source extraction/enum/legacy-body guards pass on Mac. Checks exercise real
native .NET helper processes, including 20000 lines on each pipe, exact unusual
argument tokens, Unicode/space paths, explicit environment, nonzero exit,
timeout, pre-cancel/cancel, attached descendants, concurrency behavior, missing
executables, no overwrite, type/field identity and pinned binary tamper rejection.
The helper is explicitly a process fixture, not a solver.

Original monitor checks read the actual recorded Windows STA/CVG, preserve the
one completed static increment/time/iteration and empty convergence result, and
exercise invariant parsing/D exponents using synthetic numeric rows. The CLI
refuses unknown profiles, host-incompatible/missing pinned builds, missing
monitor inputs and incorrect invocation without running a solver or creating a
run directory. Mac/Linux report no admitted native solver profile.

[Six-run verification manifest](native-job-boundary/verification.json) retains
report hashes, command logs, exact source/tool/fixture fingerprints, source
recovery checks and comparisons. Job/common/adapter/analysis sources and tools,
portable checks, monitor results and CLI controls match across hosts per mode;
all tools match across six runs. Runtime objects are excluded from engineering
result comparisons; host identity is checked separately. Native Linux runs use
cached image 27c38b44…, offline, repository read-only, temporary builds and exact
cached packages, with Podman's init reaper enabled. The user-started VM remains
running. This is not Linux x64 acceptance.

The first Linux run without an init reaper reported an attached descendant
still present; it is retained as initial-linux-without-init.json. Enabling
Podman's init option makes the unchanged cleanup check pass. The result is
consistent with orphan reaping by a real PID 1; no numerical check or process
liveness assertion was relaxed. An early Mac test compared /var versus /private/
var spellings; it now verifies access to a unique file in the intended working
directory. A field-shape test was corrected to include the original persisted
AppendOutput delegate as well as the original four job fields.

The earlier task 0023 engineering sources and all analysis tools are unchanged
by this increment; their retained six-run 331-check evidence and both explicit
correctness failures remain valid within that earlier scope. These 331 checks
are not counted as newly rerun by the job verifier. NCalc NU1701 remains visible;
no dependency/version/algorithm/tolerance change is included. Native x64 CI is
prepared additively as execution-workflow-linux-x64; **no new hosted or Windows
pass is claimed**. Full net48 compilation remains required.

## Architectural inference and exact remaining blocker

The recorded Windows 2.22 solver uses PaStiX 6.0.1 and Intel MKL runtime DLLs.
The recovered official default Makefile instead selects SPOOLES/ARPACK. Its
PaStiX instructions reference BLAS, hwloc, PaRSEC, Scotch and PaStiX4CalculiX with
integer-ABI requirements and local paths, without establishing the exact source/
patch/compiler/runtime chain of the recorded Windows binary. No native ccx,
Fortran compiler or matching accepted build was available on this Mac. Merely
building that stock default would change the sparse backend; it is not silently
substituted or promoted as parity. Upstream 3.0 RC2's actual distributed solver
bundle must also be fingerprinted before full RC2 solver acceptance.

Thus native numerical execution remains pending for a concrete reason: matching
native solver sources/patches/build/runtime/ABI provenance. Continue recovery
and measured build comparison without choosing a new default/backend policy.
In parallel, expand the original FRD/DAT field readers using the already retained
Windows results, then inspect actual new native results when a matching build
is established. No user-facing frontend or persistence format is selected here.

Lifecycle scope remains bounded: timeout/cancellation of attached children while
the parent is alive is tested; detached/escaped descendants, abrupt host death
and full Windows crash-job-object parity remain open. Both original correctness
failures/tetra host gate, Windows/net48/RC2/four-target/full workflow, CAD/UI/
persistence/source/signing/installers/Homebrew and public release gates remain.

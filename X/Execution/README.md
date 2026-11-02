# Native job execution boundary

Task 0038 adds an explicit research registry override:
`PrePoMaxX.Solve --registry <build-registry.json> run-static ...`. The default
registry remains the Windows reference. `ThirdParty/Build/calculix-cpu.py`
generates a fingerprinted native Mac ARM64 SPOOLES profile; the original bounded
deck/solve/FRD/DAT workflow has now run successfully on that host. External runtime
load paths are checked before launch; OMP/MKL/OpenBLAS reference counts stay one.
See [recipe](../../ThirdParty/Build/README.md) and
[evidence/limits](../../.project/reports/native-cpu-workflow.md). Historical
Windows/native-profile availability statements below describe the default
registry and prior task boundary, not absence of this explicit research route.

This modern partial build source-links the original CaeJob.ExecutableJob data,
Submit/progress/output behavior and original JobStatus enum in their original
assembly. Mechanical extraction keeps the original WMI/job-object implementation
in net48-only legacy partials. A .NET 10 platform partial uses structured argument
lists, native process start/exit, separate output/error capture, fresh evidence
files, timeout/cancellation and attached descendant cleanup. New platform state
is NonSerialized; no solver/numerical/persistence policy is selected.

    dotnet build X/Execution/PrePoMaxX.Execution.slnx -c Release --source X/Analysis/artifacts/offline-feed
    dotnet X/Execution/Solve/bin/Release/net10.0/PrePoMaxX.Solve.dll availability
    dotnet X/Execution/Solve/bin/Release/net10.0/PrePoMaxX.Solve.dll inspect-monitor .project/reports/windows-reference/solver/uniaxial.sta .project/reports/windows-reference/solver/uniaxial.cvg

The offline feed requires the exact packages already restored by X/Analysis.
Use an ordinary approved NuGet restore if the cache/feed has not been prepared.
NCalc NU1701 and the explicit UnitsNet asset choice remain as documented there.
Never mix this partial CaeJob or its dependencies with original application DLLs.

`availability` reports pinned profiles for the current native host. It cannot
confirm installed binaries without a directory: binaryAvailabilityChecked=false.
There is currently **no accepted native macOS/Linux solver profile**. The only
profile reproduces the already recorded Windows x64 ccx_dynamic.exe/runtime
hashes; even that profile is not a full source/build/release approval. No PATH
lookup, newest-version selection or alternative sparse backend is used.

Once the pinned Windows files are available on native Windows, the prepared
command is:

    dotnet X/Execution/Solve/bin/Release/net10.0/PrePoMaxX.Solve.dll run-static windows-reference-2.22 <solver-directory> X/Analysis/StaticDeck/cube-mesh.inp X/Analysis/StaticDeck/cube-analysis.json <new-run-directory> 120

The host checks profile/host/executable/runtime hashes before creating a run,
generates the original bounded static deck, launches directly with `-i analysis`,
sets OMP/MKL thread counts to one, supports Ctrl-C cancellation and records
status/exit/output/version/file hashes in run.json. Existing run directories are
refused. Exit zero, version and expected files are transport completion criteria;
**numericalAcceptance remains false** until engineering results are checked.
This full solver command is prepared, not executed here. Further profiles require
matching source/patch/build/ABI and analytical differential evidence.

The unchanged original CalculixMonitorDataParser reads recorded STA/CVG status
and convergence values. Its permissive row-skipping behavior remains unchanged;
monitor data is not proof of successful solution. FRD/DAT field import is next.
Process tests use a clearly marked native .NET helper, never an imitation solver.

## CPU thread recommendations

    dotnet X/Execution/Solve/bin/Release/net10.0/PrePoMaxX.Solve.dll thread-plan
    dotnet X/Execution/Solve/bin/Release/net10.0/PrePoMaxX.Solve.dll thread-plan --threads auto --jobs 2
    dotnet X/Execution/Solve/bin/Release/net10.0/PrePoMaxX.Solve.dll thread-plan --threads 8 --jobs 2

The modern-only callable `CaeJob.SolverThreadPlan.Create` recommends
`max(1, floor(available logical CPUs * 0.75))`. The CLI obtains the process's
available CPU count from .NET; callers can supply the execution host's count.
Manual `--threads N` is the total across all planned jobs, not per job. It may
override 75% up to available CPUs. Allocation is deterministic and balanced:
12 threads across five jobs gives 3,3,2,2,2. Too many simultaneous jobs for the
budget are rejected; one thread per job is required. At most 1024 jobs can be
planned in one call. Existing plans are immutable.

This command reports advice only: it launches no solver, changes no settings,
reserves no CPU capacity and does not enforce a utilization limit or schedule
jobs. Automatic production defaults, active-job allocation and GUI integration
remain future work. Existing run-static one-thread reference controls remain.
Fourteen allocation/boundary checks supplement 33 process/monitor checks; the
verifier also checks real-host auto/manual CLI results and malformed inputs.
GitLab execution checks use `tini -s` so attached descendants are reaped, matching
the local Podman `--init` requirement.

    python3 -m unittest discover -s X/Execution -p test_job_layout.py
    python3 X/Execution/verify-execution.py --expect-os Darwin --expect-architecture Arm64 --output X/Execution/artifacts/current-macos-arm64.json

Repeat with --upstream-revision 3.0.0-rc2 and post-rc2-2026-10-17. Verification
uses isolated source overlays, disposable offline package/build storage, native
process tests, original monitor fixtures and negative CLI controls. Source/enum/
legacy-project checks and downloaded source pins are retained in JSON.

Limits: full net48/Windows remains pending. Controlled timeout/cancellation tree
cleanup is tested while the parent is alive; detached/escaped children, abrupt
host death and legacy Windows crash-job-object parity remain lifecycle gates.
The original concurrent-run flag serializes jobs for one executable within this
host, with a bounded busy wait; explicit concurrent runs use fresh directories.
Cross-host locking and external executable replacement remain outside this
bounded adapter. No process-wrapper success
closes either known element correctness failure or any native-tool/release gate.

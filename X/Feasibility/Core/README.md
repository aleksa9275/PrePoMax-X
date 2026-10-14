# PrePoMax-X upstream-source core probe

An experimental .NET 10 CLI linking seven unmodified upstream C# files. It demonstrates ASCII/binary STL read/write and selected Vec3D/FeNode mathematics. No WinForms, VTK, C++/CLI, mesher, solver, NuGet package or whole-engineering-project reference is used. This is a bounded feasibility result, not the portable application or proof of PMX/command/model compatibility.

Prerequisites: .NET 10 SDK, Python 3.9+ and Git. Run from the repository root:

```sh
python3 X/Feasibility/Core/run-probe.py --output X/Feasibility/Core/artifacts/baseline.json
python3 X/Feasibility/Core/run-probe.py --revision 9e91252563739ee5304cea16c34863dfb17a74d5 --output X/Feasibility/Core/artifacts/v2.6.0.json
```

The runner verifies every source hash against `source-manifest.json` and immutable Git objects, verifies the shared fixture, builds in a disposable artifact directory, runs 23 analytical/format checks and two process-level CLI error checks, then writes JSON evidence. It does not fetch, switch branches or change source. The current build links original working-tree files; replay links an isolated temporary Git snapshot. Builds never silently stub dependencies. The two initial upstream revisions have identical selected files; the results establish replay mechanics, not adaptation to changed implementations.

Release branch v2.6.0 is divergent from master, so the verified manifest release pin is allowed even though it is not a master ancestor. Other replay revisions must be baseline ancestors. A shallow checkout may lack replay objects; fetch the official release branch explicitly if needed. Review the manifest when advancing the baseline; new source hashes must not be accepted automatically merely because Git merged successfully.

For direct inspection:

```sh
dotnet build X/Feasibility/Core/CoreProbe.csproj -c Release --disable-build-servers
dotnet X/Feasibility/Core/bin/Release/net10.0/PrePoMaxX.CoreProbe.dll inspect APIs/Python/Test_Scripts/Models/cube.stl
dotnet X/Feasibility/Core/bin/Release/net10.0/PrePoMaxX.CoreProbe.dll --self-test
```

Successful inspection emits JSON triangle count/bounds. Exit codes: 0 success, 1 input/check failure, 2 usage error. No model files are overwritten. `--self-test` uses the upstream cube fixture copied as an output asset; synthetic STL wire data and non-origin transformations have independently specified expected results.

## Source and compatibility boundaries

`CoreProbe.csproj` contains explicit links; source list and hashes are in `source-manifest.json`. Legacy `STL/Properties/AssemblyInfo.cs` is deliberately excluded from this experimental executable. Linked classes keep namespaces, but belong to the probe assembly at runtime; do not use this assembly to persist production objects or infer assembly/type compatibility. Original source attribution and repository licenses remain applicable. `NuGet.Config` clears feeds only within this experiment; there are no package dependencies.

The CLI uses the upstream STL parser and fallback option, then validates binary framing, nonempty complete triangles and finite coordinates/normals. These checks belong to the probe, not to the original application. It is not a general strict STL grammar validator: upstream partial-ASCII acceptance and other untested edge cases remain outside its guarantee.

Actual raw-parser observations are emitted separately:

- Declared binary triangle count is ignored by upstream `Read(BinaryReader)`; the probe rejects count/length mismatch.
- A binary header beginning with `solid` gives zero facets by default for the fixture; the existing `tryBinaryIfTextFailed` option handles it.
- Invalid ASCII numeric tokens can produce `NullReferenceException` in `Vertex.Read`, because its error message dereferences an unset regex match. The probe translates this into a structured input failure; upstream code remains unchanged.

The current build reports two CS0108 hiding warnings in Normal and CA2022 for STLDocument's header read. They are retained in evidence logs; no warning suppression or production patch was applied.

## Local Linux tests with Podman

The maintainer added local Podman tests on 2026-10-14, then authorized complementary native Linux x64 GitLab checks. Podman remains the local route and requires no publication. Install Podman and start its Linux engine; on macOS, initialize its VM once:

```sh
podman machine init --cpus 4 --memory 4096 --disk-size 30  # once, if no machine exists
podman machine start                                    # when stopped
python3 X/Feasibility/Core/run-podman.py
```

The default selects the Podman Linux engine's native architecture. For explicit architectures or offline reruns:

```sh
python3 X/Feasibility/Core/run-podman.py --platform linux/arm64
python3 X/Feasibility/Core/run-podman.py --platform linux/amd64
python3 X/Feasibility/Core/run-podman.py --skip-build
```

The image recipe uses Microsoft's .NET 10 SDK and installs Python/Git during preparation. Only the Containerfile is sent as build context. Tests run with networking disabled, a read-only repository and container root, and disposable `/tmp` build artifacts. JSON reports are captured and written by the host to ignored `artifacts/podman/` by default; use `--output-dir` to retain evidence elsewhere. A container/probe failure writes `success: false` and diagnostic text in that revision's report, returns nonzero and stops before the next revision. Image acquisition/build failures return nonzero before probe reports exist. No Git objects are fetched, branches changed, or files committed/pushed. The checkout must already contain both manifest-pinned source commits. Git worktrees whose object database is outside the mounted repository are not supported by this runner.

Each run verifies both pinned revisions and compares source/fixture hashes, per-check outcomes, raw parser observations, CLI contracts and cube geometry against the recorded macOS results. Image ID/digest, recipe hash, actual SDK/runtime, Podman versions, client/server architecture and cross-architecture status are retained. The tested immutable local image ID is used for execution; the base image follows .NET 10's patch line, so this is not a locked release build. `--skip-build` reuses the cached image only when its build label matches the current recipe hash.

On Apple Silicon, Linux ARM64 uses a hardware-virtualized Linux VM. Linux amd64 containers require translation/emulation; a passing translated run is supplemental evidence and does not satisfy native Linux x64 acceptance. No automatic VM creation, start, stop, resource changes or translation installation is performed by the runner. Podman Desktop is optional for these CLI tests. See `.project/reports/core-feasibility.md` for actual results and remaining platform gates.

## Complementary GitLab native Linux x64 checks

The root CI include selects `core-feasibility-linux-x64` on the documented
`saas-linux-small-amd64` hosted runner. It runs for relevant pushes to
`feature/core-feasibility`, or a manual **Run pipeline** on that branch. Other
branches, schedules, tags and merge-request pipelines are outside this task's
CI scope. The maintainer commits/pushes the reviewed changes; the agent does not
publish them. No account credentials or project variables need to be added to
this job: GitLab handles checkout, and the upstream release fetch is public.

The job uses the .NET 10 SDK image, installs Python/Git in its ephemeral
container, fetches the official release branch to obtain the divergent pinned
commit, runs comparison regression checks, then invokes:

```sh
python3 X/Feasibility/Core/run-ci.py
```

This enforces Linux/X64 in both probe runs and compares source/fixture hashes,
individual checks, parser observations, CLI contracts and cube geometry with
the recorded Mac results. Podman and CI share `probe_evidence.py`. Outputs are
`artifacts/ci/baseline.json` and `artifacts/ci/v2.6.0.json`, uploaded even on
failure and retained for 30 days. Build/probe failures retain diagnostics;
comparison failures retain the complete measured report; replay stops after a
baseline failure. Old output files are replaced with explicit pending records
before execution, preventing stale successful replay evidence.

Reports retain actual SDK/runtime versions, runner/job/pipeline identifiers,
image reference and tooling hashes, using only selected non-secret environment
fields. The image tag follows .NET 10 patch releases; the runner log's resolved
image digest must accompany downloaded evidence before acceptance. Python and
.NET process architecture assertions alone cannot prove the underlying host
is native: also inspect the actual hosted runner and job log. Configuration,
local YAML parsing and a Mac rehearsal are not a native x64 pass. Authenticated inspection confirms instance runners are enabled, the requested
amd64 runner is online/active, and October usage is 0/400 compute minutes. The
earlier pipeline was blocked by identity verification before creating any jobs.
The new manual pipeline #2947482796/job #17176590675 passed on native x64 at
822bae25, clearing the execution gate for both source pins. See
[native x64 evidence](../../../.project/reports/gitlab-linux-x64.md). Separate
GitLab semantic lint and automatic push-trigger behavior were not verified.

For a local rehearsal of CI orchestration on this Mac:

```sh
python3 X/Feasibility/Core/run-ci.py --expect-os macOS --expect-architecture Arm64 --output-dir X/Feasibility/Core/artifacts/ci-rehearsal
python3 X/Feasibility/Core/test_probe_evidence.py
```

Explicit local overrides are labelled `local rehearsal`; the GitLab job uses
the strict defaults. See [CI preparation](../../../.project/reports/gitlab-verification.md)
for actual checks and the remaining native x64 gate.

## Subsequent upstream updates

The source manifest enforces the explicit closure and baseline hashes. When upstream changes that slice, review/adapt the manifest and expectations on an integration branch, then rerun the native host and Podman checks. Review the recorded comparison references deliberately when accepting changed behavior.

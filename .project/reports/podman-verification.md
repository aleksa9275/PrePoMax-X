# Task 0002 — Local Podman verification

Date: 2026-10-14, Europe/Belgrade. Verified observation: both pinned source revisions pass on native-architecture Linux ARM64 in Podman's applehv VM, matching the recorded macOS ARM64 observations. Native Linux x64 acceptance remains pending. This report supplements the [2026-10-13 execution record](core-feasibility.md).

Later on the same date, the maintainer authorized complementary GitLab native
Linux x64 preparation alongside Podman. The YAML removal below records the
earlier adjustment; the current route restores CI. See
[CI preparation](gitlab-verification.md). The Linux results in this report
remain the actual Podman evidence.

## Authorization and changes

The maintainer installed Podman/Podman Desktop using Homebrew and requested replacing GitLab pipelines with local tests after receiving a failed-pipeline notification for `feature/core-feasibility` at `92a491cd`. The agent removed root `.gitlab-ci.yml` and `X/Feasibility/Core/gitlab-ci.yml` locally, added `Containerfile`/`run-podman.py`, and updated handoff/workflow records. Original engineering sources, legacy projects, solution, algorithms and source manifest are unchanged. No production dependencies, commits, staging, pushes or branch merges were performed for this adjustment. The maintainer handles commits and pushes.

The image build receives only the recipe as context, installs Python/Git into Microsoft's .NET SDK image and labels the recipe hash. The runner checks platform and recipe label, executes the immutable image ID, mounts the checkout read-only, disables container network access and writes build products to disposable `/tmp`. Reports are captured by the host; no writable checkout mount, host credentials or container-engine socket is passed into the test container. `--skip-build` reuses the recipe-matching image without image build/package downloads. This is a local compute test; no rendering, mesher, solver or application launch is involved.

## Infrastructure and commands

Verified observations: Podman client/server 6.1.4; macOS ARM64 client; applehv Linux ARM64 machine `podman-machine-default`, rootless, 4 CPUs, 4096 MiB RAM, 30 GiB sparse disk. At initial inspection no machine/connection existed. The agent initialized it with:

```sh
podman machine init --cpus 4 --memory 4096 --disk-size 30 --now
```

Initial invocations hit sandbox denial of `~/.config/containers` and were rerun with explicit tool approval. Starting a VM in a standalone agent command did not leave its helpers available to subsequent commands. Later starts also exposed a stale API socket (`bind: address already in use` in gvproxy's log). Keeping machine startup and test execution in the same command session allowed successful tests. The final session uses `trap 'podman machine stop' EXIT` for orderly shutdown. No machine reset/deletion, rootful switch, Docker socket helper, production package upgrade or translation installation was used.

Actual verification commands (after VM startup):

```sh
podman machine ssh 'ls /proc/sys/fs/binfmt_misc'
python3 X/Feasibility/Core/run-podman.py --platform linux/arm64 --output-dir .project/reports/core-feasibility/podman
python3 X/Feasibility/Core/run-podman.py --platform linux/arm64 --skip-build --output-dir X/Feasibility/Core/artifacts/podman-offline
python3 X/Feasibility/Core/run-podman.py --platform linux/amd64 --output-dir .project/reports/core-feasibility/podman
```

The existing VM registers `qemu-x86_64` (also i386/i486/aarch64_be); machine inspection reports Rosetta false. Cross-architecture runs use that existing translation route. They do not satisfy the charter's native Linux x64 gate.

## Linux ARM64 result

Both baseline `de8f73032a72746e3d6d9afd53d9fbd289eb310a` and release replay `9e91252563739ee5304cea16c34863dfb17a74d5` passed **23 checks, zero failures, and two CLI error contracts each**. SDK 10.0.402; runtime .NET 10.0.13; process/OS architecture Arm64. Repeating both with `--skip-build` passed again. The same three upstream-source build warnings remain recorded; no warning suppression/source patch was applied.

Evidence: [baseline](core-feasibility/podman/linux-arm64-baseline.json), [release replay](core-feasibility/podman/linux-arm64-v2.6.0.json). The evidence includes source/fixture hashes, complete checks, parser observations, CLI contracts, build log, image ID/digest, recipe hash and runtime versions. Both portable projections exactly match the corresponding macOS records: source/fixture hashes, all check results, raw parser observations, CLI contracts and cube triangle count/bounds. This is equivalence of these recorded observations, not a Windows oracle or general numerical/file-format parity result. The selected seven source files remain identical across upstream revisions.

The ARM64 derived image ID is `e2c86cca5b654054858118e3fe6e4cbdeb34c4f09ce762a36fd4f26a495f5567`, digest `sha256:3271dcd9dd3b32dd6c3fc01b5f810dda3d4474b3fbfc9f303bd5c3d47ff03c69`. Container recipe SHA-256 is retained in each report. Base SDK tag `10.0` follows patch releases; this is provenance for actual execution, not a locked release build.

The build log also retains `An issue was encountered verifying workloads`; the SDK build still succeeds with zero errors on ARM64. No workload update was needed or performed. Final `--skip-build` execution with the final runner passed both ARM64 revisions again and writes explicit `success: true` records.

## Supplemental amd64 attempt — failed before tests

The amd64 image built successfully through the existing QEMU route. Both the initial probe attempt and a cached-image retry aborted inside `dotnet build` with exit -6 and `System.AccessViolationException` in `System.Xml.NameTable.Add`, while MSBuild was loading XML. No probe tests ran, and replay was not attempted after baseline failure. The failure was reproducible in this environment; its exact runtime/emulation cause is not established. It is not evidence of a source-level test failure or a native Linux x64 result.

The final runner returned exit 1 and retained [the full failure diagnostic](core-feasibility/podman/linux-amd64-baseline.json), explicitly `success: false`. This also exercises the runner's error-reporting path. Derived image ID: `d1ddf53160f144fb6710a677b5975911927810addd4af98d052eee17c860485f`, digest `sha256:dd111f23eb3d67d7713b34923407c0e8b947aabc5ae6433cfa37bca3bc4ec39a`. No runtime workaround, Rosetta install, source patch or SDK downgrade was applied to turn this into a pass. The VM stopped successfully at the end; the initialized machine and cached images remain available for subsequent local use.

Additional verification: runner Python syntax/help checked, changed-document relative links resolve, `git diff --check` passes, and production source/solution/project diff against recorded upstream is empty. `master...upstream/master` remains 0/0. Existing Phase 0 tests were not rerun because their code is unchanged.

## GitLab state and remaining gates

The authenticated project pipeline listing showed failed pipeline `#2944154347`, branch `feature/core-feasibility`, commit `92a491cd`. Job logs/failure cause were not obtained. Do not attribute the failure to tests, quota or configuration without that evidence.

The agent attempted to open project settings; computer control returned `SCStreamErrorDomain -3801`, stating the user declined capture permission. Hosted settings were not changed and the historical pipeline was not deleted. No credentials were extracted and no remote API mutation was attempted. The local YAML removal takes effect in the repository when the maintainer commits/pushes it. It does not erase historical pipeline records.

Native Linux x64, Windows reference, macOS x64, whole-core/PMX/controller and all GUI/native-tool parity remain outside the evidence. Use the same runner on a native x64 Podman engine to address the architecture gate. Preserve upstream source paths and review the next source slice before broader extraction.

Primary tool documentation: [Podman machine initialization](https://docs.podman.io/en/latest/markdown/podman-machine-init.1.html), [container execution](https://docs.podman.io/en/latest/markdown/podman-run.1.html), [image builds](https://docs.podman.io/en/latest/markdown/podman-build.1.html). Commands and outcomes above are local observations.

## Later authenticated pipeline diagnosis — 2026-10-14

After the maintainer signed in, pipeline #2944154347 explicitly reported
GitLab identity verification was required. It created zero jobs; no probe
build/tests ran. This resolves the earlier unknown cause without changing the
Podman results. Instance runners are enabled, the selected small amd64 runner
is online/active, and October namespace usage shows 0/400 compute minutes used.
Whether the earlier account restriction is now cleared remains unconfirmed by
a new run. See [authenticated evidence](gitlab-verification.md#access-and-remaining-native-x64-gate).

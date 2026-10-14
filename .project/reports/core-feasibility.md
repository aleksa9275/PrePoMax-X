# Task 0002 core-feasibility execution report

Date: 2026-10-13, Europe/Belgrade. Outcome: **bounded Mac ARM64 source reuse proved; Linux verification pending**. No full application/core/file-compatibility claim.

Historical execution snapshot. On 2026-10-14 the maintainer replaced the GitLab CI route with local Podman testing. See [Podman verification](podman-verification.md) and [current status](../STATUS.md) for subsequent results; the CI preparation below records the original work. Later that day complementary native Linux x64 GitLab preparation was authorized alongside Podman; see [CI preparation](gitlab-verification.md).

## Authorized work and Git state

The maintainer authorized starting the recommended approach on a new branch. Reviewed Phase 0 documentation fast-forwarded into `x/main` at c840aceb; implementation branch `feature/core-feasibility` created from it. Guarded upstream sync returned zero new commits, leaving master at `de8f73032a72746e3d6d9afd53d9fbd289eb310a`. Original production source/solution/projects are unchanged relative to that upstream baseline.

Added X-owned net10.0 probe, test harness, source manifest, replay runner, Linux CI include/job and scoped agent/task records. No production dependencies, algorithm rewrites, rendering/meshing/solver integration, feature merge or push performed.

## Verified source closure

`X/Feasibility/Core/CoreProbe.csproj` explicitly links STL Extensions/Facet/Normal/STLDocument/Vertex, CaeGlobals Vec3D, and CaeMesh FeNode from their original paths. They compile together without the original engineering projects or WinForms/native bindings. Exact paths/SHA-256 and exclusions are in `X/Feasibility/Core/source-manifest.json`.

STL's legacy assembly metadata is excluded because this is a new experimental executable. Namespaces stay unchanged, but types belong to the probe assembly; this is not a production serialization identity and must not be used as PMX compatibility evidence. There are no NuGet packages, project references or upstream source edits. The experiment's local NuGet configuration has no remote feeds.

## Actual commands and outcomes

Machine: macOS ARM64; SDK 10.0.401; runtime .NET 10.0.12. Commands ran locally:

```sh
dotnet build X/Feasibility/Core/CoreProbe.csproj -c Release --disable-build-servers -v:minimal
dotnet X/Feasibility/Core/bin/Release/net10.0/PrePoMaxX.CoreProbe.dll --self-test
dotnet X/Feasibility/Core/bin/Release/net10.0/PrePoMaxX.CoreProbe.dll inspect APIs/Python/Test_Scripts/Models/cube.stl
python3 X/Feasibility/Core/run-probe.py --expect-os macOS --expect-architecture Arm64 --output .project/reports/core-feasibility/macos-arm64-baseline.json
python3 X/Feasibility/Core/run-probe.py --revision 9e91252563739ee5304cea16c34863dfb17a74d5 --expect-os macOS --expect-architecture Arm64 --output .project/reports/core-feasibility/macos-arm64-v2.6.0.json
```

Build succeeded, zero errors. Each provenance-controlled run passes 23 checks: independent ASCII/binary geometry, normals/winding/attributes/wire layout, round-trips, French numeric culture, malformed/empty/truncated/non-finite inputs through the probe, translated/rotated/mirrored/scaled nodes with preserved IDs, normalized vectors, cross-product orientation and analytic circle geometry. Two additional process checks verify JSON/error exit contracts (malformed input 1, usage 2). Cube inspection returns 12 triangles and [0,0,0]–[1,1,1] bounds.

Evidence: [baseline JSON](core-feasibility/macos-arm64-baseline.json), [stable-release replay JSON](core-feasibility/macos-arm64-v2.6.0.json). Build logs, actual runtime/architecture/SDK, per-check results, source hashes and fixture identity are stored in those records.

The source-link replay uses an isolated snapshot of the verified official v2.6.0 release branch at `9e91252563739ee5304cea16c34863dfb17a74d5`. That branch diverges from master (merge base 8273a81e784386c05c6bae71f71aa6904bbb3742); it is not a master ancestor. The runner therefore permits the explicit verified release pin plus baseline ancestors and rejects arbitrary fork revisions. An actual refusal test with `--revision feature/project-initialization` returned 1 before building.

All seven selected files are byte-identical between the two tested revisions. The replay verifies repeatable source acquisition/build/test/provenance across upstream refs, **not resilience to changed implementations or a full upstream integration**. No simulated upstream edits were introduced.

## Observed limitations, preserved rather than patched

Raw reader observations from both runs:

1. Binary declared triangle count 2 with one actual triangle parses as one; upstream ignores the count. The probe checks framing and rejects mismatch.
2. A binary header starting with `solid` produces zero triangles with the default upstream auto reader for this fixture. The existing fallback option works and is used by the probe.
3. Invalid ASCII numeric tokens produce NullReferenceException through Vertex.Read's error formatting. The probe catches/translates this into structured input failure; original code remains unchanged.

The CLI validates finite complete nonempty triangles and binary framing. It does not claim strict grammar validation of all STL inputs, nor does its validation change the Windows application. Future shared-core work should decide how to preserve/improve error behavior with targeted regressions.

Retained build warnings: CS0108 at Normal.Read(StreamReader)/Read(BinaryReader), and CA2022 at STLDocument's header read. These were not suppressed or fixed. First restore also emitted a host CSSM_ModuleLoad diagnostic; build/test exit statuses were successful and full repeatable build logs are retained. No dependency installation was used to resolve it.

## Linux CI preparation and infrastructure evidence

No local Docker, Podman, Colima, Lima, QEMU, Docker Desktop, OrbStack or Linux VM application was found by executable/common application checks. This is an available-tool inventory, not a claim about every possible remote machine.

Public GitLab project API confirms fork project 87574049 derives from official project 11057697. Runner endpoint `GET /api/v4/projects/87574049/runners` returned HTTP 401 anonymously; runner enablement and quota are not verified. No credentials were read, no pipeline submitted and no settings changed.

The prepared root CI include points to `X/Feasibility/Core/gitlab-ci.yml`. Job uses documented [Linux x64 hosted runner](https://docs.gitlab.com/ci/runners/hosted_runners/linux/) tag saas-linux-small-amd64 and SDK 10.0 image; Python/Git install occurs only inside the ephemeral CI container. It fetches the official release branch because full history of the feature alone may not contain the divergent replay commit. It runs both revisions with explicit Linux/X64 assertions and stores JSON artifacts. Both YAML files parsed successfully with Ruby's standard YAML library; **GitLab semantic lint and actual pipeline execution have not run**.

Linux acceptance remains pending publication approval and a successful job. A pipeline that waits for a runner, fails package/tool acquisition or never runs is not a pass. Windows reference and Mac Intel/Linux ARM64 execution also remain unperformed.

## Next decision

Approve publication of the concrete feature branch to origin to obtain Linux evidence. After the Linux gate, review the next managed dependency slice and acquire Windows PMX/history fixtures before broad extraction; independently recover matching custom native sources. Frontend/binding/serializer selection remains open. A small unchanged source slice compiling successfully does not resolve Controller coupling, BinaryFormatter, VTK hosting or native tool parity.

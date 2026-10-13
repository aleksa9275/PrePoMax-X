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

## Linux and subsequent upstream updates

The root `.gitlab-ci.yml` includes this directory's Linux x64 job. It uses the documented `saas-linux-small-amd64` hosted-runner tag, a .NET 10 SDK container, and ephemeral Python/Git installation. It fetches the official release branch for replay objects, verifies both revisions and records JSON artifacts. The SDK image follows the .NET 10 patch line; each report records actual SDK/runtime versions. This is not a pinned container-digest release build.

Rules run checks for relevant X/source/fixture changes. The source manifest enforces the explicit closure and baseline hashes; when upstream changes that slice, review/adapt the manifest and expectations on an integration branch. No GitLab job can merge or push development work.

No local Docker/Podman/Linux VM or QEMU installation was found on the initial Mac. The job is prepared but has not run; GitLab's project runner endpoint returned 401 without credentials, so project runner enablement/quota remains unverified. Publishing to the origin fork and successful Linux job execution are required before calling task 0002 cross-platform complete. See `.project/reports/core-feasibility.md` for actual execution evidence and remaining gates.

# Shared-core Mac acceptance and engineering data increment

Publication update: this increment is now committed/pushed at 236b1a2e;
exact-commit native Linux x64 pipeline #2956740201 passed with independently
verified downloaded evidence. [Current publication report](shared-core-data-publication.md).
Uncommitted/pending-x64 statements below retain the earlier local checkpoint.

2026-10-16, Europe/Belgrade; research/native-feasibility. Task 0015 executes the
MacBook handoff after completed native Windows tasks 0013/0014. All new changes
in this report remain uncommitted. The only published range is the reviewed
Windows commit ac51fc77449da26d9c25ddedd924feda2a55e7db.

## Verified publication and original shared slice

The existing Mac checkout was clean on the planned branch at
f1e757f15b80bb3f615c887b420180ae1a918ed5 before any fetch or update. No stash,
reset or working-tree replacement was used. Origin remained at that parent.
The supplied external bundle verified its prerequisite and branch ref; its
SHA-256 matched `4e6ea00ce6a6a961f35bb7afc7e24da39fe9d99186be4cea7c0f6c5b727c070d`.
The actual import/publication route was:

```sh
git status --short --branch
git fetch origin
git bundle verify /Users/aleksa/Downloads/PrePoMax-X-Windows-handoff/PrePoMax-X-Windows-handoff.bundle
git fetch /Users/aleksa/Downloads/PrePoMax-X-Windows-handoff/PrePoMax-X-Windows-handoff.bundle \
  research/native-feasibility:refs/remotes/windows-handoff/research-native-feasibility
git merge --ff-only refs/remotes/windows-handoff/research-native-feasibility
git push origin HEAD:refs/heads/research/native-feasibility
git ls-remote origin refs/heads/research/native-feasibility
```

The final remote query returned the full expected ac51fc77 SHA. No upstream
write, force push, mirror synchronization, x/main integration or further
implementation publication occurred. Initial sandbox Git FETCH_HEAD access was
denied; the required Git/network commands succeeded with approved escalation.

[Push pipeline #2956616374](https://gitlab.com/aleksa9275/pre-po-max-x/-/pipelines/2956616374)
passed both [shared-core job #17244123735](https://gitlab.com/aleksa9275/pre-po-max-x/-/jobs/17244123735)
and [research job #17244123734](https://gitlab.com/aleksa9275/pre-po-max-x/-/jobs/17244123734).
Both logs show checkout of ac51fc77 and native Intel Xeon Platinum 8581C CPU,
using Microsoft's SDK image ID
`sha256:9cd0d6fa04def99891bf4d5a29eb9a3878b6041f9cc25cb389ea0df2177d23fd`,
registry digest `sha256:0d99ebf1ccad15037b5c98c9fe8979d6b8dbac23812feae2277a0b277b5c5ffa`.
The shared-core log reports 25 mapping checks/nine CLI controls and successful
artifact upload. Research reports success and all six meshing/Mac comparison
categories true. Sanitized traces are retained under [platforms](shared-core/platforms/).
HTTP API access returned 403; the authenticated browser supplied the actual
pipeline/job state, complete traces and rendered shared-core artifact JSON.
That JSON was retained as normalized JSON; its hash identifies the retained
representation, not a claimed byte-for-byte archive download. Full research
artifact revalidation is not claimed in this closeout.

Before editing X/Core, the exact Windows verifier was run on both ARM64 hosts:

| Native target | SDK/runtime | Mapping checks | CLI controls | Outcome |
|---|---|---:|---:|---|
| macOS ARM64 | 10.0.401 / .NET 10.0.12 | 25 | 9 | pass |
| Linux ARM64, existing Podman VM | 10.0.402 / .NET 10.0.13 | 25 | 9 | pass |
| Hosted Linux x64 at ac51fc77 | 10.0.402 / .NET 10.0.13 | 25 | 9 | pass |

[Independent comparison](shared-core/platforms/verification.json) checks each
report's source hashes and every recorded tool fingerprint against Git objects
at ac51fc77. Check names/outcomes, all 13 vector rows and CLI sample/controls
match the retained native Windows report exactly. Maximum reported deviation
from the upstream inner-coordinate vectors is zero on all four hosts. Host
descriptions, build paths/log timing and timestamps are not portable semantics.
This closes required-platform execution of the first partial shared slice,
not whole-application acceptance.

## Verified bounded implementation

The handoff's concrete candidate is now implemented:

- `X/Core/CaeMesh/CaeMesh.csproj` adds source links for GeometryMetadata,
  GeometryMetadataEntity, GeometryMetadataProperty and IntegrationScale, retaining
  their CaeMesh namespace/assembly ownership, public visibility and serialization
  markers. Matrix remains in CaeGlobals.
- New `X/Core/CaeResults/CaeResults.csproj` links the original FrdStreamReader
  into partial CaeResults, version 1.0.0.0. The reader stays internal. A friend
  declaration applies only to PrePoMaxX.CoreDataTests in this separate portable
  project; the original Windows project/visibility is untouched. There are no
  public types in this partial CaeResults assembly. This utility is preparation
  for the full reader, not a new public results API or complete FRD decoder.
- `X/Core/Tests/Data/CoreDataTests.csproj` references those libraries and links
  the existing DataProbe harness. All 30 assertions/helpers are unchanged from
  ac51fc77; only conditional result metadata is added to the harness. SHARED_CORE
  reports actual type owners/visibility/interfaces and accurate scope limits.
  No engineering source is compiled into the new test executable.
- The verifier checks all 12 engineering sources: 11 byte-for-byte against
  de8f73032a72746e3d6d9afd53d9fbd289eb310a, plus the existing mechanically
  separated CaeException class. It checks source ownership, package absence,
  original exception extraction/net48 inclusion, seven assembly-qualified type
  identities and visibility/serialization markers, metadata interfaces and
  absence of desktop/package references. No additional original engineering
  source, original project or algorithm was changed in task 0015.

The 30 reused checks cover independent matrix values/raw singular behavior,
metadata IDs/units/copy semantics/custom field names and binary block bytes,
IntegrationScale weights and FRD partial text/binary/UTF-8/EOF/buffer behavior.
They compare exactly with the source-linked native Windows reference at
`reports/windows-reference/data-windows-x64.json`. That earlier executable
compiled the engineering sources into a probe assembly; the new executable
uses their intended separate owners. This is a behavioral comparison against
that source-linked reference, not a full original-application persistence test.

Four evidence mutations are rejected: moved serialized type, changed metadata
wire bytes, omitted assertion result and System.Windows.Forms dependency.
Two data CLI controls preserve exit code 2. Existing mapping checks, independent
geometry/topology/domain controls, sample and nine CLI controls still pass.

| Expanded assembly slice | Mapping | Data | Type contracts | CLI controls | Evidence-rejection controls |
|---|---:|---:|---:|---:|---:|
| Native Mac ARM64 | 25 | 30 | 7 | 9 + 2 | 4 |
| Native Podman Linux ARM64 | 25 | 30 | 7 | 9 + 2 | 4 |
| Native Windows x64 | pending expanded build | pending | pending | pending | pending |
| Hosted Linux x64 | pending new commit | pending | pending | pending | pending |

Both local builds have zero errors and four retained SYSLIB0050 warnings from
existing test-only FormatterConverter/SerializationInfo metadata assertions.
The three libraries compile without warnings. No BinaryFormatter, unsafe
serialization switch, PMX object reconstruction or default serializer was added.
The old isolated DataProbe was separately rebuilt on Mac: 30 checks/two CLI
controls pass and portable observations still match Windows.

[Expanded reports and independent comparison](shared-core/data-slice/verification.json)
retain the exact working-tree tool hashes, parent ac51fc77 and dirty-state flag.
Mac/Linux check rows, observations, type contracts, mapping vectors, CLI result,
source hashes and tool hashes match. The expanded build was not published;
the successful ac51fc77 pipeline cannot validate these later edits.

## Reproduce locally

From the repository root in a native ARM64 terminal:

```sh
uname -m
dotnet --info
python3 X/Core/verify.py --expect-os Darwin --expect-architecture Arm64 \
  --output X/Core/artifacts/macbook/data-macos-arm64.json
python3 X/Feasibility/Data/run-data.py --expect-os macOS --expect-architecture Arm64 \
  --reference .project/reports/windows-reference/data-windows-x64.json \
  --output X/Core/artifacts/macbook/isolated-data-macos-arm64.json
```

The existing applehv podman-machine-default was inspected, not reinitialized.
Its configuration has four CPUs, 4 GiB RAM, 30 GiB disk and Rosetta disabled.
Cached image inspection confirmed Linux/arm64, ID
`27c38b4417f399491c60ba15f35bf450ffcea6d57c78ccbc5ce3c9fb05cfcc88`, digest
`sha256:8e7419c4bb020cb0303227d5afc29c22f34f5fc5ce4d6a8fc245c8054ceec5af`.
The SDK-only e2c86cca image and translated amd64 image were not used. No C++
compiler was invoked in these managed-library runs; existing native compiler
provenance is preserved in the Windows and local-completion reports.

Initial separate-session startup left the API connection refused; a retry
reported a stale API socket bind. Ordinary machine stop cleaned up the failed
startup. Start/run/stop in one invocation then succeeded for each verifier run.
No VM/network configuration, image or installed software was changed. The VM
was confirmed stopped afterward. Actual successful command form:

```sh
trap 'podman machine stop podman-machine-default' EXIT
podman machine start podman-machine-default && \
podman run --rm --pull=never --platform linux/arm64 --network=none \
  --read-only --tmpfs /tmp:rw,size=1g \
  --mount "type=bind,source=$PWD,destination=/workspace,ro=true" \
  --entrypoint python3 \
  27c38b4417f399491c60ba15f35bf450ffcea6d57c78ccbc5ce3c9fb05cfcc88 -c '
import pathlib, subprocess, sys
result = subprocess.run(["python3", "X/Core/verify.py", "--expect-os", "Linux",
    "--expect-architecture", "Arm64", "--output", "/tmp/shared-core.json"], stdout=sys.stderr)
sys.stdout.write(pathlib.Path("/tmp/shared-core.json").read_text())
sys.exit(result.returncode)
' > X/Core/artifacts/macbook/data-linux-arm64.json
```

## Remaining gates and next handoff

Verified observation: callable source reuse has expanded without changing
engineering algorithms or the serialized owners/field contracts tested here.
Architectural inference: preserving these boundaries reduces later extraction
risk; it does not prove PMX/PMH/full clone or history compatibility.

Next bounded acceptance step is native Windows execution of the expanded
verifier (`python X/Core/verify.py --expect-os Windows --expect-architecture X64
--output X/Core/artifacts/data-windows-x64.json`) and native hosted Linux x64
after a separately authorized commit/publication. The existing CI job already
invokes this verifier. Do not overwrite this uncommitted working tree with the
older Windows bundle. The original Windows legacy smoke covers only the first
mapping source slice, not the newly added assembly slice or full solution.

Retain interactive native VTK picking/clipping/deformation/DPI, real CAD fixtures,
matching custom mesher sources/builds, full persistence/history/clone semantics
and required-platform native tool/release gates. The native Linux ARM64 GCC -O2
right_45_45 failure remains recorded (12/13; explicit contraction-off and -O0
controls pass 13/13). These managed passes do not resolve that C++ compiler
policy question. Native Windows compiler identities/default/off results remain
in the existing Windows reference report. No frontend, default serializer, F001,
production-native policy, upstream communication or integration was selected.
Private PMX/PMH/ZIP files were not needed or opened and remain outside Git.

# PrePoMax-X engineering data boundary probe

Task 0003 links six unchanged upstream files into an isolated net10.0 executable:
Matrix, GeometryMetadata/Entity/Property, IntegrationScale and FrdStreamReader.
It has no NuGet package or original-project references. Source hashes and the
baseline pin are in `source-manifest.json`.

From the repository root, with Python, Git and .NET 10 SDK installed:

```sh
python3 X/Feasibility/Data/run-data.py --expect-os macOS --expect-architecture Arm64 --output .project/reports/core-data/macos-arm64.json
```

Thirty analytical/data/stream checks and two process-level usage contracts test
independent matrix solutions, IDs/numeric/text values, copy/merge rules,
canonical-measurement exclusions, original compact metadata block bytes,
thickness/axisymmetric weights, and mixed text/binary with short reads and
buffers over 1 MiB. Raw singular matrices yield nonfinite values and negative
scale inputs are preserved; these are upstream observations, not a new input
validation policy. Metadata block length/count hardening is not established.

The probe calls the original GetObjectData and protected serialization
constructor with explicit SerializationInfo. It never invokes BinaryFormatter.
Four SYSLIB0050 warnings from this exploratory use of legacy metadata APIs are
retained. The probe's CaeMesh classes belong to PrePoMaxX.DataProbe at runtime;
never use this assembly to persist production PMX objects. No full PMX/NRBF,
mesh/result reader, CAD, FEM integration or Windows oracle claim is made.

The job `core-data-linux-x64` runs on native GitLab amd64 for pushes/manual web
runs on `feature/core-data-feasibility`. It first reruns task 0002's six
regressions and both pinned source probes, then executes this probe and compares
source hashes, checks, observations and CLI contracts with the tracked Mac
record. Reports are retained on failure; artifacts expire after 30 days.
Runner/SDK/runtime/tooling identity is recorded; image digest/CPU evidence comes
from the execution log. Push pipeline #2947730759/job #17178539405 passed at da264eef on a native
amd64 Intel Xeon host; downloaded reports match Mac observations exactly.

Full reader candidates are documented in the [dependency report](../../../.project/reports/core-data-feasibility.md).
Windows capture instructions are [here](../../../.project/reports/windows-fixture-capture.md).
The five newer source files are absent at the v2.6.0 replay pin; no six-file
replay is claimed. Task 0002's existing seven-file replay remains unchanged.

Task 0011's controlled native Windows cube exports can be checked with:

```powershell
python X/Feasibility/Data/check-windows-capture.py --capture-dir 'C:\capture' --output 'C:\evidence\semantics.json'
```

This checker expects exactly the mesh-only, reopened, and regenerated deck names
documented in `.project/reports/windows-reference-validation.md`. It checks
explicit node IDs/coordinates, connectivity, units, named sets, material values,
section associations, static time values, displacement constraints and loads.
Three altered-fixture controls reject changed connectivity/material/association.
It is a reader for this controlled export subset, not a general INP parser or
a full PMX semantic reconstruction test. Live UI observations and producer hashes
must accompany its output.

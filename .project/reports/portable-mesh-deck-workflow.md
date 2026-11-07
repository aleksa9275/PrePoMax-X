# Portable INP mesh input, measurement and mesh export

2026-10-18, Europe/Belgrade. [Task 0020](../tasks/0020-portable-mesh-deck-workflow.md).
Maintainer requests implementation while preparing Windows for GitLab. All
task 0019 edits are preserved. New implementation remains local/uncommitted on
research/native-feasibility; no additional commit/push/integration is performed.

## Runnable behavior — verified observation

`MeshDeck` now loads a real standalone INP mesh into the existing FeNode and
FeElement families, retains solver formulation names, node/element IDs and
inline/named/generated sets, and exposes inspect, measurement and mesh-only
export/reopen. It calls the existing MeasureMesh host for geometry/integration;
the sample cube measures volume 1, constant-field integral 1 and centroid
[0.5, 0.5, 0.5] within the existing analytical tolerance.

```sh
dotnet run --project X/Core/MeshDeck -c Release -- inspect X/Core/MeshDeck/unit-cube.inp
dotnet run --project X/Core/MeshDeck -c Release -- measure X/Core/MeshDeck/unit-cube.inp
dotnet run --project X/Core/MeshDeck -c Release -- export-mesh X/Core/MeshDeck/unit-cube.inp new-mesh.inp
```

The input reader distinguishes exact solver formulations, including C3D8 versus
C3D8R and multiline C3D20R connectivity. The original longest-prefix fallback
still reports a warning, e.g. C3D20RH → C3D20R; export refuses that warning rather
than silently turning a topology import into a solver-equivalence claim.
The raw exchange object is not a persisted document or an alternate FeModel.
Part/visualization construction and source element IDs are not renumbered into
new part assignments; PartId remains the original reader's unset value.

`export-mesh` explicitly omits materials, BCs, steps, surfaces and other model
keywords, listing their headers in JSON. The output is a mesh deck, not a solved
analysis deck. INCLUDE, scoped parts/assemblies, transforms and unsupported
mesh-header parameters are rejected. Coordinates must be finite; IDs and set
references are validated. Generated ranges are bounded before entering the
original loop, including zero/negative-step/overflow rejection. The input cap
is 16 MiB and 200,000 nodes/elements; the reused measurement host keeps its
10,000-item limit. Input files and existing outputs are never overwritten.

Pyramid export requires `--pyramids wedges` or `--pyramids hexahedrons`; the
original CalElement/conversion implementation produces collapsed C3D6/C3D8 or
C3D15/C3D20 elements. The explicit conversion also covers C3D5I/R and C3D13I/R
input aliases. This changes topology/formulation by the caller's explicit choice.
Quadratic tetrahedra can be inspected/exported without numerical evaluation;
measurement remains blocked by the existing correctness gate.

## Source/assembly boundaries — verified observation

Pinned upstream baseline remains de8f73032a72746e3d6d9afd53d9fbd289eb310a.
Both reviewed new upstream revisions retain the selected parser/writer bytes.
`X/Core/source_layout.py` derives and checks the mechanical source layout
against immutable Git originals; it does not generate code during compilation.
`X/Core/workflow-sources.json` fixes the reviewed compiled closure/hashes.

- `CaeModel/FileInOut/Input/InpModel/InpFileReader.MeshParsing.cs` contains the
  original element-reader table, dataset parser, element/connectivity methods,
  warnings/errors and separated node-coordinate decoding. The existing reader
  is now partial; its private AddNodes retains the original FeNodeSet handling.
  Set-label decoding receives a narrow label resolver; the original FeMesh/
  part lookup stays in a legacy wrapper. These wrappers are deterministic
  source-layout checks, not replacement algorithms or stubbed mesh types.
- `CaeGlobals/DynamicTypeDescriptor/StandardValueAttribute.cs` is the unchanged
  framework-only attribute separated from its UI editor. Namespace, public/
  internal members and assembly ownership stay unchanged; source attribution
  and original framework reference links are preserved.
- Six additional original files are linked unchanged: NamedClass,
  InpElementSet, ConvertPyramidsToEnum, CalculixKeyword, CalElement and
  CalLoadEnums. They remain in CaeGlobals/CaeMesh/CaeModel respectively.
- New InpMeshData/ReadMeshData and MeshDeckWriter are explicit input/output
  boundaries. The node transport formatter uses invariant G17 precision for
  coordinate roundtrip. CalElement performs existing element formatting and
  requested pyramid conversion. Standalone reads restore culture and parser
  state and serialize access to that entry point; no whole-application
  concurrency redesign is claimed.

The new SDK CaeModel library references the existing partial CaeMesh. Source
closure grows from 37 to 48 files. All separated/new production files are also
included once in their original net48 projects. Only four existing production
paths change in this increment: original attribute file/project and original
INP reader/project. Existing engineering formulas, serialized type ownership
and original public reader entry points are retained. No dependency/feed,
frontend, native tool or default serializer is introduced.

## Acceptance and retained evidence

[verification.json](mesh-deck-workflow/verification.json) records the six full
native reports and their hashes. Current working slice, RC2 marker 912fb3d0
and post-RC2 pin f6273e39 each pass on **macOS ARM64 and Linux ARM64**, .NET SDK
10.0.402. All six have identical tool fingerprints and portable engineering,
CLI and workflow outcomes after excluding runtime descriptions.

| Acceptance per build | Result |
|---|---:|
| Previous mapping/data/accepted element checks | 25 + 30 + 95 |
| New mesh workflow checks | 68 |
| Previous CLI controls / new mesh CLI controls | 28 / 11 |
| Data-evidence rejection controls | 4 |
| Python source/replay rejection tests | 10 passing |
| Open original-source correctness failures | 2 retained |

The new checks cover actual cube geometry/roundtrip, 12 non-pyramid element
families, quadratic-pyramid ordering, all six pyramid input names with both
explicit conversions, reduced/full integration names in one set, multiline
connectivity, named/generated sets, coordinate precision, culture restoration,
concurrent standalone reads, assembly/attribute metadata, malformed inputs and
output collisions. The strict quadratic-tetrahedron discrepancy remains
26.794910717854155 against expected 28; quadratic-pyramid IsParabolic remains
false. `fullyAccepted` remains false and no tolerance was loosened.

An initial CLI negative check exposed an uncaught InvalidDataException on an
indented keyword. The controlled-error catch is fixed; initial diagnostics are
retained under diagnostics/initial-macos-arm64.json. Later review expanded the
pyramid-alias controls and rejected empty element blocks; final counts are 68,
superseding earlier 55/67-check development runs retained as diagnostics.

Six retained native-Windows-2.6 synthetic input/export files also load through
the packaged CLI on Mac and each yields the expected eight-node, unit-volume
cube. [Fixture evidence](mesh-deck-workflow/windows-fixture-macos.json).
This is raw-mesh agreement with retained inputs, **not RC2 full-model or native
Windows execution of this new assembly slice**.

Commands used for full acceptance:

```sh
python3 -m unittest discover -s X/Core -p test_upstream_replay.py
python3 X/Core/verify.py --expect-os Darwin --expect-architecture Arm64 --output X/Core/artifacts/mesh-workflow/current-macos-arm64.json
python3 X/Core/verify.py --upstream-revision 3.0.0-rc2 --expect-os Darwin --expect-architecture Arm64 --output X/Core/artifacts/mesh-workflow/rc2-macos-arm64.json
python3 X/Core/verify.py --upstream-revision post-rc2-2026-10-17 --expect-os Darwin --expect-architecture Arm64 --output X/Core/artifacts/mesh-workflow/post-rc2-macos-arm64.json
```

Linux repeats those commands with `--expect-os Linux` in the existing cached
ARM64 image 27c38b4417f399491c60ba15f35bf450ffcea6d57c78ccbc5ce3c9fb05cfcc88,
network disabled, root/repository read-only and disposable /tmp build artifacts.
Architecture was checked before execution. The user-started Podman VM remains
running. The existing x64 CI job now builds/tests the expanded solution and
package plus both upstream pins when this work is eventually published;
configuration is not a hosted x64 pass.

## Development package and Windows continuation

`X/Core/artifacts/mesh-workflow/development-build/PrePoMaxX-Core-development.zip`
contains MapFace, MeasureMesh and MeshDeck binaries, examples, corresponding
partial-build source and license. It needs a native .NET 10 runtime; source
rebuild needs the SDK. Packaging and extracted-source verification are retained
under mesh-deck-workflow/package/. The same ZIP is checked on Mac/Linux ARM64,
including 125 manifest entries, source rebuild, published cube measurement,
export/reopen, overwrite refusal, the original gate and three tamper controls.
The hash is recorded in package-report.json and each verifier report.

```sh
python3 X/Core/package.py --output-dir X/Core/artifacts/mesh-workflow/development-build
python3 X/Core/check-package.py --archive X/Core/artifacts/mesh-workflow/development-build/PrePoMaxX-Core-development.zip --report X/Core/artifacts/mesh-workflow/development-build/verification.json --expect-os Darwin --expect-architecture Arm64
```

See [Windows continuation](../history/handoffs/windows-next-session.md) for commands.
Native Windows x64 expanded-library execution and a full original net48 build/
RC2 application oracle remain pending, as does an exact new-commit hosted Linux
x64 run. The current Mac edits are uncommitted and will not appear through Git
pull alone; the development ZIP provides an immediate manual transfer route.

## Next implementation — architectural inference

This delivers real file input and export to the already reusable kernel. It is
the first increment of the mesh/deck/solve/results direction, not that complete
workflow. Next extend shared material/section/BC/step semantics and original deck
generation, then solver execution and the full FRD/DAT result graph. Preserve
the existing job runner/gateway seams; don't assemble an independent FEM model
or silently use another solver. Full FeMesh parts/selection, persistence,
interactive VTK, matching native-source and all four-platform release gates
remain open. The Windows machine can now check a concrete new executable slice
while further portable implementation proceeds.

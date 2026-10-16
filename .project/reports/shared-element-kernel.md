# Shared element kernel and runnable development build

Publication continuation: task 0018 now authorizes publishing this increment
with a small verified CI ZIP-delivery task. Its new ZIP/report supersedes the
earlier local ZIP checksum below; the original local checkpoint is retained.

2026-10-16, Europe/Belgrade; task 0017 on research/native-feasibility. The
maintainer requested continued implementation toward a working build after
publishing the data slice. Task 0015 is published at 236b1a2e; its closing
evidence is 1f1f51c4. Their pipelines #2956740201/#2956771332 passed. All
element-kernel changes described here remain **uncommitted**.

## Delivered local build

Verified observation: the partial CaeMesh library now compiles the original
FeElement hierarchy, dimensional base classes, 17 concrete element classes,
vtkCellType and GeometryTools. CompareIntArray remains in CaeGlobals. Existing
math/mapping/metadata/FRD-stream libraries remain available. The full selected
closure is 37 files; [25 added source identities](../../X/Core/element-sources.json)
are pinned to de8f73032a72746e3d6d9afd53d9fbd289eb310a.

The sole additional application-source edit removes
`using System.Windows.Forms.VisualStyles;` from CaeMesh/GeometryTools.cs.
The verifier checks that every other byte matches the baseline. All other new
element/comparer files are source-linked byte-for-byte. Type/assembly/field
ownership, engineering algorithms and original net48 project inclusions remain.
The earlier CaeException separation is still checked independently.

An initial optional inclusion of FeElementType.cs failed with 35 CS0246 errors
for DynamicTypeDescriptor/StandardValue attributes. Those UI-annotated solver
name enums are not needed by this geometry slice and were removed from portable
Compile items; their original source was not changed/stubbed. ElementTypeCount
and the full FeMesh/parts closure remain outside this increment. After this
closure correction, the whole partial solution builds with zero errors and
five retained warnings: original unused LinearPyramidElement._a (CS0414) and
four existing test-only SYSLIB0050 metadata warnings.

`X/Core/MeasureMesh` is a callable host using existing GetCG, Integrate,
GetVtkNodeIds/GetGmshNodeIds and cell-type methods. It preserves element/node/
part IDs, returns dimension-dependent measures/centroids/integrals, and does
not add incompatible length/area/volume totals. Tetrahedral signed volume is
retained. Host checks cover finite values, unique positive IDs, distinct valid
connectivity, exact node counts, bounded input and explicit scale selection.
Thickness/axisymmetric weights use the original IntegrationScale methods.
This is tool input, not a new persistence/default-serializer decision.

The development ZIP under `X/Core/artifacts/development-build/` contains
MapFace and MeasureMesh, examples, matching source, GPL license/attribution and
a file-hash manifest. It requires a native .NET 10 runtime and contains no
runtime, GUI, CAD mesher or solver. Both published examples execute on Mac and
native Linux ARM64; the extracted source independently rebuilds. This is a
runnable core development build, not the complete interactive application.

Final ZIP: 386742 bytes, SHA-256
`5a6d295877443826a00866c33009833701420db3ec83f089138f71ae01ada347`.
All 87 manifest entries and every packaged source byte were checked; the final
archive's extracted source rebuild and native Linux ARM64 examples passed.
[Bundle verification and retained build reports](shared-core/elements/bundle/verification.json).

```sh
python3 X/Core/verify.py --expect-os Darwin --expect-architecture Arm64 \
  --output X/Core/artifacts/elements/macos-arm64.json
python3 X/Core/package.py
# Extract the ZIP, then from its directory:
dotnet MapFace/PrePoMaxX.MapFace.dll examples/equilateral.json
dotnet MeasureMesh/PrePoMaxX.MeasureMesh.dll examples/unit-tetra.json
```

The tetrahedron example returns measure 1/6, centroid [0.25,0.25,0.25],
integral 1/3 and the original element/part IDs 101/8. Complete source can be
rebuilt with `dotnet build source/X/Core/PrePoMaxX.Core.slnx -c Release -m:1`
after extraction. Git-based source provenance verification uses the full
checkout and pinned baseline rather than the source ZIP alone.

## Verification and explicit failures

| Native target | Prior mapping/data | Accepted element/host checks | CLI controls | Open correctness failures |
|---|---:|---:|---:|---:|
| Mac ARM64, SDK 10.0.401/.NET 10.0.12 | 25 + 30 | 95 | 9 + 2 + 17 | 2 |
| Podman Linux ARM64, SDK 10.0.402/.NET 10.0.13 | 25 + 30 | 95 | 9 + 2 + 17 | 2 |
| Native Windows x64, new element slice | pending | pending | pending | reproduction pending |
| Hosted Linux x64, new element slice | unpublished | pending | pending | reproduction pending |

Four previous data-verifier rejection controls and seven data type contracts
also pass. The 95 accepted checks include canonical beam/triangle/quad/tetra/
pyramid/wedge/hexa geometry (linear and midpoint quadratic), constant/affine
integrals where accepted, connectivity/ownership/copy independence, host calls,
thickness/axisymmetric scaling and failure gates. Special mass/spring/gap
coverage here is limited to type ownership/dimensions; full operations/clone
correctness are not claimed. Curved/inverted/distorted cell quality and the
complete native Windows differential corpus remain open.

**The initial strict run failed 3 of 94 checks**, retained under
[diagnostics](shared-core/elements/diagnostics/). Investigation found two
separate original-source issues, reproduced identically on both ARM64 hosts:

- **Quadratic tetrahedron integration:** for a straight 2×3×4 tetrahedron
  (volume 4) with affine scalar field `2+x+2y+3z`, the exact integral is 28.
  ParabolicTetraElement.Integrate returns **26.794910717854155**. Its constant
  integral and midpoint geometry checks pass. Independent source-table moments
  show `_w` sums to 1/6 but each first moment in `_xi/_eta/_zeta` is
  **0.03915606399552952**, rather than 1/24 (**0.041666666666666664**).
  [Moment evidence](shared-core/elements/diagnostics/tetra-quadrature-moments.json).
  Source tables are byte-identical to the pinned original; this establishes
  a source-level quadrature discrepancy, not an ARM rounding explanation.
  The new measurement host rejects this element type explicitly. The original
  numerical implementation remains in the shared library unchanged.
- **Quadratic pyramid classification:** both original FeElement.IsParabolic
  overloads omit ParabolicPyramidElement. The instance helper returns false
  for a quadratic pyramid. The host uses explicit type factories, so this
  helper is not used for dispatch. The helper remains unchanged and the
  independent expected-true check remains failed in the report.

The final report separates accepted host/compatibility checks from
`openCorrectnessChecks`; both failed checks remain false and
`elementTests.fullyAccepted` remains **false**. Two accepted checks guard that
these discrepancies are still visible, and the host-rejection check ensures
the tetrahedral result is not presented as an accepted integral. No tolerance
was relaxed and no expected analytical value was replaced with the bad result.
No upstream numerical/classifier fixes or upstream communication were performed.

[Independent ARM64 comparison](shared-core/elements/verification.json) verifies
source/tool fingerprints, accepted checks, geometry observations, both open
failures and measurement CLI outcomes match. The reused 30 data expectations
still match native Windows observations. Reports carry actual parent commits
and dirty-state flags; they are not exact-commit hosted acceptance of these edits.

The Linux run uses the existing applehv VM and cached native image
`27c38b4417f399491c60ba15f35bf450ffcea6d57c78ccbc5ce3c9fb05cfcc88`,
Linux/arm64, no Rosetta/amd64 translation. The offline read-only/tmpfs command
from [the data report](shared-core-data-slice.md#reproduce-locally) runs the same
updated verifier with output `X/Core/artifacts/elements/linux-arm64.json`.
The actual final ZIP was then mounted read-only, extracted to container /tmp,
all manifest entries checked and both published examples executed. The VM was
stopped after both runs. No C++ compiler or native-tool version was changed.

## Next boundary

Native Windows execution of the new verifier is next differential evidence;
native Linux x64 needs a separately authorized element-slice publication.
Before treating the affected operations as accepted, reproduce/resolve the
two original-source discrepancies in a separately reviewed correctness task.
Do not silently modify upstream algorithms to satisfy the new tests.

Architectural inference: this reusable element representation/integration
closure enables the next real mesh/result I/O boundary. It still does not
provide the full FeMesh/FeModel graph, INP/FRD reader or Controller. Existing
interactive VTK, CAD/source recovery, full PMX/PMH/history/clone and native
tool/release gates remain. Linux ARM64 GCC -O2 sensitivity remains recorded;
these managed tests do not resolve that C++ policy question. No frontend,
default serializer, F001 or x/main/upstream integration choice was made.

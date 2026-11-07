# Portable original FRD fields and DAT histories

This modern partial build reuses original CaeResults FRD ASCII/binary decoding,
Field/FieldData/FieldComponent and invariant calculations in their original
assemblies. CaeMesh nodes/elements retain original ownership. Required original
Tools IO/math methods are mechanically moved to a shared partial; full original
FeResults/FeMesh orchestration and unit-converter setup remain net48-only.
There is one engineering decoder and one field-math implementation.
Task 0089 also restores solver-collapsed pyramids with the original conversion
helpers, retains original decoded solver connectivity separately and carries
original GetVtkNodeIds permutations to the renderer.

With native .NET 10 and the exact packages cached by X/Analysis:

```sh
dotnet build X/Results/PrePoMaxX.Results.slnx -c Release --disable-build-servers -m:1 --source X/Analysis/artifacts/offline-feed
dotnet X/Results/Inspect/bin/Release/net10.0/PrePoMaxX.InspectResults.dll inspect-frd .project/reports/windows-reference/solver/uniaxial.frd
```

`CaeResults.FrdFileReader.ReadStaticSnapshot` reads completed linear/quadratic tetrahedron, wedge and hexahedron 3D static/frequency/buckling
results, with one complete node block, one element block and full single-record-
per-node fields. It supports the original ASCII and float/double binary formats,
displacement, force, stress, total strain, equivalent plastic strain and stress-error fields. Vector/tensor
invariants use the original Field methods. NodeIdsInValueOrder explicitly maps
component-array indices back to actual node IDs. File SHA256 and the raw unit
header are retained; numeric quantities remain as stored, with no unit conversion
or inference. JSON is tool output, not an application persistence-format choice.

Tasks 0087/0088 retain original ten-node C3D10 connectivity and fields through
native straight/curved CalculiX calculations and the desktop viewport. Original
PrePoMax measurement remains independently gated; broader result/analysis
families remain mandatory full-functionality work under D060.
[Actual quadratic evidence](../../.project/reports/quadratic-native-static.md).

Inspection is bounded to 64 MiB, 100000 nodes/elements, 4096 fields and 16 components
per field. Reject unsupported analyses/element types/axisymmetric scaling,
incomplete/truncated blocks, nonfinite values, unknown components and ambiguous
reordered full field records. The original complete-field decoder uses row order
when node counts match, so the boundary checks node order before decoding rather
than silently changing the original algorithm. Full FeResults preprocessing,
part/material graph, full DAT history graph, partial nodal fields, continuation records,
complex/cyclic/axisymmetric results and large-model capacity remain future work.

The new API serializes its own calls because the original parser has static
state, restores caller culture after invariant parsing and detects changed input
bytes. It does not configure global unit converters. Mutable original node/field
objects are retained; each call returns an independent snapshot. New partial
validation hooks are erased in the legacy build and do not alter its parser.
Snapshot/CLI code is modern-only; do not mix its partial DLLs with an installed
original application.

```sh
python3 -m unittest discover -s X/Results -p test_results_layout.py
python3 X/Results/verify-results.py --expect-os Darwin --expect-architecture Arm64 --output X/Results/artifacts/current-macos-arm64.json
python3 X/Results/verify-results.py --upstream-revision 3.0.0-rc2 --expect-os Darwin --expect-architecture Arm64 --output X/Results/artifacts/rc2-macos-arm64.json
python3 X/Results/verify-results.py --upstream-revision post-rc2-2026-10-17 --expect-os Darwin --expect-architecture Arm64 --output X/Results/artifacts/post-rc2-macos-arm64.json
python3 X/Results/run-podman.py --output-dir X/Results/artifacts/linux-arm64
```

Verification snapshots sources, uses exact package archives in a disposable
offline build, retains the original public synthetic Windows FRD fingerprint,
checks both actual CLI commands and runs 78 decoding/field/history checks plus
nine CLI rejection controls. Three-pin native Linux x64 CI is prepared. NCalc NU1701 and
the explicit UnitsNet asset selection remain as previously documented.

Stored reference FRD axial stress is 99.996, whereas its analytical/DAT reference
is 100. Tests preserve the actual FRD values and compare independent displacement,
force balance and invariant expectations; they do not round FRD stress to 100
or claim a new solver/numerical acceptance. Both existing element correctness
failures/tetra host gate and every native Windows/net48/RC2/full-workflow/native-
tool/four-platform/installer requirement remain. No solver runs in this increment.

## DAT histories

`DatFileReader.ReadStaticSnapshot` and `inspect-dat <file>` reuse the original
DAT block splitter, component repair, numeric decoder, DatDataSet and
HistoryResultEntries.Add. The command returns source SHA256, set/base-set names,
step/increment/time, node or element/integration-point IDs, local-coordinate flag
and original component histories. Quantities remain as stored; units are not
inferred. Time stays exactly as printed and is grouped separately for each step.
No resampling, averaging, invariant computation or FRD/DAT stress reconciliation
is performed for these histories.

```sh
dotnet X/Results/Inspect/bin/Release/net10.0/PrePoMaxX.InspectResults.dll inspect-dat .project/reports/windows-reference/solver/uniaxial.dat
```

The initial boundary admits canonical displacement, force, stress and strain
blocks with explicit positive ordered step/increment metadata, plain ASCII set
names, complete numeric rows and increasing time per history. Node IDs may be
non-contiguous; tensor identities retain both element ID and integration point.
Internal-set name repair uses the original method. Reference-point remapping,
long-name expansion, modal/complex/axisymmetric/contact/thermal processing,
full HistoryResults/FeResults graphs and persistent document operations remain
outside this API. DAT does not identify the analysis type by these blocks alone.

Limits: 8 MiB, 4096 characters per line, 256 datasets, 100000 rows per dataset,
100000 histories and 250000 scalar samples. Unknown records, malformed/nonfinite
values, incomplete rows, duplicate identities/blocks and mixed local/global
histories are rejected. Metadata and data blocks require the separators used by
the original splitter. **DAT has no reliable completion trailer**: a successfully
parsed prefix with complete rows cannot establish job completion or expected
record coverage. The CLI explicitly emits completionEstablished=false; use job
status and expected model/output coverage for later end-to-end acceptance.

Original legacy DAT orchestration and HistoryResultEntries stream persistence
remain mechanically preserved in net48 partials. Modern builds omit those
coupled members. Existing extension extraction now also shares the original
HashSet GetNextNumberedKey helper; no naming or numerical algorithm is rewritten.
The current combined suite runs **78 checks (39 FRD + 39 DAT)** and **nine CLI
rejection controls** per source pin. Both public Windows FRD/DAT fixture hashes
are recorded. Platform/publication evidence is tracked in .project/reports.

Thermal integration now admits original FRD NDTEMP/T, FLUX/F1–F3 and RFL/RFL,
and original DAT temperature, heat generation and integration-point heat-flux
histories. IDs, stored nodal ordering, times, values and original parser repair
stay authoritative. The boundary accepts CalculiX's heat-flux `for setSOLID`
spelling that the original reader already handles. Raw RFL is not converted into
an inferred total reaction; see the body-source convention in the
[thermal workflow report](../../.project/reports/thermal-analysis-workflow.md).

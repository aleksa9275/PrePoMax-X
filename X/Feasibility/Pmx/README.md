# Read-only PMX envelope and NRBF inspection

Task 0008. This is a research inspector, not PrePoMax deserialization or a
production PMX reader/writer. It never loads a type named by a payload, constructs
application objects, invokes BinaryFormatter, enables its compatibility switch
or materializes decoded arrays. Keep real model inputs outside the repository.

Requirements: Python 3, installed .NET 10 SDK. The research executable explicitly
references the trusted SDK's `System.Formats.Nrbf.dll`, whose version/hash is
recorded at runtime. This avoids a download for the experiment; an SDK-private
assembly is **not** a production dependency contract. NuGet feeds are cleared;
there are no original application/project references or production changes.

```sh
python3 X/Feasibility/Pmx/inspect-pmx.py /path/to/model.pmx --output /path/to/metadata.json
python3 X/Feasibility/Pmx/test-inspection.py
```

For the post-2.0.6 framing, the inspector checks the 32-byte header, signed
compressed length, bounded raw Deflate stream and Int64-prefixed NRBF graph.
It records graph/model/tail lengths/hashes, then decodes NRBF records through
Microsoft's NrbfDecoder. The custom model bytes and remaining file tail are
explicitly opaque. Pre-2.0.6 framing and uncompressed fallback are reported as
unsupported rather than guessed. Limits: 512 MiB input, 128 MiB inflated main
block/graph, 90-second decoder process timeout and a post-decode record check.
These are not an OS memory quota or a complete malicious-file security audit.

Reports omit source paths, string/primitive values and geometric/result data.
They include serialized type/assembly/member names, array shapes, record counts
and selected reference edges for Controller/model/commands/results. Reference
ordinals are local inventory labels, not persistent object IDs for a new schema.
Input hashes are checked before/after. The CLI refuses an output alias/hardlink
to the input. Temporary extracted graphs from normal inspection are cleaned up.

Synthetic tests hand-encode small NRBF records using the public format; no
formatter writes fixtures. They cover length/header/compression limits, unknown
application types, a self-reference without assembly loading, disclosure guards,
truncation/trailing records, CLI errors and input preservation.

A successful inventory is not a model reconstruction, Windows load, command
replay, legacy-compatible writer, numerical validation or cross-platform pass.
See [evidence](../../../.project/reports/pmx-record-inspection.md) and
[schema proposal](../../../.project/proposals/portable-document-schema.md).

Additional comparison tools:

```sh
python3 X/Feasibility/Pmx/compare-inspections.py before.json after.json --output comparison.json
python3 X/Feasibility/Pmx/inspect-result-chunks.py /path/to/model.pmx --output chunks.json
python3 X/Feasibility/Pmx/inspect-result-chunks.py /path/to/old.pmx --compare-with /path/to/saved.pmx --output fields.json
```

The result-frame tool is limited to the observed 2.5.1-dev/2.6.0 single-result
layout. It hashes bounded inflated payloads, keeps history opaque and does not
reconstruct numerical fields. The guarded comparison permits only the documented
datatype Int32 insertion before Field's nine-byte trailer; remaining bytes must
match. Synthetic suite: 24 tests. Inventory comparisons retain type/member
changes and never declare full semantic equivalence.

Task 0010 repeats the suite and both private reference inventories on Linux
ARM64, matching Mac portable observations. See [Linux evidence](../../../.project/reports/pmx-linux-verification.md)
and `.project/scripts/verify-pmx-linux.py --help` for the cached offline Podman
route. Native Linux x64/Windows execution and semantic/history compatibility
remain separate gates.

## PMX 3.0.0 mesh prefix

The sibling `PmxMesh` probe uses the original portable CaeMesh types to read
node IDs and coordinates, element and part IDs, and C3D8 connectivity from the
bounded custom model block. It accepts absent or empty geometry, reads binary
part names, and checks visualization array lengths while skipping their contents.
Sets and other graph metadata come from the separate NRBF record path. The probe performs no desktop open or save and prints model
coordinates and connectivity to stdout.

```sh
dotnet build X/Feasibility/PmxMesh/PmxMesh.csproj -c Release --source X/Analysis/artifacts/offline-feed
python3 X/Feasibility/Pmx/inspect-mesh-prefix.py model.pmx X/Feasibility/PmxMesh/bin/Release/net10.0/PmxMesh.dll
python3 X/Feasibility/Pmx/test-mesh-prefix.py X/Feasibility/PmxMesh/bin/Release/net10.0/PmxMesh.dll X/Feasibility/Pmx/artifacts/task0045
```

The comparison requires the controlled PMX fixtures and original exports
described in the [reference report](../../../.project/reports/supported-project-persistence.md).

## Static project and embedded fields

The static graph mode follows the original Controller and model references.
It reads bounded, explicitly selected record values without activating payload
types. The combined probe checks that sets, parts, sections, supports and loads
refer to the same mesh identities recovered from the binary model block. It
includes equation strings and static settings. It prints engineering data to
stdout, so keep output from private projects outside version control.

```sh
dotnet build X/Feasibility/Pmx/NrbfInventory.csproj -c Release
python3 X/Feasibility/Pmx/inspect-static-project.py model.pmx X/Feasibility/PmxMesh/bin/Release/net10.0/PmxMesh.dll X/Feasibility/Pmx/bin/Release/net10.0/PrePoMaxX.NrbfInventory.dll
python3 X/Feasibility/Pmx/compare-embedded-frd.py model.pmx source.frd X/Feasibility/PmxMesh/bin/Release/net10.0/PmxMesh.dll
python3 X/Feasibility/Pmx/test-static-project.py X/Feasibility/PmxMesh/bin/Release/net10.0/PmxMesh.dll X/Feasibility/Pmx/bin/Release/net10.0/PrePoMaxX.NrbfInventory.dll X/Feasibility/Pmx/artifacts/task0045
```

The field comparison uses the original CaeResults field codecs and FRD reader.
It checks raw field values by node ID using the PMX result lookup. The bounded
path covers a single C3D8 static result. The history trailer and desktop
project behavior are outside this probe.

## Embedded result histories and command timeline

The PMX 3.0.0 history probe reads stored result sets, components and entry
series from a single result, including times shared across entries. It reports
the stored values and compares the supported raw series to the original DAT
reader. Stored derived stress series are decoded and reported separately.
The separate command probe reads the Controller link, record order and cursor.
It emits command types and record identity ordinals without loading payload
types or executing any stored command.

```sh
dotnet build X/Results/Inspect/Inspect.csproj -c Release --source X/Analysis/artifacts/offline-feed
python3 X/Feasibility/Pmx/inspect-history.py model.pmx --dat source.dat --results-inspector X/Results/Inspect/bin/Release/net10.0/PrePoMaxX.InspectResults.dll
python3 X/Feasibility/Pmx/inspect-command-history.py model.pmx X/Feasibility/Pmx/bin/Release/net10.0/PrePoMaxX.NrbfInventory.dll
python3 X/Feasibility/Pmx/test-history.py X/Feasibility/Pmx/artifacts/task0045 X/Feasibility/Pmx/bin/Release/net10.0/PrePoMaxX.NrbfInventory.dll X/Results/Inspect/bin/Release/net10.0/PrePoMaxX.InspectResults.dll
```

History values printed by the result probe are model data. Keep private
project output outside version control. The command projection does not read
command arguments or implement PMH replay.

## Deck reconstruction for the pinned static fixtures

The research adapter rebuilds the baseline and edited task 0045 captures as
CalculiX decks. It checks the captured PMX hash before generating any output.
It reconstructs the analysis with original types and the existing static
writer, and emits the original density keyword separately. The command writes
only to a new deck path. The intermediate projection is not a project format.

```sh
dotnet build X/Feasibility/PmxDeck/PmxDeck.csproj -c Release --source X/Analysis/artifacts/offline-feed
python3 X/Feasibility/Pmx/reconstruct-static-deck.py model.pmx X/Feasibility/PmxMesh/bin/Release/net10.0/PmxMesh.dll X/Feasibility/Pmx/bin/Release/net10.0/PrePoMaxX.NrbfInventory.dll X/Feasibility/PmxDeck/bin/Release/net10.0/PmxDeck.dll new-deck.inp
python3 X/Feasibility/Pmx/test-reconstruction.py X/Feasibility/Pmx/artifacts/task0045 X/Feasibility/PmxMesh/bin/Release/net10.0/PmxMesh.dll X/Feasibility/Pmx/bin/Release/net10.0/PrePoMaxX.NrbfInventory.dll X/Feasibility/PmxDeck/bin/Release/net10.0/PmxDeck.dll
```

## Controlled PMX write

The write probe accepts the three exact task 0045 captures, including the
official project with a duplicate named set and shifted record IDs. It finds
the modulus, force, and magnitude string records from the decoded graph.
It checks exclusive ownership of their equation containers and conservatively
rejects possible references to the string records before and after editing.
Its default edit is 105 GPa and 50 N per node. Use
`--modulus-mpa` and `--force-n` for positive decimal values. It verifies the
generated PMX before publishing to a new path on a filesystem that supports
hard links.

```sh
python3 X/Feasibility/Pmx/write-controlled-edit.py baseline.pmx new-edited.pmx X/Feasibility/PmxMesh/bin/Release/net10.0/PmxMesh.dll X/Feasibility/Pmx/bin/Release/net10.0/PrePoMaxX.NrbfInventory.dll
python3 X/Feasibility/Pmx/test-controlled-write.py X/Feasibility/Pmx/artifacts/task0045 X/Feasibility/PmxMesh/bin/Release/net10.0/PmxMesh.dll X/Feasibility/Pmx/bin/Release/net10.0/PrePoMaxX.NrbfInventory.dll
```

## Shape-checked static edit and reopen

With `--deck-builder`, the writer checks an experimental PMX 3.0.0 static
contract instead of requiring a pinned input hash. It checks the model graph,
mesh identities, ownership of edit records, supported element formulation,
and empty saved results and command history. The original C# deck builder
must accept both the input and edited model before the new PMX is published.
The old pinned path remains the default when the flag is omitted.

```sh
python3 X/Feasibility/Pmx/write-controlled-edit.py input.pmx edited.pmx X/Feasibility/PmxMesh/bin/Release/net10.0/PmxMesh.dll X/Feasibility/Pmx/bin/Release/net10.0/PrePoMaxX.NrbfInventory.dll --deck-builder X/Feasibility/PmxDeck/bin/Release/net10.0/PmxDeck.dll --modulus-mpa 84500.5 --force-n 42.25
python3 X/Feasibility/Pmx/reconstruct-static-deck.py edited.pmx X/Feasibility/PmxMesh/bin/Release/net10.0/PmxMesh.dll X/Feasibility/Pmx/bin/Release/net10.0/PrePoMaxX.NrbfInventory.dll X/Feasibility/PmxDeck/bin/Release/net10.0/PmxDeck.dll edited.inp --validate-shape
```

This path covers one linear static step, a temperature-independent elastic
material with density, a solid section, named-set displacement supports, and
one positive global axial force on a full-integration C3D8 model. It remains
a research command.

## Broader original CAD PMX edits

Tasks 0071–0073 add `write-cad-properties.py` for the desktop's checked one-part
CAD/C3D4 subset. It persists Poisson's ratio/density, signed global vector forces
and reassignment to existing compatible named regions. The original CLoad host
calculates magnitude. A bounded wire index identifies exact member slots after
public NRBF validation; fresh string IDs preserve aliases and all unrelated
original graph/model data. The older C3D8 and axial-only writer contracts remain.

`test-cad-properties.py`, `test-cad-vector.py` and `test-cad-assignments.py` each
take source PMX, mesh decoder, graph decoder, deck builder and output receipt
paths, with optional `--original-resave`. The assignment fixture is generated by
the pinned original app using the tracked capture script; generated project
bytes remain local/ignored. [Scope, original readback and final candidate](../../../.project/reports/pmx-region-assignments.md).

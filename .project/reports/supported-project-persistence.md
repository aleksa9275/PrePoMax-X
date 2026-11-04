# Task 0045 original PMX compatibility

The supported static-solid editor can round-trip its complete input and produce
the same original C# deck in the earlier exchange experiment. The maintainer
selected original PMX compatibility for desktop Save and Open.

| Policy | Evidence and remaining work |
| --- | --- |
| Original-compatible PMX/PMH | The original Windows 2.6.0 app preserves the controlled cube and definition through PMX save/reopen and PMH import regeneration. The private model also has bounded original-app readback evidence. A native reader/writer still needs semantic reconstruction of the graph, custom mesh/result blocks, and safe history handling. It needs bidirectional tests against the exact upstream baseline before exposing PMX write. |
| Versioned exchange for the static-solid editor | The prototype preserves exact mesh and definition bytes and link identities, and the original writer produces the same deck on reopen. The first desktop implementation can use the current engineering services. Original PMX/PMH import, export and history replay remain separate parity milestones. |

The [Windows fixture report](windows-reference-validation.md) records 30
semantic checks and three negative controls. Its PMH case exercises an atomic
INP import, including undo/redo and regeneration. The
[record inventory](pmx-record-inspection.md) shows that PMX contains controller
and command aliases, custom model bytes, and a separate result tail. Recreating
only inventory records would lose engineering and replay semantics.
[CaeGlobals.Extensions.DeepClone](../../CaeGlobals/Extensions.cs) currently
uses the same legacy formatter family, but cloning needs its own alias and
mutation-isolation checks. File round-trip alone cannot establish clone
equivalence. The [post-RC2 comparison](upstream-3.0.0-rc2.md) identifies material
orientations and shell result data as examples requiring new coverage. Stable
3.0.0 source and artifact correspondence is still pending.

## Selected compatibility boundary

The maintainer selected original .pmx for project reuse. The original
`Controller.TryReadCompressedPmxAfter_2_0_6` loads the serialized graph first
and then calls `FeModel.ReadFromBinaryReader` and
`ResultsCollection.ReadFromFileStream`. The model codec delegates the custom
geometry and mesh blocks to `FeMesh`. The graph supplies the objects those
codecs populate. The original writer serializes the graph and custom model
bytes into the same compressed frame and appends results separately.

Start with an explicit record-to-domain map for a controlled fixture and
retain the original versioned binary codecs wherever the input can be
bounded. Original graph identities, member layouts, the model frame and
result tail all matter to upstream readback. A portable writer needs a proof
of the actual Windows object graph and field semantics, including command
references. A valid envelope alone cannot establish interoperability.

Check the original 3.0.0 binary and exact source first. Run original Windows
save/open in both directions and compare semantic manifests with Mac and Linux.
Verify mesh IDs and connectivity, named sets, units, equations, analysis and
output settings, result identities and values, and retained history state.
A document with unsupported state must fail safely before any lossy write.
Reopening must not execute stored commands or launch tools.

The [official downloads page](https://prepomax.fs.um.si/downloads/) lists the
3.0.0 Windows archive dated 2 November 2026. Archive contents and their source
commit correspondence have yet to be verified. The local read-only GitLab
query could not resolve the host. The existing PMX inspector passed all 24
checks on macOS. The retained Windows fixture checker passed 30 semantic checks
and matched the reopened and regenerated snapshots. This reran the comparison
of existing exports on macOS. A new Windows capture is the next acceptance input.

## Earlier exchange proof

Run [the proof](../scripts/prove-static-project-roundtrip.py) with the Release
Solve DLL as its sole argument. It stages only temporary data and reads exact
ZIP members rather than extracting archive paths. The edited synthetic cube has
nonsequential node IDs and element ID 7001. It uses 105 GPa and 50 N per node.
The original writer produced the same SHA-256 before save and after reopen,
`0158fe398faab44df9b374a35fae5f966061e78441059f07a774949dede600a3`.
The baseline deck hash differs. Six controls rejected an existing destination,
future version, unknown manifest field, unknown member, changed payload and
unknown engineering field. The result link is synthetic. The proof covers
identity retention, not result-file resolution, desktop UI or numerical reruns.

## Official 3.0.0 reference checkpoint

The official portable ZIP was downloaded and extracted into temporary storage.
The [archive receipt](pmx-3.0.0-reference/official-archive.json) pins its size,
SHA-256, Windows executable hash, and the two bundled PMX examples. A direct
read-only GitLab query returned upstream HEAD
`2a25db82896aa0aa51666eb550df19d3950a8630` and advertised no tags. The binary
and source correspondence remains unresolved.

Both bundled examples have a `PrePoMax v3.0.0` header and decode as NRBF
records. Bearing bracket has 459 records and a four-byte result tail. Profile
has 1,177 records, an FeResults record and a 1,116,744-byte result tail.
Both contain CommandsCollection records. The old inspector reports a separate
failure because this checkout differs from its historical source guard.
The receipt retains both the successful decoder outcomes and the overall
inspector failures. These public samples provide real parser fixtures while
a controlled save and original application readback are being established.

The official executable then produced three controlled PMX files through
CrossOver in a fresh temporary Windows 10 bottle. The first script failed
because a recorded script cannot replace the model or its history. The
successful scripts set model properties in a new process and reopen via the
command line in a separate process. The
[controlled receipt](pmx-3.0.0-reference/controlled-capture.json) records the
fixture hashes, decoded record counts and static-solid semantic snapshot.
Original-app exports before save and after reopen match after normalizing
nonvolatile deck lines. The result-bearing project also reopened with one
result and exported the same model deck. Its input FRD came from the retained
native Mac CalculiX solver running the synthetic uniaxial cube. The official
app assigned UNIT_LESS to this FRD at import. The result check counts reopened
results and does not compare field values.

The scripted captures show a CommandsCollection but no import, save or
recorded-script command types in the inventories. Use bundled Profile for a
real result-and-command graph and acquire a controlled nonempty history
fixture separately. Fresh Windows-native capture and full source correspondence
remain pending. The three controlled PMX inputs and graph inventories are
retained under ignored `X/Feasibility/Pmx/artifacts/task0045` for the first
portable reader increment. Reproduction scripts sit next to the receipts.

## Portable mesh prefix

The macOS probe reads the PMX 3.0.0 custom mesh prefix and constructs original
`FeNode` and `LinearHexaElement` values through the existing portable CaeMesh
assembly. All three controlled captures match the original app's exported node
coordinates, IDs, and C3D8 connectivity. The probe rejects four mutated blocks
covering nonempty geometry, oversized counts, unsupported cells, and missing
connectivity references. The existing 24 framing and inventory checks also pass.
[Mesh comparison receipt](pmx-3.0.0-reference/mesh-prefix.json).

The probe reports the remaining part bytes as unread. The next reader increment
needs to bind the mesh to the correct FeModel and FeMesh records and reconstruct
part membership, named sets and units with identity checks. Definition mapping,
result field comparisons, history and writing remain pending.

## Static project and embedded-result milestone

The portable research reader now follows the root Controller to its FeModel
and analysis FeMesh. It checks binary and graph part names and matches part
IDs, element membership, and node membership. It reads MM_TON_S_C, named
sets, elastic and density equation strings, sections, linear static settings,
supports, nodal forces, and the captured field output options. The ordered
dictionary walk verifies that stored keys and record names agree. It rejects
dangling or inconsistent references before returning an inspection result.

All three controlled graphs match the original application's deck exports
for the inspected settings. The mesh-only `Cube` name retains its original
case. The result-bearing and result-free copies yield identical static
graphs. The bounded result comparison reads the PMX node lookup and uses the
original FieldData, Field and FRD reader implementations. All four fields,
13 components and 104 raw values match by node ID. Modified values and a
duplicate result slot fail. Five graph mutation controls and the earlier
four mesh rejection controls also pass.
[macOS ARM64 verification](pmx-3.0.0-reference/static-project-macos-arm64.json).

The probe exposes selected graph data for engineering verification. Its
CaeMesh and CaeResults values reuse original types. The material, section,
step and load graph values are projections, and the visualization arrays
are only checked for framing and skipped. The result history trailer remains
opaque. Complete original model reconstruction, history replay, desktop
Open/Save and original Windows readback of a portable write remain open.

The offline Linux ARM64 run in Podman passed the same graph, mesh and field
checks and all 24 PMX inspection tests. Its static-project receipt is byte for
byte identical to macOS.
[Linux ARM64 verification](pmx-3.0.0-reference/static-project-linux-arm64.json).

For the future writer comparison, the official app under CrossOver reopened
the controlled static project and changed XSTEEL to 105 GPa and the axial load
to 50 N per node. It saved a new PMX, then reopened it in a fresh session.
The normalized solver deck survived unchanged across that cycle, and the
portable reader recovered the two edits and the preserved density. Native Mac
CalculiX solves of the before-save and after-reopen edited exports gave
identical decoded FRD fields. The edited loaded-node axial displacement was
0.00190476 mm, four times the baseline within 1e-9 mm, and the fixed-face
axial reaction changed from -100 to -200 N. Raw nodal FRD axial stress was
199.992 MPa, twice its baseline. This compares raw nodal output and does
not replace the prior integration-point analytical checks.
[Edited original-app reference](pmx-3.0.0-reference/edited-capture.json).

## Result history and command timeline milestone

The portable history probe reads the PMX 3.0.0 single-result history tree and
restores the time arrays that the original writer shares across entries. On
the controlled cube, all 96 raw series match the original DAT reader exactly,
including time, sample, identity and available metadata. Another 48 stored
derived stress series decode and match the raw series identities and times.
Their values lack an independent DAT comparison. The suite rejects seven
controls covering malformed frames, inconsistent series and changed DAT values.
[macOS history receipt](pmx-3.0.0-reference/history-macos-arm64.json).

The bundled Profile project carries 19 command records with saved cursor 18,
including geometry import, meshing, analysis and a recorded Python script.
The reader checks that the command collection refers back to the same
Controller record and preserves record order and identity without invoking
commands. The controlled scripted cube has an empty command collection.
The official executable reopened Profile through CrossOver and returned
identical time, value and effective MPa units for the saved Mises series and
the derived table series. These checks cover stored result histories and
command metadata. Command payload mapping, replay and PMH remain separate.
[Original Profile readback](pmx-3.0.0-reference/profile-history-original-readback.json).

The retained fixture directory now also contains the controlled DAT and a copy
of the official bundled Profile PMX. Their input hashes are in the receipts.

The offline Linux ARM64 verification receipt is byte for byte identical to
macOS. All 24 existing PMX inspection checks passed on both platforms, and
the earlier static-project and embedded-field comparison also passed.
[Linux history receipt](pmx-3.0.0-reference/history-linux-arm64.json).

## Reconstruction and native solve

The research adapter reconstructs both the baseline and edited official PMX
fixtures through the original mesh reader and analysis types. It builds the
deck with the existing static writer and emits the original CalDensity keyword
for the captured mass density. Only the two pinned fixture hashes can reach
the reconstruction path. A valid result-bearing PMX and an existing output
path are rejected, and the previous deck bytes survive both refusals.

The reconstructed decks match the original exports for the checked geometry,
IDs, connectivity, sets, elastic constants, density, sections, displacement
supports, forces, incrementation and field output cards. They record the same
unit system and 3D model space in a deterministic heading. The shared static
writer emits explicit default frequency 1. The original exports leave that
default implicit. Deck files therefore have their own hashes.

Native Mac CalculiX solves from both reconstructed decks. The original FRD
reader reports identical mesh identity and decoded displacement, stress and
force fields when compared with solves of the official exports. This is a
controlled PMX-to-solver reconstruction, with no generic FeModel restoration,
desktop Open or PMX write. [macOS verification](pmx-3.0.0-reference/reconstruction-macos-arm64.json).

Linux ARM64 rebuilt and verified both decks offline in Podman. Its deck
hashes, semantic checks and rejection results match macOS byte for byte.
The numerical solve comparison was run on macOS.
[Linux reconstruction verification](pmx-3.0.0-reference/reconstruction-linux-arm64.json).

## First portable write and original-app readback

The fixture-specific writer accepts only the exact original baseline PMX by
SHA-256. It replaces three identified equal-length NRBF string payloads for
the 105 GPa and 50 N per node edit, then re-encodes the original PMX envelope.
The custom model block and empty result tail remain byte-identical. The writer
checks its staged file with the portable reader before atomically publishing
to a new path. Tests reject an existing destination, the input itself as a
destination, and a different valid PMX. macOS and Linux ARM64 produce identical
candidate bytes and verification results.
[Linux receipt](pmx-3.0.0-reference/controlled-write-linux-arm64.json).

The official Windows executable running through CrossOver opened the portable
candidate, exported it and saved a separate PMX. A fresh original-app session
reopened that resave. Both exports match the official edited reference's
normalized solver deck. The portable reader recovers the same mesh and static
graph from the original resave. Native Mac CalculiX and the original FRD reader
confirm identical decoded field values from the candidate's original-app export
and the official edit's export.
[Original readback and native solve](pmx-3.0.0-reference/controlled-write-original-readback.json).

This proof uses verified string record offsets in one captured graph. General
PMX writing needs field-to-record mapping and safe graph emission for other
projects, edit types, results and command payloads. Desktop Save and native
Windows verification remain pending. Small controlled outputs are retained in
the ignored fixture directory.

## Parameterized write across two captured graphs

The controlled writer now locates unique encoded BinaryObjectString records
by the captured IDs and prior values. It recalculates the string lengths,
graph length and compressed frame length. It accepts positive decimal modulus
and axial force values and remains restricted to the baseline and official
edited capture hashes. The previous default edit still produces the same
PMX bytes. Tests cover the shifted record locations in the second graph, a
seven-byte graph growth, six rejected numeric inputs, and the existing
destination and input guards. Mac and Linux ARM64 produce identical receipts.
[Cross-platform verification](pmx-3.0.0-reference/parameterized-write-linux-arm64.json).

The official executable independently created an edit of 98,765.5 MPa and
7.125 N per node and then opened both portable candidates through CrossOver.
Their normalized solver decks match the independent official edit. The
original-app resave of the first portable candidate also matches in the
portable graph reader. Native Mac CalculiX generated byte-identical FRD files
from the independent edit and the first portable candidate's original-app
export. General field discovery and edits on other PMX graphs remain open.
[Original-app comparison](pmx-3.0.0-reference/parameterized-write-original-readback.json).

## Edit targets discovered from the saved graph

The portable writer follows Controller → FeModel → Material → Elastic to the
modulus equation and StaticStep → CLoad to the force and magnitude equations.
It resolves each equation's string record through NRBF and checks its unique
wire location before rewriting. The writer verifies the same record identities
and new values after rewriting, along with the unchanged mesh projection.
This replaces the hard-coded record IDs in the earlier proof.

The official executable created a third fixture by duplicating node set X1.
The resulting X1-1 set preserves nodes 2, 3, 6 and 7. All three target record
IDs changed. The portable writer found IDs 568, 574 and 576 and applied
123,456.75 MPa and 19.25 N per node. It retained the set and all bytes outside
the three string records in the inflated graph, as well as the model block
and result tail. Mac and Linux ARM64 writer receipts match. The 24 existing
PMX inspection tests passed on both.
[Capture and targets](pmx-3.0.0-reference/edit-discovery-fixture.json) ·
[Cross-platform checks](pmx-3.0.0-reference/edit-discovery-linux-arm64.json).

The official Windows app through CrossOver exported identical normalized decks
for its independent edit and the portable edit. Its resaved PMX produces the
same portable projection. Native Mac CalculiX produced byte-identical FRD files
from both exports. The writer still gates on the three verified input hashes.
General writes need broader field coverage and validation of shared references
outside the currently verified graphs.
[Original-app readback and solve](pmx-3.0.0-reference/edit-discovery-original-readback.json).

## Shared equation record gate

The writer now requires each target equation container to have exactly one
incoming reference in the decoded class and object array slots. It refuses
array layouts that the audit cannot inspect. For the target string record
itself, any possible NRBF MemberReference byte sequence triggers refusal.
This conservative scan also covers string arrays whose decoded values do
not expose record identity. Unrelated payload bytes can trigger the same
refusal if they match the reference encoding. The gate runs before and
after the edit, with the three known input hashes still required.

Three mutated graphs keep the same static model projection while adding an
alias through a root array slot or a class member. The gate rejects the shared
string, shared equation container in an array, and shared equation container
in a class. The approved captures still produce the same PMX hashes as the
original-app verified candidates. The tests reuse those byte-level results
for compatibility evidence without repeating the prior original-app sessions.

The macOS ARM64 and offline Linux ARM64 checks produced identical receipts.
All 24 existing PMX inspection checks passed on both platforms.
[Shared-record checks](pmx-3.0.0-reference/shared-record-gate.json).

## Shape-checked PMX edit, reopen and solve

The opt-in research path checks the PMX 3.0.0 model shape instead of a fixture
hash. It validates mesh and set identity, supported model and step records,
full-integration C3D8, and exclusive owners for the edit records. It requires
an empty command history and results tail. The original C# deck writer must
accept both the input and edited model before the PMX is published to a new
path. The previous three-fixture writer remains the default.

A fresh official fixture has a two-millimeter span, eight nonsequential nodes
and element ID 7001. The portable writer opened it, saved 84,500.5 MPa and
42.25 N per node, reopened the result and rebuilt the solver deck. A second
portable edit starts from the first generated PMX. Six refusals cover an
unlisted input on the default path, saved results, an official C3D8R project,
an older header, nonempty command history, and an existing destination.
macOS and Linux ARM64 produced identical verification receipts and all
24 existing PMX inspection checks passed.
[Cross-platform workflow checks](pmx-3.0.0-reference/shape-workflow-linux-arm64.json).

The original Windows executable through CrossOver saved the fresh fixture,
then independently performed the same edit. It opened and resaved the
portable output and exported the same normalized deck as the independent
edit. The portable reader recovered the same model projection from the
original resave. Native Mac CalculiX and the original FRD reader matched
all decoded displacement, stress and force fields from the portable
reconstruction and both original-app exports.
[Original readback and solve](pmx-3.0.0-reference/shape-workflow-original-readback.json).

Task 0045 remains open. General FeModel and visualization reconstruction,
older project layouts, projects with results and command payloads, history
replay, clone identity and broader desktop Save/Open still require coverage.
Task 0048 verifies desktop Open and Save As for the checked result-free C3D8
subset in the macOS ARM64 preview. [Desktop PMX verification](desktop-static-pmx.md).
The 4 November public upstream query returned HEAD 2a25db82896a and no
matching 3.0.0 tag, so archive-to-source correspondence remains pending.
CrossOver provided original-executable readback. Native Windows and packaged
macOS/Linux desktop acceptance still need their own runs.

## Research output cleanup, 4 November 2026

Removed 17 reviewed temporary CrossOver, build and solve directories.
Filesystem availability increased by 876,302,336 bytes, about 836 MiB. The
official ZIP, 38 fixture files and 43 retained reference records all verified
afterward. The temporary CrossOver installation can be recreated from the
retained ZIP. Work proceeds to task 0047 while the open PMX compatibility
gates stay tracked in task 0045.
[Cleanup receipt](pmx-3.0.0-reference/cleanup-2026-11-04.json).

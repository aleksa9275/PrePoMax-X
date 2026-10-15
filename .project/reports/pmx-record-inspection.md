# Real PMX framing and record-only inspection

Task 0008, 2026-10-15 (Europe/Belgrade), research/native-feasibility.
**Verified observation:** the supplied PMX is readable as bounded framing and
NRBF records on native Mac ARM64 without loading PrePoMax assemblies or invoking
BinaryFormatter. The original file remains unchanged and outside the repository.

## Input and actual payload

The maintainer recalled 2.6; the file header says **PrePoMax v2.5.1 dev**.
This is stored file metadata, not a verified producer executable/source commit.
Input SHA-256:
`80e3c303a0719317af9d23016a4f70fe5f5acb91d731e704ec45dcbbfe2e0379`.
File size 16,374,272 bytes. Its 1,910,334-byte raw-Deflate main frame inflates
to 4,703,866 bytes: Int64 graph length, 1,454,296 NRBF bytes, and 3,249,562
custom model bytes. A separate 14,463,902-byte tail follows.

[Original inventory](pmx-record-inspection/legacy-2.5.1-macos-arm64.json):
**1,638 records / 215 serialized types**, object[] root, observed PrePoMax
assembly 2.5.1.0 and engineering assemblies 1.0.0.0. It includes Controller,
FeModel, three FeMesh records, FeResults, ResultsCollection, CommandsCollection,
19 command-class records across 16 types, System.Drawing.Color and delegate
serialization metadata. PMX contains the command list; separate PMH is not
needed to inventory these stored records. Replay still needs external inputs.

Selected edges establish Controller → CommandsCollection → same Controller and
a ResultsCollection current-result reference. These are observed identities,
not source-only guesses. Reports omit source paths, string/primitive values,
geometry and result values. Record ordinals are local inventory labels.

## Decoder, bounds and tests

[Probe instructions](../../X/Feasibility/Pmx/README.md) describe setup/run.
The net10.0 executable references the trusted installed SDK's NrbfDecoder,
assembly 10.0.0.0, informational version
`10.0.12+95017c711e6afc1085133d440e42b4bd78155701`, with exact binary hash
retained. No production/application/package references, payload type loading,
array materialization or unsafe formatter switch. Loaded-assembly observations
contain none of PrePoMax/CaeGlobals/CaeMesh/CaeModel/CaeResults. An SDK-private
reference is a research convenience, not a production dependency choice.

[Microsoft's guidance](https://learn.microsoft.com/en-us/dotnet/standard/serialization/binaryformatter-migration-guide/read-nrbf-payloads)
distinguishes record decoding from constructing application objects. This tool
does not invoke original constructors, serialization callbacks or delegates.
Mac ARM64 SDK 10.0.401/.NET 10.0.12 build has zero warnings/errors; the known
CSSM_ModuleLoad diagnostic is retained.

Limits: 512 MiB input / 128 MiB inflated main block, validated lengths/Deflate
completion/trailing bytes, bounded temporary graph, 90-second decoder timeout
and post-decode record limit. These are not an OS memory quota or a comprehensive
security audit. Pre-2.0.6 framing/uncompressed fallback are explicitly unsupported.

[Synthetic evidence](pmx-record-inspection/synthetic-tests.json): **24 tests
pass**, using hand-encoded records without BinaryFormatter or the private model.
They check malformed lengths/headers/compression, limits, unknown application
types/self-reference without assembly loading, disclosure guards, CLI errors,
hardlink input preservation, result-frame bounds and field metadata comparison.

## CrossOver-saved counterpart and compatibility evidence

[Task 0009](crossover-reference.md) runs original Windows PrePoMax 2.6.0 in a
separate bottle. The maintainer confirmed model display, separate save and
model/results display after reopening. The
[saved copy](pmx-record-inspection/crossover-saved-2.6.0-macos-arm64.json)
has header v2.6.0, 1,655 records and 214 types.

[Inventory comparison](pmx-record-inspection/crossover-save-comparison.json):
custom model/mesh bytes are identical and the controller/command cycle persists.
The NRBF schema changes: OrderedDictionary adds item layout, FeModel adds keyword
overrides, CCreateMesh adds part-name fields, and environment-variable types
disappear. Semantic/job-field review remains necessary; assembly-version
normalization must not be counted as compatibility.

The compressed results tail differs. Follow-up frame fingerprints
([original](pmx-record-inspection/legacy-result-chunks.json),
[saved](pmx-record-inspection/crossover-result-chunks.json)) and
[guarded byte comparison](pmx-record-inspection/crossover-field-byte-comparison.json)
establish that the 11,793,681-byte inflated result mesh/node-lookup block is
identical. Each of four field frames preserves every original byte with one
added Int32 datatype (Vector/Tensor); the opaque 33-byte history trailer matches.
`CaeResults/FieldOutput/Field.cs` gates that insertion at version 2.5.3, before
Complex/DataState/four booleans. The check verifies unchanged prefix/suffix and
enum range; a data-change regression fails. It does not calculate a solution or
establish complete document semantics.

## Completion boundary

Task 0008's inspection/tests and
[schema proposal](../proposals/portable-document-schema.md) are complete within
scope. A PMX alone suffices for useful real compatibility evidence now. Full
domain reconstruction, clone behavior, command replay, legacy writing, a broader
historical corpus and native Windows/Linux execution remain open. The main
inspector keeps custom blocks opaque; the additional single-result probe only
fingerprints bounded frames. No default format or production serializer changed.
This supplied model is not a public regression fixture.

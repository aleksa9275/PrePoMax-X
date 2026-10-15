# Task 0008 — Read-only PMX framing and NRBF record inspection

Status: bounded inspection/tests/proposal complete, 2026-10-15 (Europe/Belgrade). Maintainer supplied a saved
PMX file and authorized continuing work without Windows; an adjusted schema is
acceptable for investigation with a future upstream PR in mind. This authorizes
a bounded legacy-format inspection/compatibility proposal, not replacing the
production format, enabling BinaryFormatter, broad refactoring, commits/pushes
or publishing/contacting upstream. Branch remains research/native-feasibility;
preceding uncommitted tasks/features are preserved.

## Scope and acceptance

Inspect the supplied file read-only, outside the repository. Verify its header,
compressed graph/model framing, source identities and bounded decompression.
Use Microsoft's record-only NrbfDecoder without loading payload types or
constructing application instances. Inventory type/assembly/member names and
array shapes/counts; do not dump string values, private paths or model contents.
Keep source input unchanged and untracked, with only hashes and compatibility
metadata in reports. Explicitly distinguish opaque binary/tail data from decoded
NRBF records. Do not claim the original Windows application can reopen the file.

Add analytical/synthetic malformed-length/compression/header/NRBF tests without
BinaryFormatter invocation. Retain decoder/runtime/tool/source hashes and actual
results. Record a versioned-schema migration proposal grounded in observed data,
preserving legacy import and explicit unsupported-data handling; no production
schema decision. Windows readback/history replay/round-trip and Linux/Windows
decoder execution remain separate verification gates.

## Outcome

[Report](../reports/pmx-record-inspection.md): 2.5.1-dev input inspected as 1,638
records/215 types on Mac ARM64; no application assemblies loaded or unsafe
formatter enabled. Twenty-four synthetic tests pass. Input unchanged/untracked;
values and original path omitted. CrossOver-saved 2.6.0 copy also inventoried,
with guarded model/result byte comparisons. The
[schema proposal](../proposals/portable-document-schema.md) is undecided for
production. No full reconstruction or native platform parity claim.

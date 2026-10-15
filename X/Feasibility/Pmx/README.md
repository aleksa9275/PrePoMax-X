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

# Task 0003 — Engineering data boundaries and PMX fixture preparation

Status: bounded probe/inventory/Windows capture preparation complete on 2026-10-14. Mac ARM64 and native GitLab Linux x64 pass 30 checks plus two CLI contracts with matching observations. Actual Windows capture/type graphs/PMX round-trip remain pending. Branch: `feature/core-data-feasibility`.

The maintainer approved proceeding with the recommended next bounded dependency
analysis/source-linked probe and PMX identity investigation, and explicitly
authorized agent commits and pushes to origin during this continuation. This
does not authorize x/main integration, production source changes, a serializer
or GUI decision, native-tool substitutions, or broad controller extraction.

## Objective and measured source selection

Advance from STL/vector/node feasibility toward original engineering data
contracts without changing persistent assembly ownership. Inspect mesh/model,
unit and reader dependencies first; compile-check candidate boundaries. Full
INP/FRD/DAT readers reach FeModel/FeMesh/FeResults, units/equations and monolithic
helpers. GeometryTools has a WinForms import; Matrix has a Drawing2D import.
Compile checks confirm GeometryTools fails at the WinForms import; Matrix builds unchanged despite its Drawing2D import. The textual scan alone could not establish that distinction.

The next bounded source-linked executable will include three original
GeometryMetadata types, IntegrationScale, FrdStreamReader and Matrix, pinned to
`de8f73032a72746e3d6d9afd53d9fbd289eb310a`. Tests preserve entity kind/IDs,
numeric/text values, canonical-measurement rules, copy/merge behavior and the
existing compact metadata binary block; test thickness/axisymmetric weights;
test mixed text/binary, partial-read and buffer-boundary stream behavior; test independently calculated matrix inversion/products/pivoting.
No full CAD/mesh/result reader or solver result interpretation is claimed.
No serialization of exploratory assembly types to PMX is permitted.

The compact block is tested through upstream GetObjectData and its original
serialization constructor with explicitly constructed SerializationInfo, not
BinaryFormatter. This is bounded binary-layout evidence, not a PMX reader,
safe arbitrary-payload decoder or selected production serialization strategy.

## Deliverables and acceptance

1. Dependency report with exact paths/symbols and compiler-boundary evidence;
   source-linked net10.0 probe with explicit hashes, no package/project refs,
   no source patches, namespace stubs or copied engineering algorithms.
2. Meaningful independently specified fixtures/assertions for the contracts
   above; explicit failures/limitations and retained warnings.
3. Native macOS ARM64 and GitLab native Linux x64 results with source/tooling,
   runtime and runner/image provenance; compare portable observations.
4. Source-only PMX/PMH framing and serialized identity inventory, clearly
   separated from observed Windows payload graphs. Windows access is available
   per maintainer; actual fixture capture/round-trip is a separate pending gate.
5. Concrete Windows capture checklist and fixture manifest template using
   original command/API paths, pinned binary/source identity and sanitised
   model-only data. No credentials/settings/token files are captured.
6. Record selected-source replay availability. Five selected newer files are absent
   at the v2.6.0 task-0002 replay pin (Matrix exists there); do not manufacture a replay or substitute
   files. Task 0002's seven-file replay remains intact.

Task 0003 completes this bounded probe/inventory/capture preparation, not the
larger roadmap's managed-core, PMX compatibility or rendering gates. Stop at a
documented boundary if preserving the selected sources requires broader edits.
Normal maintainer commit/push workflow resumes after this continuation.

## Execution and handoff

Implementation published as da264eef. Push pipeline #2947730759/job #17178539405
passed on native hosted amd64/Intel Xeon. Both original source probes and six
regressions passed before the new 30-check/two-CLI-contract probe. Downloaded
JSON/tool/source/reference hashes and portable observations were independently
verified. See [execution report](../reports/core-data-feasibility.md).
Windows access is available; [capture instructions](../reports/windows-fixture-capture.md)
and a manifest template are ready. No Windows fixture was generated or read
on this Mac; this task's completion does not close PMX compatibility.
The agent commits/pushes final evidence under the current explicit exception;
normal maintainer workflow resumes after this continuation.

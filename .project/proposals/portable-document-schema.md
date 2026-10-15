# Portable document schema — compatibility proposal

Status: **Proposed; research authorized, production schema undecided**.
2026-10-15 (Europe/Belgrade). The maintainer accepts investigating an adjusted
schema across Windows/macOS/Linux and intends an eventual upstream PR to Matej.
This is not approval to publish a PR, replace default PMX, remove legacy import,
change engineering semantics or choose a GUI. Follow the current target matrix in
PROJECT.md: Windows x64, Linux x64/ARM64 and Apple M-series macOS ARM64.

## Observations motivating the boundary

Task 0008 inspected a real supplied file with header `PrePoMax v2.5.1 dev`:
1,638 records across 215 types, including PrePoMax 2.5.1.0 and engineering
assemblies 1.0.0.0. These are observed payload identities, not only source scans.
The graph contains model/results/commands, System.Drawing.Color value records,
and delegate-serialization metadata. It has a Controller → CommandsCollection
→ same Controller cycle. ResultsCollection retains a current-result reference.
Its graph is followed by a custom model block and a large separate tail, which
the record-only inspection does not semantically decode.

See [inspection evidence](../reports/pmx-record-inspection.md). A node-only or
flat JSON conversion would omit required model/history/result semantics and
reference relationships. A new format alone does not resolve Controller/UI,
native tool, clone or rendering boundaries.

## Candidate contract

**Architectural proposal:** evolve an explicit versioned document boundary,
independent of runtime assembly layout and GUI framework, with three categories:

1. Engineering document: unit systems/equations, geometry and topology identity,
   mesh/connectivity/sets, materials/sections/interactions/steps, command
   definitions and cursor/history semantics, results/fields and their identity.
   Preserve current algorithms, numbering and numerical precision.
2. Optional presentation state: tree/view/annotation state and color values with
   explicit semantics. Such data must not require serializing WinForms objects
   or live renderer handles. Absence must not discard engineering data.
3. Platform/session references: tool paths, job directories, credentials and UI
   callbacks need explicit ownership and path-resolution rules. Executable paths
   in imported data never imply permission to launch them. Persistent command
   meaning must be preserved without reconstituting serialized delegates.

Use explicit stable object/reference IDs wherever aliasing or cycles matter;
define each command/data kind rather than using arbitrary runtime type names.
Specify format major/minor, producer version, units, numeric representation,
lengths/checksums/compression and quotas for each binary chunk. Preserve
unknown optional chunks losslessly or stop with a clear unsupported-required-
feature diagnostic; never silently omit unknown engineering content. Exact
field definitions, codec, extension and default-write policy remain open.

## Incremental compatibility path

- Keep legacy input immutable. Record-only NRBF decoding supplies an inventory;
  reconstruct only a reviewed, closed set of explicit domain types after custom
  binary blocks and version gates are understood. Decode success is not import.
- Add a bounded experimental exchange/snapshot contract only when a real use
  requires it; do not serialize exploratory source-linked assembly identities
  into production PMX files. File persistence and in-memory clone behavior have
  different callers, but both must preserve required aliases and independence.
- Test backward import and old/new same-baseline application readback. Any new
  writer must use a distinct declared version/route until legacy Windows
  compatibility or an explicit migration policy is approved. Keep original
  files and a lossless fallback for unsupported data.
- Validate on native Windows, macOS and Linux (and the required architectures).
  CrossOver can supply additional original-application evidence; it cannot stand
  for native platform acceptance or numerical equivalence.
- Prepare small upstream-reviewable changes grounded in these tests. An example
  candidate is removing the measured exception/UI-reporting compilation coupling
  while preserving type/assembly identity; it does not require a new file format.
  No production boundary change or upstream PR is implemented/published here.

## Decisions requiring evidence

Full observed type/field/version coverage, custom mesh/result blocks, historical
material/settings variants, command regeneration dependencies, shared references,
UI-state policy, unknown-data round-trip behavior and failure/size budgets need
fixtures and explicit acceptance. One 2.5.1-dev project is useful but cannot
define the entire schema. Keep compatibility investigation ahead of a format
commitment; retain the original Windows application as a reference.

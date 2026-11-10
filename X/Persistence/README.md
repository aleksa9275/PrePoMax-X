# Restricted original NRBF persistence

The original Controller retains its PMX envelope, mesh/results streams and command
history format. Original clone/dump entry points use the small
`CaeGlobals.BinarySerialization` seam. On .NET 10 a restricted serializer must be
installed; unrestricted BinaryFormatter is never enabled. The original net48
implementation retains its existing formatter behaviour.

`RestrictedNrbfSerializer` decodes records with pinned System.Formats.Nrbf,
resolves only the checked-in `allowed-types.txt` catalog and reviewed BCL data
containers, and reconstructs original data graphs. Assembly names from a payload
never trigger arbitrary assembly loading. Converter Type/interface declarations
are metadata-only. Graph references/cycles, serialization constructors/callbacks,
renamed original types, comparers, rectangular arrays and value types are retained.
Old persisted undo/redo UI delegate metadata is inert and accepted only from its
known event slot; delegates are never activated. The live event is reconnected.

The original formatter has no size limits, so limits scale with the input:
at most one record per byte (floor two million) and eight array slots per byte
(floor 32 million), 64 GiB per graph and 256 reconstruction levels. Writing is
limited only by the 64 GiB graph bound and NRBF's Int32 array lengths. Trailing data, unknown types/assemblies/data members,
unknown Type metadata and delegate payloads are rejected. These are NRBF graph
limits, not a promise about arbitrary compressed PMX file resource usage.

The catalog is an explicit reviewed build artifact, not reflection-based runtime
acceptance. `Runner --catalog` prints candidate entries for comparing against it;
adding a class requires reviewing its serialization constructor/callback behaviour
and checking interoperability before changing the file. The 20 focused graph and
rejection checks are in `X/Controller/Runner/PersistenceChecks.cs`.

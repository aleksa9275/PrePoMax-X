# B013 — `System.IO.FileInfo` in PMX objects is refused (fixed 20 November 2026)

19 November 2026; port gap found by upstream's `Test_Model_Fields.py` through `X/App` (M2 closeout).

`DistributionFromFile`, `ImportedPressure` and `ImportedSTLoad` keep `private FileInfo _oldFileInfo` (net48
`ISerializable`: OriginalPath, FullPath). Adding a distribution from a file deep-clones it for the command history
(`CaeGlobals.ExtensionMethods.DeepClone`), and the restricted NRBF serializer refuses the type
(`Type is not allowed: System.IO.FileInfo`). .NET 10 cannot serialize `FileInfo` itself.

Fix: a net48-compatible surrogate in `X/Persistence` that writes and reads exactly the members net48 writes, with
`mscorlib` identity, allowlisted for these three fields only; round-trip a PMX holding one with the original 3.0.1.
Never enable unrestricted deserialization for it.

## Fix (20 November 2026)

`X/Persistence/RestrictedNrbfSerializer.cs` writes a `FileInfo` as net48 `FileSystemInfo.GetObjectData` does
(`SystemClassWithMembersAndTypes`, `System.IO.FileInfo`, mscorlib; string members `OriginalPath`, `FullPath`) and
reads it back as `new FileInfo(FullPath)`. It is accepted only as the `_oldFileInfo` value of the three CaeModel
types, on writing and reading; anywhere else (another member, another type, a top-level FileInfo, a FileInfo with
other members or another assembly) it is refused. `FileInfo` is not added to the allowlist and nothing else changes.
Four persistence checks cover it (round trip; refusal outside the member when writing, as a payload, and under
another member name). Upstream's `Test_Model_Fields.py` passes through X/App; the full suite passes 64 of 81.

Differences from net48: the attributes (`LastWriteTimeUtc`) are read from disk on use, as on net48; a Windows path
read on macOS/Linux is not a rooted path there, so its `FullName` differs and the original code re-reads the file
(`updateData`), which it would do anyway for a moved file.

Pending: a PMX holding one, round-tripped with the original 3.0.1 (the 3.0.x CrossOver bottle of earlier phases is no
longer on this Mac; only the 2.6.0 reference bottle is).

## Since the 3.0.2 sync (23 November 2026)

Upstream 3.0.2 replaced the binary formatter: projects, clones and the history use its storage serializer, which
stores a `FileInfo` itself (`CaeGlobals/Serialization/PmxFileInfoFormatter.cs`). The X surrogate went with
`RestrictedNrbfSerializer`. Files of older versions are read by upstream's legacy reader under the X allowlist
binder; `System.IO.FileInfo` is now an allowlisted framework type there (the reader sets its `OriginalPath` and
`FullPath` fields; no constructor runs), no longer restricted to the `_oldFileInfo` member, since the binder does not
see the member. Persistence checks: "FileInfo of a distribution file" (storage round trip) and "legacy FileInfo
(net48 OriginalPath, FullPath)". The round trip with the original Windows application stays pending.

# B013 — `System.IO.FileInfo` in PMX objects is refused

19 November 2026; port gap found by upstream's `Test_Model_Fields.py` through `X/App` (M2 closeout).

`DistributionFromFile`, `ImportedPressure` and `ImportedSTLoad` keep `private FileInfo _oldFileInfo` (net48
`ISerializable`: OriginalPath, FullPath). Adding a distribution from a file deep-clones it for the command history
(`CaeGlobals.ExtensionMethods.DeepClone`), and the restricted NRBF serializer refuses the type
(`Type is not allowed: System.IO.FileInfo`). .NET 10 cannot serialize `FileInfo` itself.

Fix: a net48-compatible surrogate in `X/Persistence` that writes and reads exactly the members net48 writes, with
`mscorlib` identity, allowlisted for these three fields only; round-trip a PMX holding one with the original 3.0.1.
Never enable unrestricted deserialization for it.

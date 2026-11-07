# Original-family PMX capture inputs

These small public synthetic inputs/scripts preserve the six task0107–0110
original-app captures independently of the Mac's temporary evidence directories.
They contain no user model or original application binary. `manifest.json` hashes
the exact retained inputs. The resulting PMX files may contain local command-history
paths; keep recaptures outside Git and never regenerate them against user folders.

Use the pinned original Windows PrePoMax 3.0.0 application and an isolated work
folder containing one case's files. Read
[the original archive/executable identity](../../pmx-3.0.0-reference/official-archive.json)
first. The previously cached `/tmp/prepomaxx-task0045-official-3.0.0.zip` is absent
on 8 November; historical text saying it was retained is not a presence check.
Reacquire/verify the pinned archive when required; do not silently substitute a
newer application or claim an unexecuted native Windows check.

Run the original application with the case work folder and `capture.py`, e.g. on
Windows from a disposable directory (use actual absolute paths):

```text
PrePoMax.exe -g No --script C:\capture\case\capture.py -w C:\capture\case -u MM_TON_S_C
```

`source.inp` cases import complete synthetic original-keyword decks. `mesh.inp`
cases author the materials/sections/supports/loads through the original API,
including effective selection regions for 2D sections. The scripts create
`original.pmx` and `original.inp`. Inspect the command's exit/log and verify both
files. The original INP importer did not faithfully construct some membrane/2D
model definitions in the earlier exploratory captures; those failures are not
accepted fixtures. These retained scripts are the successful captures.

Use the existing safe native projection:

```text
python3 X/Feasibility/Pmx/inspect-family-project.py <original.pmx> <PmxMesh.dll> <PrePoMaxX.NrbfInventory.dll>
```

A successful capture/projection does not establish new native-session PMX
serialization, unrestricted graph editing, native Windows acceptance, numerical
acceptance or full compatibility. See [the workflow report](../../element-family-completion.md)
and [the current handoff](../../../handoffs/current-next-session.md).

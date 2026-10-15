# CrossOver original PrePoMax reference

Task 0009, 2026-10-15 (Europe/Belgrade). **User-confirmed read/save/reopen:**
Windows PrePoMax 2.6.0 displays the supplied model through CrossOver, saves a
separate copy and reopens it with model and results visible. This is useful
original-application evidence on Mac, not native platform/numerical acceptance.

## Setup and provenance

CrossOver 26.2 is installed (CLI product 26.2.0.39821, build tag
cxoffice-26.2.0rc2). Created **PrePoMax-X-reference-2.6**, template win10_64;
no commands operated on the unrelated existing bottle. The
[official downloads page](https://prepomax.fs.um.si/downloads/) supplies the
[portable 2.6.0 ZIP](https://prepomax.fs.um.si/Files/Downloads/PrePoMax%20v2.6.0.zip).
Downloaded bytes: 209,028,866; SHA-256
`7a08995fb776d3e962f859ee576078bf34d13f2b59d81c8012cddf8e69b1c384`.
[Provenance](crossover-reference/provenance.json) retains eight executable/library
identities and observations. PrePoMax.exe/Kitware.VTK are Windows x86-64 PE/.NET
assemblies. No exact matching source SHA is inferred from a release name.

Fresh-bottle defaults sufficed; no additional .NET redistributable was installed
in this attempt. This does not establish a runtime route for every release.
`PrePoMax.com --help` prints version 2.6.0.0 and exits 255. Actual help supports
file/regeneration/unit/work-directory flags, but lacks --script/--rpc from the
newer repository source. Do not assume the latest automation applies to this
binary. Startup used -f/-w on a disposable copy and printed the expected warning
for the older 2.5.1-dev input.

## Observed reference cycle

The human directly confirmed: original model visible; separate Save As completed;
saved PMX reopened with **model and results displayed**. Native desktop control
is unavailable to this agent's browser automation, so the agent did not operate
or capture that UI. The original file remains byte-identical. No meshing,
solver, history regeneration or manual numerical comparison ran.

[PMX evidence](pmx-record-inspection.md) retains inventories and comparisons:
model/mesh and result mesh/node-lookup blocks match exactly; original field
bytes are preserved with the version-gated datatype Int32 insertion; the opaque
history trailer matches. NRBF type/member changes, including disappearing
environment-variable records, remain explicit and need semantic review.
This is a successful supplementary reference cycle, not universal PMX parity.

## Reuse the persistent setup

All 217 copied application files and two PMX copies were verified by hash in
the new bottle. The visible session started from the temporary test directory.
Future launches can use **Run Command** in bottle PrePoMax-X-reference-2.6:

```text
C:\PrePoMax-X-reference\App\PrePoMax.exe
```

To open the saved reference with a persistent work directory, append:

```text
-f C:\PrePoMax-X-reference\Work\roundtrip-2.6.0.pmx -w C:\PrePoMax-X-reference\Work
```

Files are under `C:\PrePoMax-X-reference\Work`: reference.pmx and
roundtrip-2.6.0.pmx. The original project/server file was not moved or modified.
Application and private model copies remain outside Git. No dependencies,
binaries or private models were committed.

Task 0009 is complete within this reference scope. Genuine Windows verification,
native targets, broader PMX/history coverage and numerical/native-tool parity
remain pending. Pin mesher/solver identities before running those tools.

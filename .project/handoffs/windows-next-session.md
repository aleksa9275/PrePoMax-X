# Next session — native Windows reference validation

Prepared 2026-10-15. Maintainer says Windows will be available next session.
Start here when work resumes; this is a saved handoff, not a scheduled task.
Read AGENTS.md, PROJECT.md, STATUS.md, DECISIONS.md and
[task 0011](../tasks/0011-windows-reference-validation.md) before changing anything.

## Scope and transfer

Required release targets are **Windows x64, Linux x64, Linux ARM64 and Apple
M-series macOS ARM64**. Maintainer explicitly clarified “x86” as 64-bit Intel/AMD.
No Intel Mac or 32-bit x86 work is required. Linux ARM64 is a required target.

Research branch: **research/native-feasibility**, originally based on c11a73d9.
The maintainer subsequently authorized task 0012 to complete local preparation
and commit/push all reviewed research. Check STATUS and the remote branch for
the publication result: implementation 24c790ac is pushed and native Linux x64
pipeline #2951491552 passed; closing evidence follows on the same branch.
A fresh clone's default branch is still the upstream
mirror, so explicitly use the research branch containing task 0012/tools and
these instructions. First inspect checkout/status; preserve local work. Do not
reset/stash away work or reconstruct it from conversational memory. The scoped
task 0012 publication exception ends at its recorded completion; future agent
commits/pushes need a new instruction.
Keep private PMX copies/application bundles outside Git and transfer them
separately only as needed. Do not copy authentication/settings/token files.

For a new Windows clone, disable automatic line-ending conversion for that
operation (for example `git -c core.autocrlf=false clone --branch research/native-feasibility <origin-url>`).
The probes intentionally compare exact source bytes with Git objects; automatic
CRLF conversion can create an infrastructure hash failure. Inspect an existing
checkout/config before materializing files; never overwrite dirty work to fix
line endings. Synthetic solver outputs and the copied upstream CMake evidence
also have local attributes preserving their recorded bytes.

Original production sources/projects and algorithms are unchanged. Keep the
work bounded to reference capture, existing research probes and evidence. No
serializer/frontend selection, F001 integration, x/main merge or upstream contact.

## First actions on Windows

1. Inspect `git status --short --branch`, source HEAD and the presence of task
   0011/research tools. Record Windows version, native OS/process architecture,
   installed Python/.NET SDK and available C++ toolchain. Ask only for missing
   application/model/workspace locations; do not assume the Mac paths exist.
2. Identify the installed PrePoMax build and hash PrePoMax.exe, CaeGlobals,
   CaeMesh, CaeModel and CaeResults DLLs; hash native/solver tools actually used.
   Prefer a separate official 2.6.0 copy for the first comparison with CrossOver,
   preserving the user's installed application. If using another version,
   retain it as a separate reference, not a same-version regression pass.
3. Record actual `PrePoMax.com --help` output and exit status before selecting a
   capture route. Official 2.6.0 lacks the newer source tree's --script/--rpc
   options (its help returned 255 in CrossOver). Use ordinary GUI actions for
   that build. A matching newer source build may support the existing gateway;
   use the source-verified capture script only after confirming that capability.
4. Use a new disposable working directory and copied inputs. Avoid overwriting
   user models or regenerating history that points into live project folders.
   Record hashes before and after each reference cycle.

Reference identity: CrossOver used official 2.6.0 ZIP SHA-256
`7a08995fb776d3e962f859ee576078bf34d13f2b59d81c8012cddf8e69b1c384`.
Individual application binary hashes are in
[CrossOver provenance](../reports/crossover-reference/provenance.json).
Release binary identity is not proof of an exact source commit.

## First completed checkpoint: small PMX/history corpus

Follow [Windows capture instructions](../reports/windows-fixture-capture.md)
and populate [the existing manifest](../reports/core-data/windows-fixture-manifest.template.json)
in a new capture location. The first mesh-only cube needs no solver or CAD mesher:

- Import repository `APIs/Python/Test_Scripts/Models/cube.inp` with MM_TON_S_C
  units. Save a separate cube-mesh.pmx and export cube-export.inp. Reopen and
  verify node IDs 1–8, element 1/C3D8, connectivity 1–8 and unit cube bounds.
- Add a deliberately short, recorded material/section/set/static-step/BC/load
  sequence with explicitly recorded names, units and values. Save/reopen and
  compare those definitions and the exported deck. Record expected AND observed
  values; counts or screenshots alone are insufficient semantic evidence.
- In the disposable session, exercise undo/redo and history regeneration.
  Preserve the original referenced input files and record the command order/
  cursor and regenerated mesh/deck outcome. Locate PMH through the matching
  application/source, rather than collecting unrelated user histories.
- If copies of the supplied production model are available, compare native
  Windows read/save/reopen with the prior CrossOver observations. Original file
  header is **2.5.1 dev**, not the user's initial recollection of 2.6. Exact
  original hash: `80e3c303a0719317af9d23016a4f70fe5f5acb91d731e704ec45dcbbfe2e0379`.
  CrossOver-saved 2.6.0 hash:
  `79f8f17be53fcbdde22e2f40ea7ca1ce129e574599abd58e1b793d7256727341`.
  These private files are not in Git. Do not expect Windows resaves to be byte
  identical to CrossOver files; inspect and explain the actual differences.

The unexplained NRBF changes to review include job/environment-variable data,
OrderedDictionary layout, keyword overrides and mesh command members. See
[PMX inspection](../reports/pmx-record-inspection.md). Opaque history trailer
identity and saved-results display have not proved history replay or full
engineering equivalence.

Task 0012 follow-up to carry into these checks: shallow engineering record
comparison matches 27/29 types, but AnalysisJob executable/work-directory/CPU/
environment data changes and FeModel adds keyword overrides. The old environment
list has one redacted-key entry, saved list null. Verify override flags and the
intended job policy in native Windows. The scalar comparison does not prove
array contents, material/region associations or history replay.

The exact bundled solver is now identified as **CalculiX 2.22** and passes seven
analytical checks through CrossOver. Repeat
`X/Feasibility/Solver/uniaxial-cube.inp` natively with that same solver and compare
the [reference results](../reports/local-completion/solver-crossover/reference.json).
Do not substitute another version and call it the same reference.

## Portable probes and later checkpoints

After the first capture, run the existing PMX synthetic suite and inspect the
same copied reference files on native Windows. Entry points:
`X/Feasibility/Pmx/test-inspection.py` and `inspect-pmx.py --help`. Requires .NET
10 SDK with the trusted NRBF assembly. Record runtime/tool identities; no unsafe
formatter switch or payload assembly loading. Note that a test subprocess
currently invokes `python3`; confirm that command exists on Windows before
claiming the suite is runnable. Record/fix only a measured research-runner
portability issue; do not silently skip its hardlink/CLI checks.

Then repeat the existing core/data probes using their READMEs and compare the
portable observations with Mac/Linux records. Structured-meshing runner currently
expects clang++/g++ and Unix-style compiler arguments; inspect the actual Windows
toolchain before execution. A missing tool is an infrastructure result, not a
source regression or a pass. Do not install/upgrade packages to hide differences.

Linux ARM64 GCC 13.3 -O2 fails one original vector; -O0 or -O2 with explicit
`-ffp-contract=off` passes. Preserve this numerical build-policy question and
repeat compiler-mode controls on Windows as tools permit. Defaults were not
changed in production; a diagnostic pass does not erase the default-mode failure.

Only after pinning the actual solver: capture a small analytical solve, FRD/DAT
and PMX with/without saved results. Separately capture a real CAD shell T-junction
and intentional-gap control; hand-authored INP fixtures alone are not a meshing
reference. Recover matching custom mesher sources independently. See
[preparation exit gates](../reports/preparation-exit-gates.md) for the wider order.

## Close the session with evidence

Write commands, binary/source/input hashes, semantic expected/observed values,
readback/history outcomes and any failures under `.project/reports/`; update
task 0011 and STATUS. Keep private content/local paths out of tracked reports.
Distinguish native Windows execution from CrossOver and record inspection from
semantic reconstruction. Stop at a completed checkpoint if time/usage is short.
Leave changes uncommitted unless the maintainer gives new explicit instructions.
